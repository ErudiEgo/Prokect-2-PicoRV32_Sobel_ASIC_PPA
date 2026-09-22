"""Create deterministic degenerate INPUT images only; never outputs or cycle data."""
from pathlib import Path
from prepare_image import write_input

ROOT=Path(__file__).resolve().parents[1]

if __name__=='__main__':
    for w,h,c in ((1,1,3),(1,7,3),(9,1,1)):
        data=bytes((i*37+channel*71+13)%256 for channel in range(c) for i in range(w*h))
        write_input(ROOT/'inputs'/f'm2_{w}x{h}_c{c}',w,h,data,
                    {'generator':'prepare_m2_inputs.py','formula':'(i*37+channel*71+13)%256'},c)
