"""Independently compare the old cubic ANF after x0=1 with the new ANF."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
cfg = json.loads((HERE / 'protocol.json').read_text())
for path, digest in cfg['sources'].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest, path

degree = 131
modulus = (1 << 131) | (1 << 13) | (1 << 2) | (1 << 1) | 1
mask = (1 << degree) - 1


def mul(a, b):
    # Carryless polynomial product, then highest-bit-first reduction.
    raw = 0
    while b:
        low = b & -b
        raw ^= a << (low.bit_length() - 1)
        b ^= low
    while raw.bit_length() > degree:
        raw ^= modulus << (raw.bit_length() - degree - 1)
    return raw


def sq(a):
    return mul(a, a)


def frob(a, steps):
    for _ in range(steps):
        a = sq(a)
    return a


def add_term(out, monomial, coefficient):
    value = out.get(monomial, 0) ^ coefficient
    if value:
        out[monomial] = value
    else:
        out.pop(monomial, None)


def product(a, b):
    out = {}
    for am, av in a.items():
        for bm, bv in b.items():
            add_term(out, am | bm, mul(av, bv))
    return out


def square(a):
    return {m: sq(v) for m, v in a.items()}


def powers(a):
    a2 = square(a)
    return [{0: 1}, a, a2, product(a, a2), square(a2)]


source = json.loads((ROOT / 'n131_w33_freecode_resultant_20261018/coefficients.json').read_text())
seed_mask = 898618
seed = seed_mask << 1
positions = [i for i in range(33) if i != seed_mask.bit_length() - 1]
assert len(positions) == 32
pb = []
qb = []
for pos in positions:
    a = 1 << (pos + 1)
    value = sq(a) ^ mul(seed, a)
    pb.append(value)
    qb.append(frob(value, 18))


def build(terms, fixed_bit):
    if fixed_bit:
        p = {0: pb[0]}
        for i in range(3):
            p[1 << i] = pb[i + 1]
        q = {1 << (3 + i): value for i, value in enumerate(qb) if value}
    else:
        p = {1 << i: pb[i] for i in range(4)}
        q = {1 << (4 + i): value for i, value in enumerate(qb) if value}
    pp, qq = powers(p), powers(q)
    resultant = {}
    for i, j, coefficient in terms:
        for monomial, value in product(pp[i], qq[j]).items():
            add_term(resultant, monomial, mul(coefficient, value))
    return product(resultant, p)


def canonical_digest(anf):
    stream = ''.join(f'{m}:{v}\n' for m, v in sorted(anf.items())).encode()
    return hashlib.sha256(stream).hexdigest()


rows = []
for index in (0, 1):
    terms = [(int(i), int(j), int(c)) for i, j, c in source['rows'][index]['terms']]
    old = build(terms, fixed_bit=False)
    new = build(terms, fixed_bit=True)
    substituted = {}
    for monomial, coefficient in old.items():
        add_term(substituted, monomial >> 1, coefficient)
    assert substituted == new
    assert len(old) == 2314 and len(new) == 2215
    assert max(bin(m).count('1') for m in new) == 3
    rows.append({'target_index': index, 'old_anf_monomials': len(old),
                 'new_anf_monomials': len(new),
                 'substitution_exact': True,
                 'new_anf_sha256': canonical_digest(new)})

out = {'status': 'PASS_EXACT_FIXED_BIT_CUBIC_ANF_IDENTITY',
       'candidate_id': None, 'curve_id': cfg['curve_id'], 'rows': rows,
       'source_protocol_sha256': hashlib.sha256((HERE / 'protocol.json').read_bytes()).hexdigest()}
with (HERE / 'anf_audit_result.json').open('x') as stream:
    json.dump(out, stream, sort_keys=True, indent=2)
    stream.write('\n')
print(out['status'])
