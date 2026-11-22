"""Independent Sage check of inverse-output product and mask reconstruction."""
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing, matrix, vector

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
STATES = ROOT / 'n41_n131_fivepair_w9_w29_20261017/n41_states.json'
R = PolynomialRing(GF(2), 'u')
u = R.gen()
F = GF(2**41, name='u', modulus=u**41 + u**3 + 1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dec(word):
    return F(R([(int(word) >> bit) & 1 for bit in range(41)]))


def vec(value):
    return vector(GF(2), [int(value.polynomial()[i]) for i in range(41)])


def halftrace(value):
    return sum((value**(1 << (2*i)) for i in range(21)), F.zero())


seed = dec(56 << 1)
h = halftrace(seed)
assert h*h + h == seed
H = h*h
C = 1 + H
bits = [i for i in range(9) if i != 5]
base = [dec(1 << (i+1)) for i in bits]
PB = [a*a + seed*a for a in base]
M = matrix(GF(2), 41, len(bits), lambda i, j: vec(PB[j])[i])
assert M.rank() == 8
states = json.loads(STATES.read_text())
assert states['usable_edges'] == 71 and len(states['states'][0]) == 284
root_values = defaultdict(set)
for row in states['states'][0]:
    x, y = map(dec, row['point'])
    P = E(x, y)
    assert P != E(0) and x != 0
    z = 1/x
    mask = row['masks'][0]
    a = dec(mask << 1)
    p = a*a + seed*a
    assert C*z*z + p*z + H == 0
    assert C*z + H/z == p
    code = sum(((mask >> bit) & 1) << j for j, bit in enumerate(bits))
    recovered = M.solve_right(vec(C*z + H/z))
    assert sum(int(recovered[j]) << j for j in range(len(bits))) == code
    root_values[mask].add(z)
assert len(root_values) == 71
assert all(len(values) == 2 for values in root_values.values())
result = {'status': 'PASS_INDEPENDENT_N41_INVERSE_OUTPUT_ALL_SIGN_STATES',
          'field_modulus': 'u^41+u^3+1', 'curve': 'y^2+xy=x^3+1',
          'source_seed_mask': 56, 'product_map_rank': M.rank(),
          'checked_signed_states': len(states['states'][0]),
          'checked_canonical_edges': len(root_values),
          'roots_per_edge': 2,
          'source_sha256': {'script': sha(Path(__file__)), 'states': sha(STATES),
                            'runtime': sha(HERE / 'sage_runtime_info.json')}}
with (HERE / 'audit_n41_result.json').open('x') as out:
    json.dump(result, out, sort_keys=True, indent=2)
    out.write('\n')
print(json.dumps(result, sort_keys=True))
