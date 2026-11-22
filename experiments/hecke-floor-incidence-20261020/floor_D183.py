#!/usr/bin/env python3
"""Replay signed degree-2 cycles and ramified degree-3 floor pairings."""
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from sage.all import QQ, matrix, vector

P = Path(__file__).resolve().parent
sys.path.insert(0, str(P / 'tools'))
from degree2_graph_audit import components, signed_component  # noqa: E402
from validate import sparse_rank  # noqa: E402

sha = lambda name: hashlib.sha256((P / name).read_bytes()).hexdigest()

def dense(row, columns):
    return [int(row.get(str(j), 0)) for j in range(columns)]

def rank_QQ(rows, columns):
    return int(matrix(QQ, [dense(row, columns) for row in rows]).rank())

def main():
    gate = json.loads((P / 'audit_protocol_D183.json').read_text())
    protocol = json.loads((P / 'protocol_D183.json').read_text())
    assert gate['status'] == 'FROZEN_BEFORE_D183_F6_AUDIT'
    assert gate['floor_sha256'] == sha('floor_D183.py')
    for name, digest in gate['files'].items():
        assert sha(name) == digest, name
    audit = json.loads((P / 'audit_D183.json').read_text())
    assert audit['status'] == 'VERIFIED_D183_F6_MATRIX'
    data = json.loads((P / 'data/exp11_class_walk_D183_f6.json').read_text())
    rows = [{int(k): int(v) for k, v in r.items() if v} for r in data['relation_rows']]
    metadata = audit['row_records']
    assert len(rows) == len(metadata) == 96
    floor = {r['column'] for r in audit['points'] if r['endomorphism_conductor'] == 6}
    nonfloor = set(range(len(audit['points']))) - floor
    degree2 = {i: row for i, row in enumerate(rows) if metadata[i]['degree'] == 2}
    c3_degree2 = {i: row for i, row in degree2.items() if metadata[i]['source_conductor'] == 3}
    groups, owners = components(c3_degree2, nonfloor)
    accepted, rejected = [], []
    for group in groups:
        cert, reason = signed_component(group, c3_degree2, owners, floor)
        if cert is None:
            rejected.append({'rows': sorted(group), 'reason': reason})
        else:
            accepted.append(cert)
    cycle_floor = [{int(k): int(v) for k, v in cert['signed_floor_columns'].items()}
                   for cert in accepted]
    cycle_floor_use = Counter(k for row in cycle_floor for k in row)
    c2_degree3 = {i: row for i, row in enumerate(rows)
                  if metadata[i]['degree'] == 3 and metadata[i]['source_conductor'] == 2}
    by_lower = defaultdict(list)
    for i, row in c2_degree3.items():
        by_lower[tuple(sorted((k, v) for k, v in row.items() if k in nonfloor))].append(i)
    pair_groups = [sorted(indices) for indices in by_lower.values()]
    pair_groups.sort()
    pair_records, pair_vectors = [], []
    for indices in pair_groups:
        if len(indices) != 2:
            pair_records.append({'rows': indices, 'status': 'NOT_A_PAIR'})
            continue
        a, b = indices
        diff = {k: rows[a].get(k, 0) - rows[b].get(k, 0)
                for k in rows[a].keys() | rows[b].keys()}
        diff = {k: v for k, v in diff.items() if v}
        status = 'EXACT_FLOOR_DIFFERENCE' if set(diff) <= floor else 'NONFLOOR_REMAINDER'
        pair_records.append({'rows': indices, 'status': status,
                             'signed_columns': {str(k): v for k, v in sorted(diff.items())}})
        if status == 'EXACT_FLOOR_DIFFERENCE':
            pair_vectors.append(diff)
    pair_floor_use = Counter(k for row in pair_vectors for k in row)
    cycle_in_pair_span = []
    if pair_vectors:
        M = matrix(QQ, [[row.get(j, 0) for j in range(len(audit['points']))]
                        for row in pair_vectors])
        for cycle in cycle_floor:
            vec = vector(QQ, [cycle.get(j, 0) for j in range(len(audit['points']))])
            try:
                coeffs = M.solve_left(vec)
                replay = coeffs * M == vec
                cycle_in_pair_span.append({'in_span': bool(replay),
                                           'coefficients': [str(x) for x in coeffs]})
            except (ArithmeticError, ValueError):
                cycle_in_pair_span.append({'in_span': False, 'coefficients': None})
    ranks = {}
    for modulus in ('QQ', '23', '1000000007', '2147483647'):
        ranks[modulus] = {}
        for subset in ((2,), (3,), (2, 3)):
            selected = [row for row, info in zip(rows, metadata) if info['degree'] in subset]
            projected = [{k: v for k, v in row.items() if k in nonfloor} for row in selected]
            # The sparse modular reducer accepts integer or string keys.
            if modulus == 'QQ':
                full_rank = rank_QQ([{str(k): v for k, v in row.items()} for row in selected], len(audit['points']))
                projected_rank = rank_QQ([{str(k): v for k, v in row.items()} for row in projected], len(audit['points']))
            else:
                full_rank = sparse_rank(selected, int(modulus), len(audit['points']))
                projected_rank = sparse_rank(projected, int(modulus), len(audit['points']))
            ranks[modulus]['+'.join(map(str, subset))] = [full_rank, projected_rank]
    forecast = protocol['subset_rank_predicted']
    rank_match = all(r == forecast for r in ranks.values())
    graph_match = (len(accepted) == 2 and not rejected
                   and sorted(len(x['signed_rows']) for x in accepted) == [24, 24]
                   and set(cycle_floor_use) == floor
                   and all(v == 1 for v in cycle_floor_use.values()))
    pair_match = (len(pair_groups) == len(pair_vectors) == 8
                  and all(x['status'] == 'EXACT_FLOOR_DIFFERENCE' for x in pair_records)
                  and all(len(x) == 6 and set(x.values()) <= {-1, 1} for x in pair_vectors)
                  and set(pair_floor_use) == floor
                  and all(v == 1 for v in pair_floor_use.values()))
    span_match = (len(cycle_in_pair_span) == 2
                  and all(not x['in_span'] for x in cycle_in_pair_span))
    outcome = graph_match and pair_match and rank_match and span_match
    result = {'status': 'VERIFIED_D183_F6_FLOOR_PREDICTION' if outcome else 'VERIFIED_D183_F6_FLOOR_MISMATCH',
              'prediction_match': outcome, 'graph_match': graph_match,
              'pair_match': pair_match, 'span_match': span_match, 'rank_match': rank_match,
              'protocol_sha256': sha('protocol_D183.json'), 'audit_sha256': sha('audit_D183.json'),
              'source_sha256': sha('data/exp11_class_walk_D183_f6.json'),
              'floor_script_sha256': sha('floor_D183.py'),
              'graph_reference_sha256': sha('tools/degree2_graph_audit.py'),
              'floor_columns': len(floor), 'degree2_components': len(groups),
              'signed_degree2_components': len(accepted), 'rejected_components': rejected,
              'degree2_certificates': accepted, 'degree3_c2_rows': len(c2_degree3),
              'degree3_pair_groups': pair_groups, 'degree3_pair_records': pair_records,
              'cycle_in_pair_span': cycle_in_pair_span, 'ranks': ranks,
              'candidate_id': None, 'timing_claim': None}
    (P / 'floor_D183.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'graph_match': graph_match,
                      'pair_match': pair_match, 'span_match': span_match,
                      'rank_match': rank_match, 'ranks': ranks['QQ']}))

if __name__ == '__main__':
    main()
