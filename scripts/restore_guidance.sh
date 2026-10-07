#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p guidance
python3 - <<'PY'
from pathlib import Path
import zipfile

root = Path.cwd()
for name in ("stage43_expected.odb", "final_topology_placement.odb"):
    archive = root / "guidance_archives" / (name + ".zip")
    output = root / "guidance" / name
    with zipfile.ZipFile(archive) as zf:
        members = [m for m in zf.namelist() if Path(m).name == name]
        if len(members) != 1:
            raise SystemExit(f"Unexpected archive members for {name}: {members}")
        output.write_bytes(zf.read(members[0]))
print("H3_C40_GUIDANCE_RESTORED")
PY

