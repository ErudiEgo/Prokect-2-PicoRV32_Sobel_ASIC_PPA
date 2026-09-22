"""USER-RUN ONLY unless --precheck: characterize the frozen H2 without changing RTL."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile
from evidence import load_image, sha
from audit_m3 import audit
from finish_m2 import export
from run_m3_tests import check_sources
from verify_h2_freeze import verify
from prepare_h2_characterization import SIZES, pixels

ROOT=Path(__file__).resolve().parents[1]
MANIFEST_SHA='d41639057c7ee48e10f86284a558ad43682fe8c741f1ff3d4e34c2a974299eb6'
BASELINE_COMMIT='a5b8f2317589a90a599ea37d5bc2a782d71e99f0'

def cases():
    result=[]
    for w,h in SIZES:
        result.append((f's2_m3_soc_h2char_g{w}x{h}_t32_w1_01',w,h,32,1,
                       'pilot' if w<=128 else 'large'))
    for tile,wait in ((16,1),(64,1),(32,0),(32,3)):
        result.append((f's2_m3_soc_h2char_g64x64_t{tile}_w{wait}_01',64,64,tile,wait,'pilot'))
    return result

def baseline_contract():
    package=ROOT/'baseline/H2_LINEBUFFER_BASELINE'
    if sha(package/'manifest.json')!=MANIFEST_SHA: raise ValueError('Wrong frozen baseline manifest')
    verify(package)
    m=json.loads((package/'manifest.json').read_text())
    # Operational copy wrapper may evolve; original hardware, firmware,
    # functional runner/checkers/TBs and imported baseline must match exactly.
    bound={k:v for k,v in m['source_files_sha256'].items()
           if k.startswith(('rtl/','candidate/','tb/','firmware/','third_party/','scripts/'))
           and k!='scripts/00_copy_to_ubuntu.sh'}
    for name,digest in bound.items():
        if sha(ROOT/name)!=digest: raise ValueError('Frozen functional source changed: '+name)
    check_sources()
    return bound

def precheck():
    bound=baseline_contract()
    for w,h in SIZES:
        path=ROOT/'inputs'/f'h2_char_gray{w}x{h}_v1'
        meta,data=load_image(path)
        if (meta['width'],meta['height'],meta['channels'])!=(w,h,1) or data!=pixels(w,h):
            raise ValueError('Characterization input differs: '+str(path))
        if w*h>0x40000: raise ValueError('Frame exceeds external memory window')
    for name in ('h2_characterization.py','prepare_h2_characterization.py'):
        ast.parse((ROOT/'scripts'/name).read_text())
    plan=cases()
    if len(plan)!=10 or len({c[0] for c in plan})!=10: raise ValueError('Invalid matrix')
    print(f'H2 CHARACTERIZATION PRECHECK PASS: {len(bound)} frozen source bindings, six INPUT_ONLY fixtures, ten planned RUNs. No simulation executed.',flush=True)
    return bound

def audit_case(case,bound):
    tag,w,h,tile,wait,phase=case
    run=ROOT/'reports'/tag
    archive=run.with_suffix('.zip')
    if not run.is_dir() or not archive.is_file(): raise ValueError('Incomplete RUN/archive: '+tag)
    with zipfile.ZipFile(archive) as z:
        entries=[p for p in z.infolist() if not p.is_dir()]
        archived={p.filename:hashlib.sha256(z.read(p)).hexdigest() for p in entries}
        actual={tag+'/'+p.relative_to(run).as_posix():sha(p) for p in run.rglob('*') if p.is_file()}
        if len(entries)!=len(archived) or archived!=actual: raise ValueError('Archive differs from RUN: '+tag)
    cfg=json.loads((run/'run_config.json').read_text())
    expected={'width':w,'height':h,'channels':1,'tile':tile,'memory_wait':wait,
              'timeout_seconds':1800 if phase=='pilot' else 7200,'max_cycles':500000000,'vcd':False}
    if any(cfg.get(k)!=v for k,v in expected.items()): raise ValueError('RUN condition mismatch: '+tag)
    for name,digest in bound.items():
        if sha(run/'inputs'/name)!=digest: raise ValueError('Frozen RUN binding differs: '+name)
    for name in ('h2_characterization.py','prepare_h2_characterization.py'):
        if sha(run/'inputs/scripts'/name)!=sha(ROOT/'scripts'/name):
            raise ValueError('Experiment definition differs: '+name)
    fixture=ROOT/'inputs'/f'h2_char_gray{w}x{h}_v1'
    expected_files={p.name:sha(p) for p in fixture.iterdir() if p.is_file()}
    image=run/'inputs/image'
    if expected_files!={p.name:sha(p) for p in image.iterdir() if p.is_file()}:
        raise ValueError('Input binding differs: '+tag)
    result=audit(run)
    result['archive_sha256']=sha(archive)
    result['baseline_commit']=BASELINE_COMMIT
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('phase',choices=('pilot','large'),nargs='?',default='pilot')
    p.add_argument('--precheck',action='store_true')
    args=p.parse_args()
    bound=precheck()
    if args.precheck:return
    # Large runs require all pilot evidence, not only a console PASS string.
    if args.phase=='large':
        for case in cases():
            if case[-1]=='pilot':audit_case(case,bound)
    results=[]
    for case in cases():
        tag,w,h,tile,wait,phase=case
        if phase!=args.phase:continue
        run=ROOT/'reports'/tag
        archive=run.with_suffix('.zip')
        if not run.exists() and not archive.exists():
            print('RUN:',tag,flush=True)
            rc=subprocess.call([sys.executable,str(ROOT/'scripts/run_m3_tests.py'),tag,
                '--image',str(ROOT/'inputs'/f'h2_char_gray{w}x{h}_v1'),
                '--tile',str(tile),'--memory-wait',str(wait),
                '--timeout-seconds',str(1800 if phase=='pilot' else 7200),
                '--max-cycles','500000000'],cwd=ROOT)
            if archive.exists():export(archive)
            if rc:raise RuntimeError('Stop on failed RUN; preserve evidence: '+tag)
        else:print('AUDIT EXISTING (no rerun):',tag,flush=True)
        result=audit_case(case,bound)
        print(json.dumps(result,indent=2),flush=True)
        export(archive)
        results.append(result)
    print(f'H2 CHARACTERIZATION {args.phase.upper()} AUDIT PASS: {len(results)} RUNs. ASIC NOT_RUN.',flush=True)

if __name__=='__main__':main()
