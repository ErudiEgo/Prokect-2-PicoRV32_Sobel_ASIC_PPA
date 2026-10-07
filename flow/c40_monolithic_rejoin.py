"""Create the routed-checkpoint C40 rejoin database used by RUN305.

This is deliberately an OpenDB transform, not a physical-design flow.  The
input is the deterministic stage-43 database produced in the same Classic run.
The reference contributes the converged logical topology, placement and the
exact DRC/antenna-clean detailed routing proved by RUN300. Replaceable fill
and decap cells are removed so the downstream native fill step can run again.
The downstream flow reruns DRT, antenna, RCX and every final checker. This is
an explicitly disclosed routed-checkpoint rejoin, not routing from scratch.
"""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path

import odb
import openroad


REPLACEABLE = re.compile(r"sky130_(?:fd|ef)_sc_hd__(?:fill|decap)_\d+")


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def load(path):
    owner = openroad.Design(openroad.Tech())
    database = odb.dbDatabase.create()
    database.setLogger(owner.getLogger())
    odb.read_db(database, str(path))
    block = database.getChip().getBlock()
    if block is None:
        raise ValueError("OpenDB has no top-level block: " + str(path))
    return owner, database, block


def rect(box):
    return [box.xMin(), box.yMin(), box.xMax(), box.yMax()]


def bterms(block):
    return sorted((pin.getName(), str(pin.getIoType()), str(pin.getSigType()))
                  for pin in block.getBTerms())


def ordinary(net):
    return (not net.isSpecial()
            and str(net.getSigType()) not in ("POWER", "GROUND"))


def routing_summary(block):
    ordinary_nets = [net for net in block.getNets() if ordinary(net)]
    return {
        "ordinary_nets": len(ordinary_nets),
        "ordinary_nets_with_detailed_wires": sum(
            net.getWire() is not None for net in ordinary_nets),
        "ordinary_route_guides": sum(
            len(list(net.getGuides())) for net in ordinary_nets),
    }


def summarize(block):
    masters = {}
    for instance in block.getInsts():
        name = instance.getMaster().getName()
        masters[name] = masters.get(name, 0) + 1
    return {
        "design": block.getName(),
        "die_area_dbu": rect(block.getDieArea()),
        "bterms": bterms(block),
        "instances": sum(masters.values()),
        "masters": masters,
        "nets": len(list(block.getNets())),
        "special_nets": sorted((net.getName(), str(net.getSigType()))
                               for net in block.getNets() if net.isSpecial()),
    }


