"""USER-RUN ONLY: resume the remaining M3 runs, audit and export actual evidence."""
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from audit_m3 import audit
from run_m3_tests import SOURCES, MODES

ROOT = Path(__file__).resolve().parents[1]
DEST = Path('/mnt/e/aa. PPA_Project_List/aaa.PicoRV32_Sobel_ASIC_PPA/upgrade/reports')
CASES = (
    ('s2_m3_soc_rgb17x19_w3_01', 'rgb_partial17x19_v1', 16, 3),
    ('s2_m3_soc_gray37x35_w1_01', 'demo', 16, 1),
    ('s2_m3_soc_rgb1x1_w0_01', 'm2_1x1_c3', 1, 0),
    ('s2_m3_soc_rgb1x7_w3_01', 'm2_1x7_c3', 2, 3),
    ('s2_m3_soc_gray9x1_w1_01', 'm2_9x1_c1', 16, 1),
    ('s2_m3_soc_gray64_t64_w1_01', 'shapes64_00_01', 64, 1),
)

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def export(archive):
    DEST.mkdir(parents=True, exist_ok=True)
    target = DEST / archive.name
    if target.exists():
        if digest(target) != digest(archive):
            raise ValueError(f'Export collision; preserved both originals: {target}')
        print(f'ALREADY EXPORTED (identical SHA256): {target}', flush=True)
    else:
        with archive.open('rb') as source, target.open('xb') as output:
            shutil.copyfileobj(source, output)
        print(f'EXPORTED: {target}', flush=True)

def main():
    for tag, image, tile, wait in CASES:
        run = ROOT / 'reports' / tag
        archive = run.with_suffix('.zip')
        if run.exists() or archive.exists():
            if not run.is_dir() or not archive.is_file():
                raise ValueError(f'Incomplete existing RUN {tag}; inspect it, do not overwrite')
            print(f'AUDIT EXISTING (no rerun): {tag}', flush=True)
        else:
            print(f'RUN: {tag}', flush=True)
            rc = subprocess.call([sys.executable, str(ROOT/'scripts/run_m3_tests.py'), tag,
                '--image', str(ROOT/'inputs'/image), '--tile', str(tile), '--memory-wait', str(wait)], cwd=ROOT)
            if archive.exists():
                export(archive)  # Preserve failure evidence too.
            if rc:
                raise RuntimeError(f'{tag} failed; stop batch and inspect exported evidence')
        with zipfile.ZipFile(archive) as bundle:
            entries = [entry for entry in bundle.infolist() if not entry.is_dir()]
            archived = {entry.filename: hashlib.sha256(bundle.read(entry)).hexdigest() for entry in entries}
            existing = {tag+'/'+p.relative_to(run).as_posix():digest(p) for p in run.rglob('*') if p.is_file()}
            if len(entries) != len(archived) or archived != existing:
                raise ValueError(f'Archive differs from RUN directory: {tag}; preserved evidence')
        cfg = json.loads((run/'run_config.json').read_text())
        if cfg['tile'] != tile or cfg['memory_wait'] != wait:
            raise ValueError(f'Existing RUN settings differ: {tag}')
        # Bind the requested image content, not merely its directory name.
        expected = ROOT/'inputs'/image
        actual = run/'inputs/image'
        expected_files = {p.relative_to(expected).as_posix(): digest(p) for p in expected.rglob('*') if p.is_file()}
        actual_files = {p.relative_to(actual).as_posix(): digest(p) for p in actual.rglob('*') if p.is_file()}
        if expected_files != actual_files:
            raise ValueError(f'Existing RUN image differs: {tag}')
        for name in SOURCES + [p for _,_,p in MODES]:
            if digest(run/'inputs'/name)!=digest(ROOT/name):
                raise ValueError(f'Existing RUN uses a different source: {tag}: {name}')
        print(json.dumps(audit(run), indent=2), flush=True)
        export(archive)
    print('M3 REGRESSION SIX AUDIT PASS; send the six ZIPs for consolidated acceptance. ASIC NOT_RUN.', flush=True)

if __name__ == '__main__':
    main()
