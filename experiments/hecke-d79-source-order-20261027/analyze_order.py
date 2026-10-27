"""Exact baseline witness and frozen 256-permutation scheduling diagnostic."""
import hashlib
import json
from pathlib import Path

from sympy import Matrix, ilcm

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / 'inputs.json').read_text())


def pinned(path, sha):
    raw = (ROOT / path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != sha:
        raise ValueError('PIN_MISMATCH:' + path)
    return json.loads(raw)


def dense(row):
    return [int(row.get(str(i), 0)) for i in range(40)]


def permutation(p, rep):
    return sorted(range(40), key=lambda i: (
        hashlib.sha256(f'hecke-d79-order-v1|{p}|{rep}|{i}'.encode()).digest(), i))


def first_count(order, active_sets):
    positions = {source: k + 1 for k, source in enumerate(order)}
    return min(max(positions[i] for i in sources) for sources in active_sets)


def main():
    output = {'schema': 'hecke-d79-source-order-analysis-v1', 'cases': []}
    for case in PLAN['cases']:
        result = pinned(case['result_path'], case['result_sha256'])
        analysis = pinned(case['analysis_path'], case['analysis_sha256'])
        direct = analysis['direct']['candidates']
        hecke = analysis['hecke']['candidates']
        selected = analysis['direct']['selected_candidate_indices']
        witness_rows = [dense(x['row']) for x in result['base_rows']]
        witness_rows += [dense(direct[i]['row']) for i in selected]
        mat = Matrix(witness_rows)
        null = mat.nullspace()
        if mat.rank() != 39 or len(null) != 1:
            raise ValueError('BASELINE_RANK_MISMATCH')
        scale = ilcm(*[x.q for x in null[0]])
        vector = [int(x * scale) for x in null[0]]
        def pairing(row):
            return sum(a * b for a, b in zip(dense(row), vector))
        if any(pairing(x['row']) for x in result['base_rows']):
            raise ValueError('BASE_ROW_WITNESS_MISMATCH')
        if any(pairing(x['row']) for x in direct):
            raise ValueError('DIRECT_ROW_WITNESS_MISMATCH')
        active = [i for i, x in enumerate(hecke) if pairing(x['row'])]
        if not active:
            raise ValueError('NO_RANK_RAISING_ROWS')
        active_sets = [tuple(hecke[i]['sources']) for i in active]
        if len(set(active_sets)) != len(active_sets):
            raise ValueError('DUPLICATE_ACTIVE_SOURCES')
        counts = [first_count(permutation(case['p'], rep), active_sets)
                  for rep in range(PLAN['policy']['repetitions'])]
        ascending = first_count(list(range(40)), active_sets)
        out = {'p': case['p'], 'baseline_rank_qq': 39,
               'baseline_null_vector': vector, 'active_candidate_indices': active,
               'active_candidate_count': len(active), 'all_candidate_count': len(hecke),
               'ascending_source_count': ascending, 'source_counts': counts,
               'replay_order': permutation(case['p'], PLAN['policy']['replay_rep']),
               'replay_predicted_source_count': counts[PLAN['policy']['replay_rep']]}
        output['cases'].append(out)
    (HERE / 'analysis.json').write_text(json.dumps(output, indent=2, sort_keys=True) + '\n')
    for case in output['cases']:
        counts = sorted(case['source_counts'])
        print(json.dumps({'p': case['p'], 'active': case['active_candidate_count'],
                          'ascending': case['ascending_source_count'],
                          'rep0': case['replay_predicted_source_count'],
                          'median': (counts[127] + counts[128]) / 2}))


if __name__ == '__main__':
    main()
