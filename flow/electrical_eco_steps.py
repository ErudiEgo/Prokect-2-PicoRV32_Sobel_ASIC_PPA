from pathlib import Path
from openlane.steps import Step,OdbpyStep
from antenna_closure import AntennaClosure,VerifyAntennaTopology,GlobalRouting,DetailedRouting,OutputBufferEco,DetailedPlacement
class RouteGuard(VerifyAntennaTopology):
 id='H3.RouteGuard'
 mode='input'
 def get_script_path(self):return str(Path(__file__).with_name('route_guard_cli.py'))
 def get_command(self):
  cell,pin=self.config['DIODE_CELL'].split('/')
  return super().get_command()+['--report',str(Path(self.step_dir)/'route_guard_report.json'),'--mode',self.mode,'--diode-cell',cell,'--diode-pin',pin]
class FreshAccessGlobalRouting(GlobalRouting):
 id='H3.FreshAccessGlobalRouting'
 def get_script_path(self):return str(Path(__file__).with_name('fresh_access_grt.tcl'))
class CapacityCheck(DetailedPlacement):
 id='H3.CapacityCheck'
 def get_script_path(self):return str(Path(__file__).with_name('capacity_check.tcl'))
class ElectricalEco(OutputBufferEco):
 id='H3.ElectricalEco'
 def get_script_path(self):return str(Path(__file__).with_name('electrical_eco_cli.py'))
class CleanElectrical(ElectricalEco):
 id='H3.CleanElectrical'
 def get_command(self):return super().get_command()+['--mode','cleanup']
@Step.factory.register()
class ElectricalAntennaClosure(AntennaClosure):
 id='H3.ElectricalAntennaClosure'
 name='Two-Net RUN17 Electrical Repair (max two DRT calls)'
 Steps=[ElectricalEco,CapacityCheck,CleanElectrical,RouteGuard,FreshAccessGlobalRouting,DetailedRouting,RouteGuard]+AntennaClosure.Steps
 def run(self,state_in,**kwargs):
  if self.config['SOBEL_OUTPUT_BUFFER_REPAIR'] or not self.config['SOBEL_NATIVE_ANTENNA_REPAIR']:raise ValueError('Unreviewed routing continuation configuration')
  state=state_in;folder=Path(self.step_dir)/'electrical_eco';folder.mkdir(parents=True,exist_ok=True)
  reference=str(folder/'reference.json')
  for cls,name in [(ElectricalEco,'01-insert'),(CapacityCheck,'02-native-check'),(CleanElectrical,'03-clean-wires')]:
   options={'SOBEL_TOPOLOGY_REFERENCE':reference} if issubclass(cls,ElectricalEco) else {}
   state=cls(self.config,state,**options).start(toolbox=self.toolbox,step_dir=str(folder/name),_no_rule=True)
  def guard(mode,name):
   nonlocal state
   step=RouteGuard(self.config,state,SOBEL_TOPOLOGY_REFERENCE=reference);step.mode=mode
   state=step.start(toolbox=self.toolbox,step_dir=str(folder/name),_no_rule=True)
  guard('input','01-input-guard')
  for cls,name in [(FreshAccessGlobalRouting,'02-global-route'),(DetailedRouting,'03-detailed-route')]:
   state=cls(self.config,state).start(toolbox=self.toolbox,step_dir=str(folder/name),_no_rule=True)
  guard('routed','04-route-guard')
  views,metrics=super().run(state,**kwargs)
  from openlane.state import State
  state=State(state,overrides=views,metrics={**state.metrics,**metrics})
  guard('antenna','05-final-guard')
  return ({fmt:state[fmt] for fmt in self.outputs if state.get(fmt)!=state_in.get(fmt)},dict(state.metrics))
ElectricalAntennaClosure.config_vars=list(AntennaClosure.config_vars)
