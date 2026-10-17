"""Independent checked-Sage replay of the deterministic W29 edge sample."""
import hashlib
import json
import time
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
MASK64 = (1 << 64) - 1
WIDTH = 29
SEED = 898618
CANONICAL_BIT = 1 << (SEED.bit_length() - 1)
SAMPLES = 1 << 16


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def splitmix64(state):
    state = (state + 0x9e3779b97f4a7c15) & MASK64
    z = state
    z = ((z ^ (z >> 30)) * 0xbf58476d1ce4e5b9) & MASK64
    z = ((z ^ (z >> 27)) * 0x94d049bb133111eb) & MASK64
    return state, z ^ (z >> 31)


protocol = json.loads((HERE / 'sample_protocol.json').read_text())
worker = json.loads((HERE / 'sample_result.json').read_text())
audit_protocol = json.loads((HERE / 'sample_audit_protocol.json').read_text())
for name, digest in audit_protocol['source_sha256'].items():
    assert sha(HERE / name) == digest, name
assert protocol['status'] == 'FROZEN_BEFORE_W29_SAMPLE'
assert worker['status'] == 'COMPLETE'
assert worker['protocol_sha256'] == sha(HERE / 'sample_protocol.json')
F2 = GF(2)
R = PolynomialRing(F2, 'v')
v = R.gen()
F = GF(2**131, name='v', modulus=v**131 + v**13 + v**2 + v + 1)


def dec(mask):
    word = mask << 1
    return F(R([(word >> bit) & 1 for bit in range(30)]))


start = time.monotonic_ns()
state = 20261017
chosen = set()
counts = {'eligible_a': 0, 'eligible_b': 0, 'eligible_both': 0,
          'same_column': 0, 'inverse_checks': 0}
while len(chosen) < SAMPLES:
    state, value = splitmix64(state)
    a = (value & ((1 << WIDTH) - 1)) & ~CANONICAL_BIT
    if not a or a in chosen:
        continue
    chosen.add(a)
    b = a ^ SEED
    assert 0 < a < b < (1 << WIDTH)
    wa, wb = dec(a), dec(b)
    assert wa.trace() == 0 and wb.trace() == 0
    ia, ib = 1 / wa, 1 / wb
    assert wa * ia == 1 and wb * ib == 1
    counts['inverse_checks'] += 2
    va, vb = ia.trace() == 0, ib.trace() == 0
    counts['eligible_a'] += va
    counts['eligible_b'] += vb
    if not (va and vb):
        continue
    counts['eligible_both'] += 1
    orbit = wa
    same = False
    for _ in range(131):
        if orbit == wb:
            same = True
            break
        orbit = orbit**2
    assert same or orbit == wa
    counts['same_column'] += same
counts['usable_sample_edges'] = counts['eligible_both'] - counts['same_column']
for key, value in counts.items():
    assert value == worker['sample'][key], (key, value, worker['sample'][key])
result = {'status': 'PASS_INDEPENDENT_SAGE_W29_SAMPLE_REPLAY',
          'counts': counts, 'samples': SAMPLES,
          'elapsed_wall_seconds': (time.monotonic_ns() - start) / 1e9,
          'sample_result_sha256': sha(HERE / 'sample_result.json'),
          'audit_protocol_sha256': sha(HERE / 'sample_audit_protocol.json'),
          'auditor_sha256': sha(Path(__file__)),
          'runtime_sha256': sha(HERE / 'sage_runtime_info.json')}
with (HERE / 'sample_audit_result.json').open('x') as out:
    json.dump(result, out, sort_keys=True, indent=2)
    out.write('\n')
print(json.dumps(result, sort_keys=True), flush=True)
