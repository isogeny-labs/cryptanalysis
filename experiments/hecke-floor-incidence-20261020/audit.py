#!/usr/bin/env python3
"""Independently check D39/f6 conductors, rational fibers, rows, and ranks."""
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from sage.all import BinaryQF, EllipticCurve_from_j, PolynomialRing, QQ, classical_modular_polynomial, matrix

P = Path(__file__).resolve().parent
sys.path.insert(0, str(P / 'tools'))
import hecke11 as H  # noqa: E402

sha = lambda name: hashlib.sha256((P / name).read_bytes()).hexdigest()

def point(E, encoded):
    match = re.fullmatch(r'\((\d+) : (\d+) : 1\)', encoded)
    assert match, encoded
    return E([int(match.group(1)), int(match.group(2)), 1])

def rank_mod(rows, modulus, columns):
    pivots = {}
    for row in rows:
        current = {int(k): int(v) % modulus for k, v in row.items() if int(v) % modulus}
        assert all(0 <= col < columns for col in current)
        while current:
            pivot = min(current)
            if pivot not in pivots:
                inverse = pow(current[pivot], -1, modulus)
                pivots[pivot] = {col: value * inverse % modulus for col, value in current.items()}
                break
            multiplier = current[pivot]
            for col, value in pivots[pivot].items():
                updated = (current.get(col, 0) - multiplier * value) % modulus
                if updated:
                    current[col] = updated
                else:
                    current.pop(col, None)
    return len(pivots)

def rank_QQ(rows, columns):
    return int(matrix(QQ, [[int(row.get(str(j), 0)) for j in range(columns)]
                           for row in rows]).rank())

