"""Mock actual antenna controller termination; no physical steps executed."""
import sys,json,tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,'/design/flow')
from openlane.flows.classic import Classic
from openlane.state import State
import antenna_closure as a
import electrical_eco_steps
import c40_monolithic_steps  # register RUN305 substitution
raw=json.loads(Path('/design/config.json').read_text())
flow=Classic.Substitute(raw['meta']['substituting_steps'])('/design/config.json',design_dir='/design',pdk_root='/pdk',pdk='sky130A')
assert flow.config['SOBEL_ANTENNA_REPAIR_ROUNDS']==3
for counts,expected_routes in [([1,1,1,1],3),([1,0],1),([0],0)]:
 with tempfile.TemporaryDirectory() as temp:
  initial=State(metrics={});state=initial;calls=[];pending=list(counts)
  step=a.AntennaClosure(flow.config,initial);step.step_dir=temp;step.toolbox=None
  def fake_start(self,**kwargs):
   global state
   self.step_dir=kwargs['step_dir'];calls.append(self.id)
   if isinstance(self,a.CheckAntennas):
    n=pending.pop(0);folder=Path(self.step_dir)/'reports';folder.mkdir(parents=True)
    (folder/'antenna.rpt').write_text('mock only')
    state=State(metrics={'antenna__violating__nets':n,'antenna__violating__pins':n})
   return state
  with patch.object(a.CheckAntennas,'start',fake_start),patch.object(a.CaptureAntennaTopology,'start',fake_start),patch.object(a.NativeAntennaRepair,'start',fake_start),patch.object(a.DetailedRouting,'start',fake_start),patch.object(a.VerifyNativeTopology,'start',fake_start),patch.object(a,'checked_targets',lambda text,n,p:['mock/pin'] if n else []):
   views,metrics=step.run(initial)
  assert not pending
  assert calls.count('OpenROAD.DetailedRouting')==expected_routes,calls
  assert metrics['antenna__violating__nets']==counts[-1],metrics
  assert len(json.loads((Path(temp)/'closure_history.json').read_text()))==len(counts)
print('ANTENNA BUDGET MOCK PASS; at most three repair DRTs; unresolved violations retained, no physical execution')
