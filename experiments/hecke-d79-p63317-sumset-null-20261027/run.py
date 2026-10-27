"""Matched negation-closed random controls for the p63317 class sumset."""
import hashlib
import itertools
import json
import platform
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / 'inputs.json').read_text())
SEED_TEXT = 'hecke-d79-p63317-sumset-null-v1'


def pinned(name):
    item = PLAN['frozen'][name]
    raw = (ROOT / item['path']).read_bytes()
    if hashlib.sha256(raw).hexdigest() != item['sha256']:
        raise ValueError('PARENT_PIN_MISMATCH:' + name)
    return json.loads(raw)


def coverage(a, q):
    full = set()
    without0 = set()
    patterns = 0
    for i, j, k in itertools.combinations(range(40), 3):
        for si, sj, sk in itertools.product((-1, 1), repeat=3):
            v = (si*a[i] + sj*a[j] + sk*a[k]) % q
            full.add(v)
            if i != 0:
                without0.add(v)
            patterns += 1
    fixed = {(v - a[0]) % q for v in without0}
    return {'triple_patterns': patterns, 'triple_coverage': len(full),
            'triple_without_anchor_coverage': len(without0),
            'fixed_translate_additional': len(fixed - full),
            'fixed_translate_union': len(full | fixed),
            'fixed_translate_full': len(full | fixed) == q}


def quantile(x, num, den):
    ordered = sorted(x)
    return ordered[(len(ordered) - 1) * num // den]


def main():
    q = PLAN['q']
    logs = pinned('class-logs.json')
    parent = pinned('four-result.json')
    assert logs['q'] == q and parent['status'] == 'ALL_RESIDUALS_FOUND'
    observed_logs = logs['q_logs']
    assert observed_logs[0] == 1 and len(set(observed_logs)) == 40
    assert all(v and (-v) % q in observed_logs for v in observed_logs)
    observed = coverage(observed_logs, q)
    assert observed['triple_coverage'] == parent['triple_coverage_points'] == 2503
    assert observed['fixed_translate_additional'] == 28
    assert observed['fixed_translate_union'] == q
    rng = random.Random(int.from_bytes(hashlib.sha256(SEED_TEXT.encode()).digest(), 'big'))
    rows = []
    for n in range(256):
        reps = rng.sample(range(2, 1266), 19)
        base = [1, *reps, q-1, *((q-r) for r in reps)]
        row = {'draw': n, 'orbit_representatives': reps, **coverage(base, q)}
        rows.append(row)
    values = [row['triple_coverage'] for row in rows]
    gains = [row['fixed_translate_additional'] for row in rows]
    summary = {'draws': len(rows), 'triple_coverage_min': min(values),
               'triple_coverage_q25': quantile(values, 1, 4),
               'triple_coverage_median': quantile(values, 1, 2),
               'triple_coverage_q75': quantile(values, 3, 4),
               'triple_coverage_max': max(values),
               'triple_upper_tail_count': sum(v >= observed['triple_coverage'] for v in values),
               'triple_lower_tail_count': sum(v <= observed['triple_coverage'] for v in values),
               'triple_upper_tail_fraction': f"{1+sum(v >= observed['triple_coverage'] for v in values)}/257",
               'triple_lower_tail_fraction': f"{1+sum(v <= observed['triple_coverage'] for v in values)}/257",
               'fixed_gain_min': min(gains), 'fixed_gain_median': quantile(gains, 1, 2),
               'fixed_gain_max': max(gains),
               'full_union_draws': sum(row['fixed_translate_full'] for row in rows)}
    out = {'schema': 'hecke-d79-p63317-sumset-null-v1', 'status': 'COMPLETE',
           'p': PLAN['p'], 'q': q, 'seed_text': SEED_TEXT,
           'seed_sha256': hashlib.sha256(SEED_TEXT.encode()).hexdigest(),
           'python_version': platform.python_version(),
           'observed': observed, 'control_rows': rows, 'summary': summary,
           'candidate_id': None, 'target_online_ms': None}
    (HERE / 'result.json').write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'observed': observed, 'summary': summary}))


if __name__ == '__main__':
    main()
