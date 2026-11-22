"""Enumerate every canonical W11 source code and its signed pair outputs."""
import hashlib
import json
import resource
import signal
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / 'n41_count_protocol.json').read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path, expected in protocol['sources'].items():
    assert sha(path) == expected, path
assert not (HERE / 'n41_count_result.json').exists()
signal.signal(signal.SIGALRM, lambda _s, _f: (_ for _ in ()).throw(TimeoutError('W11 count cap')))
signal.alarm(protocol['wall_cap_seconds'])
started = time.monotonic()
P = PolynomialRing(GF(2), 'u')
u = P.gen()
K = GF(2**41, name='u', modulus=u**41 + u**3 + 1)
E = EllipticCurve(K, [1, 0, 0, 0, 1])
bits = [i for i in range(11) if i != (56).bit_length() - 1]
base = [K(P([int(j == bit+1) for j in range(41)])) for bit in bits]
seed = K(P([(112 >> j) & 1 for j in range(41)]))


def halftrace(value):
    out, power = K.zero(), value
    for _ in range(21):
        out += power
        power = power**4
    assert out*out + out == value
    return out


def source_points(w):
    h = halftrace(w)
    assert h
    x = K.one() + ~h
    return E.lift_x(x, all=True)


valid = []
output_histogram = {}
for code in range(1 << len(bits)):
    a = K.zero()
    for i, word in enumerate(base):
        if code >> i & 1:
            a += word
    b = a + seed
    if not a or not b or a.trace() or (~a).trace() or (~b).trace():
        continue
    options = []
    for left in source_points(a):
        for right in source_points(b):
            pair = left + right
            if pair != E(0) and pair[0]:
                options.append(pair)
    count = len(options)
    output_histogram[str(count)] = output_histogram.get(str(count), 0) + 1
    valid.append(code)

finished = time.monotonic()
signal.alarm(0)
result = {'status': 'EXACT_N41_W11_SOURCE_POPULATION',
          'candidate_id': None,
          'curve_id': protocol['curve_id'],
          'source_code_bits': len(bits),
          'canonical_codes': 1 << len(bits),
          'valid_pair_codes': len(valid),
          'valid_codes': valid,
          'signed_pair_output_count': sum(int(k)*v for k, v in output_histogram.items()),
          'signed_pair_output_histogram': output_histogram,
          'wall_seconds': finished - started,
          'self_maxrss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          'protocol_sha256': sha(HERE / 'n41_count_protocol.json')}
(HERE / 'n41_count_result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps({key: result[key] for key in
                  ('status', 'valid_pair_codes', 'signed_pair_output_count',
                   'signed_pair_output_histogram', 'wall_seconds')}, sort_keys=True))
