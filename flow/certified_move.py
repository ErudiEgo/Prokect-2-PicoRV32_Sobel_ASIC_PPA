"""Apply an already-certified original-cell move with explicit lock discipline."""
def move_and_relock(inst, xy, original_status):
 if original_status!='PLACED':raise ValueError('Certified move requires an originally movable PLACED cell')
 if str(inst.getPlacementStatus())!='LOCKED' or not inst.isFixed():raise ValueError('Expected temporary ECO lock before move')
 orientation=str(inst.getOrient())
 inst.setPlacementStatus('PLACED')
 try:
  if inst.isFixed():raise ValueError('Temporary unlock did not take effect')
  inst.setLocation(*xy)
  if list(inst.getLocation())!=list(xy) or str(inst.getOrient())!=orientation:raise ValueError('Certified coordinate/orientation mismatch')
 finally:
  inst.setPlacementStatus('LOCKED')
 if not inst.isFixed():raise ValueError('Original cell was not relocked')
