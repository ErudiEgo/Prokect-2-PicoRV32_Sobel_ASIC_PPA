"""Create synthetic INPUT_ONLY gray fixtures. No output pixels or measured cycles."""
from pathlib import Path
from prepare_image import write_input
from evidence import load_image, sha

ROOT=Path(__file__).resolve().parents[1]
SIZES=((32,32),(64,64),(128,128),(256,256),(320,240),(480,320))

def pixels(w,h):
    # Coordinate-defined field: all sizes are top-left crops of the same field.
    # Low-amplitude gradients plus edges/texture; not an application dataset.
    return bytes((3*x+5*y+48*((x//16+y//16)%2)+
                  (96 if (x-24)**2+(y-24)**2<100 else 0))%256
                 for y in range(h) for x in range(w))

def prepare():
    for w,h in SIZES:
        path=ROOT/'inputs'/f'h2_char_gray{w}x{h}_v1'
        data=pixels(w,h)
        if path.exists():
            meta,actual=load_image(path)
            if (meta['width'],meta['height'],meta['channels'])!=(w,h,1) or actual!=data:
                raise ValueError(f'Existing fixture differs; never overwrite: {path}')
        else:
            write_input(path,w,h,data,{'generator':'prepare_h2_characterization.py',
                'generator_sha256':sha(Path(__file__)),
                'kind':'synthetic_coordinate_field_v1',
                'formula':'(3*x+5*y+48*((x//16+y//16)%2)+(96 if (x-24)^2+(y-24)^2<100 else 0))%256',
                'sampling':'top-left crop; no scaling; synthetic diagnostic input, not natural imagery'})

if __name__=='__main__': prepare()
