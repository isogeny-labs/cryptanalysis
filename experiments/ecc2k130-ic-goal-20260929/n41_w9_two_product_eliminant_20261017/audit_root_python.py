"""Independent integer-polynomial replay of the N41 root-subspace result."""
import hashlib
import json
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / 'n41_n131_w29_rotation_alignment_20261017/aligned_states.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


protocol = json.loads((HERE / 'root_python_audit_protocol.json').read_text())
for name, path in {
    'script': Path(__file__), 'states': SOURCE,
    'eliminant': HERE / 'result.json',
    'root_probe': HERE / 'root_probe_result_v2.json',
}.items():
    assert sha(path) == protocol['source_sha256'][name], name
assert not (HERE / 'root_python_audit_result.json').exists()

source = json.loads(SOURCE.read_text())
producer = json.loads((HERE / 'result.json').read_text())
probe = json.loads((HERE / 'root_probe_result_v2.json').read_text())
mask41 = (1 << 41) - 1


def mul(a, b):
    out = 0
    while b:
        if b & 1:
            out ^= a
        b >>= 1
        a <<= 1
        if a & (1 << 41):
            a ^= (1 << 41) | (1 << 3) | 1
    return out & mask41


def square(a):
    return mul(a, a)


def rotate(a, k):
    for _ in range(k):
        a = square(a)
    return a


seed = source['seed'] << 1


def product(code_mask):
    a = code_mask << 1
    return mul(a, a ^ seed)


basis = [rotate(product(1 << i), 12) for i in range(9) if i != 5]
span = {0}
for v in basis:
    span |= {x ^ v for x in tuple(span)}
assert len(span) == 256

coefficients = probe['linearized_coefficients']
assert len(coefficients) == 9 and coefficients[-1] == 1
for x in span:
    z = x
    check = 0
    for c in coefficients:
        check ^= mul(c, z)
        z = square(z)
    assert check == 0

left = [product(source['states'][1][4 * i]['masks'][0]) for i in range(71)]
right = [rotate(product(source['states'][2][4 * i]['masks'][0]), 12)
         for i in range(71)]
assert len(set(left)) == len(set(right)) == 71
assert set(right) <= span

terms = producer['eliminant_terms']


def powers(x):
    out = [1]
    for _ in range(4):
        out.append(mul(out[-1], x))
    return out


def specialize(p):
    pp = powers(p)
    coefficients = [0] * 5
    for (i, j), c in terms:
        coefficients[j] ^= mul(c, pp[i])
    return coefficients


def evaluate(coefficients, q):
    qp = powers(q)
    out = 0
    for c, x in zip(coefficients, qp):
        out ^= mul(c, x)
    return out


start = time.monotonic()
lookup = {q: j for j, q in enumerate(right)}
hits = []
field_roots = []
for i, p in enumerate(left):
    poly = specialize(p)
    for q in span:
        if evaluate(poly, q) == 0:
            field_roots.append([i, q])
            if q in lookup:
                hits.append([i, lookup[q]])
assert hits == producer['algebraic_zero_code_pairs'] == [[61, 16]]
assert len(field_roots) == 1
assert all(run['subspace_field_roots'] == 1 and run['valid_code_hits'] == hits
           for run in probe['runs'])

result = {
    'status': 'PASS_PURE_PYTHON_N41_ROOT_SUBSPACE_REPLAY',
    'field_modulus': [41, 3, 0],
    'span_size': len(span),
    'first_code_count': len(left),
    'evaluations': len(left) * len(span),
    'field_roots': field_roots,
    'valid_code_hits': hits,
    'elapsed_seconds': time.monotonic() - start,
    'protocol_sha256': sha(HERE / 'root_python_audit_protocol.json'),
}
(HERE / 'root_python_audit_result.json').write_text(
    json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps({'status': result['status'], 'field_roots': field_roots,
                  'elapsed_seconds': result['elapsed_seconds']}))
