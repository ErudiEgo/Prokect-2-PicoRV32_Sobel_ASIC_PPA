from site_pilot import choose_sites

def test():
 data=dict(dbu=1,rows=[dict(origin=[0,0],spacing=1,count=80,orient='R0',direction='HORIZONTAL',site=[1,2])],masters={'buf':[2,2]},instances=[dict(master='logic',bbox=[0,0,12,2],fixed=True),dict(master='logic',bbox=[25,0,35,2],fixed=False)],blockages=[[65,0,80,2]])
 req=[dict(name='a',xy=[20,0],master='buf',limit_um=10),dict(name='b',xy=[20,0],master='buf',limit_um=10),dict(name='bad',xy=[70,0],master='buf',limit_um=1)]
 sites,errors=choose_sites(data,req)
 assert errors==['bad'] and len(sites)==2
 assert abs(sites['a']['xy'][0]-sites['b']['xy'][0])>=6
 assert all(16<=s['xy'][0]<=30 for s in sites.values())
 assert (sites,errors)==choose_sites(data,req)
 # Movable occupancy is permitted only as a seed, not called legal placement.
 data['instances']=[dict(master='logic',bbox=[0,0,80,2],fixed=False)];data['blockages']=[]
 sites,errors=choose_sites(data,req[:1]);assert not errors and sites['a']['soft_overlap_sites']==6
 data['instances'][0]['fixed']=True
 assert choose_sites(data,req[:1])[1]==['a']
 print('SITE SEED STATIC TEST PASS: fixed cells, movable occupancy, padding, reservations, bounds and determinism')

if __name__=='__main__':test()
