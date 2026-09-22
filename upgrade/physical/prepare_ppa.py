"""Prepare exact-source H1/H2 physical inputs. No simulation/synthesis/PNR."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import h2_characterization as characterization
from evidence import sha

def save(path,obj): path.write_text(json.dumps(obj,indent=2,default=str)+'\n')

def evidence():
    bound=characterization.baseline_contract()
    records=[]
    for case in characterization.cases():
        tag,w,h,*_=case
        archive=ROOT/'reports'/f'{tag}.zip'
        if not archive.is_file(): raise ValueError('Missing characterization evidence: '+tag)
        with tempfile.TemporaryDirectory(prefix='ppa_evidence_') as temp:
            base=Path(temp);(base/'reports').mkdir();(base/'scripts').mkdir()
            for name in ('h2_characterization.py','prepare_h2_characterization.py'):
                shutil.copy2(ROOT/'scripts'/name,base/'scripts'/name)
            image=f'h2_char_gray{w}x{h}_v1'
            shutil.copytree(ROOT/'inputs'/image,base/'inputs'/image)
            shutil.copy2(archive,base/'reports'/archive.name)
            with zipfile.ZipFile(archive) as z:
                if len(z.namelist())!=len(set(z.namelist())):raise ValueError('Duplicate archive entry')
                for n in z.namelist():
                    if not (base/'reports'/n).resolve().is_relative_to((base/'reports').resolve()):raise ValueError('Unsafe archive')
                z.extractall(base/'reports')
            characterization.ROOT=base
            try:record=characterization.audit_case(case,bound)
            finally:characterization.ROOT=ROOT
            record['original_archive']=str(archive)
            records.append(record)
        print('EVIDENCE MATCH:',tag,flush=True)
    return records

def prepare(dest):
    if dest.exists():raise ValueError('Prepared directory exists; refusing overwrite')
    ref=ROOT/'physical/run16_reference'
    origin=json.loads((ref/'origin.json').read_text())
    for name,digest in origin['files_sha256'].items():
        if sha(ref/name)!=digest:raise ValueError('RUN16 reference changed: '+name)
    records=evidence()
    dest.mkdir(parents=True)
    save(dest/'functional_link.json',{'baseline_commit':characterization.BASELINE_COMMIT,'runs':records})
    # Reuse RUN16's exact-line upstream style annotation procedure, not its old functional runner.
    spec=importlib.util.spec_from_file_location('run16_source_preparation',ref/'scripts/asic_project.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    sources=['rtl/sobel_core.v','rtl/sobel_mmio.v','rtl/sobel_tile.v','rtl/native_bus_arbiter.v',
             'candidate/sobel_tile_v2.v','candidate/picorv32_sobel_soc_m3.v','third_party/picorv32/picorv32.v']
    module.SOURCES=sources
    for name in sources:
        p=dest/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,p)
    (dest/'scripts').mkdir()
    shutil.copy2(ref/'scripts/upstream_lint_review.json',dest/'scripts/upstream_lint_review.json')
    module.prepare_sources(dest)
    # Explicit unsigned zero extension; the Verilog equality already performs it.
    tile=dest/'build/asic_sources/sobel_tile_v2.v'
    text=tile.read_text();before=sha(tile);edits=[]
    for old,new in (("sx==extent[15:0]+16'd1","{9'd0,sx}==extent[15:0]+16'd1"),
                    ("sy==extent[31:16]+16'd1","{9'd0,sy}==extent[31:16]+16'd1")):
        if text.count(old)!=1:raise ValueError('Unexpected H2 comparison expression')
        text=text.replace(old,new);edits.append({'old':old,'new':new})
    tile.write_text(text)
    save(dest/'h2_width_derivation.json',{'original_physical_sha256':before,'derived_sha256':sha(tile),
         'edits':edits,'justification':'Unsigned EQ zero-extends 7-bit LHS to 16 bits; explicit concat preserves 4-state semantics. Not a whole-design formal proof.'})
    provenance_path=dest/'build/asic_sources/provenance.json'
    provenance=json.loads(provenance_path.read_text())
    provenance['candidate/sobel_tile_v2.v']['physical_sha256']=sha(tile)
    provenance['candidate/sobel_tile_v2.v']['width_derivation']='h2_width_derivation.json'
    save(provenance_path,provenance)
    shutil.copytree(ref/'scripts',dest/'flow')
    for name in ('constraints.sdc','pin_order.cfg'):
        shutil.copy2(ref/name,dest/name)
    raw=(ROOT/'candidate/picorv32_sobel_soc_m3.v').read_text()
    match=re.search(r'module\s+picorv32_sobel_soc_m3\s*#\(.*?\)\s*\((.*?)\);',raw,re.S)
    if not match:raise ValueError('Cannot extract tested port declaration')
    ports=('clk','resetn','trap','ext_valid','ext_instr','ext_addr','ext_wdata','ext_wstrb','ext_ready','ext_rdata')
    wrapper='`default_nettype none\nmodule picorv32_image_ppa ('+match[1]+');\n'
    configs={}
    for variant,version in (('h1',1),('h2',2)):
        text=wrapper+f'picorv32_sobel_soc_m3 #(.ENABLE_SOBEL(1),.DMA_VERSION({version})) soc (\n'
        text+=',\n'.join(f'    .{p}({p})' for p in ports)+'\n);\nendmodule\n`default_nettype wire\n'
        (dest/f'{variant}_top.v').write_text(text)
        cfg=json.loads((ref/'config.json').read_text())
        cfg['DESIGN_NAME']='picorv32_image_ppa'
        cfg['SYNTH_PARAMETERS']=[]  # Literal wrapper parameters also bind the OpenLane linter.
        cfg['VERILOG_FILES']=['/design/build/asic_sources/'+Path(s).name for s in sources]+[f'/design/{variant}_top.v']
        for key,name in (('PNR_SDC_FILE','constraints.sdc'),('SIGNOFF_SDC_FILE','constraints.sdc'),('FP_PIN_ORDER_CFG','pin_order.cfg')):
            cfg[key]='/design/'+name
        save(dest/f'config_{variant}.json',cfg);configs[variant]=cfg
    a,b=(dict(configs[x]) for x in ('h1','h2'))
    a.pop('VERILOG_FILES');b.pop('VERILOG_FILES')
    if a!=b:raise ValueError('H1/H2 physical conditions differ')
    for name in ('check_ppa.py','prepare_ppa.py','ppa.py','collect_ppa.py'):
        shutil.copy2(ROOT/'physical'/name,dest/name)
    save(dest/'physical_scope.json',{'top':'picorv32_image_ppa','included':['PicoRV32','legacy Sobel MMIO','one tile DMA engine','Sobel core(s)','arbiter','H2 local line buffers when DMA_VERSION=2'],
          'excluded':['program/frame RAM','memory-controller implementation','pads/package','camera/display'],
          'wrapper':'combinational port forwarding only, DMA_VERSION fixed to 1 or 2',
          'clock_ns':50,'power':'vectorless estimate; NOT workload energy','IR':'inherited source/load assumptions; no real pad/package model',
          'reference':origin,'note':'Both variants use the same RUN16 physical methodology; new runs required. RUN16 is not H2 PPA.'})
    save(dest/'snapshot_sha256.json',{p.relative_to(dest).as_posix():sha(p) for p in sorted(dest.rglob('*')) if p.is_file()})
    print('PPA INPUTS PREPARED:',dest,'; no synthesis/physical execution',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination',type=Path)
    prepare(p.parse_args().destination.resolve())
