"""Independent symbolic coefficient audit of the factored Boolean form."""
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
N = 41


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((D / 'factor_protocol.json').read_text())
    result = json.loads((D / 'factor_result.json').read_text())
    screen = json.loads((D / 'result.json').read_text())
    assert protocol['producer_sha256'] == sha(D / 'factor.py')
    assert protocol['screen_result_sha256'] == sha(D / 'result.json')
    assert protocol['independent_audit_sha256'] == sha(D / 'audit_result.json')
    assert result['protocol_sha256'] == sha(D / 'factor_protocol.json')
    assert result['screen_result_sha256'] == sha(D / 'result.json')
    assert result['status'] == 'EXACT_SYMPLECTIC_QUADRATIC_FACTOR'
    linear = int(result['linear_mask_hex'], 16)
    pairs = [(int(a, 16), int(b, 16))
             for a, b in result['product_masks_hex']]
    assert len(pairs) == result['and_gates'] == 20
    assert all(0 < value < (1 << N) for pair in pairs for value in pair)
    original = int(screen['panels']['2']['sorted']['certificate_hex'], 16)
    assert result['covered_masks'] == screen['panels']['2']['sorted']['accepted_masks']
    assert len(result['covered_masks']) == 13
    symbolic = 0
    for i in range(N):
        bit = ((linear >> i) & 1) ^ sum(((a >> i) & 1) & ((b >> i) & 1)
                                        for a, b in pairs) % 2
        symbolic |= bit << i
    index = N
    for i in range(N):
        for j in range(i + 1, N):
            bit = sum((((a >> i) & 1) & ((b >> j) & 1)) ^
                      (((a >> j) & 1) & ((b >> i) & 1))
                      for a, b in pairs) % 2
            symbolic |= bit << index
            index += 1
    assert index == 861
    assert symbolic == original
    input_literals = sum(a.bit_count() + b.bit_count() for a, b in pairs)
    linear_terms = linear.bit_count()
    assert result['basis_coefficient_checks'] == 862
    assert result['accepted_determinant_checks'] == 832
    audit = {'status': 'EXACT_SYMBOLIC_FACTOR_AUDIT_PASS',
             'factor_protocol_sha256': sha(D / 'factor_protocol.json'),
             'factor_result_sha256': sha(D / 'factor_result.json'),
             'screen_result_sha256': sha(D / 'result.json'),
             'coefficient_bits_checked': index,
             'constant_bit_checked': True,
             'and_gates': len(pairs),
             'linear_form_input_literals': input_literals,
             'linear_output_terms': linear_terms,
             'covered_code_charts': len(result['covered_masks'])}
    (D / 'factor_audit_result.json').write_text(json.dumps(audit, indent=2, sort_keys=True) + '\n')
    print(json.dumps(audit, sort_keys=True))


if __name__ == '__main__':
    main()
