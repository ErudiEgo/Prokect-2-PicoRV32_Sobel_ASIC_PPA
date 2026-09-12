"""ASIC preparation, config loading and lint only. Never starts a physical flow."""
import argparse
import csv
import hashlib
import io
import json
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from evidence import golden

ROOT = Path(__file__).resolve().parents[1]
TEST = "soc_image_smoke_01"
SOURCES = ["rtl/sobel_core.v", "rtl/sobel_mmio.v", "rtl/picorv32_sobel_soc.v",
           "third_party/picorv32/picorv32.v"]
REPAIR_STEPS = {
    "-OpenROAD.ResizerTimingPostGRT": "OpenROAD.RepairDesignPostGRT",
    "+OpenROAD.ResizerTimingPostGRT": "OpenROAD.RepairAntennas",
    "+OpenROAD.DetailedRouting": "Sobel.AntennaClosure",
}


def save(path, data):
    path.write_text(json.dumps(data, indent=2, default=str) + "\n", encoding="utf-8")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def require_functional():
    archive = ROOT / "reports" / (TEST + ".zip")
    require(archive.is_file(), f"Missing functional evidence: {archive}")
    with zipfile.ZipFile(archive) as z:
        def read(name): return z.read(TEST + "/" + name)
        def load(name): return json.loads(read(name))
        manifest = load("inputs.sha256.json")
        for name, digest in manifest.items():
            require(sha(read("inputs/"+name)) == digest, "Modified test snapshot: "+name)
            if name.startswith(("rtl/", "tb/", "firmware/", "third_party/")):
                require((ROOT/name).is_file() and sha((ROOT/name).read_bytes()) == digest,
                        "Current functional sources differ from evidence: "+name)
        for name in SOURCES + ["firmware/main.c", "firmware/start.S", "firmware/link.ld",
                               "firmware/generated/sw.hex", "firmware/generated/hw.hex", "tb/tb_sobel_soc.sv"]:
            require(name in manifest, "Missing tested source: "+name)
        comparison = load("comparison.json")
        require(comparison["status"] == "PASS", "Functional evidence did not pass")
        for name, digest in comparison["evidence_sha256"].items():
            require(sha(read(name)) == digest, "Modified result: "+name)
        image = load("inputs/image/image.json")
        raw = read("inputs/image/image.hex")
        require(sha(raw) == image["hex_sha256"], "Image hash mismatch")
        pixels = bytes(int(t,16) for t in raw.split())
        w,h = image["width"],image["height"]
        require(len(pixels) == w*h, "Wrong input size")
        expected = golden(pixels,w,h)
        for mode in ("sw", "hw"):
            rows = list(csv.DictReader(io.StringIO(read(mode+"/pixels.csv").decode())))
            require(len(rows) == w*h, "Wrong output size")
            seen = set()
            for row in rows:
                x,y,v = (int(row[k]) for k in ("x","y","value"))
                require(0<=x<w and 0<=y<h and (x,y) not in seen, "Invalid/duplicate output coordinate")
                require(v == expected[y*w+x], f"Pixel mismatch: {mode} ({x},{y})")
                seen.add((x,y))
        require(all(c["exit_code"] == 0 for c in load("commands.json")), "Failed functional subprocess")
    record = {"test": TEST, "archive_sha256": sha(archive.read_bytes()),
              "functional_sources": {n:d for n,d in manifest.items() if n.startswith(("rtl/","tb/","firmware/","third_party/"))},
              "comparison": comparison}
    print(f"FUNCTIONAL EVIDENCE MATCH: {TEST}; SW/HW pixels rechecked; no simulation rerun")
    return record


