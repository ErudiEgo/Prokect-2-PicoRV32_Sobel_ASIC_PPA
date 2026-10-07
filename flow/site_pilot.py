"""User-run site-seeded placement pilot. Never performs routing or STA."""
import json, math, bisect
from pathlib import Path
import electrical_eco_legacy as old

def choose_sites(data, requests):
 rows=sorted(data['rows'],key=lambda r:(r['origin'][1],r['origin'][0]))
 ys=[r['origin'][1] for r in rows]
 hard=[bytearray(r['count']) for r in rows];soft=[bytearray(r['count']) for r in rows]
 height=max(r['site'][1] for r in rows)
 def block(rect,pad,masks):
  x0,y0,x1,y1=rect
  for k in range(bisect.bisect_right(ys,y0-height),bisect.bisect_left(ys,y1)):
   r=rows[k];ox,y=r['origin'];s=r['spacing']
   a=max(0,math.floor((x0-ox)/s)-pad);z=min(r['count'],math.ceil((x1-ox)/s)+pad)
   if z>a:masks[k][a:z]=b'\1'*(z-a)
 for r in rows:
  if r['direction']!='HORIZONTAL' or r['spacing']!=r['site'][0]:raise ValueError('Unsupported row geometry')
 for i in data['instances']:
  pad=0 if any(t in i['master'] for t in ('__tap','__decap','__fill')) else 2
  block(i['bbox'],pad,hard if i['fixed'] else soft)
 for rect in data['blockages']:block(rect,0,hard)
 result={};errors=[];u=data['dbu']
 for req in requests:
  x,y=req['xy'];limit=req['limit_um']*u;w,h=data['masters'][req['master']];best=None
  for k in range(bisect.bisect_left(ys,y-limit),bisect.bisect_right(ys,y+limit)):
   r=rows[k];ox,ry=r['origin'];s=r['spacing'];dy=abs(ry-y)
   if h!=r['site'][1]:continue
   span=math.ceil(w/s)+4
   lo=max(0,math.ceil((x-(limit-dy)-ox)/s)-2)
   hi=min(r['count']-span,math.floor((x+(limit-dy)-ox)/s)-2)
   for c in range(lo,hi+1):
    if any(hard[k][c:c+span]):continue
    px=ox+(c+2)*s;d=abs(px-x)+dy
    candidate=(sum(soft[k][c:c+span]),d,k,c,px,ry,span)
    if best is None or candidate<best:best=candidate
  if best is None:
   errors.append(req['name']);continue
  overlap,d,k,c,px,py,span=best;hard[k][c:c+span]=b'\1'*span
  result[req['name']]=dict(xy=[px,py],orient=rows[k]['orient'],soft_overlap_sites=overlap,seed_distance_um=d/u)
 return result,errors

def geometry(block):
 def box(x):return [x.xMin(),x.yMin(),x.xMax(),x.yMax()]
 return dict(dbu=block.getDbUnitsPerMicron(),rows=[dict(origin=list(r.getOrigin()),spacing=r.getSpacing(),count=r.getSiteCount(),orient=str(r.getOrient()),direction=str(r.getDirection()),site=[r.getSite().getWidth(),r.getSite().getHeight()]) for r in block.getRows()],instances=[dict(name=i.getName(),master=i.getMaster().getName(),bbox=box(i.getBBox()),fixed=i.isFixed()) for i in block.getInsts()],blockages=[box(x.getBBox()) for x in block.getBlockages()],masters={n:[block.getDataBase().findMaster(n).getWidth(),block.getDataBase().findMaster(n).getHeight()] for n in (old.MASTER,old.ROOT_MASTER)})

