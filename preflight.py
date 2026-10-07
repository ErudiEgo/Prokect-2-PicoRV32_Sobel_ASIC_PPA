from pathlib import Path
import json,subprocess,sys
from openlane.flows.classic import Classic
root=Path('/design');out=Path('/audit')
sys.path.insert(0,str(root/'flow'))
import antenna_closure
import electrical_eco_steps
import c40_monolithic_steps
assert [s.id for s in electrical_eco_steps.ElectricalAntennaClosure.Steps]==['H3.ElectricalEco','H3.CapacityCheck','H3.CleanElectrical','H3.RouteGuard','H3.FreshAccessGlobalRouting','OpenROAD.DetailedRouting','H3.RouteGuard']+[s.id for s in antenna_closure.AntennaClosure.Steps]

raw=json.loads((root/'config.json').read_text())
f=Classic.Substitute(raw['meta']['substituting_steps'])(str(root/'config.json'),design_dir=str(root),pdk_root='/pdk',pdk='sky130A')
assert len(f.Steps)==79
ids=[s.id for s in f.Steps]
assert ids.count('H3.C40GuidedRejoin')==1
assert ids.count('Sobel.AntennaClosure')==1
assert ids.index('H3.C40GuidedRejoin') < ids.index('OpenROAD.DetailedRouting')
from openlane.common import Path as OLPath
from openlane.state import DesignFormat,State
probe=State({DesignFormat.ODB:OLPath('/design/guidance/stage43_expected.odb')},metrics={})
probe=State(probe,overrides=c40_monolithic_steps.odb_view_update('/design/guidance/final_topology_placement.odb'),metrics={})
assert isinstance(probe[DesignFormat.ODB],OLPath)
print('C40_OPENLANE_PATH_STATE_PASS')
assert f.config['PL_MAX_DISPLACEMENT_X']==12 and f.config['PL_MAX_DISPLACEMENT_Y']==12
assert f.config['PL_OPTIMIZE_MIRRORING'] is False
assert 'OpenROAD.STAPostPNR' in [step.id for step in f.Steps]

(out/'resolved.json').write_text(json.dumps(dict(f.config),indent=2,default=str));(out/'steps.json').write_text(json.dumps([s.id for s in f.Steps],indent=2))
args=['verilator','--lint-only','--Wall','--Wno-DECLFILENAME','--Wno-EOFNEWLINE','--Werror-LATCH','--top-module','picorv32_h3_logic_ppa',*map(str,f.config['VERILOG_FILES'])]
p=subprocess.run(args,text=True,capture_output=True);(out/'lint.log').write_text(p.stdout+p.stderr);print(p.stdout+p.stderr);print('LINT_EXIT',p.returncode,'STEPS',len(f.Steps))

if p.returncode:raise RuntimeError('Lint failed')
lib=next(iter(f.config['LIB'].values()))[0];tech=next(iter(f.config['TECH_LEFS'].values()))
lines=[f'read_lef {{{tech}}}',f'read_liberty {{{lib}}}','read_verilog /design/ports_only.v','link_design picorv32_h3_logic_ppa']
for key in ('CLOCK_PERIOD','OUTPUT_CAP_LOAD','MAX_FANOUT_CONSTRAINT','MAX_TRANSITION_CONSTRAINT','MAX_CAPACITANCE_CONSTRAINT'):lines.append(f'set ::env({key}) {f.config[key]}')
lines+=['read_sdc /design/constraints.sdc','puts {H3 SDC PORT LOAD PASS}','exit']
(out/'sdc.tcl').write_text('\n'.join(lines)+'\n')
p=subprocess.run(['openroad','-exit',str(out/'sdc.tcl')],text=True,capture_output=True);(out/'sdc.log').write_text(p.stdout+p.stderr)
if p.returncode or 'H3 SDC PORT LOAD PASS' not in p.stdout or '[ERROR' in p.stdout+p.stderr:raise RuntimeError('SDC load failed')
import os,hashlib
for name in ['test_repair_api.py','test_fanout_env.py','test_antenna_targets.py']:
 cmd=[sys.executable,str(root/'flow'/name)]
 if name=='test_fanout_env.py':cmd.append(str(out/'fanout_env'))
 q=subprocess.run(cmd,capture_output=True,text=True);(out/(name+'.log')).write_text(q.stdout+q.stderr);q.check_returncode()
