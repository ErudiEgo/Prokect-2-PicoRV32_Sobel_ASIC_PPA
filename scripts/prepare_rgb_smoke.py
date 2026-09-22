"""Prepare small original RGB INPUT fixtures only. No simulated outputs/events."""
import argparse
from pathlib import Path
from prepare_image import write_input


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--width',type=int,default=32)
    p.add_argument('--height',type=int,default=32)
    a=p.parse_args()
    if not 1<=a.width<=256 or not 1<=a.height<=256:
        p.error('RGB dimensions must be 1..256')
    w,h=a.width,a.height
    # Distinct channel patterns: vertical/horizontal edges and diagonal gradients.
    # Both low-gradient arithmetic and clipped high-contrast boundaries are exercised.
    planes=[bytearray(),bytearray(),bytearray()]
    for y in range(h):
        for x in range(w):
            planes[0].append((20+3*x+(100 if x>=w//2 else 0))%256)
            planes[1].append((10+2*y+(140 if y>=h//2 else 0))%256)
            planes[2].append((x+3*y+(90 if abs(x-y)<=1 else 0))%256)
    pixels=b''.join(planes)
    original=bytes(planes[c][i] for i in range(w*h) for c in range(3))
    write_input(a.output,w,h,pixels,{'generator':'original RGB channel diagnostic v1',
        'purpose':'channel ordering, gradients, clipping, image borders, tile seams/partial tiles'},3,original)

if __name__=='__main__':
    main()
