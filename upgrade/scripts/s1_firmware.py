"""Publish/validate S1 compiled firmware; keep original S0/H1 bytes immutable."""
import json
from pathlib import Path
import sys
import zipfile
from evidence import sha, read_hex, validate_firmware

ROOT=Path(__file__).resolve().parents[1]
SOURCES={'main.c':'firmware/s1/main.c','sobel_s1.h':'firmware/s1/sobel_s1.h',
         'start.S':'firmware/start.S','link.ld':'firmware/link.ld'}
FLAGS=['-march=rv32i','-mabi=ilp32','-O2','-g','-Wall','-Wextra','-Werror',
       '-ffreestanding','-fno-builtin','-fno-pic','-msmall-data-limit=0',
       '-nostdlib','-nostartfiles','-Wl,--no-relax']

def publish(build):
    old=validate_firmware(ROOT)
    # Rebuild identical S0/H1 with the same compiler/options to confirm comparability.
    for mode in ('sw','hw'):
        if (build/f'{mode}.bin').read_bytes()!=read_hex(ROOT/f'firmware/generated/{mode}.hex',old['images'][mode]['bytes']):
            raise ValueError(f'{mode} rebuild differs from preserved firmware; investigate toolchain before publishing')
    sources={name:sha(ROOT/name) for name in SOURCES.values()}
    for local,name in SOURCES.items():
        if sha(build/local)!=sources[name]: raise ValueError('S1 source changed during build')
    binary=(build/'s1.bin').read_bytes()
    if not 0<len(binary)<=32768: raise ValueError('S1 exceeds 32 KiB code budget')
    target=ROOT/'firmware/s1/generated'
    target.mkdir(exist_ok=False)  # New revision must be deliberate; never silently replace.
    path=target/'s1.hex'
    path.write_bytes(''.join(f'{b:02x}\n' for b in binary).encode('ascii'))
    manifest={'schema':1,'kind':'COMPILED_NOT_EXECUTED','sources':sources,
              'compiler':(build/'compiler.txt').read_text(),'flags':FLAGS,
              'link_libraries':['gcc'],'baseline_rebuild':'S0_H1_BYTE_IDENTICAL',
              'baseline_hex_sha256':{m:old['images'][m]['sha256'] for m in ('sw','hw')},
              'image':{'bytes':len(binary),'sha256':sha(path)},
              'build_artifacts_sha256':{p.name:sha(p) for p in build.iterdir() if p.is_file()}}
    with zipfile.ZipFile(target/'build_evidence.zip','x',compression=zipfile.ZIP_DEFLATED) as bundle:
        for artifact in sorted(build.iterdir()):
            if artifact.is_file(): bundle.write(artifact,artifact.name)
    manifest['build_evidence_sha256']=sha(target/'build_evidence.zip')
    (target/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'S1 COMPILE/PUBLISH PASS: {len(binary)} bytes; S0/H1 rebuild byte-identical. No firmware execution.')

def validate_s1(root=ROOT):
    m=json.loads((root/'firmware/s1/generated/manifest.json').read_text())
    if m.get('schema')!=1 or m.get('baseline_rebuild')!='S0_H1_BYTE_IDENTICAL' or m.get('flags')!=FLAGS:
        raise ValueError('Unexpected S1 manifest/compiler contract')
    if set(m['sources'])!=set(SOURCES.values()): raise ValueError('Incomplete S1 source manifest')
    for name,digest in m['sources'].items():
        if sha(root/name)!=digest: raise ValueError(f'Stale S1 firmware: {name}')
    baseline=validate_firmware(root)
    if m['baseline_hex_sha256']!={k:baseline['images'][k]['sha256'] for k in ('sw','hw')}:
        raise ValueError('S1 compiler comparison uses different baseline')
    p=root/'firmware/s1/generated/s1.hex'
    if not 0<m['image']['bytes']<=32768 or sha(p)!=m['image']['sha256']:
        raise ValueError('Invalid S1 HEX')
    read_hex(p,m['image']['bytes'])
    bundle_path=root/'firmware/s1/generated/build_evidence.zip'
    if sha(bundle_path)!=m['build_evidence_sha256']: raise ValueError('S1 build evidence changed')
    with zipfile.ZipFile(bundle_path) as bundle:
        if set(bundle.namelist())!=set(m['build_artifacts_sha256']):
            raise ValueError('S1 build evidence inventory mismatch')
        import hashlib
        for name,digest in m['build_artifacts_sha256'].items():
            if hashlib.sha256(bundle.read(name)).hexdigest()!=digest:
                raise ValueError(f'S1 build artifact changed: {name}')
        if bundle.read('s1.bin')!=read_hex(p,m['image']['bytes']):
            raise ValueError('S1 HEX differs from compiled binary')
        for local,name in SOURCES.items():
            if hashlib.sha256(bundle.read(local)).hexdigest()!=m['sources'][name]:
                raise ValueError('S1 build source mismatch')
    return m

if __name__=='__main__':
    if len(sys.argv)==2: publish(Path(sys.argv[1]))
    else:
        print(json.dumps(validate_s1(),indent=2))
