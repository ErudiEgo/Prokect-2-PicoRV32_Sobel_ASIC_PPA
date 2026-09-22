"""Container-only config/lint/SDC preflight. Never invokes Flow.start or Step.start."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'flow'))
import antenna_closure  # Registration only: inherited exact RUN16 extensions.
from openlane.flows.classic import Classic

def save(path,obj):path.write_text(json.dumps(obj,indent=2,default=str)+'\n')
def run(args,path):
    p=subprocess.run(args,capture_output=True,text=True,env=(dict(os.environ,SOBEL_SCRIPT_DIR=str(ROOT/'flow')) if args[0]=='openroad' else None))
    path.write_text(p.stdout+p.stderr)
    print(p.stdout+p.stderr,flush=True)
    p.check_returncode()
    return p.stdout+p.stderr

def main(out):
    hashes=json.loads((ROOT/'snapshot_sha256.json').read_text())
    for name,digest in hashes.items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:raise ValueError('Snapshot changed: '+name)
    version=subprocess.check_output([sys.executable,'-m','openlane','--version'],text=True).splitlines()[0]
    if version!='OpenLane v2.3.10':raise ValueError('Unexpected OpenLane revision')
    configs={}
    pdk_files={}
    def record_pdk(value):
        if isinstance(value,dict):
            for item in value.values(): record_pdk(item)
        elif isinstance(value,(list,tuple)):
            for item in value: record_pdk(item)
        elif isinstance(value,str) and value.startswith('/pdk/') and value not in pdk_files and Path(value).is_file():
            with Path(value).open('rb') as f: pdk_files[value]=hashlib.file_digest(f,'sha256').hexdigest()
    for variant in ('h1','h2'):
        dest=out/variant;dest.mkdir()
        path=ROOT/f'config_{variant}.json';raw=json.loads(path.read_text())
        flow=Classic.Substitute(raw['meta']['substituting_steps'])(str(path),design_dir=str(ROOT),pdk_root='/pdk',pdk='sky130A')
        if len(Classic.Steps)!=78 or len(flow.Steps)!=81:raise ValueError('Unexpected physical step inventory')
        save(dest/'resolved_config.json',dict(flow.config))
        save(dest/'steps.json',[s.id for s in flow.Steps])
        args=['verilator','--lint-only','--Wall','--Wno-DECLFILENAME','--Wno-EOFNEWLINE','--Werror-LATCH','--top-module','picorv32_image_ppa',
              '+define+PDK_sky130A','+define+SCL_sky130_fd_sc_hd','+define+__openlane__','+define+__pnr__','+define+USE_POWER_PINS',*map(str,flow.config['VERILOG_FILES'])]
        save(dest/'lint_command.json',args)
        run(args,dest/'lint.log')
        text=(ROOT/f'{variant}_top.v').read_text()
        ports=re.search(r'module picorv32_image_ppa\s*\((.*?)\);',text,re.S).group(1)
        (dest/'ports_only.v').write_text('// SDC load fixture only, not synthesized hardware.\nmodule picorv32_image_ppa ('+ports+');\nendmodule\n')
        lib=next(iter(flow.config['LIB'].values()))[0];tech=next(iter(flow.config['TECH_LEFS'].values()))
        lines=[f'read_lef {{{tech}}}',f'read_liberty {{{lib}}}',f'read_verilog {{{dest/"ports_only.v"}}}','link_design picorv32_image_ppa']
        for key in ('CLOCK_PERIOD','OUTPUT_CAP_LOAD','MAX_FANOUT_CONSTRAINT','MAX_TRANSITION_CONSTRAINT','MAX_CAPACITANCE_CONSTRAINT'):
            lines.append(f'set ::env({key}) {flow.config[key]}')
        lines += [f'read_sdc {{{flow.config["PNR_SDC_FILE"]}}}','puts {SDC LOAD PASS: port-only; no STA/PPA results}','exit']
        (dest/'load_sdc.tcl').write_text('\n'.join(lines)+'\n')
        log=run(['openroad','-exit',str(dest/'load_sdc.tcl')],dest/'sdc_load.log')
        if 'SDC LOAD PASS:' not in log or re.search(r'\[ERROR|^Error',log,re.M):raise ValueError('SDC load failed')
        # Exercise installed multicorner cell lookup with a stubbed CTS engine.
        from openlane.common import TclUtils
        cells=[]
        corners=[(key.replace('*','nom'),paths) for key,paths in flow.config['LIB'].items()]
        cells.append('define_corners '+' '.join(corner for corner,_ in corners))
        for corner,paths in corners:
            for path in paths:cells.append(f'read_liberty -corner {corner} {{{path}}}')
        cells.append(f'read_lef {{{tech}}}')
        for path in flow.config['CELL_LEFS']:cells.append(f'read_lef {{{path}}}')
        cells += [f'read_verilog {{{dest/"ports_only.v"}}}','link_design picorv32_image_ppa']
        for key in ('CTS_CLK_BUFFERS','CTS_ROOT_BUFFER','SOBEL_CTS_FANOUT_TARGET','MAX_FANOUT_CONSTRAINT','CTS_DISTANCE_BETWEEN_BUFFERS','SOBEL_CTS_BRANCH_BUFFER_DISTANCE'):
            value=flow.config[key]
            value=TclUtils.join(value) if isinstance(value,list) else str(value)
            cells.append(TclUtils.join(['set',f'::env({key})',value]))
        cells += [f'source {{{ROOT/"flow/test_fanout_cells.tcl"}}}','exit']
        (dest/'fanout_cells.tcl').write_text('\n'.join(cells)+'\n')
        log=run(['openroad','-exit',str(dest/'fanout_cells.tcl')],dest/'fanout_cells.log')
        if 'FANOUT CELL REGRESSION PASS:' not in log:raise ValueError('Multicorner cell lookup failed')
        configs[variant]=dict(flow.config)
        record_pdk(json.loads(json.dumps(dict(flow.config),default=str)))
    diff={k for k in set(configs['h1'])|set(configs['h2']) if configs['h1'].get(k)!=configs['h2'].get(k)}
    if diff!={'VERILOG_FILES'}:raise ValueError('Unexpected resolved comparison differences: '+str(diff))
    if not pdk_files:raise ValueError('Empty PDK hash inventory')
    save(out/'pdk_files_sha256.json',pdk_files)
    run(['openroad','-exit',str(ROOT/'flow/test_fanout_policy.tcl')],out/'fanout_policy.log')
    run([sys.executable,str(ROOT/'flow/test_repair_api.py')],out/'repair_api.log')
    run([sys.executable,str(ROOT/'flow/test_fanout_env.py'),str(out/'fanout_env')],out/'fanout_env.log')
    save(out/'PASS.json',{'status':'PPA_PAIR_STATIC_PREFLIGHT_PASS','openlane':version,'variants':['h1','h2'],
         'limits':'Config/lint/port-only SDC loading only; no synthesis/PNR/STA measurement. ASIC NOT_RUN.'})
    print('PPA PAIR STATIC PREFLIGHT PASS; synthesis/physical flow NOT_RUN',flush=True)

if __name__=='__main__':main(Path(sys.argv[1]).resolve())
