"""Freeze N41 implicit two-sign pair-source RR query before construction."""
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parent
SOURCE = ROOT / 'n41_sixpair_shared_target_20261017' / 'join_input.tsv'
PREV = ROOT / 'n41_rr_function_selector_20261017'
SOLVER = Path('/opt/homebrew/bin/cryptominisat5')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


previous = json.loads((PREV / 'audit_result.json').read_text())
assert previous['status'] == 'AUDIT_PASS'
assert all(previous[key]['query_status'] == 'BOUNDED_UNKNOWN'
           for key in ('v1', 'v2', 'v3'))
assert sha(SOURCE) == previous['source_sha256']
target = list(map(int, SOURCE.open().readline().split()[3:5]))
record = {
    'schema': 1,
    'curve_id': 'EC1N41Ckb1h7d5e80d3c4d0',
    'candidate_id': None,
    'field': 'GF(2)[t]/(t^41+t^3+1)',
    'curve': 'y^2+x*y=x^3+1',
    'target': target,
    'source_sha256': sha(SOURCE),
    'predecessor_audit_sha256': sha(PREV / 'audit_result.json'),
    'builder_sha256': sha(D / 'build.py'),
    'field_circuit_sha256': sha(ROOT / 'vd_z_s3_sixleaf_circuit.py'),
    'replay_helpers_sha256': sha(ROOT / 'build_n131_v20_sixleaf_circuit.py'),
    'solver_path': str(SOLVER),
    'solver_sha256': sha(SOLVER),
    'source_policy': 'one of 40 pair codes and two independent sign bits per slot; all 960 source states covered',
    'selector_method': 'degree-two ANF in sign bits for each seven-coordinate RR row, then six variable field products',
    'normalization': 'all seven first-nonzero projective coefficient charts',
    'one_worker': True,
    'solver_wall_cap_s': 185,
    'rss_boundary_bytes': 4 * 1024**3,
}
(D / 'protocol.json').write_text(json.dumps(record, indent=2, sort_keys=True) + '\n')
print(json.dumps({'protocol_sha256': sha(D / 'protocol.json'),
                  'builder_sha256': record['builder_sha256']}))
