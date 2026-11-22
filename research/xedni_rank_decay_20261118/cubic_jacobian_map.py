#!/usr/bin/env python3
"""Exact verifier scaffold for plane-cubic to Jacobian selected-point maps.

This module does not construct a map for an arbitrary plane cubic.  It checks
an explicit rational map, its inverse identities, the translation from the
map's Jacobian origin to the chosen chord origin, coefficient-unit reduction
and commutation at every selected point, source-subgroup replay, and supplied
relations.  The supported globally certified class is a projective-linear
isomorphism to a short-Weierstrass cubic.  More general birational maps remain
``SELECTED_POINTS_ONLY`` until their exceptional loci and global extension are
certified by a pinned constructor.

The distinction is intentional: PARI ``ellfromeqn`` can reconstruct a
Jacobian equation, but it does not provide the selected-point map required by
the Xedni rank experiment.
"""

from __future__ import annotations

from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
from typing import Any, Iterable

import sympy as sp


SCHEMA = "xedni.cubic-jacobian-map/v1"
VERIFY_SCHEMA = "xedni.cubic-jacobian-map-verification/v1"
ASSESSMENT_SCOPE = "r=7..9 selected-point transfer; no natural row"
PRODUCTION_READY = False
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
RATIONAL = re.compile(r"-?(?:0|[1-9][0-9]*)(?:/[1-9][0-9]*)?\Z")

# These are deliberately conservative verifier limits, not mathematical
# bounds on cubic/Jacobian maps.  This producer-side scaffold uses SymPy for
# exact substitution and expansion, so accepting an unbounded certificate
# would let a syntactically valid artifact consume unbounded CPU or memory
# before it reached any evidentiary gate.  A future pinned constructor may use
# a new schema with independently justified limits; callers may not raise
# these values inside a v1 certificate.
MAX_CERTIFICATE_NODES = 8_192
MAX_CERTIFICATE_DEPTH = 16
MAX_CONTAINER_ITEMS = 256
MAX_CERTIFICATE_TEXT_CHARS = 262_144
MAX_JSON_STRING_CHARS = 4_096
MAX_JSON_INTEGER_BITS = 4_096
MAX_RATIONAL_BITS = 4_096
MAX_POLYNOMIAL_TERMS = 48
MAX_POLYNOMIAL_EXPONENT = 12
MAX_POLYNOMIAL_COEFFICIENT_BITS = 1_024
# Degree five makes the required multiplier degree 3d-3 exactly fit the
# per-variable exponent ceiling above; v1 intentionally rejects larger maps.
MAX_MAP_COMPONENT_DEGREE = 5
MAX_COMPOSITION_EXPANSION_TERMS = 250_000
MAX_SOURCE_MULTIPLIER_BITS = 33
MAX_RELATIONS = 9
MAX_RELATION_COEFFICIENT_ABS = 128

TOP_KEYS = {
    "schema",
    "scope",
    "construction",
    "field",
    "prime",
    "cubic",
    "jacobian",
    "map",
    "origin",
    "selected_points",
    "source_subgroup",
    "relations",
    "certificate_sha256",
}
CONSTRUCTION_KEYS = {
    "backend",
    "available",
    "version",
    "identity",
    "backend_sha256",
    "status",
    "reason",
    "construction_sha256",
}
FIELD_KEYS = {"name", "characteristic"}
MODEL_KEYS = {"variables", "equation", "model_sha256"}
JACOBIAN_KEYS = MODEL_KEYS | {"a", "b", "discriminant"}
POLY_KEYS = {"variables", "terms"}
TERM_KEYS = {"exponents", "numerator", "denominator"}
MAP_KEYS = {
    "map_class",
    "forward",
    "inverse",
    "forward_multiplier",
    "inverse_multiplier",
    "exceptional_cubic_points",
    "exceptional_jacobian_points",
    "map_sha256",
}
POINT_KEYS = {
    "point_id",
    "cubic_coordinates",
    "forward_coordinates",
    "translated_coordinates",
    "source_multiplier",
    "point_sha256",
}
SOURCE_KEYS = {
    "prime",
    "a",
    "b",
    "generator",
    "generator_order",
    "origin_multiplier",
    "selected_multipliers",
    "source_sha256",
}
RELATION_KEYS = {"coefficients", "relation_sha256"}

X, Y, Z = sp.symbols("X Y Z")
x, y, z = sp.symbols("x y z")


class CubicMapError(ValueError):
    """Strict certificate or replay failure."""


def _preflight_json(value: Any, context: str) -> None:
    """Bound JSON shape before hashing, Fraction parsing, or SymPy work."""
    state = {"nodes": 0, "text_chars": 0}
    active: set[int] = set()

    def walk(item: Any, depth: int) -> None:
        state["nodes"] += 1
        if state["nodes"] > MAX_CERTIFICATE_NODES:
            raise CubicMapError(f"{context}: certificate complexity exceeds node limit")
        if depth > MAX_CERTIFICATE_DEPTH:
            raise CubicMapError(f"{context}: certificate complexity exceeds depth limit")
        if item is None or isinstance(item, bool):
            return
        if isinstance(item, int):
            if abs(item).bit_length() > MAX_JSON_INTEGER_BITS:
                raise CubicMapError(
                    f"{context}: certificate complexity exceeds integer-bit limit"
                )
            state["text_chars"] += max(
                1, (abs(item).bit_length() * 30103) // 100000 + 1
            )
        elif isinstance(item, str):
            if len(item) > MAX_JSON_STRING_CHARS:
                raise CubicMapError(
                    f"{context}: certificate complexity exceeds string limit"
                )
            state["text_chars"] += len(item)
        elif isinstance(item, (list, dict)):
            if len(item) > MAX_CONTAINER_ITEMS:
                raise CubicMapError(
                    f"{context}: certificate complexity exceeds container limit"
                )
            identity = id(item)
            if identity in active:
                raise CubicMapError(f"{context}: cyclic value is not strict JSON")
            active.add(identity)
            try:
                if isinstance(item, list):
                    for child in item:
                        walk(child, depth + 1)
                else:
                    for key, child in item.items():
                        if not isinstance(key, str):
                            raise CubicMapError(
                                f"{context}: object key is not a string"
                            )
                        walk(key, depth + 1)
                        walk(child, depth + 1)
            finally:
                active.remove(identity)
        else:
            raise CubicMapError(f"{context}: unsupported non-JSON value")
        if state["text_chars"] > MAX_CERTIFICATE_TEXT_CHARS:
            raise CubicMapError(
                f"{context}: certificate complexity exceeds text budget"
            )

    walk(value, 0)


