"""Freeze an exact public-point witness assignment for the five-pair tower."""
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / 'n41_n131_w29_rotation_alignment_20261017/aligned_states.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


protocol = json.loads((HERE / 'fixture_protocol.json').read_text())
for name, path in {'script': Path(__file__), 'runtime': HERE / 'sage_runtime_info.json',
                   'states': SOURCE}.items():
    assert sha(path) == protocol['source_sha256'][name]
assert not (HERE / 'fixture.json').exists()

source = json.loads(SOURCE.read_text())
K = PolynomialRing(GF(2), 'u')
u = K.gen()
F = GF(2**41, name='u', modulus=u**41+u**3+1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])


def dec(word):
    return F(K([(int(word) >> i) & 1 for i in range(41)]))


def enc(x):
    return sum(int(c) << i for i, c in enumerate(x.polynomial().list()))


state_ids = [105, 244, 66, 47, 111]
points = [E(dec(source['states'][slot][sid]['point'][0]),
            dec(source['states'][slot][sid]['point'][1]))
          for slot, sid in enumerate(state_ids)]
raw = E(dec(source['target_raw_point'][0]),
        dec(source['target_raw_point'][1]))
public = E(raw[0]**(1 << 6), raw[1]**(1 << 6))
assert sum(points, E(0)) == public
left = sum(points[:3], E(0))
right = sum(points[3:], E(0))
assert left and right and left[0] and right[0] and public[0]
assert left+right == public

bits = [bit for bit in range(9) if bit != 5]
codes = []
for slot, sid in enumerate(state_ids):
    mask = source['states'][slot][sid]['masks'][0]
    code = sum(((mask >> bit) & 1) << j for j, bit in enumerate(bits))
    codes.append(code)

result = {
    'status': 'PASS_N41_IMPLICIT_TOWER_WITNESS_FIXTURE',
    'curve_id': source['curve_id'],
    'state_ids': state_ids,
    'code_ordinals': [sid//4 for sid in state_ids],
    'code_bit_words': codes,
    'left_reciprocal': enc(1/left[0]),
    'right_reciprocal': enc(1/right[0]),
    'public_reciprocal': enc(1/public[0]),
    'public_point': [enc(public[0]), enc(public[1])],
    'source_sha256': sha(SOURCE),
    'protocol_sha256': sha(HERE / 'fixture_protocol.json'),
}
(HERE / 'fixture.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
print(json.dumps(result, sort_keys=True))
