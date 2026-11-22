"""Independent Sage roots and matrix-nullspace replay for N131 labels."""
import hashlib
import json
import time
from pathlib import Path

from sage.all import GF, PolynomialRing, matrix

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


start = time.monotonic()
producer = json.loads((HERE / 'n131_result.json').read_text())
protocol = json.loads((HERE / 'n131_sage_protocol.json').read_text())
assert producer['status'] == 'PASS_SAMPLED_N131_DEGREE_TWO_EXCLUSION'
assert producer['source_sha256']['script'] == protocol['source_sha256']['script']

R = PolynomialRing(GF(2), 'u')
u = R.gen()
F = GF(2**131, name='u', modulus=u**131 + u**13 + u**2 + u + 1)
Z = PolynomialRing(F, 'z')
z = Z.gen()


def dec(word):
    return F(R([(int(word) >> i) & 1 for i in range(131)]))


def enc(value):
    return sum(int(c) << i for i, c in enumerate(value.polynomial().list()))


bits = [i for i in range(29) if i != (898618).bit_length() - 1]
assert len(bits) == 28
seed = dec(898618 << 1)
assert seed.trace() == 0
h = F.zero()
v = seed
for _ in range(66):
    h += v
    v = v**4
assert h**2 + h == seed
H, C = h**2, 1+h**2
duals = producer['dual_masks']
assert len(duals) == 47
codes, labels = producer['codes'], producer['labels']
assert len(codes) == len(labels) == 512 and len(set(codes)) == 512
root_checks = 0
for code, root, label in zip(codes, producer['roots'], labels):
    mask = sum((1 << bit) for index, bit in enumerate(bits) if code >> index & 1)
    a = dec(mask << 1)
    b = a + seed
    assert a and b and (1/a).trace() == 0 and (1/b).trace() == 0
    product = a*b
    poly = C*z**2 + product*z + H
    roots = [value for value, mult in poly.roots() for _ in range(mult)]
    assert len(roots) == 2 and roots[0] != roots[1]
    assert root in {enc(value) for value in roots}
    for value in roots:
        word = enc(value)
        projected = sum(((word & dual).bit_count() & 1) << i
                        for i, dual in enumerate(duals))
        assert projected == label
        root_checks += 1

K = GF(2)
feature_rows = []
for code in codes:
    row = [1]
    row.extend((code >> i) & 1 for i in range(28))
    row.extend(((code >> i) & 1) & ((code >> j) & 1)
               for i in range(28) for j in range(i+1, 28))
    assert len(row) == 407
    feature_rows.append(row)
features = matrix(K, feature_rows)
assert features.rank() == 407
label_matrix = matrix(K, [[(value >> i) & 1 for i in range(47)] for value in labels])
nullspace = features.left_kernel().basis_matrix()
assert nullspace.nrows() == 105
syndromes = nullspace * label_matrix
nonzero = [any(int(x) for x in syndromes.column(i)) for i in range(47)]
assert all(nonzero)
result = {
    'status': 'PASS_INDEPENDENT_N131_ROOTS_AND_DEGREE_TWO_EXCLUSION',
    'source_codes': len(codes), 'root_checks': root_checks,
    'quadratic_feature_rank': features.rank(),
    'left_nullity': nullspace.nrows(),
    'labels_with_nonzero_syndrome': sum(nonzero),
    'elapsed_seconds': time.monotonic() - start,
    'source_sha256': {'script': sha(Path(__file__)),
                      'producer': sha(HERE / 'n131_result.json'),
                      'protocol': sha(HERE / 'n131_sage_protocol.json'),
                      'runtime': sha(HERE / 'sage_runtime_info.json')},
}
(HERE / 'n131_audit_result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps(result, sort_keys=True))
