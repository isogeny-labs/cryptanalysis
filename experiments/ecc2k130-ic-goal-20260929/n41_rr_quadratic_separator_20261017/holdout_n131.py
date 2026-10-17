"""Check the fixed N131 certificate on alternate first-slot roots."""
import hashlib
import importlib.util
import json
import time
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parent
ARCHIVE = ROOT / 'n41_n131_rr_code_family_span_20261017'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parity(word):
    return word.bit_count() & 1


def main():
    start = time.monotonic()
    protocol = json.loads((D / 'holdout_protocol.json').read_text())
    assert protocol['producer_sha256'] == sha(Path(__file__))
    for path, digest in protocol['sources'].items():
        assert sha(Path(path)) == digest, path
    panel = json.loads((ARCHIVE / 'panel_n131_v2.json').read_text())
    transfer = json.loads((D / 'transfer_result.json').read_text())
    audit = json.loads((D / 'transfer_audit_result.json').read_text())
    assert audit['status'] == 'N131_SYMBOLIC_TRANSFER_AUDIT_PASS'
    spec = importlib.util.spec_from_file_location(
        'rr_holdout', ROOT / 'n41_n131_sixpair_rr_root_span_20261016' / 'run.py')
    rr = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rr)
    field = rr.Field(panel['field_degree'], panel['field_modulus'])
    linear = int(transfer['linear_mask_hex'], 16)
    products = [(int(a, 16), int(b, 16))
                for a, b in transfer['product_masks_hex']]
    rows = []
    for i, variant in enumerate(panel['variants']):
        points = [variant['roots'][1][0]] + panel['fixed_points']
        coeff = rr.coefficients([p[0] for p in points],
                                [p[1] for p in points], panel['target'], field)
        if coeff is None:
            rows.append({'chart_index': i, 'status': 'DUPLICATE_X_EXCEPTION'})
            continue
        values = [rr.evaluate(coeff, sign) for sign in range(64)]
        outputs = [parity(linear & word) ^
                   (sum(parity(a & word) & parity(b & word) for a, b in products) & 1)
                   for word in values]
        rows.append({'chart_index': i, 'status': 'VALID_CHART',
                     'coefficient_sha256': hashlib.sha256(json.dumps(coeff).encode()).hexdigest(),
                     'zero_signs': [sign for sign, word in enumerate(values) if word == 0],
                     'certificate_one_signs': [sign for sign, bit in enumerate(outputs) if bit],
                     'nonzero_values_covered': sum(word != 0 and bit == 1
                                                   for word, bit in zip(values, outputs)),
                     'values': values})
    result = {'status': 'N131_ALTERNATE_ROOT_HOLDOUT_SCREEN',
              'protocol_sha256': sha(D / 'holdout_protocol.json'),
              'rows': rows, 'wall_s': time.monotonic() - start}
    (D / 'holdout_result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': result['status'],
                      'rows': [{'chart_index': row['chart_index'],
                                'status': row['status'],
                                'zero_count': len(row.get('zero_signs', [])),
                                'certificate_one_count': len(row.get('certificate_one_signs', []))}
                               for row in rows], 'wall_s': result['wall_s']}))


if __name__ == '__main__':
    main()
