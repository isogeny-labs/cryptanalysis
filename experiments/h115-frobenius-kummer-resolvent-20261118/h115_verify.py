#!/usr/bin/env python3
"""Independent verifier for the frozen H115 Frobenius--Kummer experiment."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Optional


CURVES_SHA256 = "babd2556951ecfcaee66a5c6966364ca136bf1f62fb0a51511f391768255d295"
PROTOCOL_SHA256 = "c8412d94f3e6cc928c13c93572a8796cea3a983b5fcd4e6b043a75bc5b1a2363"
PREDICATE_COUNT = 648
CHANNEL_COUNT = 54
MOMENT_COUNT = 8


class VerifyError(Exception):
    """A deterministic evidence-verification failure."""


@dataclass(frozen=True)
class Spec:
    slug: str
    p: int
    a: int
    b: int
    order: int
    trace: int
    degree: int
    extension_size: int


SPECS = (
    Spec("h115-fp7-a1-b1-r5-d4", 7, 1, 1, 5, 3, 4, 2401),
    Spec("h115-fp5-a2-b1-r7-d6", 5, 2, 1, 7, -1, 6, 15625),
    Spec("h115-fp13-a2-b4-r17-d4", 13, 2, 4, 17, -3, 4, 28561),
    Spec("h115-fp31-a1-b19-r37-d4", 31, 1, 19, 37, -5, 4, 923521),
    Spec("h115-fp47-a1-b38-r61-d3", 47, 1, 38, 61, -13, 3, 103823),
)
SPEC_BY_SLUG = {spec.slug: spec for spec in SPECS}

Elt = tuple[int, ...]
Point = Optional[tuple[Elt, Elt]]


def trim(poly: list[int]) -> list[int]:
    while len(poly) > 1 and poly[-1] == 0:
        poly.pop()
    return poly


def poly_sub(left: list[int], right: list[int], p: int) -> list[int]:
    size = max(len(left), len(right))
    return trim([
        ((left[index] if index < len(left) else 0)
         - (right[index] if index < len(right) else 0)) % p
        for index in range(size)
    ])


def poly_mod(numerator: list[int], denominator: list[int], p: int) -> list[int]:
    numerator = trim(numerator[:])
    denominator = trim(denominator[:])
    if denominator == [0]:
        raise VerifyError("polynomial division by zero")
    inverse_lead = pow(denominator[-1], p - 2, p)
    while len(numerator) >= len(denominator) and numerator != [0]:
        shift = len(numerator) - len(denominator)
        coefficient = numerator[-1] * inverse_lead % p
        for index, term in enumerate(denominator):
            position = shift + index
            numerator[position] = (numerator[position] - coefficient * term) % p
        trim(numerator)
    return numerator


def poly_mul_mod(left: list[int], right: list[int], modulus: list[int], p: int) -> list[int]:
    product = [0] * (len(left) + len(right) - 1)
    for i, a_value in enumerate(left):
        for j, b_value in enumerate(right):
            product[i + j] = (product[i + j] + a_value * b_value) % p
    return poly_mod(product, modulus, p)


def poly_pow_mod(base: list[int], exponent: int, modulus: list[int], p: int) -> list[int]:
    result = [1]
    while exponent:
        if exponent & 1:
            result = poly_mul_mod(result, base, modulus, p)
        exponent >>= 1
        if exponent:
            base = poly_mul_mod(base, base, modulus, p)
    return result


def poly_gcd(left: list[int], right: list[int], p: int) -> list[int]:
    left, right = trim(left[:]), trim(right[:])
    while right != [0]:
        left, right = right, poly_mod(left, right, p)
    inverse = pow(left[-1], p - 2, p)
    return [(coefficient * inverse) % p for coefficient in left]


def prime_divisors(value: int) -> list[int]:
    result: list[int] = []
    candidate = 2
    while candidate * candidate <= value:
        if value % candidate == 0:
            result.append(candidate)
            while value % candidate == 0:
                value //= candidate
        candidate += 1
    if value > 1:
        result.append(value)
    return result


def irreducible(modulus: list[int], p: int) -> bool:
    degree = len(modulus) - 1
    if degree < 1 or modulus[-1] != 1:
        return False
    x_poly = [0, 1]
    powers = [x_poly]
    for _ in range(degree):
        powers.append(poly_pow_mod(powers[-1], p, modulus, p))
    if poly_sub(powers[degree], x_poly, p) != [0]:
        return False
    for divisor in prime_divisors(degree):
        difference = poly_sub(powers[degree // divisor], x_poly, p)
        if poly_gcd(modulus, difference, p) != [1]:
            return False
    return True


def first_irreducible(p: int, degree: int) -> tuple[int, ...]:
    for code in range(p ** degree):
        remainder = code
        coefficients = [0] * (degree + 1)
        for index in range(degree):
            place = p ** (degree - 1 - index)
            coefficients[index], remainder = divmod(remainder, place)
        coefficients[degree] = 1
        if irreducible(coefficients, p):
            return tuple(coefficients)
    raise VerifyError(f"no irreducible polynomial for p={p}, degree={degree}")


class Fq:
    """Tuple-valued finite field, independent of the Rust representation."""

    def __init__(self, p: int, degree: int, modulus: tuple[int, ...]):
        if len(modulus) != degree + 1 or modulus[-1] != 1:
            raise VerifyError("invalid extension modulus")
        self.p = p
        self.degree = degree
        self.modulus = modulus
        self.q = p ** degree
        self.zero = (0,) * degree
        self.one = (1,) + (0,) * (degree - 1)

    def base(self, value: int) -> Elt:
        return (value % self.p,) + (0,) * (self.degree - 1)

    def elt(self, index: int) -> Elt:
        if not 0 <= index < self.q:
            raise VerifyError("field serialization out of range")
        coefficients = []
        for _ in range(self.degree):
            index, coefficient = divmod(index, self.p)
            coefficients.append(coefficient)
        return tuple(coefficients)

    def index(self, value: Elt) -> int:
        if len(value) != self.degree:
            raise VerifyError("field element has wrong degree")
        result = 0
        place = 1
        for coefficient in value:
            if not 0 <= coefficient < self.p:
                raise VerifyError("noncanonical field coefficient")
            result += coefficient * place
            place *= self.p
        return result

    def add(self, left: Elt, right: Elt) -> Elt:
        return tuple((a_value + b_value) % self.p for a_value, b_value in zip(left, right))

    def neg(self, value: Elt) -> Elt:
        return tuple((-coefficient) % self.p for coefficient in value)

    def sub(self, left: Elt, right: Elt) -> Elt:
        return self.add(left, self.neg(right))

    def mul(self, left: Elt, right: Elt) -> Elt:
        product = [0] * (2 * self.degree - 1)
        for i, a_value in enumerate(left):
            for j, b_value in enumerate(right):
                product[i + j] = (product[i + j] + a_value * b_value) % self.p
        for power in range(2 * self.degree - 2, self.degree - 1, -1):
            leading = product[power]
            for index in range(self.degree):
                position = power - self.degree + index
                product[position] = (product[position] - leading * self.modulus[index]) % self.p
        return tuple(product[:self.degree])

    def power(self, base: Elt, exponent: int) -> Elt:
        result = self.one
        while exponent:
            if exponent & 1:
                result = self.mul(result, base)
            exponent >>= 1
            if exponent:
                base = self.mul(base, base)
        return result

    def inverse(self, value: Elt) -> Elt:
        if value == self.zero:
            raise VerifyError("field inversion of zero")
        return self.power(value, self.q - 2)

    def divide(self, numerator: Elt, denominator: Elt) -> Elt:
        return self.mul(numerator, self.inverse(denominator))

    def frobenius(self, value: Elt) -> Elt:
        return self.power(value, self.p)

    def frobenius_power(self, value: Elt, exponent: int) -> Elt:
        for _ in range(exponent):
            value = self.frobenius(value)
        return value

    def square_root(self, value: Elt) -> Optional[Elt]:
        if value == self.zero:
            return value
        if self.power(value, (self.q - 1) // 2) != self.one:
            return None
        odd = self.q - 1
        twos = 0
        while odd % 2 == 0:
            odd //= 2
            twos += 1
        if twos == 1:
            root = self.power(value, (self.q + 1) // 4)
        else:
            nonresidue = next(
                (self.elt(index) for index in range(2, self.q)
                 if self.power(self.elt(index), (self.q - 1) // 2) == self.neg(self.one)),
                None,
            )
            if nonresidue is None:
                raise VerifyError("quadratic nonresidue not found")
            c_value = self.power(nonresidue, odd)
            root = self.power(value, (odd + 1) // 2)
            residue = self.power(value, odd)
            active_twos = twos
            while residue != self.one:
                probe = self.mul(residue, residue)
                index = 1
                while index < active_twos and probe != self.one:
                    probe = self.mul(probe, probe)
                    index += 1
                if index == active_twos:
                    raise VerifyError("Tonelli-Shanks invariant failure")
                b_value = self.power(c_value, 1 << (active_twos - index - 1))
                root = self.mul(root, b_value)
                b_squared = self.mul(b_value, b_value)
                residue = self.mul(residue, b_squared)
                c_value = b_squared
                active_twos = index
        if self.mul(root, root) != value:
            raise VerifyError("square-root check failed")
        negative = self.neg(root)
        return root if self.index(root) <= self.index(negative) else negative

    def to_base(self, value: Elt) -> int:
        if any(value[index] for index in range(1, self.degree)):
            raise VerifyError(f"moment is not in base field: {self.index(value)}")
        return value[0]


class EC:
    def __init__(self, field: Fq, a_value: int | Elt, b_value: int | Elt):
        self.field = field
        self.a = field.base(a_value) if isinstance(a_value, int) else a_value
        self.b = field.base(b_value) if isinstance(b_value, int) else b_value

    def on_curve(self, point: Point) -> bool:
        if point is None:
            return True
        x_value, y_value = point
        left = self.field.mul(y_value, y_value)
        x_squared = self.field.mul(x_value, x_value)
        right = self.field.add(
            self.field.add(self.field.mul(x_squared, x_value), self.field.mul(self.a, x_value)),
            self.b,
        )
        return left == right

    def neg(self, point: Point) -> Point:
        if point is None:
            return None
        return point[0], self.field.neg(point[1])

    def add(self, left: Point, right: Point) -> Point:
        if left is None:
            return right
        if right is None:
            return left
        x_left, y_left = left
        x_right, y_right = right
        if x_left == x_right and self.field.add(y_left, y_right) == self.field.zero:
            return None
        if left == right:
            numerator = self.field.add(
                self.field.mul(self.field.base(3), self.field.mul(x_left, x_left)), self.a
            )
            denominator = self.field.mul(self.field.base(2), y_left)
        else:
            numerator = self.field.sub(y_right, y_left)
            denominator = self.field.sub(x_right, x_left)
        slope = self.field.divide(numerator, denominator)
        x_result = self.field.sub(self.field.sub(self.field.mul(slope, slope), x_left), x_right)
        y_result = self.field.sub(self.field.mul(slope, self.field.sub(x_left, x_result)), y_left)
        result = x_result, y_result
        if not self.on_curve(result):
            raise VerifyError("elliptic addition left the curve")
        return result

    def sub(self, left: Point, right: Point) -> Point:
        return self.add(left, self.neg(right))

    def scale(self, scalar: int, point: Point) -> Point:
        if scalar < 0:
            return self.neg(self.scale(-scalar, point))
        result = None
        addend = point
        while scalar:
            if scalar & 1:
                result = self.add(result, addend)
            scalar >>= 1
            if scalar:
                addend = self.add(addend, addend)
        return result

    def frobenius(self, point: Point) -> Point:
        if point is None:
            return None
        return self.field.frobenius(point[0]), self.field.frobenius(point[1])

    def frobenius_power(self, point: Point, exponent: int) -> Point:
        for _ in range(exponent):
            point = self.frobenius(point)
        return point


def extension_group_order(spec: Spec) -> int:
    previous_previous = 2
    previous = spec.trace
    if spec.degree == 0:
        power_sum = previous_previous
    elif spec.degree == 1:
        power_sum = previous
    else:
        for _ in range(2, spec.degree + 1):
            previous_previous, previous = previous, spec.trace * previous - spec.p * previous_previous
        power_sum = previous
    return spec.p ** spec.degree + 1 - power_sum


@dataclass
class Context:
    spec: Spec
    field: Fq
    curve: EC
    group_order: int
    cofactor: int
    enumerated_states: int
    base_generator: Point
    transverse: Point
    kernel_generator: Point
    torsion: set[Point]
    kernel: set[Point]

    def verschiebung(self, point: Point, curve: Optional[EC] = None) -> Point:
        active = curve or self.curve
        return active.scale(self.spec.p, active.frobenius_power(point, self.spec.degree - 1))


def first_base_point(curve: EC, p: int) -> Point:
    for x_value in range(p):
        for y_value in range(p):
            point = curve.field.base(x_value), curve.field.base(y_value)
            if curve.on_curve(point):
                return point
    raise VerifyError("base point not found")


def build_context(spec: Spec) -> Context:
    modulus = first_irreducible(spec.p, spec.degree)
    field = Fq(spec.p, spec.degree, modulus)
    if field.q != spec.extension_size:
        raise VerifyError(f"extension size mismatch for {spec.slug}")
    curve = EC(field, spec.a, spec.b)
    group_order = extension_group_order(spec)
    r_squared = spec.order * spec.order
    if group_order % r_squared:
        raise VerifyError(f"r^2 does not divide extension order for {spec.slug}")
    cofactor = group_order // r_squared
    if math.gcd(cofactor, spec.order) != 1:
        raise VerifyError(f"cofactor is divisible by r for {spec.slug}")
    generator = first_base_point(curve, spec.p)
    if curve.scale(spec.order, generator) is not None:
        raise VerifyError("base generator order mismatch")
    transverse = None
    kernel_generator = None
    enumerated_states = 0
    for x_index in range(field.q):
        enumerated_states += 1
        x_value = field.elt(x_index)
        rhs = field.add(
            field.add(field.mul(field.mul(x_value, x_value), x_value), field.mul(curve.a, x_value)),
            curve.b,
        )
        y_value = field.square_root(rhs)
        if y_value is None:
            continue
        projected = curve.scale(cofactor, (x_value, y_value))
        if projected is None or curve.scale(spec.order, projected) is not None:
            continue
        candidate_kernel = curve.sub(curve.frobenius(projected), projected)
        if candidate_kernel is None:
            continue
        transverse, kernel_generator = projected, candidate_kernel
        break
    if transverse is None or kernel_generator is None:
        raise VerifyError(f"transverse point not found for {spec.slug}")
    torsion: set[Point] = set()
    for left_scalar in range(spec.order):
        left = curve.scale(left_scalar, generator)
        for right_scalar in range(spec.order):
            point = curve.add(left, curve.scale(right_scalar, transverse))
            if curve.scale(spec.order, point) is not None:
                raise VerifyError("torsion-table point is not killed by r")
            if point in torsion:
                raise VerifyError("dependent torsion basis")
            torsion.add(point)
    kernel_line = {curve.scale(scalar, kernel_generator) for scalar in range(spec.order)}
    checked_kernel: set[Point] = set()
    provisional = Context(
        spec, field, curve, group_order, cofactor, enumerated_states,
        generator, transverse, kernel_generator, torsion, set(),
    )
    for point in torsion:
        pi_point = curve.frobenius(point)
        characteristic = curve.add(
            curve.sub(curve.frobenius(pi_point), curve.scale(spec.trace, pi_point)),
            curve.scale(spec.p, point),
        )
        if characteristic is not None:
            raise VerifyError("Frobenius characteristic equation failed")
        cocycle = curve.sub(pi_point, point)
        factor = curve.sub(provisional.verschiebung(cocycle), cocycle)
        if factor != curve.scale(spec.order, point):
            raise VerifyError("Frobenius/Verschiebung factorization failed")
        if curve.sub(provisional.verschiebung(point), point) is None:
            checked_kernel.add(point)
    if checked_kernel != kernel_line:
        raise VerifyError("image/kernel line mismatch")
    if curve.frobenius(kernel_generator) != curve.scale(spec.p % spec.order, kernel_generator):
        raise VerifyError("kernel Frobenius eigenvalue mismatch")
    provisional.kernel = checked_kernel
    return provisional


def raw_moments(
    curve: EC,
    shift: Point,
    line: Point,
    order: int,
    omit_infinity: bool,
) -> tuple[list[Elt], list[Elt], int]:
    field = curve.field
    x_sums = [field.zero] * MOMENT_COUNT
    y_sums = [field.zero] * MOMENT_COUNT
    terms = 0
    for scalar in range(order):
        point = curve.add(shift, curve.scale(scalar, line))
        if point is None:
            if omit_infinity:
                continue
            raise VerifyError("infinity in affine moment fiber")
        x_value, y_value = point
        x_power = field.one
        terms += 1
        for index in range(MOMENT_COUNT):
            y_sums[index] = field.add(y_sums[index], field.mul(y_value, x_power))
            x_power = field.mul(x_power, x_value)
            x_sums[index] = field.add(x_sums[index], x_power)
    return x_sums, y_sums, terms


def descend(field: Fq, value: Elt) -> Elt:
    trace = field.zero
    conjugate = value
    for _ in range(field.degree):
        trace = field.add(trace, conjugate)
        conjugate = field.frobenius(conjugate)
    inverse_degree = pow(field.degree % field.p, -1, field.p)
    return field.mul(trace, field.base(inverse_degree))


def moments(
    curve: EC,
    shift: Point,
    line: Point,
    order: int,
    use_descent: bool,
    omit_infinity: bool,
) -> tuple[tuple[tuple[int, ...], tuple[int, ...]], int]:
    x_sums, y_sums, terms = raw_moments(curve, shift, line, order, omit_infinity)
    if use_descent:
        x_sums = [descend(curve.field, value) for value in x_sums]
        y_sums = [descend(curve.field, value) for value in y_sums]
    return (
        tuple(curve.field.to_base(value) for value in x_sums),
        tuple(curve.field.to_base(value) for value in y_sums),
    ), terms


def ratio(numerator: int, denominator: int, p: int) -> int:
    return 0 if denominator == 0 else numerator * pow(denominator, -1, p) % p


def make_channels(
    target: tuple[tuple[int, ...], tuple[int, ...]],
    generator: tuple[tuple[int, ...], tuple[int, ...]],
    p: int,
) -> tuple[int, ...]:
    target_x, target_y = target
    generator_x, generator_y = generator
    result = list(target_x) + list(target_y)
    result.extend(ratio(target_values[index], generator_values[index], p)
                  for target_values, generator_values in
                  ((target_x, generator_x), (target_y, generator_y))
                  for index in range(MOMENT_COUNT))
    result.extend(
        ratio(
            target_values[index] * generator_values[index + 1] % p,
            target_values[index + 1] * generator_values[index] % p,
            p,
        )
        for target_values, generator_values in
        ((target_x, generator_x), (target_y, generator_y))
        for index in range(MOMENT_COUNT - 1)
    )
    result.extend(
        ratio(
            target_y[index] * generator_x[index] % p,
            target_x[index] * generator_y[index] % p,
            p,
        )
        for index in range(MOMENT_COUNT)
    )
    if len(result) != CHANNEL_COUNT:
        raise VerifyError(f"constructed {len(result)} channels")
    return tuple(result)


PERMUTATIONS_THREE = (
    (0, 1, 2), (0, 2, 1), (1, 0, 2),
    (1, 2, 0), (2, 0, 1), (2, 1, 0),
)


def predicate_parts(predicate_id: int) -> tuple[int, int, int]:
    if not 0 <= predicate_id < PREDICATE_COUNT:
        raise VerifyError(f"predicate ID out of range: {predicate_id}")
    channel, remainder = divmod(predicate_id, 12)
    permutation_two, permutation_three = divmod(remainder, 6)
    return channel, permutation_two, permutation_three


def predict(predicate_id: int, channel_values: tuple[int, ...]) -> int:
    channel, permutation_two, permutation_three = predicate_parts(predicate_id)
    value = channel_values[channel]
    residue_two = value % 2
    mapped_two = residue_two if permutation_two == 0 else 1 - residue_two
    mapped_three = PERMUTATIONS_THREE[permutation_three][value % 3]
    return (3 * mapped_two + 4 * mapped_three) % 6


def channel_cost(
    target: tuple[tuple[int, ...], tuple[int, ...]],
    generator: tuple[tuple[int, ...], tuple[int, ...]],
) -> tuple[int, int]:
    target_x, target_y = target
    generator_x, generator_y = generator
    multiplications = 0
    inversions = 0
    for denominator in generator_x + generator_y:
        if denominator:
            multiplications += 1
            inversions += 1
    for target_values, generator_values in ((target_x, generator_x), (target_y, generator_y)):
        for index in range(MOMENT_COUNT - 1):
            multiplications += 2
            if target_values[index + 1] and generator_values[index]:
                multiplications += 1
                inversions += 1
    for index in range(MOMENT_COUNT):
        multiplications += 2
        if target_x[index] and generator_y[index]:
            multiplications += 1
            inversions += 1
    return multiplications, inversions


class SplitMix64:
    def __init__(self, seed: int):
        self.state = seed

    def next(self) -> int:
        mask = (1 << 64) - 1
        self.state = (self.state + 0x9E3779B97F4A7C15) & mask
        value = self.state
        value = ((value ^ (value >> 30)) * 0xBF58476D1CE4E5B9) & mask
        value = ((value ^ (value >> 27)) * 0x94D049BB133111EB) & mask
        return value ^ (value >> 31)


def seeded_rng(domain: str, spec: Spec, multiplier: int, replicate: int) -> SplitMix64:
    material = (
        domain.encode("ascii") + b"\x00" + spec.slug.encode("ascii") + b"\x00"
        + str(multiplier).encode("ascii") + b"\x00" + str(replicate).encode("ascii")
    )
    seed = int.from_bytes(hashlib.sha256(material).digest()[:8], "big")
    return SplitMix64(seed)


def shuffled_labels(spec: Spec, multiplier: int, replicate: int) -> list[int]:
    labels = [scalar % 6 for scalar in range(1, spec.order)]
    rng = seeded_rng("matched-label", spec, multiplier, replicate)
    for upper in range(len(labels) - 1, 0, -1):
        index = rng.next() % (upper + 1)
        labels[upper], labels[index] = labels[index], labels[upper]
    return labels


def random_line(context: Context, multiplier: int, replicate: int) -> tuple[int, Point]:
    used: set[int] = set()
    generator = context.curve.scale(multiplier, context.base_generator)
    selected: Optional[tuple[int, Point]] = None
    for active_replicate in range(replicate + 1):
        rng = seeded_rng("random-line", context.spec, multiplier, active_replicate)
        selected = None
        for _ in range(context.spec.order * 4):
            left = rng.next() % context.spec.order
            right = rng.next() % context.spec.order
            if left == 0 or right == 0:
                continue
            normalized = left * pow(right, -1, context.spec.order) % context.spec.order
            if normalized in used:
                continue
            used.add(normalized)
            line = context.curve.add(
                context.curve.scale(normalized, generator), context.transverse
            )
            pi_line = context.curve.frobenius(line)
            eigen = any(
                context.curve.scale(scalar, line) == pi_line
                for scalar in range(context.spec.order)
            )
            if not eigen:
                selected = normalized, line
                break
        if selected is None:
            raise VerifyError("random non-eigen line not found")
    assert selected is not None
    return selected


def coordinate_map(field: Fq, point: Point, lambda_value: int = 2) -> Point:
    if point is None:
        return None
    scale = field.base(lambda_value)
    lambda_squared = field.mul(scale, scale)
    lambda_cubed = field.mul(lambda_squared, scale)
    return field.mul(lambda_squared, point[0]), field.mul(lambda_cubed, point[1])


Moment = tuple[tuple[int, ...], tuple[int, ...]]


class Expected:
    def __init__(self):
        self.contexts = {spec.slug: build_context(spec) for spec in SPECS}
        self.moment_cache: dict[tuple[str, int, int, str, Optional[int]], tuple[Moment, int]] = {}

    def moment(
        self,
        spec: Spec,
        multiplier: int,
        scalar: int,
        record_class: str,
        replicate: Optional[int],
    ) -> tuple[Moment, int]:
        key = spec.slug, multiplier, scalar, record_class, replicate
        if key in self.moment_cache:
            return self.moment_cache[key]
        context = self.contexts[spec.slug]
        generator = context.curve.scale(multiplier, context.base_generator)
        inverse_p_minus_one = pow((spec.p - 1) % spec.order, -1, spec.order)
        target = context.curve.scale(scalar, generator)
        section = context.curve.scale(inverse_p_minus_one, target)
        if record_class == "candidate":
            value = moments(
                context.curve, section, context.kernel_generator,
                spec.order, False, False,
            )
            self.verify_candidate_fiber(context, target, section)
        elif record_class == "random-line":
            if replicate is None:
                raise VerifyError("random-line record lacks replicate")
            _, line = random_line(context, multiplier, replicate)
            value = moments(context.curve, section, line, spec.order, True, False)
        elif record_class == "rational-line":
            value = moments(context.curve, None, generator, spec.order, True, True)
        elif record_class == "coordinate-isomorphism":
            field = context.field
            scale = field.base(2)
            lambda_squared = field.mul(scale, scale)
            lambda_fourth = field.mul(lambda_squared, lambda_squared)
            lambda_sixth = field.mul(lambda_fourth, lambda_squared)
            iso_curve = EC(
                field,
                field.mul(lambda_fourth, context.curve.a),
                field.mul(lambda_sixth, context.curve.b),
            )
            iso_generator = coordinate_map(field, generator)
            iso_target = iso_curve.scale(scalar, iso_generator)
            iso_section = iso_curve.scale(inverse_p_minus_one, iso_target)
            iso_kernel = coordinate_map(field, context.kernel_generator)
            value = moments(iso_curve, iso_section, iso_kernel, spec.order, False, False)
        else:
            raise VerifyError(f"unknown moment class {record_class!r}")
        self.moment_cache[key] = value
        return value

    @staticmethod
    def verify_candidate_fiber(context: Context, target: Point, section: Point) -> None:
        points: set[Point] = set()
        for scalar in range(context.spec.order):
            point = context.curve.add(
                section, context.curve.scale(scalar, context.kernel_generator)
            )
            if point in points:
                raise VerifyError("candidate fiber duplicate")
            points.add(point)
            if context.curve.sub(context.verschiebung(point), point) != target:
                raise VerifyError("candidate fiber image mismatch")
        if len(points) != context.spec.order:
            raise VerifyError("candidate fiber cardinality mismatch")


def require_dict(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise VerifyError(f"{context} is not an object")
    return value


def require_int(value: Any, context: str, minimum: Optional[int] = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise VerifyError(f"{context} is not an integer")
    if minimum is not None and value < minimum:
        raise VerifyError(f"{context} is below {minimum}")
    return value


def require_int_list(value: Any, context: str, length: Optional[int] = None) -> list[int]:
    if not isinstance(value, list):
        raise VerifyError(f"{context} is not an array")
    result = [require_int(item, f"{context}[{index}]", 0) for index, item in enumerate(value)]
    if length is not None and len(result) != length:
        raise VerifyError(f"{context} length {len(result)} != {length}")
    return result


def require_bool_list(value: Any, context: str, length: int) -> list[bool]:
    if not isinstance(value, list) or len(value) != length or not all(isinstance(item, bool) for item in value):
        raise VerifyError(f"{context} is not a {length}-boolean array")
    return value


def parse_point(field: Fq, value: Any, context: str) -> Point:
    if value is None:
        return None
    coordinates = require_int_list(value, context, 2)
    return field.elt(coordinates[0]), field.elt(coordinates[1])


def parse_moment(value: Any, context: str) -> Moment:
    obj = require_dict(value, context)
    if set(obj) != {"x", "y"}:
        raise VerifyError(f"{context} keys mismatch")
    return (
        tuple(require_int_list(obj["x"], f"{context}.x", MOMENT_COUNT)),
        tuple(require_int_list(obj["y"], f"{context}.y", MOMENT_COUNT)),
    )


def validate_counter_object(value: Any, context: str) -> None:
    obj = require_dict(value, context)
    expected_keys = {
        "base_additions", "base_multiplications", "base_inversions",
        "extension_additions", "extension_multiplications", "extension_inversions",
        "frobenius_maps", "point_additions", "scalar_multiplications",
    }
    if set(obj) != expected_keys:
        raise VerifyError(f"{context} counter keys mismatch")
    for key, item in obj.items():
        require_int(item, f"{context}.{key}", 0)


def row_scores(channels_by_scalar: dict[int, tuple[int, ...]], spec: Spec, labels: list[int]) -> list[int]:
    if len(labels) != spec.order - 1:
        raise VerifyError("label vector length mismatch")
    scores = [0] * PREDICATE_COUNT
    for scalar, label in enumerate(labels, start=1):
        if scalar not in channels_by_scalar:
            raise VerifyError("candidate/control channel table gap")
        channel_values = channels_by_scalar[scalar]
        for predicate_id in range(PREDICATE_COUNT):
            if predict(predicate_id, channel_values) == label:
                scores[predicate_id] += 1
    return scores


def best(scores: list[int]) -> tuple[int, list[int]]:
    best_score = max(scores, default=0)
    return best_score, [index for index, score in enumerate(scores) if score == best_score]


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


@dataclass
class ParsedEvidence:
    data_records: list[dict[str, Any]]
    summary: dict[str, Any]
    raw_digest: str
    raw_bytes: int


def parse_evidence(path: Path) -> ParsedEvidence:
    payload = path.read_bytes()
    lines = payload.splitlines(keepends=True)
    if len(lines) < 2:
        raise VerifyError("evidence file is too short")
    if any(not line.endswith(b"\n") for line in lines):
        raise VerifyError("every evidence line must end in newline")
    objects: list[dict[str, Any]] = []
    for index, line in enumerate(lines):
        try:
            value = json.loads(line)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise VerifyError(f"invalid JSON on line {index + 1}: {error}") from error
        obj = require_dict(value, f"line {index + 1}")
        if canonical_json(obj) + b"\n" != line:
            raise VerifyError(f"line {index + 1} is not canonical JSON")
        objects.append(obj)
    summary = objects[-1]
    if summary.get("type") != "summary":
        raise VerifyError("last record is not the summary")
    if any(record.get("type") == "summary" for record in objects[:-1]):
        raise VerifyError("summary appears before the last record")
    raw_payload = b"".join(lines[:-1])
    return ParsedEvidence(
        objects[:-1], summary, hashlib.sha256(raw_payload).hexdigest(), len(raw_payload)
    )


def verify_evidence(path: Path) -> dict[str, Any]:
    evidence = parse_evidence(path)
    expected = Expected()
    meta_seen = 0
    curves_seen: set[str] = set()
    candidate: dict[tuple[str, int], dict[int, tuple[int, ...]]] = {}
    random_controls: dict[tuple[str, int, int], dict[int, tuple[int, ...]]] = {}
    row_summaries: list[dict[str, Any]] = []
    control_summaries: list[dict[str, Any]] = []
    label_controls: list[dict[str, Any]] = []
    class_counts = {
        "candidate": 0,
        "random-line": 0,
        "rational-line": 0,
        "coordinate-isomorphism": 0,
    }
    moment_terms = 0
    channel_multiplications = 0
    channel_inversions = 0

    for record_index, record in enumerate(evidence.data_records):
        record_type = record.get("type")
        where = f"record {record_index + 1}"
        if record_type == "meta":
            meta_seen += 1
            expected_meta = {
                "type": "meta",
                "schema": "h115.raw/v1",
                "curves_sha256": CURVES_SHA256,
                "protocol_sha256": PROTOCOL_SHA256,
                "predicate_count": PREDICATE_COUNT,
                "channel_count": CHANNEL_COUNT,
                "radix": 6,
            }
            if record != expected_meta or record_index != 0:
                raise VerifyError("metadata record mismatch or wrong position")
        elif record_type == "curve":
            expected_keys = {
                "type", "curve", "modulus", "extension_order", "base_generator",
                "transverse", "kernel_generator", "torsion_count", "kernel_count",
                "cofactor", "enumerated_extension_states", "setup_counters",
            }
            if set(record) != expected_keys:
                raise VerifyError(f"{where} curve keys mismatch")
            slug = record.get("curve")
            if not isinstance(slug, str) or slug not in SPEC_BY_SLUG:
                raise VerifyError(f"{where} unknown curve")
            if slug in curves_seen:
                raise VerifyError(f"duplicate curve record {slug}")
            curves_seen.add(slug)
            context = expected.contexts[slug]
            if require_int_list(record["modulus"], f"{where}.modulus") != list(context.field.modulus):
                raise VerifyError(f"{where} extension coefficient mismatch")
            exact_curve_fields = {
                "extension_order": context.group_order,
                "torsion_count": context.spec.order ** 2,
                "kernel_count": context.spec.order,
                "cofactor": context.cofactor,
                "enumerated_extension_states": context.enumerated_states,
            }
            for key, expected_value in exact_curve_fields.items():
                if require_int(record[key], f"{where}.{key}", 0) != expected_value:
                    raise VerifyError(f"{where} {key} mismatch")
            point_fields = {
                "base_generator": context.base_generator,
                "transverse": context.transverse,
                "kernel_generator": context.kernel_generator,
            }
            for key, expected_point in point_fields.items():
                if parse_point(context.field, record[key], f"{where}.{key}") != expected_point:
                    raise VerifyError(f"{where} {key} mismatch")
            validate_counter_object(record["setup_counters"], f"{where}.setup_counters")
        elif record_type == "moment":
            expected_keys = {
                "type", "class", "curve", "multiplier", "scalar", "replicate",
                "moment", "channels", "label", "terms",
            }
            if set(record) != expected_keys:
                raise VerifyError(f"{where} moment keys mismatch")
            record_class = record.get("class")
            if record_class not in class_counts:
                raise VerifyError(f"{where} unknown moment class")
            slug = record.get("curve")
            if not isinstance(slug, str) or slug not in SPEC_BY_SLUG:
                raise VerifyError(f"{where} unknown curve")
            spec = SPEC_BY_SLUG[slug]
            multiplier = require_int(record["multiplier"], f"{where}.multiplier", 1)
            if multiplier not in (1, 2, 3):
                raise VerifyError(f"{where} bad multiplier")
            scalar = require_int(record["scalar"], f"{where}.scalar", 1)
            if scalar >= spec.order:
                raise VerifyError(f"{where} scalar outside canonical range")
            replicate_value = record["replicate"]
            if replicate_value is None:
                replicate = None
            else:
                replicate = require_int(replicate_value, f"{where}.replicate", 0)
            if record_class == "random-line":
                if replicate is None or replicate >= 8 or SPECS.index(spec) >= 2:
                    raise VerifyError(f"{where} invalid random-line scope")
            elif replicate is not None:
                raise VerifyError(f"{where} unexpected replicate")
            if record_class == "coordinate-isomorphism" and multiplier != 1:
                raise VerifyError(f"{where} coordinate record multiplier is not one")
            expected_moment, expected_terms = expected.moment(
                spec, multiplier, scalar, record_class, replicate
            )
            actual_moment = parse_moment(record["moment"], f"{where}.moment")
            if actual_moment != expected_moment:
                raise VerifyError(f"{where} moment mismatch")
            generator_moment, _ = expected.moment(
                spec, multiplier, 1, record_class, replicate
            )
            expected_channels = make_channels(expected_moment, generator_moment, spec.p)
            actual_channels = tuple(require_int_list(
                record["channels"], f"{where}.channels", CHANNEL_COUNT
            ))
            if actual_channels != expected_channels:
                raise VerifyError(f"{where} channel mismatch")
            if require_int(record["label"], f"{where}.label", 0) != scalar % 6:
                raise VerifyError(f"{where} scalar label mismatch")
            if require_int(record["terms"], f"{where}.terms", 0) != expected_terms:
                raise VerifyError(f"{where} moment term count mismatch")
            multiplication_cost, inversion_cost = channel_cost(expected_moment, generator_moment)
            channel_multiplications += multiplication_cost
            channel_inversions += inversion_cost
            moment_terms += expected_terms
            class_counts[record_class] += 1
            if record_class == "candidate":
                row = candidate.setdefault((slug, multiplier), {})
                if scalar in row:
                    raise VerifyError(f"{where} duplicate candidate scalar")
                row[scalar] = actual_channels
            elif record_class == "random-line":
                assert replicate is not None
                row = random_controls.setdefault((slug, multiplier, replicate), {})
                if scalar in row:
                    raise VerifyError(f"{where} duplicate random-control scalar")
                row[scalar] = actual_channels
            elif record_class == "coordinate-isomorphism":
                base_channels = candidate.get((slug, multiplier), {}).get(scalar)
                if base_channels is None or actual_channels[16:] != base_channels[16:]:
                    raise VerifyError(f"{where} normalized coordinate transport mismatch")
        elif record_type == "row_summary":
            row_summaries.append(record)
        elif record_type == "control_summary":
            control_summaries.append(record)
        elif record_type == "label_control":
            label_controls.append(record)
        else:
            raise VerifyError(f"{where} unknown record type {record_type!r}")

    if meta_seen != 1 or curves_seen != set(SPEC_BY_SLUG):
        raise VerifyError("metadata/curve record cardinality mismatch")
    if class_counts != {
        "candidate": 366,
        "random-line": 240,
        "rational-line": 366,
        "coordinate-isomorphism": 122,
    }:
        raise VerifyError(f"moment class counts mismatch: {class_counts}")
    if len(candidate) != 15 or len(random_controls) != 48:
        raise VerifyError("row/control table count mismatch")
    if len(row_summaries) != 15 or len(control_summaries) != 48 or len(label_controls) != 48:
        raise VerifyError("summary/control record count mismatch")

    row_score_tables: dict[tuple[str, int], list[int]] = {}
    global_scores = [0] * PREDICATE_COUNT
    global_exact = [True] * PREDICATE_COUNT
    for key, channel_table in candidate.items():
        spec = SPEC_BY_SLUG[key[0]]
        scores = row_scores(channel_table, spec, [scalar % 6 for scalar in range(1, spec.order)])
        row_score_tables[key] = scores
        for predicate_id, score in enumerate(scores):
            global_scores[predicate_id] += score
            global_exact[predicate_id] &= score == spec.order - 1

    seen_row_summaries: set[tuple[str, int]] = set()
    for record in row_summaries:
        expected_keys = {
            "type", "curve", "multiplier", "targets", "best_score", "best_ids",
            "exact", "counters",
        }
        if set(record) != expected_keys:
            raise VerifyError("row summary keys mismatch")
        slug = record.get("curve")
        if not isinstance(slug, str) or slug not in SPEC_BY_SLUG:
            raise VerifyError("row summary curve mismatch")
        multiplier = require_int(record["multiplier"], "row multiplier", 1)
        key = slug, multiplier
        if key in seen_row_summaries or key not in row_score_tables:
            raise VerifyError("duplicate or unknown row summary")
        seen_row_summaries.add(key)
        spec = SPEC_BY_SLUG[slug]
        scores = row_score_tables[key]
        best_score, best_ids = best(scores)
        expected_exact = [score == spec.order - 1 for score in scores]
        if require_int(record["targets"], "row targets", 0) != spec.order - 1:
            raise VerifyError("row target count mismatch")
        if require_int(record["best_score"], "row best", 0) != best_score:
            raise VerifyError("row best score mismatch")
        if require_int_list(record["best_ids"], "row best IDs") != best_ids:
            raise VerifyError("row best IDs mismatch")
        if require_bool_list(record["exact"], "row exact", PREDICATE_COUNT) != expected_exact:
            raise VerifyError("row exact bitmap mismatch")
        validate_counter_object(record["counters"], "row counters")

    seen_control_summaries: set[tuple[str, int, int]] = set()
    for record in control_summaries:
        expected_keys = {
            "type", "class", "curve", "multiplier", "replicate", "line_id",
            "best_score", "best_ids",
        }
        if set(record) != expected_keys or record.get("class") != "random-line":
            raise VerifyError("random control summary schema mismatch")
        slug = record.get("curve")
        if not isinstance(slug, str) or slug not in SPEC_BY_SLUG:
            raise VerifyError("random control curve mismatch")
        multiplier = require_int(record["multiplier"], "control multiplier", 1)
        replicate = require_int(record["replicate"], "control replicate", 0)
        key = slug, multiplier, replicate
        if key in seen_control_summaries or key not in random_controls:
            raise VerifyError("duplicate or unknown random control summary")
        seen_control_summaries.add(key)
        spec = SPEC_BY_SLUG[slug]
        line_id, _ = random_line(expected.contexts[slug], multiplier, replicate)
        if require_int(record["line_id"], "line ID", 0) != line_id:
            raise VerifyError("random control line ID mismatch")
        scores = row_scores(
            random_controls[key], spec, [scalar % 6 for scalar in range(1, spec.order)]
        )
        best_score, best_ids = best(scores)
        if require_int(record["best_score"], "control best", 0) != best_score:
            raise VerifyError("random control best score mismatch")
        if require_int_list(record["best_ids"], "control best IDs") != best_ids:
            raise VerifyError("random control best IDs mismatch")

    seen_label_controls: set[tuple[str, int, int]] = set()
    for record in label_controls:
        expected_keys = {
            "type", "curve", "multiplier", "replicate", "labels",
            "best_score", "best_ids",
        }
        if set(record) != expected_keys:
            raise VerifyError("label control schema mismatch")
        slug = record.get("curve")
        if not isinstance(slug, str) or slug not in SPEC_BY_SLUG:
            raise VerifyError("label control curve mismatch")
        multiplier = require_int(record["multiplier"], "label multiplier", 1)
        replicate = require_int(record["replicate"], "label replicate", 0)
        key = slug, multiplier, replicate
        if key in seen_label_controls or (slug, multiplier) not in candidate:
            raise VerifyError("duplicate or unknown label control")
        seen_label_controls.add(key)
        spec = SPEC_BY_SLUG[slug]
        expected_labels = shuffled_labels(spec, multiplier, replicate)
        if require_int_list(record["labels"], "shuffled labels") != expected_labels:
            raise VerifyError("shuffled label vector mismatch")
        scores = row_scores(candidate[(slug, multiplier)], spec, expected_labels)
        best_score, best_ids = best(scores)
        if require_int(record["best_score"], "label best", 0) != best_score:
            raise VerifyError("label control best score mismatch")
        if require_int_list(record["best_ids"], "label best IDs") != best_ids:
            raise VerifyError("label control best IDs mismatch")

    exact_ids = [index for index, exact in enumerate(global_exact) if exact]
    global_best, global_best_ids = best(global_scores)
    raw_best = max(global_scores[:16 * 12])
    normalized_best = max(global_scores[16 * 12:])
    decoder_queries = 0
    decoder_targets = 0
    forbidden_targets = 0
    for (slug, multiplier), channel_table in candidate.items():
        context = expected.contexts[slug]
        spec = context.spec
        generator = context.curve.scale(multiplier, context.base_generator)
        inverse_six = pow(6, -1, spec.order)
        channels_by_point = {
            context.curve.scale(scalar, generator): values
            for scalar, values in channel_table.items()
        }
        for predicate_id in exact_ids:
            for scalar in range(1, spec.order):
                target = context.curve.scale(scalar, generator)
                current = target
                reconstructed = 0
                place = 1
                queries = 0
                while current is not None:
                    if current not in channels_by_point:
                        raise VerifyError("decoder queried a noncohort point")
                    digit = predict(predicate_id, channels_by_point[current])
                    current = context.curve.scale(
                        inverse_six,
                        context.curve.sub(current, context.curve.scale(digit, generator)),
                    )
                    reconstructed += digit * place
                    place *= 6
                    queries += 1
                    if queries > 64:
                        raise VerifyError("candidate decoder failed to terminate")
                if reconstructed != scalar or context.curve.scale(reconstructed, generator) != target:
                    raise VerifyError("candidate decoder reconstruction mismatch")
                decoder_queries += queries
                decoder_targets += 1
        for scalar in range(1, spec.order):
            target = context.curve.scale(scalar, generator)
            current = target
            remaining = scalar
            reconstructed = 0
            place = 1
            while current is not None:
                digit = remaining % 6
                current = context.curve.scale(
                    inverse_six,
                    context.curve.sub(current, context.curve.scale(digit, generator)),
                )
                reconstructed += digit * place
                place *= 6
                remaining //= 6
                if current != context.curve.scale(remaining, generator):
                    raise VerifyError("forbidden-oracle group update mismatch")
            if reconstructed != scalar or remaining != 0:
                raise VerifyError("forbidden-oracle reconstruction mismatch")
            forbidden_targets += 1

    summary = evidence.summary
    expected_summary_keys = {
        "type", "raw_sha256", "records", "raw_bytes", "rows", "targets",
        "global_best_score", "global_best_ids", "exact_ids", "raw_only_best",
        "normalized_only_best", "random_control_records", "rational_control_records",
        "coordinate_records", "moment_terms", "channel_base_multiplications",
        "channel_base_inversions", "predicate_evaluations", "decoder_targets",
        "decoder_queries", "forbidden_positive", "forbidden_targets", "wall_ms",
    }
    if set(summary) != expected_summary_keys:
        raise VerifyError("summary keys mismatch")
    exact_summary = {
        "raw_sha256": evidence.raw_digest,
        "records": len(evidence.data_records),
        "raw_bytes": evidence.raw_bytes,
        "rows": 15,
        "targets": 366,
        "global_best_score": global_best,
        "global_best_ids": global_best_ids,
        "exact_ids": exact_ids,
        "raw_only_best": raw_best,
        "normalized_only_best": normalized_best,
        "random_control_records": class_counts["random-line"],
        "rational_control_records": class_counts["rational-line"],
        "coordinate_records": class_counts["coordinate-isomorphism"],
        "moment_terms": moment_terms,
        "channel_base_multiplications": channel_multiplications,
        "channel_base_inversions": channel_inversions,
        "predicate_evaluations": (366 + 240 + 240) * PREDICATE_COUNT,
        "decoder_targets": decoder_targets,
        "decoder_queries": decoder_queries,
        "forbidden_positive": True,
        "forbidden_targets": forbidden_targets,
    }
    for key, expected_value in exact_summary.items():
        if summary.get(key) != expected_value:
            raise VerifyError(f"summary {key} mismatch: {summary.get(key)!r} != {expected_value!r}")
    require_int(summary["wall_ms"], "summary wall_ms", 0)
    return {
        "raw_sha256": evidence.raw_digest,
        "records": len(evidence.data_records),
        "global_best_score": global_best,
        "global_best_ids": global_best_ids,
        "exact_ids": exact_ids,
        "decoder_targets": decoder_targets,
        "decoder_queries": decoder_queries,
        "moment_terms": moment_terms,
    }


def synthetic_packet() -> dict[str, Any]:
    core = {
        "extension": [1, 0, 1],
        "frobenius_image": 7,
        "fiber_member": [4, 9],
        "moment": [13, 17],
        "scalar": 11,
        "label": 5,
        "predicate_id": 23,
    }
    raw = canonical_json(core) + b"\n"
    return {
        "core": core,
        "raw_digest": hashlib.sha256(raw).hexdigest(),
        "summary_count": 1,
    }


def validate_synthetic(packet: dict[str, Any]) -> None:
    expected = synthetic_packet()
    obj = require_dict(packet, "synthetic packet")
    if set(obj) != {"core", "raw_digest", "summary_count"}:
        raise VerifyError("synthetic packet keys mismatch")
    core = require_dict(obj["core"], "synthetic core")
    expected_core = expected["core"]
    checks = (
        ("extension", "extension coefficient"),
        ("frobenius_image", "Frobenius image"),
        ("fiber_member", "fiber member"),
        ("moment", "moment"),
        ("label", "scalar label"),
        ("predicate_id", "predicate ID"),
    )
    for key, description in checks:
        if core.get(key) != expected_core[key]:
            raise VerifyError(f"synthetic {description} mismatch")
    if core.get("scalar") != expected_core["scalar"] or core.get("label") != core.get("scalar") % 6:
        raise VerifyError("synthetic scalar/label relation mismatch")
    predicate_parts(require_int(core.get("predicate_id"), "synthetic predicate ID", 0))
    raw = canonical_json(core) + b"\n"
    if obj.get("raw_digest") != hashlib.sha256(raw).hexdigest():
        raise VerifyError("synthetic raw digest mismatch")
    if obj.get("summary_count") != 1:
        raise VerifyError("synthetic summary count mismatch")


def selftest() -> dict[str, Any]:
    modulus = first_irreducible(3, 2)
    if modulus != (1, 0, 1):
        raise VerifyError(f"unexpected synthetic modulus {modulus}")
    field = Fq(3, 2, modulus)
    for index in range(field.q):
        value = field.elt(index)
        if field.index(value) != index or field.frobenius_power(value, 2) != value:
            raise VerifyError("synthetic field round-trip/Frobenius failure")
        if value != field.zero and field.mul(value, field.inverse(value)) != field.one:
            raise VerifyError("synthetic field inverse failure")
    names = {
        f"ch{predicate_parts(predicate_id)[0]:02}-p2{predicate_parts(predicate_id)[1]}-p3{predicate_parts(predicate_id)[2]}"
        for predicate_id in range(PREDICATE_COUNT)
    }
    if len(names) != PREDICATE_COUNT:
        raise VerifyError("predicate ID round-trip collision")
    base = synthetic_packet()
    validate_synthetic(base)
    mutations = {
        "extension-coefficient": ("core", "extension"),
        "frobenius-image": ("core", "frobenius_image"),
        "fiber-member": ("core", "fiber_member"),
        "moment": ("core", "moment"),
        "scalar-label": ("core", "label"),
        "predicate-id": ("core", "predicate_id"),
        "raw-digest": ("raw_digest",),
        "summary-count": ("summary_count",),
    }
    rejected: list[str] = []
    for name, path in mutations.items():
        mutated = copy.deepcopy(base)
        if path == ("core", "extension"):
            mutated["core"]["extension"][0] ^= 1
        elif path == ("core", "frobenius_image"):
            mutated["core"]["frobenius_image"] += 1
        elif path == ("core", "fiber_member"):
            mutated["core"]["fiber_member"][0] += 1
        elif path == ("core", "moment"):
            mutated["core"]["moment"][1] += 1
        elif path == ("core", "label"):
            mutated["core"]["label"] = (mutated["core"]["label"] + 1) % 6
        elif path == ("core", "predicate_id"):
            mutated["core"]["predicate_id"] = PREDICATE_COUNT
        elif path == ("raw_digest",):
            mutated["raw_digest"] = "00" * 32
        elif path == ("summary_count",):
            mutated["summary_count"] += 1
        else:
            raise VerifyError(f"unknown selftest mutation {name}")
        try:
            validate_synthetic(mutated)
        except VerifyError:
            rejected.append(name)
        else:
            raise VerifyError(f"tamper class was accepted: {name}")
    return {
        "synthetic_field": "F_3^2",
        "modulus": list(modulus),
        "predicate_ids": len(names),
        "tamper_rejections": rejected,
    }


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--selftest", action="store_true")
    group.add_argument("--verify", type=Path, metavar="H115_JSONL")
    arguments = parser.parse_args(argv)
    try:
        result = selftest() if arguments.selftest else verify_evidence(arguments.verify)
    except (OSError, VerifyError, ValueError) as error:
        print(f"H115 verification failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
