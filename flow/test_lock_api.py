"""Check placement-status semantics on a new empty synthetic database."""
import odb
db = odb.dbDatabase.create()
tech = odb.dbTech.create(db, 'test_tech')
lib = odb.dbLib.create(db, 'test_lib', tech)
master = odb.dbMaster.create(lib, 'test_buffer')
master.setType('CORE')
master.setFrozen()
chip = odb.dbChip.create(db)
block = odb.dbBlock.create(chip, 'test_block')
inst = odb.dbInst.create(block, master, 'test_inst')
inst.setPlacementStatus('PLACED')
assert not inst.isFixed()
inst.setPlacementStatus('LOCKED')
assert inst.isFixed() and str(inst.getPlacementStatus()) == 'LOCKED'
inst.setPlacementStatus('PLACED')
assert not inst.isFixed()
print('NATIVE LOCK/RESTORE API PASS on empty synthetic database; real checkpoint unmodified')
