"""Independent Sage enumeration of all 256 W9 fixed-seed pair codes."""
import hashlib
import json
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
R = PolynomialRing(GF(2), 'u')
u = R.gen()
F = GF(2**41, name='u', modulus=u**41 + u**3 + 1)
BITS = [bit for bit in range(9) if bit != 5]
SEED = 56


def dec(word):
    return F(R([(word >> bit) & 1 for bit in range(41)]))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


states_path = HERE.parent / 'n41_n131_fivepair_w9_w29_20261017/n41_states.json'
states = json.loads(states_path.read_text())
expected = {row['masks'][0] for row in states['states'][0]}
accepted = set()
for code in range(256):
    mask = sum((code >> j & 1) << bit for j, bit in enumerate(BITS))
    a = dec(mask << 1)
    b = a + dec(SEED << 1)
    if a and b and a.trace() == 0 and b.trace() == 0 \
            and (1 / a).trace() == 0 and (1 / b).trace() == 0:
        accepted.add(mask)
assert accepted == expected
result = {'status': 'PASS_INDEPENDENT_SAGE_W9_SOURCE_CENSUS',
          'evaluated_codes': 256, 'accepted_codes': len(accepted),
          'accepted_masks': sorted(accepted),
          'source_sha256': {'auditor': sha(Path(__file__)),
                            'states': sha(states_path),
                            'runtime': sha(HERE / 'sage_runtime_info.json')}}
with (HERE / 'census_sage_result.json').open('x') as out:
    json.dump(result, out, sort_keys=True, indent=2)
    out.write('\n')
print(json.dumps({'status': result['status'],
                  'accepted_codes': len(accepted)}))
