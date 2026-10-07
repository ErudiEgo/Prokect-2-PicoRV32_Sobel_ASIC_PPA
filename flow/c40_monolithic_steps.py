"""OpenLane Classic stage used by the user-run 79-stage C40 reproduction."""
import hashlib
import json
from pathlib import Path
import subprocess

from openlane.common import Path as OLPath
from openlane.config import Variable
from openlane.state import DesignFormat
from openlane.steps import Step
from openlane.steps.step import CompositeStep


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def odb_view_update(path):
    """Return an OpenLane-typed ODB view update, not pathlib.Path."""
    return {DesignFormat.ODB: OLPath(str(path))}


class C40GuidedDatabase(Step):
    id = "H3.C40GuidedDatabase"
    name = "C40 Frozen Routed ECO Checkpoint Rejoin"
    inputs = [DesignFormat.ODB]
    outputs = [DesignFormat.ODB]
    config_vars = [
        Variable("C40_GUIDANCE_ODB", str, "Exact RUN304 topology/placement reference"),
        Variable("C40_GUIDANCE_SHA256", str, "SHA256 of the RUN304 reference ODB"),
        Variable("C40_STAGE43_BASELINE_ODB", str, "Frozen stage-43 structural baseline"),
        Variable("C40_STAGE43_SHA256", str, "Expected deterministic pre-rejoin ODB SHA256"),
    ]

    def run(self, state_in, **kwargs):
        source = Path(state_in[DesignFormat.ODB])
        output = Path(self.step_dir) / "picorv32_h3_logic_ppa.odb"
        report = Path(self.step_dir) / "guided_rejoin.json"
        script = Path(__file__).with_name("c40_monolithic_rejoin.py")
        command = ["openroad", "-exit", "-no_splash", "-python", str(script),
                   "--input", str(source),
                   "--baseline", self.config["C40_STAGE43_BASELINE_ODB"],
                   "--reference", self.config["C40_GUIDANCE_ODB"],
                   "--output", str(output), "--report", str(report),
                   "--baseline-sha", self.config["C40_STAGE43_SHA256"],
                   "--reference-sha", self.config["C40_GUIDANCE_SHA256"]]
        process = subprocess.run(command, text=True, stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT)
        (Path(self.step_dir) / "guided_rejoin.log").write_text(process.stdout)
        print(process.stdout, end="", flush=True)
        process.check_returncode()
        result = json.loads(report.read_text())
        if (result.get("status") != "C40_MONOLITHIC_GUIDED_REJOIN_PASS"
                or result.get("input_odb_sha256") != sha(source)
                or result.get("baseline_odb_sha256") != self.config["C40_STAGE43_SHA256"]
                or result.get("input_structural_identity") != "PASS"
                or result.get("output_odb_sha256") != sha(output)
                or result.get("destroyed_detailed_wires") != 0
                or result.get("cleared_route_guides") != 0
                or result.get("ordinary_nets_unrouted") != 0
                or result.get("routing_after", {}).get(
                    "ordinary_nets_with_detailed_wires", 0) < 43000):
            raise ValueError("Guided rejoin report/output linkage failed")
        return odb_view_update(output), {
            "c40__guided_rejoin__instance_count": result["output_summary"]["instances"],
            "c40__guided_rejoin__removed_fill_count": result["removed_replaceable_fill_decap"],
            "c40__guided_rejoin__unrouted_net_count": result["ordinary_nets_unrouted"],
            "c40__guided_rejoin__preserved_wired_net_count": result["routing_after"]["ordinary_nets_with_detailed_wires"],
        }


@Step.factory.register()
class C40GuidedRejoin(CompositeStep):
    id = "H3.C40GuidedRejoin"
    name = "C40 Guided Routed ECO Checkpoint Rejoin"
    Steps = [C40GuidedDatabase]

    def run(self, state_in, **kwargs):
        state = state_in
        stages = ((C40GuidedDatabase, "01-guided-routed-checkpoint"),)
        for cls, name in stages:
            state = cls(self.config, state).start(
                toolbox=self.toolbox, step_dir=str(Path(self.step_dir) / name),
                _no_rule=True)
        views = {fmt: state[fmt] for fmt in self.outputs
                 if state.get(fmt) != state_in.get(fmt)}
        metrics = {key: value for key, value in state.metrics.items()
                   if state_in.metrics.get(key) != value}
        return views, metrics
