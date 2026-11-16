#!/usr/bin/env python3
"""Frozen current-upstream panel; execute on one CUDA-capable allocation."""
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import platform
import shlex
import statistics
import subprocess
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
OUT = HERE / 'run-001'
BUILD = Path('/tmp/ic-current-cloud-build')
BASE = '2b97ddf662b53d330581ae51a7818a82e94585ac'
CASES = [(2000000579, 0), (1099511627791, 0), (281474976710597, 0),
         (14636773816760213, 0), (2000000579, 1)]
FIXTURES = list(range(10, 15))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    try:
        return Path(path).read_text()
    except OSError:
        return None


def command(args, timeout=120):
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=timeout)


def snapshot():
    paths = ['/proc/self/status', '/proc/self/cgroup', '/proc/stat',
             '/sys/fs/cgroup/cpu.max', '/sys/fs/cgroup/cpu.stat',
             '/sys/fs/cgroup/memory.max', '/sys/fs/cgroup/memory.events']
    return {p: read(p) for p in paths}


def build():
    cmds = [['cmake', '-S', str(ROOT), '-B', str(BUILD), '-DCA_CUPQC=OFF',
             '-DCA_WERROR=ON', '-DCA_BUILD_SHARED=OFF', '-DCA_BUILD_TOOLS=OFF',
             '-DCMAKE_EXPORT_COMPILE_COMMANDS=ON'],
            ['cmake', '--build', str(BUILD), '-j', '3'],
            ['ctest', '--test-dir', str(BUILD), '--output-on-failure']]
    for index, args in enumerate(cmds):
        proc = command(args, timeout=240)
        (OUT / f'build-{index}.log').write_text(proc.stdout + proc.stderr)
        if proc.returncode:
            raise RuntimeError(f'build/check failed: {args}; see build-{index}.log')
    entries = json.loads((BUILD / 'compile_commands.json').read_text())
    entry = next(e for e in entries if e['file'].endswith('/src/indexcalc.c'))
    args = shlex.split(entry['command'])
    args[args.index('-o') + 1] = str(BUILD / 'reference.o')
    args[args.index('-c') + 1] = str(HERE / 'baseline_indexcalc.c')
    proc = command(args)
    if proc.returncode:
        raise RuntimeError(proc.stderr)
    cc = os.environ.get('CC', 'cc')
    for variant in ('reference', 'optimized', 'references'):
        source = HERE / ('references.c' if variant == 'references' else 'pipeline.c')
        args = [cc, '-O3', '-std=c11', '-ffp-contract=off', '-I' + str(ROOT / 'include'),
                '-I' + str(ROOT / 'src'), str(source)]
        if variant == 'reference':
            args += [str(BUILD / 'reference.o')]
        args += [str(BUILD / 'libcryptanalysis.a'), '-lm', '-lpthread', '-o', str(BUILD / variant)]
        proc = command(args)
        if proc.returncode:
            raise RuntimeError(proc.stderr)
    return cmds


