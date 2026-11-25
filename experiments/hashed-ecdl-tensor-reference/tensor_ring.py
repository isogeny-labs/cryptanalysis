"""Exact unramified extension arithmetic used by the contraction construction.

Elements are coefficient tuples in (Z/2^p Z)[U]/f(U). The same monic binary
irreducible f is used at every recursive precision. Only ell=1 is needed for
integer-valued Boolean tensor networks and their recursive packet tensors.
"""

from fractions import Fraction
from functools import lru_cache

from ecc2k import BinaryField


def valuation2(value: int) -> int:
    if value == 0:
        raise ValueError("valuation of zero is infinite")
    return (abs(value) & -abs(value)).bit_length() - 1


@lru_cache(maxsize=32)
def binary_irreducible(degree: int) -> int:
    if degree == 1:
        return 3
    for lower in range(1, 1 << degree, 2):
        candidate = (1 << degree) | lower
        if BinaryField(degree, candidate).irreducible():
            return candidate
    raise ArithmeticError("no irreducible binary polynomial found")


class UnramifiedRing:
    def __init__(self, degree: int, precision: int, polynomial: int | None = None):
        if degree < 1 or precision < 1:
            raise ValueError("degree and precision must be positive")
        self.degree, self.precision = degree, precision
        self.polynomial = binary_irreducible(degree) if polynomial is None else polynomial
        if self.polynomial.bit_length() != degree + 1:
            raise ValueError("wrong polynomial degree")
        self.modulus, self.mask = 1 << precision, (1 << precision) - 1
        self.lower_terms = tuple(i for i in range(degree) if self.polynomial >> i & 1)
        self.zero, self.one = (0,) * degree, (1,) + (0,) * (degree - 1)

    def at_precision(self, precision: int):
        return UnramifiedRing(self.degree, precision, self.polynomial)

    def coerce(self, value):
        if isinstance(value, int):
            return (value & self.mask,) + (0,) * (self.degree - 1)
        if len(value) != self.degree:
            raise ValueError("extension basis mismatch")
        return tuple(v & self.mask for v in value)

    def lift_from(self, value, creation_precision: int):
        if isinstance(value, int):
            return self.coerce(value & ((1 << creation_precision) - 1))
        mask = (1 << creation_precision) - 1
        return self.coerce(tuple(v & mask for v in value))

    def residue_point(self, index: int):
        if not 0 <= index < 1 << self.degree:
            raise ValueError("not enough distinct residue-field interpolation points")
        return tuple((index >> i) & 1 for i in range(self.degree))

    def add(self, left, right):
        return tuple((a + b) & self.mask for a, b in zip(left, right))

    def neg(self, value):
        return tuple((-a) & self.mask for a in value)

    def sub(self, left, right):
        return tuple((a - b) & self.mask for a, b in zip(left, right))

    def scale(self, value, scalar: int):
        if not scalar or not any(value):
            return self.zero
        return tuple((a * scalar) & self.mask for a in value)

    def mul(self, left, right):
        if not any(left) or not any(right):
            return self.zero
        if not any(left[1:]):
            return self.scale(right, left[0])
        if not any(right[1:]):
            return self.scale(left, right[0])
        values = [0] * (2 * self.degree - 1)
        for i, a in enumerate(left):
            if a:
                for j, b in enumerate(right):
                    if b:
                        values[i + j] += a * b
        for i in range(len(values) - 1, self.degree - 1, -1):
            value = values[i]
            if value:
                for term in self.lower_terms:
                    values[i - self.degree + term] -= value
        return tuple(value & self.mask for value in values[:self.degree])

    def power(self, value, exponent: int):
        if exponent < 0:
            return self.power(self.inv(value), -exponent)
        result = self.one
        while exponent:
            if exponent & 1:
                result = self.mul(result, value)
            exponent >>= 1
            if exponent:
                value = self.mul(value, value)
        return result

    def inv(self, value):
        if not any(value[1:]):
            if value[0] % 2 == 0:
                raise ZeroDivisionError("nonunit in unramified ring")
            return self.coerce(pow(value[0], -1, self.modulus))
        reduced = sum((v & 1) << i for i, v in enumerate(value))
        if not reduced:
            raise ZeroDivisionError("nonunit in unramified ring")
        if self.degree == 1:
            inverse = 1
        else:
            inverse = BinaryField(self.degree, self.polynomial).inv(reduced)
        result = self.residue_point(inverse)
        precision = 1
        while precision < self.precision:
            result = self.mul(result, self.sub(self.coerce(2), self.mul(value, result)))
            precision *= 2
        return result

    def fraction(self, value: Fraction):
        value = Fraction(value)
        if value.denominator % 2 == 0:
            raise ValueError("fraction is not two-adically integral")
        return self.coerce(value.numerator * pow(value.denominator, -1, self.modulus))


def polynomial_product(left, right, ring: UnramifiedRing, limit: int | None = None):
    size = len(left) + len(right) - 1
    if limit is not None:
        size = min(size, limit)
    result = [ring.zero] * max(0, size)
    for i, a in enumerate(left):
        for j, b in enumerate(right[:max(0, size - i)]):
            result[i + j] = ring.add(result[i + j], ring.mul(a, b))
    return result


def interpolate_low(nodes, values, ring: UnramifiedRing, limit: int):
    """Newton interpolation at residue-distinct nodes, retaining low powers."""
    if len(nodes) != len(values) or not nodes:
        raise ValueError("invalid interpolation data")
    coefficients = list(values)
    inverses = {}
    for order in range(1, len(nodes)):
        for j in range(len(nodes) - 1, order - 1, -1):
            difference = ring.sub(nodes[j], nodes[j - order])
            if difference not in inverses:
                inverses[difference] = ring.inv(difference)
            coefficients[j] = ring.mul(ring.sub(coefficients[j], coefficients[j - 1]), inverses[difference])
    result = [coefficients[-1]]
    for j in range(len(nodes) - 2, -1, -1):
        result = polynomial_product(result, [ring.neg(nodes[j]), ring.one], ring, limit)
        result[0] = ring.add(result[0], coefficients[j])
    return result + [ring.zero] * (limit - len(result))
