#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
expected = json.loads((root / "snapshot_sha256.json").read_text())

errors = []
for relative, digest in expected.items():
    path = root / relative
    if not path.is_file():
        errors.append(f"MISSING {relative}")
        continue
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != digest:
        errors.append(f"HASH {relative} expected={digest} actual={actual}")

guidance = {
    "guidance/stage43_expected.odb": "2f3fd5676252003517c2ab013d44ec881d95fff20f2077b11b42a7a8afbd7b7d",
    "guidance/final_topology_placement.odb": "e2ed4af7735b0fb2c1d444b0f406e426a6b2cae5f2ea32b966a441eb75100229",
}
for relative, digest in guidance.items():
    path = root / relative
    if not path.is_file():
        errors.append(f"MISSING {relative}; run restore_guidance first")
        continue
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != digest:
        errors.append(f"HASH {relative} expected={digest} actual={actual}")

if errors:
    raise SystemExit("H3_C40_FROZEN_SOURCE_FAIL\n" + "\n".join(errors))
print(f"H3_C40_FROZEN_SOURCE_PASS files={len(expected) + len(guidance)}")

