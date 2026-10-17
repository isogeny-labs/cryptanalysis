"""Independent Sage rank audit for all 17 N41 quotient code labels."""
import hashlib
import itertools
import json
from pathlib import Path

from sage.all import GF, PolynomialRing, matrix, vector

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


protocol = json.loads((HERE / 'quotient_label_protocol.json').read_text())
result = json.loads((HERE / 'quotient_label_result.json').read_text())
source = json.loads((HERE / 'aligned_states.json').read_text())
assert result['status'] == 'PASS_EXACT_N41_QUOTIENT_CODE_LABEL_SCREEN'
assert result['protocol_sha256'] == sha(HERE / 'quotient_label_protocol.json')
assert protocol['source_sha256']['script'] == sha(HERE / 'screen_n41_quotient_labels.py')
assert protocol['source_sha256']['states'] == sha(HERE / 'aligned_states.json')

R = PolynomialRing(GF(2), 'u')
u = R.gen()
F = GF(2**41, name='u', modulus=u**41 + u**3 + 1)


def dec(word):
    return F(R([(int(word) >> i) & 1 for i in range(41)]))


def enc(value):
    return sum(int(coefficient) << index
               for index, coefficient in enumerate(value.polynomial().list()))


def parity(value):
    return int(value.bit_count() & 1)


halftrace = lambda a: sum((a**(1 << (2 * i)) for i in range(21)), F.zero())
seed = dec(source['seed'] << 1)
C = 1 + halftrace(seed)**2
bits = [bit for bit in range(9) if bit != source['seed'].bit_length() - 1]
diff = [(dec(1 << (bit + 1))**2 + seed * dec(1 << (bit + 1))) / C
        for bit in bits]
branch_vectors = [enc(value**(1 << rotation))
                  for rotation in (0, 12, 24) for value in diff]
duals = [int(row['dual_mask']) for row in result['rows']]
assert len(duals) == 17
assert all(parity(dual & vec) == 0 for dual in duals for vec in branch_vectors)
assert matrix(GF(2), 41, 17,
              lambda i, j: (duals[j] >> i) & 1).rank() == 17

codes, roots = [], []
for index in range(0, 284, 4):
    block = source['states'][0][index:index + 4]
    mask = block[0]['masks'][0]
    code = sum(((mask >> bit) & 1) << i for i, bit in enumerate(bits))
    zs = sorted({enc(1 / dec(row['point'][0])) for row in block})
    assert len(zs) == 2
    codes.append(code)
    roots.append(zs)
assert len(codes) == len(set(codes)) == 71
monomials = [sum(1 << bit for bit in subset)
             for degree in range(3)
             for subset in itertools.combinations(range(8), degree)]
assert len(monomials) == 37
features = matrix(GF(2), 71, len(monomials),
                  lambda i, j: int(codes[i] & monomials[j] == monomials[j]))
base_rank = int(features.rank())
assert base_rank == 37
augmented_ranks = []
for row in result['rows']:
    dual = int(row['dual_mask'])
    labels = [parity(dual & zpair[0]) for zpair in roots]
    assert all(parity(dual & zpair[0]) == parity(dual & zpair[1])
               for zpair in roots)
    assert sum(labels) == row['ones']
    augmented = features.augment(matrix(GF(2), 71, 1,
                                       lambda i, j: labels[i]))
    augmented_ranks.append(int(augmented.rank()))
assert augmented_ranks == [38] * 17
audit = {'status': 'PASS_INDEPENDENT_N41_QUOTIENT_LABEL_DEGREE2_EXCLUSION',
         'source_codes': len(codes), 'quotient_dimension': len(duals),
         'quadratic_feature_count': len(monomials), 'feature_rank': base_rank,
         'augmented_ranks': augmented_ranks,
         'protocol_sha256': sha(HERE / 'quotient_label_protocol.json'),
         'producer_result_sha256': sha(HERE / 'quotient_label_result.json'),
         'auditor_sha256': sha(Path(__file__)),
         'runtime_sha256': sha(HERE / 'sage_runtime_info.json')}
with (HERE / 'quotient_label_audit.json').open('x') as out:
    json.dump(audit, out, sort_keys=True, indent=2)
    out.write('\n')
print(json.dumps({'status': audit['status'], 'source_codes': len(codes),
                  'quadratic_feature_rank': base_rank,
                  'all_augmented_ranks': sorted(set(augmented_ranks))}))