def _preflight_certificate_complexity(value: Any) -> None:
    """Apply semantic scalar/count ceilings before symbolic or group work."""
    _preflight_json(value, "certificate")
    if not isinstance(value, dict):
        return
    points = [value.get("origin")]
    selected = value.get("selected_points")
    if isinstance(selected, list):
        points.extend(selected)
    for point in points:
        if not isinstance(point, dict):
            continue
        multiplier = point.get("source_multiplier")
        if (
            isinstance(multiplier, int)
            and not isinstance(multiplier, bool)
            and abs(multiplier).bit_length() > MAX_SOURCE_MULTIPLIER_BITS
        ):
            raise CubicMapError(
                "certificate: source multiplier exceeds exact-replay bit limit"
            )
    relations = value.get("relations")
    if not isinstance(relations, list):
        return
    if len(relations) > MAX_RELATIONS:
        raise CubicMapError(
            "certificate: relation count exceeds exact-replay limit"
        )
    for relation in relations:
        if not isinstance(relation, dict):
            continue
        coefficients = relation.get("coefficients")
        if not isinstance(coefficients, list):
            continue
        for coefficient in coefficients:
            if (
                isinstance(coefficient, int)
                and not isinstance(coefficient, bool)
                and abs(coefficient) > MAX_RELATION_COEFFICIENT_ABS
            ):
                raise CubicMapError(
                    "certificate: relation coefficient exceeds exact-replay scalar limit"
                )


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def object_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _exact_keys(value: Any, expected: set[str], context: str) -> dict:
    if not isinstance(value, dict):
        raise CubicMapError(f"{context}: expected object")
    actual = set(value)
    if actual != expected:
        raise CubicMapError(
            f"{context}: key mismatch missing={sorted(expected-actual)} "
            f"extra={sorted(actual-expected)}"
        )
    return value


