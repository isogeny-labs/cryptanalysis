"""Independent symbolic audit of the N131 four-chart quadratic certificate."""
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parent
ARCHIVE = ROOT / 'n41_n131_rr_code_family_span_20261017'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parity(value):
    return value.bit_count() & 1


def main():
    result = json.loads((D / 'transfer_result.json').read_text())
    run = json.loads((D / 'transfer_run_result.json').read_text())
    protocol = json.loads((D / 'transfer_protocol.json').read_text())
    archive = json.loads((ARCHIVE / 'audit_result_n131.json').read_text())
    panel = json.loads((ARCHIVE / 'panel_n131_v2.json').read_text())
    assert run['status'] == 'COMPLETE'
    assert run['result_sha256'] == sha(D / 'transfer_result.json')
    assert result['protocol_sha256'] == sha(D / 'transfer_protocol.json')
    assert protocol['sources'][str(ARCHIVE / 'audit_result_n131.json')] == sha(ARCHIVE / 'audit_result_n131.json')
    assert archive['status'] == 'PASS_INDEPENDENT_N131_DETERMINANT_RANK_REPLAY'
    assert result['target'] == panel['target']
    assert [m['coefficient_sha256'] for m in result['chart_metadata']] == \
           [row['coefficient_sha256'] for row in archive['rows']]
    n = result['field_degree']
    assert n == 131
    products = [(int(left, 16), int(right, 16))
                for left, right in result['product_masks_hex']]
    linear = int(result['linear_mask_hex'], 16)
    assert len(products) == result['and_gates'] == 11
    assert all(0 < mask < (1 << n) for pair in products for mask in pair)
    assert 0 <= linear < (1 << n)
    symbolic = 0
    for i in range(n):
        bit = (linear >> i) & 1
        for left, right in products:
            bit ^= ((left >> i) & 1) & ((right >> i) & 1)
        symbolic |= bit << i
    index = n
    for i in range(n):
        for j in range(i + 1, n):
            bit = 0
            for left, right in products:
                bit ^= (((left >> i) & 1) & ((right >> j) & 1)) ^ \
                       (((left >> j) & 1) & ((right >> i) & 1))
            symbolic |= bit << index
            index += 1
    assert index == n + n * (n - 1) // 2 == 8646
    assert symbolic == int(result['quadratic']['certificate_hex'], 16)
    assert result['quadratic']['accepted_masks'] == [0, 1, 2, 3]
    assert result['linear']['accepted_masks'] == [0, 1, 2]
    checked = 0
    for values in result['values'].values():
        assert len(values) == 64
        for word in values:
            assert word != 0
            output = parity(linear & word)
            for left, right in products:
                output ^= parity(left & word) & parity(right & word)
            assert output == 1
            checked += 1
    assert checked == 256
    receipt = {'status': 'N131_SYMBOLIC_TRANSFER_AUDIT_PASS',
               'transfer_result_sha256': sha(D / 'transfer_result.json'),
               'archived_independent_audit_sha256': sha(ARCHIVE / 'audit_result_n131.json'),
               'coefficient_bits_checked': index, 'determinant_values_checked': checked,
               'constant_bit_checked': True, 'and_gates': len(products),
               'linear_form_input_literals': sum(a.bit_count() + b.bit_count()
                                                 for a, b in products),
               'linear_output_terms': linear.bit_count()}
    (D / 'transfer_audit_result.json').write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n')
    print(json.dumps(receipt, sort_keys=True))


if __name__ == '__main__':
    main()
