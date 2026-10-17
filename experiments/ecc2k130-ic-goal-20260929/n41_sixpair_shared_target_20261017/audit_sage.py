"""Independent Sage replay of the constructed six-pair circuit control."""
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
protocol = json.loads((HERE / 'protocol.json').read_text())
for path, digest in protocol['sources'].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest, path

geometry = json.loads((ROOT / 'n41_w8_fixed_sum_table_20261009/geometry.json').read_text())
source_path = ROOT / 'n41_w7_entropy_cubic_20261011/w8/geometry.json'
baseline = json.loads((ROOT / 'n41_w8_selector_elimination_control_20261013/audit_protocol_v2.json').read_text())
assert hashlib.sha256(source_path.read_bytes()).hexdigest() == baseline['sources'][str(source_path)]
source = json.loads(source_path.read_text())
ring = PolynomialRing(GF(2), 't')
t = ring.gen()
field = GF(2**41, name='t', modulus=t**41 + t**3 + 1)
curve = EllipticCurve(field, [1, 0, 0, 0, 1])

def dec(word):
    return field(ring([(int(word) >> i) & 1 for i in range(41)]))

def enc(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))

def xy(point):
    return [enc(point[0]), enc(point[1])]

def trace(value):
    result = field(0)
    for _ in range(41):
        result += value
        value = value**2
    return result

rows = {row['mask']: row for row in source['rows']}
nodes = []
columns = []
pairs = []
for slot, state in enumerate(geometry['positive_control']['states'][:6]):
    points = []
    for mask, sign in ((state['a'], state['sign_a']), (state['b'], state['sign_b'])):
        raw = curve(*map(dec, rows[mask]['raw_point']))
        signed = -raw if sign else raw
        rotation = geometry['rotations'][slot]
        points.append(curve(signed[0] ** (1 << rotation), signed[1] ** (1 << rotation)))
        columns.append(rows[mask]['column'])
    point = points[0] + points[1]
    assert point != curve(0) and point[0] != 0
    assert xy(point) == state['raw_sum']
    assert enc(1 / (point[0] + 1)) == state['z']
    nodes.append(point)
    pairs.append({'slot': slot, 'masks': [state['a'], state['b']], 'raw_sum': xy(point)})

assert len(columns) == len(set(columns)) == 12
assert protocol['topology'] == [[0,1,6],[2,3,7],[4,5,8],[6,7,9],[9,8,10]]
links = []
for left, right, output in protocol['topology']:
    point = nodes[left] + nodes[right]
    assert point != curve(0) and point[0] != 0
    assert output == len(nodes)
    nodes.append(point)
    u, v, w = (1 / nodes[index][0] for index in (left, right, output))
    total = u + v + w
    assert trace(total) == 0
    links.append({'inputs': [left,right], 'output': output, 'point': xy(point), 'reciprocal_x': enc(w)})

assert xy(nodes[10]) == protocol['control_raw_point']
assert xy(4 * nodes[10]) == protocol['control_subgroup_point']
assert protocol['public_subgroup_point'] == geometry['positive_control']['subgroup_target']
result = {'status': 'PASS_INDEPENDENT_N41_SIXPAIR_REPLAY',
          'protocol_sha256': hashlib.sha256((HERE/'protocol.json').read_bytes()).hexdigest(),
          'source_geometry_sha256': hashlib.sha256(source_path.read_bytes()).hexdigest(),
          'pairs': pairs, 'links': links, 'distinct_columns': len(set(columns)),
          'control_raw_point': xy(nodes[10]), 'control_subgroup_point': xy(4*nodes[10])}
with (HERE/'audit_result.json').open('x') as out:
    json.dump(result, out, sort_keys=True, indent=2)
    out.write('\n')
print(result['status'], flush=True)
