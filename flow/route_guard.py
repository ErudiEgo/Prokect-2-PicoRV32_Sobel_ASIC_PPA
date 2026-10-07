"""Read-only connectivity/placement guard against accepted RUN14."""
import electrical_eco_legacy as old
def check(block,data,mode,diode_cell='sky130_fd_sc_hd__diode_2',diode_pin='DIODE'):
 old.verify_original(block,old.decode_original(data['expected']))
 if old.bterms(block)!=data['ports']:raise ValueError('Port connectivity changed')
 current=old.positions(block)
 for name,position in data['capacity_expected_positions'].items():
  if current.get(name)!=position:raise ValueError('Accepted placement moved: '+name)
 added=set(current)-set(data['capacity_expected_positions'])
 if added and mode!='antenna':raise ValueError('Unexpected added instances')
 for name in added:
  i=block.findInst(name);t=i.findITerm(diode_pin)
  if i.getMaster().getName()!=diode_cell or t is None or t.getNet() is None:raise ValueError('Unexpected added non-diode '+name)
 if mode=='input':
  for name in data['dirty_nets']:
   net=block.findNet(name)
   if net is None or net.getWire() is not None or list(net.getGuides()):raise ValueError('Stale dirty-net routing '+name)
 return {'status':'H3_ROUTE_GUARD_PASS','mode':mode,'preserved_instances':len(data['capacity_expected_positions']),'added_diodes':sorted(added),'limits':'Topology/placement only; not timing or physical signoff'}
