"""Read-only project identity/import checks. No simulator/physical tool launch."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def validate_project(root=ROOT):
    meta = json.loads((root / 'stage2.json').read_text(encoding='utf-8'))
    if meta.get('project_id') != 'picorv32_sobel_stage2' or meta.get('milestone') not in ('M1_baseline_and_profile','M2_software_baseline'):
        raise ValueError('Wrong project/milestone; reassess runner contract')
    manifest = json.loads((root / 'baseline/import_manifest.json').read_text(encoding='utf-8'))
    archive = root / 'baseline/stage1_import.zip'
    if hashlib.sha256(archive.read_bytes()).hexdigest() != manifest['archive_sha256']:
        raise ValueError('Baseline source bundle changed')
    with zipfile.ZipFile(archive) as bundle:
        if len(bundle.namelist()) != len(set(bundle.namelist())) or set(bundle.namelist()) != set(manifest['files']):
            raise ValueError('Baseline bundle inventory mismatch')
        for name, digest in manifest['files'].items():
            if hashlib.sha256(bundle.read(name)).hexdigest() != digest:
                raise ValueError(f'Baseline bundle mismatch: {name}')
            # M1/M2 preserve imported S0/H1 and hardware; S1 lives in additional files.
            if name.startswith(('rtl/', 'firmware/', 'third_party/')):
                if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest:
                    raise ValueError(f'M1 hardware/firmware changed: {name}')
    return meta


if __name__ == '__main__':
    print(json.dumps(validate_project(), indent=2))
    print('STAGE2 IDENTITY AND BASELINE INTEGRITY PASS (not functional evidence)')
