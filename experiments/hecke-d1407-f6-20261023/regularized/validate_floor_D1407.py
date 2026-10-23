"""Independent integer and rational replay of the D1407/f6 floor result."""
from collections import Counter
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
import json

P = Path(__file__).resolve().parent
digest = lambda name: sha256((P / name).read_bytes()).hexdigest()

def rank(rows, modulus=None):
    pivots = {}
    for source in rows:
        row = {int(k): (Fraction(v) if modulus is None else int(v) % modulus)
               for k, v in source.items() if v}
        while row:
            col = min(row)
            if col not in pivots:
                inv = 1 / row[col] if modulus is None else pow(row[col], -1, modulus)
                pivots[col] = {k: (v * inv if modulus is None else v * inv % modulus)
                               for k, v in row.items()}
                break
            scale = row[col]
            for k, v in pivots[col].items():
                val = row.get(k, 0) - scale * v
                if modulus is not None: val %= modulus
                if val: row[k] = val
                else: row.pop(k, None)
    return len(pivots)

def main():
    gate = json.loads((P / 'validation_protocol_D1407.json').read_text())
    assert gate['status'] == 'FROZEN_BEFORE_D1407_F6_VALIDATION'
    assert gate['validator_sha256'] == digest('validate_floor_D1407.py')
    assert all(digest(name) == value for name, value in gate['files'].items())
    source = json.loads((P / 'data/exp11_class_walk_D1407_f6.json').read_text())
    audit = json.loads((P / 'audit_D1407.json').read_text())
    floor_result = json.loads((P / 'floor_D1407.json').read_text())
    graph = json.loads((P / 'graph_D1407.json').read_text())
    rows = [{int(k): int(v) for k, v in row.items() if v} for row in source['relation_rows']]
    floor = {x['column'] for x in audit['points'] if x['endomorphism_conductor'] == 6}
    nonfloor = set(range(384)) - floor
    assert len(rows) == 288 and len(floor) == 144 and len(nonfloor) == 240
    cycles = []
    for cert in floor_result['degree2_certificates']:
        row = Counter()
        for index, sign in cert['signed_rows'].items():
            for col, value in rows[int(index)].items(): row[col] += int(sign) * value
        replay = {k: v for k, v in row.items() if v}
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
    assert len(cycles) == 12 and len(pairs) == 24
    assert Counter(k for row in cycles for k in row) == Counter({k: 1 for k in floor})
    assert Counter(k for row in pairs for k in row) == Counter({k: 1 for k in floor})
    touch = [sum(bool(set(pair) & set(cycle)) for cycle in cycles) for pair in pairs]
    assert touch == [6] * 24
    assert graph['six_distinct_cycles_per_pair'] and graph['all_match']
    assert len(graph['components']) == graph['balanced_component_count'] == 2
    for component in graph['components']:
        assert len(component['cycles']) == 6 and len(component['pairs']) == 12
        values = component['normalized_assignment']
        assert values is not None
        lhs, rhs = Counter(), Counter()
        for index in component['cycles']:
            for col, value in cycles[index].items(): lhs[col] += Fraction(values[f'c{index}']) * value
        for index in component['pairs']:
            for col, value in pairs[index].items(): rhs[col] += Fraction(values[f'p{index}']) * value
        assert lhs == rhs
    assert rank(cycles) == 12 and rank(pairs) == 24 and rank(cycles + pairs) == 34
    ranks = {}
    for modulus in (None, 23, 1000000007, 2147483647):
        key = 'QQ' if modulus is None else str(modulus)
        ranks[key] = {}
        for subset in ((2,), (3,), (2, 3)):
            chosen = [row for row, info in zip(rows, audit['row_records']) if info['degree'] in subset]
            projected = [{k: v for k, v in row.items() if k in nonfloor} for row in chosen]
            ranks[key]['+'.join(map(str, subset))] = [rank(chosen, modulus), rank(projected, modulus)]
        assert ranks[key] == {'2': [192, 180], '3': [96, 72], '2+3': [240, 206]}
        assert ranks[key] == floor_result['ranks'][key]
    result = {'status': 'EXACT_D1407_F6_SIX_CYCLE_HOLDOUT',
              'validation_protocol_sha256': digest('validation_protocol_D1407.json'),
              'source_sha256': digest('data/exp11_class_walk_D1407_f6.json'),
              'audit_sha256': digest('audit_D1407.json'), 'floor_sha256': digest('floor_D1407.json'),
              'graph_sha256': digest('graph_D1407.json'), 'validator_sha256': digest('validate_floor_D1407.py'),
              'cycle_count': 12, 'pair_count': 24, 'touch_counts': touch,
              'balanced_components': 2, 'floor_direction_rank': 34, 'ranks': ranks,
              'candidate_id': None, 'timing_claim': None}
    (P / 'validation_D1407.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'status': result['status'], 'floor_direction_rank': 34, 'ranks': ranks['QQ']}))

if __name__ == '__main__': main()
