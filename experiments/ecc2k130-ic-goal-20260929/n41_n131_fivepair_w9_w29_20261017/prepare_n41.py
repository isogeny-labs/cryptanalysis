"""Construct exact W9 fixed-seed signed-pair states for the N41 public point."""
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / 'n41_w8_fixed_sum_table_20261009/geometry.json'
F2 = GF(2)
R = PolynomialRing(F2, 't')
t = R.gen()
F = GF(2**41, name='t', modulus=t**41 + t**3 + 1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])
WIDTH = 9
SEED = 56
ROTATIONS = [0, 6, 12, 18, 24]


def dec(word):
    return F(R([(word >> i) & 1 for i in range(41)]))


def enc(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))


def xy(point):
    return [enc(point[0]), enc(point[1])]


def halftrace(value):
    result = F.zero()
    current = value
    for _ in range(21):
        result += current
        current = current**4
    assert result**2 + result == value
    return result


def column(point):
    current = point[0]
    values = []
    for _ in range(41):
        values.append(enc(current))
        current = current**2
    return min(values)


def main():
    source = json.loads(SOURCE.read_text())
    target = source['positive_control']['raw_target']
    assert E(*map(dec, target)) != E(0)
    point_by_mask = {}
    for mask in range(1, 1 << WIDTH):
        w = dec(mask << 1)
        if w.trace() or (1 / w).trace():
            continue
        h = halftrace(w)
        if not h:
            continue
        x = 1 + 1 / h
        point = E.lift_x(x, all=True)[0]
        assert point[0] == x and x and 1 / (x + 1) == h
        point_by_mask[mask] = point
    columns = {mask: column(point) for mask, point in point_by_mask.items()}
    labels = {value: index for index, value in enumerate(sorted(set(columns.values())))}
    edges = []
    for a in range(1, 1 << WIDTH):
        b = a ^ SEED
        if a >= b or a not in point_by_mask or b not in point_by_mask:
            continue
        ca, cb = labels[columns[a]], labels[columns[b]]
        if ca == cb:
            continue
        edges.append((a, b, ca, cb))
    rows = []
    for slot, rotation in enumerate(ROTATIONS):
        slot_rows = []
        for a, b, ca, cb in edges:
            for sa in range(2):
                for sb in range(2):
                    p = (-point_by_mask[a] if sa else point_by_mask[a]) + \
                        (-point_by_mask[b] if sb else point_by_mask[b])
                    assert p != E(0)
                    rotated = E(p[0]**(1 << rotation), p[1]**(1 << rotation))
                    slot_rows.append({'masks': [a, b], 'signs': [sa, sb],
                                      'columns': [ca, cb], 'point': xy(rotated)})
        rows.append(slot_rows)
    assert len({len(row) for row in rows}) == 1
    data = {'status': 'COMPLETE_SOURCE', 'curve_id': 'EC1N41Ckb1h7d5e80d3c4d0',
            'field_modulus_taps': [0, 3, 41], 'width': WIDTH, 'seed': SEED,
            'rotations': ROTATIONS, 'target_raw_point': target,
            'eligible_mask_count': len(point_by_mask), 'usable_edges': len(edges),
            'folded_column_count': len(labels), 'states_per_slot': len(rows[0]),
            'states': rows,
            'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (HERE / 'n41_states.json').write_text(json.dumps(data, sort_keys=True) + '\n')
    print(json.dumps({key: data[key] for key in
                      ('status', 'eligible_mask_count', 'usable_edges',
                       'folded_column_count', 'states_per_slot')}))


if __name__ == '__main__':
    main()
