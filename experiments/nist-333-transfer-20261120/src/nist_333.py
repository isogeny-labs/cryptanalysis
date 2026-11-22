#!/usr/bin/env python3
"""Reproduce the NIST P-224/P-256 (3,3,3)-kernel eligibility result.

This module deliberately stops before solving a discrete logarithm.  It builds
exact 3-torsion points in small extension fields, certifies a maximal isotropic
kernel in E[3]^3, and emits a transfer-assessment evidence bundle.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
import os
import platform
import subprocess
import sys
import time
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import sympy
from sympy.utilities.exceptions import SymPyDeprecationWarning


def h(value: str) -> int:
    return int(value.replace(" ", "").replace("\n", ""), 16)


CURVES = {
    "P-224": {
        "openssl": "secp224r1",
        "p": h("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF000000000000000000000001"),
        "a": h("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFE"),
        "b": h("B4050A850C04B3ABF54132565044B0B7D7BFD8BA270B39432355FFB4"),
        "n": h("FFFFFFFFFFFFFFFFFFFFFFFFFFFF16A2E0B8F03E13DD29455C5C2A3D"),
    },
    "P-256": {
        "openssl": "prime256v1",
        "p": h("FFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF"),
        "a": h("FFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFC"),
        "b": h("5AC635D8AA3A93E7B3EBBD55769886BC651D06B0CC53B0F63BCE3C3E27D2604B"),
        "n": h("FFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551"),
    },
}


CONTROL_PROFILES = {
    # (p mod 3, t mod 3); values are independently rechecked with OpenSSL.
    "P-192": (2, 1),
    "P-224": (1, 1),
    "P-256": (1, 1),
    "P-384": (2, 2),
    "P-521": (1, 0),
}


OPENSSL_NAMES = {
    "P-192": "prime192v1",
    "P-224": "secp224r1",
    "P-256": "prime256v1",
    "P-384": "secp384r1",
    "P-521": "secp521r1",
}


class FFContext:
    """Prime field or monogenic extension F_p[z]/(modulus)."""

    def __init__(self, p: int, modulus: Sequence[int]):
        self.p = int(p)
        self.modulus = tuple(int(c) % p for c in modulus)
        if len(self.modulus) < 2 or self.modulus[-1] != 1:
            raise ValueError("modulus must be monic and have positive degree")
        self.degree = len(self.modulus) - 1
        self.order = p**self.degree

    def e(self, value=0) -> "FFE":
        if isinstance(value, FFE):
            if value.ctx is not self:
                raise TypeError("field mismatch")
            return value
        if isinstance(value, int):
            coeffs = [value]
        else:
            coeffs = list(value)
        coeffs += [0] * (self.degree - len(coeffs))
        if len(coeffs) != self.degree:
            raise ValueError("wrong coefficient length")
        return FFE(self, tuple(c % self.p for c in coeffs))

    @property
    def zero(self) -> "FFE":
        return self.e(0)

    @property
    def one(self) -> "FFE":
        return self.e(1)


@dataclass(frozen=True)
class FFE:
    ctx: FFContext
    coeffs: tuple[int, ...]

    def _coerce(self, other) -> "FFE":
        return self.ctx.e(other)

    def __add__(self, other):
        other = self._coerce(other)
        return self.ctx.e([(a + b) % self.ctx.p for a, b in zip(self.coeffs, other.coeffs)])

    __radd__ = __add__

    def __neg__(self):
        return self.ctx.e([(-a) % self.ctx.p for a in self.coeffs])

    def __sub__(self, other):
        return self + (-self._coerce(other))

    def __rsub__(self, other):
        return self._coerce(other) - self

    def __mul__(self, other):
        other = self._coerce(other)
        d, p = self.ctx.degree, self.ctx.p
        tmp = [0] * (2 * d - 1)
        for i, a in enumerate(self.coeffs):
            for j, b in enumerate(other.coeffs):
                tmp[i + j] = (tmp[i + j] + a * b) % p
        for k in range(len(tmp) - 1, d - 1, -1):
            c = tmp[k] % p
            if c:
                for j in range(d):
                    tmp[k - d + j] = (tmp[k - d + j] - c * self.ctx.modulus[j]) % p
        return self.ctx.e(tmp[:d])

    __rmul__ = __mul__

    def __pow__(self, exponent: int):
        if exponent < 0:
            return (self.inverse()) ** (-exponent)
        result, base = self.ctx.one, self
        while exponent:
            if exponent & 1:
                result = result * base
            base = base * base
            exponent >>= 1
        return result

    def inverse(self):
        if not self:
            raise ZeroDivisionError
        return self ** (self.ctx.order - 2)

    def __truediv__(self, other):
        return self * self._coerce(other).inverse()

    def __rtruediv__(self, other):
        return self._coerce(other) / self

    def __bool__(self):
        return any(self.coeffs)

    def as_json(self):
        return [hex(c) for c in self.coeffs]


class QuadContext:
    """Quadratic extension K[u]/(u^2-r)."""

    def __init__(self, base: FFContext, r: FFE):
        self.base = base
        self.r = base.e(r)
        self.order = base.order**2

    def e(self, a=0, b=0) -> "QE":
        if isinstance(a, QE):
            if a.ctx is not self:
                raise TypeError("field mismatch")
            return a
        return QE(self, self.base.e(a), self.base.e(b))

    @property
    def zero(self):
        return self.e()

    @property
    def one(self):
        return self.e(1)

    @property
    def u(self):
        return self.e(0, 1)


@dataclass(frozen=True)
class QE:
    ctx: QuadContext
    a: FFE
    b: FFE

    def _coerce(self, other):
        return self.ctx.e(other)

    def __add__(self, other):
        other = self._coerce(other)
        return self.ctx.e(self.a + other.a, self.b + other.b)

    __radd__ = __add__

    def __neg__(self):
        return self.ctx.e(-self.a, -self.b)

    def __sub__(self, other):
        return self + (-self._coerce(other))

    def __rsub__(self, other):
        return self._coerce(other) - self

    def __mul__(self, other):
        other = self._coerce(other)
        return self.ctx.e(
            self.a * other.a + self.b * other.b * self.ctx.r,
            self.a * other.b + self.b * other.a,
        )

    __rmul__ = __mul__

    def __pow__(self, exponent: int):
        if exponent < 0:
            return (self.inverse()) ** (-exponent)
        result, base = self.ctx.one, self
        while exponent:
            if exponent & 1:
                result = result * base
            base = base * base
            exponent >>= 1
        return result

    def inverse(self):
        if not self:
            raise ZeroDivisionError
        denom = (self.a * self.a - self.b * self.b * self.ctx.r).inverse()
        return self.ctx.e(self.a * denom, -self.b * denom)

    def __truediv__(self, other):
        return self * self._coerce(other).inverse()

    def __rtruediv__(self, other):
        return self._coerce(other) / self

    def __bool__(self):
        return bool(self.a) or bool(self.b)

    def as_json(self):
        return {"a": self.a.as_json(), "b": self.b.as_json()}


Point = tuple[QE, QE] | None
ProductPoint = tuple[Point, Point, Point]


def ec_neg(point: Point) -> Point:
    return None if point is None else (point[0], -point[1])


def ec_add(left: Point, right: Point, a: QE) -> Point:
    if left is None:
        return right
    if right is None:
        return left
    x1, y1 = left
    x2, y2 = right
    if x1 == x2:
        if y1 == -y2:
            return None
        slope = (3 * x1 * x1 + a) / (2 * y1)
    else:
        slope = (y2 - y1) / (x2 - x1)
    x3 = slope * slope - x1 - x2
    y3 = slope * (x1 - x3) - y1
    return (x3, y3)


def ec_mul(scalar: int, point: Point, a: QE) -> Point:
    if scalar < 0:
        return ec_mul(-scalar, ec_neg(point), a)
    out = None
    base = point
    while scalar:
        if scalar & 1:
            out = ec_add(out, base, a)
        base = ec_add(base, base, a)
        scalar >>= 1
    return out


def point_on_curve(point: Point, a: QE, b: QE) -> bool:
    if point is None:
        return True
    x, y = point
    return y * y == x * x * x + a * x + b


def product_add(left: ProductPoint, right: ProductPoint, a: QE) -> ProductPoint:
    return tuple(ec_add(x, y, a) for x, y in zip(left, right))  # type: ignore[return-value]


def product_mul(scalar: int, point: ProductPoint, a: QE) -> ProductPoint:
    return tuple(ec_mul(scalar, x, a) for x in point)  # type: ignore[return-value]


def product_zero() -> ProductPoint:
    return (None, None, None)


def point_json(point: Point):
    if point is None:
        return None
    return {"x": point[0].as_json(), "y": point[1].as_json()}


def product_json(point: ProductPoint):
    return [point_json(x) for x in point]


def frobenius_point(point: Point, p: int) -> Point:
    if point is None:
        return None
    return (point[0] ** p, point[1] ** p)


def frobenius_product(point: ProductPoint, p: int) -> ProductPoint:
    return tuple(frobenius_point(x, p) for x in point)  # type: ignore[return-value]


def mod_sqrt(value: int, p: int) -> int:
    """Deterministic Tonelli-Shanks square root for odd prime p."""
    value %= p
    if value == 0:
        return 0
    if pow(value, (p - 1) // 2, p) != 1:
        raise ValueError("not a square")
    if p % 4 == 3:
        return pow(value, (p + 1) // 4, p)
    q, s = p - 1, 0
    while q % 2 == 0:
        q //= 2
        s += 1
    z = 2
    while pow(z, (p - 1) // 2, p) != p - 1:
        z += 1
    m, c = s, pow(z, q, p)
    t, r = pow(value, q, p), pow(value, (q + 1) // 2, p)
    while t != 1:
        i, t2 = 1, t * t % p
        while t2 != 1:
            t2 = t2 * t2 % p
            i += 1
        b = pow(c, 1 << (m - i - 1), p)
        r, t, c, m = r * b % p, t * b * b % p, b * b % p, i
    return min(r, p - r)


def psi3_factorization(p: int, a: int, b: int):
    x = sympy.symbols("x")
    poly = sympy.Poly(3 * x**4 + 6 * a * x**2 + 12 * b * x - a * a, x, modulus=p)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SymPyDeprecationWarning)
        unit, factors = sympy.factor_list(poly)
    return int(unit) % p, factors


def linear_root(poly: sympy.Poly, p: int) -> int:
    coeffs = [int(c) % p for c in poly.monic().all_coeffs()]
    if len(coeffs) != 2:
        raise ValueError("not linear")
    return (-coeffs[1]) % p


KERNEL_MATRIX = [
    [1, 0, 0, 1, 0, 1],
    [0, 1, 0, 2, 1, 0],
    [0, 0, 1, 1, 2, 2],
]

# A second P-224 kernel selected from the exhaustive census.  Unlike the
# shared P-224/P-256 kernel above, it has zero intersection with E_v[3] for
# every scalar diagonal E_v={(v1*R,v2*R,v3*R)} indexed by P^2(F_3).  This is a
# stronger repeated-factor diagnostic, but is not by itself an
# indecomposability proof.
P224_ZERO_DIAGONAL_INCIDENCE_KERNEL_MATRIX = [
    [1, 0, 0, 0, 0, 1],
    [0, 1, 0, 1, 1, 0],
    [0, 0, 1, 1, 0, 1],
]


def matrix_kernel_generators(P: Point, Q: Point, a: QE, matrix=KERNEL_MATRIX) -> list[ProductPoint]:
    out = []
    basis = [P, Q, P, Q, P, Q]
    for row in matrix:
        coords = []
        for block in range(3):
            value = None
            for j in range(2):
                value = ec_add(value, ec_mul(row[2 * block + j], basis[2 * block + j], a), a)
            coords.append(value)
        out.append(tuple(coords))
    return out


def kernel_elements(generators: Sequence[ProductPoint], a: QE) -> list[ProductPoint]:
    out = []
    for coeffs in itertools.product(range(3), repeat=3):
        value = product_zero()
        for scalar, gen in zip(coeffs, generators):
            value = product_add(value, product_mul(scalar, gen, a), a)
        out.append(value)
    return out


def rank_mod3(rows: Sequence[Sequence[int]]) -> int:
    a = [[x % 3 for x in row] for row in rows]
    rank = 0
    for col in range(len(a[0]) if a else 0):
        pivot = next((i for i in range(rank, len(a)) if a[i][col]), None)
        if pivot is None:
            continue
        a[rank], a[pivot] = a[pivot], a[rank]
        inv = pow(a[rank][col], -1, 3)
        a[rank] = [(x * inv) % 3 for x in a[rank]]
        for i in range(len(a)):
            if i != rank and a[i][col]:
                z = a[i][col]
                a[i] = [(a[i][j] - z * a[rank][j]) % 3 for j in range(len(a[0]))]
        rank += 1
    return rank


def matmul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(len(b))) % 3 for j in range(len(b[0]))] for i in range(len(a))]


def transpose(a):
    return [list(x) for x in zip(*a)]


def symplectic_gram(matrix):
    j = [[0] * 6 for _ in range(6)]
    for block in range(3):
        j[2 * block][2 * block + 1] = 1
        j[2 * block + 1][2 * block] = 2
    return matmul(matmul(matrix, j), transpose(matrix))


def all_lagrangians():
    """Enumerate the 1120 Lagrangians of the standard symplectic F_3^6."""
    for pivots in itertools.combinations(range(6), 3):
        slots = [
            (i, col)
            for i in range(3)
            for col in range(pivots[i] + 1, 6)
            if col not in pivots
        ]
        for values in itertools.product(range(3), repeat=len(slots)):
            matrix = [[0] * 6 for _ in range(3)]
            for i, pivot in enumerate(pivots):
                matrix[i][pivot] = 1
            for (i, col), value in zip(slots, values):
                matrix[i][col] = value
            if all(x == 0 for row in symplectic_gram(matrix) for x in row):
                yield matrix


def block_diag_frobenius(f):
    out = [[0] * 6 for _ in range(6)]
    for block in range(3):
        for i in range(2):
            for j in range(2):
                out[2 * block + i][2 * block + j] = f[i][j] % 3
    return out


def factor_transverse(matrix) -> bool:
    for block in range(3):
        coordinate_factor = [
            [int(col == 2 * block + i) for col in range(6)] for i in range(2)
        ]
        if rank_mod3(list(matrix) + coordinate_factor) != 5:
            return False
    return True


def projective_lines_f3():
    """Canonical representatives of the 13 points of P^2(F_3)."""
    lines = []
    for vector in itertools.product(range(3), repeat=3):
        if not any(vector):
            continue
        first = next(x for x in vector if x)
        normalized = tuple((x * pow(first, -1, 3)) % 3 for x in vector)
        if normalized not in lines:
            lines.append(normalized)
    return lines


def scalar_diagonal_incidence(matrix):
    """Return E_v[3] intersections for scalar diagonal elliptic subgroups.

    E_v[3] is spanned by (v1*P,v1*Q,v2*P,v2*Q,v3*P,v3*Q).  These 13 tests
    include the coordinate factors, but not elliptic subvarieties using
    non-scalar endomorphisms of E.
    """
    intersections = []
    for vector in projective_lines_f3():
        torsion = [
            [vector[0], 0, vector[1], 0, vector[2], 0],
            [0, vector[0], 0, vector[1], 0, vector[2]],
        ]
        dimension = 5 - rank_mod3(list(matrix) + torsion)
        if dimension:
            intersections.append({"vector": list(vector), "intersection_dimension": dimension})
    return intersections


def stable_under(matrix, transformation) -> bool:
    image = matmul(matrix, transpose(transformation))
    return rank_mod3(list(matrix) + image) == 3


def lagrangian_census(frobenius):
    total = stable = admissible = 0
    diagonal_incidence_histogram = {}
    for matrix in all_lagrangians():
        total += 1
        if stable_under(matrix, block_diag_frobenius(frobenius)):
            stable += 1
            if factor_transverse(matrix):
                admissible += 1
                incidence_count = len(scalar_diagonal_incidence(matrix))
                diagonal_incidence_histogram[incidence_count] = (
                    diagonal_incidence_histogram.get(incidence_count, 0) + 1
                )
    return {
        "total": total,
        "frobenius_stable": stable,
        "factor_transverse": admissible,
        "scalar_diagonal_incidence_histogram": {
            str(key): value for key, value in sorted(diagonal_incidence_histogram.items())
        },
    }


def build_p224():
    c = CURVES["P-224"]
    p, a0, b0 = c["p"], c["a"], c["b"]
    unit, factors = psi3_factorization(p, a0, b0)
    roots = sorted(linear_root(poly, p) for poly, multiplicity in factors for _ in range(multiplicity))
    assert len(roots) == 4 and all(poly.degree() == 1 for poly, _ in factors)
    x0, x1 = roots[:2]
    r0 = (pow(x0, 3, p) + a0 * x0 + b0) % p
    r1 = (pow(x1, 3, p) + a0 * x1 + b0) % p
    assert pow(r0, (p - 1) // 2, p) == p - 1
    assert pow(r1, (p - 1) // 2, p) == p - 1
    ratio_sqrt = mod_sqrt(r1 * pow(r0, -1, p) % p, p)
    fp = FFContext(p, [0, 1])
    field = QuadContext(fp, fp.e(r0))
    a, b = field.e(a0), field.e(b0)
    P = (field.e(x0), field.u)
    Q = (field.e(x1), field.e(0, ratio_sqrt))
    assert point_on_curve(P, a, b) and point_on_curve(Q, a, b)
    assert ec_mul(3, P, a) is None and ec_mul(3, Q, a) is None
    assert frobenius_point(P, p) == ec_neg(P)
    assert frobenius_point(Q, p) == ec_neg(Q)
    return {
        "curve": "P-224",
        "psi3_unit": hex(unit),
        "psi3_factor_degrees": [poly.degree() for poly, _ in factors],
        "torsion_field": {
            "description": "F_p[u]/(u^2-r0)",
            "degree": 2,
            "r0": hex(r0),
            "nonsquare_check": True,
        },
        "basis": {"P": point_json(P), "Q": point_json(Q)},
        "frobenius_matrix_mod_3": [[2, 0], [0, 2]],
        "basis_points": (P, Q, a),
    }


def build_p256():
    c = CURVES["P-256"]
    p, a0, b0 = c["p"], c["a"], c["b"]
    unit, factors = psi3_factorization(p, a0, b0)
    degrees = sorted(poly.degree() for poly, _ in factors)
    assert degrees == [1, 3]
    cubic = next(poly for poly, _ in factors if poly.degree() == 3).monic()
    high = [int(x) % p for x in cubic.all_coeffs()]
    modulus = list(reversed(high))
    fp3 = FFContext(p, modulus)
    z = fp3.e([0, 1, 0])
    r = z**3 + a0 * z + b0
    assert r ** ((fp3.order - 1) // 2) == -fp3.one
    field = QuadContext(fp3, r)
    a, b = field.e(a0), field.e(b0)
    P = (field.e(z), field.u)
    Q = frobenius_point(P, p)
    assert point_on_curve(P, a, b) and point_on_curve(Q, a, b)
    assert ec_mul(3, P, a) is None and ec_mul(3, Q, a) is None
    assert Q not in (P, ec_neg(P))
    assert frobenius_point(Q, p) == ec_add(ec_neg(P), Q, a)
    return {
        "curve": "P-256",
        "psi3_unit": hex(unit),
        "psi3_factor_degrees": degrees,
        "torsion_field": {
            "description": "F_p[z,u]/(g(z), u^2-r(z))",
            "degree": 6,
            "g_low_to_high": [hex(x) for x in modulus],
            "r_low_to_high": r.as_json(),
            "nonsquare_check": True,
        },
        "basis": {"P": point_json(P), "Q": point_json(Q)},
        "frobenius_matrix_mod_3": [[0, 2], [1, 1]],
        "basis_points": (P, Q, a),
    }


def certify_kernel(bundle, p: int):
    P, Q, a = bundle.pop("basis_points")
    generators = matrix_kernel_generators(P, Q, a)
    elements = kernel_elements(generators, a)
    assert len(set(elements)) == 27
    assert all(product_mul(3, x, a) == product_zero() for x in elements)
    for factor in range(3):
        intersection = [
            x for x in elements if all(x[j] is None for j in range(3) if j != factor)
        ]
        assert intersection == [product_zero()]
    assert all(frobenius_product(g, p) in elements for g in generators)
    gram = symplectic_gram(KERNEL_MATRIX)
    assert all(x == 0 for row in gram for x in row)
    transformation = block_diag_frobenius(bundle["frobenius_matrix_mod_3"])
    image_rows = matmul(KERNEL_MATRIX, transpose(transformation))
    # KERNEL_MATRIX is in RREF with pivot columns 0,1,2, so these columns are
    # the generator-coordinate matrix for each image row.
    frobenius_on_generators = [row[:3] for row in image_rows]
    assert matmul(frobenius_on_generators, KERNEL_MATRIX) == image_rows
    bundle["kernel"] = {
        "coordinate_basis_order": ["P1", "Q1", "P2", "Q2", "P3", "Q3"],
        "generator_matrix_mod_3": KERNEL_MATRIX,
        "generators": [product_json(x) for x in generators],
        "cardinality": len(set(elements)),
        "all_elements_killed_by_3": True,
        "symplectic_gram_mod_3": gram,
        "maximal_isotropic": True,
        "factor_intersection_cardinalities": [1, 1, 1],
        "frobenius_stable": True,
        "frobenius_action_on_generator_coordinates_mod_3": frobenius_on_generators,
    }
    if bundle["curve"] == "P-224":
        alternate_generators = matrix_kernel_generators(
            P, Q, a, P224_ZERO_DIAGONAL_INCIDENCE_KERNEL_MATRIX
        )
        alternate_elements = kernel_elements(alternate_generators, a)
        assert len(set(alternate_elements)) == 27
        assert all(frobenius_product(g, p) in alternate_elements for g in alternate_generators)
        bundle["zero_scalar_diagonal_incidence_alternate_kernel"] = {
            "coordinate_basis_order": ["P1", "Q1", "P2", "Q2", "P3", "Q3"],
            "generator_matrix_mod_3": P224_ZERO_DIAGONAL_INCIDENCE_KERNEL_MATRIX,
            "generators": [product_json(x) for x in alternate_generators],
            "cardinality": 27,
            "maximal_isotropic": True,
            "factor_transverse": True,
            "frobenius_stable": True,
            "scalar_diagonal_incidence": [],
            "scope_note": "stronger repeated-factor diagnostic, not a complete End(E)-linear indecomposability certificate",
        }
    return bundle


def parse_openssl_profile(name: str):
    try:
        out = subprocess.check_output(
            ["openssl", "ecparam", "-name", name, "-param_enc", "explicit", "-text", "-noout"],
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None

    def section(label, next_label):
        start = out.index(label + ":") + len(label) + 1
        end = out.index(next_label + ":", start)
        return int("".join(c for c in out[start:end] if c in "0123456789abcdefABCDEF"), 16)

    p = section("Prime", "A")
    a = section("A", "B")
    b = section("B", "Generator (uncompressed)")
    n = section("Order", "Cofactor")
    t = p + 1 - n
    return {
        "p_mod_3": p % 3,
        "t_mod_3": t % 3,
        "n_mod_3": n % 3,
        "p": hex(p),
        "a": hex(a),
        "b": hex(b),
        "n": hex(n),
    }


def cost_model(curve):
    p, n = curve["p"], curve["n"]
    rho_log2 = math.log2(0.886) + math.log2(n) / 2
    destination_log2 = math.log2(p)
    return {
        "baseline": "Pollard rho with negation-map constant 0.886*sqrt(n)",
        "baseline_log2_group_operations": rho_log2,
        "published_tian_destination_model": "soft-O(p) after substituting q=p for a prime-field NIST destination",
        "destination_log2_field_scale_excluding_polylogs": destination_log2,
        "destination_minus_rho_log2": destination_log2 - rho_log2,
        "construction": "unmeasured",
        "transfer": "unmeasured",
        "recovery": "unmeasured",
        "interpretation": "the published destination term alone is asymptotically larger; no end-to-end speedup is established",
    }


def environment_manifest():
    return {
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "python": sys.version,
        "sympy": sympy.__version__,
        "platform": platform.platform(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count(),
    }


def run():
    p224 = certify_kernel(build_p224(), CURVES["P-224"]["p"])
    p256 = certify_kernel(build_p256(), CURVES["P-256"]["p"])

    census = {}
    exact_frobenius = {
        "P-192": [[0, 1], [1, 1]],  # det=2, trace=1
        "P-224": [[2, 0], [0, 2]],  # psi_3 splits; F != I because 3 does not divide n
        "P-256": [[0, 2], [1, 1]],  # one linear plus one cubic psi_3 factor
        "P-384": [[0, 1], [1, 2]],  # det=2, trace=2
        "P-521": [[0, 2], [1, 0]],  # det=1, trace=0
    }
    openssl_checks = {}
    for label, profile in CONTROL_PROFILES.items():
        observed = parse_openssl_profile(OPENSSL_NAMES[label])
        openssl_checks[label] = observed
        if observed is not None:
            assert (observed["p_mod_3"], observed["t_mod_3"]) == profile
            if label in CURVES:
                assert all(
                    int(observed[key], 16) == CURVES[label][key]
                    for key in ["p", "a", "b", "n"]
                )
                observed["exact_target_parameters_match"] = True
        census[label] = lagrangian_census(exact_frobenius[label])

    curves = {}
    for bundle in [p224, p256]:
        label = bundle["curve"]
        c = CURVES[label]
        t = c["p"] + 1 - c["n"]
        assert sympy.isprime(c["n"])
        curves[label] = {
            "parameters": {
                "p": hex(c["p"]),
                "a": hex(c["a"]),
                "b": hex(c["b"]),
                "n": hex(c["n"]),
                "t": hex(t),
                "n_is_prime": True,
                "gcd_n_3": math.gcd(c["n"], 3),
                "recovery_scalar_3_inverse_mod_n": hex(pow(3, -1, c["n"])),
                "composed_diagonal_recovery_scalar_9_inverse_mod_n": hex(pow(9, -1, c["n"])),
            },
            **bundle,
            "lagrangian_census": census[label],
            "cost_model": cost_model(c),
        }

    return {
        "format": "nist-333-evidence-v1",
        "scope": "public NIST curve structure and transfer assessment; no DLP solving",
        "environment": environment_manifest(),
        "kernel_matrix_symplectic_gram": symplectic_gram(KERNEL_MATRIX),
        "repeated_factor_diagnostic": {
            "scope": "exact intersections with the 13 scalar diagonal E_v[3] subgroups; not a complete End(E)-linear indecomposability test",
            "shared_kernel_incidence": scalar_diagonal_incidence(KERNEL_MATRIX),
            "p224_zero_incidence_alternate": {
                "generator_matrix_mod_3": P224_ZERO_DIAGONAL_INCIDENCE_KERNEL_MATRIX,
                "symplectic_gram_mod_3": symplectic_gram(P224_ZERO_DIAGONAL_INCIDENCE_KERNEL_MATRIX),
                "factor_transverse": factor_transverse(P224_ZERO_DIAGONAL_INCIDENCE_KERNEL_MATRIX),
                "frobenius_stable": stable_under(
                    P224_ZERO_DIAGONAL_INCIDENCE_KERNEL_MATRIX,
                    block_diag_frobenius(exact_frobenius["P-224"]),
                ),
                "incidence": scalar_diagonal_incidence(P224_ZERO_DIAGONAL_INCIDENCE_KERNEL_MATRIX),
            },
        },
        "curves": curves,
        "negative_controls": {
            label: {"profile": CONTROL_PROFILES[label], "census": census[label]}
            for label in ["P-192", "P-384", "P-521"]
        },
        "openssl_profile_checks": openssl_checks,
        "claims": {
            "explicit_kernel": "supported for P-224 and P-256",
            "genus3_quotient": "not constructed",
            "explicit_isogeny": "not constructed",
            "subgroup_preservation": "supported conditionally on a quotient isogeny with this kernel",
            "computational_advantage": "refuted for the published Tian destination-cost substitution; unknown for any new relation mechanism",
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = run()
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(encoded)
    else:
        print(encoded, end="")


if __name__ == "__main__":
    main()
