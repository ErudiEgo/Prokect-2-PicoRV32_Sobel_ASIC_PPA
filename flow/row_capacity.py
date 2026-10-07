"""Integer row capacity witness. No ODB edits or native placement invocation.

Preserve original row/order, fixed/clock/driver cells and all original y coordinates.
Original x shifts limited to12um; reserve new padded intervals jointly.
"""
import json,math
from collections import ChainMap
from native_sites import NativeSites

def solve(items):
 earliest=[];edge=0
 for i in items:
  start=max(i['lo'],edge)
  if start>i['hi']:return None
  earliest.append(start);edge=start+i['span']
 result={};end=10**12
 for i,low in reversed(list(zip(items,earliest))):
  hi=min(i['hi'],end-i['span'])
  if low>hi:return None
  x=min(hi,max(low,i['want']));result[i['name']]=x;end=x
 return result

def witness(data,config,plan):
 sites=NativeSites(data,config);u=data['dbu'];rows=sites.rows
 if data['blockages']:raise ValueError('Blockages require explicit interval modeling')
 by_y={r['origin'][1]:k for k,r in enumerate(rows)}
 if len(by_y)!=len(rows):raise ValueError('Fragmented rows unsupported by capacity witness')
 originals={i['name']:i for i in data['instances']};items=[[] for _ in rows]
 drivers={r['driver'].rsplit('/',1)[0] for r in plan}
 for i in data['instances']:
  x,y,z,t=i['bbox'];k=by_y.get(y)
  if k is None:raise ValueError('Instance outside supported rows '+i['name'])
  row=rows[k];ox,_=row['origin'];s=row['spacing'];l,r=sites.padding(i['master'])
  if t-y!=row['site'][1] or (x-ox)%s or (z-x)%s or i['xy']!=[x,y]:raise ValueError('Unsupported instance grid '+i['name'])
  fixed=i['fixed'] or i['name'] in drivers or i['name'].startswith(('H3_ECO13_','H3_ECO16_')) or '__clkbuf_' in i['master'] or '__clkinv_' in i['master']
  want=(x-ox)//s-l;span=(z-x)//s+l+r;delta=0 if fixed else math.floor(12*u/s)
  items[k].append(dict(name=i['name'],lo=max(0,want-delta),hi=min(row['count']-span,want+delta),want=want,span=span,left=l,new=False))
 for k,ls in enumerate(items):
  ls.sort(key=lambda i:i['want'])
  # Input padded occupancy must already be legal; do not silently repair a baseline mismatch.
  if any(i['want']<i['lo'] or i['want']>i['hi'] for i in ls) or any(a['want']+a['span']>b['want'] for a,b in zip(ls,ls[1:])):
   raise ValueError('Parent padded row mismatch '+str(k))
 requests=[]
 for first in (True,False):
  for r in plan:
   for index,n in enumerate(r['branches']):
    if (index==0)==first:requests.append((n,r.get('root_search_um',25) if first else 80))
 assignments={};new_meta={};fail=[]
 all_nodes={n['buffer']:n for r in plan for n in r['branches']}
 bynet={n['net']:n['buffer'] for n in all_nodes.values()}
 children={name:[] for name in all_nodes}
 for name,n in all_nodes.items():
  if n['upstream'] in bynet:children[bynet[n['upstream']]].append(name)
 def geometry_ok(k,trial,result,node):
  positions=ChainMap({},base_positions)
  rr=rows[k]
  for it in trial:positions[it['name']]=[rr['origin'][0]+(result[it['name']]+it['left'])*rr['spacing'],rr['origin'][1]]
  for name in list(new_meta)+[node['buffer']]:
   n=all_nodes[name];sinks=children[name]+[p.rsplit('/',1)[0] for p in n['loads']]
   distance=sum(sum(abs(a-b) for a,b in zip(positions[name],positions[t])) for t in sinks if t in positions)
   if distance>240*u:return False
  return True
 for node,limit_um in requests:
  base_positions={name:v['xy'] for name,v in originals.items()}
  for rk,sol in assignments.items():
   rr=rows[rk]
   for it in items[rk]:base_positions[it['name']]=[rr['origin'][0]+(sol[it['name']]+it['left'])*rr['spacing'],rr['origin'][1]]
  x,y=node['xy'];w,h=data['masters'][node['master']];left,right=sites.padding(node['master']);best=None
  for k,row in enumerate(rows):
   ox,ry=row['origin'];s=row['spacing'];dy=abs(ry-y);budget=limit_um*u-dy
   if budget<0 or h!=row['site'][1] or w%s:continue
   span=w//s+left+right
   lo=max(0,math.ceil((x-budget-ox)/s)-left);hi=min(row['count']-span,math.floor((x+budget-ox)/s)-left)
   if lo>hi:continue
   item=dict(name=node['buffer'],lo=lo,hi=hi,want=round((x-ox)/s)-left,span=span,left=left,new=True)
   for index in range(len(items[k])+1):
    if index and items[k][index-1]['lo']+items[k][index-1]['span']>hi:continue
    if index<len(items[k]) and items[k][index]['hi']<lo+span:continue
    trial=items[k][:index]+[item]+items[k][index:];result=solve(trial)
    if result is None:continue
    if not geometry_ok(k,trial,result,node):continue
    moved=[(i,abs(result[i['name']]-i['want'])) for i in trial if not i['new']]
    px=ox+(result[item['name']]+left)*s
    score=(sum(d>0 for _,d in moved),sum(d*s for _,d in moved),abs(px-x)+dy,k,index)
    if best is None or score<best[0]:best=(score,k,trial,result,item)
  if best is None:fail.append(node['buffer']);continue
  _,k,trial,result,item=best
  # Freeze every accepted added buffer reservation; originals retain bounded x intervals.
  item['lo']=item['hi']=item['want']=result[item['name']]
  items[k]=trial;assignments[k]=result
  new_meta[node['buffer']]=(k,node)
 changes={};new={}
 for k,result in assignments.items():
  row=rows[k];ox,y=row['origin'];s=row['spacing']
  for i in items[k]:
   xy=[ox+(result[i['name']]+i['left'])*s,y]
   if i['new']:new[i['name']]=dict(xy=xy,orient=row['orient'])
   elif xy!=originals[i['name']]['xy']:changes[i['name']]=dict(xy=xy,orient=originals[i['name']]['orient'])
 return dict(status='ROW_CAPACITY_WITNESS' if not fail else 'ROW_CAPACITY_INCOMPLETE',new_buffers=new,original_moves=changes,unplaced=fail,limits='One-dimensional row capacity only; native placement, pin access, routing and timing NOT_VERIFIED')

if __name__=='__main__':
 import sys
 from pathlib import Path
 root=Path(sys.argv[1]);cfg=json.loads(Path(sys.argv[2]).read_text());plan=json.loads(Path(sys.argv[3]).read_text())
 result=witness(json.loads((root/'geometry.json').read_text()),cfg,plan)
 (root/'capacity_witness.json').write_text(json.dumps(result,indent=2))
 print(result['status'],'new',len(result['new_buffers']),'original_moves',len(result['original_moves']),'unplaced',result['unplaced'])
