#!/usr/bin/env python3
"""Finite-field theta-null reconstruction for the P-224 (3,3,3) quotient.

This implements the normal-Weil-set and theta-null stages of Tian's
construction directly over the compositum F_(p^6).  It deliberately treats
the six square roots used to normalize the quotient 2-Weil set as formal
symbols: every Weber product needed for the quartic has even exponent in each
symbol, so only their squares are evaluated in the finite field.
"""

from __future__ import annotations

import argparse
import importlib.util
import itertools
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location("nist_333", ROOT / "src" / "nist_333.py")
nist = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["nist_333"] = nist
SPEC.loader.exec_module(nist)


class CubicContext:
    """A cubic extension of an existing exact finite-field context."""

    def __init__(self, base, modulus):
        self.base = base
        self.modulus = tuple(base.e(x) for x in modulus)
        if len(self.modulus) != 4 or self.modulus[-1] != base.one:
            raise ValueError("cubic modulus must be monic and low-to-high")
        self.order = base.order**3

    def e(self, value=0):
        if isinstance(value, CubicElement):
            if value.ctx is not self:
                raise TypeError("field mismatch")
            return value
        if isinstance(value, (list, tuple)):
            coeffs = list(value)
        else:
            coeffs = [value]
        if len(coeffs) > 3:
            raise ValueError("too many cubic-extension coefficients")
        coeffs += [0] * (3 - len(coeffs))
        return CubicElement(self, tuple(self.base.e(x) for x in coeffs))

    @property
    def zero(self):
        return self.e(0)

    @property
    def one(self):
        return self.e(1)

    @property
    def generator(self):
        return self.e([0, 1, 0])


@dataclass(frozen=True)
class CubicElement:
    ctx: CubicContext
    coeffs: tuple

    def _coerce(self, other):
        return self.ctx.e(other)

    def __add__(self, other):
        other = self._coerce(other)
        return self.ctx.e([x + y for x, y in zip(self.coeffs, other.coeffs)])

    __radd__ = __add__

    def __neg__(self):
        return self.ctx.e([-x for x in self.coeffs])

    def __sub__(self, other):
        return self + (-self._coerce(other))

    def __rsub__(self, other):
        return self._coerce(other) - self

    def __mul__(self, other):
        other = self._coerce(other)
        base = self.ctx.base
        values = [base.zero] * 5
        for i, x in enumerate(self.coeffs):
            for j, y in enumerate(other.coeffs):
                values[i + j] = values[i + j] + x * y
        for degree in (4, 3):
            leading = values[degree]
            if leading:
                for j in range(3):
                    values[degree - 3 + j] = (
                        values[degree - 3 + j] - leading * self.ctx.modulus[j]
                    )
        return self.ctx.e(values[:3])

    __rmul__ = __mul__

    def __pow__(self, exponent):
        if exponent < 0:
            return self.inverse() ** (-exponent)
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
        # Invert the multiplication matrix with exact Gaussian elimination.
        columns = []
        for j in range(3):
            product = self * self.ctx.e([int(i == j) for i in range(3)])
            columns.append(product.coeffs)
        matrix = [[columns[col][row] for col in range(3)] for row in range(3)]
        solution = solve_linear(matrix, [self.ctx.base.one, self.ctx.base.zero, self.ctx.base.zero])
        return self.ctx.e(solution)

    def __truediv__(self, other):
        return self * self._coerce(other).inverse()

    def __rtruediv__(self, other):
        return self._coerce(other) / self

    def __bool__(self):
        return any(bool(x) for x in self.coeffs)

    def frobenius(self, prime):
        return self**prime

    def in_prime_field(self, prime):
        return self**prime == self

    def as_json(self):
        return [coefficient.as_json() for coefficient in self.coeffs]


def solve_linear(matrix, rhs):
    """Solve a square linear system over any supported exact field."""
    size = len(rhs)
    augmented = [list(row) + [rhs[i]] for i, row in enumerate(matrix)]
    for col in range(size):
        pivot = next((row for row in range(col, size) if augmented[row][col]), None)
        if pivot is None:
            raise ZeroDivisionError("singular matrix")
        augmented[col], augmented[pivot] = augmented[pivot], augmented[col]
        inverse = augmented[col][col].inverse()
        augmented[col] = [value * inverse for value in augmented[col]]
        for row in range(size):
            if row == col or not augmented[row][col]:
                continue
            scale = augmented[row][col]
            augmented[row] = [
                x - scale * y for x, y in zip(augmented[row], augmented[col])
            ]
    return [augmented[i][-1] for i in range(size)]


