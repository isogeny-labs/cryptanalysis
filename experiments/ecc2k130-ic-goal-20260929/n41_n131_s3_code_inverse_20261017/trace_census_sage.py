"""Concrete reciprocal-curve trace and S3 discriminant census."""
import hashlib
import json
import time
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ALIGN = ROOT / 'n41_n131_w29_rotation_alignment_20261017'
QUOTIENT = ROOT / 'n41_n131_aligned_quotient_transfer_20261017'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


protocol = json.loads((HERE / 'trace_protocol.json').read_text())
for key, path in {
    'script': Path(__file__), 'runtime': HERE / 'sage_runtime_info.json',
    'n41_states': ALIGN / 'aligned_states.json',
    'n41_result': HERE / 'result.json',
    'n131_sample': QUOTIENT / 'n131_result.json',
    'n131_control': ALIGN / 'n131_aligned_control.json',
    'n131_result': HERE / 'n131_result.json',
}.items():
    assert sha(path) == protocol['source_sha256'][key], key


def field(n, powers):
    R = PolynomialRing(GF(2), 'u')
    u = R.gen()
    F = GF(2**n, name='u', modulus=sum(u**p for p in powers))
    def dec(word):
        return F(R([(int(word) >> i) & 1 for i in range(n)]))
    return F, dec


started = time.monotonic()
F41, dec41 = field(41, (41, 3, 0))
states = json.loads((ALIGN / 'aligned_states.json').read_text())
n41 = json.loads((HERE / 'result.json').read_text())
z41 = []
for i in range(71):
    values = {1/dec41(row['point'][0]) for row in states['states'][0][4*i:4*i+4]}
    assert len(values) == 2
    z41.extend(values)
t41 = [dec41(row['target_reciprocal']) for row in n41['queries']]
assert len(z41) == 142 and len(t41) == 65

F131, dec131 = field(131, (131, 13, 2, 1, 0))
sample = json.loads((QUOTIENT / 'n131_result.json').read_text())
control = json.loads((ALIGN / 'n131_aligned_control.json').read_text())
n131 = json.loads((HERE / 'n131_result.json').read_text())
seed = dec131(898618 << 1)
h = F131.zero()
v = seed
for _ in range(66):
    h += v
    v = v**4
assert h**2 + h == seed
C = 1+h**2
bits = [i for i in range(29) if i != (898618).bit_length()-1]
z131 = []
for code, root_word in zip(sample['codes'], sample['roots']):
    mask = sum(1 << bit for i, bit in enumerate(bits) if code >> i & 1)
    a = dec131(mask << 1)
    p = a*(a+seed)
    z = dec131(root_word)
    z131.extend((z, z+p/C))
for j in (0, 1):
    p = dec131(control['pairs'][j]['source_product'])
    z = 1/dec131(control['rotated_pair_points'][j][0])
    z131.extend((z, z+p/C))
t131 = [dec131(row['target_reciprocal']) for row in n131['queries']]
assert len(z131) == 1028 and len(t131) == 2


def check(values, targets):
    assert all(z and (z**2 + 1/z).trace() == 0 for z in values)
    assert all(t and (t**2 + 1/t).trace() == 0 for t in targets)
    pairs = 0
    for a in values:
        for t in targets:
            rhs = (1+(a*t)**2)*(a**2+t**2)/(a*t)**2
            split = a**2 + 1/a**2 + t**2 + 1/t**2
            assert rhs == split and rhs.trace() == 0
            pairs += 1
    return {'source_reciprocals': len(values), 'target_reciprocals': len(targets),
            'normalized_rhs_checks': pairs,
            'nonzero_trace_count': 0}


result = {
    'status': 'PASS_N41_N131_CURVE_TRACE_SEPARATION',
    'n41': check(z41, t41), 'n131': check(z131, t131),
    'elapsed_seconds': time.monotonic()-started,
    'protocol_sha256': sha(HERE / 'trace_protocol.json'),
    'source_sha256': {'script': sha(Path(__file__)),
                      'runtime': sha(HERE / 'sage_runtime_info.json')},
}
(HERE / 'trace_result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps(result, sort_keys=True))
