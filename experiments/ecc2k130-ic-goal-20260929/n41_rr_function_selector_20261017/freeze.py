"""Freeze the N41 source and exact formula implementation before building."""
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
R = D.parent
SOURCE = R/'n41_sixpair_shared_target_20261017'/'join_input.tsv'
SOLVER = Path('/opt/homebrew/bin/cryptominisat5')

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

head = SOURCE.read_text().splitlines()[0].split()
assert head[:3] == ['ECC2K41', '6', '160']
target = list(map(int, head[3:]))
assert target == [2026560328086, 1928332930914]
assert SOLVER.is_file()
protocol = {'schema': 1, 'source_sha256': sha(SOURCE),
            'builder_sha256': sha(D/'build.py'),
            'field_circuit_sha256': sha(R/'vd_z_s3_sixleaf_circuit.py'),
            'karatsuba_sha256': sha(R.parent/'koblitz-polynomial-w-pair-20260925'/'karatsuba_circuit.py'),
            'base_circuit_sha256': sha(R.parent/'koblitz-s5-invariant-20260924'/'circuit_sat.py'),
            'replay_helpers_sha256': sha(R/'build_n131_v20_sixleaf_circuit.py'),
            'solver_path': str(SOLVER), 'solver_sha256': sha(SOLVER),
            'target': target, 'curve_id': 'EC1N41Ckb1h7d5e80d3c4d0',
            'function_basis': ['x^2*y','x^3','x^2','x','x*y','y','1'],
            'normalization': 'one of seven projective leading coefficients equals one; all earlier coefficients zero',
            'source_policy': 'one of 160 exact signed pair states per slot; twelve distinct folded columns and seven distinct x coordinates',
            'one_worker': True, 'build_wall_cap_s': 180,
            'solver_wall_cap_s': 185, 'rss_boundary_bytes': 4294967296}
(D/'protocol.json').write_text(json.dumps(protocol, indent=2, sort_keys=True)+'\n')
print(json.dumps({'protocol_sha256': sha(D/'protocol.json'),
                  'source_sha256': protocol['source_sha256'],
                  'solver_sha256': protocol['solver_sha256']}))