def main():
    protocol = json.loads((P / 'protocol.json').read_text())
    gate = json.loads((P / 'audit_protocol.json').read_text())
    launch = json.loads((P / 'launch.json').read_text())
    assert protocol['status'] == 'FROZEN_BEFORE_D39_F6_PRODUCER'
    assert gate['status'] == 'FROZEN_BEFORE_D39_F6_AUDIT'
    assert gate['audit_sha256'] == sha('audit.py')
    for name, digest in {**protocol['input_sha256'], **gate['files']}.items():
        assert sha(name) == digest, name
    assert launch['status'] == 'PROCESS_COMPLETE' and launch['exit_code'] == 0
    assert launch['protocol_sha256'] == sha('protocol.json')
    assert launch['result_sha256'] == sha('data/exp11_class_walk_D39_f6.json')
    data = json.loads((P / 'data/exp11_class_walk_D39_f6.json').read_text())
    assert (data['DK'], data['f'], data['p'], data['u'], data['hecke_primes']) == (-39, 6, 367, 8, [2, 3])
    assert 8 * 8 - 4 * 367 == -39 * 6 * 6
    form2, form3 = BinaryQF(2, 1, 44), BinaryQF(3, 0, 13)
    assert int(form2.discriminant()) == -351 and int(form3.discriminant()) == -156
    norm2_order, norm3_order = int(form2.form_class().order()), int(form3.form_class().order())
    assert norm2_order == 12 and norm3_order == 2
    funcs, jfun = H.build([2, 3])
    reduced = H.Reduced(367, funcs, jfun, [2, 3])
    points = [point(reduced.E, s) for s in data['column_points']]
    indexes = {q: i for i, q in enumerate(points)}
    assert len(points) == len(indexes) == data['class_size']
    phi = {ell: classical_modular_polynomial(ell) for ell in (2, 3)}
    ring = PolynomialRing(reduced.Fp, 'J')
    J = ring.gen()
    conductors_by_j = {}
    strata = Counter()
    root_counts = {2: Counter(), 3: Counter()}
    by_conductor = {2: defaultdict(Counter), 3: defaultdict(Counter)}
    point_records, row_records = [], []
    row_index = 0
    for index, q in enumerate(points):
        j = reduced.j(q)
        assert j is not None
        key = int(j)
        if key not in conductors_by_j:
            conductors_by_j[key] = int(EllipticCurve_from_j(j).endomorphism_order().conductor())
        c = conductors_by_j[key]
        assert 6 % c == 0
        strata[c] += 1
        record = {'column': index, 'j': key, 'endomorphism_conductor': c, 'degrees': {}}
        for ell in (2, 3):
            predicted = ell + 1 if (6 // c) % ell == 0 else 1
            hecke_roots = reduced.neighbour_x(ell, q).roots()
            modular_roots = ring(phi[ell](j, J)).roots()
            hecke_total = sum(int(m) for _, m in hecke_roots)
            modular_total = sum(int(m) for _, m in modular_roots)
            assert hecke_total == modular_total == predicted, (index, c, ell, predicted, hecke_total, modular_total)
            root_counts[ell][hecke_total] += 1
            by_conductor[ell][c][hecke_total] += 1
            record['degrees'][str(ell)] = {'predicted': predicted,
                                          'hecke_roots_with_multiplicity': hecke_total,
                                          'modular_roots_with_multiplicity': modular_total,
                                          'distinct_hecke_x_roots': len(hecke_roots),
                                          'distinct_modular_j_roots': len(modular_roots)}
            if predicted == ell + 1:
                neighbours = reduced.neighbours_all(ell, q)
                assert neighbours is not None and len(neighbours) == ell + 1
                assert sum(neighbours, reduced.E(0)) == reduced.a_l[ell] * q
                assert all(neighbour in indexes for neighbour in neighbours)
                row = Counter(indexes[neighbour] for neighbour in neighbours)
                row[index] -= reduced.a_l[ell]
                decoded = {str(k): int(v) for k, v in row.items() if v}
                saved = {k: int(v) for k, v in data['relation_rows'][row_index].items() if v}
                assert decoded == saved, (index, ell, row_index)
                row_records.append({'row': row_index, 'source_column': index,
                                    'source_conductor': c, 'degree': ell})
                row_index += 1
        point_records.append(record)
    assert row_index == len(data['relation_rows']) == data['relations']
    labels = [x['degree'] for x in row_records]
    assert {str(ell): labels.count(ell) for ell in (2, 3)} == data['relations_per_l']
    ranks = {}
    for modulus in (23, 1000000007, 2147483647):
        ranks[str(modulus)] = {}
        for subset in ((2,), (3,), (2, 3)):
            rows = [row for row, label in zip(data['relation_rows'], labels) if label in subset]
            ranks[str(modulus)]['+'.join(map(str, subset))] = rank_mod(rows, modulus, len(points))
    ranks['QQ'] = {}
    for subset in ((2,), (3,), (2, 3)):
        rows = [row for row, label in zip(data['relation_rows'], labels) if label in subset]
        ranks['QQ']['+'.join(map(str, subset))] = rank_QQ(rows, len(points))
    assert all(value['2+3'] == data['rank'] for value in ranks.values())
    summary_match = (len(points) == 64 and dict(strata) == {1: 8, 2: 8, 3: 24, 6: 24}
                     and root_counts[2] == {1: 32, 3: 32}
                     and root_counts[3] == {1: 48, 4: 16}
                     and row_index == 48 and all(v == {'2': 32, '3': 16, '2+3': 40}
                                             for v in ranks.values()))
    output = {'status': 'VERIFIED_D39_F6_MATRIX' if summary_match else 'PREDICTION_MISMATCH',
              'prediction_match': summary_match, 'source_sha256': sha('data/exp11_class_walk_D39_f6.json'),
              'launch_sha256': sha('launch.json'), 'audit_script_sha256': sha('audit.py'),
              'runtime_info_sha256': sha('sage_runtime.json'), 'norm2_class_order': norm2_order,
              'norm3_class_order': norm3_order, 'point_count': len(points),
              'conductor_counts': dict(sorted(strata.items())),
              'root_counts': {str(ell): dict(sorted(root_counts[ell].items())) for ell in (2, 3)},
              'by_conductor': {str(ell): {str(c): dict(sorted(v.items()))
                                          for c, v in sorted(by_conductor[ell].items())} for ell in (2, 3)},
              'matched_rows': row_index, 'subset_ranks': ranks,
              'points': point_records, 'row_records': row_records,
              'candidate_id': None, 'timing_claim': None}
    (P / 'audit.json').write_text(json.dumps(output, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': output['status'], 'points': len(points),
                      'rows': row_index, 'ranks': ranks}))

if __name__ == '__main__':
    main()
