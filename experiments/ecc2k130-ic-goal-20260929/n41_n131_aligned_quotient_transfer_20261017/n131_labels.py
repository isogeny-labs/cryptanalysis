"""Frozen sampled lower bound on Boolean degree of N131 quotient labels."""
import hashlib
import importlib.util
import itertools
import json
import random
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
DESIGN = HERE.parent / 'n41_n131_fivepair_w9_w29_20261017/circuit_n131_3p2.py'
COUNT = 512
SEED = 202610171856


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rank_basis(values):
    pivots = {}
    for v in values:
        while v:
            k = v.bit_length() - 1
            if k not in pivots:
                pivots[k] = v
                break
            v ^= pivots[k]
    return pivots


def dual_basis(values, n):
    rows = rank_basis(values)
    duals = []
    for bit in range(n):
        if bit in rows:
            continue
        v = 1 << bit
        for pivot in sorted(rows):
            if (v & rows[pivot]).bit_count() & 1:
                v |= 1 << pivot
        assert all(not ((v & x).bit_count() & 1) for x in values)
        duals.append(v)
    return duals


def run():
    start = time.monotonic()
    spec = importlib.util.spec_from_file_location('n131_label_design', DESIGN)
    design = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(design)
    F = design.F
    inverse_C = F.inverse(design.C)
    diff = [F.mul(v, inverse_C) for v in design.PB]
    duals = dual_basis([F.frob(v, r) for r in (0, 36, 72) for v in diff], 131)
    assert len(duals) == 47
    monomials = [sum(1 << bit for bit in subset)
                 for d in range(3) for subset in itertools.combinations(range(28), d)]
    assert len(monomials) == 407
    rng = random.Random(SEED)
    codes, roots, labels = [], [], []
    seen = set()
    draws = 0
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
        if design.previous.trace(F.inverse(a)) or design.previous.trace(F.inverse(b)):
            continue
        # z=(p/C)*u, where u^2+u=H*C/p^2.
        rhs = F.mul(F.mul(design.H, design.C), F.inverse(F.square(p)))
        if design.previous.trace(rhs):
            continue
        u = design.previous.halftrace(rhs)
        z0 = F.mul(F.mul(p, inverse_C), u)
        z1 = z0 ^ F.mul(p, inverse_C)
        assert z0 and z1 and z0 != z1
        assert F.mul(design.C, F.square(z0)) ^ F.mul(p, z0) ^ design.H == 0
        assert F.mul(design.C, F.square(z1)) ^ F.mul(p, z1) ^ design.H == 0
        label0 = sum(((z0 & v).bit_count() & 1) << i for i, v in enumerate(duals))
        label1 = sum(((z1 & v).bit_count() & 1) << i for i, v in enumerate(duals))
        assert label0 == label1
        codes.append(code)
        roots.append(z0)
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
        'source_sha256': {'script': sha(Path(__file__)), 'design': sha(DESIGN)},
    }
    assert result['feature_rank'] == 407 and result['all_labels_contradicted']
    (HERE / 'n131_result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in (
        'status', 'samples', 'random_draws', 'feature_rank',
        'residual_rows', 'all_labels_contradicted', 'elapsed_seconds')}))


if __name__ == '__main__':
    run()
