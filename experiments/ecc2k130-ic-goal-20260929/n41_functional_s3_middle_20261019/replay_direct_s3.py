"""Replay exact S3 middle enumeration on the fixed circuit inputs."""
import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / 'n41_w9_lazy_source_20261017'))
import circuit as design


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


protocol = json.loads((HERE / 'direct_replay_protocol.json').read_text())
for path, expected in protocol['sources'].items():
    assert sha(path) == expected, path
assert not (HERE / 'direct_replay_result.json').exists()
fixture = json.loads(Path(protocol['fixture']).read_text())
fixed = json.loads((HERE / 'fixed_build_result.json').read_text())
F = design.F


def s3(a, b, z):
    ab = F.mul(a, b)
    abz = F.mul(ab, z)
    return F.square(abz) ^ abz ^ F.square(a ^ b) ^ F.square(z)


def roots(a, b):
    B = F.mul(a, b)
    A = F.square(B) ^ 1
    D = F.square(a ^ b)
    assert A and B  # The frozen control avoids the exceptional coefficients.
    q = F.mul(F.mul(A, D), F.square(F.inverse(B)))
    if design.trace(q):
        return []
    h = design.halftrace(q)
    scale = F.mul(B, F.inverse(A))
    found = sorted((F.mul(scale, h), F.mul(scale, h ^ 1)))
    assert len(set(found)) == 2
    assert all(s3(a, b, z) == 0 for z in found)
    return found


start = time.monotonic()
outputs = fixed['fixed_outputs']
assert outputs == [row['output_reciprocal'] for row in fixture['pairs']]
rotated = [F.frob(value, shift)
           for value, shift in zip(outputs, fixture['rotations'])]
rows = []
for left in roots(rotated[0], rotated[1]):
    for middle in roots(left, rotated[2]):
        for right in roots(rotated[3], rotated[4]):
            if s3(middle, right, fixture['target_reciprocal']) == 0:
                rows.append([left, middle, right])
elapsed = time.monotonic() - start
assert len(rows) == 1
assert rows[0] == fixture['middle_reciprocals']
result = {'status': 'PASS_N41_FUNCTIONAL_S3_DIRECT_FIXED_REPLAY',
          'candidate_id': None, 'curve_id': protocol['curve_id'],
          'candidate_middle_tuples': 8, 'target_compatible_tuples': len(rows),
          'middle_reciprocals': rows[0], 'wall_seconds': elapsed,
          'fixed_formula_sha256': sha(HERE / 'fixed_formula.xcnf'),
          'protocol_sha256': sha(HERE / 'direct_replay_protocol.json')}
(HERE / 'direct_replay_result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps(result, sort_keys=True))
