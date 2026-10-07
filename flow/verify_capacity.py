"""Independent interval and net-geometry verifier for a row-capacity witness."""
import fnmatch,math

def verify(data,cfg,plan,witness):
 if witness['status']!='ROW_CAPACITY_WITNESS' or witness['unplaced']:raise ValueError('Incomplete witness')
 new=witness['new_buffers'];moves=witness['original_moves'];original={i['name']:i for i in data['instances']}
 nodes={n['buffer']:n for r in plan for n in r['branches']}
 if set(new)!=set(nodes) or not set(moves)<=set(original) or set(new)&set(original):raise ValueError('Wrong inventory')
 drivers={r['driver'].rsplit('/',1)[0] for r in plan};u=data['dbu'];rows={r['origin'][1]:r for r in data['rows']};intervals={y:[] for y in rows};positions={}
 def pad(master):
  l=r=int(cfg['DPL_CELL_PADDING'])//2
  if any(fnmatch.fnmatchcase(master,s) for s in cfg['CELL_PAD_EXCLUDE']):l=r=0
  if cfg.get('DIODE_PADDING') and master==cfg['DIODE_CELL'].split('/')[0]:l=int(cfg['DIODE_PADDING'])
  return l,r
 def record(name,xy,orient,width,height,master):
  x,y=xy;row=rows[y];ox,_=row['origin'];s=row['spacing'];l,r=pad(master)
  if height!=row['site'][1] or (x-ox)%s or width%s:raise ValueError('Off-grid '+name)
  a=x-l*s;z=x+width+r*s
  if a<ox or z>ox+row['count']*s:raise ValueError('Outside row '+name)
  intervals[y].append((a,z,name));positions[name]=xy
 for name,i in original.items():
  v=moves.get(name,dict(xy=i['xy'],orient=i['orient']));x,y=v['xy']
  if y!=i['xy'][1] or abs(x-i['xy'][0])>12*u or v['orient']!=i['orient']:raise ValueError('Invalid original move '+name)
  if name in moves and (i['fixed'] or name in drivers or i['name'].startswith(('H3_ECO13_','H3_ECO16_')) or '__clkbuf_' in i['master'] or '__clkinv_' in i['master']):raise ValueError('Protected cell moved '+name)
  a,b,c,d=i['bbox'];record(name,v['xy'],v['orient'],c-a,d-b,i['master'])
 for name,v in new.items():
  master=nodes[name]['master'];w,h=data['masters'][master]
  if v['orient']!=rows[v['xy'][1]]['orient']:raise ValueError('Wrong new row orientation')
  record(name,v['xy'],v['orient'],w,h,master)
 for y,ints in intervals.items():
  ints.sort()
  for a,b in zip(ints,ints[1:]):
   if a[1]>b[0]:raise ValueError('Padded overlap '+a[2]+' / '+b[2])
 if data['blockages']:raise ValueError('Unsupported blockages')
 def dist(a,b):return sum(abs(x-y) for x,y in zip(a,b))/u
 roots=[];nets=[]
 for r in plan:
  root=r['branches'][0];d=dist(r.get('root_anchor', positions[r['driver'].rsplit('/',1)[0]]),positions[root['buffer']]);roots.append(d)
  if d>r.get('root_search_um',25):raise ValueError('Root beyond frozen search bound')
  bynet={n['net']:n for n in r['branches']};children={n:[] for n in bynet}
  for n in r['branches']:
   if n['upstream'] in children:children[n['upstream']].append(n['buffer'])
  for n in r['branches']:
   sinks=children[n['net']]+[p.rsplit('/',1)[0] for p in n['loads']]
   d=sum(dist(positions[n['buffer']],positions[p]) for p in sinks)
   if len(sinks)>3 or d>240:raise ValueError('Branch geometry '+n['net']+' '+str(d))
   nets.append(d)
 return dict(status='ROW_CAPACITY_CERTIFICATE_PASS',original_instances=len(original),new_buffers=len(new),original_moves=len(moves),max_original_move_um=max([0]+[abs(v['xy'][0]-original[n]['xy'][0])/u for n,v in moves.items()]),max_root_distance_um=max(roots),max_branch_sum_um=max(nets),limits='Integer row/padding and geometry certificate, not native placement/DRC/STA sign-off')

if __name__=='__main__':
 import json,sys
 from pathlib import Path
 p=Path(sys.argv[1]);result=verify(json.loads((p/'geometry.json').read_text()),json.loads(Path(sys.argv[2]).read_text()),json.loads(Path(sys.argv[3]).read_text()),json.loads((p/'capacity_witness.json').read_text()))
 (p/'capacity_certificate.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
