"""Pure-integer GF(2^131) replay of the frozen positive resultant root."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
MASK = (1 << 131) - 1
REDUCTION = (1 << 13) | (1 << 2) | (1 << 1) | 1
SEED_MASK = 898618
SEED = SEED_MASK << 1


def mul(a, b):
    assert 0 <= a <= MASK and 0 <= b <= MASK
    out = 0
    while b:
        if b & 1:
            out ^= a
        b >>= 1
        a <<= 1
        if a >> 131:
            a = (a & MASK) ^ REDUCTION
    return out


def frob(a, power):
    for _ in range(power):
        a = mul(a, a)
    return a


def encoded_parameter(code):
    bits = [bit for bit in range(33) if bit != SEED_MASK.bit_length() - 1]
    assert len(bits) == 32 and 0 <= code < 1 << 32
    return sum(1 << (bit + 1) for j, bit in enumerate(bits) if code >> j & 1)


def product(code, rotation):
    a = encoded_parameter(code)
    return frob(mul(a, a ^ SEED), rotation)


def evaluate(terms, p, q):
    pp = [1, p]
    qq = [1, q]
    for _ in range(3):
        pp.append(mul(pp[-1], p))
        qq.append(mul(qq[-1], q))
    out = 0
    for i, j, coefficient in terms:
        out ^= mul(coefficient, mul(pp[i], qq[j]))
    return out


source = json.loads((ROOT / 'n131_w33_freecode_resultant_20261018' / 'coefficients.json').read_text())
positive = source['positive_source_checks']
assert [r['code'] for r in positive] == [3, 16722]
assert source['rotations'] == [0, 18]
for check in positive:
    assert encoded_parameter(check['code']) == check['parameter']
    assert mul(check['parameter'], check['parameter'] ^ SEED) == check['unrotated_product']
p = product(positive[0]['code'], 0)
q = product(positive[1]['code'], 18)
assert [p, q] == source['rows'][0]['positive_pair_products']
assert evaluate(source['rows'][0]['terms'], p, q) == 0
assert source['rows'][0]['symbolic_remainder_verified'] is True
build = json.loads((HERE / 'build_0_result.json').read_text())
assert build['status'] == 'PASS_N131_W33_RESULTANT_FILTER_CIRCUIT'
assert build['positive_assignment_check'] == {
    'clauses': build['counts']['clauses'], 'native_xor_rows': build['counts']['xor_rows']}
assert build['counts']['and_gates'] == 6841
assert build['counts']['variables'] == 11868
out = {'status': 'PASS_N131_W33_INDEPENDENT_POSITIVE_ROOT',
       'candidate_id': None, 'source_codes': [3, 16722],
       'rotated_products': [p, q], 'resultant_value': 0,
       'coefficients_sha256': hashlib.sha256((ROOT / 'n131_w33_freecode_resultant_20261018' / 'coefficients.json').read_bytes()).hexdigest(),
       'formula_sha256': build['formula_sha256']}
(HERE / 'independent_audit_result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
print(json.dumps(out, sort_keys=True))
