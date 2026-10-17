"""Freeze exact gate-factorization input after independent RR audit."""
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


audit = json.loads((D / 'audit_result.json').read_text())
screen = json.loads((D / 'result.json').read_text())
assert audit['status'] == 'INDEPENDENT_QUADRATIC_CERTIFICATE_AUDIT_PASS'
assert audit['result_sha256'] == sha(D / 'result.json')
assert screen['panels']['2']['sorted']['quadratic_terms'] == 385
assert len(screen['panels']['2']['sorted']['accepted_masks']) == 13
record = {'schema': 1, 'screen_result_sha256': sha(D / 'result.json'),
          'independent_audit_sha256': sha(D / 'audit_result.json'),
          'producer_sha256': sha(D / 'factor.py'),
          'field_bits': 41,
          'gate_model': 'one AND per product of two arbitrary binary-linear forms; XORs counted separately',
          'certificate_arm': 'degree2 sorted code order'}
(D / 'factor_protocol.json').write_text(json.dumps(record, indent=2, sort_keys=True) + '\n')
print(json.dumps({'protocol_sha256': sha(D / 'factor_protocol.json')}))
