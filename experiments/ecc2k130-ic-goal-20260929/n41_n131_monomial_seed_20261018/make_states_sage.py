"""Enumerate exact N41 W9 signed pair source for monomial-halftrace seed."""
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


cfg = json.loads((HERE / 'source_protocol.json').read_text())
assert cfg['status'] == 'FROZEN_BEFORE_SOURCE'
for name, entry in cfg['sources'].items():
    assert sha(entry['path']) == entry['sha256'], name
R = PolynomialRing(GF(2), 't')
t = R.gen()
F = GF(2**41, name='t', modulus=t**41 + t**3 + 1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])
seed = cfg['seed_mask']
assert seed == 36
seed_field = F.from_integer(seed << 1)
assert seed_field == F(t**6 + t**3)


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


h = halftrace(seed_field)
assert h == F(t**3) and h**2 == F(t**6)
target_xy = cfg['raw_target']
assert E(*(F.from_integer(v) for v in target_xy)) != E(0)
point_by_mask = {}
for mask in range(1, 1 << 9):
    w = F.from_integer(mask << 1)
    if w.trace() or (1 / w).trace():
        continue
    h_mask = halftrace(w)
    if not h_mask:
        continue
    x = 1 + 1 / h_mask
    point = E.lift_x(x, all=True)[0]
    assert point[0] == x and x
    point_by_mask[mask] = point
columns = {mask:column(point) for mask,point in point_by_mask.items()}
labels = {value:index for index,value in enumerate(sorted(set(columns.values())))}
edges = []
for a in range(1, 1 << 9):
    b = a ^ seed
    if a >= b or a not in point_by_mask or b not in point_by_mask:
        continue
    ca, cb = labels[columns[a]], labels[columns[b]]
    if ca != cb:
        edges.append((a,b,ca,cb))
rows = []
for slot, rotation in enumerate(cfg['rotations']):
    slot_rows = []
    for a,b,ca,cb in edges:
        for sa in range(2):
            for sb in range(2):
                left = -point_by_mask[a] if sa else point_by_mask[a]
                right = -point_by_mask[b] if sb else point_by_mask[b]
                summed = left + right
                assert summed != E(0)
                rotated = E(summed[0]**(1 << rotation), summed[1]**(1 << rotation))
                slot_rows.append({'masks':[a,b], 'signs':[sa,sb],
                                  'columns':[ca,cb], 'point':xy(rotated)})
    rows.append(slot_rows)
assert all(len(slot)==len(rows[0]) for slot in rows)
result = {'status':'COMPLETE_MONOMIAL_SEED_SOURCE',
          'curve_id':cfg['curve_id'],'seed_mask':seed,
          'halftrace':enc(h),'H':enc(h*h),'C':enc(1+h*h),
          'eligible_mask_count':len(point_by_mask),
          'usable_edges':len(edges),'folded_column_count':len(labels),
          'states_per_slot':len(rows[0]),'rotations':cfg['rotations'],
          'raw_target':target_xy,'states':rows,
          'source_protocol_sha256':sha(HERE/'source_protocol.json'),
          'generator_sha256':sha(Path(__file__))}
(HERE/'states.json').write_text(json.dumps(result,separators=(',',':'),sort_keys=True)+'\n')
print(json.dumps({k:result[k] for k in ('status','seed_mask','halftrace','H','C','eligible_mask_count','usable_edges','folded_column_count','states_per_slot')}),flush=True)
