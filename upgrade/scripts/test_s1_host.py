"""Host algorithm regression only. No RV32 execution/cycles or RTL evidence."""
import ctypes
from pathlib import Path
import random
import subprocess
import tempfile
from evidence import golden

ROOT=Path(__file__).resolve().parents[1]

def main():
    rng=random.Random(17092026)
    with tempfile.TemporaryDirectory(prefix='s1_host_') as temp:
        d=Path(temp)
        (d/'wrapper.c').write_text('#include "sobel_s1.h"\nvoid run_tile(const unsigned char *src, unsigned char *dst, int w,int h,int x,int y,int xe,int ye){sobel_tile_s1(src,dst,w,h,x,y,xe,ye);}\n')
        subprocess.run(['gcc','-std=c11','-O2','-Wall','-Wextra','-Werror','-shared','-fPIC',
                        '-I',str(ROOT/'firmware/s1'),str(d/'wrapper.c'),'-o',str(d/'kernel.so')],check=True)
        library=ctypes.CDLL(str(d/'kernel.so'))
        fn=library.run_tile
        ptr=ctypes.POINTER(ctypes.c_ubyte)
        fn.argtypes=[ptr,ptr,*([ctypes.c_int]*6)];fn.restype=None
        cases=0
        for w,h in ((1,1),(1,7),(9,1),(2,2),(3,3),(17,19),(31,33),(37,35),(65,9)):
            for tile in (1,2,16,32,64):
                for pattern in ('zero','full','ramp','impulse','random'):
                    n=w*h
                    pixels=bytes(0 if pattern=='zero' else 255 if pattern=='full' else
                                 (i*17)%256 if pattern=='ramp' else (255 if i==n//2 else 0) if pattern=='impulse' else
                                 rng.randrange(256) for i in range(n))
                    src=(ctypes.c_ubyte*(n+2))(73,*pixels,91)
                    dst=(ctypes.c_ubyte*(n+2))(73,*([0xA5]*n),91)
                    source=ctypes.cast(ctypes.byref(src,1),ptr)
                    output=ctypes.cast(ctypes.byref(dst,1),ptr)
                    expected=golden(pixels,w,h)
                    for y in range(0,h,tile):
                        for x in range(0,w,tile):
                            before=bytes(dst)
                            xe,ye=min(w,x+tile),min(h,y+tile)
                            fn(source,output,w,h,x,y,xe,ye)
                            for yy in range(h):
                                for xx in range(w):
                                    i=yy*w+xx
                                    wanted=expected[i] if x<=xx<xe and y<=yy<ye else before[i+1]
                                    if dst[i+1]!=wanted: raise AssertionError((w,h,tile,pattern,x,y,xx,yy))
                    if bytes(src[1:n+1])!=pixels or (src[0],src[-1],dst[0],dst[-1])!=(73,91,73,91):
                        raise AssertionError('Input/canary modified')
                    cases+=1
        print(f'HOST S1 ALGORITHM CHECK PASS: {cases} cases, tile-local writes and independent golden; not RV32/RTL simulation.')

if __name__=='__main__': main()
