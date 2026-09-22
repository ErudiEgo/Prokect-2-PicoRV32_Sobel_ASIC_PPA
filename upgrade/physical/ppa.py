"""Stage2 physical workflow. Only the explicit 'run' command executes OpenLane."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
IMAGE = 'sha256:37c3bd4ea0534a276cb2deb88d601044857bad2807b9bc5b36efe9d02c62624e'
PDK_REV = '0fe599b2afb6708d281543108caf8310912f54af'


def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def save(p, data):
    p.write_text(json.dumps(data, indent=2) + '\n')


def inventory(folder):
    return {p.relative_to(folder).as_posix(): sha(p)
            for p in sorted(folder.rglob('*')) if p.is_file()}


def tag_check(tag):
    if not re.fullmatch(r's2_[A-Za-z0-9_-]{1,70}', tag):
        raise ValueError('Use an explicit s2_ tag, maximum 73 characters')


def environment():
    if sys.platform != 'linux' or str(ROOT).startswith('/mnt/') or ' ' in str(ROOT):
        raise ValueError('Use the copied Ubuntu stage2 project under ~/openlane_projects')
    pdk = Path(os.environ.get('PDK_ROOT', str(Path.home()/'.volare'))).resolve()
    resolved = (pdk/'sky130A').resolve(strict=True)
    if resolved.parts[-2:] != (PDK_REV, 'sky130A'):
        raise ValueError('SKY130 revision differs from reviewed RUN16 environment: '+str(resolved))
    image = subprocess.check_output(['docker', 'image', 'inspect', IMAGE, '--format', '{{.Id}}'], text=True).strip()
    if image != IMAGE:
        raise ValueError('Docker image differs')
    subprocess.run(['docker', 'info', '--format', '{{.ServerVersion}}'], check=True)
    return {'image_id': image, 'pdk_root': str(pdk), 'pdk_resolved': str(resolved), 'pdk_revision': PDK_REV}


def docker_args(env, bundle, audit=None, work=None):
    args = ['docker', 'run', '--rm', '--network', 'none', '--user', f'{os.getuid()}:{os.getgid()}',
            '-e', 'HOME=/tmp', '-e', 'PYTHONDONTWRITEBYTECODE=1',
            '-v', str(bundle)+':/design:ro', '-v', env['pdk_root']+':/pdk:ro']
    if audit:
        args += ['-v', str(audit)+':/audit']
    if work:
        args += ['-v', str(work)+':/work', '-w', '/work']
    else:
        args += ['-w', '/design']
    return args


def verify_packet(packet):
    ready = json.loads((packet/'READY.json').read_text())
    if ready['status'] != 'PPA_PAIR_STATIC_PREFLIGHT_PASS':
        raise ValueError('Packet not accepted by static preflight')
    for name, digest in ready['files_sha256'].items():
        path = (packet/name).resolve()
        if not path.is_relative_to(packet.resolve()) or sha(path) != digest:
            raise ValueError('Prepared packet changed: '+name)
    return ready


def verify_pdk(packet, env):
    # Includes resolved PDK config paths (libraries, LEF/GDS and rule files).
    records = json.loads((packet/'preflight/pdk_files_sha256.json').read_text())
    if not records:
        raise ValueError('Empty PDK hash inventory')
    for name, digest in records.items():
        p = Path(env['pdk_root']) / name.removeprefix('/pdk/')
        if sha(p) != digest:
            raise ValueError('PDK file changed: '+name)


def precheck(tag):
    tag_check(tag)
    env = environment()
    packet = ROOT/'run_inputs'/tag
    if packet.exists() or (ROOT/'runs'/tag).exists():
        raise ValueError('Tag already exists; choose a new pair tag')
    packet.mkdir(parents=True)
    save(packet/'environment.json', env)
    subprocess.run([sys.executable, '-B', str(ROOT/'physical/prepare_ppa.py'), str(packet/'sources')], check=True)
    audit = packet/'preflight'
    audit.mkdir()
    args = docker_args(env, packet/'sources', audit) + [IMAGE, 'python3', '/design/check_ppa.py', '/audit']
    with (audit/'console.log').open('w') as log:
        p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in p.stdout:
            print(line, end='', flush=True)
            log.write(line)
        if p.wait() != 0:
            raise ValueError('Static preflight failed; preserve '+str(packet))
    result = json.loads((audit/'PASS.json').read_text())
    verify_pdk(packet, env)
    save(packet/'READY.json', {'status': result['status'], 'pair': tag, 'files_sha256': inventory(packet)})
    print('PPA PAIR READY:', tag, '; ASIC NOT_RUN', flush=True)


def run(variant, tag, pair):
    tag_check(tag)
    tag_check(pair)
    if not tag.startswith('s2_ppa_'+variant+'_'):
        raise ValueError('RUN name must start s2_ppa_'+variant+'_')
    packet = ROOT/'run_inputs'/pair
    ready = verify_packet(packet)
    if sha(Path(__file__)) != sha(packet/'sources/ppa.py'):
        raise ValueError('Launcher changed since preparation; use a newly prepared pair')
    env = environment()
    if env != json.loads((packet/'environment.json').read_text()):
        raise ValueError('Environment changed since preflight')
    verify_pdk(packet, env)
    snap = ROOT/'run_inputs'/tag
    if snap.exists() or (ROOT/'runs'/tag).exists():
        raise ValueError('RUN/snapshot already exists; no overwrite or automatic resume')
    # Reuse one audited pair; no repeated characterization or RTL simulation.
    shutil.copytree(packet, snap)
    verify_packet(snap)
    save(snap/'execution.json', {'variant': variant, 'pair': pair,
         'pair_ready_sha256': sha(packet/'READY.json'), 'flow': 'Classic with RUN16 substitutions',
         'mode': 'full_from_start', 'base_steps': 78, 'configured_steps': 81,
         'config': 'sources/config_'+variant+'.json'})
    jobs = os.environ.get('OPENLANE_JOBS', '4')
    if not jobs.isdigit() or int(jobs) < 1:
        raise ValueError('OPENLANE_JOBS must be positive')
    args = docker_args(env, snap/'sources', work=ROOT)
    # Read-only overlay also protects the snapshot through its /work alias.
    args += ['-v', str(snap)+':/work/run_inputs/'+tag+':ro']
    if sys.stdin.isatty() and sys.stdout.isatty():
        args += ['-it', '-e', 'TERM='+os.environ.get('TERM', 'xterm-256color')]
    args += [IMAGE, 'python3', '/design/flow/openlane_with_repairs.py', '--manual-pdk',
             '--pdk-root', '/pdk', '--pdk', 'sky130A', '--design-dir', '/work',
             '--run-tag', tag, '-j', jobs, '/design/config_'+variant+'.json']
    # Do not pass --flow: it would discard frozen meta substitutions.
    save(snap/'command.json', args)
    start = time.time()
    (snap/'runtime.txt').write_text(f'start_epoch={start}\nstatus=RUNNING\n')
    code = 130
    print(f'USER PHYSICAL RUN: {tag}; {variant}; 50 ns; Classic 78 + 3 additions', flush=True)
    try:
        code = subprocess.run(args).returncode
    finally:
        end = time.time()
        (snap/'runtime.txt').write_text(f'start_epoch={start}\nend_epoch={end}\nelapsed_seconds={end-start}\nopenlane_exit_status={code}\n')
        print(f'Collect even after failure: bash scripts/32_collect_ppa.sh {tag}', flush=True)
    return code


def collect(tag):
    tag_check(tag)
    snap = ROOT/'run_inputs'/tag
    # Use the collector frozen before this RUN, not a subsequently edited one.
    subprocess.run([sys.executable, '-B', str(snap/'sources/collect_ppa.py'), str(ROOT), tag], check=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    s = sub.add_parser('precheck'); s.add_argument('pair')
    s = sub.add_parser('run'); s.add_argument('variant', choices=['h1','h2']); s.add_argument('tag'); s.add_argument('pair')
    s = sub.add_parser('collect'); s.add_argument('tag')
    a = p.parse_args()
    if a.command == 'precheck': precheck(a.pair)
    elif a.command == 'collect': collect(a.tag)
    else: return run(a.variant, a.tag, a.pair)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as e:
        sys.exit('ERROR: '+str(e))
