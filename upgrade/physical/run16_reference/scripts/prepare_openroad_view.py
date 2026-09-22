"""Prepare a read-only final ODB viewer script. Does not launch OpenROAD."""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


def prepare(root, tag, out, latest_state=False):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", tag):
        raise ValueError("Unsafe RUN name")
    root = root.resolve()
    out = out.resolve()
    if not out.is_relative_to(root / "build") or not out.is_dir():
        raise ValueError("Viewer audit must be in existing project/build directory")
    run = root / "runs" / tag
    state_file = None
    if latest_state:
        states = [p for p in run.glob("*/state_out.json") if re.match(r"^\d+-", p.parent.name)]
        if not states:
            raise ValueError("No completed top-level stage state to inspect")
        state_file = max(states, key=lambda p: int(p.parent.name.split("-")[0]))
        value = json.loads(state_file.read_text()).get("odb")
        if not isinstance(value, str) or not value.startswith("/work/"):
            raise ValueError("Latest state has no supported ODB reference")
        odb = (root / value[len("/work/"):]).resolve()
        if not odb.is_relative_to(run.resolve()) or not odb.is_file():
            raise ValueError("Referenced ODB missing or outside requested RUN")
        label = "STAGE VIEW: RUN not certified PASS; selected from latest completed state"
    else:
        final = run / "final"
        odbs = list(final.rglob("*.odb"))
        if len(odbs) != 1:
            raise ValueError(f"Expected one final ODB, found {len(odbs)}; use --latest-state explicitly for a failed/incomplete RUN")
        odb = odbs[0].resolve()
        if not odb.is_relative_to(final.resolve()):
            raise ValueError("ODB escapes RUN final directory")
        label = "FINAL VIEW: read existing final ODB; this viewer does not certify checks"
    name = "/work/" + odb.relative_to(root).as_posix()
    if any(c in name for c in "{}\n\r"):
        raise ValueError("Unsupported Tcl path")
    (out / "view.tcl").write_text("read_db {" + name + "}\nif {[llength [info commands gui::fit]]} {gui::fit}\nputs {VIEW ONLY: ODB loaded; no physical steps executed}\nputs {" + label + "}\n")
    (out / "view_source.json").write_text(json.dumps({"run": tag, "odb": name, "odb_sha256": hashlib.sha256(odb.read_bytes()).hexdigest(), "state": str(state_file) if state_file else None, "label": label, "scope": "layout viewing only; no STA/PPA recomputation"}, indent=2)+"\n")
    print(label)
    print("Prepared existing ODB view:", name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tag")
    parser.add_argument("out", type=Path)
    parser.add_argument("--latest-state", action="store_true")
    args = parser.parse_args()
    prepare(Path.cwd(), args.tag, args.out, args.latest_state)
