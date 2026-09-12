"""Copy and validate an existing DRT checkpoint into a NEW frozen snapshot.

File preparation only; no OpenLane flow/step is started. Original RUN untouched.
"""
import json
import re
import shutil
import sys
from pathlib import Path
from collect_asic import integrity, load, sha, stage_number
from antenna_targets import checked_targets


def prepare(root, parent, tag):
    for name in (parent, tag):
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', name):
            raise ValueError('Unsafe RUN name')
    if parent == tag or (root/'runs'/tag).exists():
        raise ValueError('Resume requires a new, unused RUN tag')
    old, new = root/'run_inputs'/parent, root/'run_inputs'/tag
    if not integrity(old) or not integrity(new):
        raise ValueError('Snapshot/functional hash verification failed')
    if load(old/'config.json') != load(new/'config.json'):
        raise ValueError('Physical configuration changed; use a full new RUN')
    original = load(old/'source_sha256.json')
    for name, digest in original.items():
        if name.startswith(('rtl/', 'third_party/', 'build/asic_sources/')) or name in (
                'constraints.sdc', 'pin_order.cfg', 'scripts/upstream_lint_review.json'):
            if sha(new/name) != digest:
                raise ValueError('Checkpoint input differs: '+name)
    def environment(snapshot):
        return dict(line.split('=',1) for line in (snapshot/'environment.txt').read_text().splitlines() if '=' in line)
    a, b = environment(old), environment(new)
    for key in ('image_id','pdk_resolved'):
        if not a.get(key) or a[key] != b.get(key):
            raise ValueError('Checkpoint tool/PDK mismatch: '+key)
    run = root/'runs'/parent
    stages = sorted([p for p in run.iterdir() if p.is_dir() and re.match(r'^\d+-',p.name)],key=stage_number)
    drt = [p for p in stages if p.name.endswith('-openroad-detailedrouting') and (p/'state_out.json').is_file()]
    cts = [p for p in stages if p.name.endswith('-openroad-cts') and (p/'state_out.json').is_file()]
    closures = [p for p in stages if p.name.endswith('-sobel-antennaclosure')
                and (p/'state_out.json').is_file() and (p/'closure_history.json').is_file()]
    antenna_only = bool(closures)
    routed = closures[-1] if antenna_only else (drt[-1] if drt else None)
    cts_state = cts[-1]/'state_out.json' if cts else old/'resume_checkpoint/parent_cts_state.json'
    if routed is None or not cts_state.is_file():
        raise ValueError('No completed routed/CTS checkpoint')
    if antenna_only:
        history = load(routed/'closure_history.json')
        if not history: raise ValueError('Completed closure has no audit history')
        # Select the pre-filler composite output, never final sign-off/filler ODB.
        # All earlier repairs are retained; no resizer may run in this continuation.
    state_path = routed/'state_out.json' 
    state = load(state_path)
    if not state.get('odb'): raise ValueError('Checkpoint has no ODB')
    dest = new/'resume_checkpoint'
    dest.mkdir(exist_ok=False)
    copies = {}
    def copy_view(value):
        if isinstance(value, dict): return {k:copy_view(v) for k,v in value.items()}
        if isinstance(value, list): return [copy_view(v) for v in value]
        if value is None: return None
        if not isinstance(value,str) or not value.startswith('/work/'):
            raise ValueError('Unrecognized checkpoint view: '+str(value))
        source = (root/value.removeprefix('/work/')).resolve()
        if not source.is_file(): raise ValueError('Missing checkpoint view: '+value)
        if source.is_relative_to(run.resolve()):
            relative = source.relative_to(run.resolve())
        elif source.is_relative_to((old/'resume_checkpoint/views').resolve()):
            # Parent is itself a continuation. integrity(old) above verifies
            # these frozen inherited files; copy them into the new snapshot.
            relative = Path('inherited')/source.relative_to((old/'resume_checkpoint/views').resolve())
        else:
            raise ValueError('View outside verified parent RUN/snapshot: '+value)
        target = dest/'views'/relative
        target.parent.mkdir(parents=True,exist_ok=True)
        if value not in copies:
            with source.open('rb') as src, target.open('xb') as out: shutil.copyfileobj(src,out)
            copies[value] = {'path':target.relative_to(new).as_posix(),'sha256':sha(target)}
        return '/work/run_inputs/'+tag+'/'+target.relative_to(new).as_posix()
    resumed = {k:(v if k=='metrics' else copy_view(v)) for k,v in state.items()}
    (dest/'state.json').write_text(json.dumps(resumed,indent=2)+'\n')
    shutil.copy2(state_path,dest/'parent_drt_state.json')
    shutil.copy2(cts_state,dest/'parent_cts_state.json')
    # Congestion evidence for the inherited routed design; later reroute logs
    # in the resumed RUN supersede this table.
    candidates = []
    for stage in stages:
        if stage_number(stage)>stage_number(routed): break
        for log in sorted(stage.rglob('*.log')):
            if 'Final congestion report:' in log.read_text(errors='replace'): candidates.append(log)
    congestion = None
    if candidates:
        shutil.copy2(candidates[-1],dest/'parent_globalrouting.log')
        congestion = str(candidates[-1].relative_to(root))
    # Copy a real independent antenna check for this exact checkpoint ODB.
    # Frozen precheck can then exercise target/connectivity reads before PNR.
    antenna_report = None
    for report in sorted(run.rglob('reports/antenna.rpt')):
        check_state = report.parent.parent/'state_out.json'
        if not check_state.is_file(): continue
        checked = load(check_state)
        if checked.get('odb') != state['odb']: continue
        metrics = checked['metrics']
        targets = checked_targets(report.read_text(encoding='utf-8'),
                                  metrics['antenna__violating__nets'], metrics['antenna__violating__pins'])
        antenna_report = (report, targets)
    if antenna_report is None:
        raise ValueError('No independent antenna report matching the checkpoint ODB')
    shutil.copy2(antenna_report[0], dest/'parent_antenna.rpt')
    (dest/'antenna_targets.json').write_text(json.dumps(antenna_report[1],indent=2)+'\n')
    record = {'parent_run':parent,'from_step':'Sobel.AntennaClosure',
              'parent_state':str(state_path.relative_to(root)),'parent_state_sha256':sha(state_path),
              'parent_cts_state':str(cts_state.relative_to(root)),
              'checkpoint_kind':'completed_antenna_closure' if antenna_only else 'detailed_routing',
              'antenna_only':antenna_only,
              'parent_congestion_log':congestion,'copied_views':copies,
              'parent_antenna_report':str(antenna_report[0].relative_to(root)),
              'runtime_scope':'Continuation only; excludes parent synthesis/placement/routing time'}
    (dest/'provenance.json').write_text(json.dumps(record,indent=2)+'\n')
    frozen_path = new/'config.frozen.json'
    frozen = load(frozen_path)
    frozen['SOBEL_ANTENNA_ONLY'] = antenna_only
    frozen_path.write_text(json.dumps(frozen,indent=2)+'\n')
    manifest = load(new/'source_sha256.json')
    manifest['config.frozen.json'] = sha(frozen_path)
    for p in dest.rglob('*'):
        if p.is_file(): manifest[p.relative_to(new).as_posix()] = sha(p)
    (new/'source_sha256.json').write_text(json.dumps(manifest,indent=2)+'\n')
    if not integrity(new): raise ValueError('Copied checkpoint integrity failed')
    print('CHECKPOINT READY:',parent,'->',tag,'from Sobel.AntennaClosure; views copied and hashed; no flow started')


if __name__ == '__main__':
    # Launcher cd's to the project root before invoking this frozen script.
    prepare(Path.cwd(),*sys.argv[1:])
