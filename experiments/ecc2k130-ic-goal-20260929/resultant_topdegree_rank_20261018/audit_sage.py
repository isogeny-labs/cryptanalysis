"""Independent Sage field and GF(2)-matrix replay of top-degree ranks."""
import hashlib
import json
from pathlib import Path

from sage.all import GF, PolynomialRing, matrix

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
cfg = json.loads((HERE / 'audit_protocol.json').read_text())
for path, expected in cfg['sources'].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path
saved = json.loads((HERE / 'result.json').read_text())
assert saved['status'] == 'COMPLETE_RESULTANT_TOPDEGREE_RANK'


def field(degree):
    P = PolynomialRing(GF(2), 'u')
    u = P.gen()
    modulus = u**41 + u**3 + 1 if degree == 41 else u**131 + u**13 + u**2 + u + 1
    K = GF(2**degree, name='u', modulus=modulus)
    def dec(n):
        return K(P([(n >> i) & 1 for i in range(degree)]))
    def enc(v):
        return sum(int(bit) << i for i, bit in enumerate(v.polynomial().list()))
    return K, dec, enc


def rank(values, degree):
    return int(matrix(GF(2), len(values), degree,
                      lambda i, j: (values[i] >> j) & 1).rank())


rows = []
for degree in (41, 131):
    K, dec, enc = field(degree)
    if degree == 41:
        seed, bits, rotations = dec(112), [0, 1, 2, 3, 4, 6, 7, 8, 9, 10], (12, 24)
    else:
        seed_mask = 898618
        seed = dec(seed_mask << 1)
        bits = [i for i in range(33) if i != seed_mask.bit_length()-1]
        rotations = (0, 18)
    base = [dec(1 << (i + 1)) for i in bits]
    raw = [a*(a+seed) for a in base]
    first = [a**(1 << rotations[0]) for a in raw]
    second = [a**(1 << rotations[1]) for a in raw]
    first_pairs = {(i,j): first[i]**2*first[j] + first[i]*first[j]**2
                   for i in range(len(bits)) for j in range(i+1,len(bits))}
    second_pairs = {(i,j): second[i]**2*second[j] + second[i]*second[j]**2
                    for i in range(len(bits)) for j in range(i+1,len(bits))}
    second_values = [enc(v) for v in second_pairs.values()]
    qrank = rank(second_values, degree)
    for saved_row in [r for r in saved['rows'] if r['field_degree'] == degree]:
        assert saved_row['q_pair_rank'] == qrank
        assert saved_row['p_first_pair_coefficient'] == enc(first_pairs[(0,1)])
        for pivot in saved_row['q_pair_pivots']:
            i,j = pivot['label']
            assert enc(second_pairs[(i,j)]) == pivot['value']
        block_ranks = []
        c33 = dec(saved_row['c33'])
        for block in saved_row['block_ranks']:
            k = block['first_free_bits']
            values = [enc(c33*a*b)
                      for (i,j),a in first_pairs.items() if j < k
                      for b in second_pairs.values()]
            actual = rank(values, degree)
            assert actual == block['coefficient_rank']
            assert len(values) == block['quartic_monomials']
            block_ranks.append([k, actual])
        rows.append({'field_degree': degree, 'target_index': saved_row['target_index'],
                     'q_pair_rank': qrank, 'block_ranks': block_ranks})
out = {'status': 'PASS_INDEPENDENT_SAGE_TOPDEGREE_RANK',
       'candidate_id': None, 'rows': rows,
       'protocol_sha256': hashlib.sha256((HERE / 'audit_protocol.json').read_bytes()).hexdigest()}
(HERE / 'audit_result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
print(json.dumps(out, sort_keys=True))
