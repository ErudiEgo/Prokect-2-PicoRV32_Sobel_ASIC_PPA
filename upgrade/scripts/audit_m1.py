"""Audit existing M1 RUNs only. Never launches simulation or physical tools."""
import argparse
import json
from pathlib import Path
import shutil
import tempfile

from evidence import sha, load_image, golden, verify_mode
from profile_contract import derive_metrics
from stage2_project import validate_project
from run16_basis import validate_run16_rtl


def within(root, relative):
    path = (root/relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f'Unsafe evidence path: {relative}')
    return path


def audit(run):
    run = Path(run).resolve()
    cfg = json.loads((run/'run_config.json').read_text())
    result = json.loads((run/'comparison.json').read_text())
    if cfg.get('project_id') != 'picorv32_sobel_stage2' or result.get('status') != 'PASS':
        raise ValueError(f'Not a passing stage2 RUN: {run}')
    if cfg.get('milestone') != 'M1_baseline_and_profile' or cfg.get('accelerator') != 'tile_dma_v1':
        raise ValueError('Not the M1 architecture')
    frozen=run/'inputs'
    hashes=json.loads((run/'inputs.sha256.json').read_text())
    actual={p.relative_to(frozen).as_posix() for p in frozen.rglob('*') if p.is_file()}
    if actual != set(hashes):
        raise ValueError('Frozen snapshot inventory mismatch')
    for name,digest in hashes.items():
        if sha(within(frozen,name)) != digest:
            raise ValueError(f'Frozen hash mismatch: {name}')
    validate_project(frozen)
    if json.loads((run/'run16_rtl_basis.json').read_text()) != validate_run16_rtl(frozen):
        raise ValueError('RUN16 source-basis record mismatch')
    if cfg.get('run') != run.name or result.get('run') != run.name:
        raise ValueError('RUN identity mismatch')
    commands=json.loads((run/'commands.json').read_text())
    if len(commands)!=12 or any(cmd.get('exit_code')!=0 for cmd in commands):
        raise ValueError('Incomplete/failed compile or simulation command records')
    markers={
        'tb_sobel_core':'TEST PASS: sobel_core 1283 vectors; latency, busy, done, reset checked',
        'tb_sobel_mmio':'TEST PASS: sobel_mmio register, handshake, arithmetic, error and reset checks',
        'tb_sobel_tile':'TEST PASS: sobel_tile borders, partial tiles, byte lanes, stalls, busy protection and reset',
        'tb_native_bus_arbiter':'TEST PASS: native_bus_arbiter contention, backpressure, ownership and reset',
    }
    for top,marker in markers.items():
        if marker not in (run/top/'simulation.log').read_text().splitlines():
            raise ValueError(f'Missing actual unit-test completion: {top}')
    expected_evidence={'run16_rtl_basis.json'}
    meta,pixels=load_image(frozen/'image')
    w,h,c=meta['width'],meta['height'],meta.get('channels',1)
    if result.get('width')!=w or result.get('height')!=h or result.get('channels')!=c:
        raise ValueError('Comparison metadata mismatch')
    for mode in ('sw','hw'):
        expected_evidence.update(f'{mode}/{name}' for name in (
            'pixels.csv','tiles.csv','execution.json','profile.json','stage2_metrics.json',
            'output.ppm' if c==3 else 'output.pgm'))
    if set(result['evidence_sha256']) != expected_evidence:
        raise ValueError('Missing/extra evidence hash entries')
    for name,digest in result['evidence_sha256'].items():
        if sha(within(run,name)) != digest:
            raise ValueError(f'Evidence hash mismatch: {name}')
    expected=golden(pixels,w,h,c)
    measurements={}
    for index,mode in enumerate(('sw','hw')):
        directory=run/mode
        # The existing checker writes its verified image. Use a disposable copy
        # so auditing never touches original evidence, even on failure.
        with tempfile.TemporaryDirectory(prefix='s2_audit_') as temporary:
            scratch=Path(temporary)
            for name in ('pixels.csv','tiles.csv','execution.json'):
                shutil.copy2(directory/name,scratch/name)
            checked=verify_mode(scratch,index,w,h,cfg['tile'],cfg['memory_wait'],expected,c)
            output='output.ppm' if c==3 else 'output.pgm'
            if sha(scratch/output)!=sha(directory/output):
                raise ValueError('Verified output bytes differ')
        for key,value in checked.items():
            if result['modes'][mode].get(key)!=value:
                raise ValueError(f'Comparison {mode}/{key} differs from traces')
        execution=json.loads((directory/'execution.json').read_text())
        metrics=derive_metrics(directory,execution,index)
        if metrics!=json.loads((directory/'stage2_metrics.json').read_text()) or metrics!=result['modes'][mode]['stage2_metrics']:
            raise ValueError('Derived metrics differ from measured evidence')
        profile=json.loads((directory/'profile.json').read_text())
        if profile!=result['modes'][mode]['profile']:
            raise ValueError('Comparison profile differs from measured counters')
        measurements[mode]={'cycles':checked['cycles'],'metrics':metrics}
    ratio=measurements['sw']['cycles']/measurements['hw']['cycles']
    if ratio!=result['sw_cycles_div_hw_cycles']:
        raise ValueError('Speedup does not match measured cycles')
    return {'run':run.name,'configuration':[w,h,c,cfg['tile'],cfg['memory_wait']],
            'measurements':measurements,'speedup_vs_S0':ratio,
            'snapshot_sha256':sha(run/'inputs.sha256.json'),
            'comparison_sha256':sha(run/'comparison.json')}, hashes


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('runs',nargs=3,type=Path,help='RGB32 wait1, RGB17x19 wait3, gray37x35 wait1; order does not matter')
    args=parser.parse_args()
    verified=[audit(run) for run in args.runs]
    wanted={(32,32,3,16,1),(17,19,3,16,3),(37,35,1,16,1)}
    if {tuple(item['configuration']) for item,_ in verified}!=wanted:
        raise ValueError('M1 requires exactly the three prescribed cases')
    common=[{k:v for k,v in hashes.items() if not k.startswith('image/')} for _,hashes in verified]
    if any(hashes!=common[0] for hashes in common[1:]):
        raise ValueError('M1 cases used different source snapshots')
    # Input identity is part of the gate, not merely dimensions.
    fixture_by_shape={(32,32,3):'rgb_smoke32_v1',(17,19,3):'rgb_partial17x19_v1',(37,35,1):'demo'}
    for path,(item,_) in zip(args.runs,verified):
        shape=tuple(item['configuration'][:3])
        manifest=json.loads((path/'inputs/baseline/import_manifest.json').read_text())
        digest=manifest['files'][f'inputs/{fixture_by_shape[shape]}/image.hex']
        if sha(path/'inputs/image/image.hex')!=digest:
            raise ValueError('M1 input differs from preserved baseline fixture')
        if shape==(32,32,3):
            if [item['measurements'][m]['cycles'] for m in ('sw','hw')]!=[1352946,206960]:
                raise ValueError('Observer/baseline regression: RGB32 cycles differ from audited historical RUN; investigate, do not force PASS')
    print(json.dumps({'status':'STAGE2_M1_ACCEPTANCE_PASS','runs':[item for item,_ in verified],
                      'limits':'Only M1 functional regression/profile audit. DMA v2/S1/RGB480 not implemented; stage2 ASIC NOT_RUN.'},indent=2))


if __name__=='__main__':
    main()
