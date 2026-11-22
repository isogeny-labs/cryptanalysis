"""Checked-Sage N131 source-code quotient-label degree screen."""
import hashlib
import importlib.util
import itertools
import json
import random
import time
from pathlib import Path

from sage.all import GF, PolynomialRing

from n131_labels import dual_basis

HERE = Path(__file__).resolve().parent
DESIGN = HERE.parent / 'n41_n131_fivepair_w9_w29_20261017/circuit_n131_3p2.py'
COUNT = 512
SEED = 202610171856


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


spec = importlib.util.spec_from_file_location('n131_label_design_sage', DESIGN)
design = importlib.util.module_from_spec(spec)
spec.loader.exec_module(design)
R = PolynomialRing(GF(2), 'u')
u = R.gen()
F = GF(2**131, name='u', modulus=u**131 + u**13 + u**2 + u + 1)


def dec(word):
    return F(R([(int(word) >> i) & 1 for i in range(131)]))


def enc(value):
    return sum(int(coefficient) << i for i, coefficient in enumerate(value.polynomial().list()))


def halftrace(value):
    initial = value
    out = F.zero()
    for _ in range(66):
        out += value
        value = value**4
    assert out**2 + out == initial
    return out


start = time.monotonic()
inverse_C = design.F.inverse(design.C)
diff = [design.F.mul(v, inverse_C) for v in design.PB]
duals = dual_basis([design.F.frob(v, r) for r in (0, 36, 72) for v in diff], 131)
assert len(duals) == 47
monomials = [sum(1 << bit for bit in subset)
             for d in range(3) for subset in itertools.combinations(range(28), d)]
assert len(monomials) == 407
rng = random.Random(SEED)
codes, roots, labels = [], [], []
seen = set()
draws = 0
C, H = dec(design.C), dec(design.H)
while len(codes) < COUNT:
    code = rng.getrandbits(28)
    draws += 1
    if not code or code in seen:
        continue
    seen.add(code)
    a = 0
    p = 0
    for i in range(28):
        if code >> i & 1:
            a ^= design.BASE[i]
            p ^= design.PB[i]
    b = a ^ design.SEED
    if not a or not b or not p:
        continue
    a_f, b_f, p_f = dec(a), dec(b), dec(p)
    if (a_f**-1).trace() or (b_f**-1).trace():
        continue
    rhs = H*C/(p_f**2)
    if rhs.trace():
        continue
    z0 = (p_f/C)*halftrace(rhs)
    z1 = z0 + p_f/C
    assert z0 and z1 and z0 != z1
    assert C*z0**2 + p_f*z0 + H == 0
    assert C*z1**2 + p_f*z1 + H == 0
    z0_i, z1_i = enc(z0), enc(z1)
    label0 = sum(((z0_i & v).bit_count() & 1) << i for i, v in enumerate(duals))
    label1 = sum(((z1_i & v).bit_count() & 1) << i for i, v in enumerate(duals))
    assert label0 == label1
    codes.append(code)
    roots.append(z0_i)
    labels.append(label0)

basis = {}
contradiction_mask = 0
residual_count = 0
for code, label in zip(codes, labels):
    row = sum(1 << i for i, monomial in enumerate(monomials)
              if code & monomial == monomial)
    value = label
    while row:
        pivot = row.bit_length() - 1
        if pivot not in basis:
            basis[pivot] = (row, value)
            break
        old_row, old_value = basis[pivot]
        row ^= old_row
        value ^= old_value
    if not row:
        residual_count += 1
        contradiction_mask |= value
result = {
    'status': 'PASS_SAMPLED_N131_DEGREE_TWO_EXCLUSION',
    'samples': COUNT, 'random_draws': draws, 'random_seed': SEED,
    'code_bit_width': 28, 'feature_count': len(monomials),
    'feature_rank': len(basis), 'residual_rows': residual_count,
    'quotient_dimension': len(duals), 'contradicted_label_mask': contradiction_mask,
    'all_labels_contradicted': contradiction_mask == (1 << len(duals)) - 1,
    'dual_masks': duals, 'codes': codes, 'roots': roots, 'labels': labels,
    'elapsed_seconds': time.monotonic() - start,
    'source_sha256': {'script': sha(Path(__file__)), 'design': sha(DESIGN),
                      'runtime': sha(HERE / 'sage_runtime_info.json')},
}
assert result['feature_rank'] == 407 and result['all_labels_contradicted']
(HERE / 'n131_result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps({key: result[key] for key in (
    'status', 'samples', 'random_draws', 'feature_rank',
    'residual_rows', 'all_labels_contradicted', 'elapsed_seconds')}))
