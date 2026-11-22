#!/usr/bin/env python3
"""Bounded complex-fiber diagnostic for the repeated-product quotient.

This does not construct the finite-field NIST quotient.  It takes an explicit
Lagrangian K in E[3]^3, derives a quotient period matrix for several complex
elliptic periods, and numerically counts vanishing even theta constants.  All
36 nonzero even theta constants are the genus-3 non-hyperelliptic pattern.
"""

from __future__ import annotations

import argparse
import importlib.util
import itertools
import json
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location("nist_333", ROOT / "src" / "nist_333.py")
nist = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["nist_333"] = nist
SPEC.loader.exec_module(nist)


def inverse_mod3(matrix):
    size = len(matrix)
    augmented = [
        [x % 3 for x in row] + [int(i == j) for j in range(size)]
        for i, row in enumerate(matrix)
    ]
    for col in range(size):
        pivot = next(i for i in range(col, size) if augmented[i][col])
        augmented[col], augmented[pivot] = augmented[pivot], augmented[col]
        scale = pow(augmented[col][col], -1, 3)
        augmented[col] = [(scale * x) % 3 for x in augmented[col]]
        for row in range(size):
            if row != col and augmented[row][col]:
                scale = augmented[row][col]
                augmented[row] = [
                    (x - scale * y) % 3
                    for x, y in zip(augmented[row], augmented[col])
                ]
    return [row[size:] for row in augmented]


def graph_matrix(matrix):
    """Write row(K) as row([I|S]) in grouped P/Q coordinates."""
    p_part = [[row[0], row[2], row[4]] for row in matrix]
    q_part = [[row[1], row[3], row[5]] for row in matrix]
    p_inverse = inverse_mod3(p_part)
    result = nist.matmul(p_inverse, q_part)
    if result != nist.transpose(result):
        raise ValueError("isotropic graph must be symmetric")
    return result


def symmetric_integer_lift(matrix):
    return [[-1 if x % 3 == 2 else x % 3 for x in row] for row in matrix]


def quotient_period_matrix(matrix, tau):
    """Return Omega'=3*tau*(I+tau*S)^(-1) for K=row([I|S])."""
    s = np.array(symmetric_integer_lift(graph_matrix(matrix)), dtype=complex)
    omega = 3 * tau * np.linalg.inv(np.eye(3, dtype=complex) + tau * s)
    if np.max(np.abs(omega - omega.T)) > 1e-11:
        raise ValueError("period matrix is not symmetric")
    return omega


def lattice_points(characteristic_a, cutoff):
    # For a_i=1, [-N,N-1] is invariant under n -> -n-1.  This preserves the
    # exact odd-theta cancellation much better than an asymmetric truncation.
    ranges = [
        range(-cutoff, cutoff) if bit else range(-cutoff, cutoff + 1)
        for bit in characteristic_a
    ]
    return np.array(list(itertools.product(*ranges)), dtype=float)


def theta_constant(a, b, omega, cutoff):
    vectors = lattice_points(a, cutoff) + np.array(a, dtype=float) / 2
    quadratic = np.einsum("ni,ij,nj->n", vectors, omega, vectors)
    linear = vectors @ np.array(b, dtype=float)
    return np.exp(np.pi * 1j * (quadratic + linear)).sum()


def diagnose(matrix, tau, cutoff=6, zero_threshold=1e-8):
    omega = quotient_period_matrix(matrix, tau)
    eigenvalues = np.linalg.eigvalsh(omega.imag)
    if eigenvalues.min() <= 0:
        raise ValueError("period matrix is outside Siegel upper half-space")
    rows = []
    max_delta = 0.0
    for a in itertools.product(range(2), repeat=3):
        for b in itertools.product(range(2), repeat=3):
            value = theta_constant(a, b, omega, cutoff)
            previous = theta_constant(a, b, omega, cutoff - 1)
            delta = abs(value - previous)
            max_delta = max(max_delta, delta)
            rows.append(
                {
                    "a": list(a),
                    "b": list(b),
                    "parity": "odd" if sum(x * y for x, y in zip(a, b)) % 2 else "even",
                    "absolute_value": float(abs(value)),
                    "cutoff_delta": float(delta),
                }
            )
    even = [row for row in rows if row["parity"] == "even"]
    odd = [row for row in rows if row["parity"] == "odd"]
    return {
        "tau": {"real": tau.real, "imag": tau.imag},
        "graph_matrix_mod_3": graph_matrix(matrix),
        "symmetric_integer_lift": symmetric_integer_lift(graph_matrix(matrix)),
        "quotient_period_matrix": [
            [{"real": z.real, "imag": z.imag} for z in row] for row in omega
        ],
        "imaginary_part_eigenvalues": [float(x) for x in eigenvalues],
        "cutoff": cutoff,
        "max_cutoff_delta": max_delta,
        "zero_threshold": zero_threshold,
        "even_nonzero_count": sum(row["absolute_value"] > zero_threshold for row in even),
        "even_min_absolute_value": min(row["absolute_value"] for row in even),
        "odd_max_absolute_value": max(row["absolute_value"] for row in odd),
        "classification": "non-hyperelliptic theta-null pattern"
        if sum(row["absolute_value"] > zero_threshold for row in even) == 36
        else "not the 36-even-nonzero pattern",
    }


def build():
    periods = [0.17 + 1.3j, -0.23 + 1.1j, 0.31 + 1.7j]
    kernels = {
        "shared_p224_p256_kernel": nist.KERNEL_MATRIX,
        "p224_zero_diagonal_incidence_alternate": nist.P224_ZERO_DIAGONAL_INCIDENCE_KERNEL_MATRIX,
    }
    return {
        "format": "complex-theta-diagnostic-v1",
        "evidence_label": "bounded numerical complex-fiber diagnostic; not a finite-field construction or proof",
        "derivation": "For K=row([I|S]) in E_tau[3]^3, a symplectic basis of the quotient lattice gives Omega'=3*tau*(I+tau*S)^(-1).",
        "interpretation": "All sampled fibers have 36 nonzero even theta constants, so repeated E^3 and these kernels are not generically forced to decompose or be hyperelliptic. Finite-field NIST reconstruction and descent remain open.",
        "kernels": {
            name: {
                "generator_matrix_mod_3": matrix,
                "runs": [diagnose(matrix, tau) for tau in periods],
            }
            for name, matrix in kernels.items()
        },
        "dependencies": {"numpy": np.__version__},
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = build()
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(encoded)
    else:
        print(encoded, end="")


if __name__ == "__main__":
    main()
