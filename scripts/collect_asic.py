"""Read existing ASIC reports. Never launches simulation, synthesis or PNR."""
import argparse
import hashlib
import json
import math
import re
import shutil
import tarfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MISSING = "MISSING"
FIELDS = {
    "standard cell area (um^2)":"design__instance__area__stdcell",
    "standard cell count":"design__instance__count__stdcell",
    "core area (um^2)":"design__core__area",
    "die area (um^2)":"design__die__area",
    "standard cell utilization (ratio)":"design__instance__utilization__stdcell",
    "setup worst slack (ns)":"timing__setup__ws",
    "hold worst slack (ns)":"timing__hold__ws",
    "setup WNS (ns)":"timing__setup__wns",
    "hold WNS (ns)":"timing__hold__wns",
    "setup TNS (ns)":"timing__setup__tns",
    "hold TNS (ns)":"timing__hold__tns",
    "vectorless internal power (W)":"power__internal__total",
    "vectorless switching power (W)":"power__switching__total",
    "leakage power (W)":"power__leakage__total",
    "vectorless total power (W)":"power__total",
    "VPWR worst drop (V)":"design_powergrid__drop__worst__net:VPWR",
    "VGND worst voltage/rise (V)":"design_powergrid__voltage__worst__net:VGND",
    "wirelength (um)":"route__wirelength",
}
ZERO = ["magic__drc_error__count", "klayout__drc_error__count", "design__lvs_error__count",
        "design__xor_difference__count", "magic__illegal_overlap__count", "route__drc_errors",
        "design__max_slew_violation__count", "design__max_cap_violation__count",
        "design__max_fanout_violation__count", "timing__setup_vio__count", "timing__hold_vio__count",
        "design__critical_disconnected_pin__count", "design__power_grid_violation__count"]


def load(path): return json.loads(path.read_text(encoding="utf-8"))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def numeric(v): return isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v)
def stage_number(path): return int(path.name.split("-",1)[0])


def check_value(key, metrics, post_antenna_metrics):
    # Antenna state inherits OLD timing metrics. Use it ONLY for antenna keys.
    if key.startswith("post_drt_antenna__"):
        return post_antenna_metrics.get(key.removeprefix("post_drt_"), MISSING)
    return metrics.get(key, MISSING)


def clean(v):
    if isinstance(v,float) and not math.isfinite(v): return str(v)
    if isinstance(v,dict): return {k:clean(x) for k,x in v.items()}
    if isinstance(v,list): return [clean(x) for x in v]
    return v


def integrity(snapshot):
    try:
        manifest = load(snapshot / "source_sha256.json")
        if not manifest: return False
        for name,digest in manifest.items():
            path = (snapshot/name).resolve()
            if not path.is_relative_to(snapshot.resolve()) or sha(path) != digest: return False
        record = load(snapshot / "functional_link.json")
        if sha(snapshot / "functional_evidence.zip") != record["archive_sha256"]: return False
        return all(sha(snapshot/n) == d for n,d in record["functional_sources"].items())
    except (OSError,ValueError,KeyError): return False


