"""Read-only padded occupancy matching the pinned OpenLane dpl_cell_pad.tcl."""
import bisect,fnmatch,math

class NativeSites:
 def __init__(self,data,config):
  self.data=data;self.rows=sorted(data['rows'],key=lambda r:(r['origin'][1],r['origin'][0]));self.ys=[r['origin'][1] for r in self.rows]
  self.used=[bytearray(r['count']) for r in self.rows];self.config=config
  self.h=max(r['site'][1] for r in self.rows)
  for r in self.rows:
   if r['direction']!='HORIZONTAL' or r['spacing']!=r['site'][0]:raise ValueError('Unsupported row grid')
  for i in data['instances']:
   l,r=self.padding(i['master']);self.block(i['bbox'],l,r)
  for b in data['blockages']:self.block(b,0,0)
 def padding(self,master):
  total=int(self.config['DPL_CELL_PADDING']);left=right=total//2
  if any(fnmatch.fnmatchcase(master,p) for p in self.config['CELL_PAD_EXCLUDE']):left=right=0
  diode=self.config.get('DIODE_PADDING')
  if diode and master==self.config['DIODE_CELL'].split('/')[0]:left=int(diode)
  return left,right
 def block(self,rect,left,right):
  x0,y0,x1,y1=rect
  for k in range(bisect.bisect_right(self.ys,y0-self.h),bisect.bisect_left(self.ys,y1)):
   r=self.rows[k];ox,y=r['origin'];s=r['spacing']
   a=max(0,math.floor((x0-ox)/s)-left);z=min(r['count'],math.ceil((x1-ox)/s)+right)
   if z>a:self.used[k][a:z]=b'\1'*(z-a)
 def candidates(self,xy,master,limit_um):
  w,h=self.data['masters'][master];l,rpad=self.padding(master);u=self.data['dbu'];limit=limit_um*u
  result=[]
  for k in range(bisect.bisect_left(self.ys,xy[1]-limit),bisect.bisect_right(self.ys,xy[1]+limit)):
   row=self.rows[k];ox,y=row['origin'];s=row['spacing'];dy=abs(y-xy[1])
   if row['site'][1]!=h or w%s:continue
   width=w//s;span=width+l+rpad
   lo=max(0,math.ceil((xy[0]-(limit-dy)-ox)/s)-l)
   hi=min(row['count']-span,math.floor((xy[0]+(limit-dy)-ox)/s)-l)
   for c in range(lo,hi+1):
    if any(self.used[k][c:c+span]):continue
    x=ox+(c+l)*s;result.append(dict(xy=[x,y],orient=row['orient'],distance_um=(abs(x-xy[0])+dy)/u,row=k,start=c,span=span))
  return sorted(result,key=lambda x:(x['distance_um'],x['row'],x['start']))
 def reserve(self,candidate):
  k,c,n=candidate['row'],candidate['start'],candidate['span']
  if any(self.used[k][c:c+n]):raise ValueError('Overlapping reservation')
  self.used[k][c:c+n]=b'\1'*n

if __name__=='__main__':
 import json,sys
 from pathlib import Path
 p=Path(sys.argv[1]);data=json.loads((p/'sites.json').read_text());cfg=json.loads(Path(sys.argv[2]).read_text());plan=json.loads((p/'eco_plan.json').read_text())
 sites=NativeSites(data,cfg);rows=[]
 for r in plan:
  n=r['branches'][0];c=sites.candidates(n['xy'],n['master'],25)
  rows.append(dict(driver=r['driver'],candidates=len(c),nearest=c[0] if c else None))
 print(json.dumps(dict(roots=len(rows),available=sum(bool(x['candidates']) for x in rows),selected=[x for x in rows if x['driver'] in ['_39052_/Y','max_cap340/X','fanout7361/X']]),indent=2))
