"""Audit every admissible pair-code quadratic used by the tower circuit."""
import hashlib
import json
import resource
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / 'n41_n131_w29_rotation_alignment_20261017/aligned_states.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


protocol = json.loads((HERE / 'pair_law_protocol.json').read_text())
for name, path in {'script': Path(__file__),
                   'runtime': HERE / 'pair_law_runtime_info.json',
                   'states': SOURCE,
                   'build': HERE / 'build_result.json',
                   'early_build': HERE / 'early_build_result.json'}.items():
    assert sha(path) == protocol['source_sha256'][name], name
assert not (HERE / 'pair_law_result.json').exists()

start = time.monotonic()
source = json.loads(SOURCE.read_text())
K = PolynomialRing(GF(2), 'u')
u = K.gen()
F = GF(2**41, name='u', modulus=u**41+u**3+1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])


def dec(word):
    return F(K([(int(word) >> i) & 1 for i in range(41)]))


def enc(value):
    return sum(int(c) << i for i, c in enumerate(value.polynomial().list()))


def halftrace(x):
    initial = x
    out = F.zero()
    for _ in range(21):
        out += x
        x = x**4
    assert out*out+out == initial
    return out


seed = dec(source['seed'] << 1)
H0 = halftrace(seed)**2
C0 = 1+H0
assert H0 and C0
root_rows = 0
signed_states = 0
for slot, rotation in enumerate(source['rotations']):
    H = H0**(1 << rotation)
    C = C0**(1 << rotation)
    for code in range(71):
        block = source['states'][slot][4*code:4*code+4]
        assert len(block) == 4
        mask = block[0]['masks'][0]
        a = dec(mask << 1)
        product = (a*(a+seed))**(1 << rotation)
        roots = set()
        columns = set(block[0]['columns'])
        assert len(columns) == 2
        for row in block:
            assert set(row['columns']) == columns
            point = E(dec(row['point'][0]), dec(row['point'][1]))
            assert point != E(0) and point[0]
            z = 1/point[0]
            assert C*z*z+product*z+H == 0
            roots.add(enc(z))
            signed_states += 1
        assert len(roots) == 2
        root_rows += 1

result = {
    'status': 'PASS_ALL_N41_IMPLICIT_PAIR_QUADRATICS',
    'curve_id': source['curve_id'],
    'pair_code_rows_checked': root_rows,
    'signed_states_checked': signed_states,
    'roots_per_code': 2,
    'elapsed_seconds': time.monotonic()-start,
    'self_maxrss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    'protocol_sha256': sha(HERE / 'pair_law_protocol.json'),
}
(HERE / 'pair_law_result.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
print(json.dumps(result, sort_keys=True))