def collect(tag):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}",tag): raise ValueError("Unsafe RUN tag")
    run, snap = ROOT / "runs" / tag, ROOT / "run_inputs" / tag
    if not snap.is_dir() and not run.is_dir():
        raise ValueError("No physical RUN or snapshot. Send precheck log instead.")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out = ROOT / "reports" / (tag + "_collect_" + stamp)
    out.mkdir(parents=True,exist_ok=False)
    stages = sorted([p for p in run.glob("*") if p.is_dir() and re.match(r"^\d+-",p.name)],key=stage_number)
    final = run / "final/metrics.json"
    metric_source = final if final.is_file() else None
    metrics = load(final) if final.is_file() else {}
    if metric_source is None:
        for stage in reversed(stages):
            if (stage / "state_out.json").is_file():
                metric_source = stage / "state_out.json"
                metrics = load(metric_source).get("metrics",{})
                break
    if metric_source is None:
        # A composite may fail after a child completed but before writing its
        # own state_out. Keep that real partial evidence, labelled by its path.
        for stage in reversed(stages):
            completed = sorted(stage.rglob("state_out.json"))
            if completed:
                metric_source = completed[-1]
                metrics = load(metric_source).get("metrics",{})
                break
    resolved = load(run / "resolved.json") if (run / "resolved.json").is_file() else {}
    runtime = {}
    resume_dir = snap / "resume_checkpoint"
    resume = load(resume_dir/"provenance.json") if (resume_dir/"provenance.json").is_file() else None
    resume_valid = bool(resume and integrity(snap) and (resume_dir/"parent_drt_state.json").is_file()
                        and sha(resume_dir/"parent_drt_state.json") == resume.get("parent_state_sha256"))
    if (snap / "runtime.txt").is_file():
        runtime = dict(line.split("=",1) for line in (snap / "runtime.txt").read_text().splitlines() if "=" in line)
    gds = [p for p in (run / "final").rglob("*.gds") if p.stat().st_size>0]
    stage_gds = [p for s in stages for p in s.glob("*.gds") if p.stat().st_size>0]
    drt = [s for s in stages if "-openroad-detailedrouting" in s.name and (s/"state_out.json").is_file()]
    antenna = [s for s in stages if "-openroad-checkantennas" in s.name and (s/"state_out.json").is_file()]
    post_antenna = antenna[-1]/"state_out.json" if antenna and (
        (drt and stage_number(antenna[-1])>stage_number(drt[-1])) or (not drt and resume_valid)) else None
    if post_antenna is None:
        for stage in reversed(stages):
            if not (resume_valid or (drt and stage_number(stage)>stage_number(drt[-1]))): continue
            children = sorted(p.parent.parent/"state_out.json" for p in stage.rglob("reports/antenna.rpt")
                              if (p.parent.parent/"state_out.json").is_file())
            if children:
                post_antenna = children[-1]
                break
    am = load(post_antenna).get("metrics",{}) if post_antenna else {}
    checks = {}
    for key in ZERO:
        v = metrics.get(key)
        checks[key] = MISSING if not numeric(v) else "PASS" if v==0 else "FAIL"
    for key in ("antenna__violating__nets","antenna__violating__pins"):
        v=am.get(key)
        checks["post_drt_"+key] = MISSING if not numeric(v) else "PASS" if v==0 else "FAIL"
    corners = resolved.get("STA_CORNERS",[])
    if not corners: checks["STA_CORNERS"] = MISSING
    for corner in corners:
        for kind in ("setup","hold"):
            key=f"timing__{kind}__ws__corner:{corner}"
            v=metrics.get(key)
            checks[key] = MISSING if not numeric(v) else "PASS" if v>=0 else "FAIL"
    for key,v in metrics.items():
        if key.startswith(("timing__setup_vio__count__","timing__hold_vio__count__",
                           "design__max_slew_violation__count__","design__max_cap_violation__count__")) or key in (
                           "timing__unconstrained__count","timing__unconstrained_endpoint__count","flow__errors__count"):
            checks[key] = MISSING if not numeric(v) else "PASS" if v==0 else "FAIL"
    checks["snapshot_and_functional_integrity"] = "PASS" if integrity(snap) else "FAIL"
    checks["final_metrics"] = "PASS" if final.is_file() else MISSING
    checks["flow_exit_zero"] = "PASS" if runtime.get("openlane_exit_status") == "0" else "FAIL/INCOMPLETE"
    checks["final_gds"] = "PASS" if gds else MISSING
    checks["cts_completed"] = "PASS" if (any(s.name.endswith("-openroad-cts") and (s/"state_out.json").is_file() for s in stages)
        or (resume_valid and (resume_dir/"parent_cts_state.json").is_file())) else MISSING
    if resume is not None: checks["resume_checkpoint_integrity"] = "PASS" if resume_valid else "FAIL"
    checks["physical_clock"] = "PASS" if resolved.get("CLOCK_PORT")=="clk" and resolved.get("RUN_CTS") is True else MISSING
    # Preserve actual congestion tables with their source; no inference from DRC.
    tables=[]
    log_groups = [[resume_dir/"parent_globalrouting.log"]] if resume_valid and (resume_dir/"parent_globalrouting.log").is_file() else []
    log_groups += [sorted(s.rglob("*.log")) for s in stages]
    for logs in log_groups:
        for log in logs:
            for block in log.read_text(errors="replace").split("Final congestion report:")[1:]:
                rows=[]
                for line in block.splitlines():
                    match=re.fullmatch(r"\s*(\S+)\s+(\d+)\s+(\d+)\s+([\d.]+)%\s+(\d+)\s*/\s*(\d+)\s*/\s*(\d+)\s*",line)
                    if match:
                        layer,res,demand,usage,h,v,total=match.groups()
                        rows.append(dict(layer=layer,resource=int(res),demand=int(demand),usage_pct=float(usage),max_h=int(h),max_v=int(v),total_overflow=int(total)))
                        if layer=="Total": break
                if rows and rows[-1]["layer"]=="Total": tables.append(dict(source=str(log.relative_to(ROOT)),rows=rows))
    checks["global_routing_overflow"] = ("PASS" if tables[-1]["rows"][-1]["total_overflow"]==0 else "FAIL") if tables else MISSING
    status = "PASS_FOR_REPORTED_FLOW_CHECKS" if all(v=="PASS" for v in checks.values()) else "FAIL_OR_INCOMPLETE"
    payload = dict(run=tag,status=status,checks=checks,metrics_source=str(metric_source or MISSING),
                   post_drt_antenna_source=str(post_antenna or MISSING),metrics=metrics,post_drt_antenna_metrics=am,
                   resolved=resolved,runtime=runtime,congestion=tables[-1] if tables else MISSING,resume=resume)
    (out/"metrics.json").write_text(json.dumps(clean(payload),indent=2,allow_nan=False)+"\n")
    summary = [f"PHYSICAL RUN: {tag}",f"FLOW CHECK STATUS: {status}",f"METRICS SOURCE: {metric_source or MISSING}",
        "SCOPE: PicoRV32 + Sobel + native bus; excludes external program/image RAM, pads and package.",
        "POWER: vectorless estimates. Simulation cycles/VCD are not switching-activity annotation.",
        "IR DROP: indicative; VSRC_LOC_FILES="+str(resolved.get("VSRC_LOC_FILES"))+
        "; source/load assumptions require review. No board/package source model provided.",
        "LINT: 33 exact-site upstream style annotations documented; physical checkers remain enabled.",
        "This is laboratory flow evidence, not a claim of full chip/tapeout sign-off.","",
        "CONFIGURATION"]
    if resume:
        summary += ["CHECKPOINT PROVENANCE: "+json.dumps(resume),
                    "RUNTIME SCOPE: continuation only; parent synthesis/placement/routing time excluded."]
    summary += [f"{k}: {resolved.get(k,MISSING)}" for k in ("CLOCK_PERIOD","PDK","STD_CELL_LIBRARY","STA_CORNERS","FP_CORE_UTIL","PL_TARGET_DENSITY_PCT","DIE_AREA")]
    summary += [f"{k}: {v}" for k,v in runtime.items()]
    summary += ["","PPA"] + [f"{label}: {metrics.get(key,MISSING)}" for label,key in FIELDS.items()]
    summary += ["","CHECKS"] + [f"{k}: {v}; value={check_value(k,metrics,am)}" for k,v in checks.items()]
    summary += ["","ALL CORNER / POWERGRID / CONGESTION METRICS"] + [f"{k}: {v}" for k,v in sorted(metrics.items()) if "__corner:" in k or re.search("powergrid|power_grid|overflow|congestion",k)]
    summary += ["","GLOBAL ROUTING TABLE",json.dumps(tables[-1] if tables else MISSING,indent=2),"","FINAL GDS"] + ([str(p) for p in gds] or [MISSING])
    summary += ["","STAGE GDS (may exist even when deferred errors prevent final export; NOT sign-off PASS)"] + ([str(p) for p in stage_gds] or [MISSING])
    (out/"SUMMARY.txt").write_text("\n".join(summary)+"\n",encoding="utf-8")
    sta = [s/"summary.rpt" for s in stages if "stapostpnr" in s.name and (s/"summary.rpt").is_file()]
    if sta: shutil.copy2(sta[-1],out/"STA_SUMMARY.rpt")
    # Every collection is new. Preserve all previous exports and RUN data.
    archive = Path(str(out)+".tar.gz")
    with tarfile.open(archive,"x:gz") as tar:
        for p in sorted(snap.rglob("*")):
            if p.is_file(): tar.add(p,arcname=p.relative_to(ROOT))
        for p in sorted(run.rglob("*")):
            if p.is_file() and (p.suffix.lower() in (".json",".log",".rpt",".txt",".sdc",".csv",".gds") or
                               ("final" in p.relative_to(run).parts and p.suffix.lower() in (".gds",".lef"))):
                tar.add(p,arcname=p.relative_to(ROOT))
        console = ROOT/"reports"/(tag+"_console.log")
        if console.is_file(): tar.add(console,arcname=console.relative_to(ROOT))
        tar.add(out,arcname=out.relative_to(ROOT))
    windows=Path("/mnt/e/aa. PPA_Project_List/aaa.PicoRV32_Sobel_ASIC_PPA/reports")
    if windows.parent.is_dir():
        windows.mkdir(exist_ok=True)
        target=windows/archive.name
        with archive.open("rb") as source,target.open("xb") as dest: shutil.copyfileobj(source,dest)
        print("WINDOWS EVIDENCE:",target)
    print("\n".join(summary[:9]))
    print("SUMMARY:",out/"SUMMARY.txt")
    print("ARCHIVE:",archive)
    print("No flow or simulation was rerun. Full ODB/netlists remain in the Ubuntu RUN.")


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run")
    args=parser.parse_args()
    try: collect(args.run)
    except (OSError,ValueError,KeyError) as e: raise SystemExit("ERROR: "+str(e))
