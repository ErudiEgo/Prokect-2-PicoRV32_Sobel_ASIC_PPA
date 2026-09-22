"""Prepare a controlled physical-margin experiment from an immutable pair.

No RTL simulation, synthesis, repair, placement or routing is executed here.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import ppa

PARENT_READY = '259c3508f0728480157f95cc0bc82d8e94626923f7bbcd3ff29dbae7718f50de'
H2_ARCHIVE = 's2_ppa_h2_clk50_01_collect_20260922T054005584302Z.tar.gz'
H2_SHA = '5564b206ce732d49dfe49fce6534b1f260f368f3e41bf9e4219f3ba3acc8282a'
CHANGES = {'GRT_ANTENNA_MARGIN': (30, 10), 'SOBEL_POST_FANOUT_MARGIN_PCT': (70, 80)}


def derive_sources(source, dest):
    """Copy validated sources and change only two optimization margins in both configs."""
    manifest = json.loads((source/'snapshot_sha256.json').read_text())
    for name, digest in manifest.items():
        if ppa.sha(source/name) != digest:
            raise ValueError('Parent source changed: '+name)
    shutil.copytree(source, dest)
    for variant in ('h1','h2'):
        path=dest/f'config_{variant}.json'
        cfg=json.loads(path.read_text())
        for key,(old,new) in CHANGES.items():
            if cfg[key] != old: raise ValueError('Unexpected parent setting: '+key)
            cfg[key]=new
        ppa.save(path,cfg)
    # Prove all original files other than the two config files stayed identical.
    for name,digest in manifest.items():
        if name not in ('config_h1.json','config_h2.json') and ppa.sha(dest/name)!=digest:
            raise ValueError('Unintended source change: '+name)
    ppa.save(dest/'repair_experiment.json',{
        'status':'HYPOTHESIS_UNMEASURED', 'parent_ready_sha256':PARENT_READY,
        'failed_h2_archive':H2_ARCHIVE, 'failed_h2_archive_sha256':H2_SHA,
        'changes':CHANGES,
        'hypothesis':'Lower antenna optimization over-margin may reduce diode loading; higher resizer electrical headroom may absorb post-route capacitance growth.',
        'observed':'Six fanout violations have 8-11 diode loads each; one non-diode NOR4B output exceeds its SS cell-specific capacitance limit by 0.000297 pF.',
        'unchanged':'RTL, firmware, SDC, max fanout 10, max cap 0.2 pF, library pin limits, 50 ns clock, all physical checkers, tool/PDK, 81 configured steps.',
        'risks':'Fewer diode reserves may leave antenna violations; more buffering may cost area/power. No closure prediction or PASS claim.',
        'comparison':'Old H1/H2 pair remains baseline. New H2 is a repair experiment; same-profile H1 is required before a new controlled PPA comparison.'})
    shutil.copy2(Path(__file__),dest/'prepare_repair_pair.py')
    files=ppa.inventory(dest);files.pop('snapshot_sha256.json')
    ppa.save(dest/'snapshot_sha256.json',files)


def main(parent_tag,new_tag):
    ppa.tag_check(parent_tag);ppa.tag_check(new_tag)
    parent=ppa.ROOT/'run_inputs'/parent_tag;dest=ppa.ROOT/'run_inputs'/new_tag
    ppa.verify_packet(parent)
    if ppa.sha(parent/'READY.json') != PARENT_READY:raise ValueError('Wrong baseline pair')
    if dest.exists() or (ppa.ROOT/'runs'/new_tag).exists():raise ValueError('New pair tag already exists')
    if ppa.sha(ppa.ROOT/'reports'/H2_ARCHIVE)!=H2_SHA:raise ValueError('H2 evidence archive mismatch')
    env=ppa.environment()
    if env!=json.loads((parent/'environment.json').read_text()):raise ValueError('Environment changed')
    ppa.verify_pdk(parent,env)
    if ppa.sha(Path(ppa.__file__))!=ppa.sha(parent/'sources/ppa.py'):raise ValueError('Launcher changed')
    dest.mkdir()
    shutil.copy2(parent/'environment.json',dest/'environment.json')
    derive_sources(parent/'sources',dest/'sources')
    audit=dest/'preflight';audit.mkdir()
    args=ppa.docker_args(env,dest/'sources',audit)+[ppa.IMAGE,'python3','/design/check_ppa.py','/audit']
    with (audit/'console.log').open('x') as log:
        process=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        for line in process.stdout:
            print(line,end='',flush=True);log.write(line)
        if process.wait()!=0:raise ValueError('Repair preflight failed; retain '+str(dest))
    result=json.loads((audit/'PASS.json').read_text())
    ppa.verify_pdk(dest,env)
    ppa.save(dest/'READY.json',{'status':result['status'],'pair':new_tag,'files_sha256':ppa.inventory(dest)})
    print('PPA REPAIR PAIR READY:',new_tag,'; physical repair NOT_RUN')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('parent_pair');p.add_argument('new_pair');a=p.parse_args()
    try:main(a.parent_pair,a.new_pair)
    except (OSError,ValueError,KeyError,subprocess.CalledProcessError) as e:sys.exit('ERROR: '+str(e))
