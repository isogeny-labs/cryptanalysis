#!/usr/bin/env python3
"""Independent verifier for H116 truncated Frobenius-fiber evidence."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


J = 8
PROTOCOL_SHA256 = "42b510bd0f67d23ad49e5827d947510de5e1c68bf82d29c78fa35e4861fe4bf3"
COHORT_SHA256 = "29e2fd5596ce3ed8e93933161e05b92229cd3065a892bc8ee59d6265f6fa2d99"
TARGETS_SHA256 = "585a07cddf4bc0b9f44523f2982e6a140fddc6f79c70f48d17d8944a1a935b56"
LABELS_SHA256 = "368aec98f2c3143f16a838572dbf3aacbe1e3c56b119370685efd1082850554b"
TARGET_HEADER = f"h116-targets/v1\t{PROTOCOL_SHA256}\t{COHORT_SHA256}"
LABEL_HEADER = f"h116-target-labels/v1\t{PROTOCOL_SHA256}\t{COHORT_SHA256}"
TARGET_SEEDS = (116001, 116002, 116003, 116004, 116005)


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


SPECS = (
    Spec("h116-fp107-a1-b25-r127-d3", 107, 1, 25, 127, -19, 3),
    Spec("h116-fp211-a1-b148-r197-d4", 211, 1, 148, 197, 15, 4),
    Spec("h116-fp241-a1-b57-r257-d4", 241, 1, 57, 257, -15, 4),
    Spec("h116-fp431-a1-b111-r397-d3", 431, 1, 111, 397, 35, 3),
    Spec("h116-fp587-a1-b204-r547-d3", 587, 1, 204, 547, 41, 3),
)
SPEC_BY_SLUG = {spec.slug: spec for spec in SPECS}

Elt = tuple[int, ...]
Point = Optional[tuple[Elt, Elt]]
Moment = tuple[tuple[int, ...], tuple[int, ...]]


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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
    for i, left_value in enumerate(left):
        for j, right_value in enumerate(right):
            product[i + j] = (product[i + j] + left_value * right_value) % p
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
        if poly_gcd(modulus, poly_sub(powers[degree // divisor], x_poly, p), p) != [1]:
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
    """Tuple-valued finite field independent of the Rust representation."""

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
        return tuple((a + b) % self.p for a, b in zip(left, right))

    def neg(self, value: Elt) -> Elt:
        return tuple((-coefficient) % self.p for coefficient in value)

    def sub(self, left: Elt, right: Elt) -> Elt:
        return self.add(left, self.neg(right))

    def mul(self, left: Elt, right: Elt) -> Elt:
        product = [0] * (2 * self.degree - 1)
        for i, left_value in enumerate(left):
            for j, right_value in enumerate(right):
                product[i + j] = (product[i + j] + left_value * right_value) % self.p
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
            nonresidue = next((
                self.elt(index) for index in range(2, self.q)
                if self.power(self.elt(index), (self.q - 1) // 2) == self.neg(self.one)
            ), None)
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
        if any(value[1:]):
            raise VerifyError(f"value is not in the base field: {self.index(value)}")
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
        result = (x_result, y_result)
        if not self.on_curve(result):
            raise VerifyError("point addition left the curve")
        return result

    def sub(self, left: Point, right: Point) -> Point:
        return self.add(left, self.neg(right))

    def scale(self, scalar: int, point: Point) -> Point:
        result = None
        while scalar:
            if scalar & 1:
                result = self.add(result, point)
            scalar >>= 1
            if scalar:
                point = self.add(point, point)
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
    before, previous = 2, spec.trace
    if spec.degree == 0:
        power_sum = before
    elif spec.degree == 1:
        power_sum = previous
    else:
        for _ in range(2, spec.degree + 1):
            before, previous = previous, spec.trace * previous - spec.p * before
        power_sum = previous
    return spec.p ** spec.degree + 1 - power_sum


def first_base_point(curve: EC, p: int) -> Point:
    for x_value in range(p):
        for y_value in range(p):
            point = (curve.field.base(x_value), curve.field.base(y_value))
            if curve.on_curve(point):
                return point
    raise VerifyError("base point not found")


@dataclass(frozen=True)
class Context:
    spec: Spec
    modulus: tuple[int, ...]
    field: Fq
    curve: EC
    base_generator: Point
    kernel_generator: Point
    group_order: int
    cofactor: int
    states_examined: int


def build_context(spec: Spec) -> Context:
    modulus = first_irreducible(spec.p, spec.degree)
    field = Fq(spec.p, spec.degree, modulus)
    curve = EC(field, spec.a, spec.b)
    group_order = extension_group_order(spec)
    if group_order % (spec.order ** 2):
        raise VerifyError("r^2 does not divide extension group order")
    cofactor = group_order // (spec.order ** 2)
    if cofactor % spec.order == 0:
        raise VerifyError("r divides torsion cofactor")
    base_generator = first_base_point(curve, spec.p)
    if curve.scale(spec.order, base_generator) is not None:
        raise VerifyError("base generator has wrong order")
    for x_index in range(field.q):
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
        kernel = curve.sub(curve.frobenius(projected), projected)
        if kernel is None or curve.scale(spec.order, kernel) is not None:
            continue
        inverse_frobenius = curve.frobenius_power(kernel, spec.degree - 1)
        verschiebung = curve.scale(spec.p, inverse_frobenius)
        if curve.sub(verschiebung, kernel) is not None:
            continue
        return Context(
            spec, modulus, field, curve, base_generator, kernel,
            group_order, cofactor, x_index + 1,
        )
    raise VerifyError("kernel generator not found")


class SplitMix64:
    def __init__(self, seed: int):
        self.state = seed & ((1 << 64) - 1)

    def next(self) -> int:
        mask = (1 << 64) - 1
        self.state = (self.state + 0x9E3779B97F4A7C15) & mask
        value = self.state
        value = ((value ^ (value >> 30)) * 0xBF58476D1CE4E5B9) & mask
        value = ((value ^ (value >> 27)) * 0x94D049BB133111EB) & mask
        return (value ^ (value >> 31)) & mask


def shuffled_scalars(order: int, seed: int) -> list[int]:
    values = list(range(1, order))
    generator = SplitMix64(seed)
    for index in range(len(values) - 1, 0, -1):
        swap = generator.next() % (index + 1)
        values[index], values[swap] = values[swap], values[index]
    return values


def target_digest(spec: Spec, generator_label: int, x_value: int, y_value: int) -> str:
    domain = (
        f"H116-TARGET\0{PROTOCOL_SHA256}\0{COHORT_SHA256}\0{spec.slug}"
        f"\0{generator_label}\0{x_value}\0{y_value}"
    )
    return sha256_hex(domain.encode())


def base_coordinates(field: Fq, point: Point) -> tuple[int, int]:
    if point is None:
        raise VerifyError("unexpected identity point")
    return field.to_base(point[0]), field.to_base(point[1])


def exact_lines(path: Path, expected_sha256: str, header: str) -> list[str]:
    data = path.read_bytes()
    if sha256_hex(data) != expected_sha256:
        raise VerifyError(f"{path.name} SHA-256 mismatch")
    if not data.endswith(b"\n"):
        raise VerifyError(f"{path.name} lacks final newline")
    try:
        lines = data.decode("utf-8").splitlines()
    except UnicodeDecodeError as error:
        raise VerifyError(f"{path.name} is not UTF-8") from error
    if not lines or lines[0] != header:
        raise VerifyError(f"{path.name} header mismatch")
    return lines[1:]


def expected_target_rows() -> tuple[list[str], list[str]]:
    target_rows: list[str] = []
    label_rows: list[str] = []
    for curve_index, spec in enumerate(SPECS):
        field = Fq(spec.p, 1, (0, 1))
        curve = EC(field, spec.a, spec.b)
        base_generator = first_base_point(curve, spec.p)
        if curve.scale(spec.order, base_generator) is not None:
            raise VerifyError(f"{spec.slug} base generator has wrong order")
        order = shuffled_scalars(spec.order, TARGET_SEEDS[curve_index])
        for generator_label in range(1, 4):
            generator = curve.scale(generator_label, base_generator)
            for scalar in order:
                point = curve.scale(scalar, generator)
                x_value, y_value = base_coordinates(field, point)
                digest = target_digest(spec, generator_label, x_value, y_value)
                target_rows.append(
                    f"{spec.slug}\t{generator_label}\t{digest}\t{x_value}\t{y_value}"
                )
                label_rows.append(f"{spec.slug}\t{generator_label}\t{digest}\t{scalar}")
    return target_rows, label_rows


def require_exact_rows(actual: list[str], expected: list[str], name: str) -> None:
    if len(actual) != len(expected):
        raise VerifyError(f"{name} row count {len(actual)} != {len(expected)}")
    for index, (actual_row, expected_row) in enumerate(zip(actual, expected), start=2):
        if actual_row != expected_row:
            raise VerifyError(
                f"{name} mismatch at line {index}: {actual_row!r} != {expected_row!r}"
            )


def verify_targets(target_path: Path, label_path: Path) -> dict[str, Any]:
    actual_targets = exact_lines(target_path, TARGETS_SHA256, TARGET_HEADER)
    actual_labels = exact_lines(label_path, LABELS_SHA256, LABEL_HEADER)
    expected_targets, expected_labels = expected_target_rows()
    require_exact_rows(actual_targets, expected_targets, "target manifest")
    require_exact_rows(actual_labels, expected_labels, "label map")
    target_digests = {row.split("\t")[2] for row in actual_targets}
    label_digests = {row.split("\t")[2] for row in actual_labels}
    if len(target_digests) != len(actual_targets) or target_digests != label_digests:
        raise VerifyError("digest join is not one-to-one")
    return {
        "status": "pass",
        "curves": len(SPECS),
        "target_rows": len(actual_targets),
        "label_rows": len(actual_labels),
        "target_sha256": TARGETS_SHA256,
        "label_sha256": LABELS_SHA256,
    }


def load_blinded_groups(target_path: Path) -> dict[tuple[str, int], list[tuple[str, int, int]]]:
    rows = exact_lines(target_path, TARGETS_SHA256, TARGET_HEADER)
    groups: dict[tuple[str, int], list[tuple[str, int, int]]] = {}
    seen: set[str] = set()
    for line_number, row in enumerate(rows, start=2):
        columns = row.split("\t")
        if len(columns) != 5:
            raise VerifyError(f"target manifest line {line_number} has wrong column count")
        slug, label_text, digest, x_text, y_text = columns
        spec = SPEC_BY_SLUG.get(slug)
        if spec is None:
            raise VerifyError(f"unknown curve at target line {line_number}")
        try:
            label, x_value, y_value = int(label_text), int(x_text), int(y_text)
        except ValueError as error:
            raise VerifyError(f"noninteger target field at line {line_number}") from error
        if label not in (1, 2, 3) or not (0 <= x_value < spec.p and 0 <= y_value < spec.p):
            raise VerifyError(f"noncanonical target at line {line_number}")
        if digest != target_digest(spec, label, x_value, y_value):
            raise VerifyError(f"target digest mismatch at line {line_number}")
        if digest in seen:
            raise VerifyError(f"duplicate target digest at line {line_number}")
        seen.add(digest)
        groups.setdefault((slug, label), []).append((digest, x_value, y_value))
    for spec in SPECS:
        for label in range(1, 4):
            if len(groups.get((spec.slug, label), [])) != spec.order - 1:
                raise VerifyError(f"incomplete target group {spec.slug}/{label}")
    return groups


def coordinate_map(field: Fq, point: Point, lambda_value: int) -> Point:
    if point is None:
        return None
    scale = field.base(lambda_value)
    square = field.mul(scale, scale)
    cube = field.mul(square, scale)
    return field.mul(square, point[0]), field.mul(cube, point[1])


def section(context: Context, target: Point) -> Point:
    scalar = pow((context.spec.p - 1) % context.spec.order, -1, context.spec.order)
    return context.curve.scale(scalar, target)


def absolute_direct_moments(context: Context, shift: Point) -> Moment:
    field, curve, spec = context.field, context.curve, context.spec
    x_sums = [field.zero] * J
    y_sums = [field.zero] * J
    current = shift
    for _ in range(spec.order):
        if current is None:
            raise VerifyError("identity in affine fiber")
        x_value, y_value = current
        x_power = field.one
        for index in range(J):
            y_sums[index] = field.add(y_sums[index], field.mul(y_value, x_power))
            x_power = field.mul(x_power, x_value)
            x_sums[index] = field.add(x_sums[index], x_power)
        current = curve.add(current, context.kernel_generator)
    if current != shift:
        raise VerifyError("direct fiber did not close")
    return (
        tuple(field.to_base(value) for value in x_sums),
        tuple(field.to_base(value) for value in y_sums),
    )


def scale_moments(moment: Moment, lambda_value: int, p: int) -> Moment:
    return (
        tuple(value * pow(lambda_value, 2 * (index + 1), p) % p
              for index, value in enumerate(moment[0])),
        tuple(value * pow(lambda_value, 3 + 2 * index, p) % p
              for index, value in enumerate(moment[1])),
    )


def relative_direct(target: Moment, reference: Moment, p: int) -> Moment:
    return (
        tuple((target[0][index] - reference[0][index]) % p for index in range(J)),
        target[1],
    )


@dataclass
class BaseOps:
    add: int = 0
    mul: int = 0
    inv: int = 0

    def as_dict(self) -> dict[str, int]:
        return {"add": self.add, "mul": self.mul, "inv": self.inv}


class CountedFp:
    def __init__(self, p: int):
        self.p = p
        self.ops = BaseOps()

    def add(self, left: int, right: int) -> int:
        self.ops.add += 1
        return (left + right) % self.p

    def neg(self, value: int) -> int:
        return (-value) % self.p

    def sub(self, left: int, right: int) -> int:
        return self.add(left, self.neg(right))

    def mul(self, left: int, right: int) -> int:
        self.ops.mul += 1
        return left * right % self.p

    def inverse(self, value: int) -> int:
        self.ops.inv += 1
        if value % self.p == 0:
            raise VerifyError("base-field inversion of zero")
        return pow(value, self.p - 2, self.p)

    def divide(self, numerator: int, denominator: int) -> int:
        return self.mul(numerator, self.inverse(denominator))


@dataclass(frozen=True)
class Jet:
    p: int
    h: tuple[int, ...]
    differential_squared: int
    differential_cubed: int
    setup_ops: dict[str, int]


def build_jet(p: int, curve_a: int, curve_b: int, trace: int) -> Jet:
    if p <= 2 * J + 3:
        raise VerifyError(f"characteristic {p} outside p>19")
    field = CountedFp(p)
    differential = (trace - 1) % p
    if differential == 0:
        raise VerifyError("zero differential")
    d2 = field.mul(differential, differential)
    d3 = field.mul(d2, differential)
    d4 = field.mul(d2, d2)
    d6 = field.mul(d3, d3)
    target_a = field.mul(d4, curve_a)
    target_b = field.mul(d6, curve_b)
    h = [0] * J
    h[1] = field.divide(field.sub(curve_a, target_a), 5)
    h[2] = field.divide(field.sub(curve_b, target_b), 7)
    for k in range(3, J):
        convolution = 0
        for index in range(1, k - 1):
            convolution = field.add(convolution, field.mul(h[index], h[k - 1 - index]))
        denominator = (k - 2) * (2 * k + 3)
        first = field.divide(field.mul(3, convolution), denominator % p)
        second_inner = field.mul(curve_a, h[k - 2])
        second = field.divide(field.mul(2 * k - 3, second_inner), (2 * k + 3) % p)
        third_inner = field.mul(curve_b, h[k - 3])
        third = field.divide(field.mul(2 * (k - 3), third_inner), (2 * k + 3) % p)
        h[k] = field.sub(field.sub(first, second), third)
    return Jet(p, tuple(h), d2, d3, field.ops.as_dict())


def inverse_and_log(polynomial: list[int], field: CountedFp) -> tuple[list[int], list[int]]:
    inverse = [0] * J
    inverse[0] = 1
    for degree in range(1, J):
        total = 0
        for index in range(1, degree + 1):
            total = field.add(total, field.mul(polynomial[index], inverse[degree - index]))
        inverse[degree] = field.neg(total)
    log_derivative = [0] * J
    for degree in range(J):
        total = 0
        for index in range(1, degree + 2):
            derivative = field.mul(index, polynomial[index])
            total = field.add(total, field.mul(derivative, inverse[degree + 1 - index]))
        log_derivative[degree] = total
    return inverse, log_derivative


def jet_online(jet: Jet, target_x: int, target_y: int, reference_x: int) -> tuple[Moment, dict[str, int]]:
    field = CountedFp(jet.p)
    normalized_target = field.mul(jet.differential_squared, target_x)
    normalized_reference = field.mul(jet.differential_squared, reference_x)

    def polynomial(normalized_x: int) -> list[int]:
        result = [0] * (J + 1)
        result[0] = 1
        result[1] = field.neg(normalized_x)
        result[2:] = jet.h[1:]
        return result

    inverse, target_log = inverse_and_log(polynomial(normalized_target), field)
    _, reference_log = inverse_and_log(polynomial(normalized_reference), field)
    y_scale = field.mul(jet.differential_cubed, target_y)
    x_values = []
    y_values = []
    for index in range(J):
        x_values.append(field.sub(reference_log[index], target_log[index]))
        y_values.append(field.mul(y_scale, inverse[index]))
    return (tuple(x_values), tuple(y_values)), field.ops.as_dict()


def candidate_for(spec: Spec, target: tuple[int, int], reference: tuple[int, int], lambda_value: int) -> tuple[Moment, dict[str, int], dict[str, int]]:
    p = spec.p
    square = lambda_value * lambda_value % p
    cube = square * lambda_value % p
    fourth = square * square % p
    sixth = cube * cube % p
    model_a = spec.a * fourth % p
    model_b = spec.b * sixth % p
    target_x = target[0] * square % p
    target_y = target[1] * cube % p
    reference_x = reference[0] * square % p
    jet = build_jet(p, model_a, model_b, spec.trace)
    moment, online_ops = jet_online(jet, target_x, target_y, reference_x)
    return moment, jet.setup_ops, online_ops


def planted_controls() -> list[Moment]:
    p = 1009
    controls: list[Moment] = []
    for case_id in range(32):
        degree = 9 + case_id % 8
        roots = [1 + ((case_id * 29 + index * 37) % (p - 1)) for index in range(degree)]
        if len(set(roots)) != degree:
            raise VerifyError("repeated planted root")
        field = CountedFp(p)
        polynomial = [0] * (J + 1)
        polynomial[0] = 1
        for root in roots:
            for index in range(J, 0, -1):
                polynomial[index] = field.sub(polynomial[index], field.mul(root, polynomial[index - 1]))
        inverse, log_derivative = inverse_and_log(polynomial, field)
        candidate: Moment = (
            tuple((-value) % p for value in log_derivative),
            tuple(inverse),
        )
        direct_x = tuple(sum(pow(root, index + 1, p) for root in roots) % p for index in range(J))
        direct_y = [0] * J
        for root_index, root in enumerate(roots):
            denominator = 1
            for other_index, other in enumerate(roots):
                if other_index != root_index:
                    denominator = denominator * (root - other) % p
            weight = pow(denominator, p - 2, p)
            for index in range(J):
                direct_y[index] = (direct_y[index] + weight * pow(root, degree - 1 + index, p)) % p
        direct: Moment = direct_x, tuple(direct_y)
        if candidate != direct:
            raise VerifyError(f"planted control {case_id} failed")
        tampered = [list(candidate[0]), list(candidate[1])]
        side, index = divmod(case_id % 16, J)
        tampered[side][index] = (tampered[side][index] + 1) % p
        if (tuple(tampered[0]), tuple(tampered[1])) == direct:
            raise VerifyError(f"planted tamper {case_id} survived")
        controls.append(candidate)
    return controls


def require_object(value: Any, context: str, keys: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise VerifyError(f"{context} is not an object")
    if set(value) != keys:
        raise VerifyError(f"{context} keys {sorted(value)} != {sorted(keys)}")
    return value


def require_int(value: Any, context: str, minimum: Optional[int] = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise VerifyError(f"{context} is not an integer")
    if minimum is not None and value < minimum:
        raise VerifyError(f"{context} is below {minimum}")
    return value


def require_bool(value: Any, context: str) -> bool:
    if not isinstance(value, bool):
        raise VerifyError(f"{context} is not a boolean")
    return value


def parse_moment(value: Any, context: str) -> Moment:
    obj = require_object(value, context, {"x", "y"})
    result = []
    for coordinate in ("x", "y"):
        values = obj[coordinate]
        if not isinstance(values, list) or len(values) != J:
            raise VerifyError(f"{context}.{coordinate} has wrong length")
        result.append(tuple(require_int(item, f"{context}.{coordinate}[{index}]", 0)
                            for index, item in enumerate(values)))
    return result[0], result[1]


def moment_object(moment: Moment) -> dict[str, list[int]]:
    return {"x": list(moment[0]), "y": list(moment[1])}


EXTENSION_OP_KEYS = {
    "base_additions", "base_multiplications", "base_inversions",
    "extension_additions", "extension_multiplications", "extension_inversions",
    "frobenius_maps", "point_additions", "scalar_multiplications",
}


def parse_ops(value: Any, context: str, keys: set[str]) -> dict[str, int]:
    obj = require_object(value, context, keys)
    return {key: require_int(obj[key], f"{context}.{key}", 0) for key in sorted(keys)}


def load_jsonl(path: Path) -> tuple[list[dict[str, Any]], str]:
    data = path.read_bytes()
    if not data.endswith(b"\n"):
        raise VerifyError("packet lacks final newline")
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(data.splitlines(), start=1):
        try:
            record = json.loads(line)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise VerifyError(f"invalid JSON at packet line {line_number}") from error
        if not isinstance(record, dict):
            raise VerifyError(f"packet line {line_number} is not an object")
        records.append(record)
    return records, sha256_hex(data)


def verify_packet(target_path: Path, packet_path: Path) -> dict[str, Any]:
    target_groups = load_blinded_groups(target_path)
    records, packet_sha256 = load_jsonl(packet_path)
    cursor = 0

    def take(kind: str) -> dict[str, Any]:
        nonlocal cursor
        if cursor >= len(records):
            raise VerifyError(f"packet ended before {kind}")
        record = records[cursor]
        cursor += 1
        if record.get("type") != kind:
            raise VerifyError(f"packet record {cursor} is {record.get('type')!r}, expected {kind!r}")
        return record

    header = require_object(take("header"), "header", {
        "type", "schema", "protocol_sha256", "cohort_sha256",
        "target_manifest_sha256", "labels_available_to_process",
    })
    if header != {
        "type": "header",
        "schema": "h116.component/v2",
        "protocol_sha256": PROTOCOL_SHA256,
        "cohort_sha256": COHORT_SHA256,
        "target_manifest_sha256": TARGETS_SHA256,
        "labels_available_to_process": False,
    }:
        raise VerifyError("packet header binding mismatch")

    planted = planted_controls()
    for case_id, expected in enumerate(planted):
        control = require_object(take("positive_control"), f"positive control {case_id}", {
            "type", "case_id", "candidate", "direct", "match", "tamper_rejected",
        })
        if require_int(control["case_id"], "positive case id", 0) != case_id:
            raise VerifyError("positive control order mismatch")
        candidate = parse_moment(control["candidate"], f"positive {case_id}.candidate")
        direct = parse_moment(control["direct"], f"positive {case_id}.direct")
        if candidate != expected or direct != expected:
            raise VerifyError(f"positive control {case_id} moment mismatch")
        if not require_bool(control["match"], f"positive {case_id}.match"):
            raise VerifyError(f"positive control {case_id} reports mismatch")
        if not require_bool(control["tamper_rejected"], f"positive {case_id}.tamper"):
            raise VerifyError(f"positive control {case_id} accepted tamper")

    for prime in (5, 7, 13):
        control = require_object(take("negative_control"), f"negative control {prime}", {
            "type", "prime", "rejected",
        })
        if require_int(control["prime"], "negative prime", 0) != prime:
            raise VerifyError("negative control order mismatch")
        if not require_bool(control["rejected"], f"negative {prime}.rejected"):
            raise VerifyError(f"negative control p={prime} was not rejected")
        try:
            build_jet(prime, 2 % prime, 4 % prime, -3)
        except VerifyError:
            pass
        else:
            raise VerifyError(f"independent boundary p={prime} did not reject")

    rows = 0
    mismatches = 0
    stopped = False
    context_summaries = []
    for spec in SPECS:
        context = build_context(spec)
        setup = require_object(take("setup"), f"setup {spec.slug}", {
            "type", "curve", "modulus", "group_order", "cofactor", "states_examined",
        })
        expected_setup = {
            "type": "setup",
            "curve": spec.slug,
            "modulus": list(context.modulus),
            "group_order": context.group_order,
            "cofactor": context.cofactor,
            "states_examined": context.states_examined,
        }
        if setup != expected_setup:
            raise VerifyError(f"setup mismatch for {spec.slug}")
        context_summaries.append({
            "curve": spec.slug,
            "modulus": list(context.modulus),
            "states_examined": context.states_examined,
        })
        absolute_cache: dict[tuple[int, int], Moment] = {}

        def absolute(point: Point) -> Moment:
            coordinates = base_coordinates(context.field, point)
            if coordinates not in absolute_cache:
                absolute_cache[coordinates] = absolute_direct_moments(context, section(context, point))
            return absolute_cache[coordinates]

        for generator_label in range(1, 4):
            reference_point = context.curve.scale(generator_label, context.base_generator)
            reference_coordinates = base_coordinates(context.field, reference_point)
            reference_native = absolute(reference_point)
            blinded_targets = target_groups[(spec.slug, generator_label)]
            for lambda_value in (1, 2):
                reference_scaled = scale_moments(reference_native, lambda_value, spec.p)
                for digest, target_x, target_y in blinded_targets:
                    target_point = (context.field.base(target_x), context.field.base(target_y))
                    if not context.curve.on_curve(target_point):
                        raise VerifyError(f"off-curve blinded target {digest}")
                    if context.curve.scale(spec.order, target_point) is not None:
                        raise VerifyError(f"wrong-order blinded target {digest}")
                    target_native = absolute(target_point)
                    target_scaled = scale_moments(target_native, lambda_value, spec.p)
                    independent_direct = relative_direct(target_scaled, reference_scaled, spec.p)
                    independent_candidate, setup_ops, online_ops = candidate_for(
                        spec, (target_x, target_y), reference_coordinates, lambda_value
                    )
                    expected_match = independent_candidate == independent_direct
                    row = require_object(take("row"), f"row {rows}", {
                        "type", "curve", "generator_label", "target_digest", "lambda",
                        "candidate", "direct", "direct_aa", "match", "jet_setup_ops",
                        "candidate_online_ops", "direct_ops", "direct_aa_ops",
                        "candidate_dev_ns", "direct_dev_ns",
                    })
                    if row["curve"] != spec.slug:
                        raise VerifyError(f"row {rows} curve mismatch")
                    if require_int(row["generator_label"], f"row {rows}.label", 1) != generator_label:
                        raise VerifyError(f"row {rows} generator label mismatch")
                    if row["target_digest"] != digest:
                        raise VerifyError(f"row {rows} target digest mismatch")
                    if require_int(row["lambda"], f"row {rows}.lambda", 1) != lambda_value:
                        raise VerifyError(f"row {rows} lambda mismatch")
                    candidate = parse_moment(row["candidate"], f"row {rows}.candidate")
                    direct = parse_moment(row["direct"], f"row {rows}.direct")
                    direct_aa = parse_moment(row["direct_aa"], f"row {rows}.direct_aa")
                    if candidate != independent_candidate:
                        raise VerifyError(f"row {rows} candidate moment mismatch")
                    if direct != independent_direct:
                        raise VerifyError(f"row {rows} direct moment mismatch")
                    if direct_aa != independent_direct:
                        raise VerifyError(f"row {rows} A/A moment mismatch")
                    if require_bool(row["match"], f"row {rows}.match") != expected_match:
                        raise VerifyError(f"row {rows} match boolean mismatch")
                    if parse_ops(row["jet_setup_ops"], f"row {rows}.setup_ops", {"add", "mul", "inv"}) != setup_ops:
                        raise VerifyError(f"row {rows} setup operation mismatch")
                    if parse_ops(row["candidate_online_ops"], f"row {rows}.online_ops", {"add", "mul", "inv"}) != online_ops:
                        raise VerifyError(f"row {rows} online operation mismatch")
                    direct_ops = parse_ops(row["direct_ops"], f"row {rows}.direct_ops", EXTENSION_OP_KEYS)
                    aa_ops = parse_ops(row["direct_aa_ops"], f"row {rows}.direct_aa_ops", EXTENSION_OP_KEYS)
                    if direct_ops != aa_ops:
                        raise VerifyError(f"row {rows} direct operation A/A mismatch")
                    require_int(row["candidate_dev_ns"], f"row {rows}.candidate_dev_ns", 0)
                    require_int(row["direct_dev_ns"], f"row {rows}.direct_dev_ns", 0)
                    rows += 1
                    if not expected_match:
                        mismatches += 1
                        stopped = True
                        break
                if stopped:
                    break
            if stopped:
                break
        if stopped:
            break

    summary = require_object(take("summary"), "summary", {
        "type", "rows", "mismatches", "status",
    })
    expected_status = "exact" if mismatches == 0 else "first_mismatch"
    if summary != {
        "type": "summary", "rows": rows, "mismatches": mismatches, "status": expected_status,
    }:
        raise VerifyError("packet summary mismatch")
    if cursor != len(records):
        raise VerifyError("records follow packet summary")
    if mismatches == 0 and rows != 9120:
        raise VerifyError(f"exact packet has {rows} rows, expected 9120")
    return {
        "status": expected_status,
        "rows": rows,
        "mismatches": mismatches,
        "positive_controls": len(planted),
        "negative_controls": 3,
        "packet_sha256": packet_sha256,
        "contexts": context_summaries,
        "development_timings_admitted": False,
    }


def validate_synthetic_packet(packet: dict[str, Any]) -> None:
    require_object(packet, "synthetic packet", {
        "header", "positive", "negative", "rows", "summary",
    })
    if packet["header"] != {"schema": "synthetic/v1", "binding": "f" * 64}:
        raise VerifyError("synthetic header mismatch")
    zero: Moment = (tuple([0] * J), tuple([0] * J))
    positive = require_object(packet["positive"], "synthetic positive", {
        "candidate", "direct", "tamper_rejected",
    })
    if parse_moment(positive["candidate"], "synthetic positive candidate") != zero:
        raise VerifyError("synthetic positive candidate mismatch")
    if parse_moment(positive["direct"], "synthetic positive direct") != zero:
        raise VerifyError("synthetic positive direct mismatch")
    if not require_bool(positive["tamper_rejected"], "synthetic positive tamper"):
        raise VerifyError("synthetic positive tamper survived")
    if packet["negative"] != {"prime": 13, "rejected": True}:
        raise VerifyError("synthetic negative mismatch")
    rows = packet["rows"]
    if not isinstance(rows, list) or len(rows) != 1:
        raise VerifyError("synthetic row count mismatch")
    row = require_object(rows[0], "synthetic row", {
        "digest", "candidate", "direct", "direct_aa", "match",
    })
    if row["digest"] != "a" * 64:
        raise VerifyError("synthetic row digest mismatch")
    for name in ("candidate", "direct", "direct_aa"):
        if parse_moment(row[name], f"synthetic row {name}") != zero:
            raise VerifyError(f"synthetic row {name} mismatch")
    if not require_bool(row["match"], "synthetic row match"):
        raise VerifyError("synthetic row match false")
    if packet["summary"] != {"rows": 1, "mismatches": 0, "status": "exact"}:
        raise VerifyError("synthetic summary mismatch")


def synthetic_packet_rejections() -> list[str]:
    zero = {"x": [0] * J, "y": [0] * J}
    packet = {
        "header": {"schema": "synthetic/v1", "binding": "f" * 64},
        "positive": {"candidate": copy.deepcopy(zero), "direct": copy.deepcopy(zero), "tamper_rejected": True},
        "negative": {"prime": 13, "rejected": True},
        "rows": [{
            "digest": "a" * 64,
            "candidate": copy.deepcopy(zero),
            "direct": copy.deepcopy(zero),
            "direct_aa": copy.deepcopy(zero),
            "match": True,
        }],
        "summary": {"rows": 1, "mismatches": 0, "status": "exact"},
    }
    validate_synthetic_packet(packet)
    mutations: dict[str, dict[str, Any]] = {}
    for name in (
        "header-hash", "candidate-coordinate", "direct-coordinate", "aa-coordinate",
        "positive-coordinate", "negative-boolean", "duplicate-row", "summary-count",
    ):
        mutations[name] = copy.deepcopy(packet)
    mutations["header-hash"]["header"]["binding"] = "e" * 64
    mutations["candidate-coordinate"]["rows"][0]["candidate"]["x"][0] = 1
    mutations["direct-coordinate"]["rows"][0]["direct"]["x"][0] = 1
    mutations["aa-coordinate"]["rows"][0]["direct_aa"]["x"][0] = 1
    mutations["positive-coordinate"]["positive"]["candidate"]["y"][0] = 1
    mutations["negative-boolean"]["negative"]["rejected"] = False
    mutations["duplicate-row"]["rows"].append(copy.deepcopy(packet["rows"][0]))
    mutations["summary-count"]["summary"]["rows"] = 2
    rejected = []
    for name, mutation in mutations.items():
        try:
            validate_synthetic_packet(mutation)
        except VerifyError:
            rejected.append(name)
        else:
            raise VerifyError(f"synthetic packet tamper {name} survived")
    return rejected


def selftest() -> dict[str, Any]:
    if sha256_hex(b"abc") != "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad":
        raise VerifyError("SHA-256 known-answer failure")
    if SplitMix64(0).next() != 0xE220A8397B1DCDAF:
        raise VerifyError("SplitMix64 known-answer failure")
    if first_irreducible(3, 2) != (1, 0, 1):
        raise VerifyError("irreducible-polynomial known-answer failure")
    if len(planted_controls()) != 32:
        raise VerifyError("planted-control count failure")
    for prime in (5, 7, 13):
        try:
            build_jet(prime, 2 % prime, 4 % prime, -3)
        except VerifyError:
            pass
        else:
            raise VerifyError(f"boundary p={prime} was accepted")

    excluded = Spec("h115-control-fp31", 31, 1, 19, 37, -5, 4)
    context = build_context(excluded)
    reference = context.base_generator
    target = context.curve.scale(2, reference)
    reference_coordinates = base_coordinates(context.field, reference)
    target_coordinates = base_coordinates(context.field, target)
    reference_native = absolute_direct_moments(context, section(context, reference))
    target_native = absolute_direct_moments(context, section(context, target))
    for lambda_value in (1, 2):
        direct = relative_direct(
            scale_moments(target_native, lambda_value, excluded.p),
            scale_moments(reference_native, lambda_value, excluded.p),
            excluded.p,
        )
        candidate, _, _ = candidate_for(
            excluded, target_coordinates, reference_coordinates, lambda_value
        )
        if candidate != direct:
            raise VerifyError(f"excluded p=31 lambda={lambda_value} mismatch")

    expected = ["curve\t1\tdigest\t2\t3", "curve\t1\tdigest2\t4\t5"]
    mutations = {
        "target-coordinate": ["curve\t1\tdigest\t2\t4", expected[1]],
        "target-digest": ["curve\t1\tdigesx\t2\t3", expected[1]],
        "target-order": list(reversed(expected)),
        "truncated-row": [expected[0]],
    }
    rejected = []
    for name, actual in mutations.items():
        try:
            require_exact_rows(actual, expected, name)
        except VerifyError:
            rejected.append(name)
        else:
            raise VerifyError(f"synthetic tamper {name} survived")
    rejected.extend(synthetic_packet_rejections())
    return {
        "status": "pass",
        "excluded_fixture": excluded.slug,
        "positive_controls": 32,
        "negative_controls": [5, 7, 13],
        "synthetic_tamper_rejections": rejected,
    }


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--selftest", action="store_true")
    modes.add_argument("--verify-targets", nargs=2, metavar=("TARGETS", "LABELS"))
    modes.add_argument("--verify-packet", nargs=2, metavar=("TARGETS", "PACKET"))
    arguments = parser.parse_args(argv)
    try:
        if arguments.selftest:
            result = selftest()
        elif arguments.verify_targets:
            result = verify_targets(Path(arguments.verify_targets[0]), Path(arguments.verify_targets[1]))
        else:
            result = verify_packet(Path(arguments.verify_packet[0]), Path(arguments.verify_packet[1]))
    except (OSError, VerifyError) as error:
        print(f"h116 verifier error: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
