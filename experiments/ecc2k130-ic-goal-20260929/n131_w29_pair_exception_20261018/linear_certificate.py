"""Produce an explicit GF(2)-linear obstruction to the W29 exception."""
import hashlib
import json
from pathlib import Path

here = Path(__file__).resolve().parent
rank = json.loads((here / 'rank_result.json').read_text())
n = rank['field_degree']
modulus = (1 << n) | sum(1 << tap for tap in rank['field_taps'])


def mul(a, b):
    out = 0
    while b:
        if b & 1:
            out ^= a
        b >>= 1
        a <<= 1
        if a >> n:
            a ^= modulus
    return out


def basis_size(words):
    pivots = {}
    for word in words:
        while word:
            bit = word.bit_length() - 1
            if bit not in pivots:
                pivots[bit] = word
                break
            word ^= pivots[bit]
    return len(pivots)


PB = rank['product_basis']
CH = mul(rank['C'], rank['H'])
assert CH == rank['CH']
squares = [mul(b, b) for b in PB]
pair_products = [mul(PB[i], PB[j]) for i in range(28) for j in range(i, 28)]
scaled_squares = [mul(CH, value) for value in squares]
generators = squares + pair_products + scaled_squares
span_rank = basis_size(generators)
augmented_rank = basis_size(generators + [1])
assert span_rank == 114 and augmented_rank == 115

# Solve dot(mask, generator)=0 with mask bit 0 fixed to 1.
rows = {}
for word in generators:
    coeff = word >> 1
    rhs = word & 1
    while coeff:
        bit = coeff.bit_length() - 1
        if bit not in rows:
            rows[bit] = (coeff, rhs)
            break
        previous, previous_rhs = rows[bit]
        coeff ^= previous
        rhs ^= previous_rhs
    else:
        assert rhs == 0
reduced_mask = 0
for bit in sorted(rows):
    coeff, rhs = rows[bit]
    value = rhs ^ ((coeff & reduced_mask).bit_count() & 1)
    reduced_mask |= value << bit
mask = 1 | (reduced_mask << 1)
assert mask < (1 << n)
assert all((mask & word).bit_count() % 2 == 0 for word in generators)
assert (mask & 1).bit_count() == 1

receipt = {
    'status': 'EXACT_LINEAR_SEPARATION_CERTIFICATE',
    'candidate_id': None,
    'curve_id': rank['curve_id'],
    'field_degree': n,
    'field_taps': rank['field_taps'],
    'source_seed': rank['source_seed'],
    'source_basis': rank['source_basis'],
    'product_basis': PB,
    'C': rank['C'],
    'H': rank['H'],
    'CH': CH,
    'square_generators': len(squares),
    'pair_product_generators': len(pair_products),
    'scaled_square_generators': len(scaled_squares),
    'generator_span_rank': span_rank,
    'augmented_span_rank': augmented_rank,
    'parity_mask': mask,
    'all_generator_parities_zero': True,
    'unit_parity_one': True,
    'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
}
(here / 'linear_certificate.json').write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n')
print(json.dumps({key: receipt[key] for key in ('generator_span_rank',
                                               'augmented_span_rank', 'parity_mask')},
                 sort_keys=True))
