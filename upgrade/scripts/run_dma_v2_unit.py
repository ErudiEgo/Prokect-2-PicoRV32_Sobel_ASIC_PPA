"""USER-RUN ONLY: freeze and exercise the independent TIL2 candidate."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import traceback
from evidence import sha
from run_soc_tests import command, save

ROOT = Path(__file__).resolve().parents[1]
MARKER = 'TEST PASS: sobel_tile_v2 181 cases, exact pixels/read counts, borders, lanes, stalls, descriptor guards and reset'

def verify_log(path):
    lines = path.read_text().splitlines()
    if lines.count(MARKER) != 1:
        raise ValueError('Missing/duplicate unit completion')
    records = [line for line in lines if line.startswith('V2_CASE ')]
    if len(records) != 181:
        raise ValueError('Missing case evidence')
    for index, line in enumerate(records, 1):
        match = re.fullmatch(r'V2_CASE (\d+) frame=(\d+)x(\d+) origin=(\d+),(\d+) tile=(\d+)x(\d+) lane=(\d+) pattern=(\d+) reads=(\d+) writes=(\d+)', line)
        if not match:
            raise ValueError(f'Malformed case: {line}')
        seq,w,h,x,y,tw,th,lane,pattern,reads,writes = map(int, match.groups())
        expected_reads = (min(w,x+tw+1)-max(0,x-1))*(min(h,y+th+1)-max(0,y-1))
        if seq != index or reads != expected_reads or writes != tw*th or not 0<=lane<=3 or not 0<=pattern<=5:
            raise ValueError(f'Invalid case counts: {line}')
    return len(records)

def execute(out):
    commands = []
    status = {'status': 'FAIL_OR_INCOMPLETE', 'scope': 'standalone DMA unit; no RV32, RGB480 or ASIC result'}
    try:
        hashes = json.loads((out/'inputs.sha256.json').read_text())
        if hashes != {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(ROOT.rglob('*')) if p.is_file()}:
            raise ValueError('Frozen source mismatch')
        versions = {'python':sys.version}
        for tool in ('iverilog','vvp'):
            result = subprocess.run([tool,'-V'], capture_output=True, text=True, check=True)
            versions[tool] = result.stdout+result.stderr
        save(out/'tool_versions.json', versions)
        command(['iverilog','-g2012','-Wall','-Wno-timescale','-s','tb_sobel_tile_v2',
                 '-o',str(out/'unit.vvp'),str(ROOT/'rtl/sobel_core.v'),
                 str(ROOT/'candidate/sobel_tile_v2.v'),str(ROOT/'candidate/tb_sobel_tile_v2.sv')],
                out,'compile',120,commands)
        wall = command(['vvp',str(out/'unit.vvp')],out,'simulation',600,commands)
        cases = verify_log(out/'simulation.log')
        status.update(status='DMA_V2_UNIT_FUNCTIONAL_PASS', cases=cases,
                      simulation_wall_seconds=wall, target_cycles='NOT_MEASURED',
                      asic='NOT_RUN', soc_integration='NOT_RUN')
        return 0
    except (Exception,KeyboardInterrupt):
        status['error'] = traceback.format_exc()
        print(status['error'], file=sys.stderr)
        return 1
    finally:
        save(out/'commands.json',commands)
        status['evidence_sha256'] = {name:sha(out/name) for name in
            ('inputs.sha256.json','tool_versions.json','commands.json','compile.log','simulation.log') if (out/name).exists()}
        save(out/'result.json',status)
        (out/'SUMMARY.txt').write_text(json.dumps(status,indent=2)+'\n')
        print(json.dumps(status,indent=2),flush=True)

def main():
    if len(sys.argv)==3 and sys.argv[1]=='--execute-frozen':
        return execute(Path(sys.argv[2]).resolve())
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run')
    args = parser.parse_args()
    if not re.fullmatch(r's2_m3_unit_[A-Za-z0-9_-]{1,60}',args.run):
        parser.error('Use a fresh s2_m3_unit_ RUN name')
    out = ROOT/'reports'/args.run
    if out.exists() or out.with_suffix('.zip').exists():
        parser.error('RUN/archive exists; no overwrite')
    out.mkdir(parents=True)
    try:
        frozen = out/'inputs'
        for name in ('candidate','scripts'):
            shutil.copytree(ROOT/name,frozen/name,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        (frozen/'rtl').mkdir()
        shutil.copy2(ROOT/'rtl/sobel_core.v',frozen/'rtl/sobel_core.v')
        shutil.copy2(ROOT/'DMA_V2_CANDIDATE.md',frozen/'DMA_V2_CANDIDATE.md')
        save(out/'inputs.sha256.json',{p.relative_to(frozen).as_posix():sha(p) for p in sorted(frozen.rglob('*')) if p.is_file()})
        return subprocess.call([sys.executable,str(frozen/'scripts/run_dma_v2_unit.py'),
            '--execute-frozen',str(out)],env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
    finally:
        archive = shutil.make_archive(str(out),'zip',root_dir=out.parent,base_dir=out.name)
        print(f'ARCHIVE: {archive}\nExport this evidence even if the unit fails.',flush=True)

if __name__=='__main__':
    sys.exit(main())