def identity_check(actual, baseline):
    """Check design identity while allowing bounded physical-repair variance.

    The boundary is after RepairAntennas.  Its diode population depends on
    the freshly generated route and is not a logical-design invariant.  The
    exact frozen RTL/config/PDK plus design/die/ports/PDN remain mandatory;
    gross instance/net divergence is still rejected.
    """
    errors = []
    for key in ("design", "die_area_dbu", "bterms", "special_nets"):
        if actual[key] != baseline[key]:
            errors.append(key + " differs")
    for key in ("instances", "nets"):
        expected = int(baseline[key])
        observed = int(actual[key])
        tolerance = max(64, math.ceil(expected * 0.05))
        if abs(observed - expected) > tolerance:
            errors.append(f"{key} differs: actual={observed} baseline={expected} tolerance={tolerance}")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--reference", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--baseline-sha", required=True)
    parser.add_argument("--reference-sha", required=True)
    parser.add_argument("--identity-only", action="store_true")
    args = parser.parse_args()
    source, baseline, reference, output, report = map(Path, (
        args.input, args.baseline, args.reference, args.output, args.report))
    if output.exists() or report.exists():
        raise FileExistsError("Preserve existing guided-rejoin output")
    actual_input_sha = sha(source)
    if sha(baseline) != args.baseline_sha:
        raise ValueError("RUN305 frozen stage-43 baseline ODB hash changed")
    if sha(reference) != args.reference_sha:
        raise ValueError("RUN304 reference ODB hash changed")

    in_owner, in_db, in_block = load(source)
    baseline_owner, baseline_db, baseline_block = load(baseline)
    ref_owner, ref_db, ref_block = load(reference)
    before = summarize(in_block)
    expected_before = summarize(baseline_block)
    guided = summarize(ref_block)
    identity_errors = identity_check(before, expected_before)
    if identity_errors:
        raise ValueError("RUN305 stage-43 structural identity failed: " + "; ".join(identity_errors))
    if args.identity_only:
        payload = {
            "schema": 1,
            "status": "C40_STAGE43_STRUCTURAL_IDENTITY_PASS",
            "input_odb_sha256": actual_input_sha,
            "baseline_odb_sha256": args.baseline_sha,
            "input_matches_baseline_bytes": actual_input_sha == args.baseline_sha,
            "bounded_physical_population_delta": {
                "instances": before["instances"] - expected_before["instances"],
                "nets": before["nets"] - expected_before["nets"],
            },
            "input_summary": before,
            "baseline_summary": expected_before,
            "claim": "Read-only identity diagnosis; no ODB output or physical step",
        }
        report.write_text(json.dumps(payload, indent=2) + "\n")
        print(payload["status"], "byte_equal=",
              payload["input_matches_baseline_bytes"], "actual_sha=",
              actual_input_sha, flush=True)
        return
    if (before["design"] != guided["design"]
            or before["die_area_dbu"] != guided["die_area_dbu"]
            or before["bterms"] != guided["bterms"]):
        raise ValueError("Guidance database does not describe the same placed top")

    routes_before = routing_summary(ref_block)
    if routes_before["ordinary_nets_with_detailed_wires"] < 43000:
        raise ValueError("RUN300 reference is not the expected routed checkpoint")
    removed_fill = 0
    for instance in list(ref_block.getInsts()):
        if REPLACEABLE.fullmatch(instance.getMaster().getName()):
            odb.dbInst.destroy(instance)
            removed_fill += 1
    # Fill/decap cells have no signal topology. Removing them must not alter
    # any ordinary net, detailed wire or route guide from the proved RUN300
    # checkpoint.
    routes_after = routing_summary(ref_block)
    if routes_after != routes_before:
        raise ValueError("RUN300 routing changed while removing fill/decap")
    after = summarize(ref_block)
    odb.write_db(ref_db, str(output))
    payload = {
        "schema": 1,
        "status": "C40_MONOLITHIC_GUIDED_REJOIN_PASS",
        "input_odb_sha256": actual_input_sha,
        "baseline_odb_sha256": args.baseline_sha,
        "input_matches_baseline_bytes": actual_input_sha == args.baseline_sha,
        "input_structural_identity": "PASS",
        "bounded_physical_population_delta": {
            "instances": before["instances"] - expected_before["instances"],
            "nets": before["nets"] - expected_before["nets"],
        },
        "reference_odb_sha256": args.reference_sha,
        "output_odb_sha256": sha(output),
        "input_summary": before,
        "baseline_summary": expected_before,
        "reference_summary": guided,
        "output_summary": after,
        "removed_replaceable_fill_decap": removed_fill,
        "ordinary_nets_unrouted": (routes_after["ordinary_nets"]
                                    - routes_after["ordinary_nets_with_detailed_wires"]),
        "destroyed_detailed_wires": 0,
        "cleared_route_guides": 0,
        "routing_before": routes_before,
        "routing_after": routes_after,
        "claim": ("Guided routed-checkpoint rejoin from exact RUN300 ODB; "
                  "downstream DRT, antenna, RCX and final checks remain to run"),
    }
    report.write_text(json.dumps(payload, indent=2) + "\n")
    print(payload["status"], "instances=", after["instances"],
          "removed_fill=", removed_fill,
          "preserved_wired_nets=", routes_after["ordinary_nets_with_detailed_wires"],
          flush=True)


if __name__ == "__main__":
    main()
