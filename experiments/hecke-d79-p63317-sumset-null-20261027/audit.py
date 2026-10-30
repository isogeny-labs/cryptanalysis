"""Independent pair-plus-third enumeration of every matched null row."""
import hashlib
import itertools
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / 'inputs.json').read_text())
POST = json.loads((HERE / 'post-run.json').read_text())


def pinned(name):
    item = PLAN['frozen'][name]
    raw = (ROOT / item['path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == item['sha256']
    return json.loads(raw)


def replay(a, q):
    # Build signed pairs once, then extend each by a later third source.
    all_points = set()
    no_anchor = set()
    for i, j in itertools.combinations(range(40), 2):
        pair_values = (a[i] + a[j], a[i] - a[j], -a[i] + a[j], -a[i] - a[j])
        for k in range(j + 1, 40):
            for v in pair_values:
                plus = (v + a[k]) % q
                minus = (v - a[k]) % q
                all_points.add(plus)
                all_points.add(minus)
                if i != 0:
                    no_anchor.add(plus)
                    no_anchor.add(minus)
    translated = {(v - a[0]) % q for v in no_anchor}
    return (len(all_points), len(no_anchor), len(translated - all_points),
            len(all_points | translated), len(all_points | translated) == q)


def main():
    raw = (HERE / 'result.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == POST['result_sha256']
    result = json.loads(raw)
    assert pinned('four-audit.json')['status'] == 'PASS'
    q = PLAN['q']
    logs = pinned('class-logs.json')['q_logs']
    observed = replay(logs, q)
    keys = ('triple_coverage', 'triple_without_anchor_coverage',
            'fixed_translate_additional', 'fixed_translate_union', 'fixed_translate_full')
    assert observed == tuple(result['observed'][key] for key in keys)
    seed_text = 'hecke-d79-p63317-sumset-null-v1'
    assert result['seed_text'] == seed_text
    rng = random.Random(int(hashlib.sha256(seed_text.encode()).hexdigest(), 16))
    rows = result['control_rows']
    assert len(rows) == 256
    triple_values, gain_values, full_count = [], [], 0
    for n, row in enumerate(rows):
        reps = rng.sample(range(2, 1266), 19)
        assert row['draw'] == n and row['orbit_representatives'] == reps
        a = [1] + reps + [q - 1] + [q - r for r in reps]
        metrics = replay(a, q)
        assert metrics == tuple(row[key] for key in keys), n
        triple_values.append(metrics[0])
        gain_values.append(metrics[2])
        full_count += metrics[4]
    s = result['summary']
    assert s['triple_coverage_min'] == min(triple_values)
    assert s['triple_coverage_max'] == max(triple_values)
    assert s['triple_upper_tail_count'] == sum(v >= observed[0] for v in triple_values)
    assert s['triple_lower_tail_count'] == sum(v <= observed[0] for v in triple_values)
    assert s['fixed_gain_min'] == min(gain_values) and s['fixed_gain_max'] == max(gain_values)
    assert s['full_union_draws'] == full_count
    out = {'schema': 'hecke-d79-p63317-sumset-null-audit-v1', 'status': 'PASS',
           'draws_replayed': len(rows), 'observed_metrics': dict(zip(keys, observed)),
           'control_triple_min': min(triple_values), 'control_triple_max': max(triple_values),
           'control_full_union_draws': full_count}
    (HERE / 'audit.json').write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'status': 'PASS', 'draws_replayed': len(rows),
                      'full_union_draws': full_count}))


if __name__ == '__main__':
    main()
