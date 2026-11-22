"""Derive source-inverse tensor coefficients for pair-output trace."""
import hashlib
import json
import random
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
N41_STATES = ROOT / 'n41_n131_fivepair_w9_w29_20261017/n41_states.json'
N131_CONTROL = ROOT / 'n41_n131_fivepair_w9_w29_20261017/n131_control_3p2.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def setup(n, taps, width, seed_mask):
    R = PolynomialRing(GF(2), 'u')
    u = R.gen()
    F = GF(2**n, name='u', modulus=u**n + sum(u**k for k in taps))
    def dec(word):
        return F(R([(int(word) >> bit) & 1 for bit in range(n)]))
    bits = [bit for bit in range(width) if bit != seed_mask.bit_length() - 1]
    seed = dec(seed_mask << 1)
    assert seed.trace() == 0
    def halftrace(value):
        return sum((value**(1 << (2 * bit)) for bit in range((n + 1) // 2)), F.zero())
    h = halftrace(seed)
    assert h**2 + h == seed
    H = h**2
    C = 1 + H
    assert C
    basis = [dec(1 << (bit + 1)) for bit in bits]
    products = [value**2 + seed * value for value in basis]
    inverse_basis = [dec(1 << bit) for bit in range(n)]
    L = [halftrace(C * H * value**2) for value in inverse_basis]
    coefficients = [(i, j) for i, p in enumerate(products)
                    for j, image in enumerate(L) if int(((p / C) * image).trace())]
    def predict(mask_code, inverse_word):
        return sum((mask_code >> i & 1) & (inverse_word >> j & 1)
                   for i, j in coefficients) & 1
    def by_field(a, q):
        p = a**2 + seed * a
        assert p * q == 1
        u = C * H * q**2
        assert u.trace() == 0
        t = halftrace(u)
        assert t**2 + t == u
        z = (p / C) * t
        assert C * z**2 + p * z + H == 0
        other = z + p / C
        assert C * other**2 + p * other + H == 0
        assert int(z.trace()) == int(other.trace())
        assert int((p / C).trace()) == int(a.trace())
        return int(z.trace())
    return F, dec, bits, seed, coefficients, predict, by_field


F41, dec41, bits41, seed41, coeff41, predict41, field41 = setup(41, [0, 3], 9, 56)
census = json.loads((HERE / 'census_trace_result.json').read_text())
states = json.loads(N41_STATES.read_text())
assert census['n41']['edge_count'] == states['usable_edges'] == 71
for code, expected in census['n41']['code_trace_rows']:
    mask = sum((code >> index & 1) << bit for index, bit in enumerate(bits41))
    a = dec41(mask << 1)
    p = a * (a + seed41)
    q = 1 / p
    qword = sum(int(bit) << index for index, bit in enumerate(q.polynomial().list()))
    assert predict41(code, qword) == expected == field41(a, q)

F131, dec131, bits131, seed131, coeff131, predict131, field131 = setup(
    131, [0, 1, 2, 13], 29, 898618)
control = json.loads(N131_CONTROL.read_text())
for row in control['pairs']:
    mask = row['masks'][0]
    code = sum((mask >> bit & 1) << index for index, bit in enumerate(bits131))
    a = dec131(mask << 1)
    q = dec131(row['source_inverse_product'])
    expected = int(dec131(row['output_reciprocal']).trace())
    assert predict131(code, row['source_inverse_product']) == expected == field131(a, q)

prng = random.Random(20261017)
sample_codes = prng.sample(range(1 << len(bits131)), 512)
sample_survivors = 0
for code in sample_codes:
    mask = sum((code >> index & 1) << bit for index, bit in enumerate(bits131))
    a = dec131(mask << 1)
    b = a + seed131
    if not a or not b or a.trace() or b.trace():
        continue
    if (1 / a).trace() or (1 / b).trace():
        continue
    p = a * b
    q = 1 / p
    qword = sum(int(bit) << index for index, bit in enumerate(q.polynomial().list()))
    assert predict131(code, qword) == field131(a, q)
    sample_survivors += 1
assert sample_survivors > 0

result = {'status': 'PASS_SOURCE_TENSOR_TRACE_COEFFICIENTS',
          'identity': 'Tr(z)=sum coeff[i,j]*mask_bit[i]*source_product_inverse_bit[j] for admissible fixed-seed pairs',
          'n41': {'field_degree': 41, 'source_bits': len(bits41),
                  'inverse_bits': 41, 'coefficients': coeff41,
                  'coefficient_weight': len(coeff41),
                  'checked_eligible_edges': 71},
          'n131': {'field_degree': 131, 'source_bits': len(bits131),
                   'inverse_bits': 131, 'coefficients': coeff131,
                   'coefficient_weight': len(coeff131),
                   'checked_constructed_pairs': 5,
                   'sample_seed': 20261017,
                   'sampled_distinct_canonical_codes': len(sample_codes),
                   'sample_eligible_pairs': sample_survivors},
          'source_sha256': {path.name: sha(path) for path in
                            (Path(__file__), N41_STATES, N131_CONTROL,
                             HERE / 'census_trace_result.json',
                             HERE / 'sage_runtime_info.json')}}
with (HERE / 'source_trace_coeff_result.json').open('x') as out:
    json.dump(result, out, sort_keys=True, indent=2)
    out.write('\n')
print(json.dumps({'status': result['status'],
                  'n41_coefficient_weight': len(coeff41),
                  'n131_coefficient_weight': len(coeff131),
                  'n131_sample_eligible_pairs': sample_survivors}))
