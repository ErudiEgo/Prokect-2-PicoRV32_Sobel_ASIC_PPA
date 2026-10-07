"""Three-net placement-only experiment with pinned sources and roots."""
import json
from pathlib import Path
import electrical_eco_legacy as old
from site_pilot import geometry, choose_sites, audit

TARGETS = ['_39052_/Y','max_cap340/X','fanout7361/X']

def is_clock_cell(master):
 return '__clkbuf_' in master or '__clkinv_' in master

def in_neighborhood(bbox, xy, dbu):
 x,y=xy;x0,y0,x1,y1=bbox
 return max(x0-x,0,x-x1)+max(y0-y,0,y-y1)<=30*dbu

def seed_plan(block, rows):
 if sorted(r['driver'] for r in rows)!=sorted(TARGETS):raise ValueError('Wrong pilot targets')
 data=geometry(block);drivers={r['driver'].rsplit('/',1)[0] for r in rows}
 for i in data['instances']:
  i['fixed']=i['fixed'] or i['name'] in drivers or is_clock_cell(i['master'])
 requests=[]
 for root_first in (True,False):
  for row in rows:
   for index,n in enumerate(row['branches']):
    if (index==0)==root_first:requests.append(dict(name=n['buffer'],xy=n['xy'],master=n['master'],limit_um=10 if index==0 else 20))
 seeds,errors=choose_sites(data,requests)
 if errors:raise ValueError('No bounded site seeds: '+str(errors))
 local=[]
 for i in data['instances']:
  if not i['fixed'] and any(in_neighborhood(i['bbox'],s['xy'],data['dbu']) for s in seeds.values()):local.append(i['name'])
 local_set=set(local)
 locked=[i['name'] for i in data['instances'] if i['name'] not in local_set]
 return dict(seeds=seeds,movable_original=local,locked_original=locked,drivers=sorted(drivers),limits='Seeds are not legal placement. Only user native legalization can prove feasibility.')

def run(block,mode,reference,plan_file,pins_file,plan_only=False):
 ref=Path(reference)
 if mode=='insert':
  rows=old.plan(block,json.loads(Path(pins_file).read_text()))
  if rows!=json.loads(Path(plan_file).read_text()):raise ValueError('Frozen plan mismatch')
  proposal=seed_plan(block,rows)
  if plan_only:
   print('LOCAL PILOT READ ONLY PLAN PASS',len(rows),'nets',len(proposal['seeds']),'buffers',len(proposal['movable_original']),'movable neighbors');return
  if ref.exists():raise FileExistsError(ref)
  (ref.parent/'site_seed_report.json').write_text(json.dumps(proposal,indent=2))
  old.run(block,mode,reference,plan_file,pins_file,False)
  data=json.loads(ref.read_text());data['fixed_original']=proposal['locked_original'];data['local_policy']=proposal
  for name in proposal['movable_original']:block.findInst(name).setPlacementStatus(data['statuses'][name])
  for name,seed in proposal['seeds'].items():
   inst=block.findInst(name);inst.setOrient(seed['orient']);inst.setLocation(*seed['xy'])
  roots={r['branches'][0]['buffer'] for r in rows}
  for name in roots:
   inst=block.findInst(name);inst.setPlacementStatus('LOCKED')
   if not inst.isFixed():raise ValueError('Could not lock root '+name)
  current_positions=old.positions(block)
  data['pinned_roots']={n:current_positions[n] for n in roots}
  ref.write_text(json.dumps(data,indent=2));print('LOCAL ROOTS/DRIVERS LOCKED; native legalization NOT_YET_RUN');return
 data=json.loads(ref.read_text());report=audit(block,data);now=old.positions(block)
 for name,xy in data['pinned_roots'].items():
  if now[name]!=xy:report['errors'].append(dict(kind='pinned_root_moved',instance=name))
 # Enforce per-axis native policy independently of the Manhattan geometry gate.
 for name in data['local_policy']['movable_original']:
  before=data['positions'][name];after=now[name];u=block.getDbUnitsPerMicron()
  if any(abs(before[k]-after[k])>12*u for k in (0,1)):report['errors'].append(dict(kind='axis_displacement',instance=name))
 report['status']='H3_SITE_GEOMETRY_FAIL' if report['errors'] else 'H3_SITE_GEOMETRY_PASS'
 report['scope']='Three nets only; routing/STA/antenna/final DRC/LVS NOT_RUN'
 (ref.parent/'site_geometry_report.json').write_text(json.dumps(report,indent=2))
 print(report['status'],'errors='+str(len(report['errors'])),'moved_original='+str(len(report['moved_original'])))
 if report['errors']:raise ValueError('Local placement gate failed; inspect full geometry report')
 if mode=='cleanup':
  for name,status in data['statuses'].items():block.findInst(name).setPlacementStatus(status)
  for name in data['pinned_roots']:block.findInst(name).setPlacementStatus('PLACED')
  for name in report['dirty_nets']:
   net=block.findNet(name)
   if net.getWire() is not None:old.odb.dbWire.destroy(net.getWire())
   net.clearGuides()
   if list(net.getGuides()):raise ValueError('Stale guide '+name)
 print('LOCAL PILOT ONLY; no routing or timing acceptance')
