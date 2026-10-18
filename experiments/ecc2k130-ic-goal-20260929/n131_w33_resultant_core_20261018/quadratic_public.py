"""Fixed-first-code Boolean quadratic probe on the frozen public point."""
import hashlib
import json
import sys
import time
from pathlib import Path

from sage.all import BooleanPolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / 'n131_w23_sixpair_shared_circuit_20261017'))
import circuit as design


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


cfg = json.loads((HERE / 'public_quadratic_protocol.json').read_text())
for path, expected in cfg['sources'].items():
    assert sha(path) == expected, path
assert cfg['first_code'] == 3
coeff = json.loads((ROOT / 'n131_w33_freecode_resultant_20261018' / 'coefficients.json').read_text())
assert coeff['source_product_rank'] == 32
F = design.F
seed = design.SEED
seed_mask = seed >> 1
bits = [i for i in range(33) if i != seed_mask.bit_length()-1]
base = [1 << (i+1) for i in bits]
pb = [F.square(a) ^ F.mul(seed, a) for a in base]
qb = [F.frob(a, 18) for a in pb]
first = coeff['positive_source_checks'][0]['unrotated_product']
assert first == pb[0] ^ pb[1]
row = coeff['rows'][1]
terms = {(i, j): c for i, j, c in row['terms']}
Aj = {j: 0 for j in range(5)}
for (i, j), c in terms.items():
    power = 1
    for _ in range(i):
        power = F.mul(power, first)
    Aj[j] ^= F.mul(c, power)

linear = []
for b in qb:
    b2 = F.square(b)
    b4 = F.square(b2)
    b3 = F.mul(b, b2)
    linear.append(F.mul(Aj[1], b) ^ F.mul(Aj[2], b2) ^
                  F.mul(Aj[3], b3) ^ F.mul(Aj[4], b4))
quadratic = []
for i in range(32):
    bi2 = F.square(qb[i])
    for j in range(i+1, 32):
        bj2 = F.square(qb[j])
        quadratic.append((i, j, F.mul(Aj[3],
                                      F.mul(bi2, qb[j]) ^ F.mul(qb[i], bj2))))
assert len(quadratic) == 496

def evaluate(code):
    value = Aj[0]
    for i, c in enumerate(linear):
        if code >> i & 1:
            value ^= c
    for i, j, c in quadratic:
        if code >> i & 1 and code >> j & 1:
            value ^= c
    return value


R = BooleanPolynomialRing(32, 'x', order='lex')
x = R.gens()
equations = []
for bit in range(131):
    f = R(Aj[0] >> bit & 1)
    for i, c in enumerate(linear):
        if c >> bit & 1:
            f += x[i]
    for i, j, c in quadratic:
        if c >> bit & 1:
            f += x[i]*x[j]
    equations.append(f)
started = time.monotonic()
print(json.dumps({'event': 'GB_START', 'equations': len(equations),
                  'variables': 32, 'quadratic_monomials': len(quadratic),
                  'first_code': cfg['first_code'],
                  'target_point': row['point']}), flush=True)
gb = list(R.ideal(equations).groebner_basis())
elapsed = time.monotonic()-started
pins = {}
for j in range(32):
    if x[j] in gb:
        pins[j] = 0
    elif x[j]+1 in gb:
        pins[j] = 1
recovered = sum(value << j for j, value in pins.items()) if len(pins) == 32 else None
assert recovered is None or evaluate(recovered) == 0
result = {'status': 'GB_COMPLETE', 'candidate_id': None,
          'curve_id': cfg['curve_id'], 'equations': 131, 'variables': 32,
          'gb_polynomials': len(gb), 'pinned_bits': len(pins),
          'unit_ideal_reported': R.one() in gb,
          'recovered_second_code': recovered,
          'first_code': cfg['first_code'], 'target_point': row['point'],
          'wall_seconds_gb': elapsed,
          'protocol_sha256': sha(HERE / 'public_quadratic_protocol.json')}
(HERE / 'public_quadratic_result.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
print(json.dumps(result, sort_keys=True), flush=True)