def _plain_int(value: Any, context: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise CubicMapError(f"{context}: expected integer")
    return value


def _positive_int(value: Any, context: str) -> int:
    result = _plain_int(value, context)
    if result <= 0:
        raise CubicMapError(f"{context}: expected positive integer")
    return result


def _hash(value: Any, context: str) -> str:
    if not isinstance(value, str) or HEX64.fullmatch(value) is None:
        raise CubicMapError(f"{context}: expected lowercase SHA-256")
    return value


def _fraction(value: Any, context: str) -> Fraction:
    if not isinstance(value, str) or RATIONAL.fullmatch(value) is None:
        raise CubicMapError(f"{context}: expected canonical rational text")
    result = Fraction(value)
    if (
        abs(result.numerator).bit_length() > MAX_RATIONAL_BITS
        or result.denominator.bit_length() > MAX_RATIONAL_BITS
    ):
        raise CubicMapError(f"{context}: rational complexity exceeds bit limit")
    canonical = str(result.numerator)
    if result.denominator != 1:
        canonical += f"/{result.denominator}"
    if value != canonical:
        raise CubicMapError(f"{context}: rational text is not canonical")
    return result


def _fraction_text(value: Fraction | int) -> str:
    value = Fraction(value)
    return (
        str(value.numerator)
        if value.denominator == 1
        else f"{value.numerator}/{value.denominator}"
    )


def _projective(value: Any, context: str) -> tuple[Fraction, Fraction, Fraction]:
    if not isinstance(value, list) or len(value) != 3:
        raise CubicMapError(f"{context}: expected three projective coordinates")
    coordinates = tuple(_fraction(item, f"{context}[{index}]") for index, item in enumerate(value))
    if all(item == 0 for item in coordinates):
        raise CubicMapError(f"{context}: all-zero projective point")
    return _normalize_projective(coordinates)


def _normalize_projective(
    point: Iterable[Fraction | int],
) -> tuple[Fraction, Fraction, Fraction]:
    values = tuple(Fraction(item) for item in point)
    denominators = [item.denominator for item in values]
    scale = math.lcm(*denominators)
    integers = [int(item * scale) for item in values]
    divisor = 0
    for item in integers:
        divisor = math.gcd(divisor, abs(item))
    if divisor == 0:
        raise CubicMapError("all-zero projective point")
    integers = [item // divisor for item in integers]
    for item in integers:
        if item:
            if item < 0:
                integers = [-entry for entry in integers]
            break
    return tuple(Fraction(item) for item in integers)  # type: ignore[return-value]


def _point_json(point: Iterable[Fraction | int]) -> list[str]:
    return [_fraction_text(value) for value in _normalize_projective(point)]


def _poly(value: Any, expected_variables: tuple[str, str, str], context: str) -> sp.Poly:
    value = _exact_keys(value, POLY_KEYS, context)
    if value["variables"] != list(expected_variables):
        raise CubicMapError(f"{context}.variables: unexpected variables")
    terms = value["terms"]
    if not isinstance(terms, list) or not terms:
        raise CubicMapError(f"{context}.terms: expected nonempty list")
    if len(terms) > MAX_POLYNOMIAL_TERMS:
        raise CubicMapError(f"{context}: polynomial complexity exceeds term limit")
    symbols = (X, Y, Z) if expected_variables == ("X", "Y", "Z") else (x, y, z)
    seen: set[tuple[int, int, int]] = set()
    expression = sp.Integer(0)
    last: tuple[int, int, int] | None = None
    for index, raw in enumerate(terms):
        raw = _exact_keys(raw, TERM_KEYS, f"{context}.terms[{index}]")
        exponents = raw["exponents"]
        if (
            not isinstance(exponents, list)
            or len(exponents) != 3
            or any(
                isinstance(item, bool)
                or not isinstance(item, int)
                or item < 0
                or item > MAX_POLYNOMIAL_EXPONENT
                for item in exponents
            )
        ):
            raise CubicMapError(f"{context}.terms[{index}].exponents: invalid")
        exponent_tuple = tuple(exponents)
        if exponent_tuple in seen:
            raise CubicMapError(f"{context}: duplicate monomial")
        if last is not None and exponent_tuple >= last:
            raise CubicMapError(f"{context}: terms are not in descending canonical order")
        seen.add(exponent_tuple)
        last = exponent_tuple
        numerator = _plain_int(raw["numerator"], f"{context}.terms[{index}].numerator")
        denominator = _positive_int(raw["denominator"], f"{context}.terms[{index}].denominator")
        if (
            abs(numerator).bit_length() > MAX_POLYNOMIAL_COEFFICIENT_BITS
            or denominator.bit_length() > MAX_POLYNOMIAL_COEFFICIENT_BITS
        ):
            raise CubicMapError(
                f"{context}.terms[{index}]: polynomial coefficient complexity exceeds bit limit"
            )
        coefficient = Fraction(numerator, denominator)
        if coefficient == 0 or coefficient.denominator != denominator:
            raise CubicMapError(f"{context}.terms[{index}]: noncanonical coefficient")
        monomial = sp.Integer(1)
        for symbol, exponent in zip(symbols, exponent_tuple):
            monomial *= symbol**exponent
        expression += sp.Rational(coefficient.numerator, coefficient.denominator) * monomial
    return sp.Poly(expression, *symbols, domain=sp.QQ)


def _poly_json(
    terms: dict[tuple[int, int, int], Fraction | int], variables: tuple[str, str, str]
) -> dict:
    retained = []
    for exponents in sorted(terms, reverse=True):
        coefficient = Fraction(terms[exponents])
        if not coefficient:
            continue
        retained.append(
            {
                "exponents": list(exponents),
                "numerator": coefficient.numerator,
                "denominator": coefficient.denominator,
            }
        )
    return {"variables": list(variables), "terms": retained}


def _poly_eval(poly: sp.Poly, point: tuple[Fraction, Fraction, Fraction]) -> Fraction:
    result = poly.as_expr().subs(dict(zip(poly.gens, map(sp.Rational, point))))
    return Fraction(result)


def _component_list(value: Any, variables: tuple[str, str, str], context: str) -> list[sp.Poly]:
    if not isinstance(value, list) or len(value) != 3:
        raise CubicMapError(f"{context}: expected three map components")
    components = [_poly(item, variables, f"{context}[{index}]") for index, item in enumerate(value)]
    if any(not component.is_homogeneous for component in components):
        raise CubicMapError(f"{context}: every component must be homogeneous")
    degrees = {component.total_degree() for component in components}
    if len(degrees) != 1 or next(iter(degrees)) <= 0:
        raise CubicMapError(f"{context}: components must have one common degree")
    return components


def _map_eval(
    components: list[sp.Poly], point: tuple[Fraction, Fraction, Fraction], context: str
) -> tuple[Fraction, Fraction, Fraction]:
    values = tuple(_poly_eval(component, point) for component in components)
    if all(value == 0 for value in values):
        raise CubicMapError(f"{context}: point is in map base locus")
    return _normalize_projective(values)


def _substitute(poly: sp.Poly, components: list[sp.Poly], target_symbols: tuple[sp.Symbol, ...]) -> sp.Poly:
    substitutions = dict(zip(poly.gens, [component.as_expr() for component in components]))
    return sp.Poly(sp.expand(poly.as_expr().subs(substitutions, simultaneous=True)), *target_symbols, domain=sp.QQ)


def _composition_term_bound(poly: sp.Poly, components: list[sp.Poly]) -> int:
    """Naive expansion upper bound, used only to reject hazardous inputs."""
    component_terms = [len(component.terms()) for component in components]
    total = 0
    for exponents, _coefficient in poly.terms():
        term_bound = 1
        for count, exponent in zip(component_terms, exponents):
            term_bound *= count**exponent
            if term_bound > MAX_COMPOSITION_EXPANSION_TERMS:
                return term_bound
        total += term_bound
        if total > MAX_COMPOSITION_EXPANSION_TERMS:
            return total
    return total


def _require_bounded_composition(
    poly: sp.Poly, components: list[sp.Poly], context: str
) -> None:
    if _composition_term_bound(poly, components) > MAX_COMPOSITION_EXPANSION_TERMS:
        raise CubicMapError(
            f"{context}: symbolic composition complexity exceeds expansion limit"
        )


def _zero(poly: sp.Poly, context: str) -> None:
    if not poly.is_zero:
        raise CubicMapError(f"{context}: polynomial identity failed")


def _divisible(poly: sp.Poly, divisor: sp.Poly, context: str) -> None:
    _, remainder = sp.div(poly, divisor)
    if not remainder.is_zero:
        raise CubicMapError(f"{context}: identity does not vanish on the curve")


PointQ = tuple[Fraction, Fraction] | None
PointP = tuple[int, int] | None


def _affine(point: tuple[Fraction, Fraction, Fraction], context: str) -> PointQ:
    if point[2] == 0:
        if point != (Fraction(0), Fraction(1), Fraction(0)):
            raise CubicMapError(f"{context}: unexpected point at infinity")
        return None
    return point[0] / point[2], point[1] / point[2]


def _projectivize(point: PointQ) -> tuple[Fraction, Fraction, Fraction]:
    return (Fraction(0), Fraction(1), Fraction(0)) if point is None else (point[0], point[1], Fraction(1))


def _on_curve_q(point: PointQ, a: int, b: int) -> bool:
    if point is None:
        return True
    px, py = point
    return py * py == px * px * px + a * px + b


def _neg_q(point: PointQ) -> PointQ:
    return None if point is None else (point[0], -point[1])


def _add_q(left: PointQ, right: PointQ, a: int) -> PointQ:
    if left is None:
        return right
    if right is None:
        return left
    x1, y1 = left
    x2, y2 = right
    if x1 == x2 and y1 == -y2:
        return None
    if left == right:
        if y1 == 0:
            return None
        slope = (3 * x1 * x1 + a) / (2 * y1)
    else:
        slope = (y2 - y1) / (x2 - x1)
    x3 = slope * slope - x1 - x2
    return x3, slope * (x1 - x3) - y1


def _mul_q(scalar: int, point: PointQ, a: int) -> PointQ:
    if scalar < 0:
        return _mul_q(-scalar, _neg_q(point), a)
    result = None
    addend = point
    while scalar:
        if scalar & 1:
            result = _add_q(result, addend, a)
        addend = _add_q(addend, addend, a)
        scalar >>= 1
    return result


def _reduce_fraction(value: Fraction, prime: int, context: str) -> int:
    if value.denominator % prime == 0:
        raise CubicMapError(f"{context}: denominator is not a unit modulo p")
    return value.numerator * pow(value.denominator, -1, prime) % prime


def _reduce_point(point: PointQ, prime: int, context: str) -> PointP:
    if point is None:
        return None
    return (
        _reduce_fraction(point[0], prime, f"{context}.x"),
        _reduce_fraction(point[1], prime, f"{context}.y"),
    )


def _normalize_projective_p(
    point: Iterable[int], prime: int, context: str
) -> tuple[int, int, int]:
    values = tuple(value % prime for value in point)
    for value in values:
        if value:
            inverse = pow(value, -1, prime)
            return tuple(entry * inverse % prime for entry in values)  # type: ignore[return-value]
    raise CubicMapError(f"{context}: all-zero projective point modulo p")


def _reduce_projective(
    point: tuple[Fraction, Fraction, Fraction], prime: int, context: str
) -> tuple[int, int, int]:
    values = tuple(
        _reduce_fraction(value, prime, f"{context}[{index}]")
        for index, value in enumerate(point)
    )
    return _normalize_projective_p(values, prime, context)


def _poly_eval_p(
    poly: sp.Poly, point: tuple[int, int, int], prime: int, context: str
) -> int:
    total = 0
    for exponents, coefficient in poly.terms():
        rational = Fraction(coefficient)
        if rational.denominator % prime == 0:
            raise CubicMapError(
                f"{context}: map coefficient denominator is not a unit modulo p"
            )
        value = rational.numerator * pow(rational.denominator, -1, prime) % prime
        for coordinate, exponent in zip(point, exponents):
            value = value * pow(coordinate, exponent, prime) % prime
        total = (total + value) % prime
    return total


def _map_eval_p(
    components: list[sp.Poly],
    point: tuple[int, int, int],
    prime: int,
    context: str,
) -> tuple[int, int, int]:
    values = tuple(
        _poly_eval_p(component, point, prime, f"{context}[{index}]")
        for index, component in enumerate(components)
    )
    return _normalize_projective_p(values, prime, context)


def _require_unit_coefficients(polynomials: Iterable[sp.Poly], prime: int) -> None:
    for polynomial in polynomials:
        for coefficient in polynomial.coeffs():
            if Fraction(coefficient).denominator % prime == 0:
                raise CubicMapError(
                    "map: coefficient denominator is not a unit modulo p"
                )


def _on_curve_p(point: PointP, a: int, b: int, prime: int) -> bool:
    if point is None:
        return True
    px, py = point
    return (py * py - (px * px * px + a * px + b)) % prime == 0


def _neg_p(point: PointP, prime: int) -> PointP:
    return None if point is None else (point[0], (-point[1]) % prime)


def _add_p(left: PointP, right: PointP, a: int, prime: int) -> PointP:
    if left is None:
        return right
    if right is None:
        return left
    x1, y1 = left
    x2, y2 = right
    if x1 == x2 and (y1 + y2) % prime == 0:
        return None
    if left == right:
        if 2 * y1 % prime == 0:
            return None
        slope = (3 * x1 * x1 + a) * pow(2 * y1, -1, prime) % prime
    else:
        slope = (y2 - y1) * pow((x2 - x1) % prime, -1, prime) % prime
    x3 = (slope * slope - x1 - x2) % prime
    return x3, (slope * (x1 - x3) - y1) % prime


def _mul_p(scalar: int, point: PointP, a: int, prime: int) -> PointP:
    if scalar < 0:
        return _mul_p(-scalar, _neg_p(point, prime), a, prime)
    result = None
    addend = point
    while scalar:
        if scalar & 1:
            result = _add_p(result, addend, a, prime)
        addend = _add_p(addend, addend, a, prime)
        scalar >>= 1
    return result


def _is_prime(value: int) -> bool:
    if value < 2:
        return False
    small = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)
    for prime in small:
        if value % prime == 0:
            return value == prime
    odd = value - 1
    shifts = 0
    while odd % 2 == 0:
        shifts += 1
        odd //= 2
    for base in (2, 3, 5, 7, 11):
        if base >= value:
            continue
        witness = pow(base, odd, value)
        if witness in (1, value - 1):
            continue
        for _ in range(shifts - 1):
            witness = witness * witness % value
            if witness == value - 1:
                break
        else:
            return False
    return True


def _verify_self_hash(value: dict, field: str, context: str) -> None:
    expected = _hash(value[field], f"{context}.{field}")
    payload = {key: item for key, item in value.items() if key != field}
    if object_sha256(payload) != expected:
        raise CubicMapError(f"{context}.{field}: self hash mismatch")


def _model(value: Any, variables: tuple[str, str, str], context: str) -> sp.Poly:
    value = _exact_keys(value, MODEL_KEYS, context)
    if value["variables"] != list(variables):
        raise CubicMapError(f"{context}.variables: unexpected variables")
    _verify_self_hash(value, "model_sha256", context)
    equation = _poly(value["equation"], variables, f"{context}.equation")
    if equation.total_degree() != 3 or not equation.is_homogeneous:
        raise CubicMapError(f"{context}.equation: expected homogeneous cubic")
    return equation


def _jacobian(value: Any) -> tuple[sp.Poly, int, int]:
    value = _exact_keys(value, JACOBIAN_KEYS, "jacobian")
    _verify_self_hash(value, "model_sha256", "jacobian")
    a = _plain_int(value["a"], "jacobian.a")
    b = _plain_int(value["b"], "jacobian.b")
    discriminant = _plain_int(value["discriminant"], "jacobian.discriminant")
    expected_discriminant = -16 * (4 * a**3 + 27 * b**2)
    if discriminant != expected_discriminant or discriminant == 0:
        raise CubicMapError("jacobian.discriminant: mismatch or singular")
    equation = _poly(value["equation"], ("x", "y", "z"), "jacobian.equation")
    expected = sp.Poly(y**2 * z - x**3 - a * x * z**2 - b * z**3, x, y, z, domain=sp.QQ)
    if equation != expected:
        raise CubicMapError("jacobian.equation: not the stated short-Weierstrass model")
    return equation, a, b


def _map(value: Any, cubic: sp.Poly, jacobian: sp.Poly) -> dict:
    value = _exact_keys(value, MAP_KEYS, "map")
    _verify_self_hash(value, "map_sha256", "map")
    map_class = value["map_class"]
    if map_class not in {"projective_linear_isomorphism", "birational_selected_points_only"}:
        raise CubicMapError("map.map_class: unsupported")
    forward = _component_list(value["forward"], ("X", "Y", "Z"), "map.forward")
    inverse = _component_list(value["inverse"], ("x", "y", "z"), "map.inverse")
    forward_multiplier = _poly(value["forward_multiplier"], ("X", "Y", "Z"), "map.forward_multiplier")
    inverse_multiplier = _poly(value["inverse_multiplier"], ("x", "y", "z"), "map.inverse_multiplier")
    forward_degree = forward[0].total_degree()
    inverse_degree = inverse[0].total_degree()
    if (
        forward_degree > MAX_MAP_COMPONENT_DEGREE
        or inverse_degree > MAX_MAP_COMPONENT_DEGREE
    ):
        raise CubicMapError("map: map-component degree exceeds complexity limit")
    if (
        not forward_multiplier.is_homogeneous
        or forward_multiplier.total_degree() != 3 * forward_degree - 3
    ):
        raise CubicMapError("map.forward_multiplier: wrong homogeneous degree")
    if (
        not inverse_multiplier.is_homogeneous
        or inverse_multiplier.total_degree() != 3 * inverse_degree - 3
    ):
        raise CubicMapError("map.inverse_multiplier: wrong homogeneous degree")
    _require_bounded_composition(jacobian, forward, "map.forward")
    _require_bounded_composition(cubic, inverse, "map.inverse")
    _zero(
        _substitute(jacobian, forward, (X, Y, Z)) - cubic * forward_multiplier,
        "map.forward",
    )
    _zero(
        _substitute(cubic, inverse, (x, y, z)) - jacobian * inverse_multiplier,
        "map.inverse",
    )
    for index, component in enumerate(inverse):
        _require_bounded_composition(
            component, forward, f"map.inverse_after_forward[{index}]"
        )
    for index, component in enumerate(forward):
        _require_bounded_composition(
            component, inverse, f"map.forward_after_inverse[{index}]"
        )
    inverse_after_forward = [_substitute(component, forward, (X, Y, Z)) for component in inverse]
    forward_after_inverse = [_substitute(component, inverse, (x, y, z)) for component in forward]
    for left, right, context in (
        (0, 1, "inverse-forward XY"),
        (0, 2, "inverse-forward XZ"),
        (1, 2, "inverse-forward YZ"),
    ):
        source_coordinates = (X, Y, Z)
        cross = inverse_after_forward[left] * source_coordinates[right] - inverse_after_forward[right] * source_coordinates[left]
        _divisible(cross, cubic, f"map.{context}")
    for left, right, context in (
        (0, 1, "forward-inverse xy"),
        (0, 2, "forward-inverse xz"),
        (1, 2, "forward-inverse yz"),
    ):
        destination_coordinates = (x, y, z)
        cross = forward_after_inverse[left] * destination_coordinates[right] - forward_after_inverse[right] * destination_coordinates[left]
        _divisible(cross, jacobian, f"map.{context}")
    if map_class == "projective_linear_isomorphism":
        if any(component.total_degree() != 1 for component in forward + inverse):
            raise CubicMapError("map: projective-linear class requires linear components")
        if value["exceptional_cubic_points"] or value["exceptional_jacobian_points"]:
            raise CubicMapError("map: projective-linear class has no exceptional points")
        forward_matrix = sp.Matrix(
            [
                [component.coeff_monomial(symbol) for symbol in (X, Y, Z)]
                for component in forward
            ]
        )
        inverse_matrix = sp.Matrix(
            [
                [component.coeff_monomial(symbol) for symbol in (x, y, z)]
                for component in inverse
            ]
        )
        if forward_matrix.det() == 0 or inverse_matrix.det() == 0:
            raise CubicMapError("map: projective-linear component matrix is singular")
    else:
        forward_matrix = None
        inverse_matrix = None
    for key, curve, components in (
        ("exceptional_cubic_points", cubic, forward),
        ("exceptional_jacobian_points", jacobian, inverse),
    ):
        if not isinstance(value[key], list):
            raise CubicMapError(f"map.{key}: expected list")
        seen_exceptional = set()
        for index, raw_point in enumerate(value[key]):
            point = _projective(raw_point, f"map.{key}[{index}]")
            if point in seen_exceptional:
                raise CubicMapError(f"map.{key}: duplicate exceptional point")
            seen_exceptional.add(point)
            if _poly_eval(curve, point) != 0:
                raise CubicMapError(f"map.{key}[{index}]: point is off the named curve")
            if any(_poly_eval(component, point) != 0 for component in components):
                raise CubicMapError(f"map.{key}[{index}]: point is not in the base locus")
    return {
        "class": map_class,
        "forward": forward,
        "inverse": inverse,
        "all_polynomials": forward
        + inverse
        + [forward_multiplier, inverse_multiplier, cubic, jacobian],
        "forward_matrix": forward_matrix,
        "inverse_matrix": inverse_matrix,
    }


def _point(value: Any, context: str) -> dict:
    value = _exact_keys(value, POINT_KEYS, context)
    _verify_self_hash(value, "point_sha256", context)
    point_id = value["point_id"]
    if not isinstance(point_id, str) or not re.fullmatch(r"[A-Za-z0-9_.:-]{1,96}", point_id):
        raise CubicMapError(f"{context}.point_id: invalid")
    multiplier = _plain_int(value["source_multiplier"], f"{context}.source_multiplier")
    if abs(multiplier).bit_length() > MAX_SOURCE_MULTIPLIER_BITS:
        raise CubicMapError(
            f"{context}.source_multiplier: exceeds exact-replay bit limit"
        )
    return {
        "id": point_id,
        "cubic": _projective(value["cubic_coordinates"], f"{context}.cubic_coordinates"),
        "forward": _projective(value["forward_coordinates"], f"{context}.forward_coordinates"),
        "translated": _projective(value["translated_coordinates"], f"{context}.translated_coordinates"),
        "multiplier": multiplier,
    }


def _source(value: Any, prime: int, a: int, b: int, r: int) -> dict:
    value = _exact_keys(value, SOURCE_KEYS, "source_subgroup")
    _verify_self_hash(value, "source_sha256", "source_subgroup")
    if value["prime"] != prime or value["a"] != a or value["b"] != b:
        raise CubicMapError("source_subgroup: curve identity mismatch")
    generator_raw = value["generator"]
    if (
        not isinstance(generator_raw, list)
        or len(generator_raw) != 2
        or any(isinstance(item, bool) or not isinstance(item, int) for item in generator_raw)
    ):
        raise CubicMapError("source_subgroup.generator: invalid")
    generator = tuple(item % prime for item in generator_raw)
    if not _on_curve_p(generator, a, b, prime):
        raise CubicMapError("source_subgroup.generator: off curve")
    order = _positive_int(value["generator_order"], "source_subgroup.generator_order")
    hasse_upper = prime + 1 + math.isqrt(4 * prime)
    if order > hasse_upper:
        raise CubicMapError("source_subgroup.generator_order: exceeds Hasse bound")
    if _mul_p(order, generator, a, prime) is not None:
        raise CubicMapError("source_subgroup.generator_order: does not annihilate generator")
    remaining = order
    prime_divisors = []
    divisor = 2
    while divisor * divisor <= remaining:
        if remaining % divisor == 0:
            prime_divisors.append(divisor)
            while remaining % divisor == 0:
                remaining //= divisor
        divisor += 1 if divisor == 2 else 2
    if remaining > 1:
        prime_divisors.append(remaining)
    for divisor in prime_divisors:
        if _mul_p(order // divisor, generator, a, prime) is None:
            raise CubicMapError("source_subgroup.generator_order: not exact")
    selected = value["selected_multipliers"]
    if not isinstance(selected, list) or len(selected) != r:
        raise CubicMapError("source_subgroup.selected_multipliers: wrong length")
    selected = [_plain_int(item, f"source_subgroup.selected_multipliers[{index}]") for index, item in enumerate(selected)]
    return {
        "generator": generator,
        "order": order,
        "origin_multiplier": _plain_int(value["origin_multiplier"], "source_subgroup.origin_multiplier"),
        "selected_multipliers": selected,
    }


def _relation(value: Any, r: int, index: int) -> list[int]:
    value = _exact_keys(value, RELATION_KEYS, f"relations[{index}]")
    _verify_self_hash(value, "relation_sha256", f"relations[{index}]")
    coefficients = value["coefficients"]
    if (
        not isinstance(coefficients, list)
        or len(coefficients) != r
        or any(isinstance(item, bool) or not isinstance(item, int) for item in coefficients)
        or not any(coefficients)
    ):
        raise CubicMapError(f"relations[{index}].coefficients: invalid")
    if any(abs(item) > MAX_RELATION_COEFFICIENT_ABS for item in coefficients):
        raise CubicMapError(
            f"relations[{index}]: coefficient exceeds exact-replay scalar limit"
        )
    divisor = 0
    for item in coefficients:
        divisor = math.gcd(divisor, abs(item))
    if divisor != 1:
        raise CubicMapError(f"relations[{index}]: expected primitive vector")
    return coefficients


def verify_certificate(certificate: Any) -> dict:
    """Replay one explicit transfer certificate without constructing a map."""
    _preflight_certificate_complexity(certificate)
    certificate = _exact_keys(certificate, TOP_KEYS, "certificate")
    if certificate["schema"] != SCHEMA or certificate["scope"] != ASSESSMENT_SCOPE:
        raise CubicMapError("certificate: schema or scope mismatch")
    _verify_self_hash(certificate, "certificate_sha256", "certificate")
    construction = _exact_keys(certificate["construction"], CONSTRUCTION_KEYS, "construction")
    _verify_self_hash(construction, "construction_sha256", "construction")
    if construction["available"] is not True or construction["status"] != "SUPPLIED_EXPLICIT_MAP":
        raise CubicMapError("construction: explicit map is unavailable")
    for key in ("backend", "version", "identity", "reason"):
        if not isinstance(construction[key], str) or not construction[key].strip():
            raise CubicMapError(f"construction.{key}: nonempty string required")
    expected_backend_hash = object_sha256(
        {
            "backend": construction["backend"],
            "version": construction["version"],
            "identity": construction["identity"],
        }
    )
    if _hash(construction["backend_sha256"], "construction.backend_sha256") != expected_backend_hash:
        raise CubicMapError("construction.backend_sha256: identity mismatch")
    field = _exact_keys(certificate["field"], FIELD_KEYS, "field")
    if field != {"name": "Q", "characteristic": 0}:
        raise CubicMapError("field: only Q is supported")
    prime = _positive_int(certificate["prime"], "prime")
    if prime == 2 or prime >= 2**32 or not _is_prime(prime):
        raise CubicMapError("prime: expected an odd prime below 2^32")
    cubic = _model(certificate["cubic"], ("X", "Y", "Z"), "cubic")
    jacobian, a, b = _jacobian(certificate["jacobian"])
    map_data = _map(certificate["map"], cubic, jacobian)
    _require_unit_coefficients(map_data["all_polynomials"], prime)
    if map_data["class"] == "projective_linear_isomorphism":
        for name in ("forward_matrix", "inverse_matrix"):
            determinant = Fraction(map_data[name].det())
            if _reduce_fraction(determinant, prime, f"map.{name}.determinant") == 0:
                raise CubicMapError(f"map.{name}: singular after reduction")
    if certificate["jacobian"]["discriminant"] % prime == 0:
        raise CubicMapError("jacobian: bad reduction at source prime")
    origin = _point(certificate["origin"], "origin")
    selected_raw = certificate["selected_points"]
    if not isinstance(selected_raw, list) or len(selected_raw) not in (7, 8, 9):
        raise CubicMapError("selected_points: expected r=7, 8, or 9")
    selected = [_point(value, f"selected_points[{index}]") for index, value in enumerate(selected_raw)]
    identifiers = [item["id"] for item in selected]
    if len(set(identifiers)) != len(identifiers) or origin["id"] != "origin":
        raise CubicMapError("points: duplicate id or origin id mismatch")
    cubic_points = [item["cubic"] for item in selected]
    if len(set(cubic_points)) != len(cubic_points) or origin["cubic"] in set(cubic_points):
        raise CubicMapError("points: selected cubic points and origin must be distinct")
    source = _source(certificate["source_subgroup"], prime, a, b, len(selected))
    if source["origin_multiplier"] != origin["multiplier"]:
        raise CubicMapError("origin: source multiplier mismatch")
    if source["selected_multipliers"] != [item["multiplier"] for item in selected]:
        raise CubicMapError("selected_points: source multiplier ordering mismatch")
    residues = [item % source["order"] for item in source["selected_multipliers"]]
    if (
        len(set(residues)) != len(residues)
        or source["origin_multiplier"] % source["order"] in set(residues)
    ):
        raise CubicMapError("source_subgroup: selected points and origin are not distinct")
    exceptional_cubic = {
        _projective(value, f"map.exceptional_cubic_points[{index}]")
        for index, value in enumerate(certificate["map"]["exceptional_cubic_points"])
    }
    exceptional_jacobian = {
        _projective(value, f"map.exceptional_jacobian_points[{index}]")
        for index, value in enumerate(certificate["map"]["exceptional_jacobian_points"])
    }
    all_points = [origin] + selected
    forward_affine: list[PointQ] = []
    translated_affine: list[PointQ] = []
    for index, point in enumerate(all_points):
        context = "origin" if index == 0 else f"selected_points[{index-1}]"
        if point["cubic"] in exceptional_cubic:
            raise CubicMapError(f"{context}: point is exceptional")
        if _poly_eval(cubic, point["cubic"]) != 0:
            raise CubicMapError(f"{context}: cubic point is off curve")
        mapped = _map_eval(map_data["forward"], point["cubic"], context)
        if mapped != point["forward"]:
            raise CubicMapError(f"{context}: forward image mismatch")
        if mapped in exceptional_jacobian:
            raise CubicMapError(f"{context}: forward image is inverse-exceptional")
        recovered = _map_eval(map_data["inverse"], mapped, f"{context}.inverse")
        if recovered != point["cubic"]:
            raise CubicMapError(f"{context}: inverse image mismatch")
        cubic_mod = _reduce_projective(point["cubic"], prime, f"{context}.cubic")
        forward_mod_projective = _reduce_projective(mapped, prime, f"{context}.forward")
        if (
            _map_eval_p(map_data["forward"], cubic_mod, prime, f"{context}.forward_mod")
            != forward_mod_projective
        ):
            raise CubicMapError(f"{context}: forward map does not commute with reduction")
        if (
            _map_eval_p(
                map_data["inverse"],
                forward_mod_projective,
                prime,
                f"{context}.inverse_mod",
            )
            != cubic_mod
        ):
            raise CubicMapError(f"{context}: inverse map does not commute with reduction")
        affine = _affine(mapped, f"{context}.forward")
        if not _on_curve_q(affine, a, b):
            raise CubicMapError(f"{context}: forward image is off Jacobian")
        forward_affine.append(affine)
    origin_image = forward_affine[0]
    for index, (point, forward_point) in enumerate(zip(all_points, forward_affine)):
        context = "origin" if index == 0 else f"selected_points[{index-1}]"
        translated = _add_q(forward_point, _neg_q(origin_image), a)
        if _normalize_projective(_projectivize(translated)) != point["translated"]:
            raise CubicMapError(f"{context}: origin translation mismatch")
        translated_affine.append(translated)
    if translated_affine[0] is not None:
        raise CubicMapError("origin: translated origin is not the identity")
    generator = source["generator"]
    order = source["order"]
    origin_mod = _reduce_point(origin_image, prime, "origin.forward")
    if origin_mod != _mul_p(origin["multiplier"], generator, a, prime):
        raise CubicMapError("origin: finite-field source replay failed")
    for index, point in enumerate(selected):
        forward_mod = _reduce_point(forward_affine[index + 1], prime, f"selected_points[{index}].forward")
        translated_mod = _reduce_point(translated_affine[index + 1], prime, f"selected_points[{index}].translated")
        if forward_mod != _mul_p(point["multiplier"], generator, a, prime):
            raise CubicMapError(f"selected_points[{index}]: forward source replay failed")
        shifted = (point["multiplier"] - origin["multiplier"]) % order
        if translated_mod != _mul_p(shifted, generator, a, prime):
            raise CubicMapError(f"selected_points[{index}]: translated source replay failed")
    relations_raw = certificate["relations"]
    if not isinstance(relations_raw, list):
        raise CubicMapError("relations: expected list")
    relations = [_relation(value, len(selected), index) for index, value in enumerate(relations_raw)]
    for relation_index, coefficients in enumerate(relations):
        total_q = None
        total_p = None
        scalar_total = 0
        for coefficient, point_q, point in zip(coefficients, translated_affine[1:], selected):
            total_q = _add_q(total_q, _mul_q(coefficient, point_q, a), a)
            total_p = _add_p(total_p, _mul_p(coefficient, _reduce_point(point_q, prime, "relation point"), a, prime), a, prime)
            scalar_total += coefficient * (point["multiplier"] - origin["multiplier"])
        if total_q is not None or total_p is not None or scalar_total % order:
            raise CubicMapError(f"relations[{relation_index}]: replay failed")
    global_status = (
        "VERIFIED_PROJECTIVE_LINEAR_TRANSFER"
        if map_data["class"] == "projective_linear_isomorphism"
        else "SELECTED_POINTS_ONLY"
    )
    result = {
        "schema": VERIFY_SCHEMA,
        "status": global_status,
        "production_eligible": False,
        "scope": ASSESSMENT_SCOPE,
        "selected_point_count": len(selected),
        "relation_count": len(relations),
        "prime": prime,
        "map_class": map_data["class"],
        "checks": [
            "curve_equation_identities",
            "inverse_projective_compositions",
            "origin_translation",
            "selected_point_images",
            "coefficient_unit_and_selected_point_reduction_commutation",
            "source_subgroup_replay",
            "relation_replay",
        ],
        "open_obligations": [
            "pinned general cubic map constructor is unavailable",
            "exceptional-locus completeness is not certified for general birational maps",
            "natural r=7..9 rows are not integrated into runner or freeze",
            "licensed Magma rank cross-check is unavailable",
        ],
        "certificate_sha256": certificate["certificate_sha256"],
        "verifier": {
            "implementation_sha256": file_sha256(Path(__file__)),
            "sympy_version": sp.__version__,
        },
    }
    result["verification_sha256"] = object_sha256(result)
    return result


def construction_probe() -> dict:
    """Report constructor availability without treating coefficients as a map."""
    sage = shutil.which("sage")
    magma = shutil.which("magma")
    gp = shutil.which("gp")
    return {
        "schema": "xedni.cubic-jacobian-construction-probe/v1",
        "sage": {"available": sage is not None, "path": sage},
        "magma": {"available": magma is not None, "path": magma},
        "pari": {
            "available": gp is not None,
            "path": gp,
            "ellfromeqn_scope": "Jacobian coefficients only; no selected-point map",
        },
        "verifier": {
            "implementation_sha256": file_sha256(Path(__file__)),
            "sympy_version": sp.__version__,
        },
        "status": "AVAILABLE" if sage or magma else "BLOCKED_NO_EXPLICIT_CONSTRUCTOR",
    }


def _seal(value: dict, field: str) -> dict:
    result = dict(value)
    result[field] = object_sha256(value)
    return result


def _model_json(variables: tuple[str, str, str], equation: dict) -> dict:
    return _seal({"variables": list(variables), "equation": equation}, "model_sha256")


def _point_record(
    point_id: str,
    cubic_point: PointQ,
    forward_point: PointQ,
    translated_point: PointQ,
    multiplier: int,
) -> dict:
    return _seal(
        {
            "point_id": point_id,
            "cubic_coordinates": _point_json(_projectivize(cubic_point)),
            "forward_coordinates": _point_json(_projectivize(forward_point)),
            "translated_coordinates": _point_json(_projectivize(translated_point)),
            "source_multiplier": multiplier,
        },
        "point_sha256",
    )


def build_identity_control(r: int = 9, prime: int = 101) -> dict:
    """Build a non-natural control with a nonidentity chord origin.

    The plane cubic is already in projective short-Weierstrass form, so the
    birational curve map is the identity.  The chosen group origin is P=(0,1),
    hence the actual group correspondence is psi(Q)=Q-P.  Selected points are
    [2]P through [r+1]P, which supplies the exact source replay expected by the
    natural r=7..9 interface without claiming a general constructor.
    """
    if r not in (7, 8, 9) or prime != 101:
        raise CubicMapError("identity control is frozen at r=7..9 and p=101")
    a, b = -1, 1
    generator_q: PointQ = (Fraction(0), Fraction(1))
    generator_p: PointP = (0, 1)
    order = 1
    while _mul_p(order, generator_p, a, prime) is not None:
        order += 1
        if order > 2 * prime + 10:
            raise CubicMapError("control generator order search failed")
    cubic_equation = _poly_json(
        {
            (3, 0, 0): -1,
            (1, 0, 2): 1,
            (0, 2, 1): 1,
            (0, 0, 3): -1,
        },
        ("X", "Y", "Z"),
    )
    jacobian_equation = _poly_json(
        {
            (3, 0, 0): -1,
            (1, 0, 2): 1,
            (0, 2, 1): 1,
            (0, 0, 3): -1,
        },
        ("x", "y", "z"),
    )
    coordinate_x = _poly_json({(1, 0, 0): 1}, ("X", "Y", "Z"))
    coordinate_y = _poly_json({(0, 1, 0): 1}, ("X", "Y", "Z"))
    coordinate_z = _poly_json({(0, 0, 1): 1}, ("X", "Y", "Z"))
    inverse_x = _poly_json({(1, 0, 0): 1}, ("x", "y", "z"))
    inverse_y = _poly_json({(0, 1, 0): 1}, ("x", "y", "z"))
    inverse_z = _poly_json({(0, 0, 1): 1}, ("x", "y", "z"))
    one_source = _poly_json({(0, 0, 0): 1}, ("X", "Y", "Z"))
    one_destination = _poly_json({(0, 0, 0): 1}, ("x", "y", "z"))
    map_payload = {
        "map_class": "projective_linear_isomorphism",
        "forward": [coordinate_x, coordinate_y, coordinate_z],
        "inverse": [inverse_x, inverse_y, inverse_z],
        "forward_multiplier": one_source,
        "inverse_multiplier": one_destination,
        "exceptional_cubic_points": [],
        "exceptional_jacobian_points": [],
    }
    map_record = _seal(map_payload, "map_sha256")
    origin = generator_q
    origin_record = _point_record("origin", origin, origin, None, 1)
    selected = []
    multipliers = list(range(2, r + 2))
    for index, multiplier in enumerate(multipliers):
        point = _mul_q(multiplier, generator_q, a)
        translated = _add_q(point, _neg_q(origin), a)
        selected.append(_point_record(f"P{index}", point, point, translated, multiplier))
    source_record = _seal(
        {
            "prime": prime,
            "a": a,
            "b": b,
            "generator": [0, 1],
            "generator_order": order,
            "origin_multiplier": 1,
            "selected_multipliers": multipliers,
        },
        "source_sha256",
    )
    coefficients = [0] * r
    coefficients[0], coefficients[1] = 2, -1
    relation = _seal({"coefficients": coefficients}, "relation_sha256")
    discriminant = -16 * (4 * a**3 + 27 * b**2)
    backend_identity = {
        "backend": "explicit-control",
        "version": "1",
        "identity": "projective-short-weierstrass-identity",
    }
    construction = _seal(
        {
            **backend_identity,
            "available": True,
            "backend_sha256": object_sha256(backend_identity),
            "status": "SUPPLIED_EXPLICIT_MAP",
            "reason": "non-natural verifier control; not a general constructor",
        },
        "construction_sha256",
    )
    payload = {
        "schema": SCHEMA,
        "scope": ASSESSMENT_SCOPE,
        "construction": construction,
        "field": {"name": "Q", "characteristic": 0},
        "prime": prime,
        "cubic": _model_json(("X", "Y", "Z"), cubic_equation),
        "jacobian": _seal(
            {
                "variables": ["x", "y", "z"],
                "equation": jacobian_equation,
                "a": a,
                "b": b,
                "discriminant": discriminant,
            },
            "model_sha256",
        ),
        "map": map_record,
        "origin": origin_record,
        "selected_points": selected,
        "source_subgroup": source_record,
        "relations": [relation],
    }
    return _seal(payload, "certificate_sha256")


if __name__ == "__main__":
    print(json.dumps(verify_certificate(build_identity_control()), indent=2, sort_keys=True))
