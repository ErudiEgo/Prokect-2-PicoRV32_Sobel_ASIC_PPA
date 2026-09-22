#!/usr/bin/env bash
# Only stage2 sources; preserves all destination RUNs and snapshots.
set -euo pipefail
SOURCE=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
DEST="$HOME/openlane_projects/picorv32_sobel_stage2"
export PYTHONDONTWRITEBYTECODE=1
python3 "$SOURCE/scripts/stage2_project.py"
python3 - "$SOURCE" "$DEST" <<'PY'
import json, shutil, sys, hashlib
from pathlib import Path
src,dst=map(lambda p: Path(p).resolve(),sys.argv[1:])
if src==dst:
    raise SystemExit('Source and destination are identical')
if dst.exists() and any(dst.iterdir()):
    marker=dst/'stage2.json'
    if not marker.is_file() or json.loads(marker.read_text()).get('project_id')!='picorv32_sobel_stage2':
        raise SystemExit('Destination is nonempty and is not the stage2 project')
dst.mkdir(parents=True,exist_ok=True)
for name in ('rtl','tb','firmware','inputs','third_party','scripts','baseline','candidate','physical'):
    target=dst/name
    if target.is_symlink():
        raise SystemExit(f'Refusing destination symlink: {target}')
    if name=='baseline':
        for item in (src/name).iterdir():
            dest=target/item.name
            if dest.is_symlink(): raise SystemExit(f'Refusing baseline symlink: {dest}')
            if dest.exists():
                def inventory(p):
                    if p.is_file(): return {'file':hashlib.sha256(p.read_bytes()).hexdigest()}
                    return {q.relative_to(p).as_posix():hashlib.sha256(q.read_bytes()).hexdigest()
                            for q in p.rglob('*') if q.is_file()}
                if inventory(item)!=inventory(dest): raise SystemExit(f'Existing baseline differs; no overwrite: {dest}')
            else:
                target.mkdir(parents=True,exist_ok=True)
                if item.is_dir(): shutil.copytree(item,dest)
                else: shutil.copy2(item,dest)
        continue
    shutil.copytree(src/name,target,dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
for name in ('.gitignore','.gitattributes','stage2.json','README.md','AGENTS.md','OPENLANE_WORKFLOW_NOTES.md',
             'ARCHITECTURE.md','RGB_RUN_GUIDE.md','RGB32_FIRST_RUN_REVIEW.md',
             'RUN16_REVIEW.md','STAGE2_RESEARCH_ROADMAP.md','STAGE2_RUN_GUIDE.md',
             'STAGE2_ACCEPTANCE.md','M1_ACCEPTANCE_REVIEW.md','M2_RUN_GUIDE.md','M2_DESIGN.md','M2_RGB32_REVIEW.md','DMA_V2_CANDIDATE.md','NEXT_RUNS.md','M3_RUN_GUIDE.md','M2_M3_UNIT_ACCEPTANCE.md','M3_RGB32_REVIEW.md','PROJECT_DIRECTION_LOW_RES_IMAGE_SOC.md','H2_FREEZE_REVIEW.md','H2_CHARACTERIZATION_PLAN.md','H2_CHARACTERIZATION_ACCEPTANCE.md','PPA_RUN_GUIDE.md','H1_PPA_REVIEW.md','H2_PPA_REVIEW.md','H2_REPAIR01_REVIEW.md','H2_ECO_RUN_GUIDE.md'):
    if (dst/name).is_symlink():
        raise SystemExit(f'Refusing destination symlink: {dst/name}')
    shutil.copy2(src/name,dst/name)
print(f'COPY PASS: {dst}\nNo simulation or physical flow executed. Existing RUNs preserved.')
PY
