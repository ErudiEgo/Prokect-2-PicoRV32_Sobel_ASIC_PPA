"""Verify immutable H2 package bytes/inventories. Read-only; no simulator or flow."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def verify(root):
    m=json.loads((root/'manifest.json').read_text())
    if m['baseline']!='H2_LINEBUFFER_BASELINE': raise ValueError('Wrong baseline')
    wanted=set(m['artifacts_sha256'])|{'manifest.json'}
    if {p.name for p in root.iterdir()}!=wanted: raise ValueError('Package inventory differs')
    for name,digest in m['artifacts_sha256'].items():
        if Path(name).name!=name or sha(root/name)!=digest: raise ValueError('Artifact mismatch: '+name)
    for archive,key in (('sources.zip','source_files_sha256'),('evidence.zip','evidence_files_sha256')):
        with zipfile.ZipFile(root/archive) as z:
            names=z.namelist()
            if len(names)!=len(set(names)) or set(names)!=set(m[key]): raise ValueError('ZIP inventory mismatch')
            for name in names:
                p=PurePosixPath(name)
                if p.is_absolute() or '..' in p.parts or '\\' in name: raise ValueError('Unsafe ZIP name')
                if hashlib.sha256(z.read(name)).hexdigest()!=m[key][name]: raise ValueError('ZIP hash mismatch: '+name)
    return {'status':'H2_FREEZE_PACKAGE_INTEGRITY_PASS','baseline':m['baseline'],
            'manifest_sha256':sha(root/'manifest.json'),'sources':len(m['source_files_sha256']),
            'evidence_archives':len(m['evidence_files_sha256']),
            'limits':'Integrity of previously audited evidence; no simulation, PPA or H3 claim.'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('package',type=Path)
    print(json.dumps(verify(p.parse_args().package.resolve()),indent=2))
