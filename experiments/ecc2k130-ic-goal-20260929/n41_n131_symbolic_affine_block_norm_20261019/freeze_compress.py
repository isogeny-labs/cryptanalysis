import hashlib
import json
from pathlib import Path

here = Path(__file__).resolve().parent
prior = json.loads((here / 'retry_protocol.json').read_text())
paths = [
    here / 'compress_sage.py',
    here / 'retry_result.json',
    here / 'sage_runtime_info.json',
    Path(prior['eliminant']),
    Path(prior['source_states']),
    Path('/Volumes/SSD990/cryptanalysis/experiments/ecc2k130-ic-goal-20260929/n41_w9_two_product_eliminant_20261017/group_audit_result.json'),
]
protocol = {
    'status': 'FROZEN_BEFORE_N41_COMPRESSED_AFFINE_BLOCK_NORM',
    'candidate_id': None,
    'curve_id': prior['curve_id'],
    'eliminant': prior['eliminant'],
    'source_states': prior['source_states'],
    'variable_code_bit_indices': [2, 0, 1, 3],
    'positive_prefix': 14,
    'wall_cap_seconds': 120,
    'sources': {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths},
    'test': 'Exact 16-code affine norm compression, all 16 prefixes, independent explicit products and right-subspace GCDs',
}
dest = here / 'compress_protocol.json'
assert not dest.exists()
dest.write_text(json.dumps(protocol, sort_keys=True, indent=2) + '\n')
print(hashlib.sha256(dest.read_bytes()).hexdigest())
