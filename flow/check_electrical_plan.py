"""Exact checkpoint read-only validation and intentional corruption tests."""
import json,os,copy
from pathlib import Path
import odb
import electrical_eco_legacy as old
from capacity_pilot import run,complete_geometry
from verify_capacity import verify
state=json.loads(Path(os.environ['ECO_STATE']).read_text());db=odb.dbDatabase.create();odb.read_db(db,state['odb']);block=db.getChip().getBlock()
before=old.capture_original(block);positions=old.positions(block)
run(block,'insert','/tmp/unused_reference.json','/design/eco_plan.json','/design/eco_pins.json',True)
data=complete_geometry(block);cfg=json.loads(Path('/design/padding_config.json').read_text());plan=json.loads(Path('/design/eco_plan.json').read_text());w=json.loads(Path('/design/capacity_witness.json').read_text())
def reject(candidate):
 try:verify(data,cfg,plan,candidate)
 except ValueError:return
 raise AssertionError('Corrupt capacity witness accepted')
bad=copy.deepcopy(w);names=list(bad['new_buffers']);bad['new_buffers'][names[1]]=bad['new_buffers'][names[0]];reject(bad)
bad=copy.deepcopy(w);bad['new_buffers'][names[0]]['xy'][0]+=1;reject(bad)
bad=copy.deepcopy(w);name=next(iter(bad['original_moves']));bad['original_moves'][name]['xy'][0]+=13000;reject(bad)
bad=copy.deepcopy(w);driver=plan[0]['driver'].rsplit('/',1)[0];obj=block.findInst(driver);bad['original_moves'][driver]=dict(xy=[obj.getLocation()[0]+460,obj.getLocation()[1]],orient=str(obj.getOrient()));reject(bad)
import test_lock_api
old.verify_original(block,before);assert old.positions(block)==positions
print('ECO READ ONLY CHECK PASS; joint occupancy, padding, movement, root/branch bounds, corruption rejection; no native placement/STA')

import test_certified_move_api
import test_capacity_apply_mock
import test_retained_split
