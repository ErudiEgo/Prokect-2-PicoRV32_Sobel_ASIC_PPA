"""Mock physical child execution. Runs no placement, routing or STA."""
import sys,tempfile,json
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,'/design/flow')
from openlane.flows.classic import Classic
from openlane.state import State,DesignFormat
import electrical_eco_steps as module
import c40_monolithic_steps  # register RUN305 substitution
raw=json.loads(Path('/design/config.json').read_text())
flow=Classic.Substitute(raw['meta']['substituting_steps'])('/design/config.json',design_dir='/design',pdk_root='/pdk',pdk='sky130A')
with tempfile.TemporaryDirectory() as temp:
 state=State({DesignFormat.ODB:'/initial.odb'},metrics={'starting':1})
 step=module.ElectricalAntennaClosure(flow.config,state);step.step_dir=temp;step.toolbox=None
 calls=[]
 def fake_start(self,**kwargs):
  calls.append((self.id,getattr(self,'mode',None)))
  if isinstance(self,module.RouteGuard):
   self.step_dir=kwargs['step_dir'];cmd=self.get_command()
   assert cmd[cmd.index('--report')+1]==str(Path(self.step_dir)/'route_guard_report.json')
  return State(state,overrides={DesignFormat.ODB:'/child.odb'},metrics={'starting':1,'new_metric':7})
 def fake_antenna(self,entered,**kwargs):
  assert str(entered[DesignFormat.ODB])=='/child.odb'
  calls.append(('native-antenna',None))
  return {DesignFormat.ODB:'/antenna.odb'},{'antenna__violating__nets':0}
 with patch.object(module.ElectricalEco,'start',fake_start),patch.object(module.CapacityCheck,'start',fake_start),patch.object(module.CleanElectrical,'start',fake_start),patch.object(module.RouteGuard,'start',fake_start),patch.object(module.FreshAccessGlobalRouting,'start',fake_start),patch.object(module.DetailedRouting,'start',fake_start),patch.object(module.AntennaClosure,'run',fake_antenna):
  views,metrics=step.run(state)
 assert calls==[('H3.ElectricalEco',None),('H3.CapacityCheck',None),('H3.CleanElectrical',None),('H3.RouteGuard','input'),('H3.FreshAccessGlobalRouting',None),('OpenROAD.DetailedRouting',None),('H3.RouteGuard','routed'),('native-antenna',None),('H3.RouteGuard','antenna')],calls
 assert metrics['new_metric']==7
 print('BATCH16 SEQUENCE MOCK PASS; no physical child executed')
