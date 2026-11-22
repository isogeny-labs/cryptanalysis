"""Independent pure-Python replay of the complete W29 exception search."""
import hashlib
import json
from pathlib import Path

here = Path(__file__).resolve().parent
rank = json.loads((here / 'rank_result.json').read_text())
result = json.loads((here / 'enumeration_result.json').read_text())
n = rank['field_degree']
modulus = (1 << n) | sum(1 << tap for tap in rank['field_taps'])
mask = (1 << n) - 1


def mul(a, b):
    out = 0
    while b:
        if b & 1:
            out ^= a
        b >>= 1
        a <<= 1
        if a >> n:
            a ^= modulus
    return out & mask


def xor_combine(code, words):
    out = 0
    while code:
        bit = (code & -code).bit_length() - 1
        out ^= words[bit]
        code &= code - 1
    return out


def echelon(words):
    piv = {}
    for word in words:
        while word:
            bit = word.bit_length() - 1
            if bit not in piv:
                piv[bit] = word
                break
            word ^= piv[bit]
    return piv


def in_span(word, piv):
    while word:
        bit = word.bit_length() - 1
        if bit not in piv:
            return False
        word ^= piv[bit]
    return True


PB = rank['product_basis']
assert n == 131 and rank['field_taps'] == [0, 1, 2, 13]
assert len(PB) == 28 and len(rank['source_basis']) == 28
assert len(echelon(PB)) == 28
assert all(a == mul(x, x) ^ mul(rank['source_seed'], x)
           for a, x in zip(PB, rank['source_basis']))
assert rank['C'] ^ rank['H'] == 1
CH = mul(rank['C'], rank['H'])
assert CH == rank['CH'] == result['CH']
assert PB == result['product_basis']
low = [1] + [mul(b, b) for b in PB]
low += [mul(PB[i], PB[j]) for i in range(28) for j in range(i, 28)]
high = [mul(CH, mul(b, b)) for b in PB]
low_piv = echelon(low)
assert len(low_piv) == rank['low_rank'] == 104
assert len(echelon(low + high)) == rank['combined_rank'] == 115
assert len(echelon(high)) == rank['high_rank'] == 28
kernel = result['kernel_codes']
assert len(kernel) == 17 and len(echelon(kernel)) == 17
assert all(in_span(xor_combine(code, high), low_piv) for code in kernel)

sw = [xor_combine(code, PB) for code in kernel]
hi = [mul(CH, mul(s, s)) for s in sw]
delta = [[mul(b, s) for b in PB] for s in sw]
columns = [mul(b, b) for b in PB]
target = 1
s_code = 0
histogram = {}
solvable = 0
for k in range(1, 1 << 17):
    bit = (k & -k).bit_length() - 1
    s_code ^= kernel[bit]
    target ^= hi[bit]
    columns = [v ^ d for v, d in zip(columns, delta[bit])]
    piv = echelon(columns)
    label = str(len(piv))
    histogram[label] = histogram.get(label, 0) + 1
    solvable += in_span(target, piv)

assert solvable == result['solvable_nonzero_s'] == 0
assert histogram == result['linear_system_rank_histogram']
assert result['nonzero_s_checked'] == (1 << 17) - 1
receipt = {
    'status': 'PASS_INDEPENDENT_PURE_PYTHON_REPLAY',
    'curve_id': result['curve_id'],
    'source_result_sha256': hashlib.sha256((here / 'enumeration_result.json').read_bytes()).hexdigest(),
    'nonzero_s_checked': (1 << 17) - 1,
    'solvable_nonzero_s': solvable,
    'linear_system_rank_histogram': histogram,
}
(here / 'verification_result.json').write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n')
print(json.dumps({key: receipt[key] for key in ('status', 'nonzero_s_checked',
                                                 'solvable_nonzero_s')}, sort_keys=True))
