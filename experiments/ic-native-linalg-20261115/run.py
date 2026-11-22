#!/usr/bin/env python3
"""Frozen paired full-pipeline diagnostic; preserves failed/capped rows."""
import hashlib
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
BUILD = Path('/tmp/cryptanalysis-ic-native-20261115')
CASES = [(2000000579, 0), (1099511627791, 0), (281474976710597, 0),
         (14636773816760213, 0), (2000000579, 1)]
FIXTURES = list(range(5, 10))
ONLINE_REPEATS = 100


def run(args):
    return subprocess.run(args, cwd=ROOT, check=True, capture_output=True, text=True)


def main():
    commands = []
    args = ['cmake', '--build', str(BUILD), '-j', '3', '--target', 'cryptanalysis_static']
    run(args)
    commands.append(args)
    cc = os.environ.get('CC', 'cc')
    common = [cc, '-O3', '-std=c11', '-I' + str(ROOT/'include'), '-I' + str(ROOT/'src')]
    objects = []
    for name in ('reference_linalg', 'reference_indexcalc'):
        obj = BUILD / (name + '.o')
        args = common + ['-c', str(HERE/(name+'.c')), '-o', str(obj)]
        run(args)
        commands.append(args)
        objects.append(str(obj))
    bins = {}
    for variant in ('reference', 'optimized'):
        binary = BUILD / ('pipeline-' + variant)
        args = common + [str(HERE/'pipeline.c')]
        if variant == 'reference':
            args += objects
        args += [str(BUILD/'libcryptanalysis.a'), '-lm', '-lpthread', '-o', str(binary)]
        run(args)
        commands.append(args)
        bins[variant] = str(binary)
    files = list((ROOT/'src').glob('*.[ch]')) + list((ROOT/'include/cryptanalysis').glob('*.h'))
    files += list(HERE.glob('*.c')) + [HERE/'run.py']
    receipt = {
        'started_unix': time.time(), 'host': platform.platform(), 'machine': platform.machine(),
        'compiler': run([cc, '--version']).stdout, 'commands': commands,
        'base_commit': run(['git', 'rev-parse', 'HEAD']).stdout.strip(),
        'reference_commit': '888727f277b3ad4926c8d057e575887fd6c8e27d',
        'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
        'binary_sha256': {k: hashlib.sha256(Path(v).read_bytes()).hexdigest() for k,v in bins.items()},
        'cases': CASES, 'fixtures': FIXTURES, 'collector_seed': 12345,
        'online_repeats_per_single_point': ONLINE_REPEATS,
        'threads': 1, 'per_arm_timeout_seconds': 120,
        'load_start': os.getloadavg(), 'logical_cpus': os.cpu_count(),
        'measurement_class': 'exploratory shared-host full-pipeline implementation comparison',
        'tier_gate': 'not established', 'promoted_wall_speedup': None,
        'setup_boundary': 'entry to ca_ic_precompute through return; includes all reusable tables, collection, LA and factor-log verification',
        'online_boundary': 'each entry to ca_ic_log through return; includes internal replay; 100 independent repeated solves of the same public point, with raw individual intervals and per-point arithmetic means; additional independent exponentiation recorded separately',
        'target_fixtures': 'fixed five public points per case; generated before timing from the fixture formula in pipeline.c',
        'pair_rule': 'alternate reference/optimized order by fixture; retain all arms; compare public input, scalar and collection counts; preserve differing query counts as algorithm diagnostics',
    }
    (HERE/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    rows = []
    with (HERE/'samples.jsonl').open('w') as f:
        for p, method in CASES:
            for fixture in FIXTURES:
                variants = ['reference', 'optimized']
                if fixture & 1:
                    variants.reverse()
                for order, variant in enumerate(variants):
                    args = [bins[variant], str(p), str(method), str(fixture), str(ONLINE_REPEATS)]
                    row = dict(p=p, method=method, fixture=fixture, variant=variant, order=order)
                    started = time.time()
                    try:
                        proc = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=120)
                        row.update(exit_code=proc.returncode, stderr=proc.stderr)
                        row.update(json.loads(proc.stdout))
                        row['status'] = 'verified' if proc.returncode == 0 and row.get('verified') else 'failed'
                    except subprocess.TimeoutExpired:
                        row['status'] = 'timeout'
                    except Exception as error:
                        row.update(status='invalid_output', error=repr(error))
                    row.update(started_unix=started, finished_unix=time.time())
                    rows.append(row)
                    f.write(json.dumps(row, sort_keys=True)+'\n')
                    f.flush()
    summaries = []
    for p, method in CASES:
        pairs = []
        for fixture in FIXTURES:
            a, b = ({r['variant']:r for r in rows if (r['p'],r['method'],r['fixture']) == (p,method,fixture)}[v]
                    for v in ('reference','optimized'))
            agreement = all(a.get(k)==b.get(k) for k in ('g','h','x','relations','base_primes','verified_logs','online_repeats'))
            pair = dict(fixture=fixture, agreement=agreement, verified=a['status']==b['status']=='verified')
            if agreement and pair['verified']:
                for metric in ('setup_wall','setup_cpu','online_wall','online_cpu'):
                    pair[metric] = a[metric] / b[metric]
                pair['setup_plus_online_cpu'] = (a['setup_cpu']+a['online_cpu'])/(b['setup_cpu']+b['online_cpu'])
                pair['iterations'] = [a['lanczos_iterations'], b['lanczos_iterations']]
                pair['queries_reference_optimized'] = [a['online_tries'], b['online_tries']]
            pairs.append(pair)
        summary = dict(p=p, method=method, pairs=pairs)
        for metric in ('setup_wall','setup_cpu','online_wall','online_cpu','setup_plus_online_cpu'):
            vals = [pair[metric] for pair in pairs if metric in pair]
            summary[metric] = dict(median=statistics.median(vals), minimum=min(vals), maximum=max(vals)) if len(vals)==5 else None
        summaries.append(summary)
    (HERE/'summary.json').write_text(json.dumps(summaries, indent=2)+'\n')
    receipt.update(finished_unix=time.time(), load_end=os.getloadavg())
    (HERE/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    if any(r['status']!='verified' for r in rows) or any(not pair['agreement'] for s in summaries for pair in s['pairs']):
        raise SystemExit('panel contains failed or disagreeing arms; inspect retained samples')
    for s in summaries:
        print(s['p'], s['method'], 'setup CPU', s['setup_cpu'], 'online CPU', s['online_cpu'])


if __name__ == '__main__':
    main()