def prepare_sources(root):
    target = root / "build/asic_sources"
    target.mkdir(parents=True, exist_ok=True)
    provenance = {}
    for name in SOURCES:
        raw = (root/name).read_bytes()
        # Timescale affects event simulation, not hardware. Remove this one
        # upstream directive in the generated physical copy; original untouched.
        derived, count = re.subn(rb"(?m)^`timescale[^\r\n]*\r?\n", b"", raw)
        require(count == (1 if name.endswith("/picorv32.v") else 0), "Unexpected timescale directives")
        reviewed = []
        if name.endswith("/picorv32.v"):
            review = json.loads((root / "scripts/upstream_lint_review.json").read_text())
            require(sha(raw) == review["upstream_sha256"], "Upstream changed; redo lint review")
            lines = derived.decode().splitlines(keepends=True)
            sites = {s["line_without_timescale"]:s for s in review["sites"]}
            require(len(sites) == len(review["sites"]), "Duplicate lint review line")
            result = []
            for number,line in enumerate(lines,1):
                site = sites.get(number)
                if site:
                    require(line.rstrip("\r\n") == site["text"], "Lint review line no longer matches")
                    require(site["rule"] in ("GENUNNAMED","UNUSEDSIGNAL","BLKSEQ"), "Disallowed lint review rule")
                    result.append(f"/* verilator lint_off {site['rule']} */\n")
                result.append(line)
                if site:
                    result.append(f"/* verilator lint_on {site['rule']} */\n")
                    reviewed.append(site)
            derived = "".join(result).encode()
            restored = re.sub(rb"(?m)^/\* verilator lint_(?:off|on) (?:GENUNNAMED|UNUSEDSIGNAL|BLKSEQ) \*/\n",b"",derived)
            require(restored == re.sub(rb"(?m)^`timescale[^\r\n]*\r?\n",b"",raw), "Physical preparation changed RTL tokens")
        output = target / Path(name).name
        output.write_bytes(derived)
        provenance[name] = {"source_sha256": sha(raw), "physical_sha256": sha(derived),
                            "removed_timescale_lines": count, "reviewed_style_sites": reviewed}
    save(target / "provenance.json", provenance)


def validate():
    c = json.loads((ROOT / "config.json").read_text())
    require(c["meta"] == {"version":2,"flow":"Classic","substituting_steps":REPAIR_STEPS},
            "Expected Classic with only the three reviewed repair additions")
    require(c["DESIGN_NAME"] == "picorv32_sobel_soc", "Wrong physical top")
    require(c["PDK"] == "sky130A" and c["STD_CELL_LIBRARY"] == "sky130_fd_sc_hd", "Wrong PDK/library")
    require(c["SYNTH_PARAMETERS"] == ["ENABLE_SOBEL=1"], "Initial physical run must include Sobel")
    require(c.get("RUN_HEURISTIC_DIODE_INSERTION") is False,
            "repair_04 uses targeted antenna repair, not broad heuristic insertion")
    require(c["CLOCK_PORT"] == "clk" and c["CLOCK_PERIOD"] > 10.5, "Invalid real clock budget")
    require(c["VERILOG_FILES"] == ["dir::build/asic_sources/"+Path(s).name for s in SOURCES], "Unexpected physical source list")
    for key in ("RUN_LINTER","RUN_CTS","RUN_DRT","RUN_MCSTA","RUN_SPEF_EXTRACTION",
                "RUN_IRDROP_REPORT","RUN_ANTENNA_REPAIR","RUN_MAGIC_STREAMOUT","RUN_KLAYOUT_STREAMOUT",
                "RUN_MAGIC_DRC","RUN_KLAYOUT_DRC","RUN_KLAYOUT_XOR","RUN_LVS",
                "ERROR_ON_LINTER_WARNINGS","ERROR_ON_MAGIC_DRC","ERROR_ON_KLAYOUT_DRC",
                "ERROR_ON_LVS_ERROR","ERROR_ON_DISCONNECTED_PINS"):
        require(c.get(key) is True, "Required check disabled: "+key)
    for key in ("TIMING_VIOLATION_CORNERS","MAX_SLEW_VIOLATION_CORNERS","MAX_CAP_VIOLATION_CORNERS"):
        require(c.get(key) == ["*"], "Must check all corners: "+key)
    for key in ("PNR_SDC_FILE","SIGNOFF_SDC_FILE","FP_PIN_ORDER_CFG"):
        require((ROOT / c[key].removeprefix("dir::")).is_file(), "Missing: "+key)
    require_functional()
    prepare_sources(ROOT)
    print("ASIC INPUT CHECK PASS: CPU + Sobel; external program/image memory excluded")


