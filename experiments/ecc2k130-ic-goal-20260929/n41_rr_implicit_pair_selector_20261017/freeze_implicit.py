"""Freeze mask/curve source derivation before its exhaustive N41 replay."""
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parent
SOURCE = ROOT / 'n41_sixpair_shared_target_20261017' / 'join_input.tsv'
GEOMETRY = ROOT / 'n41_w8_fixed_sum_table_20261009' / 'geometry.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


record = {'schema': 1, 'curve_id': 'EC1N41Ckb1h7d5e80d3c4d0',
          'source_sha256': sha(SOURCE), 'geometry_sha256': sha(GEOMETRY),
          'producer_sha256': sha(D / 'implicit_geometry.py'),
          'target': list(map(int, SOURCE.open().readline().split()[3:5])),
          'source_policy': 'canonical fixed-sum mask pair, independent half-trace endpoint signs, six fixed rotations',
          'expected_point_output_checks': 960}
(D / 'implicit_protocol.json').write_text(json.dumps(record, indent=2, sort_keys=True) + '\n')
print(json.dumps({'protocol_sha256': sha(D / 'implicit_protocol.json')}))