def audit(block,data):
 old.verify_original(block,old.decode_original(data['expected']))
 if old.bterms(block)!=data['ports']:raise ValueError('Port connection changed')
 if len(list(block.getInsts()))!=len(data['expected']['masters']):raise ValueError('Instance count changed')
 u=block.getDbUnitsPerMicron();now=old.positions(block);movement=[];errors=[];dirty=set(data['dirty_nets'])
 for name,xy in data['positions'].items():
  actual=now[name];d=old.distance(actual[:2],xy[:2])/u
  if actual!=xy:
   movement.append(dict(instance=name,distance_um=d,orientation_changed=actual[2]!=xy[2]))
   if name in data['fixed_original'] or d>25:errors.append(dict(kind='original_movement',instance=name,distance_um=d))
   for t in block.findInst(name).getITerms():
    net=t.getNet()
    if net is not None and not net.isSpecial():dirty.add(net.getName())
 nets=[];roots=[]
 for row in data['rows']:
  root=block.findInst(row['branches'][0]['buffer']);driver=old.term(block,row['driver']).getInst()
  d=old.distance(root.getLocation(),driver.getLocation())/u
  if d>25:errors.append(dict(kind='root_distance',driver=row['driver'],distance_um=d))
  roots.append(d)
  for node in row['branches']:
   xy=block.findInst(node['buffer']).getLocation();net=block.findNet(node['net'])
   sinks=[t for t in net.getITerms() if not t.isOutputSignal()]
   total=sum(old.distance(xy,t.getInst().getLocation()) for t in sinks)/u
   nets.append(dict(net=node['net'],distance_sum_um=total,loads=len(sinks)))
   if total>240 or len(sinks)>3:errors.append(dict(kind='branch_geometry',**nets[-1]))
 return dict(status='H3_SITE_GEOMETRY_PASS' if not errors else 'H3_SITE_GEOMETRY_FAIL',errors=errors,moved_original=movement,roots_max_um=max(roots),nets=nets,dirty_nets=sorted(dirty),limits='Geometry and structural checks only; routing/STA/antenna/DRC/LVS NOT_RUN. Original-cell displacement budget25um; all timing must be remeasured.')

def run(block,mode,reference,plan_file,pins_file,plan_only=False):
 ref=Path(reference)
 if mode=='insert':
  if plan_only:return old.run(block,mode,reference,plan_file,pins_file,True)
  if ref.exists():raise FileExistsError(ref)
  rows=old.plan(block,json.loads(Path(pins_file).read_text()))
  if rows!=json.loads(Path(plan_file).read_text()):raise ValueError('Parent plan mismatch')
  fixed=[i.getName() for i in block.getInsts() if i.isFixed()]
  req=[]
  for root_first in (True,False):
   for row in rows:
    for index,n in enumerate(row['branches']):
     if (index==0)==root_first:req.append(dict(name=n['buffer'],xy=n['xy'],master=n['master'],limit_um=10 if index==0 else 20))
  seeds,errors=choose_sites(geometry(block),req)
  (ref.parent/'site_seed_report.json').write_text(json.dumps(dict(seeds=seeds,unplaced=errors,limits='Seeds may overlap movable original cells; native legalization and geometry gate mandatory'),indent=2))
  if errors:raise ValueError('No bounded seed site for '+str(len(errors))+' buffers; see site_seed_report.json')
  old.run(block,mode,reference,plan_file,pins_file,False)
  data=json.loads(ref.read_text());data['fixed_original']=fixed
  # Restore original mobility. Existing fixed instances remain fixed.
  for name,status in data['statuses'].items():block.findInst(name).setPlacementStatus(status)
  for name,seed in seeds.items():
   inst=block.findInst(name);inst.setOrient(seed['orient']);inst.setLocation(*seed['xy'])
  ref.write_text(json.dumps(data,indent=2));print('SITE SEEDS READY; native legalization still required');return
 data=json.loads(ref.read_text());report=audit(block,data)
 (ref.parent/'site_geometry_report.json').write_text(json.dumps(report,indent=2))
 print(report['status'],'errors='+str(len(report['errors'])),'moved_original='+str(len(report['moved_original'])))
 if report['errors']:raise ValueError('Placement gate failed; see complete site_geometry_report.json')
 if mode=='cleanup':
  for name in report['dirty_nets']:
   net=block.findNet(name)
   if net.getWire() is not None:old.odb.dbWire.destroy(net.getWire())
   net.clearGuides()
   if list(net.getGuides()):raise ValueError('Stale guide '+name)
 print('PLACEMENT PILOT ONLY; routing and timing NOT_RUN')
