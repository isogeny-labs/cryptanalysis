"""Independent curve-group bridge for the sampled N131 source codes."""
import hashlib
import json
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


start = time.monotonic()
producer = json.loads((HERE / 'n131_result.json').read_text())
assert producer['status'] == 'PASS_SAMPLED_N131_DEGREE_TWO_EXCLUSION'
R = PolynomialRing(GF(2), 'u')
u = R.gen()
F = GF(2**131, name='u', modulus=u**131 + u**13 + u**2 + u + 1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])


def dec(word):
    return F(R([(int(word) >> i) & 1 for i in range(131)]))


def enc(value):
    return sum(int(c) << i for i, c in enumerate(value.polynomial().list()))


def halftrace(value):
    original = value
    total = F.zero()
    for _ in range(66):
        total += value
        value = value**4
    assert total**2 + total == original
    return total


bits = [i for i in range(29) if i != (898618).bit_length() - 1]
seed = 898618 << 1
checked = 0
for code, recorded_root in zip(producer['codes'], producer['roots']):
    mask = sum(1 << bit for index, bit in enumerate(bits) if code >> index & 1)
    a, b = dec(mask << 1), dec((mask << 1) ^ seed)
    assert a and b and a.trace() == 0 and b.trace() == 0
    ha, hb = halftrace(a), halftrace(b)
    assert ha and hb
    xa, xb = 1 + 1/ha, 1 + 1/hb
    va = halftrace(xa + 1/(xa**2))
    vb = halftrace(xb + 1/(xb**2))
    point_a = E(xa, xa*va)
    point_b = E(xb, xb*vb)
    sums = [point_a + point_b, point_a - point_b]
    assert all(point != E(0) and point[0] for point in sums)
    roots = {enc(1/point[0]) for point in sums}
    assert len(roots) == 2 and recorded_root in roots
    checked += 1
result = {
    'status': 'PASS_INDEPENDENT_N131_SOURCE_GROUP_BRIDGE',
    'sampled_source_codes': checked,
    'pair_output_roots_checked': 2*checked,
    'elapsed_seconds': time.monotonic() - start,
    'source_sha256': {'script': sha(Path(__file__)),
                      'producer': sha(HERE / 'n131_result.json'),
                      'runtime': sha(HERE / 'sage_runtime_info.json')},
}
(HERE / 'n131_group_audit_result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps(result, sort_keys=True))