def run_arm(args, prefix):
    start = time.time()
    before = snapshot()
    try:
        proc = command(prefix + args)
        row = {'exit_code': proc.returncode, 'stdout': proc.stdout, 'stderr': proc.stderr}
        if proc.returncode == 0:
            row['result'] = json.loads(proc.stdout)
    except subprocess.TimeoutExpired:
        row = {'status': 'timeout'}
    except Exception as error:
        row = {'status': 'invalid_output', 'error': repr(error)}
    row.update(started_unix=start, finished_unix=time.time(), before=before, after=snapshot())
    return row


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    gpu = command(['nvidia-smi', '--query-gpu=name,uuid,driver_version', '--format=csv,noheader'])
    host = {'platform': platform.platform(), 'machine': platform.machine(),
            'provider': 'Modal', 'job_id': os.environ.get('JOB_ID'),
            'requested_cpu': 4, 'requested_memory_gib': 8, 'requested_gpu': 'L4',
            'gpu_exit_code': gpu.returncode, 'gpu_devices': gpu.stdout.strip().splitlines(),
            'kernel_backend': 'host-only CPU control; CUDA hardware exposed',
            'cpuinfo': read('/proc/cpuinfo'), 'initial': snapshot(),
            'memory_technology': 'unknown', 'base_commit': BASE,
            'source_sha256': {str(p.relative_to(ROOT)): digest(p) for p in
                              [ROOT/'src/indexcalc.c', ROOT/'src/linalg.c',
                               ROOT/'src/ic_rational.h', HERE/'pipeline.c',
                               HERE/'references.c', HERE/'baseline_indexcalc.c', HERE/'run.py']}}
    (OUT/'host.json').write_text(json.dumps(host, indent=2)+'\n')
    if gpu.returncode or not gpu.stdout.strip():
        raise RuntimeError('CUDA-host requirement failed; no performance arms launched')
    host['build_commands'] = build()
    allowed = sorted(os.sched_getaffinity(0))
    cpu = allowed[0]
    os.sched_setaffinity(0, {cpu})
    nodes = sorted(Path(f'/sys/devices/system/cpu/cpu{cpu}').glob('node*'))
    node = int(nodes[0].name[4:]) if nodes else None
    prefix = []
    policy = {'selected_cpu': cpu, 'initial_allowed_cpus': allowed, 'local_node': node,
              'memory_policy': 'default first-touch; placement unverified'}
    if node is not None:
        try:
            trial = command(['numactl', f'--physcpubind={cpu}', f'--membind={node}', 'true'])
            policy['numactl_exit_code'] = trial.returncode
            policy['numactl_stderr'] = trial.stderr
            if trial.returncode == 0:
                prefix = ['numactl', f'--physcpubind={cpu}', f'--membind={node}']
                policy['memory_policy'] = 'explicit local-node bind'
        except FileNotFoundError:
            policy['numactl_exit_code'] = None
    host.update(placement=policy, binary_sha256={v:digest(BUILD/v) for v in ('reference','optimized','references')})
    (OUT/'host.json').write_text(json.dumps(host, indent=2)+'\n')
    pairs = []
    with (OUT/'arms.jsonl').open('w') as raw:
        for p, method in CASES:
            for fixture in FIXTURES:
                pair = {'p':p, 'method':method, 'fixture':fixture}
                pre = run_arm([str(BUILD/'optimized'), '--calibration'], prefix)
                variants = ['reference','optimized'] if fixture % 2 == 0 else ['optimized','reference']
                for order, variant in enumerate(variants):
                    arm = run_arm([str(BUILD/variant), str(p), str(method), str(fixture), '100'], prefix)
                    arm.update(p=p, method=method, fixture=fixture, variant=variant, order=order)
                    raw.write(json.dumps(arm, sort_keys=True)+'\n'); raw.flush()
                    pair[variant] = arm
                # Both references solve precisely this public point. Their
                # target-independent factor/group/table setup is separate.
                pair['references'] = run_arm([str(BUILD/'references'), str(p), str(fixture)], prefix)
                post = run_arm([str(BUILD/'optimized'), '--calibration'], prefix)
                pair.update(calibration_pre=pre, calibration_post=post)
                reasons = []
                if not all(x.get('exit_code') == 0 for x in (pre, post, pair['reference'], pair['optimized'])):
                    reasons.append('failed/capped arm or calibration')
                else:
                    a, b = pair['reference']['result'], pair['optimized']['result']
                    expected = ((0x23456789abcd + fixture * 0x9e3779b97f4a7c15) & ((1 << 64) - 1)) % (p - 1)
                    if not all(a[k] == b[k] for k in ('p','g','h','x','relations','base_primes','verified_logs')):
                        reasons.append('input/collection mismatch')
                    for result in (a,b):
                        if result['x'] != expected or any(x['x'] != expected or pow(result['g'], x['x'], p) != result['h'] for x in result['online_runs']):
                            reasons.append('answer replay failed')
                        pages = result.get('numa_pages', {})
                        if not pages or any(int(k) != node and v > 0 for k,v in pages.items()):
                            reasons.append('anonymous page placement gate')
                    before, after = pre['result'], post['result']
                    if before['checksum'] != after['checksum'] or not 0.85 <= before['cpu']/after['cpu'] <= 1.15:
                        reasons.append('A/A calibration gate')
                    ar, br = a['online_runs'][0], b['online_runs'][0]
                    if ar['wall'] <= 0 or br['wall'] <= 0:
                        reasons.append('nonpositive primary interval')
                    else:
                        pair['primary_wall_ratio'] = ar['wall']/br['wall']
                        pair['primary_cpu_ratio'] = ar['cpu']/br['cpu'] if br['cpu'] > 0 else None
                        pair['secondary_mean_wall_ratio'] = a['online_wall']/b['online_wall']
                    if ar['involuntary'] or br['involuntary']:
                        reasons.append('primary involuntary context switch')
                    pair['setup_wall_ratio'] = a['setup_wall']/b['setup_wall']
                    rr = pair['references'].get('result')
                    if rr and rr['rho_status'] == 0 and pow(a['g'],rr['rho_x'],p) == a['h']:
                        pair['rho_over_candidate_wall'] = rr['rho_wall']/br['wall']
                    if rr and rr['precomp_status'] == 0 and pow(a['g'],rr['precomp_x'],p) == a['h']:
                        pair['precomp_rho_over_candidate_wall'] = rr['precomp_online_wall']/br['wall']
                # These gates are deliberately fail-closed. Unavailable
                # cgroup/placement fields leave the qualified tier unknown.
                if policy['memory_policy'] != 'explicit local-node bind':
                    reasons.append('NUMA placement gate unavailable')
                for variant in variants:
                    arm = pair[variant]
                    def steal(text):
                        for line in (text or '').splitlines():
                            parts = line.split()
                            if parts and parts[0] == f'cpu{cpu}' and len(parts) > 8:
                                return int(parts[8])
                        return None
                    s0 = steal(arm['before'].get('/proc/stat'))
                    s1 = steal(arm['after'].get('/proc/stat'))
                    if s0 is None or s1 is None:
                        reasons.append('missing selected-CPU steal counters')
                    elif s1 != s0:
                        reasons.append('selected-CPU steal changed')
                    for path in ('/sys/fs/cgroup/cpu.stat','/sys/fs/cgroup/memory.events'):
                        def counters(text):
                            return dict(line.split() for line in (text or '').splitlines() if len(line.split()) == 2)
                        before, after = counters(arm['before'].get(path)), counters(arm['after'].get(path))
                        if not before or not after:
                            reasons.append('missing cgroup counters')
                        for key in ('nr_throttled','oom','oom_kill'):
                            if key in before and int(after[key]) != int(before[key]):
                                reasons.append(f'{variant} {key} changed')
                pair['tier_rejection_reasons'] = sorted(set(reasons))
                pair['accepted_for_tier'] = not reasons
                pairs.append(pair)
                (OUT/'pairs.json').write_text(json.dumps(pairs, indent=2)+'\n')
    summaries = []
    for p, method in CASES:
        selected = [x for x in pairs if x['p'] == p and x['method'] == method]
        vals = [x['primary_wall_ratio'] for x in selected if 'primary_wall_ratio' in x]
        summary = {'p':p,'method':method,'all_five_tier_gates':all(x['accepted_for_tier'] for x in selected),
                   'qualified_wall_speedup':None, 'raw_primary_wall_ratios':vals}
        if len(vals) == 5:
            logs = [math.log(v) for v in vals]
            bootstrap = sorted(math.exp(sum(logs[i] for i in indices)/5)
                               for indices in itertools.product(range(5), repeat=5))
            interval = [bootstrap[int(0.025*len(bootstrap))], bootstrap[int(0.975*len(bootstrap))]]
            summary.update(exploratory_median_ratio=statistics.median(vals), paired_geomean_95_interval=interval)
            if summary['all_five_tier_gates'] and interval[0] > 1 and all(v > 1 for v in vals):
                summary['qualified_wall_speedup'] = statistics.median(vals)
        summaries.append(summary)
    (OUT/'summary.json').write_text(json.dumps(summaries, indent=2)+'\n')
    print(json.dumps(summaries, indent=2))


if __name__ == '__main__':
    main()
