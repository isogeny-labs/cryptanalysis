"""Independent binary-field matrix replay of aligned root-difference ranks."""
import hashlib
import json
from pathlib import Path

from sage.all import GF, PolynomialRing, matrix

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


protocol = json.loads((HERE / 'branch_rank_protocol.json').read_text())
result = json.loads((HERE / 'branch_rank_result.json').read_text())
assert result['status'] == 'PASS_EXACT_BRANCH_DIFFERENCE_RANKS'
assert result['protocol_sha256'] == sha(HERE / 'branch_rank_protocol.json')
for name, path in {'script': HERE / 'rank_branch_spans.py',
                   'n41': ROOT / 'n41_w9_lazy_source_20261017/circuit.py',
                   'n131': ROOT / 'n41_n131_fivepair_w9_w29_20261017/circuit_n131_3p2.py'}.items():
    assert sha(path) == protocol['source_sha256'][name]


def field(n, taps):
    R = PolynomialRing(GF(2), 'u')
    u = R.gen()
    F = GF(2**n, name='u', modulus=u**n + sum(u**i for i in taps))
    def dec(word):
        return F(R([(int(word) >> bit) & 1 for bit in range(n)]))
    def enc(value):
        return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))
    return F, dec, enc


rows = {}
for name, n, taps, width, seed_mask in (
        ('n41', 41, [0, 3], 9, 56),
        ('n131', 131, [0, 1, 2, 13], 29, 898618)):
    F, dec, enc = field(n, taps)
    seed = dec(seed_mask << 1)
    halftrace = lambda a: sum((a**(1 << (2 * i)) for i in range((n + 1) // 2)), F.zero())
    assert halftrace(seed)**2 + halftrace(seed) == seed
    C = 1 + halftrace(seed)**2
    assert C
    bits = [bit for bit in range(width) if bit != seed_mask.bit_length() - 1]
    base = [dec(1 << (bit + 1)) for bit in bits]
    diff = [(a**2 + seed * a) / C for a in base]
    assert len(diff) == result['rows'][name]['source_product_rank']
    cases = {}
    for variant, rotations in protocol['rotation_schedules'][name].items():
        vectors = []
        prefix_ranks = []
        for rotation in rotations:
            vectors.extend(enc(value**(1 << rotation)) for value in diff)
            M = matrix(GF(2), n, len(vectors),
                       lambda i, j: (vectors[j] >> i) & 1)
            prefix_ranks.append(int(M.rank()))
        assert prefix_ranks == result['rows'][name]['cases'][variant]['prefix_ranks']
        cases[variant] = {'prefix_ranks': prefix_ranks,
                          'annihilator_dimension': n - prefix_ranks[-1]}
    rows[name] = cases

states = json.loads((ROOT / 'n41_n131_fivepair_w9_w29_20261017/n41_states.json').read_text())
F, dec, enc = field(41, [0, 3])
seed = dec(56 << 1)
halftrace = lambda a: sum((a**(1 << (2 * i)) for i in range(21)), F.zero())
C = 1 + halftrace(seed)**2
checked = 0
for i in range(0, 284, 4):
    block = states['states'][0][i:i+4]
    assert all(row['masks'] == block[0]['masks'] for row in block)
    reciprocals = {1 / dec(row['point'][0]) for row in block}
    assert len(reciprocals) == 2
    a, b = [dec(mask << 1) for mask in block[0]['masks']]
    assert sum(reciprocals, F.zero()) == a * b / C
    checked += 1
assert checked == 71

audit = {'status': 'PASS_INDEPENDENT_BRANCH_SPAN_RANKS',
         'rows': rows, 'n41_pair_root_difference_edges': checked,
         'protocol_sha256': sha(HERE / 'branch_rank_protocol.json'),
         'producer_result_sha256': sha(HERE / 'branch_rank_result.json'),
         'source_states_sha256': sha(ROOT / 'n41_n131_fivepair_w9_w29_20261017/n41_states.json'),
         'auditor_sha256': sha(Path(__file__)),
         'runtime_sha256': sha(HERE / 'sage_runtime_info.json')}
with (HERE / 'branch_rank_audit.json').open('x') as out:
    json.dump(audit, out, sort_keys=True, indent=2)
    out.write('\n')
print(json.dumps({'status': audit['status'], 'rows': rows,
                  'n41_pair_root_difference_edges': checked}))
