"""Real OpenLane env serialization and wrapper loading; upstream flow is a stub.

No Step.start, CTS, repair, routing, simulation or design database is executed.
"""
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from openlane.steps.tclstep import TclStep


def main():
    scripts = Path(__file__).resolve().parent
    output = Path(sys.argv[1])
    output.mkdir(parents=True, exist_ok=False)
    upstream = output / "mock upstream scripts" / "openroad"
    upstream.mkdir(parents=True)
    cases = (("cts_fanout.tcl", "cts.tcl", "clock_tree_synthesis", "sobel_call_cts"),
             ("repair_design_fanout.tcl", "repair_design_postgrt.tcl", "repair_design", "sobel_call_repair_design"))
    for wrapper, native_file, command, hook in cases:
        # The stub does not invoke the command. It only checks that the real
        # wrapper installed its hook and loaded all serialized configuration.
        (upstream / native_file).write_text(
            'source $::env(_TCL_ENV_IN)\n'
            'if {$::env(SOBEL_CTS_FANOUT_TARGET) != 6 || '
            '$::env(SOBEL_SIGNAL_FANOUT_TARGET) != 5 || '
            '$::env(MAX_FANOUT_CONSTRAINT) != 10} {error "Wrong serialized config"}\n'
            f'if {{[string first {hook} [info body {command}]] < 0}} {{error "Hook missing"}}\n'
            'puts {WRAPPER ENV LOAD PASS: upstream stub reached; no physical commands}\n')
        for broken in (True, False):
            folder = output / (Path(wrapper).stem + ("_old_failure" if broken else "_fixed"))
            folder.mkdir()
            candidate = scripts / wrapper
            if broken:
                text = candidate.read_text()
                loader = 'source $::env(_TCL_ENV_IN)\n'
                assert text.count(loader) == 1
                candidate = folder / wrapper
                candidate.write_text(text.replace(loader, '', 1))
            env = dict(os.environ)
            env.update(SOBEL_SCRIPT_DIR=str(scripts), SCRIPTS_DIR=str(upstream.parent),
                       SOBEL_CTS_FANOUT_TARGET='6', SOBEL_SIGNAL_FANOUT_TARGET='5',
                       MAX_FANOUT_CONSTRAINT='10')
            # Exactly the installed serialization used by TclStep.run_subprocess.
            routed = TclStep._reroute_env(SimpleNamespace(step_dir=str(folder)), env)
            assert 'SOBEL_SCRIPT_DIR' not in routed, 'Fixture must reproduce file-only custom environment'
            assert 'SOBEL_SCRIPT_DIR' in Path(routed['_TCL_ENV_IN']).read_text()
            result = subprocess.run(['openroad', '-exit', '-no_splash', str(candidate)],
                                    env=routed, text=True, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, timeout=30)
            (folder / 'load.log').write_text(result.stdout)
            if broken:
                assert result.returncode != 0 and 'SOBEL_SCRIPT_DIR' in result.stdout, result.stdout
                assert 'WRAPPER ENV LOAD PASS:' not in result.stdout
                print(f'OLD FAILURE REPRODUCED: {wrapper}')
            else:
                assert result.returncode == 0 and 'WRAPPER ENV LOAD PASS:' in result.stdout, result.stdout
                print(f'FIXED WRAPPER LOAD PASS: {wrapper}')
    print('FANOUT ENV REGRESSION PASS: both real wrappers loaded via installed OpenLane env serialization; upstream stubs only.')


if __name__ == '__main__':
    main()
