#!/usr/bin/env python3
"""Exploratory CPU field component panel. Never qualifies full IC timing."""
import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import statistics
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RUN_ID = os.environ.get('IC_FIELD_RUN_ID', 'run-001')
if not RUN_ID.replace('-', '').isalnum():
    raise ValueError('invalid run directory')
FIXTURE_START = int(os.environ.get('IC_FIELD_FIXTURE_START', '20'))
if FIXTURE_START < 0 or FIXTURE_START > 1000000:
    raise ValueError('invalid fixture range')
OUT = HERE / RUN_ID
OUT.mkdir(exist_ok=False)


def read(path):
    try:
        return Path(path).read_text()
    except OSError:
        return None


def snap():
    return {p: read(p) for p in ['/proc/self/status', '/proc/self/cgroup',
            '/proc/self/mountinfo', '/proc/stat', '/proc/self/numa_maps',
            '/sys/fs/cgroup/cpu.stat', '/sys/fs/cgroup/memory.events',
            '/sys/fs/cgroup/cpu/cpu.stat', '/sys/fs/cgroup/memory/memory.failcnt']}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


host = {'platform': platform.platform(), 'cpuinfo': read('/proc/cpuinfo'),
        'initial': snap(), 'allowed_cpus': sorted(os.sched_getaffinity(0)),
        'source_sha256': {p: sha(ROOT / p) for p in [
            'suite/src/binary_ecc/f2m.rs', str(HERE.relative_to(ROOT) / 'Cargo.lock'),
            str(HERE.relative_to(ROOT) / 'src/main.rs'), str(HERE.relative_to(ROOT) / 'run_panel.py')]},
        'rustc': subprocess.check_output(['rustc', '-Vv'], text=True),
        'kernel': 'host CPU only; CUDA allocation supplies required host envelope'}
os.sched_setaffinity(0, {host['allowed_cpus'][0]})
host['selected_cpu'] = host['allowed_cpus'][0]
binaries = {}
for variant in ['default', 'specialized']:
    target = '/tmp/ic-field-' + variant
    env = dict(os.environ, CARGO_TARGET_DIR=target)
    extra = ['--features', 'f2m-karatsuba3'] if variant == 'specialized' else []
    for action in ['test', 'build']:
        args = ['cargo', action, '--release', '--locked', '--manifest-path', str(HERE / 'Cargo.toml')] + extra
        result = subprocess.run(args, env=env, cwd=ROOT, text=True, capture_output=True, timeout=240)
        (OUT / f'{variant}-{action}.log').write_text(result.stdout + result.stderr)
        if result.returncode:
            raise RuntimeError(f'{variant} {action} failed')
    binaries[variant] = target + '/release/ic-f2m-three-limb-validation'
host['binary_sha256'] = {k: sha(v) for k, v in binaries.items()}
(OUT / 'host.json').write_text(json.dumps(host, indent=2) + '\n')


def arm(variant, degree, fixture, role):
    before = snap()
    usage0 = resource.getrusage(resource.RUSAGE_CHILDREN)
    args = [binaries[variant], str(degree), str(fixture), '1000000']
    result = subprocess.run(args, text=True, capture_output=True, timeout=60)
    usage1 = resource.getrusage(resource.RUSAGE_CHILDREN)
    row = {'variant': variant, 'role': role, 'argv': args, 'before': before,
           'after': snap(), 'exit_code': result.returncode, 'stderr': result.stderr,
           'stdout': result.stdout, 'cpu_s': usage1.ru_utime + usage1.ru_stime - usage0.ru_utime - usage0.ru_stime,
           'involuntary': usage1.ru_nivcsw - usage0.ru_nivcsw,
           'voluntary': usage1.ru_nvcsw - usage0.ru_nvcsw}
    if result.returncode == 0:
        row['result'] = json.loads(result.stdout)
    with (OUT / 'arms.jsonl').open('a') as out:
        out.write(json.dumps(row) + '\n')
    if result.returncode:
        raise RuntimeError('arm failed; retained raw row')
    return row


pairs = []
for degree in [113, 131, 155, 163, 233]:
    for fixture in range(FIXTURE_START, FIXTURE_START + 5):
        pre = arm('default', 131, 0, 'calibration')
        order = ['default', 'specialized'] if fixture % 2 == 0 else ['specialized', 'default']
        runs = {v: arm(v, degree, fixture, 'component') for v in order}
        post = arm('default', 131, 0, 'calibration')
        baseline, candidate = runs['default']['result'], runs['specialized']['result']
        aa = pre['result']['wall_s'] / post['result']['wall_s']
        pair = {'degree': degree, 'fixture': fixture, 'runs': runs,
                'calibration_pre': pre, 'calibration_post': post,
                'checksum_equal': baseline['checksum'] == candidate['checksum'],
                'calibration_ratio': aa, 'calibration_within_bound': .85 <= aa <= 1.15,
                'raw_wall_ratio': baseline['wall_s'] / candidate['wall_s'],
                'qualified_wall_ratio': None,
                'qualification': 'exploratory component only; required host controls incomplete'}
        pairs.append(pair)
        (OUT / 'pairs.json').write_text(json.dumps(pairs, indent=2) + '\n')
summary = {'status': 'exploratory_unqualified', 'pairs': len(pairs),
           'all_checksums_equal': all(p['checksum_equal'] for p in pairs),
           'calibration_failures': sum(not p['calibration_within_bound'] for p in pairs),
           'qualified': None, 'cases': []}
for degree in [113, 131, 155, 163, 233]:
    values = [p['raw_wall_ratio'] for p in pairs if p['degree'] == degree]
    summary['cases'].append({'degree': degree, 'n': len(values),
                             'raw_median_ratio': statistics.median(values),
                             'raw_min_ratio': min(values), 'raw_max_ratio': max(values)})
(OUT / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary))