def field_sqrt(value, field):
    """Tonelli-Shanks in an arbitrary supported finite field."""
    value = field.e(value)
    if not value:
        return field.zero
    order = field.order
    if value ** ((order - 1) // 2) != field.one:
        raise ValueError("element is not a square in the working field")
    odd = order - 1
    power = 0
    while odd % 2 == 0:
        power += 1
        odd //= 2
    if power == 1:
        return value ** ((order + 1) // 4)
    nonsquare = None
    candidates = [field.e(i) for i in range(2, 32)]
    if hasattr(field, "generator"):
        candidates += [field.generator + i for i in range(16)]
    if hasattr(field, "base") and hasattr(field.base, "u"):
        candidates += [field.e(field.base.u + i) for i in range(16)]
    if hasattr(field, "generator"):
        candidates += [field.generator**2 + a * field.generator + b for a in range(4) for b in range(4)]
    for candidate in candidates:
        if candidate and candidate ** ((order - 1) // 2) == -field.one:
            nonsquare = candidate
            break
    if nonsquare is None:
        raise RuntimeError("failed to find a deterministic nonsquare")
    c = nonsquare**odd
    x = value ** ((odd + 1) // 2)
    t = value**odd
    m = power
    while t != field.one:
        i = 1
        t2 = t * t
        while i < m and t2 != field.one:
            t2 *= t2
            i += 1
        if i == m:
            raise ArithmeticError("Tonelli-Shanks invariant failed")
        b = c ** (1 << (m - i - 1))
        x *= b
        t *= b * b
        c = b * b
        m = i
    if x * x != value:
        raise ArithmeticError("invalid square root")
    return x


P224_GX = int("B70E0CBD6BB4BF7F321390B94A03C1D356C21122343280D6115C1D21", 16)
P224_GY = int("BD376388B5F723FB4C22DFE6CD4375A05A07476444D5819985007E34", 16)
P256_GX = int("6B17D1F2E12C4247F8BCE6E563A440F277037D812DEB33A0F4A13945D898C296", 16)
P256_GY = int("4FE342E2FE1A7F9B8EE7EB4A7C0F9E162BCE33576B315ECECBB6406837BF51F5", 16)


def embed_point(point, field):
    if point is None:
        return None
    return (field.e(point[0]), field.e(point[1]))


def coordinate_parameter(parameter, index):
    return parameter[index] if isinstance(parameter, (tuple, list)) else parameter


def add_product(left, right, a):
    return tuple(
        nist.ec_add(x, y, coordinate_parameter(a, index))
        for index, (x, y) in enumerate(zip(left, right))
    )


def negate_product(point):
    return tuple(nist.ec_neg(x) for x in point)


def scalar_product(scalar, point, a):
    return tuple(
        nist.ec_mul(scalar, x, coordinate_parameter(a, index))
        for index, x in enumerate(point)
    )


def p224_setup(kernel_matrix=None):
    curve = nist.CURVES["P-224"]
    bundle = nist.build_p224()
    p2, q2, a2 = bundle["basis_points"]
    k2 = p2[0].ctx
    cubic = CubicContext(k2, [k2.e(curve["b"]), k2.e(curve["a"]), k2.zero, k2.one])
    w = cubic.generator
    a, b = cubic.e(curve["a"]), cubic.e(curve["b"])
    if w**3 + a * w + b:
        raise AssertionError("2-division generator does not satisfy the cubic")
    roots = [w, w**curve["p"], w ** (curve["p"] ** 2)]
    if len(set(roots)) != 3 or sum(roots, cubic.zero):
        raise AssertionError("failed to obtain the three nonzero 2-torsion points")
    two_torsion = [(root, cubic.zero) for root in roots]
    q1, q2_torsion, q3 = two_torsion
    if nist.ec_add(q1, q2_torsion, a) != q3:
        raise AssertionError("2-torsion labeling is inconsistent")
    p3, q3_basis = embed_point(p2, cubic), embed_point(q2, cubic)
    if kernel_matrix is None:
        kernel_matrix = nist.P224_ZERO_DIAGONAL_INCIDENCE_KERNEL_MATRIX
    kernel_generators = nist.matrix_kernel_generators(p3, q3_basis, a, kernel_matrix)
    kernel = {}
    for coefficients in itertools.product(range(3), repeat=3):
        point = (None, None, None)
        for scalar, generator in zip(coefficients, kernel_generators):
            point = add_product(point, scalar_product(scalar, generator, a), a)
        kernel[coefficients] = point
    if len(set(kernel.values())) != 27:
        raise AssertionError("kernel enumeration collapsed")
    generator = (cubic.e(P224_GX), cubic.e(P224_GY))
    if not nist.point_on_curve(generator, a, b):
        raise AssertionError("P-224 generator is not on the curve")
    generic = (
        generator,
        nist.ec_mul(2, generator, a),
        nist.ec_mul(4, generator, a),
    )
    return {
        "curve": curve,
        "field": cubic,
        "a": (a, a, a),
        "b": (b, b, b),
        "three_basis": (p3, q3_basis),
        "kernel_generator_points": tuple(kernel_generators),
        "kernel": kernel,
        "two_torsion": ((q1, q1, q1), (q2_torsion, q2_torsion, q2_torsion), (q3, q3, q3)),
        "generic": generic,
    }


def univariate_mod(polynomial, modulus):
    return univariate_divmod(polynomial, modulus)[1]


def univariate_mulmod(left, right, modulus):
    return univariate_mod(univariate_mul(left, right), modulus)


def univariate_powmod(polynomial, exponent, modulus, one):
    result, base = [one], univariate_mod(polynomial, modulus)
    while exponent:
        if exponent & 1:
            result = univariate_mulmod(result, base, modulus)
        base = univariate_mulmod(base, base, modulus)
        exponent >>= 1
    return result


def split_depressed_cubic(field, a, b):
    """Split x^3+a*x+b over a supplied odd finite field.

    A deterministic Cantor--Zassenhaus search isolates one root.  The
    remaining quadratic is then solved directly.  This is used for P-256,
    where the 2-division polynomial splits in the already-constructed F_(p^3)
    subfield of the 3-torsion field.
    """
    a, b = field.e(a), field.e(b)
    polynomial = [b, a, field.zero, field.one]
    if not hasattr(field, "degree") or field.degree < 2:
        raise ValueError("a nontrivial explicit extension field is required")
    z = field.e([0, 1] + [0] * (field.degree - 2))
    candidates = [
        z + constant for constant in range(8)
    ] + [
        z * z + multiple * z + constant
        for multiple in range(1, 5)
        for constant in range(4)
    ]
    linear = None
    for shift in candidates:
        power = univariate_powmod(
            [shift, field.one], (field.order - 1) // 2, polynomial, field.one
        )
        split = univariate_gcd(polynomial, univariate_add(power, [-field.one]))
        if len(split) == 2:
            linear = split
            break
        if len(split) == 3:
            quotient, remainder = univariate_divmod(polynomial, split)
            if remainder:
                raise ArithmeticError("invalid cubic factorization remainder")
            if len(quotient) == 2:
                linear = quotient
                break
    if linear is None:
        raise RuntimeError("deterministic cubic split search exhausted")
    root = -linear[0] / linear[1]
    quotient, remainder = univariate_divmod(polynomial, [-root, field.one])
    if remainder or len(quotient) != 3:
        raise ArithmeticError("isolated value is not a cubic root")
    quotient = [value / quotient[-1] for value in quotient]
    discriminant = quotient[1] ** 2 - 4 * quotient[0]
    # P-256 has p^3 == 3 (mod 4), so this is the exact square-root formula.
    if field.order % 4 != 3:
        raise ValueError("quadratic completion currently expects q == 3 mod 4")
    square_root = discriminant ** ((field.order + 1) // 4)
    if square_root * square_root != discriminant:
        raise ArithmeticError("quadratic discriminant is not a square")
    inverse_two = field.e(2).inverse()
    roots = [root, (-quotient[1] + square_root) * inverse_two, (-quotient[1] - square_root) * inverse_two]
    if len(set(roots)) != 3 or any(value**3 + a * value + b for value in roots):
        raise ArithmeticError("cubic roots failed verification")
    return tuple(roots)


def p256_setup(kernel_matrix=None):
    """Build the P-256 theta engine in its minimal degree-six field."""
    curve = nist.CURVES["P-256"]
    bundle = nist.build_p256()
    p6, q6, a6 = bundle["basis_points"]
    field = p6[0].ctx
    fp3 = field.base
    roots3 = split_depressed_cubic(fp3, curve["a"], curve["b"])
    roots = tuple(field.e(root) for root in roots3)
    a, b = field.e(curve["a"]), field.e(curve["b"])
    two_torsion = tuple((root, field.zero) for root in roots)
    q1, q2_torsion, q3 = two_torsion
    # Relabel if needed so Q1+Q2=Q3 (all three roots are otherwise symmetric).
    if nist.ec_add(q1, q2_torsion, a) != q3:
        raise AssertionError("P-256 2-torsion labeling is inconsistent")
    if kernel_matrix is None:
        kernel_matrix = nist.KERNEL_MATRIX
    kernel_generators = nist.matrix_kernel_generators(p6, q6, a, kernel_matrix)
    kernel = {}
    for coefficients in itertools.product(range(3), repeat=3):
        point = (None, None, None)
        for scalar, generator_point in zip(coefficients, kernel_generators):
            point = add_product(point, scalar_product(scalar, generator_point, a), a)
        kernel[coefficients] = point
    if len(set(kernel.values())) != 27:
        raise AssertionError("P-256 kernel enumeration collapsed")
    generator = (field.e(P256_GX), field.e(P256_GY))
    if not nist.point_on_curve(generator, a, b):
        raise AssertionError("P-256 generator is not on the curve")
    generic = (generator, nist.ec_mul(2, generator, a), nist.ec_mul(4, generator, a))
    return {
        "curve": curve,
        "field": field,
        "a": (a, a, a),
        "b": (b, b, b),
        "three_basis": (p6, q6),
        "kernel_generator_points": tuple(kernel_generators),
        "kernel": kernel,
        "two_torsion": ((q1, q1, q1), (q2_torsion, q2_torsion, q2_torsion), (q3, q3, q3)),
        "generic": generic,
    }


def tian_523_setup():
    """Published positive control from Tian, Section 3.3."""
    p = 523
    k3 = nist.FFContext(p, [2, 0, 0, 1])  # w^3+2
    w = k3.e([0, 1, 0])
    k6 = nist.QuadContext(k3, w + 6)  # theta^2=w+6
    theta = k6.u

    def c3(c0, c1=0, c2=0):
        return k3.e([c0, c1, c2])

    a3 = c3(140, 92, 82)
    b3 = c3(243, 339, 359)
    a6, b6 = k6.e(a3), k6.e(b3)
    k18 = CubicContext(k6, [b6, a6, k6.zero, k6.one])
    v = k18.generator

    def e3(c0, c1=0, c2=0):
        return k18.e(k6.e(c3(c0, c1, c2)))

    theta18 = k18.e(theta)

    def point(x_coefficients, y_coefficients):
        return (
            e3(*x_coefficients),
            e3(*y_coefficients) * theta18,
        )

    generators = [
        (
            point((337, 370, 222), (400, 387, 122)),
            point((156, 287, 312), (493, 362, 21)),
            point((156, 275, 415), (451, 251, 419)),
        ),
        (
            point((156, 484, 319), (108, 484, 298)),
            point((337, 442, 245), (6, 456, 305)),
            point((156, 275, 415), (72, 272, 104)),
        ),
        (
            point((156, 484, 319), (415, 39, 225)),
            point((156, 287, 312), (493, 362, 21)),
            point((337, 234, 56), (222, 109, 150)),
        ),
    ]
    a_values = tuple(k18.e(k6.e(a3 ** (p**i))) for i in range(3))
    b_values = tuple(k18.e(k6.e(b3 ** (p**i))) for i in range(3))
    for generator in generators:
        for index, coordinate in enumerate(generator):
            if not nist.point_on_curve(coordinate, a_values[index], b_values[index]):
                raise AssertionError("Tian control kernel point is not on its factor")
            if nist.ec_mul(3, coordinate, a_values[index]) is not None:
                raise AssertionError("Tian control kernel point is not 3-torsion")
    kernel = {}
    for coefficients in itertools.product(range(3), repeat=3):
        value = (None, None, None)
        for scalar, generator in zip(coefficients, generators):
            value = add_product(value, scalar_product(scalar, generator, a_values), a_values)
        kernel[coefficients] = value
    if len(set(kernel.values())) != 27:
        raise AssertionError("Tian control kernel collapsed")

    q = p**3
    roots = [v, v**q, v ** (q**2)]
    if len(set(roots)) != 3:
        raise AssertionError("Tian control 2-division polynomial did not split")
    q1 = tuple((roots[0] ** (p**i), k18.zero) for i in range(3))
    q2 = tuple((roots[1] ** (p**i), k18.zero) for i in range(3))
    q3 = tuple((roots[2] ** (p**i), k18.zero) for i in range(3))
    for index in range(3):
        if nist.ec_add(q1[index], q2[index], a_values[index]) != q3[index]:
            raise AssertionError("Tian control 2-torsion labeling is inconsistent")

    base_point = (e3(7), e3(310, 306, 155))
    conjugates = tuple(
        (base_point[0] ** (p**i), base_point[1] ** (p**i)) for i in range(3)
    )
    generic = tuple(
        nist.ec_mul(multiplier, conjugates[index], a_values[index])
        for index, multiplier in enumerate((1, 2, 4))
    )
    return {
        "curve": {"name": "Tian-523-control", "p": p},
        "field": k18,
        "a": a_values,
        "b": b_values,
        "kernel_generator_points": tuple(generators),
        "kernel": kernel,
        "two_torsion": (q1, q2, q3),
        "generic": generic,
    }


def coeff_add(left, right):
    return tuple((x + y) % 3 for x, y in zip(left, right))


def coeff_scale(scalar, value):
    return tuple((scalar * x) % 3 for x in value)


def translate_product(point, translation, a):
    return add_product(point, translation, a)


def tangent_weil_value(torsion_point, argument, q3, a, field):
    """Evaluate f_P with div(f_P)=3*T_P^*Theta-3*Theta."""
    if torsion_point is None:
        return field.one
    shifted = nist.ec_add(argument, q3, a)  # q3=-q3 for two-torsion
    if shifted is None:
        raise ZeroDivisionError("tangent Weil function evaluated at its pole")
    center = nist.ec_neg(torsion_point)
    x0, y0 = center
    slope = (3 * x0 * x0 + a) / (2 * y0)
    x, y = shifted
    return y - y0 - slope * (x - x0)


class P224ThetaEngine:
    def __init__(self, data=None):
        self.data = p224_setup() if data is None else data
        self.field = self.data["field"]
        self.a = self.data["a"]
        self.kernel = self.data["kernel"]
        self.kernel_generators = self.data["kernel_generator_points"]
        self.q1, self.q2, self.q3 = self.data["two_torsion"]
        self.generic = self.data["generic"]
        self._f_cache = {}
        self._line_cache = {}
        self.alpha = self._normalize_kernel()
        self._generic_two_translates = {}
        self._generic_theta = {}
        self._h_cache = {}
        self.g_constants = None

    def initial_weil(self, coefficients, argument):
        key = (coefficients, argument)
        if key in self._f_cache:
            return self._f_cache[key]
        kernel_point = self.kernel[coefficients]
        value = self.field.one
        for index, (point, coordinate) in enumerate(zip(kernel_point, argument)):
            value *= self.coordinate_weil(point, coordinate, index)
        self._f_cache[key] = value
        return value

    def coordinate_weil(self, torsion_point, argument, coordinate):
        if torsion_point is None:
            return self.field.one
        a = coordinate_parameter(self.a, coordinate)
        shifted = nist.ec_add(argument, self.q3[coordinate], a)
        if shifted is None:
            raise ZeroDivisionError("tangent Weil function evaluated at its pole")
        key = (coordinate, torsion_point)
        if key not in self._line_cache:
            center = nist.ec_neg(torsion_point)
            x0, y0 = center
            slope = (3 * x0 * x0 + a) / (2 * y0)
            self._line_cache[key] = (x0, y0, slope)
        x0, y0, slope = self._line_cache[key]
        x, y = shifted
        return y - y0 - slope * (x - x0)

    def translated_generic(self, coefficients):
        return translate_product(self.generic, self.kernel[coefficients], self.a)

    def _normalize_kernel(self):
        zero = (0, 0, 0)
        basis = [(1, 0, 0), (0, 1, 0), (0, 0, 1)]
        alpha = {zero: self.field.one}
        for generator in basis:
            double = coeff_scale(2, generator)
            f_g = self.initial_weil(generator, self.generic)
            f_2g = self.initial_weil(double, self.generic)
            at_plus_g = self.translated_generic(generator)
            u = (
                f_2g
                / (f_g * self.initial_weil(generator, at_plus_g))
                / (f_g * self.initial_weil(double, at_plus_g))
            )
            minus_generic = negate_product(self.generic)
            v = self.initial_weil(double, self.generic) / (
                f_g
                * self.initial_weil(double, at_plus_g)
                * self.initial_weil(generator, minus_generic)
            )
            alpha[generator] = u / v
            alpha[double] = (
                alpha[generator] ** 2
                * f_g
                * self.initial_weil(generator, at_plus_g)
                / f_2g
            )

        current = {(0, 0, 0): self.field.one}
        for generator in basis:
            expanded = dict(current)
            for existing, existing_alpha in current.items():
                for scalar in (1, 2):
                    term = coeff_scale(scalar, generator)
                    combined = coeff_add(existing, term)
                    translated = self.translated_generic(term)
                    expanded[combined] = (
                        existing_alpha
                        * alpha[term]
                        * self.initial_weil(term, self.generic)
                        * self.initial_weil(existing, translated)
                        / self.initial_weil(combined, self.generic)
                    )
            current = expanded
        if len(current) != 27:
            raise AssertionError("normalization did not cover the kernel")
        self._check_kernel_normalization(current)
        return current

    def _check_kernel_normalization(self, alpha):
        checks = [
            ((1, 0, 0), (0, 1, 0)),
            ((1, 2, 0), (0, 1, 1)),
            ((2, 1, 2), (1, 2, 1)),
        ]
        for left, right in checks:
            translated = self.translated_generic(left)
            lhs = (
                alpha[left]
                * self.initial_weil(left, self.generic)
                * alpha[right]
                * self.initial_weil(right, translated)
            )
            total = coeff_add(left, right)
            rhs = alpha[total] * self.initial_weil(total, self.generic)
            if lhs != rhs:
                raise AssertionError(f"kernel normalization failed for {left},{right}")

    def theta(self, argument):
        return sum(
            (self.alpha[coefficients] * self.initial_weil(coefficients, argument)
             for coefficients in self.kernel),
            self.field.zero,
        )

    @staticmethod
    def char_from_index(index):
        # Tian's order: i=i4+2*i5+4*i6+8*i1+16*i2+32*i3.
        return (
            (index >> 3) & 1,
            (index >> 4) & 1,
            (index >> 5) & 1,
            index & 1,
            (index >> 1) & 1,
            (index >> 2) & 1,
        )

    @staticmethod
    def index_from_char(characteristic):
        i1, i2, i3, i4, i5, i6 = characteristic
        return i4 + 2 * i5 + 4 * i6 + 8 * i1 + 16 * i2 + 32 * i3

    @staticmethod
    def xor_char(left, right):
        return tuple(x ^ y for x, y in zip(left, right))

    def two_torsion_product(self, characteristic):
        points = []
        for coordinate in range(3):
            point = None
            if characteristic[coordinate]:
                point = nist.ec_add(
                    point, self.q1[coordinate], coordinate_parameter(self.a, coordinate)
                )
            if characteristic[coordinate + 3]:
                point = nist.ec_add(
                    point, self.q2[coordinate], coordinate_parameter(self.a, coordinate)
                )
            points.append(point)
        return tuple(points)

    def generic_two_translate(self, characteristic):
        if characteristic not in self._generic_two_translates:
            self._generic_two_translates[characteristic] = add_product(
                self.generic, self.two_torsion_product(characteristic), self.a
            )
        return self._generic_two_translates[characteristic]

    def theta_generic_translate(self, characteristic):
        if characteristic not in self._generic_theta:
            self._generic_theta[characteristic] = self.theta(
                self.generic_two_translate(characteristic)
            )
            if not self._generic_theta[characteristic]:
                raise ZeroDivisionError("generic point hit the descended theta divisor")
        return self._generic_theta[characteristic]

    def g_value(self, characteristic, argument):
        value = self.field.one
        for coordinate, point in enumerate(argument):
            e1 = self.q1[coordinate][0]
            e2 = self.q2[coordinate][0]
            e3 = self.q3[coordinate][0]
            top = characteristic[coordinate]
            bottom = characteristic[coordinate + 3]
            if not top and not bottom:
                continue
            if self.g_constants is not None:
                value *= self.g_constants[coordinate][(top, bottom)]
            if point is None:
                raise ZeroDivisionError("generic g evaluation reached infinity")
            x = point[0]
            if top and not bottom:
                value *= (x - e2) / (x - e3)
            elif bottom and not top:
                value *= (x - e1) / (x - e3)
            else:
                value /= x - e3
        return value

    def set_paper_g_constants(self):
        constants = []
        for coordinate in range(3):
            e1 = self.q1[coordinate][0]
            e2 = self.q2[coordinate][0]
            e3 = self.q3[coordinate][0]
            constants.append(
                {
                    (1, 0): field_sqrt((e1 - e3) / (e1 - e2), self.field),
                    (0, 1): field_sqrt((e2 - e3) / (e2 - e1), self.field),
                    (1, 1): field_sqrt((e3 - e1) * (e2 - e3), self.field),
                }
            )
        self.g_constants = tuple(constants)
        self._h_cache.clear()
        return self.g_constants

    def h_generic(self, function_characteristic, translation_characteristic):
        key = (function_characteristic, translation_characteristic)
        if key in self._h_cache:
            return self._h_cache[key]
        argument = self.generic_two_translate(translation_characteristic)
        destination = self.xor_char(function_characteristic, translation_characteristic)
        value = (
            self.g_value(function_characteristic, argument) ** 3
            * self.theta_generic_translate(destination) ** 2
            / self.theta_generic_translate(translation_characteristic) ** 2
        )
        if not value:
            raise ZeroDivisionError("generic quotient Weil function vanished")
        self._h_cache[key] = value
        return value

    def quotient_weil_values(self, argument, quotient_data=None):
        """Evaluate the 64 normalized level-2 quotient Weil functions.

        These are executable projective coordinates on the quotient Kummer
        variety.  Squaring the translated theta section makes the coordinates
        insensitive to the sign of the destination Jacobian point.  They are
        therefore a point-map stage, but not yet a signed degree-three divisor
        representative on the descended plane quartic.
        """
        if quotient_data is None:
            quotient_data = self.quotient_theta_data()
        theta_argument = self.theta(argument)
        if not theta_argument:
            raise ZeroDivisionError("argument lies on the descended theta divisor")
        values = []
        for index in range(64):
            characteristic = self.char_from_index(index)
            translated = add_product(
                argument, self.two_torsion_product(characteristic), self.a
            )
            value = (
                quotient_data["scalar"][characteristic]
                * self.g_value(characteristic, argument) ** 3
                * self.theta(translated) ** 2
                / theta_argument**2
            )
            values.append(value)
        return tuple(values)

    @staticmethod
    def normalize_projective(values):
        pivot = next((value for value in values if value), None)
        if pivot is None:
            raise ZeroDivisionError("all projective coordinates vanished")
        return tuple(value / pivot for value in values)

    def quotient_kummer_image(self, argument, quotient_data=None):
        """Return normalized projective Kummer coordinates of the quotient image."""
        return self.normalize_projective(
            self.quotient_weil_values(argument, quotient_data)
        )

    def theta_leading_at_two_torsion(self, characteristic):
        torsion = self.two_torsion_product(characteristic)
        total = self.field.zero
        for coefficients, kernel_point in self.kernel.items():
            value = self.alpha[coefficients]
            for coordinate, (kernel_coordinate, torsion_coordinate) in enumerate(
                zip(kernel_point, torsion)
            ):
                if torsion_coordinate == self.q3[coordinate]:
                    # With t=-x/y at infinity, a nonzero 3-torsion tangent
                    # line has leading term -t^-3.  f_0=1 has no t^-3 term.
                    if kernel_coordinate is None:
                        value = self.field.zero
                        break
                    value = -value
                else:
                    value *= self.coordinate_weil(
                        kernel_coordinate, torsion_coordinate, coordinate
                    )
            total += value
        return total

    def quotient_theta_data(self):
        zero_characteristic = (0, 0, 0, 0, 0, 0)
        theta_zero = self.theta((None, None, None))
        if not theta_zero:
            raise ZeroDivisionError("theta section vanishes at the identity")
        h_zero = {}
        for index in range(64):
            characteristic = self.char_from_index(index)
            leading = self.theta_leading_at_two_torsion(characteristic)
            g_leading = self.field.one
            if self.g_constants is not None:
                for coordinate in range(3):
                    local = (characteristic[coordinate], characteristic[coordinate + 3])
                    if local != (0, 0):
                        g_leading *= self.g_constants[coordinate][local]
            h_zero[characteristic] = g_leading**3 * (leading / theta_zero) ** 2

        basis = [tuple(int(i == j) for i in range(6)) for j in range(6)]
        u = [
            self.field.one
            / (
                self.h_generic(characteristic, zero_characteristic)
                * self.h_generic(characteristic, characteristic)
            )
            for characteristic in basis
        ]

        scalar = {zero_characteristic: self.field.one}
        current = {zero_characteristic: self.field.one}
        for basis_index, generator in enumerate(basis):
            expanded = dict(current)
            for existing, existing_scalar in current.items():
                combined = self.xor_char(existing, generator)
                d_value = -1 if basis_index < 3 and existing[basis_index + 3] else 1
                expanded[combined] = (
                    existing_scalar
                    * self.h_generic(generator, zero_characteristic)
                    * self.h_generic(existing, generator)
                    / self.h_generic(combined, zero_characteristic)
                    / d_value
                )
            current = expanded
        scalar = current
        if len(scalar) != 64:
            raise AssertionError("quotient normalization did not cover all characteristics")

        factors = {
            characteristic: scalar[characteristic] * h_zero[characteristic]
            for characteristic in scalar
        }
        odd_zero = 0
        even_nonzero = 0
        violations = []
        for characteristic, value in factors.items():
            odd = sum(
                characteristic[i] * characteristic[i + 3] for i in range(3)
            ) % 2
            if odd:
                odd_zero += int(not value)
                if value:
                    violations.append({"characteristic": characteristic, "expected": "zero"})
            else:
                even_nonzero += int(bool(value))
                if not value:
                    violations.append({"characteristic": characteristic, "expected": "nonzero"})
        return {
            "u": u,
            "scalar": scalar,
            "h_zero": h_zero,
            "factors": factors,
            "odd_zero_count": odd_zero,
            "even_nonzero_count": even_nonzero,
            "violations": violations,
        }

    def theta_product(self, indices, quotient_data):
        characteristics = [self.char_from_index(index) for index in indices]
        exponents = [sum(characteristic[j] for characteristic in characteristics) for j in range(6)]
        if any(exponent % 2 for exponent in exponents):
            raise ValueError(f"formal normalization roots do not cancel for {indices}: {exponents}")
        value = self.field.one
        for characteristic in characteristics:
            value *= quotient_data["factors"][characteristic]
        for root_square, exponent in zip(quotient_data["u"], exponents):
            value *= root_square ** (exponent // 2)
        return value

    def reconstruct_quartic(self, quotient_data):
        product = lambda *indices: self.theta_product(indices, quotient_data)
        a = product(5, 12, 33, 40)
        b = product(21, 28, 49, 56)
        c = product(7, 14, 35, 42)
        alpha12 = (a + b - c) / (2 * product(5, 12, 49, 56))
        alpha13 = (a + c - b) / (2 * product(5, 12, 35, 42))

        d = product(2, 28, 47, 49)
        e = product(5, 27, 40, 54)
        f = product(14, 16, 35, 61)
        alpha22 = (d + e - f) / (2 * product(5, 27, 47, 49))
        alpha23 = (d - e - f) / (2 * product(5, 27, 35, 61))

        g = product(7, 16, 42, 61)
        h = product(12, 27, 33, 54)
        i = product(2, 21, 47, 56)
        # The reduced-characteristic signs in this Aronhold marking are
        # positive for the last two entries of the third row.  The minus signs
        # printed in the 2020 preprint fail Tian's own q=523 source control;
        # the positive signs uniquely reproduce its published quartic moduli.
        alpha32 = (g - h - i) / (2 * product(12, 27, 47, 56))
        alpha33 = (h + g - i) / (2 * product(12, 27, 42, 61))

        one = self.field.one
        alphas = [
            [one, alpha12, alpha13],
            [one, alpha22, alpha23],
            [one, alpha32, alpha33],
        ]
        u_matrix = [
            [one / alphas[0][coordinate], one / alphas[1][coordinate], one / alphas[2][coordinate]]
            for coordinate in range(3)
        ]
        minus_one = -one
        u = solve_linear(u_matrix, [minus_one] * 3)
        k_matrix = [
            [u[line] * alphas[line][coordinate] for line in range(3)]
            for coordinate in range(3)
        ]
        k = solve_linear(k_matrix, [minus_one] * 3)

        left = [
            [one, one, one],
            [one / alphas[0][0], one / alphas[0][1], one / alphas[0][2]],
            [one / alphas[1][0], one / alphas[1][1], one / alphas[1][2]],
            [one / alphas[2][0], one / alphas[2][1], one / alphas[2][2]],
        ]
        right = [
            [one, one, one],
            [k[0] * value for value in alphas[0]],
            [k[1] * value for value in alphas[1]],
            [k[2] * value for value in alphas[2]],
        ]
        xi = [[self.field.zero] * 3 for _ in range(3)]
        for variable in range(3):
            column = solve_linear(
                [row[:] for row in left[:3]],
                [-right[row][variable] for row in range(3)],
            )
            for xi_index, coefficient in enumerate(column):
                xi[xi_index][variable] = coefficient
        for variable in range(3):
            lhs = sum((left[3][j] * xi[j][variable] for j in range(3)), self.field.zero)
            if lhs != -right[3][variable]:
                raise AssertionError("Riemann's overdetermined linear system is inconsistent")

        x = {(1, 0, 0): one}
        y = {(0, 1, 0): one}
        z = {(0, 0, 1): one}
        xi_polynomials = [
            {
                (1, 0, 0): row[0],
                (0, 1, 0): row[1],
                (0, 0, 1): row[2],
            }
            for row in xi
        ]
        diagonal = poly_add(
            poly_add(poly_mul(x, xi_polynomials[0]), poly_mul(y, xi_polynomials[1])),
            poly_scale(poly_mul(z, xi_polynomials[2]), -one),
        )
        quartic = poly_add(
            poly_mul(diagonal, diagonal),
            poly_scale(
                poly_mul(poly_mul(poly_mul(x, y), xi_polynomials[0]), xi_polynomials[1]),
                -4 * one,
            ),
        )
        quartic = {monomial: coefficient for monomial, coefficient in quartic.items() if coefficient}
        if len(quartic) > 15 or any(sum(monomial) != 4 for monomial in quartic):
            raise AssertionError("quartic polynomial has an invalid support")
        leading_monomial = sorted(quartic, reverse=True)[0]
        scale = quartic[leading_monomial].inverse()
        quartic = {monomial: coefficient * scale for monomial, coefficient in quartic.items()}
        lines = [
            [one, self.field.zero, self.field.zero],
            [self.field.zero, one, self.field.zero],
            [self.field.zero, self.field.zero, one],
            [one, one, one],
            *alphas,
        ]
        bitangent_checks = [line_is_bitangent(quartic, line, self.field) for line in lines]
        if not all(bitangent_checks):
            raise AssertionError("Riemann reconstruction failed an Aronhold bitangent check")
        return {
            "alphas": alphas,
            "u": u,
            "k": k,
            "xi": xi,
            "quartic": quartic,
            "aronhold_bitangent_checks": bitangent_checks,
            "prime_field_coefficients": all(
                coefficient ** self.data["curve"]["p"] == coefficient
                for coefficient in quartic.values()
            ),
        }


def poly_add(left, right):
    result = dict(left)
    for monomial, coefficient in right.items():
        result[monomial] = result.get(monomial, 0) + coefficient
        if not result[monomial]:
            del result[monomial]
    return result


def poly_scale(polynomial, scalar):
    return {monomial: scalar * coefficient for monomial, coefficient in polynomial.items()}


def poly_mul(left, right):
    result = {}
    for left_monomial, left_coefficient in left.items():
        for right_monomial, right_coefficient in right.items():
            monomial = tuple(x + y for x, y in zip(left_monomial, right_monomial))
            result[monomial] = result.get(monomial, 0) + left_coefficient * right_coefficient
    return {monomial: coefficient for monomial, coefficient in result.items() if coefficient}


def univariate_trim(polynomial):
    polynomial = list(polynomial)
    while polynomial and not polynomial[-1]:
        polynomial.pop()
    return polynomial


def univariate_add(left, right):
    size = max(len(left), len(right))
    out = []
    for i in range(size):
        out.append((left[i] if i < len(left) else 0) + (right[i] if i < len(right) else 0))
    return univariate_trim(out)


def univariate_mul(left, right):
    if not left or not right:
        return []
    out = [0] * (len(left) + len(right) - 1)
    for i, x in enumerate(left):
        for j, y in enumerate(right):
            out[i + j] = out[i + j] + x * y
    return univariate_trim(out)


def univariate_pow(polynomial, exponent, one):
    result, base = [one], polynomial
    while exponent:
        if exponent & 1:
            result = univariate_mul(result, base)
        base = univariate_mul(base, base)
        exponent >>= 1
    return result


def univariate_divmod(numerator, denominator):
    numerator = univariate_trim(numerator)
    denominator = univariate_trim(denominator)
    if not denominator:
        raise ZeroDivisionError
    quotient = [0] * max(1, len(numerator) - len(denominator) + 1)
    denominator_inverse = denominator[-1].inverse()
    while len(numerator) >= len(denominator) and numerator:
        degree = len(numerator) - len(denominator)
        scale = numerator[-1] * denominator_inverse
        quotient[degree] = scale
        for i, value in enumerate(denominator):
            numerator[degree + i] = numerator[degree + i] - scale * value
        numerator = univariate_trim(numerator)
    return univariate_trim(quotient), numerator


def univariate_gcd(left, right):
    left, right = univariate_trim(left), univariate_trim(right)
    while right:
        _, remainder = univariate_divmod(left, right)
        left, right = right, remainder
    if not left:
        return []
    inverse = left[-1].inverse()
    return [value * inverse for value in left]


def restricted_univariate(quartic, first_vector, second_vector, field):
    result = []
    coordinate_polynomials = [
        [second_vector[i], first_vector[i]] for i in range(3)
    ]
    for monomial, coefficient in quartic.items():
        term = [coefficient]
        for coordinate, exponent in enumerate(monomial):
            term = univariate_mul(
                term, univariate_pow(coordinate_polynomials[coordinate], exponent, field.one)
            )
        result = univariate_add(result, term)
    return univariate_trim(result)


def line_is_bitangent(quartic, line, field):
    a, b, c = line
    zero, one = field.zero, field.one
    if c:
        first = [one, zero, -a / c]
        second = [zero, one, -b / c]
    elif b:
        first = [one, -a / b, zero]
        second = [zero, zero, one]
    else:
        first = [zero, one, zero]
        second = [zero, zero, one]
    parameterizations = [
        (first, second),
        ([x + y for x, y in zip(first, second)], second),
        (first, [x + y for x, y in zip(first, second)]),
    ]
    for first_vector, second_vector in parameterizations:
        polynomial = restricted_univariate(quartic, first_vector, second_vector, field)
        if len(polynomial) != 5:
            continue
        derivative = [(i + 1) * polynomial[i + 1] for i in range(len(polynomial) - 1)]
        gcd = univariate_gcd(polynomial, derivative)
        if len(gcd) - 1 >= 2 and (len(polynomial) - 1) - (len(gcd) - 1) <= 2:
            return True
    return False


def field_value_json(value):
    return value.as_json()


def quartic_json(quartic):
    return [
        {
            "exponents_xyz": list(monomial),
            "coefficient": field_value_json(coefficient),
        }
        for monomial, coefficient in sorted(quartic.items(), reverse=True)
    ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    parser.add_argument("--curve", choices=("P-224", "P-256"), default="P-224")
    args = parser.parse_args()
    started = time.time()
    setup = p224_setup() if args.curve == "P-224" else p256_setup()
    engine = P224ThetaEngine(setup)
    quotient = engine.quotient_theta_data()
    reconstruction = engine.reconstruct_quartic(quotient)
    curve_slug = args.curve.lower().replace("-", "")
    result = {
        "format": f"nist-{curve_slug}-finite-field-theta-stage-v1",
        "curve": args.curve,
        "status": "candidate extension-field quartic constructed with corrected reduced-characteristic signs; external moduli and descent validation required",
        "field_degree": 6,
        "kernel_size": len(engine.kernel),
        "normalization_size": len(engine.alpha),
        "theta_at_generic_nonzero": bool(engine.theta(engine.generic)),
        "odd_theta_zero_count": quotient["odd_zero_count"],
        "even_theta_nonzero_count": quotient["even_nonzero_count"],
        "theta_pattern_violations": quotient["violations"],
        "riemann_linear_system_consistent": True,
        "quartic_term_count": len(reconstruction["quartic"]),
        "quartic_coefficients_in_prime_field": reconstruction["prime_field_coefficients"],
        "aronhold_bitangent_checks": reconstruction["aronhold_bitangent_checks"],
        "quartic": quartic_json(reconstruction["quartic"]),
        "elapsed_seconds": time.time() - started,
    }
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(encoded)
    else:
        print(encoded, end="")


if __name__ == "__main__":
    main()
