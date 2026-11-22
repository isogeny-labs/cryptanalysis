"""Freeze table-free arithmetic source circuit after exhaustive source replay."""
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parent
SOURCE = ROOT / 'n41_sixpair_shared_target_20261017' / 'join_input.tsv'
GEOMETRY = ROOT / 'n41_w8_fixed_sum_table_20261009' / 'geometry.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


implicit = json.loads((D / 'implicit_result.json').read_text())
code_query = json.loads((D / 'query_result.json').read_text())
assert implicit['status'] == 'ALL_960_IMPLICIT_POINT_OUTPUTS_MATCH'
assert implicit['point_output_checks'] == 960
assert code_query['status'] == 'BOUNDED_UNKNOWN'
assert code_query['protocol_sha256'] == sha(D / 'query_protocol.json')
assert implicit['source_sha256'] == sha(SOURCE)
assert implicit['geometry_sha256'] == sha(GEOMETRY)
base = json.loads((D / 'protocol.json').read_text())
record = {'schema': 1, 'curve_id': base['curve_id'], 'candidate_id': None,
          'field': base['field'], 'curve': base['curve'],
          'target': base['target'], 'source_sha256': sha(SOURCE),
          'geometry_sha256': sha(GEOMETRY),
          'implicit_result_sha256': sha(D / 'implicit_result.json'),
          'predecessor_query_result_sha256': sha(D / 'query_result.json'),
          'builder_sha256': sha(D / 'implicit_build.py'),
          'support_builder_sha256': sha(D / 'build.py'),
          'field_circuit_sha256': base['field_circuit_sha256'],
          'replay_helpers_sha256': base['replay_helpers_sha256'],
          'solver_path': base['solver_path'],
          'solver_sha256': base['solver_sha256'],
          'source_policy': 'seven canonical mask bits plus two independent half-trace endpoint signs per slot; no point-row table',
          'normalization': base['normalization'],
          'one_worker': True, 'solver_wall_cap_s': 185,
          'rss_boundary_bytes': base['rss_boundary_bytes']}
(D / 'implicit_build_protocol.json').write_text(json.dumps(record, indent=2, sort_keys=True) + '\n')
print(json.dumps({'protocol_sha256': sha(D / 'implicit_build_protocol.json'),
                  'builder_sha256': record['builder_sha256']}))
