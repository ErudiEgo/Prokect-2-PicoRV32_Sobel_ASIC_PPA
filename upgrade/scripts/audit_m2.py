"""Audit one existing M2 RUN. No simulator/firmware/physical execution."""
import argparse
import json
from pathlib import Path
import shutil
import tempfile
from evidence import sha, load_image, golden
from run16_basis import validate_run16_rtl
from run_m2_tests import check_sources, measure, MODES, UNITS
from audit_m1 import within

def audit(run):
    run=Path(run).resolve()
    frozen=run/'inputs'
    cfg=json.loads((run/'run_config.json').read_text())
    result=json.loads((run/'comparison.json').read_text())
    if result.get('status')!='PASS' or result.get('milestone')!='M2_software_baseline':
        raise ValueError('Not a passing M2 RUN')
    if cfg.get('run')!=run.name or result.get('run')!=run.name or cfg.get('hardware_enable_sobel')!=1:
        raise ValueError('RUN identity/hardware configuration mismatch')
    if cfg.get('mode_identities')!={k:i for k,i,_ in MODES}:
        raise ValueError('Wrong firmware variant identities')
    hashes=json.loads((run/'inputs.sha256.json').read_text())
    if set(hashes)!={p.relative_to(frozen).as_posix() for p in frozen.rglob('*') if p.is_file()}:
        raise ValueError('Frozen source inventory mismatch')
    for name,digest in hashes.items():
        if sha(within(frozen,name))!=digest: raise ValueError(f'Snapshot hash mismatch: {name}')
    check_sources(frozen)
    if json.loads((run/'run16_rtl_basis.json').read_text())!=validate_run16_rtl(frozen):
        raise ValueError('RUN16 hardware identity mismatch')
    meta,pixels=load_image(frozen/'image')
    c=meta.get('channels',1)
    if any(result.get(k)!=meta.get(k,1) or cfg.get(k)!=meta.get(k,1) for k in ('width','height','channels')):
        raise ValueError('Input metadata mismatch')
    required={'run16_rtl_basis.json','run_config.json','tool_versions.json','commands.json'}
    for mode,_,_ in MODES:
        required.update(f'{mode}/{name}' for name in ('pixels.csv','tiles.csv','execution.json','profile.json',
                        'stage2_metrics.json','compile.log','simulation.log','output.ppm' if c==3 else 'output.pgm'))
    for top,_,_ in UNITS: required.update((f'{top}/compile.log',f'{top}/simulation.log'))
    if set(result['evidence_sha256'])!=required: raise ValueError('Incomplete evidence bindings')
    for name,digest in result['evidence_sha256'].items():
        if sha(within(run,name))!=digest: raise ValueError(f'Evidence hash mismatch: {name}')
    commands=json.loads((run/'commands.json').read_text())
    if len(commands)!=14 or any(cmd.get('exit_code')!=0 for cmd in commands):
        raise ValueError('Missing/failed execution records')
    for top,_,marker in UNITS:
        if marker not in (run/top/'simulation.log').read_text().splitlines():
            raise ValueError(f'Missing unit-test completion: {top}')
    expected=golden(pixels,meta['width'],meta['height'],c)
    for index,(name,identity,hex_path) in enumerate(MODES):
        compile_record=commands[8+2*index]
        args=compile_record.get('argv',[])
        if '-Ptb_sobel_soc_m2.ENABLE_SOBEL=1' not in args or f'-Ptb_sobel_soc_m2.FIRMWARE_MODE={identity}' not in args:
            raise ValueError('Compile parameters differ between declared variants')
        with tempfile.TemporaryDirectory(prefix='s2_m2_audit_') as temp:
            d=Path(temp)
            for file in ('pixels.csv','tiles.csv','execution.json','profile.json'):
                shutil.copy2(run/name/file,d/file)
            execution,profile,metrics=measure(d,identity,cfg,meta,expected)
            image='output.ppm' if c==3 else 'output.pgm'
            if sha(d/image)!=sha(run/name/image): raise ValueError('Verified output mismatch')
        saved=result['modes'][name]
        if execution!=saved['execution'] or profile!=saved['profile'] or metrics!=saved['metrics']:
            raise ValueError('Comparison differs from independently rechecked traces')
        if metrics!=json.loads((run/name/'stage2_metrics.json').read_text()):
            raise ValueError('Stored metrics differ')
        if saved['firmware_sha256']!=sha(frozen/hex_path) or saved.get('hardware_enable_sobel')!=1:
            raise ValueError('Wrong firmware/hardware binding')
    cycles={k:result['modes'][k]['execution']['cycles'] for k,_,_ in MODES}
    ratios={'S0_div_S1':cycles['s0']/cycles['s1'],'S0_div_H1':cycles['s0']/cycles['h1'],
            'S1_div_H1':cycles['s1']/cycles['h1']}
    if ratios!=result['ratios']: raise ValueError('Incorrect cycle ratios')
    return {'status':'M2_SINGLE_RUN_AUDIT_PASS','run':run.name,'cycles':cycles,'ratios':ratios,
            'snapshot_sha256':sha(run/'inputs.sha256.json'),'comparison_sha256':sha(run/'comparison.json'),
            'limits':'One workload only; DMA v2/RGB480 not implemented; ASIC NOT_RUN.'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('run',type=Path)
    a=p.parse_args();print(json.dumps(audit(a.run),indent=2))
