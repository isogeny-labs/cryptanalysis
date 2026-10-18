"""Enumerate the S3 tree through exact characteristic-two quadratics."""
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


protocol = json.loads((HERE / 's3_resolution_protocol.json').read_text())
for path, expected in protocol['sources'].items():
    assert sha(path) == expected, path
fixture = json.loads((ROOT / 'n41_n131_w29_rotation_alignment_20261017' /
                      'n41_model_fixture.json').read_text())
F = design.F


def s3_value(a, b, z):
    ab = F.mul(a, b)
    abz = F.mul(ab, z)
    return F.square(abz) ^ abz ^ F.square(a ^ b) ^ F.square(z)


def s3_roots(a, b):
    ab = F.mul(a, b)
    A = F.square(ab) ^ 1
    B = ab
    D = F.square(a ^ b)
    assert A and B
    q = F.mul(F.mul(A, D), F.square(F.inverse(B)))
    if design.trace(q):
        return []
    h = design.halftrace(q)
    unit = F.mul(B, F.inverse(A))
    roots = sorted((F.mul(unit, h), F.mul(unit, h ^ 1)))
    assert len(set(roots)) == 2
    assert all(s3_value(a, b, z) == 0 for z in roots)
    return roots


started = time.monotonic()
outputs = [row['output_reciprocal'] for row in fixture['pairs']]
assert len(outputs) == 5
left_first = s3_roots(outputs[0], outputs[1])
right = s3_roots(outputs[3], outputs[4])
rows = []
for m0 in left_first:
    for m1 in s3_roots(m0, outputs[2]):
        for m2 in right:
            rows.append({'middle_reciprocals': [m0, m1, m2],
                         'target_match': s3_value(m1, m2,
                                                  fixture['target_reciprocal']) == 0})
matches = [row for row in rows if row['target_match']]
assert any(row['middle_reciprocals'] == fixture['middle_reciprocals']
           for row in matches)
result = {'status': 'PASS_N41_W11_DIRECT_S3_TARGET_FILTER',
          'candidate_id': None, 'curve_id': protocol['curve_id'],
          'pair_outputs': outputs,
          'first_middle_count': len(left_first),
          'right_middle_count': len(right),
          'candidate_middle_tuples': len(rows),
          'target_compatible_tuples': len(matches),
          'matching_tuples': matches,
          'wall_seconds': time.monotonic() - started,
          'protocol_sha256': sha(HERE / 's3_resolution_protocol.json')}
out = HERE / 's3_resolution_result.json'
assert not out.exists()
out.write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps({k: result[k] for k in
                  ('status', 'candidate_middle_tuples',
                   'target_compatible_tuples', 'wall_seconds')}, sort_keys=True))
