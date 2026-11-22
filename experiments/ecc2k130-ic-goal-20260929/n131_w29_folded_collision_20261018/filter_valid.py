"""Enumerate orbit collisions and retain pairs with two valid W29 sources."""
import hashlib
import json
import resource
import signal
import sys
import time
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / 'n41_n131_fivepair_w9_w29_20261017'))
import circuit_n131_3p2 as design


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


protocol = json.loads((HERE / 'filter_protocol.json').read_text())
for path, digest in protocol['sources'].items():
    assert sha(path) == digest, path
assert not (HERE / 'filter_result.json').exists()
signal.signal(signal.SIGALRM, lambda _s, _f: (_ for _ in ()).throw(TimeoutError('valid collision filter wall cap')))
signal.alarm(protocol['wall_cap_seconds'])
started = time.monotonic()
audit = json.loads((HERE / 'audit_result.json').read_text())
assert audit['status'] == 'EXACT_N131_W29_FROBENIUS_COLLISION_SPACES'

P = PolynomialRing(GF(2), 'u')
u = P.gen()
K = GF(2**131, name='u', modulus=u**131 + u**13 + u**2 + u + 1)


def field(word):
    return K(P([(int(word) >> i) & 1 for i in range(131)]))


field_basis = [field(word) for word in design.BASE]
seed = field(design.SEED)
valid_cache = {}


def valid(code):
    if code not in valid_cache:
        a = K.zero()
        for i, basis in enumerate(field_basis):
            if code >> i & 1:
                a += basis
        b = a + seed
        if not a or not b:
            valid_cache[code] = False
        else:
            p = a*b
            inverse = ~p
            valid_cache[code] = (int(a.trace()) == 0 and
                                 int((a*inverse).trace()) == 0 and
                                 int((seed*inverse).trace()) == 0)
    return valid_cache[code]


control = json.loads((ROOT / 'n41_n131_w29_rotation_alignment_20261017' /
                      'n131_aligned_control.json').read_text())
for row in control['pairs']:
    mask = row['masks'][0]
    code = sum(((mask >> bit) & 1) << index for index, bit in enumerate(design.BITS))
    assert valid(code)

mask28 = (1 << 28) - 1
counts = {'nontrivial_cases': 0, 'enumerated_code_pairs': 0,
          'distinct_nonzero_code_pairs': 0, 'both_sources_valid_occurrences': 0}
unique = {}
case_rows = []
for row in audit['cases']:
    if not row['has_nontrivial_pair'] or row['frobenius_power'] == 0:
        continue
    counts['nontrivial_cases'] += 1
    initial = row['solution_code']
    kernel = row['kernel_codes']
    case_total = 0
    case_distinct = 0
    case_valid = 0
    for selection in range(1 << len(kernel)):
        solution = initial
        for i, word in enumerate(kernel):
            if selection >> i & 1:
                solution ^= word
        a_code, b_code = solution & mask28, solution >> 28
        case_total += 1
        if not a_code or not b_code or a_code == b_code:
            continue
        case_distinct += 1
        if valid(a_code) and valid(b_code):
            case_valid += 1
            pair = tuple(sorted((a_code, b_code)))
            provenance = (row['frobenius_power'], row['source_endpoint_e'],
                          row['other_endpoint_f'])
            unique.setdefault(pair, set()).add(provenance)
    counts['enumerated_code_pairs'] += case_total
    counts['distinct_nonzero_code_pairs'] += case_distinct
    counts['both_sources_valid_occurrences'] += case_valid
    case_rows.append({'frobenius_power': row['frobenius_power'],
                      'source_endpoint_e': row['source_endpoint_e'],
                      'other_endpoint_f': row['other_endpoint_f'],
                      'kernel_dimension': len(kernel),
                      'enumerated': case_total,
                      'distinct_nonzero': case_distinct,
                      'both_valid': case_valid})

collision_pairs = [
    {'codes': list(pair), 'provenance': [list(x) for x in sorted(provenance)]}
    for pair, provenance in sorted(unique.items())
]
finished = time.monotonic()
signal.alarm(0)
out = {
    'status': 'EXACT_VALID_N131_W29_FOLDED_COLLISION_PAIRS',
    'candidate_id': None,
    'curve_id': protocol['curve_id'],
    'validity': 'a,b nonzero; trace(a)=trace(a/p)=trace(seed/p)=0 with p=a(a+seed)',
    'counts': counts,
    'source_codes_tested': len(valid_cache),
    'distinct_valid_collision_pairs': len(collision_pairs),
    'cases': case_rows,
    'collision_pairs': collision_pairs,
    'wall_seconds': finished - started,
    'self_maxrss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    'protocol_sha256': sha(HERE / 'filter_protocol.json'),
}
(HERE / 'filter_result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
print(json.dumps({key: out[key] for key in
                  ('status', 'counts', 'source_codes_tested',
                   'distinct_valid_collision_pairs', 'wall_seconds')},
                 sort_keys=True))
