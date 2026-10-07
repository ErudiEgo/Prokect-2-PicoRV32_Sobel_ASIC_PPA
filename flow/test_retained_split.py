"""Synthetic split regression; never edits a physical database."""
import sys,json,tempfile,copy
from pathlib import Path
from types import SimpleNamespace
import electrical_eco_legacy as e
sys.modules['electrical_eco']=e
import test_electrical_mock as f
saved=e.odb
e.odb=SimpleNamespace(dbInst=SimpleNamespace(create=f.instcreate),dbNet=SimpleNamespace(create=f.netcreate),dbWire=SimpleNamespace(destroy=lambda w:None))
try:
 b=f.Block();n=f.netcreate(b,'net1278');driver=f.instcreate(b,b.findMaster(e.MASTER),'fanout1278');driver.findITerm('X').connect(n)
 for pg in e.PG:driver.findITerm(pg).connect(f.netcreate(b,pg))
 for i in range(8):
  c=f.instcreate(b,b.findMaster(e.MASTER),'logic'+str(i));c.setLocation(30000+i*5000,30000);c.findITerm('A').connect(n)
 dm=f.Master('sky130_fd_sc_hd__diode_2');dm.pins={'DIODE':f.Pin('DIODE','INOUT')};b.masters[dm.name]=dm
 for i in range(5):
  c=f.instcreate(b,dm,'ANTENNA_'+str(i));c.findITerm('DIODE').connect(n)
 pins=[e.pinname(t) for t in n.getITerms() if not t.isOutputSignal()]
 rows=e.plan(b,['fanout1278/X']);r=rows[0]
 assert len(r['retained_loads'])==9
 assert all('ANTENNA_'+str(i)+'/DIODE' in r['retained_loads'] for i in range(5))
 bad=copy.deepcopy(r);bad['retained_loads'].pop();f.fail(lambda:e.validate_tree(bad,pins))
 with tempfile.TemporaryDirectory() as tmp:
  p=Path(tmp);(p/'plan').write_text(json.dumps(rows));(p/'pins').write_text(json.dumps(['fanout1278/X']))
  e.run(b,'insert',p/'ref',p/'plan',p/'pins')
  assert len([t for t in n.getITerms() if not t.isOutputSignal()])==10
  assert all(b.findInst('ANTENNA_'+str(i)).findITerm('DIODE').getNet() is n for i in range(5))
  for i in range(8):
   net=b.findInst('logic'+str(i)).findITerm('A').getNet();seen=set()
   while net is not n:
    assert net.getName() not in seen;seen.add(net.getName())
    outputs=[t for t in net.getITerms() if t.isOutputSignal()];assert len(outputs)==1
    c=outputs[0].getInst();assert c.getMaster().getName() in (e.MASTER,e.ROOT_MASTER)
    net=c.findITerm('A').getNet()
  e.run(b,'cleanup',p/'ref',p/'plan',p/'pins')
  b.findInst('ANTENNA_0').findITerm('DIODE').connect(b.findNet(r['branches'][0]['net']))
  f.fail(lambda:e.run(b,'verify',p/'ref',p/'plan',p/'pins'))
finally:e.odb=saved
print('RETAINED SPLIT MOCK PASS: fanout10, five diodes retained, identity paths and corruption rejection')
