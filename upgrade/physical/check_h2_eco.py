"""Read-only checkpoint plan, config, lint and host checks. NO physical steps."""
import gzip
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import openlane
from openlane.state import State
import check_ppa


def main(out):
    check_ppa.main(out)
    # Remove generic PASS until the additional ECO gates have passed.
    (out/'PASS.json').unlink()
    state=State.loads(Path('/snapshot/resume_checkpoint/state.json').read_text(),validate_path=True)
    cfg=json.loads((out/'h2/resolved_config.json').read_text())
    if float(cfg['CLOCK_PERIOD'])!=50 or not cfg['SOBEL_ANTENNA_ONLY'] or not cfg['SOBEL_OUTPUT_BUFFER_REPAIR']:
        raise ValueError('Wrong ECO configuration')
    steps=json.loads((out/'h2/steps.json').read_text())
    if steps.count('Sobel.AntennaClosure')!=1: raise ValueError('Ambiguous continuation step')
    # Verify non-inverting buffer truth in each configured library corner.
    for corner, libraries in cfg['LIB'].items():
        found=False
        for path in libraries:
            text=gzip.open(path,'rt').read() if path.endswith('.gz') else Path(path).read_text()
            cells=re.split(r'\bcell\s*\(',text)
            for cell in cells[1:]:
                if not re.match(r'\s*"?sky130_fd_sc_hd__buf_8"?\s*\)',cell): continue
                pins=re.split(r'\bpin\s*\(',cell)
                output=[p for p in pins[1:] if re.match(r'\s*"?X"?\s*\)',p)]
                if len(output)!=1 or not re.search(r'\bfunction\s*:\s*"(?:A|\(A\))"\s*;',output[0]):
                    raise ValueError('Buffer identity function not verified: '+corner)
                found=True
        if not found: raise ValueError('buf_8 missing in '+corner)
    env=dict(os.environ)
    env['PYTHONPATH']=str(Path(openlane.__file__).parent/'scripts/odbpy')+':/design/flow'
    cmd=['openroad','-exit','-python','/design/flow/output_buffer_eco.py','--reference',str(out/'unused_reference.json'),
         '--plan-only',str(state['odb'])]
    p=subprocess.run(cmd,capture_output=True,text=True,env=env)
    (out/'eco_plan.log').write_text(p.stdout+p.stderr)
    print(p.stdout+p.stderr,flush=True); p.check_returncode()
    if 'H2 ECO PLAN PASS:' not in p.stdout: raise ValueError('No plan PASS')
    if (out/'unused_reference.json').exists(): raise ValueError('Plan-only unexpectedly wrote reference')
    check_ppa.run([sys.executable,'/design/test_h2_eco.py'],out/'host_contract_tests.log')
    # Inspect CLI only. Never dispatch a flow during preflight.
    helptext=subprocess.check_output([sys.executable,'/design/flow/openlane_with_repairs.py','--help'],text=True)
    if '--with-initial-state' not in helptext or '--from' not in helptext: raise ValueError('Continuation CLI unavailable')
    (out/'cli_help.txt').write_text(helptext)
    check_ppa.save(out/'PASS.json',{'status':'H2_ECO_STATIC_PREFLIGHT_PASS',
        'limits':'Read-only actual ODB plan, config/lint/host tests only. Physical ECO and closure NOT_RUN.',
        'continuation_step':'Sobel.AntennaClosure','planned_added_buffers':4})
    print('H2 ECO STATIC PREFLIGHT PASS; physical ECO NOT_RUN',flush=True)


if __name__=='__main__': main(Path(sys.argv[1]).resolve())
