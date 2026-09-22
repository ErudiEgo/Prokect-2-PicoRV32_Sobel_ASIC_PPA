"""Registered Classic extension. Importing it never runs a physical step.

Execution belongs exclusively to the user-run OpenLane command. Each round
has its own reports and uses actual post-detailed-route antenna violations.
"""
import json
from pathlib import Path
from openlane.config import Variable
from openlane.logging import info
from openlane.state import DesignFormat
from openlane.steps import Step, OdbpyStep
from openlane.steps.step import CompositeStep
from antenna_targets import checked_targets

CheckAntennas = Step.factory.get('OpenROAD.CheckAntennas')
DetailedPlacement = Step.factory.get('OpenROAD.DetailedPlacement')
RepairDesign = Step.factory.get('OpenROAD.RepairDesignPostGRT')
RepairTiming = Step.factory.get('OpenROAD.ResizerTimingPostGRT')
DetailedRouting = Step.factory.get('OpenROAD.DetailedRouting')
GlobalRouting = Step.factory.get('OpenROAD.GlobalRouting')
CTS = Step.factory.get("OpenROAD.CTS")


@Step.factory.register()
class CTSWithFanoutMargin(CTS):
    """Run the original CTS with temporary master-cell fanout headroom."""
    id = "Sobel.CTSWithFanoutMargin"
    name = "Clock Tree Synthesis with Fanout Headroom"
    config_vars = CTS.config_vars + [Variable(
        "SOBEL_CTS_FANOUT_TARGET", int,
        "Optimization-only clock-buffer fanout target; final SDC remains unchanged", default=6), Variable(
        "SOBEL_CTS_BRANCH_BUFFER_DISTANCE", int,
        "Minimum branch length in microns for an endpoint buffer with CTS spacing enabled", default=1)]

    def get_script_path(self):
        return str(Path(__file__).with_name("cts_fanout.tcl"))

    def run(self, state_in, **kwargs):
        kwargs, env = self.extract_env(kwargs)
        env["SOBEL_SCRIPT_DIR"] = str(Path(__file__).resolve().parent)
        return super().run(state_in, env=env, **kwargs)


@Step.factory.register()
class RepairDesignSlowCorner(RepairDesign):
    """Repair the SS electrical limits before the normal multi-corner timing step."""
    id = "Sobel.RepairDesignSlowCorner"
    name = "Electrical Design Repair at Slow Corner"
    config_vars = RepairDesign.config_vars + [Variable(
        "SOBEL_DESIGN_REPAIR_CORNERS", list[str],
        "Liberty corner used for this extra electrical repair; signoff corners remain unchanged",
        default=["max_ss_100C_1v60"]), Variable(
        "SOBEL_SIGNAL_FANOUT_TARGET", int,
        "Temporary resizer target reserving fanout budget for diode loads", default=5), Variable(
        "SOBEL_POST_FANOUT_MARGIN_PCT", int,
        "Second electrical pass slew/cap optimization margin after fanout buffering", default=70)]

    def get_script_path(self):
        return str(Path(__file__).with_name("repair_design_fanout.tcl"))

    def run(self, state_in, **kwargs):
        kwargs, env = self.extract_env(kwargs)
        env["SOBEL_SCRIPT_DIR"] = str(Path(__file__).resolve().parent)
        return super().run(state_in, corners_key="SOBEL_DESIGN_REPAIR_CORNERS", env=env, **kwargs)


class TargetedDiodes(OdbpyStep):
    id = 'Sobel.TargetedDiodes'
    config_vars = [Variable('SOBEL_ANTENNA_TARGETS', str, 'Exact targets from the preceding independent antenna report')]

    def get_script_path(self):
        return str(Path(__file__).with_name('targeted_diodes.py'))

    def run(self, state_in, **kwargs):
        kwargs, env = self.extract_env(kwargs)
        env['PYTHONPATH'] = str(Path(__file__).parent) + ':' + env.get('PYTHONPATH', '')
        return super().run(state_in, env=env, **kwargs)

    def get_command(self):
        cell, pin = self.config['DIODE_CELL'].split('/')
        return super().get_command() + ['--targets', self.config['SOBEL_ANTENNA_TARGETS'],
                                        '--diode-cell', cell, '--diode-pin', pin]


