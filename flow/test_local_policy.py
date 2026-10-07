"""Synthetic mutation regression of RUN12 lock/restore and rejection paths."""
import json,tempfile
from pathlib import Path
from types import SimpleNamespace
import electrical_eco_legacy as e
import local_pilot as lp
import test_electrical_mock as f

original_odb=e.odb;original_seed=lp.seed_plan
e.odb=SimpleNamespace(dbInst=SimpleNamespace(create=f.instcreate),dbNet=SimpleNamespace(create=f.netcreate),dbWire=SimpleNamespace(destroy=lambda w:None))
try:
 b=f.Block();n=f.netcreate(b,'signal');driver=f.instcreate(b,b.findMaster(e.MASTER),'driver');driver.findITerm('X').connect(n)
 for pg in e.PG:driver.findITerm(pg).connect(f.netcreate(b,pg))
 for j in range(2):
  i=f.instcreate(b,b.findMaster(e.MASTER),'load'+str(j));i.setLocation(30000+j*10000,0);i.findITerm('A').connect(n)
 rows=e.plan(b,['driver/X'])
 proposal=dict(seeds={v['buffer']:dict(xy=v['xy'],orient='R0') for r in rows for v in r['branches']},movable_original=['load0'],locked_original=['driver','load1'],drivers=['driver'])
 lp.seed_plan=lambda block,rs:proposal
 with tempfile.TemporaryDirectory() as tmp:
  p=Path(tmp);pins=p/'pins.json';plan=p/'plan.json';ref=p/'reference.json'
  pins.write_text(json.dumps(['driver/X']));plan.write_text(json.dumps(rows))
  lp.run(b,'insert',ref,plan,pins)
  root=b.findInst(rows[0]['branches'][0]['buffer'])
  assert root.isFixed() and driver.isFixed() and b.findInst('load1').isFixed() and not b.findInst('load0').isFixed()
  driver.setLocation(1,0);f.fail(lambda:lp.run(b,'cleanup',ref,plan,pins));driver.setLocation(0,0)
  xy=root.getLocation()[:];root.setLocation(xy[0]+1,xy[1]);f.fail(lambda:lp.run(b,'cleanup',ref,plan,pins));root.setLocation(*xy)
  load=b.findInst('load0');xy=load.getLocation()[:];load.setLocation(xy[0]+13000,xy[1]);f.fail(lambda:lp.run(b,'cleanup',ref,plan,pins))
  report=json.loads((p/'site_geometry_report.json').read_text());assert any(x['kind']=='axis_displacement' for x in report['errors'])
  load.setLocation(xy[0]+1000,xy[1]);lp.run(b,'cleanup',ref,plan,pins)
  assert not driver.isFixed() and not root.isFixed() and not b.findInst('load1').isFixed()
  assert json.loads((p/'site_geometry_report.json').read_text())['status']=='H3_SITE_GEOMETRY_PASS'
finally:e.odb=original_odb;lp.seed_plan=original_seed
print('LOCAL POLICY SYNTHETIC PASS: source/root/nonlocal locks, axis rejection, restore, dirty-net cleanup')
