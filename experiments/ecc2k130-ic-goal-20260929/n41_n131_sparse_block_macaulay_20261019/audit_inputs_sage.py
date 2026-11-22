"""Independently reconstruct every frozen sparse input over checked Sage fields."""
import hashlib
import json
import time
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def field_for(n):
    polynomial = PolynomialRing(GF(2), 'u')
    u = polynomial.gen()
    modulus = u**41 + u**3 + 1 if n == 41 else u**131 + u**13 + u**2 + u + 1
    return GF(2**n, name='u', modulus=modulus)


def add(left, right, zero):
    result = dict(left)
    for mask, value in right.items():
        result[mask] = result.get(mask, zero) + value
        if not result[mask]:
            del result[mask]
    return result


def mul(left, right, zero):
    result = {}
    for mask_a, value_a in left.items():
        for mask_b, value_b in right.items():
            mask = mask_a | mask_b
            result[mask] = result.get(mask, zero) + value_a * value_b
            if not result[mask]:
                del result[mask]
    return result


def powers(poly, one, zero):
    square = {mask: value**2 for mask, value in poly.items()}
    fourth = {mask: value**2 for mask, value in square.items()}
    return [{0: one}, poly, square, mul(poly, square, zero), fourth]


def expected_supports(n, terms, anchor):
    field = field_for(n)
    decode = field.from_integer
    encode = lambda value: sum(int(bit) << i for i, bit in
                               enumerate(value.polynomial().list()))
    if n == 41:
        seed, positions, rotations = 112, [0, 1, 2, 3, 4, 6, 7, 8, 9, 10], [12, 24]
    else:
        mask = 898618
        seed, positions, rotations = mask << 1, [i for i in range(33)
            if i != mask.bit_length() - 1], [0, 18]
    bases = []
    for rotation in rotations:
        bases.append([(decode(1 << (bit + 1))**2 +
                       decode(seed) * decode(1 << (bit + 1)))**(1 << rotation)
                      for bit in positions])
    p0 = sum((bases[0][i] for i in range(len(positions)) if anchor >> i & 1),
             field.zero())
    left = {0: p0, 1: bases[0][0], 2: bases[0][1]}
    right = {1 << (j + 2): value for j, value in enumerate(bases[1])}
    pp = powers(left, field.one(), field.zero())
    qq = powers(right, field.one(), field.zero())
    result = {}
    for (i, j), encoded in terms.items():
        term = mul(pp[i], qq[j], field.zero())
        scaled = {mask: decode(encoded) * value for mask, value in term.items()}
        result = add(result, scaled, field.zero())
    supports = [[] for _ in range(n)]
    for monomial, value in result.items():
        encoded = encode(value)
        while encoded:
            low = encoded & -encoded
            supports[low.bit_length() - 1].append(monomial)
            encoded ^= low
    for row in supports:
        row.sort()
    return supports, len(result)


def read_equations(path, variables, n):
    with path.open() as stream:
        assert stream.readline().split() == ['EQS', str(variables), str(n), '4', '2']
        rows = []
        for bit in range(n):
            values = [int(x) for x in stream.readline().split()]
            assert values[0] == bit and values[1] == len(values) - 2
            rows.append(values[2:])
        assert not stream.read().strip()
    return rows


def main():
    cfg = json.loads((HERE / 'audit_protocol.json').read_text())
    assert cfg['status'] == 'FROZEN_BEFORE_SPARSE_INPUT_SAGE_AUDIT'
    for item in cfg['sources'].values():
        assert sha(item['path']) == item['sha256']
    prepared = json.loads((HERE / 'prepare_result.json').read_text())
    n41_terms = {i: {} for i in [0, 1]}
    for line in (ROOT / 'n41_w11_freecode_resultant_20261018' /
                 'resultant_input.tsv').read_text().splitlines():
        row = line.split()
        if row[0] == 'C' and int(row[1]) in n41_terms:
            n41_terms[int(row[1])][int(row[2]), int(row[3])] = int(row[4])
    n131_coeff = json.loads((ROOT / 'n131_w33_freecode_resultant_20261018' /
                             'coefficients.json').read_text())
    start = time.monotonic()
    checks = []
    for record in prepared['outputs']:
        n = record['field_degree']
        if n == 41:
            terms = n41_terms[record['target_index']]
        else:
            terms = {(i, j): value for i, j, value in
                     n131_coeff['rows'][record['target_index']]['terms']}
        supports, term_count = expected_supports(n, terms, record['anchor'])
        assert term_count == record['anf_terms']
        assert supports == read_equations(Path(record['path']), record['variables'], n)
        checks.append({'label': record['label'], 'field_degree': n,
                       'anf_terms': term_count,
                       'support_entries': sum(map(len, supports)),
                       'input_sha256': sha(record['path'])})
    assert len(checks) == 8
    result = {'status': 'PASS_SPARSE_INPUT_SAGE_AUDIT', 'candidate_id': None,
              'checks': checks, 'wall_seconds': time.monotonic() - start,
              'protocol_sha256': sha(HERE / 'audit_protocol.json'),
              'script_sha256': sha(__file__)}
    (HERE / 'audit_result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'files': len(checks),
                      'wall_seconds': result['wall_seconds']}, sort_keys=True))


if __name__ == '__main__':
    main()
