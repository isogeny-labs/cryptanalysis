#!/usr/bin/env python3
"""Independent exact replay of the D39/f6 floor-span mismatch."""
import hashlib
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path

P = Path(__file__).resolve().parent
sha = lambda name: hashlib.sha256((P / name).read_bytes()).hexdigest()

def rank(rows, columns, modulus=None):
    pivots = {}
    for encoded in rows:
        if modulus is None:
            current = {int(k): Fraction(v) for k, v in encoded.items() if v}
        else:
            current = {int(k): int(v) % modulus for k, v in encoded.items() if int(v) % modulus}
        assert all(0 <= k < columns for k in current)
        while current:
            pivot = min(current)
            if pivot not in pivots:
                inverse = 1 / current[pivot] if modulus is None else pow(current[pivot], -1, modulus)
                pivots[pivot] = {k: v * inverse if modulus is None else v * inverse % modulus
                                 for k, v in current.items()}
                break
            scalar = current[pivot]
            for k, v in pivots[pivot].items():
                updated = current.get(k, 0) - scalar * v
                if modulus is not None:
                    updated %= modulus
                if updated:
                    current[k] = updated
                else:
                    current.pop(k, None)
    return len(pivots)

def sum_rows(rows, signed_indices):
    out = Counter()
    for text, sign in signed_indices.items():
        for k, v in rows[int(text)].items():
            out[k] += int(sign) * v
    return {k: v for k, v in out.items() if v}

def main():
    gate = json.loads((P / 'validation_protocol.json').read_text())
    assert gate['status'] == 'FROZEN_BEFORE_D39_F6_VALIDATION'
    assert gate['validator_sha256'] == sha('validate_floor.py')
    for name, digest in gate['files'].items():
        assert sha(name) == digest, name
    audit = json.loads((P / 'audit.json').read_text())
    floor_result = json.loads((P / 'floor.json').read_text())
    source = json.loads((P / 'data/exp11_class_walk_D39_f6.json').read_text())
    assert audit['status'] == 'VERIFIED_D39_F6_MATRIX'
    assert floor_result['status'] == 'VERIFIED_D39_F6_FLOOR_MISMATCH'
    rows = [{int(k): int(v) for k, v in encoded.items() if v}
            for encoded in source['relation_rows']]
    assert len(rows) == len(audit['row_records']) == 48
    floor = {x['column'] for x in audit['points'] if x['endomorphism_conductor'] == 6}
    nonfloor = set(range(64)) - floor
    assert len(floor) == 24 and len(nonfloor) == 40
    cycles = []
    for cert in floor_result['degree2_certificates']:
        replay = sum_rows(rows, cert['signed_rows'])
        claimed = {int(k): int(v) for k, v in cert['signed_floor_columns'].items()}
        assert replay == claimed and set(replay) <= floor
        assert len(cert['signed_rows']) == len(replay) == 12
        cycles.append(replay)
    pairs = []
    for item in floor_result['degree3_pair_records']:
        assert item['status'] == 'EXACT_FLOOR_DIFFERENCE'
        a, b = item['rows']
        replay = {k: rows[a].get(k, 0) - rows[b].get(k, 0)
                  for k in rows[a].keys() | rows[b].keys()}
        replay = {k: v for k, v in replay.items() if v}
        claimed = {int(k): int(v) for k, v in item['signed_columns'].items()}
        assert replay == claimed and set(replay) <= floor
        assert len(replay) == 6 and set(replay.values()) <= {-1, 1}
        pairs.append(replay)
    assert len(cycles) == 2 and len(pairs) == 4
    assert Counter(k for row in cycles for k in row) == Counter({k: 1 for k in floor})
    assert Counter(k for row in pairs for k in row) == Counter({k: 1 for k in floor})
    witnesses = []
    for cycle_index, cycle in enumerate(cycles):
        overlaps = []
        for pair_index, pair in enumerate(pairs):
            shared = sorted(set(cycle) & set(pair))
            if not shared:
                continue
            ratios = {k: cycle[k] * pair[k] for k in shared}
            positive = next((k for k in shared if ratios[k] == 1), None)
            negative = next((k for k in shared if ratios[k] == -1), None)
            assert positive is not None and negative is not None
            overlaps.append({'pair': pair_index, 'columns': [positive, negative],
                             'ratios': [1, -1]})
        assert len(overlaps) == 2
        witnesses.append({'cycle': cycle_index, 'overlaps': overlaps})
    # Disjoint pair supports force a separate scalar on each pair support.
    # Opposite ratios at two columns force that scalar and the cycle scalar
    # both to zero. The two cycle supports are disjoint, so all six vectors
    # are linearly independent over QQ.
    ranks = {}
    for modulus in (None, 23, 1000000007, 2147483647):
        key = 'QQ' if modulus is None else str(modulus)
        ranks[key] = {}
        for subset in ((2,), (3,), (2, 3)):
            selected = [row for row, meta in zip(rows, audit['row_records'])
                        if meta['degree'] in subset]
            projected = [{k: v for k, v in row.items() if k in nonfloor}
                         for row in selected]
            label = '+'.join(map(str, subset))
            ranks[key][label] = [rank(selected, 64, modulus), rank(projected, 64, modulus)]
        assert ranks[key] == {'2': [32, 30], '3': [16, 12], '2+3': [40, 34]}
        assert ranks[key] == floor_result['ranks'][key]
    output = {'status': 'EXACT_D39_F6_SIX_FLOOR_DIRECTIONS',
              'validation_protocol_sha256': sha('validation_protocol.json'),
              'source_sha256': sha('data/exp11_class_walk_D39_f6.json'),
              'audit_sha256': sha('audit.json'), 'floor_sha256': sha('floor.json'),
              'validator_sha256': sha('validate_floor.py'),
              'exact_integer_cycles': len(cycles), 'exact_integer_pairs': len(pairs),
              'ratio_contradiction_witnesses': witnesses,
              'independent_floor_directions': 6,
              'full_rank': 40, 'nonfloor_projection_rank': 34,
              'ranks': ranks, 'candidate_id': None, 'timing_claim': None}
    (P / 'validation.json').write_text(json.dumps(output, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': output['status'], 'witnesses': witnesses,
                      'ranks_QQ': ranks['QQ']}))

if __name__ == '__main__':
    main()
