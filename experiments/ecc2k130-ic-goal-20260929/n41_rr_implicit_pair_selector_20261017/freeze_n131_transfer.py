"""Freeze the archived Sage sample comparison before N131 source replay."""
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parent
SAGE_AUDIT = ROOT / 'n131_w23_sixpair_density_20261016' / 'sage_audit_result.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


archived = json.loads(SAGE_AUDIT.read_text())
assert archived['status'] == 'PASS_SAGE_W23_FIXED_SEED_EDGE_AND_PAIR_AUDIT'
assert len(archived['audited_edges']) == 8
record = {'schema': 1, 'curve_id': 'EC1N131Ckb1heb5f1998f20b',
          'field_modulus': 't^131+t^13+t^2+t+1',
          'curve': 'y^2+x*y=x^3+1',
          'seed_mask': 898618, 'sample_edges': 8,
          'archived_sage_audit_sha256': sha(SAGE_AUDIT),
          'producer_sha256': sha(D / 'n131_transfer.py'),
          'source_scope': 'archived W23 Sage-audited edge samples only'}
(D / 'n131_transfer_protocol.json').write_text(json.dumps(record, indent=2, sort_keys=True) + '\n')
print(json.dumps({'protocol_sha256': sha(D / 'n131_transfer_protocol.json')}))
