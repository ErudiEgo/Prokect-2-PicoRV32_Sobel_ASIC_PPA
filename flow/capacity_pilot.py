"""Apply a verified simultaneous row assignment; native legality is a separate user step."""
import json
from pathlib import Path
import electrical_eco_legacy as old
from site_pilot import geometry
from verify_capacity import verify
from certified_move import move_and_relock

def complete_geometry(block):
 data=geometry(block)
 for i in data['instances']:
  obj=block.findInst(i['name']);i.update(xy=list(obj.getLocation()),orient=str(obj.getOrient()),status=str(obj.getPlacementStatus()))
 return data

def run(block,mode,reference,plan_file,pins_file,plan_only=False):
 ref=Path(reference);base=Path(plan_file).parent
 witness=json.loads((base/'capacity_witness.json').read_text());cfg=json.loads((base/'padding_config.json').read_text())
 if mode=='insert':
  rows=old.plan(block,json.loads(Path(pins_file).read_text()))
  if rows!=json.loads(Path(plan_file).read_text()):raise ValueError('Frozen batch tree mismatch')
  certificate=verify(complete_geometry(block),cfg,rows,witness)
  if plan_only:
   print('CAPACITY READ ONLY CHECK PASS',json.dumps(certificate));return
  if ref.exists():raise FileExistsError(ref)
  old.run(block,mode,reference,plan_file,pins_file,False)
  data=json.loads(ref.read_text());dirty=set(data['dirty_nets'])
  for name,v in witness['original_moves'].items():
   inst=block.findInst(name);move_and_relock(inst,v['xy'],data['statuses'][name])
   for t in inst.getITerms():
    net=t.getNet()
    if net is not None and not net.isSpecial():dirty.add(net.getName())
  for name,v in witness['new_buffers'].items():
   inst=block.findInst(name);inst.setOrient(v['orient']);inst.setLocation(*v['xy']);inst.setPlacementStatus('LOCKED')
  data['capacity_witness']=witness;data['dirty_nets']=sorted(dirty);data['capacity_certificate']=certificate
  expected_positions=dict(data['positions'])
  for updates in (witness['original_moves'],witness['new_buffers']):
   for name,v in updates.items():expected_positions[name]=[*v['xy'],v['orient']]
  if old.positions(block)!=expected_positions:raise ValueError('Applied coordinates differ from certified witness')
  data['capacity_expected_positions']=expected_positions
  for inst in block.getInsts():
   if not inst.isFixed():raise ValueError('Assignment not locked '+inst.getName())
  ref.write_text(json.dumps(data,indent=2));(ref.parent/'capacity_certificate.json').write_text(json.dumps(certificate,indent=2))
  print('CAPACITY ASSIGNMENT APPLIED; native check_placement NOT_YET_RUN');return
 data=json.loads(ref.read_text());old.verify_original(block,old.decode_original(data['expected']))
 if old.bterms(block)!=data['ports'] or len(list(block.getInsts()))!=len(data['expected']['masters']):raise ValueError('Unexpected topology change')
 now=old.positions(block);errors=[dict(kind='assignment_changed',instance=n) for n,p in data['capacity_expected_positions'].items() if now.get(n)!=p]
 report=dict(status='H3_SITE_GEOMETRY_FAIL' if errors else 'H3_SITE_GEOMETRY_PASS',errors=errors,moved_original=list(data['capacity_witness']['original_moves']),certificate=data['capacity_certificate'],dirty_nets=data['dirty_nets'],limits='Certified batch assignment and native placement check; downstream routing/STA results are separate')
 (ref.parent/'site_geometry_report.json').write_text(json.dumps(report,indent=2))
 if errors:raise ValueError('Native check changed the certified assignment')
 if mode=='cleanup':
  for name,status in data['statuses'].items():block.findInst(name).setPlacementStatus(status)
  for name in data['capacity_witness']['new_buffers']:block.findInst(name).setPlacementStatus('PLACED')
  for name in data['dirty_nets']:
   net=block.findNet(name)
   if net.getWire() is not None:old.odb.dbWire.destroy(net.getWire())
   net.clearGuides()
   if list(net.getGuides()):raise ValueError('Stale route guide '+name)
 print('H3_SITE_GEOMETRY_PASS errors=0; placement gate only; subsequent routing/STA not yet verified')