class VerifyAntennaTopology(OdbpyStep):
    id = 'Sobel.VerifyAntennaTopology'
    config_vars = [Variable('SOBEL_TOPOLOGY_REFERENCE', str, 'Connectivity immediately after diode insertion')]

    def run(self, state_in, **kwargs):
        kwargs, env = self.extract_env(kwargs)
        env['PYTHONPATH'] = str(Path(__file__).parent) + ':' + env.get('PYTHONPATH', '')
        return super().run(state_in, env=env, **kwargs)

    def get_script_path(self):
        return str(Path(__file__).with_name('verify_antenna_topology.py'))

    def get_command(self):
        return OdbpyStep.get_command(self) + ['--reference', self.config['SOBEL_TOPOLOGY_REFERENCE']]


class CaptureAntennaTopology(VerifyAntennaTopology):
    id = 'Sobel.CaptureAntennaTopology'

    def get_script_path(self):
        return str(Path(__file__).with_name('capture_antenna_topology.py'))


class NativeAntennaRepair(GlobalRouting):
    id = 'Sobel.NativeAntennaRepair'
    config_vars = GlobalRouting.config_vars + [v for v in DetailedRouting.config_vars if v.name == 'DRT_THREADS']

    def get_script_path(self):
        return str(Path(__file__).with_name('native_antenna_repair.tcl'))


class OutputBufferEco(VerifyAntennaTopology):
    id = 'Sobel.OutputBufferEco'

    def get_script_path(self):
        return str(Path(__file__).with_name('output_buffer_eco.py'))


class CleanMovedWires(OutputBufferEco):
    id = 'Sobel.CleanMovedWires'

    def get_command(self):
        return super().get_command() + ['--mode', 'cleanup']


class VerifyOutputBuffers(OutputBufferEco):
    id = 'Sobel.VerifyOutputBuffers'

    def get_command(self):
        return super().get_command() + ['--mode', 'verify']


class VerifyNativeTopology(VerifyAntennaTopology):
    id = 'Sobel.VerifyNativeTopology'

    def get_command(self):
        cell, pin = self.config['DIODE_CELL'].split('/')
        return super().get_command() + ['--allow-added-diodes', '--diode-cell', cell, '--diode-pin', pin]


def routing_steps(iteration, antenna_only=False):
    # First attempt is comparable to RUN 6. Later attempts must not resize
    # gates or split diode-protected nets after adding protection.
    if iteration == 0 and not antenna_only:
        return [(RepairDesign, '04-repair-electrical-ss', {'RSZ_CORNERS': ['max_ss_100C_1v60']}),
                (RepairTiming, '05-repair-timing', {})]
    return [(GlobalRouting, '04-global-routing', {})]