q=subprocess.run(['openroad','-exit',str(root/'flow/test_fanout_policy.tcl')],capture_output=True,text=True,env=dict(os.environ,SOBEL_SCRIPT_DIR=str(root/'flow')))
(out/'fanout_policy.log').write_text(q.stdout+q.stderr);q.check_returncode()
if 'FANOUT' not in q.stdout or '[ERROR' in q.stdout+q.stderr:raise RuntimeError('fanout policy check failed')
pdk={}
def record(v):
 if isinstance(v,dict):
  for x in v.values():record(x)
 elif isinstance(v,list):
  for x in v:record(x)
 elif isinstance(v,str) and v.startswith('/pdk/') and Path(v).is_file():
  with Path(v).open('rb') as f:pdk[v]=hashlib.file_digest(f,'sha256').hexdigest()
record(json.loads((out/'resolved.json').read_text()));assert pdk
(out/'pdk_files_sha256.json').write_text(json.dumps(pdk,indent=2))
# Confirm the exact pinned buffer implements X=A in each timing library.
import gzip,re
checked=[]
for libpath in sorted({str(p) for libs in f.config['LIB'].values() for p in libs}):
 op=gzip.open if libpath.endswith('.gz') else open
 with op(libpath,'rt') as stream:libtext=stream.read()
 match=re.search(r'cell\s*\(\s*"?sky130_fd_sc_hd__buf_8"?\s*\)\s*\{',libtext)
 if not match:raise ValueError('buf_8 absent in '+libpath)
 start=match.end();depth=1;end=start
 while depth and end<len(libtext):
  depth+=(libtext[end]=='{')-(libtext[end]=='}');end+=1
 cell=libtext[start:end]
 if re.findall(r'(?<![A-Za-z_])function\s*:\s*"([^"]+)"\s*;',cell) not in (['A'],['(A)']):raise ValueError('buf_8 identity function missing '+libpath)
 checked.append(libpath)
(out/'buffer_identity.json').write_text(json.dumps({'cell':'sky130_fd_sc_hd__buf_8','function':'A','libraries':checked},indent=2))
q=subprocess.run(['openroad','-exit','/design/flow/test_fresh_access.tcl'],capture_output=True,text=True)
(out/'fresh_access_mock.log').write_text(q.stdout+q.stderr);q.check_returncode()
if 'FRESH ACCESS ORDER MOCK PASS' not in q.stdout or '[ERROR' in q.stdout+q.stderr:raise ValueError('Pin access order check failed')
(out/'PASS.json').write_text(json.dumps({'status':'H3_LOGIC_STATIC_PREFLIGHT_PASS','steps':len(f.Steps),'limits':'Config/lint/port-only SDC; no synthesis, timing or physical run. Seven reviewed H3 warnings plus inherited CPU exceptions; RAM/UART excluded.'},indent=2))
print('H3 LOGIC STATIC PREFLIGHT PASS; ASIC NOT_RUN')


subprocess.run([sys.executable,str(root/'flow/check_identity_libs.py')],check=True)

expected=json.loads((root/"padding_config.json").read_text())
for k,v in expected.items():
 assert str(f.config[k])==str(v) or f.config[k]==v,(k,f.config[k],v)

subprocess.run([sys.executable,str(root/'flow/test_batch_sequence.py')],check=True)

assert f.config['SOBEL_ANTENNA_REPAIR_ROUNDS']==3
subprocess.run([sys.executable,str(root/'flow/test_antenna_budget.py')],check=True)
