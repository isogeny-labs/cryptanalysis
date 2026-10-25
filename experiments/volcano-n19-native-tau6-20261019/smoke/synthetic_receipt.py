"""Synthetic receipt (fake numbers, plumbing test of verify_receipt.py only; not data).

    python3 synthetic_receipt.py OUTDIR [--break-gate]
"""
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.join(HERE, '..')
sched = json.load(open(os.path.join(EXP, 'schedule.json')))
info = json.load(open(os.path.join(EXP, '..', 'volcano-ic', 'rho-arm-20261014', 'results', 'runtime-info.json')))
out = sys.argv[1]
os.makedirs(out, exist_ok=True)
rng = random.Random(1)
f = open(os.path.join(out, 'runs.jsonl'), 'w')
for seg in sched['segments']:
    for r in seg['rows']:
        a = r['arm']
        base = {'arm': a, 'affinity': [0], 'native_sha256': 'x' * 64, 'correct': True}
        if a == 'selftest':
            base.update({'systems': 300, 'set_equal': 300, 'bruteforce_equal': 300, 'ok': True})
        elif a == 'O':
            base.update({'all_equal': True, 'instances': []})
        elif a == 'rho':
            base.update({'cpu_s': 0.0025, 'cpu_s_total': 0.16, 'group_ops_total': 6000, 'verified_reps': 64,
                         'steps_mean': 73})
            base.pop('native_sha256')
        else:
            k = int(r['point'][1:])
            cold = {'B': 40.0, 'NX': 41.0}.get(a, 0.6) * (1 + 0.02 * rng.random()) * (1 + 0.1 * k / 16)
            base.update({'scalar': r['scalar'], 'targets': 300 + k, 'gb_calls': 5000 + k, 'spurious': 1,
                         'relations': 39, 'log': r['scalar'], 'cold_cpu_s': cold, 'setup_cpu_s': 0.01,
                         'online_cpu_s': cold - 0.01, 'cold_wall_s': cold, 'gb_cpu_s': cold * 0.9,
                         'linalg_cpu_s': 0.003, 'relation_cpu_s': cold - 0.013, 'P': info['P'],
                         'relations_digest': {'rows_sha256': 'r%d' % k, 'canonical_sha256': 'c%d' % k,
                                              'ordered_sha256': 'o%d' % k}})
            if a == 'B':
                base.pop('native_sha256')
            if a == 'NX':
                base['plant'] = {'checked_calls': 5000 + k}
            if a in ('N', 'Naa'):
                base['warm_batch'] = {'same_relations': True, 'setup_cpu_s_mean': 0.005, 'online_cpu_s_mean': 0.55}
        if '--break-gate' in sys.argv and r['row'] == 'p03-Naa':
            base['gb_calls'] += 1
        f.write(json.dumps({'segment': seg['id'], **r, 'status': 'ran', 'exit': 0, 'launcher_wall_s': 5.0,
                            'result': base}) + '\n')
