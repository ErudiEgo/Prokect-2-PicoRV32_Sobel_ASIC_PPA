"""Compile/static checks only; never starts vvp or firmware execution."""
import ast
import subprocess
import tempfile
from pathlib import Path
from run_m3_tests import ROOT, SOURCES, MODES, VERSIONS, check_sources
from profile_m3 import expected_reads

def main():
    check_sources()
    for script in (ROOT/'scripts').glob('*.py'):
        ast.parse(script.read_text())
    # Independent enumerated halo oracle; these are host checker tests, not RTL results.
    count=0
    for w,h in ((1,1),(1,7),(9,1),(17,19),(67,67)):
        for tile in (1,2,16,64):
            oracle=0
            for y in range(0,h,tile):
                for x in range(0,w,tile):
                    samples={(xx,yy) for yy in range(y-1,min(h,y+tile)+1)
                             for xx in range(x-1,min(w,x+tile)+1) if 0<=xx<w and 0<=yy<h}
                    oracle+=len(samples)
            for c in (1,3):
                if expected_reads(w,h,c,tile,3)!=c*oracle:
                    raise ValueError('Halo checker disagrees with enumeration')
                count+=1
    (ROOT/'build').mkdir(exist_ok=True)
    out=Path(tempfile.mkdtemp(prefix='m3_static_',dir=ROOT/'build'))
    for name,identity,_ in MODES:
        args=['iverilog','-g2012','-Wall','-Wno-timescale','-s','tb_sobel_soc_m3',
              '-Ptb_sobel_soc_m3.ENABLE_SOBEL=1',f'-Ptb_sobel_soc_m3.FIRMWARE_MODE={identity}',
              f'-Ptb_sobel_soc_m3.DMA_VERSION={VERSIONS[name]}','-o',str(out/f'{name}.vvp'),
              *[str(ROOT/p) for p in SOURCES]]
        result=subprocess.run(args,capture_output=True,text=True)
        (out/f'{name}.log').write_text(result.stdout+result.stderr)
        print(result.stdout+result.stderr,end='')
        result.check_returncode()
    print(f'M3 STATIC CHECK PASS: four SoC configurations compiled; {count} host halo checks; firmware hashes valid.\nEvidence: {out}\nRTL simulation NOT_RUN; ASIC NOT_RUN.')

if __name__=='__main__': main()
