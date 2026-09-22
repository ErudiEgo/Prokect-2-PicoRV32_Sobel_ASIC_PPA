"""USER-RUN ONLY: Four CPU executions: S1/H1 on v1 and S1/H2 on v2, common CPU/arbiter/RAM."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import traceback
from evidence import sha, load_image, golden, verify_mode, validate_firmware
from run16_basis import validate_run16_rtl
from stage2_project import validate_project
from s1_firmware import validate_s1
from profile_m3 import derive_metrics
from h2_firmware import validate_h2
from run_dma_v2_unit import MARKER
from run_soc_tests import command, save

ROOT=Path(__file__).resolve().parents[1]
MODES=(('s1_v1',2,'firmware/s1/generated/s1.hex'),
       ('h1',1,'firmware/generated/hw.hex'),
       ('s1_v2',2,'firmware/s1/generated/s1.hex'),
       ('h2',3,'firmware/h2/generated/h2.hex'))
VERSIONS={'s1_v1':1,'h1':1,'s1_v2':2,'h2':2}
SOURCES=['rtl/sobel_core.v','rtl/sobel_mmio.v','rtl/sobel_tile.v',
         'rtl/native_bus_arbiter.v','candidate/picorv32_sobel_soc_m3.v','candidate/sobel_tile_v2.v',
         'third_party/picorv32/picorv32.v','candidate/tb_sobel_soc_m3.sv']
UNITS=(
    ('tb_sobel_tile_v2',['rtl/sobel_core.v','candidate/sobel_tile_v2.v','candidate/tb_sobel_tile_v2.sv'],MARKER),
    ('tb_sobel_core',['rtl/sobel_core.v','tb/tb_sobel_core.sv'],
     'TEST PASS: sobel_core 1283 vectors; latency, busy, done, reset checked'),
    ('tb_sobel_mmio',['rtl/sobel_core.v','rtl/sobel_mmio.v','tb/tb_sobel_mmio.sv'],
     'TEST PASS: sobel_mmio register, handshake, arithmetic, error and reset checks'),
    ('tb_sobel_tile',['rtl/sobel_core.v','rtl/sobel_tile.v','tb/tb_sobel_tile.sv'],
     'TEST PASS: sobel_tile borders, partial tiles, byte lanes, stalls, busy protection and reset'),
    ('tb_native_bus_arbiter',['rtl/native_bus_arbiter.v','tb/tb_native_bus_arbiter.sv'],
     'TEST PASS: native_bus_arbiter contention, backpressure, ownership and reset'),
)

def check_sources(root=ROOT):
    meta=validate_project(root)
    if meta['milestone']!='M2_software_baseline' or meta.get('integration')!='M3_dma_integration':
        raise ValueError('Use the M3 source revision')
    return validate_firmware(root),validate_s1(root),validate_h2(root)

def measure(directory, identity, cfg, meta, expected, version):
    w,h,c=meta['width'],meta['height'],meta.get('channels',1)
    execution=verify_mode(directory,identity,w,h,cfg['tile'],cfg['memory_wait'],expected,c)
    if execution.get('hardware_enable_sobel')!=1 or execution.get('dma_version')!=version:
        raise ValueError('M3 execution hardware/version binding mismatch')
    metrics=derive_metrics(directory,execution,identity if identity in (1,3) else 0)
    metrics['notes']=[n for n in metrics['notes'] if not n.startswith('S0 software')]
    metrics['notes'].append('M3 CPU, arbiter and memory model are identical; DMA_VERSION selects v1 or v2. Compare software within each version.')
    profile=json.loads((directory/'profile.json').read_text())
    if identity==2 and (profile['mmio_read_tx'] or profile['mmio_write_tx'] or profile['tile_busy_cycles']):
        raise ValueError('Software-only variant unexpectedly used Sobel MMIO/engine')
    return execution,profile,metrics

def execute(out):
    cfg=json.loads((out/'run_config.json').read_text())
    commands=[]
    try:
        hashes=json.loads((out/'inputs.sha256.json').read_text())
        for name,digest in hashes.items():
            if sha(ROOT/name)!=digest: raise ValueError(f'Frozen input changed: {name}')
        fw,s1,h2=check_sources()
        save(out/'run16_rtl_basis.json',validate_run16_rtl(ROOT))
        meta,pixels=load_image(ROOT/'image')
        w,h,c=meta['width'],meta['height'],meta.get('channels',1)
        expected=golden(pixels,w,h,c)
        versions={'python':sys.version,'platform':sys.platform}
        for tool in ('iverilog','vvp'):
            r=subprocess.run([tool,'-V'],capture_output=True,text=True,check=True)
            versions[tool]=r.stdout+r.stderr
        save(out/'tool_versions.json',versions)
        for top,sources,marker in UNITS:
            d=out/top;d.mkdir()
            command(['iverilog','-g2012','-Wall','-Wno-timescale','-s',top,'-o','sim.vvp',
                     *[str(ROOT/p) for p in sources]],d,'compile',cfg['timeout_seconds'],commands)
            command(['vvp','sim.vvp'],d,'simulation',cfg['timeout_seconds'],commands)
            if marker not in (d/'simulation.log').read_text().splitlines():
                raise ValueError(f'Missing unit completion: {top}')
        modes={}
        for name,identity,hex_path in MODES:
            d=out/name;d.mkdir()
            size=s1['image']['bytes'] if identity==2 else h2['image']['bytes'] if identity==3 else fw['images']['hw']['bytes']
            version=VERSIONS[name]
            command(['iverilog','-g2012','-Wall','-Wno-timescale','-s','tb_sobel_soc_m3',
                     '-Ptb_sobel_soc_m3.ENABLE_SOBEL=1',
                     f'-Ptb_sobel_soc_m3.FIRMWARE_MODE={identity}',f'-Ptb_sobel_soc_m3.DMA_VERSION={version}','-o','sim.vvp',
                     *[str(ROOT/p) for p in SOURCES]],d,'compile',cfg['timeout_seconds'],commands)
            elapsed=command(['vvp','sim.vvp',f'+firmware={ROOT/hex_path}',f'+firmware_bytes={size}',
                f'+image={ROOT/"image/image.hex"}',f'+width={w}',f'+height={h}',f'+channels={c}',
                f'+tile={cfg["tile"]}',f'+memory_wait={cfg["memory_wait"]}',
                f'+max_cycles={cfg["max_cycles"]}',*(['+vcd'] if cfg['vcd'] else [])],
                d,'simulation',cfg['timeout_seconds'],commands)
            e,p,m=measure(d,identity,cfg,meta,expected,version)
            save(d/'stage2_metrics.json',m)
            modes[name]={'execution':e,'profile':p,'metrics':m,'simulation_wall_seconds':elapsed,
                         'firmware_sha256':sha(ROOT/hex_path),'hardware_enable_sobel':1,'dma_version':version}
            print(f'M3 PIXEL/PROFILE CHECK PASS: {name}; {w*h*c} samples; cycles={e["cycles"]}; CPU image reads={p["cpu_image_read_tx"]}; DMA reads={p["dma_read_tx"]}',flush=True)
        cycles={k:v['execution']['cycles'] for k,v in modes.items()}
        ratios={'S1v1_div_H1':cycles['s1_v1']/cycles['h1'],
                'S1v2_div_H2':cycles['s1_v2']/cycles['h2'],
                'H1_div_H2':cycles['h1']/cycles['h2']}
        if modes['s1_v1']['profile']!=modes['s1_v2']['profile']:
            raise ValueError('Idle DMA version changed S1 profile; investigate before comparison')
        save(out/'commands.json',commands)
        result={'status':'PASS','project_id':'picorv32_sobel_stage2','milestone':'M3_dma_integration',
                'run':out.name,'width':w,'height':h,'channels':c,'modes':modes,'ratios':ratios,
                'scope':'Real CPU RTL; identical CPU/arbiter/external TB RAM; explicitly different DMA_VERSION',
                'asic_checks':'NOT_RUN','speedup_is_not_required_for_functional_pass':True}
        bound=[out/'run16_rtl_basis.json',out/'run_config.json',out/'tool_versions.json',out/'commands.json']
        for name,_,_ in MODES:
            bound += [out/name/f for f in ('pixels.csv','tiles.csv','execution.json','profile.json','stage2_metrics.json',
                                           'output.ppm' if c==3 else 'output.pgm','compile.log','simulation.log')]
        for top,_,_ in UNITS: bound += [out/top/'compile.log',out/top/'simulation.log']
        result['evidence_sha256']={p.relative_to(out).as_posix():sha(p) for p in bound}
        save(out/'comparison.json',result)
        summary=(f'M3 SOC FUNCTIONAL TEST PASS: {out.name}\n'
                 f'Cycles: {cycles}\nRatios: {ratios}\n'
                 'S1 profiles match between v1/v2 hardware. Pixel/traffic checks passed.\n'
                 'Measured interval includes transfer/control/tile overhead, excludes boot/host decoding.\n'
                 'RGB480 and ASIC/power/energy NOT_RUN. No required speedup.\n')
        (out/'SUMMARY.txt').write_text(summary)
        print(summary,flush=True)
        return 0
    except (Exception,KeyboardInterrupt) as exc:
        save(out/'failure.json',{'status':'FAIL_OR_INCOMPLETE','error':str(exc),'traceback':traceback.format_exc()})
        (out/'SUMMARY.txt').write_text(f'M3 FAIL_OR_INCOMPLETE: {exc}\nASIC NOT_RUN\n')
        print(traceback.format_exc(),file=sys.stderr)
        return 1
    finally:
        save(out/'commands.json',commands)

def main():
    if len(sys.argv)==3 and sys.argv[1]=='--execute-frozen': return execute(Path(sys.argv[2]).resolve())
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('run');p.add_argument('--image',required=True,type=Path)
    p.add_argument('--tile',type=int,default=16);p.add_argument('--memory-wait',type=int,default=1)
    p.add_argument('--timeout-seconds',type=int,default=600);p.add_argument('--max-cycles',type=int,default=100000000)
    p.add_argument('--vcd',action='store_true');a=p.parse_args()
    if not re.fullmatch(r's2_m3_soc_[A-Za-z0-9_-]{1,70}',a.run): p.error('Use a new s2_m3_soc_ RUN name')
    if not 1<=a.tile<=64 or not 0<=a.memory_wait<=100 or a.timeout_seconds<1 or not 1<=a.max_cycles<=2000000000:
        p.error('Invalid tile/wait/timeout/watchdog')
    check_sources();validate_run16_rtl(ROOT)
    for tool in ('iverilog','vvp'):
        if not shutil.which(tool): p.error(f'Missing {tool}')
    meta,_=load_image(a.image)
    out=ROOT/'reports'/a.run
    if out.exists() or out.with_suffix('.zip').exists(): p.error('RUN/archive exists; no overwrite')
    out.mkdir(parents=True)
    try:
        frozen=out/'inputs';frozen.mkdir()
        for name in ('rtl','tb','firmware','third_party','scripts','baseline','candidate'):
            shutil.copytree(ROOT/name,frozen/name,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        for doc in [*ROOT.glob('*.md'),ROOT/'stage2.json']:
            shutil.copy2(doc,frozen/doc.name)
        shutil.copytree(a.image,frozen/'image')
        cfg={'project_id':'picorv32_sobel_stage2','milestone':'M3_dma_integration','run':a.run,
             'hardware_enable_sobel':1,'mode_identities':{k:i for k,i,_ in MODES},
             'dma_versions':VERSIONS,'accelerator':'comparison_v1_v2','tile':a.tile,'memory_wait':a.memory_wait,
             'timeout_seconds':a.timeout_seconds,'max_cycles':a.max_cycles,'vcd':a.vcd,
             'width':meta['width'],'height':meta['height'],'channels':meta.get('channels',1),
             'source_image':str(a.image.resolve())}
        save(out/'run_config.json',cfg)
        save(out/'inputs.sha256.json',{p.relative_to(frozen).as_posix():sha(p) for p in sorted(frozen.rglob('*')) if p.is_file()})
        env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
        return subprocess.call([sys.executable,str(frozen/'scripts/run_m3_tests.py'),'--execute-frozen',str(out)],env=env)
    finally:
        archive=shutil.make_archive(str(out),'zip',root_dir=out.parent,base_dir=out.name)
        print(f'EVIDENCE: {out}\nARCHIVE: {archive}',flush=True)

if __name__=='__main__': sys.exit(main())