def check_openlane(config_path, output):
    import antenna_closure  # register local step; no physical execution
    from openlane.flows.classic import Classic
    from openlane.config import InvalidConfig
    meta = json.loads(config_path.read_text())["meta"]
    require(meta == {"version":2,"flow":"Classic","substituting_steps":REPAIR_STEPS},
            "Unexpected flow selection/step changes")
    # Match OpenLane 2.3.10 CLI meta handling. --flow Classic would OVERRIDE
    # these additions; the user-run launcher deliberately omits that flag.
    TargetFlow = Classic.Substitute(meta["substituting_steps"])
    try:
        flow = TargetFlow(str(config_path), design_dir="/work", pdk_root="/pdk", pdk="sky130A")
    except InvalidConfig as e:
        print("CONFIG WARNINGS", e.warnings)
        print("CONFIG ERRORS", e.errors)
        raise
    keys = ("DESIGN_NAME","PDK","STD_CELL_LIBRARY","CLOCK_PORT","CLOCK_PERIOD","SYNTH_PARAMETERS",
            "STA_CORNERS","FP_SIZING","FP_CORE_UTIL","PL_TARGET_DENSITY_PCT","FP_PDN_VPITCH",
            "FP_PDN_HPITCH","DIODE_ON_PORTS","RUN_ANTENNA_REPAIR","VSRC_LOC_FILES",
            "CTS_SINK_CLUSTERING_SIZE","RSZ_CORNERS","GRT_DESIGN_REPAIR_MAX_SLEW_PCT",
            "GRT_DESIGN_REPAIR_MAX_CAP_PCT","RUN_HEURISTIC_DIODE_INSERTION",
            "HEURISTIC_ANTENNA_THRESHOLD","GRT_ANTENNA_MARGIN","GRT_ANTENNA_ITERS","SOBEL_ANTENNA_ONLY")
    report = {key:flow.config.get(key) for key in keys}
    report["classic_base_steps"] = [s.id for s in Classic.Steps]
    report["classic_steps"] = [s.id for s in flow.Steps]
    # Verify all original steps remain, in order, and the repair steps occur
    # exactly around timing repair. Normalized duplicate IDs carry a -N suffix.
    def canonical(step_id): return re.sub(r"-\d+$", "", step_id)
    base_ids = [canonical(s.id) for s in Classic.Steps]
    actual_ids = [canonical(s.id) for s in flow.Steps]
    expected_ids = list(base_ids)
    at = expected_ids.index("OpenROAD.ResizerTimingPostGRT")
    expected_ids.insert(at, "OpenROAD.RepairDesignPostGRT")
    expected_ids.insert(at+2, "OpenROAD.RepairAntennas")
    expected_ids.insert(expected_ids.index("OpenROAD.DetailedRouting")+1, "Sobel.AntennaClosure")
    require(actual_ids == expected_ids and len(actual_ids) == 81,
            "Classic repair sequence differs from reviewed 78 + 3 steps")
    # Construct child configurations only. Never call Step.start here.
    from openlane.state import State
    closure = antenna_closure.AntennaClosure(flow.config, State())
    diode = antenna_closure.TargetedDiodes(closure.config, State(),
                                         SOBEL_ANTENNA_TARGETS=str(output / "static-targets-only.json"))
    electrical = antenna_closure.RepairDesign(closure.config, State(),
                                             RSZ_CORNERS=["max_ss_100C_1v60"])
    require(str(diode.config["DIODE_CELL"]).endswith("/DIODE"), "Missing PDK diode binding")
    require(electrical.config["RSZ_CORNERS"] == ["max_ss_100C_1v60"], "Electrical corner override lost")
    antenna_closure.GlobalRouting(closure.config, State())
    antenna_closure.VerifyAntennaTopology(closure.config, State(),
                                         SOBEL_TOPOLOGY_REFERENCE=str(output / "topology_reference.json"))
    print("TARGETED REPAIR CONFIG PASS: child configs constructed; no Step.start called")
    api_test = subprocess.run([sys.executable, str(ROOT / "scripts/test_repair_api.py")],
                              text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (output / "repair_api_test.log").write_text(api_test.stdout)
    print(api_test.stdout)
    require(api_test.returncode == 0, "Installed OpenLane API regression failed")
    checkpoint = config_path.parent / "resume_checkpoint"
    if checkpoint.is_dir():
        import os
        import openlane
        initial = json.loads((checkpoint / "state.json").read_text())
        provenance = json.loads((checkpoint / "provenance.json").read_text())
        require(flow.config['SOBEL_ANTENNA_ONLY'] == provenance.get('antenna_only', False),
                'Continuation repair mode differs from checkpoint provenance')
        cell, pin = str(flow.config["DIODE_CELL"]).split("/")
        env = dict(os.environ)
        env["PYTHONPATH"] = str(Path(openlane.__file__).parent / "scripts/odbpy") + ":" + str(ROOT / "scripts")
        cmd = ["openroad", "-exit", "-python", str(ROOT / "scripts/targeted_diodes.py"),
               "--plan-only", "--targets", str(checkpoint / "antenna_targets.json"),
               "--diode-cell", cell, "--diode-pin", pin, initial["odb"]]
        plan = subprocess.run(cmd, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (output / "targeted_read_preflight.log").write_text(plan.stdout)
        save(output / "targeted_read_preflight_command.json", cmd)
        print(plan.stdout)
        require(plan.returncode == 0 and "CONNECTIVITY READ CHECK:" in plan.stdout and "TARGET PLAN PASS:" in plan.stdout,
                "Read-only target/connectivity preflight failed; no physical flow launched")
        regression = subprocess.run(["openroad", "-exit", "-python", str(ROOT / "scripts/test_targeted_read.py"), initial["odb"], str(output / "topology_reference.json")],
                                    env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (output / "odb_read_regression.log").write_text(regression.stdout)
        print(regression.stdout)
        require(regression.returncode == 0 and "ODB READ REGRESSION PASS:" in regression.stdout,
                "Read-only ODB mismatch-guard regression failed")
        guard = subprocess.run(["openroad", "-exit", "-python", str(ROOT / "scripts/verify_antenna_topology.py"),
                                "--reference", str(output / "topology_reference.json"), initial["odb"]],
                               env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (output / "topology_guard_preflight.log").write_text(guard.stdout)
        print(guard.stdout)
        require(guard.returncode == 0 and "ANTENNA TOPOLOGY PASS:" in guard.stdout,
                "Read-only routing topology guard failed")
        # Use real existing ODB cells as stand-ins for added instances by
        # omitting them only from expected JSON. The database is never edited.
        for kind, should_pass in (('diode', True), ('logic', False)):
            cmd = ['openroad', '-exit', '-python', str(ROOT / 'scripts/verify_antenna_topology.py'),
                   '--reference', str(output / ('topology_without_'+kind+'.json')),
                   '--allow-added-diodes', '--diode-cell', cell, '--diode-pin', pin, initial['odb']]
            trial = subprocess.run(cmd, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            (output / ('native_guard_'+kind+'.log')).write_text(trial.stdout)
            if should_pass:
                require(trial.returncode == 0 and 'NATIVE ADDED DIODE CHECK: 1 ' in trial.stdout,
                        'Native guard did not accept a connected PDK diode')
            else:
                require(trial.returncode != 0 and 'added non-diode or disconnected instance' in trial.stdout,
                        'Native guard did not reject added logic')
        print('NATIVE GUARD REGRESSION PASS: connected PDK diode accepted; added logic rejected; no ODB edits')
        from openlane.common import Toolbox
        initial_state = State.loads((checkpoint / "state.json").read_text(), validate_path=True)
        native = antenna_closure.NativeAntennaRepair(closure.config, initial_state)
        native.step_dir = str(output)
        native.toolbox = Toolbox(str(output / "toolbox"))
        native_env = native.prepare_env({}, initial_state)
        native_env['SOBEL_NATIVE_PREFLIGHT'] = '1'
        from openlane.common import TclUtils
        native_env = {k: str(v) for k, v in native_env.items()}
        env_file = output / 'native_preflight_env.tcl'
        env_file.write_text('\n'.join(TclUtils.join(['set', f'::env({k})', v]) for k, v in native_env.items())+'\n')
        native_env = dict(os.environ, **native_env)
        native_env['_TCL_ENV_IN'] = str(env_file)
        native_check = subprocess.run(['openroad', '-exit', native.get_script_path()], env=native_env,
                                      text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (output / 'native_antenna_preflight.log').write_text(native_check.stdout)
        print(native_check.stdout)
        require(native_check.returncode == 0 and 'NATIVE ANTENNA PREFLIGHT PASS:' in native_check.stdout,
                'Native post-DRT read/config preflight failed')
    report["openlane_version"] = subprocess.check_output([sys.executable,"-m","openlane","--version"],text=True).splitlines()[0]
    require(report["openlane_version"] == "OpenLane v2.3.10", "Tool revision changed; review configuration before RUN")
    print(json.dumps({k:v for k,v in report.items() if k not in ("classic_steps","classic_base_steps")},indent=2,default=str))
    save(output / "config_checked.json", report)
    # Standalone lint command with the installed flow's defines/options.
    # No Step.start/Flow.start, synthesis or PNR is invoked.
    cmd = ["verilator","--lint-only","--Wall","--Wno-DECLFILENAME","--Wno-EOFNEWLINE",
           "--Werror-LATCH","--top-module",flow.config["DESIGN_NAME"],
           "+define+PDK_sky130A","+define+SCL_sky130_fd_sc_hd","+define+__openlane__",
           "+define+__pnr__","+define+USE_POWER_PINS", *map(str,flow.config["VERILOG_FILES"])]
    r = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (output / "verilator.log").write_text(r.stdout)
    save(output / "lint_command.json", cmd)
    print(r.stdout)
    require(r.returncode == 0, "Verilator lint failed; see verilator.log")
    # Load constraints against a port-only declaration copied from the real top.
    # No synthesized gates, timing analysis, placement or routing is performed.
    top_path = next(Path(p) for p in flow.config["VERILOG_FILES"] if str(p).endswith("/picorv32_sobel_soc.v"))
    match = re.search(r"module\s+picorv32_sobel_soc\s*#\(.*?\)\s*\((.*?)\);",top_path.read_text(),re.S)
    require(match is not None, "Cannot extract top port declaration")
    (output / "ports_only.v").write_text("// SDC syntax/port-loading fixture only, NOT a synthesized design.\nmodule picorv32_sobel_soc ("+match[1]+");\nendmodule\n")
    lib = next(iter(flow.config["LIB"].values()))[0]
    tech = next(iter(flow.config["TECH_LEFS"].values()))
    tcl = [f"read_lef {{{tech}}}",f"read_liberty {{{lib}}}",f"read_verilog {{{output / 'ports_only.v'}}}","link_design picorv32_sobel_soc"]
    for key in ("CLOCK_PERIOD","OUTPUT_CAP_LOAD","MAX_FANOUT_CONSTRAINT","MAX_TRANSITION_CONSTRAINT","MAX_CAPACITANCE_CONSTRAINT"):
        tcl.append(f"set ::env({key}) {flow.config[key]}")
    tcl += [f"read_sdc {{{flow.config['PNR_SDC_FILE']}}}","puts {SDC LOAD PASS: port-only declaration; no timing/physical results}","exit"]
    (output/"load_sdc.tcl").write_text("\n".join(tcl)+"\n")
    r = subprocess.run(["openroad","-exit",str(output/"load_sdc.tcl")],text=True,
                       stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    (output/"sdc_load.log").write_text(r.stdout)
    print(r.stdout)
    require(r.returncode == 0 and "SDC LOAD PASS:" in r.stdout and not re.search(r"\[ERROR|^Error",r.stdout,re.M), "SDC loading failed")
    print(f"ASIC PRECHECK PASS: config loaded; standalone lint passed; Classic has {len(flow.Steps)} steps (78 original + 3 repair additions)")
    print("Lint uses 33 reviewed, exact-line upstream style annotations; see upstream_lint_review.json.")
    print("No simulation, synthesis, floorplan, routing or physical checker was run.")


def freeze(tag):
    require(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}",tag), "Unsafe RUN name")
    require(not (ROOT / "runs" / tag).exists(), "RUN exists; use new tag")
    dest = ROOT / "run_inputs" / tag
    record = require_functional()
    dest.mkdir(parents=True, exist_ok=False)
    for name in ("rtl","tb","firmware","third_party","scripts"):
        shutil.copytree(ROOT/name,dest/name,ignore=shutil.ignore_patterns("__pycache__","*.pyc"))
    for name in ("config.json","constraints.sdc","pin_order.cfg","README.md","ARCHITECTURE.md",
                 "OPENLANE_WORKFLOW_NOTES.md","AGENTS.md","ASIC_RUN_GUIDE.md","ASIC_BASE01_REVIEW.md","ASIC_REPAIR02_REVIEW.md","ASIC_REPAIR03_REVIEW.md","ASIC_REPAIR04_REVIEW.md","ASIC_REPAIR06_REVIEW.md","ASIC_REPAIR07_REVIEW.md","ASIC_REPAIR08_REVIEW.md"):
        shutil.copy2(ROOT/name,dest/name)
    for name,digest in record["functional_sources"].items():
        require(sha((dest/name).read_bytes()) == digest,"Source changed while freezing: "+name)
    shutil.copy2(ROOT / "reports" / (TEST+".zip"),dest / "functional_evidence.zip")
    save(dest / "functional_link.json",record)
    prepare_sources(dest)
    def bind(v):
        if isinstance(v,str) and v.startswith("dir::"):
            path = (dest/v[5:]).resolve()
            require(path.is_relative_to(dest.resolve()) and path.is_file(),"Bad config path: "+v)
            return "/work/run_inputs/"+tag+"/"+v[5:]
        if isinstance(v,list): return [bind(x) for x in v]
        if isinstance(v,dict): return {k:bind(x) for k,x in v.items()}
        return v
    save(dest / "config.frozen.json",bind(json.loads((dest/"config.json").read_text())))
    save(dest / "source_sha256.json",{p.relative_to(dest).as_posix():sha(p.read_bytes()) for p in sorted(dest.rglob("*")) if p.is_file()})
    print("FROZEN INPUTS:",dest)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action",choices=["validate","check-openlane","freeze"])
    p.add_argument("arguments",nargs="*")
    args = p.parse_args()
    if args.action == "validate": validate()
    elif args.action == "freeze": freeze(args.arguments[0])
    else: check_openlane(Path(args.arguments[0]),Path(args.arguments[1]))


if __name__ == "__main__":
    try:
        main()
    except (ValueError,OSError,KeyError,IndexError) as e:
        raise SystemExit("ERROR: "+str(e))
