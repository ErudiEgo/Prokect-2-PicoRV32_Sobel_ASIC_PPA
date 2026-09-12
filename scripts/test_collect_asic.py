"""Regression check against existing base_01 evidence; no flow or simulation."""
import argparse
from pathlib import Path
from collect_asic import load, check_value, integrity


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("evidence_root",type=Path,help="Root containing extracted runs/ and run_inputs/")
    args = p.parse_args()
    run = args.evidence_root / "runs/picorv32_sobel_clk50_base_01"
    metrics = load(run / "76-misc-reportmanufacturability/state_out.json")["metrics"]
    antenna = load(run / "47-openroad-checkantennas-1/state_out.json")["metrics"]
    # These stages intentionally differ in the real failed RUN. The old code
    # displayed antenna-stage inherited counts alongside post-PNR PASS/FAIL.
    wanted = {
        "design__max_slew_violation__count": 33,
        "design__max_cap_violation__count": 8,
        "design__max_fanout_violation__count": 61,
        "design__max_slew_violation__count__corner:nom_tt_025C_1v80": 0,
        "design__max_cap_violation__count__corner:nom_tt_025C_1v80": 0,
        "post_drt_antenna__violating__nets": 14,
        "post_drt_antenna__violating__pins": 15,
    }
    assert antenna["design__max_slew_violation__count"] != metrics["design__max_slew_violation__count"]
    for key, expected in wanted.items():
        assert check_value(key,metrics,antenna) == expected, key
    assert integrity(args.evidence_root / "run_inputs/picorv32_sobel_clk50_base_01")
    print("COLLECTOR REGRESSION PASS: 7 actual metric values, stage separation and snapshot integrity")
    print("No simulation or physical flow executed; original evidence unchanged")


if __name__ == "__main__":
    main()
