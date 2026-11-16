#!/usr/bin/env python3
"""Fresh-process S3 construction panel; raw host timing only."""
import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import shutil
import signal
import statistics
import subprocess
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / 'run-001'
OUT.mkdir(exist_ok=False)
START = time.monotonic()


def read(p):
    try:
        return Path(p).read_text()
    except OSError:
        return None


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def snap():
    return {p: read(p) for p in ['/proc/self/status', '/proc/self/cgroup',
            '/proc/self/mountinfo', '/proc/stat', '/proc/self/numa_maps',
            '/sys/fs/cgroup/cpu.stat', '/sys/fs/cgroup/memory.events',
            '/sys/fs/cgroup/cpu/cpu.stat', '/sys/fs/cgroup/memory/memory.failcnt']}


def command(args, timeout, env=None):
    remaining = 780 - (time.monotonic() - START)
    if remaining <= 0:
        raise TimeoutError('controller budget exhausted')
    p = subprocess.Popen(args, cwd=ROOT, env=env, text=True,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         start_new_session=True)
    try:
        out, err = p.communicate(timeout=min(timeout, remaining))
        return p.returncode, out, err
    except subprocess.TimeoutExpired:
        os.killpg(p.pid, signal.SIGKILL)
        out, err = p.communicate()
        return 124, out, err + '\nprocess group killed at budget\n'


host = {'platform': platform.platform(), 'cpuinfo': read('/proc/cpuinfo'),
        'initial': snap(), 'allowed_cpus': sorted(os.sched_getaffinity(0)),
        'source_sha256': {p: sha(ROOT / p) for p in [
            'suite/src/cryptanalysis/pq_descent_symbolic.rs',
            'suite/src/cryptanalysis/semaev_decomp.rs', 'suite/Cargo.toml',
            'suite/Cargo.lock', 'suite/examples/ic_s3_direct_probe.rs',
            str(HERE.relative_to(ROOT) / 'PROTOCOL.md'),
            str(HERE.relative_to(ROOT) / 'run_panel.py')]},
        'rustc': subprocess.check_output(['rustc', '-Vv'], text=True),
        'kernel': 'host CPU on L4 allocation; placement unqualified'}
pairs = []
binaries = {}
try:
    for variant in ['reference', 'direct']:
        env = dict(os.environ, CARGO_TARGET_DIR='/tmp/ic-s3-target')
        args = ['cargo', 'build', '--release', '--locked', '-j2',
                '--manifest-path', str(ROOT / 'suite/Cargo.toml'),
                '--example', 'ic_s3_direct_probe']
        if variant == 'direct':
            args += ['--features', 's3-direct-coefficients']
        code, out, err = command(args, 330, env)
        (OUT / f'{variant}-build.log').write_text(out + err)
        if code:
            raise RuntimeError(f'{variant} build exit {code}')
        binary = OUT / ('probe-' + variant)
        shutil.copy2('/tmp/ic-s3-target/release/examples/ic_s3_direct_probe', binary)
        binaries[variant] = str(binary)
    host['binary_sha256'] = {k: sha(v) for k, v in binaries.items()}
    os.sched_setaffinity(0, {host['allowed_cpus'][0]})
    host['selected_cpu'] = host['allowed_cpus'][0]

    def arm(variant, n, np, m, fixture, role):
        args = [binaries[variant], str(n), str(np), str(fixture), str(m)]
        before = snap()
        usage0 = resource.getrusage(resource.RUSAGE_CHILDREN)
        code, out, err = command(args, 20)
        usage1 = resource.getrusage(resource.RUSAGE_CHILDREN)
        row = {'variant': variant, 'role': role, 'argv': args,
               'before': before, 'after': snap(), 'exit_code': code,
               'stdout': out, 'stderr': err,
               'cpu_s': usage1.ru_utime + usage1.ru_stime - usage0.ru_utime - usage0.ru_stime,
               'involuntary': usage1.ru_nivcsw - usage0.ru_nivcsw}
        if not code:
            row['result'] = json.loads(out)
        with (OUT / 'arms.jsonl').open('a') as f:
            f.write(json.dumps(row) + '\n')
        if code:
            raise RuntimeError(f'arm exit {code}')
        return row

    for n, np, m in [(31,8,2), (31,20,2), (53,24,2), (63,32,2), (23,6,3)]:
        for fixture in range(60,66):
            pre = arm('reference',53,24,2,0,'calibration')
            order = ['reference','direct'] if fixture % 2 == 0 else ['direct','reference']
            runs = {v: arm(v,n,np,m,fixture,'construction') for v in order}
            post = arm('reference',53,24,2,0,'calibration')
            ref, direct = (runs[v]['result'] for v in ['reference','direct'])
            aa = pre['result']['cold_stage_s'] / post['result']['cold_stage_s']
            pair = {'n':n,'np':np,'summands':m,'fixture':fixture,'order':order,
                    'runs':runs,'pre':pre,'post':post,
                    'checksum_equal':ref['checksum']==direct['checksum'],
                    'calibration_ratio':aa,'calibration_within_bound':.85<=aa<=1.15,
                    'raw_cold_ratio':ref['cold_stage_s']/direct['cold_stage_s'],
                    'raw_build_ratio':ref['first_build_s']/direct['first_build_s'],
                    'qualified_ratio':None}
            pairs.append(pair)
            (OUT / 'pairs.json').write_text(json.dumps(pairs,indent=2)+'\n')
            if not pair['checksum_equal']:
                raise RuntimeError('canonical coefficient checksum mismatch')
    summary = {'status':'exploratory_unqualified','qualified':None,'pairs':len(pairs),
               'all_checksums_equal':all(p['checksum_equal'] for p in pairs),
               'calibration_failures':sum(not p['calibration_within_bound'] for p in pairs),
               'cases':[]}
    for n,np,m in [(31,8,2),(31,20,2),(53,24,2),(63,32,2),(23,6,3)]:
        selected = [p for p in pairs if (p['n'],p['np'],p['summands'])==(n,np,m)]
        summary['cases'].append({'n':n,'np':np,'summands':m,'pairs':len(selected),
            'raw_cold_median':statistics.median(p['raw_cold_ratio'] for p in selected),
            'raw_build_median':statistics.median(p['raw_build_ratio'] for p in selected),
            'raw_cold_min':min(p['raw_cold_ratio'] for p in selected),
            'raw_cold_max':max(p['raw_cold_ratio'] for p in selected)})
except Exception as e:
    summary = {'status':'failed_or_capped','error':repr(e),'pairs':len(pairs),'qualified':None}
finally:
    host['final'] = snap()
    (OUT / 'host.json').write_text(json.dumps(host,indent=2)+'\n')
    (OUT / 'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary),flush=True)
if summary['status'] != 'exploratory_unqualified':
    raise SystemExit(1)
