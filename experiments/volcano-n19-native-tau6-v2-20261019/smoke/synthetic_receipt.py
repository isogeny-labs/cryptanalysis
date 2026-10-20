"""Synthetic receipt for protocol v2 (fake numbers, plumbing test of verify_receipt.py only; not data).

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
proto = json.load(open(os.path.join(EXP, 'protocol.json')))
f = open(os.path.join(out, 'runs.jsonl'), 'w')
for seg in sched['segments']:
    for r in seg['rows']:
        a = r['arm']
        base = {'arm': a, 'affinity': [0], 'native_sha256': 'x' * 64, 'correct': True,
                'binding_check': {'ok': True}}
        if a == 'selftest':
            n0, n3 = proto['s0']['systems'], proto['s0']['v1_systems'] + proto['s0']['new_systems']
            det = [{'src': 'v1', 'xR': x, 'j': j} for x, j in proto['s0']['v1_mismatch_systems']]
            det += [{'src': 'other'}] * (n0 - len(det))
            base.update({'systems': n0, 'set_equal': n0, 'order_equal': n0, 'bruteforce_equal': n0,
                         'third_checked': n3, 'third_equal': n3, 'multi_systems': proto['s0']['multi_systems'],
                         'detail': det, 'ok': True})
        elif a == 'O':
            base.update({'all_equal': True, 'instances': []})
        elif a == 'rho':
            base.update({'cpu_s': 0.0025, 'cpu_s_total': 0.16, 'group_ops_total': 6000, 'verified_reps': 64,
                         'steps_mean': 73})
            base.pop('native_sha256')
            base.pop('binding_check')
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
                base.pop('binding_check')
            if a == 'NX':
                base['plant'] = {'checked_calls': 5000 + k, 'multi_solution_calls': 2, 'order_agree_calls': 2}
            if a in ('N', 'Naa'):
                base['warm_batch'] = {'same_relations': True, 'setup_cpu_s_mean': 0.005, 'online_cpu_s_mean': 0.55}
        if '--break-gate' in sys.argv and r['row'] == 'p03-Naa':
            base['gb_calls'] += 1
        if '--break-binding' in sys.argv and r['row'] == 'p05-N':
            base['binding_check'] = {'ok': False}
        if '--break-order' in sys.argv and r['row'] == 'p07-B':
            base['relations_digest'] = dict(base['relations_digest'], ordered_sha256='other')
        f.write(json.dumps({'segment': seg['id'], **r, 'status': 'ran', 'exit': 0, 'launcher_wall_s': 5.0,
                            'result': base}) + '\n')
