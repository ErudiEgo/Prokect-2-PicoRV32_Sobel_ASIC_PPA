"""Exercise production insertion/cleanup with mocks that reject moves while LOCKED."""
import sys,json,tempfile
from pathlib import Path
from types import SimpleNamespace
import electrical_eco_legacy as old
import capacity_pilot as cp
saved=sys.modules.get('electrical_eco');sys.modules['electrical_eco']=old
try:import test_electrical_mock as fixture
finally:
 if saved is None:sys.modules.pop('electrical_eco',None)
 else:sys.modules['electrical_eco']=saved
saved_odb=old.odb;saved_geometry=cp.complete_geometry;saved_set=fixture.Inst.setLocation
def strict_set(self,*xy):
 if self.isFixed():raise RuntimeError('ODB-0359: mock rejects move while LOCKED')
 return saved_set(self,*xy)
fixture.Inst.setLocation=strict_set
old.odb=SimpleNamespace(dbInst=SimpleNamespace(create=fixture.instcreate),dbNet=SimpleNamespace(create=fixture.netcreate),dbWire=SimpleNamespace(destroy=lambda w:None))
try:
 b=fixture.Block();net=fixture.netcreate(b,'signal');driver=fixture.instcreate(b,b.findMaster(old.MASTER),'driver');driver.setLocation(1000,0);driver.findITerm('X').connect(net)
 for pg in old.PG:driver.findITerm(pg).connect(fixture.netcreate(b,pg))
 load=fixture.instcreate(b,b.findMaster(old.MASTER),'load');load.setLocation(30000,0);load.findITerm('A').connect(net)
 geom=dict(dbu=1000,rows=[dict(origin=[0,0],spacing=1000,count=100,site=[1000,1000],direction='HORIZONTAL',orient='R0')],blockages=[],masters={n:[1000,1000] for n in (old.MASTER,old.ROOT_MASTER)},instances=[dict(name=i.getName(),master=old.MASTER,xy=list(i.getLocation()),bbox=[i.getLocation()[0],0,i.getLocation()[0]+1000,1000],orient='R0',fixed=False,status='PLACED') for i in (driver,load)])
 cp.complete_geometry=lambda block:geom
 rows=old.plan(b,['driver/X']);assert len(rows[0]['branches'])==2
 names=[n['buffer'] for n in rows[0]['branches']]
 witness=dict(status='ROW_CAPACITY_WITNESS',unplaced=[],new_buffers={names[0]:dict(xy=[3000,0],orient='R0'),names[1]:dict(xy=[25000,0],orient='R0')},original_moves={'load':dict(xy=[29000,0],orient='R0')})
 with tempfile.TemporaryDirectory() as tmp:
  p=Path(tmp);plan=p/'eco_plan.json';pins=p/'eco_pins.json';ref=p/'reference.json'
  plan.write_text(json.dumps(rows));pins.write_text(json.dumps(['driver/X']))
  (p/'capacity_witness.json').write_text(json.dumps(witness));(p/'padding_config.json').write_text(json.dumps(dict(DPL_CELL_PADDING=0,CELL_PAD_EXCLUDE=[],DIODE_PADDING=None,DIODE_CELL='unused/DIODE')))
  cp.run(b,'insert',ref,plan,pins)
  assert load.getLocation()==[29000,0] and all(i.isFixed() for i in b.getInsts())
  # Old RUN13 sequence must be rejected by this fixture.
  try:load.setLocation(28000,0)
  except RuntimeError:pass
  else:raise AssertionError('Fixture failed to enforce native lock semantics')
  state=json.loads(ref.read_text());assert state['capacity_expected_positions']['load']==[29000,0,'R0']
  # No native physical check is run here; only production cleanup logic is exercised.
  cp.run(b,'cleanup',ref,plan,pins)
  assert all(not i.isFixed() for i in b.getInsts())
  assert load.getLocation()==[29000,0] and not net.getGuides()
  assert all(not b.findNet(n['net']).getGuides() for n in rows[0]['branches'])
  assert b.findNet('VPWR').getGuides()==['stale']
  assert json.loads((p/'site_geometry_report.json').read_text())['status']=='H3_SITE_GEOMETRY_PASS'
finally:
 old.odb=saved_odb;cp.complete_geometry=saved_geometry;fixture.Inst.setLocation=saved_set
print('CAPACITY PRODUCTION APPLY/CLEANUP MOCK PASS; strict LOCKED setters; real checkpoint untouched; native physical check NOT_RUN')
