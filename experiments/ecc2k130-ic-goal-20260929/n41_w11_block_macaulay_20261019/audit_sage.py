"""Independent Sage truth-table and certificate replay for six N41 blocks."""
import hashlib
import json
import time
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / 'audit_protocol.json').read_text())
    assert protocol['status'] == 'FROZEN_BEFORE_N41_W11_BLOCK_SAGE_AUDIT'
    for item in protocol['sources'].values():
        assert sha(item['path']) == item['sha256']
    run = json.loads((HERE / 'result.json').read_text())
    assert run['status'] == 'COMPLETE_N41_W11_BLOCK_MACAULAY'
    rows = (ROOT / 'n41_w11_freecode_resultant_20261018' /
            'resultant_input.tsv').read_text().splitlines()
    terms = {i: {} for i in range(25)}
    for line in rows:
        parts = line.split()
        if parts[0] == 'C':
            terms[int(parts[1])][int(parts[2]), int(parts[3])] = int(parts[4])
    assert all(len(t) == 13 for t in terms.values())
    polynomial = PolynomialRing(GF(2), 'u')
    u = polynomial.gen()
    field = GF(2**41, name='u', modulus=u**41 + u**3 + 1)
    decode = field.from_integer
    encode = lambda value: sum(int(bit) << i for i, bit in
                               enumerate(value.polynomial().list()))
    seed = decode(112)
    bits = [0, 1, 2, 3, 4, 6, 7, 8, 9, 10]
    bases = []
    for rotation in [12, 24]:
        bases.append([(decode(1 << (bit + 1))**2 +
                       seed * decode(1 << (bit + 1)))**(1 << rotation)
                      for bit in bits])

    def product(code, basis):
        result = field.zero()
        for i, value in enumerate(basis):
            if code >> i & 1:
                result += value
        return result

    left = {code: product(code, bases[0])
            for row in run['results'] for code in range(row['anchor'], row['anchor'] + 4)}
    right = [product(code, bases[1]) for code in range(1024)]
    right_powers = [[field.one(), q, q**2, q**3, q**4] for q in right]
    decoded_terms = {index: {(i, j): decode(value) for (i, j), value in values.items()}
                     for index, values in terms.items()}
    start = time.monotonic()
    checks = []
    for cell in run['results']:
        target_index, anchor = cell['target_index'], cell['anchor']
        by_left = {}
        for code in range(anchor, anchor + 4):
            p = left[code]
            powers = [field.one(), p, p**2, p**3, p**4]
            coeff = [field.zero() for _ in range(5)]
            for (i, j), value in decoded_terms[target_index].items():
                coeff[j] += value * powers[i]
            by_left[code] = coeff
        truth = []
        roots = []
        for assignment in range(4096):
            code = anchor + (assignment & 3)
            right_code = assignment >> 2
            coeff = by_left[code]
            value = sum((coeff[j] * right_powers[right_code][j]
                         for j in range(5)), field.zero())
            if not value:
                roots.append([code, right_code])
            truth.append(encode(value))
        assert roots == cell['roots']
        # Binary Möbius transform converts the full truth table to the
        # unique squarefree ANF, independently of the producer's expansion.
        anf = truth[:]
        for bit in range(12):
            for mask in range(4096):
                if mask >> bit & 1:
                    anf[mask] ^= anf[mask ^ (1 << bit)]
        nonzero = [(mask, value) for mask, value in enumerate(anf) if value]
        assert len(nonzero) == cell['anf_terms']
        assert max(mask.bit_count() for mask, _ in nonzero) == cell['anf_degree']
        checked_certificates = 0
        for level in cell['levels']:
            if not level['reject']:
                assert level['certificate_rows'] is None
                continue
            replay = {}
            for field_bit, factor in level['certificate_rows']:
                assert 0 <= field_bit < 41 and factor.bit_count() <= 2
                for mask, value in nonzero:
                    if value >> field_bit & 1:
                        key = mask | factor
                        replay[key] = replay.get(key, 0) ^ 1
            assert {mask: value for mask, value in replay.items() if value} == {0: 1}
            checked_certificates += 1
        checks.append({'target_index': target_index, 'anchor': anchor,
                       'roots': roots, 'anf_terms': len(nonzero),
                       'certificates_checked': checked_certificates})
    assert len(checks) == 6
    out = {'status': 'PASS_N41_W11_BLOCK_SAGE_AUDIT',
           'candidate_id': None, 'curve_id': run['curve_id'],
           'cells_checked': len(checks),
           'certificates_checked': sum(c['certificates_checked'] for c in checks),
           'truth_table_values': 4096 * len(checks),
           'wall_seconds': time.monotonic() - start,
           'protocol_sha256': sha(HERE / 'audit_protocol.json'),
           'script_sha256': sha(__file__), 'run_sha256': sha(HERE / 'result.json'),
           'checks': checks}
    (HERE / 'audit_result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps({key: out[key] for key in
          ['status', 'cells_checked', 'certificates_checked', 'truth_table_values',
           'wall_seconds']}, sort_keys=True))


if __name__ == '__main__':
    main()
