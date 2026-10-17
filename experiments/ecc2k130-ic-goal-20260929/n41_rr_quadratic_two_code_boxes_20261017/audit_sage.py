"""Independent group-law audit of every frozen source box."""
import hashlib
import itertools
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'n41_sixpair_shared_target_20261017/join_input.tsv'
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
p = json.loads((HERE / 'protocol.json').read_text())
assert sha(SOURCE) == p['source_sha256']['source']
R = PolynomialRing(GF(2), 't')
t = R.gen()
F = GF(2**41, name='t', modulus=t**41+t**3+1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])
def dec(v):
    return F(R([(int(v) >> i) & 1 for i in range(41)]))
rows = {}
for line in SOURCE.read_text().splitlines()[1:]:
    v = line.split()
    rows[int(v[1]), int(v[2])] = E(dec(v[9]), dec(v[10]))
assert len(rows) == 960
Q = E(*(dec(v) for v in p['target']))
w, e = p['witness_codes'], p['extra_codes']
boxes = [('witness_single', [[x] for x in w]),
         ('disjoint_single', [[x] for x in e]),
         ('witness_double', [[w[i], e[i]] for i in range(6)]),
         ('shifted_double', [[p['replacement_first_code'], e[0]]] +
          [[w[i], e[i]] for i in range(1, 6)])]
output = []
for name, codes in boxes:
    ids = [tuple(4*c+s for c in group for s in range(4)) for group in codes]
    left = {}
    for key in itertools.product(*ids[:3]):
        point = sum((rows[i, key[i]] for i in range(3)), E(0))
        left.setdefault(point, []).append(key)
    hits = []
    for key in itertools.product(*ids[3:]):
        need = Q - sum((rows[i+3, key[i]] for i in range(3)), E(0))
        for left_key in left.get(need, ()):
            hits.append(list(left_key + key))
    output.append({'name': name, 'relation_count': len(hits), 'hits': hits,
                   'left_keys': sum(map(len, left.values())),
                   'right_keys': len(ids[3])*len(ids[4])*len(ids[5])})
    print(name, len(hits), flush=True)
assert [12, 122, 116, 47, 128, 34] in output[0]['hits']
assert [12, 122, 116, 47, 128, 34] in output[2]['hits']
record = {'status': 'PASS_EXACT_GROUP_BOX_AUDIT', 'rows': output,
          'protocol_sha256': sha(HERE / 'protocol.json'),
          'source_sha256': sha(SOURCE)}
with (HERE / 'audit.json').open('x') as f:
    json.dump(record, f, indent=2, sort_keys=True)
    f.write('\n')
