"""Freeze the alternate-root N131 holdout before evaluation."""
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parent
ARCHIVE = ROOT / 'n41_n131_rr_code_family_span_20261017'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


sources = [ARCHIVE / 'panel_n131_v2.json', D / 'transfer_result.json',
           D / 'transfer_audit_result.json',
           ROOT / 'n41_n131_sixpair_rr_root_span_20261016' / 'run.py']
record = {'schema': 1, 'producer_sha256': sha(D / 'holdout_n131.py'),
          'sources': {str(path): sha(path) for path in sources},
          'chart_indices': [0, 1, 2, 3], 'first_slot_root': 1,
          'fixed_suffix_point_count': 5, 'certificate_source': 'N131 root0 four-chart fit'}
(D / 'holdout_protocol.json').write_text(json.dumps(record, sort_keys=True, indent=2) + '\n')
print(json.dumps({'protocol_sha256': sha(D / 'holdout_protocol.json')}))
