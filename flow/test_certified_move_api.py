"""Test production move helper on a small synthetic OpenDB, not a design checkpoint."""
import odb
from certified_move import move_and_relock
db=odb.dbDatabase.create();tech=odb.dbTech.create(db,'move_test_tech');lib=odb.dbLib.create(db,'move_test_lib',tech)
master=odb.dbMaster.create(lib,'move_test_cell');master.setType('CORE');master.setWidth(2760);master.setHeight(2720);master.setFrozen()
chip=odb.dbChip.create(db);block=odb.dbBlock.create(chip,'move_test_block')
for name,start,end in [('_39033_',781540,780160),('fanout1960',786600,785220)]:
 inst=odb.dbInst.create(block,master,name);inst.setOrient('R0');inst.setLocation(start,527680);inst.setPlacementStatus('LOCKED')
 move_and_relock(inst,[end,527680],'PLACED')
 assert list(inst.getLocation())==[end,527680] and inst.isFixed() and str(inst.getPlacementStatus())=='LOCKED'
 try:move_and_relock(inst,[start,527680],'LOCKED')
 except ValueError:pass
 else:raise AssertionError('Originally fixed cell accepted')
 assert list(inst.getLocation())==[end,527680] and inst.isFixed()
class FailingCell:
 status='LOCKED'
 def getPlacementStatus(self):return self.status
 def isFixed(self):return self.status=='LOCKED'
 def getOrient(self):return 'R0'
 def setPlacementStatus(self,v):self.status=v
 def setLocation(self,*xy):
  assert not self.isFixed()
  raise RuntimeError('injected setter failure')
cell=FailingCell()
try:move_and_relock(cell,[0,0],'PLACED')
except RuntimeError:pass
else:raise AssertionError('Injected failure swallowed')
assert cell.isFixed()
print('NATIVE CERTIFIED MOVE API PASS: unlock/move/relock for both moves; fixed rejection; exception relock. Synthetic database only.')
