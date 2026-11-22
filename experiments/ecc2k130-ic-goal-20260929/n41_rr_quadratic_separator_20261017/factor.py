"""Exact symplectic factorization of the quadratic RR certificate."""
import hashlib
import json
import time
from pathlib import Path

D = Path(__file__).resolve().parent
N = 41
WIDTH = N + N * (N - 1) // 2


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parity(value):
    return value.bit_count() & 1


def quadratic_rows(coeff):
    rows = [0] * N
    index = N
    for i in range(N):
        for j in range(i + 1, N):
            if coeff >> index & 1:
                rows[i] |= 1 << j
                rows[j] |= 1 << i
            index += 1
    assert index == WIDTH
    return rows


def monomial_eval(coeff, value):
    total = parity(coeff & value)
    index = N
    for i in range(N):
        for j in range(i + 1, N):
            if (coeff >> index & 1) and (value >> i & 1) and (value >> j & 1):
                total ^= 1
            index += 1
    return total


def polar(rows, left, right):
    result = 0
    while left:
        low = left & -left
        result ^= parity(rows[low.bit_length() - 1] & right)
        left ^= low
    return result


def inverse_basis(columns):
    assert len(columns) == N
    rows = [sum(((columns[j] >> i) & 1) << j for j in range(N))
            for i in range(N)]
    aug = [row | (1 << (N + i)) for i, row in enumerate(rows)]
    for column in range(N):
        pivot = next((i for i in range(column, N) if aug[i] >> column & 1), None)
        assert pivot is not None
        aug[column], aug[pivot] = aug[pivot], aug[column]
        for i in range(N):
            if i != column and aug[i] >> column & 1:
                aug[i] ^= aug[column]
    assert [row & ((1 << N) - 1) for row in aug] == [1 << i for i in range(N)]
    inverse_rows = [row >> N for row in aug]
    assert all(parity(inverse_rows[i] & columns[j]) == (i == j)
               for i in range(N) for j in range(N))
    return inverse_rows


def factored_eval(linear, pairs, value):
    result = parity(linear & value)
    for left, right in pairs:
        result ^= parity(left & value) & parity(right & value)
    return result


def main():
    start = time.monotonic()
    protocol = json.loads((D / 'factor_protocol.json').read_text())
    assert protocol['producer_sha256'] == sha(Path(__file__))
    assert protocol['screen_result_sha256'] == sha(D / 'result.json')
    result = json.loads((D / 'result.json').read_text())
    saved = result['panels']['2']['sorted']
    coeff = int(saved['certificate_hex'], 16)
    assert coeff < 1 << WIDTH
    bilinear = quadratic_rows(coeff)
    remaining = [1 << i for i in range(N)]
    basis = []
    pairs_count = 0
    while True:
        choice = next(((i, j) for i in range(len(remaining))
                       for j in range(i + 1, len(remaining))
                       if polar(bilinear, remaining[i], remaining[j])), None)
        if choice is None:
            break
        i, j = choice
        left, right = remaining[i], remaining[j]
        rest = [value for k, value in enumerate(remaining) if k not in (i, j)]
        next_rest = []
        for value in rest:
            adjusted = value
            if polar(bilinear, value, right):
                adjusted ^= left
            if polar(bilinear, value, left):
                adjusted ^= right
            assert polar(bilinear, adjusted, left) == 0
            assert polar(bilinear, adjusted, right) == 0
            next_rest.append(adjusted)
        basis.extend((left, right))
        pairs_count += 1
        remaining = next_rest
    basis.extend(remaining)
    assert len(basis) == N
    inverse_rows = inverse_basis(basis)
    assert all(polar(bilinear, basis[i], basis[j]) ==
               (i // 2 == j // 2 and i != j and i < 2 * pairs_count and j < 2 * pairs_count)
               for i in range(N) for j in range(N))
    linear = 0
    for i, vector in enumerate(basis):
        if monomial_eval(coeff, vector):
            linear ^= inverse_rows[i]
    products = [(inverse_rows[2 * k], inverse_rows[2 * k + 1])
                for k in range(pairs_count)]
    # Evaluations at 0, every basis vector, and every two-basis sum are an
    # exact coefficient certificate for all quadratic Boolean polynomials.
    checks = 1
    assert monomial_eval(coeff, 0) == factored_eval(linear, products, 0) == 0
    for i in range(N):
        word = 1 << i
        assert monomial_eval(coeff, word) == factored_eval(linear, products, word)
        checks += 1
        for j in range(i + 1, N):
            word = (1 << i) | (1 << j)
            assert monomial_eval(coeff, word) == factored_eval(linear, products, word)
            checks += 1
    assert checks == 1 + N + N * (N - 1) // 2
    checked_values = 0
    for mask in saved['accepted_masks']:
        for value in result['root0_values'][str(mask)]:
            assert factored_eval(linear, products, value) == 1
            checked_values += 1
    assert checked_values == 13 * 64
    factor = {'status': 'EXACT_SYMPLECTIC_QUADRATIC_FACTOR',
              'protocol_sha256': sha(D / 'factor_protocol.json'),
              'screen_result_sha256': sha(D / 'result.json'),
              'field_bits': N, 'quadratic_feature_width': WIDTH,
              'polarization_rank': 2 * pairs_count,
              'and_gates': pairs_count,
              'original_quadratic_monomials': saved['quadratic_terms'],
              'linear_mask_hex': hex(linear),
              'product_masks_hex': [[hex(a), hex(b)] for a, b in products],
              'basis_coefficient_checks': checks,
              'accepted_determinant_checks': checked_values,
              'covered_masks': saved['accepted_masks'],
              'wall_s': time.monotonic() - start}
    (D / 'factor_result.json').write_text(json.dumps(factor, indent=2, sort_keys=True) + '\n')
    print(json.dumps({k: factor[k] for k in ('status', 'polarization_rank',
                                            'and_gates', 'original_quadratic_monomials',
                                            'basis_coefficient_checks', 'wall_s')}))


if __name__ == '__main__':
    main()
