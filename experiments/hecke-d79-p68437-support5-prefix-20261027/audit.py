"""Independent exact-arithmetic replay of every reported prefix rank."""
import hashlib
import json
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / 'inputs.json').read_text())


def read_pinned(item):
    raw = (ROOT / item['path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == item['sha256']
    return json.loads(raw)


def row(record):
    return {int(k): int(v) for k, v in record['row'].items() if v}


def rank(rows, modulus=None):
    pivots = {}
    for sparse in rows:
        v = {i: (x % modulus if modulus else Fraction(x)) for i, x in sparse.items()}
        v = {i: x for i, x in v.items() if x}
        while v:
            col = min(v)
            if col not in pivots:
                scalar = v[col]
                pivots[col] = {i: (x * pow(int(scalar), -1, modulus) % modulus if modulus else x / scalar)
                               for i, x in v.items()}
                break
            scalar = v[col]
            for i, x in pivots[col].items():
                y = v.get(i, 0) - scalar * x
                if modulus:
                    y %= modulus
                if y:
                    v[i] = y
                else:
                    v.pop(i, None)
    return len(pivots)


def main():
    frozen = {key: read_pinned(value) for key, value in PLAN['frozen'].items()}
    cls = next(x for x in frozen['class']['cases'] if x['p'] == PLAN['p'])
    earlier = next(x for x in frozen['support4']['cases'] if x['p'] == PLAN['p'])
    support5 = frozen['support5']['arms']
    base = [row(x) for x in cls['base_rows'] + earlier['direct_candidates'] + earlier['hecke_candidates']]
    direct = [row(x) for x in support5['direct']['candidates']]
    hecke = support5['hecke']['candidates']
    assert (rank(base), rank(base + direct)) == (34, 39)
    output = {'schema': 'hecke-d79-p68437-support5-prefix-audit-v1', 'status': 'PASS', 'runs': {}}
    for order in PLAN['orders']:
        run = json.loads((HERE / f'run-{order}.json').read_text())
        expected_order = cls['ascending_order' if order == 'ascending' else 'priority_order']
        assert run['status'] == 'COMPLETE' and run['order'] == order
        assert run['visited_sources'] == len(run['steps'])
        assert run['cache']['status'] == 'CACHE_HIT' and run['cache']['build_invocations'] == 0
        first = {label: None for label in PLAN['baselines']}
        previous = {label: 0 for label in PLAN['baselines']}
        for step_number, step in enumerate(run['steps'], 1):
            assert step['source'] == expected_order[step_number - 1]
            assert step['source_count'] == step_number
            seen = set(expected_order[:step_number])
            selected = [row(x) for x in hecke if set(x['sources']) <= seen]
            assert step['candidate_count'] == len(selected)
            assert step['pair_entries'] == 4 * step_number * (step_number - 1) // 2
            assert step['triple_queries'] == 4 * step_number * (step_number - 1) * (step_number - 2) // 6
            for label, rows in [('support4', base + selected),
                                ('support4_plus_direct5', base + direct + selected)]:
                rational = rank(rows)
                mod_q = rank(rows, PLAN['q'])
                assert step['ranks'][label] == {'rank_qq': rational, 'rank_mod_q': mod_q}
                assert rational >= previous[label]
                previous[label] = rational
                if rational == PLAN['class_size'] and first[label] is None:
                    first[label] = step_number
        assert first == run['stop_source_counts']
        assert all(x is not None for x in first.values())
        assert len(run['steps']) == max(first.values())
        output['runs'][order] = {'first_rational_rank40': first,
                                 'visited_sources': len(run['steps']),
                                 'candidate_count_at_stop': run['steps'][-1]['candidate_count'],
                                 'final_rank_mod_q': {k: v['rank_mod_q'] for k, v in run['steps'][-1]['ranks'].items()},
                                 'run_sha256': hashlib.sha256((HERE / f'run-{order}.json').read_bytes()).hexdigest()}
    (HERE / 'audit.json').write_text(json.dumps(output, indent=2, sort_keys=True) + '\n')
    print(json.dumps(output['runs'], sort_keys=True))


if __name__ == '__main__':
    main()