@Step.factory.register()
class AntennaClosure(CompositeStep):
    id = 'Sobel.AntennaClosure'
    name = 'Targeted Antenna Repair after Detailed Routing'
    # Used to derive output formats. Inner steps always use Step.start so their
    # config, ODB, logs and state snapshots receive standard OpenLane handling.
    Steps = [CheckAntennas, TargetedDiodes, DetailedPlacement, RepairDesign,
             RepairTiming, GlobalRouting, DetailedRouting, VerifyAntennaTopology,
             CaptureAntennaTopology, NativeAntennaRepair, VerifyNativeTopology,
             OutputBufferEco, CleanMovedWires, VerifyOutputBuffers]

    def run(self, state_in, **kwargs):
        state = state_in
        history = []
        antenna_only = self.config['SOBEL_ANTENNA_ONLY']

        def run_step(cls, directory, **overrides):
            nonlocal state
            step = cls(self.config, state, **overrides)
            state = step.start(toolbox=self.toolbox, step_dir=str(directory), _no_rule=True)
            return step

        if self.config['SOBEL_OUTPUT_BUFFER_REPAIR']:
            if not antenna_only:
                raise ValueError('Output buffer ECO requires an explicit routed continuation')
            folder = Path(self.step_dir) / 'electrical_eco'
            reference = str(folder / 'output_buffer_reference.json')
            folder.mkdir(parents=True, exist_ok=True)
            run_step(OutputBufferEco, folder/'01-insert-buffers', SOBEL_TOPOLOGY_REFERENCE=reference)
            run_step(DetailedPlacement, folder/'02-legalize')
            run_step(CleanMovedWires, folder/'03-clean-moved-wires', SOBEL_TOPOLOGY_REFERENCE=reference)
            run_step(GlobalRouting, folder/'04-global-routing')
            run_step(DetailedRouting, folder/'05-detailed-routing')
            run_step(VerifyOutputBuffers, folder/'06-verify-buffers', SOBEL_TOPOLOGY_REFERENCE=reference)

        # Three targeted repair attempts maximum. Always check the final result;
        # zero violation metrics are never written by this controller.
        for iteration in range(4):
            folder = Path(self.step_dir) / f'round_{iteration:02d}'
            check = run_step(CheckAntennas, folder / '01-check-antennas')
            report = Path(check.step_dir) / 'reports/antenna.rpt'
            targets = checked_targets(report.read_text(),
                                      state.metrics['antenna__violating__nets'],
                                      state.metrics['antenna__violating__pins'])
            target_file = folder / 'targets.json'
            target_file.write_text(json.dumps(targets, indent=2)+'\n')
            history.append({'round': iteration, 'nets': state.metrics['antenna__violating__nets'],
                            'pins': len(targets), 'report': str(report), 'targets': str(target_file)})
            (Path(self.step_dir)/'closure_history.json').write_text(json.dumps(history, indent=2)+'\n')
            if not targets:
                info('Independent post-DRT antenna check has zero violating nets/pins.')
                break
            if iteration == 3:
                self.warn('Targeted antenna repair limit reached; remaining violations are retained. Read final checkers; this is not PASS.')
                break
            if antenna_only or self.config["SOBEL_NATIVE_ANTENNA_REPAIR"]:
                reference = str(folder/'topology_before_native.json')
                info(f'Native post-DRT round {iteration+1}/3: preserve routed wires, repair antennas incrementally, then DRT and topology check.')
                run_step(CaptureAntennaTopology, folder/'02-capture-topology', SOBEL_TOPOLOGY_REFERENCE=reference)
                run_step(NativeAntennaRepair, folder/'03-native-antenna-repair')
                run_step(DetailedRouting, folder/'06-detailed-routing')
                run_step(VerifyNativeTopology, folder/'07-verify-topology', SOBEL_TOPOLOGY_REFERENCE=reference)
                continue
            mode = 'electrical/timing repair'  if iteration == 0 and not antenna_only else 'antenna-only routing with topology guard'
            info(f'Targeted round {iteration+1}/3: add one diode at each of {len(targets)} reported pins, legalize, {mode}.')
            run_step(TargetedDiodes, folder/'02-targeted-diodes', SOBEL_ANTENNA_TARGETS=str(target_file))
            run_step(DetailedPlacement, folder/'03-legalize')
            for cls, directory, overrides in routing_steps(iteration, antenna_only):
                run_step(cls, folder/directory, **overrides)
            run_step(DetailedRouting, folder/'06-detailed-routing')
            if iteration > 0 or antenna_only:
                run_step(VerifyAntennaTopology, folder/'07-verify-topology',
                         SOBEL_TOPOLOGY_REFERENCE=str(folder/'topology_after_diodes.json'))
        views = {fmt: state[fmt] for fmt in self.outputs if state.get(fmt) != state_in.get(fmt)}
        metrics = {k: v for k, v in state.metrics.items() if state_in.metrics.get(k) != v}
        return views, metrics


# A per-round path is supplied to the child only, never by the user's config.
AntennaClosure.config_vars = [v for v in AntennaClosure.config_vars if v.name not in ('SOBEL_ANTENNA_TARGETS', 'SOBEL_TOPOLOGY_REFERENCE')]

AntennaClosure.config_vars.append(Variable('SOBEL_ANTENNA_ONLY', bool,
    'Resume a completed antenna closure checkpoint without resizing logic', default=False))

AntennaClosure.config_vars.append(Variable("SOBEL_OUTPUT_BUFFER_REPAIR", bool,
    "Insert two reviewed non-inverting output buffers before antenna closure", default=False))

AntennaClosure.config_vars.append(Variable("SOBEL_NATIVE_ANTENNA_REPAIR", bool,
    "Use native post-DRT antenna repair on the current RUN wires; no parent checkpoint required", default=False))
