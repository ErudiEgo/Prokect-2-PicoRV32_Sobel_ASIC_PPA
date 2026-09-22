"""Prepare/freeze, explicitly run, or collect H2 targeted ECO. No automatic flow."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import ppa

PARENT = 's2_ppa_h2_clk50_repair_01'
PARENT_READY = 'b10245c1bca95585143f187c254e02d0fdf10b4521e4599d04cde7a546cf38f7'
STATUS = 'H2_ECO_STATIC_PREFLIGHT_PASS'
HERE = Path(__file__).resolve().parent


def verify(snap):
    ready = json.loads((snap/'READY.json').read_text())
    if ready['status'] != STATUS: raise ValueError('ECO preflight not accepted')
    for name, digest in ready['files_sha256'].items():
        p = (snap/name).resolve()
        if not p.is_relative_to(snap.resolve()) or ppa.sha(p) != digest:
            raise ValueError('Frozen ECO input changed: '+name)
    return ready


def prepare(root, snap, env):
    parent = root/'run_inputs'/PARENT
    ppa.verify_packet(parent)
    if ppa.sha(parent/'READY.json') != PARENT_READY:
        raise ValueError('Wrong parent repair01 snapshot')
    execution = json.loads((parent/'execution.json').read_text())
    if execution['variant'] != 'h2' or execution['mode'] != 'full_from_start':
        raise ValueError('Wrong parent execution')
    run = root/'runs'/PARENT
    stages = sorted((p for p in run.iterdir() if p.is_dir() and p.name.split('-')[0].isdigit()),
                    key=lambda p:int(p.name.split('-')[0]))
    closure = next(p for p in stages if p.name.endswith('-sobel-antennaclosure'))
    parent_state = closure/'state_out.json'
    if ppa.sha(parent_state) != '5da1851ab04f21d33a7e28b95aeec3aad96193929dbb4ff93e66ff21ad40b87a':
        raise ValueError('Parent checkpoint differs from reviewed archive')
    state = json.loads(parent_state.read_text())
    if any(state['metrics'].get(k) != 0 for k in ('antenna__violating__nets', 'antenna__violating__pins')):
        raise ValueError('Parent checkpoint antenna is not zero')
    cts = next(p/'state_out.json' for p in stages if p.name.endswith('-sobel-ctswithfanoutmargin'))
    snap.mkdir(parents=True, exist_ok=False)
    source = snap/'sources'; shutil.copytree(parent/'sources', source)
    for name in ('h2_eco.py', 'check_h2_eco.py', 'test_h2_eco.py'):
        shutil.copy2(HERE/name, source/name)
    shutil.copy2(HERE/'h2_targeted_eco.py', source/'flow/output_buffer_eco.py')
    # Preserve parent manifest, then create the ECO manifest after all edits.
    shutil.copy2(source/'snapshot_sha256.json', source/'parent_snapshot_sha256.json')
    for variant in ('h1','h2'):
        path=source/f'config_{variant}.json'; config=json.loads(path.read_text())
        config['SOBEL_ANTENNA_ONLY']=True
        config['SOBEL_OUTPUT_BUFFER_REPAIR']=True
        ppa.save(path, config)
    # Dedicated frozen collector accepts only this new continuation mode.
    collector=(source/'collect_ppa.py').read_text()
    old="execution['mode']!='full_from_start'"
    if collector.count(old)!=1: raise ValueError('Parent collector contract changed')
    collector=collector.replace("ready['status']!='PPA_PAIR_STATIC_PREFLIGHT_PASS'", "ready['status']!='H2_ECO_STATIC_PREFLIGHT_PASS'")
    collector=collector.replace(old, "execution['mode']!='h2_targeted_eco_continuation'")
    anchor='    status = "PASS_FOR_REPORTED_FLOW_CHECKS"'
    if collector.count(anchor)!=1: raise ValueError('Collector status anchor changed')
    extra='''    eco_logs = [p for s in stages for p in s.rglob('*.log')]
    eco_ok = any('H2 ECO ROUTED TOPOLOGY PASS' in p.read_text(errors='replace') for p in eco_logs)
    checks['h2_eco_routed_topology'] = 'PASS' if eco_ok else MISSING
'''
    collector=collector.replace(anchor,extra+anchor)
    collector=collector.replace('".csv",".gds")', '".csv",".gds",".v")')
    (source/'collect_ppa.py').write_text(collector)
    checkpoint=snap/'resume_checkpoint'; checkpoint.mkdir()
    copied={}
    def copy_view(value):
        if isinstance(value, dict): return {k:copy_view(v) for k,v in value.items()}
        if isinstance(value, list): return [copy_view(v) for v in value]
        if value is None: return None
        if not isinstance(value,str) or not value.startswith('/work/runs/'+PARENT+'/'):
            raise ValueError('Unexpected checkpoint view: '+str(value))
        rel=Path(value.removeprefix('/work/'))
        src=(root/rel).resolve()
        if not src.is_relative_to(run.resolve()) or not src.is_file(): raise ValueError('Missing/escaped checkpoint view')
        dest=checkpoint/'views'/src.relative_to(run.resolve())
        dest.parent.mkdir(parents=True,exist_ok=True)
        if not dest.exists(): shutil.copy2(src,dest)
        copied[dest.relative_to(checkpoint).as_posix()]=ppa.sha(dest)
        return '/snapshot/resume_checkpoint/'+dest.relative_to(checkpoint).as_posix()
    updated={k:(v if k=='metrics' else copy_view(v)) for k,v in state.items()}
    odb_path=snap/updated['odb'].removeprefix('/snapshot/')
    if ppa.sha(odb_path)!='3f933ed6e30db0278ebdd74a203794c1f3dd3135a4ee9cd433204e3b03ef8696':
        raise ValueError('Parent ODB differs from read-only reviewed checkpoint')
    ppa.save(checkpoint/'state.json',updated)
    shutil.copy2(parent_state, checkpoint/'parent_drt_state.json')
    shutil.copy2(cts, checkpoint/'parent_cts_state.json')
    grt=[p for s in stages for p in s.rglob('*.log') if 'Final congestion report:' in p.read_text(errors='replace')]
    if grt: shutil.copy2(grt[-1],checkpoint/'parent_globalrouting.log')
    ppa.save(checkpoint/'provenance.json',{'parent_run':PARENT, 'parent_ready_sha256':PARENT_READY,
        'parent_state':str(parent_state.relative_to(root)), 'parent_state_sha256':ppa.sha(parent_state),
        'mode':'completed pre-filler antenna checkpoint; prefix inherited, not rerun', 'views_sha256':copied})
    ppa.save(snap/'environment.json',env)
    ppa.save(source/'eco_plan.json',{'parent':PARENT,'changes':'4 buf_8; two NOR isolation buffers; 13 FF loads split 7/6',
        'clock_ns':50,'limits_changed':False,'rtl_changed':False,'parent_runtime_excluded':True,
        'scope':'H2 continuation, NOT H3; full final checks required; closure not guaranteed'})
    (source/'snapshot_sha256.json').unlink()
    ppa.save(source/'snapshot_sha256.json',ppa.inventory(source))


def precheck(tag):
    env=ppa.environment(); snap=ppa.ROOT/'run_inputs'/tag
    if (ppa.ROOT/'runs'/tag).exists(): raise ValueError('RUN already exists')
    prepare(ppa.ROOT,snap,env)
    audit=snap/'preflight'; audit.mkdir()
    args=ppa.docker_args(env,snap/'sources',audit)+['-v',str(snap)+':/snapshot:ro',
        ppa.IMAGE,'python3','/design/check_h2_eco.py','/audit']
    with (audit/'console.log').open('w') as log:
        proc=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        for line in proc.stdout: print(line,end='',flush=True); log.write(line)
        if proc.wait(): raise ValueError('ECO preflight failed; preserve tag and log')
    ppa.verify_pdk(snap,env)
    if json.loads((audit/'PASS.json').read_text())['status']!=STATUS: raise ValueError('No preflight PASS')
    ppa.save(snap/'READY.json',{'status':STATUS,'files_sha256':ppa.inventory(snap)})
    print('H2 ECO READY:',tag,'; physical ECO NOT_RUN')


def run(tag):
    snap=ppa.ROOT/'run_inputs'/tag; verify(snap); env=ppa.environment()
    if env!=json.loads((snap/'environment.json').read_text()): raise ValueError('Environment changed')
    ppa.verify_pdk(snap,env)
    if ppa.sha(HERE/'h2_eco.py')!=ppa.sha(snap/'sources/h2_eco.py'): raise ValueError('Launcher changed')
    if (ppa.ROOT/'runs'/tag).exists() or (snap/'execution.json').exists(): raise ValueError('No overwrite/rerun')
    jobs=os.environ.get('OPENLANE_JOBS','4')
    if not jobs.isdigit() or int(jobs)<1: raise ValueError('Invalid OPENLANE_JOBS')
    ppa.save(snap/'execution.json',{'variant':'h2','pair_ready_sha256':ppa.sha(snap/'READY.json'),
        'mode':'h2_targeted_eco_continuation','parent_run':PARENT,'from':'Sobel.AntennaClosure',
        'prefix_inherited':True,'runtime_scope':'continuation only; excludes parent'})
    args=ppa.docker_args(env,snap/'sources',work=ppa.ROOT)+['-v',str(snap)+':/snapshot:ro',
        '-v',str(snap)+':/work/run_inputs/'+tag+':ro']
    if sys.stdin.isatty() and sys.stdout.isatty(): args+=['-it','-e','TERM='+os.environ.get('TERM','xterm-256color')]
    args += [ppa.IMAGE,'python3','/design/flow/openlane_with_repairs.py','--manual-pdk','--pdk-root','/pdk',
        '--pdk','sky130A','--design-dir','/work','--run-tag',tag,'-j',jobs,
        '--from','Sobel.AntennaClosure','--with-initial-state','/snapshot/resume_checkpoint/state.json','/design/config_h2.json']
    ppa.save(snap/'command.json',args)
    start=time.time(); code=130
    (snap/'runtime.txt').write_text(f'start_epoch={start}\nstatus=RUNNING\nruntime_scope=continuation_only\n')
    try: code=subprocess.run(args).returncode
    finally:
        end=time.time()
        (snap/'runtime.txt').write_text(f'start_epoch={start}\nend_epoch={end}\nelapsed_seconds={end-start}\nopenlane_exit_status={code}\nruntime_scope=continuation_only\n')
        print('Collect even after failure: bash scripts/36_collect_h2_eco.sh '+tag)
    return code


def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument('command',choices=['precheck','run','collect']); ap.add_argument('tag')
    a=ap.parse_args(); ppa.tag_check(a.tag)
    if not a.tag.startswith('s2_ppa_h2_eco_'): raise ValueError('Use s2_ppa_h2_eco_ tag')
    if a.command=='precheck': precheck(a.tag)
    elif a.command=='run': return run(a.tag)
    else:
        snap=ppa.ROOT/'run_inputs'/a.tag; verify(snap)
        subprocess.run([sys.executable,'-B',str(snap/'sources/collect_ppa.py'),str(ppa.ROOT),a.tag],check=True)
    return 0


if __name__=='__main__':
    try: sys.exit(main())
    except (OSError,ValueError,KeyError,StopIteration,subprocess.CalledProcessError) as e: sys.exit('ERROR: '+str(e))
