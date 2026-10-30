"""Exhaustive rank-gain and source-union search over frozen Hecke rows."""
import hashlib
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / 'inputs.json').read_text())


def pinned(name):
    item = PLAN['frozen'][name]
    raw = (ROOT / item['path']).read_bytes()
    if hashlib.sha256(raw).hexdigest() != item['sha256']:
        raise ValueError('PARENT_PIN_MISMATCH:' + name)
    return json.loads(raw)


def row(item, q):
    return [int(item['row'].get(str(i), 0)) % q for i in range(40)]


def reduce(basis, v, q):
    v = v[:]
    for p, b in sorted(basis.items()):
        if v[p]:
            factor = v[p]
            v = [(x - factor*y) % q for x, y in zip(v, b)]
    return v


def insert(basis, v, q):
    v = reduce(basis, v, q)
    for p, x in enumerate(v):
        if x:
            inv = pow(x, -1, q)
            basis[p] = [(inv*y) % q for y in v]
            return True
    return False


def main():
    cls = pinned('class-result.json')
    analysis = pinned('analysis.json')
    source = pinned('source-result.json')
    logs = pinned('class-logs.json')
    cases = []
    for p in PLAN['primes']:
        c = next(x for x in cls['cases'] if x['p'] == p)
        a = next(x for x in analysis['cases'] if x['p'] == p)
        s = next(x for x in source['cases'] if x['p'] == p)
        q = c['largest_prime_factor']
        basis = {}
        for item in c['base_rows'] + a['direct_candidates']:
            insert(basis, row(item, q), q)
        base_rank = len(basis)
        residuals = [reduce(basis, row(x, q), q) for x in a['hecke_candidates']]
        full_basis = {k:v[:] for k,v in basis.items()}
        for v in residuals:
            insert(full_basis, v, q)
        full_rank = len(full_basis)
        gain = full_rank - base_rank
        if gain not in (1, 2):
            raise ValueError('UNSUPPORTED_GAIN')
        tested = 0
        rank_increasing = 0
        four_source_union_pairs = 0
        four_source_union_rank_two = 0
        best = None
        iterator = ((i,) for i in range(len(residuals))) if gain == 1 else itertools.combinations(range(len(residuals)), 2)
        for indices in iterator:
            tested += 1
            union = tuple(sorted(set().union(*(a['hecke_candidates'][i]['sources'] for i in indices))))
            trial = {}
            for i in indices:
                insert(trial, residuals[i], q)
            trial_rank = len(trial)
            if gain == 2 and len(union) == 4:
                four_source_union_pairs += 1
                four_source_union_rank_two += trial_rank == 2
            if trial_rank != gain:
                continue
            rank_increasing += 1
            score = (len(union), union, indices)
            if best is None or score < best:
                best = score
        if best is None:
            raise ValueError('NO_COMPLETING_WITNESS')
        union = list(best[1])
        chosen = list(best[2])
        lifts = s['degree13_sources']
        lift_ns = sum(lifts[i]['lift_wall_ns'] for i in union)
        cases.append({'p': p, 'q': q, 'class_points': 40,
                      'base_row_count': len(c['base_rows']),
                      'direct_candidate_count': len(a['direct_candidates']),
                      'hecke_candidate_count': len(a['hecke_candidates']),
                      'baseline_rank': base_rank, 'full_pool_rank': full_rank,
                      'rank_gain': gain, 'tested_combinations': tested,
                      'rank_increasing_combinations': rank_increasing,
                      'four_source_union_pairs': four_source_union_pairs,
                      'four_source_union_rank_two': four_source_union_rank_two,
                      'selected_candidate_indices': chosen,
                      'selected_sources': union, 'selected_source_count': len(union),
                      'selected_rows': [a['hecke_candidates'][i] for i in chosen],
                      'selected_source_lift_ns': lift_ns,
                      'all_source_lift_ns': sum(x['lift_wall_ns'] for x in lifts),
                      'remaining_rank_deficit': 40 - full_rank})
    assert next(x for x in cases if x['p'] == 63317)['full_pool_rank'] == logs['relation_rank_mod_q'] == 39
    out = {'schema': 'hecke-d79-rank-source-compression-v1', 'status': 'COMPLETE',
           'cases': cases, 'candidate_id': None, 'target_online_ms': None}
    (HERE / 'result.json').write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'cases': [{k:x[k] for k in ('p','baseline_rank','full_pool_rank','selected_sources','selected_candidate_indices','remaining_rank_deficit')} for x in cases]}))


if __name__ == '__main__':
    main()
