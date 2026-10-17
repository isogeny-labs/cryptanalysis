"""Freeze the archived N131 transfer inputs before running the separator."""
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parent
ARCHIVE = ROOT / 'n41_n131_rr_code_family_span_20261017'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


sources = [ARCHIVE / name for name in
           ('panel_n131_v2.json', 'result_n131_v2.json', 'audit_result_n131.json')]
sources += [ROOT / 'n41_n131_sixpair_rr_root_span_20261016' / 'run.py',
            D / 'screen.py', D / 'factor.py']
record = {'schema': 1, 'producer_sha256': sha(D / 'transfer_n131.py'),
          'sources': {str(path): sha(path) for path in sources},
          'field_degree': 131, 'chart_count': 4,
          'first_slot_root': 0, 'fixed_suffix_point_count': 5,
          'target_conditioning': 'frozen archived N131 public target',
          'worker_count': 1, 'wall_cap_s': 180, 'rss_cap_bytes': 4 * 1024 ** 3}
(D / 'transfer_protocol.json').write_text(json.dumps(record, sort_keys=True, indent=2) + '\n')
print(json.dumps({'protocol_sha256': sha(D / 'transfer_protocol.json')}))
