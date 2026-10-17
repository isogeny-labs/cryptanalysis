"""Freeze both roots of four N131 source codes before certificate fitting."""
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parent
OLD = ROOT / 'n41_rr_quadratic_separator_20261017'
ARCH = ROOT / 'n41_n131_rr_code_family_span_20261017'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


sources = [OLD / name for name in
           ('transfer_result.json', 'transfer_audit_result.json',
            'holdout_result.json', 'holdout_audit_result.json',
            'screen.py', 'factor.py')]
sources += [ARCH / 'panel_n131_v2.json']
record = {'schema': 1, 'producer_sha256': sha(D / 'fit.py'),
          'sources': {str(path): sha(path) for path in sources},
          'train_codes': [0, 1, 2, 3], 'train_roots': [0, 1],
          'train_signs': list(range(64)),
          'holdout_first_mask_rule': 'first source-valid first-slot mask strictly greater than 46, ascending, with pair mate mask xor 898618 and distinct folded columns against the five frozen suffix pairs',
          'worker_count': 1, 'wall_cap_s': 180, 'rss_cap_bytes': 4 * 1024**3}
(D / 'protocol.json').write_text(json.dumps(record, sort_keys=True, indent=2) + '\n')
print(json.dumps({'protocol_sha256': sha(D / 'protocol.json')}))
