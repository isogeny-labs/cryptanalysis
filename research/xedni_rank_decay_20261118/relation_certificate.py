#!/usr/bin/env python3
"""Exact certificates for *supplied* Xedni selected-point relations.

This module is deliberately a verifier, not a relation finder.  It accepts an
integer vector supplied by a caller, replays it with exact rational arithmetic
on the generalized Weierstrass lift, reduces it to the frozen source subgroup,
and checks target-scalar recovery.  It never emits a natural rank row.

The bounded PARI-height/LLL proposer lives in the deliberately separate
``relation_pari`` module.  This verifier does not import or invoke it: a caller
must pass only the proposed integer vectors across that boundary.  Every such
vector must pass ``build_relation_certificate`` before it is counted as a
relation.  Exhausting or rejecting supplied candidates does not certify
selected-point independence; a no-hit result remains ``UNKNOWN``.
"""

from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import re
import sys
from typing import Any, Iterable


HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import field
import lift_builder


SCHEMA = "xedni.relation-certificate/v1"
STATUS = "exact_supplied_relation_replay"
SCOPE = "verifier_only_no_relation_search_no_natural_rank_row"
MIN_R = 2
MAX_R = 6
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
EXPECTED_LIFT_CERTIFICATE = {
    "source_replay": True,
    "local_replay": True,
    "exact_incidence": True,
    "coefficient_congruence": True,
    "all_points_integral_and_on_curve": True,
    "nonsingular_over_q": True,
    "good_reduction_at_all_moduli": True,
    "all_reductions_replayed": True,
}

FINDER_STATUS = {
    "implemented": False,
    "scope": "this_exact_verifier_module_only",
    "external_backend": "relation_pari.py",
    "method": "caller-supplied integer vectors only",
    "reason": (
        "heuristic proposal is intentionally separated from exact certificate "
        "replay; call relation_pari.py with its scalar-free strict input"
    ),
    "acceptance_rule": "a proposal counts only after exact certificate replay",
}


class RelationCertificateError(RuntimeError):
    """A supplied relation or one of its bound records failed closed."""

    def __init__(self, code: str, message: str, details: dict | None = None):
        super().__init__(message)
        self.code = code
        self.details = {} if details is None else details


PointQ = tuple[Fraction, Fraction] | None


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def object_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def _plain_integer(value: Any, context: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise RelationCertificateError("invalid_integer", f"{context} must be an integer")
    return value


def _integer_vector(value: Any, length: int, context: str) -> list[int]:
    if not isinstance(value, (list, tuple)) or len(value) != length:
        raise RelationCertificateError(
            "invalid_relation", f"{context} must have exactly {length} entries"
        )
    return [_plain_integer(entry, f"{context}[{index}]") for index, entry in enumerate(value)]


def _ainvs(value: Any) -> tuple[Fraction, Fraction, Fraction, Fraction, Fraction]:
    raw = _integer_vector(value, 5, "lift.ainvs")
    return tuple(Fraction(entry) for entry in raw)  # type: ignore[return-value]


def _points(value: Any, r: int) -> list[PointQ]:
    if not isinstance(value, list) or len(value) != r:
        raise RelationCertificateError("invalid_points", "lift.points has the wrong length")
    points: list[PointQ] = []
    for index, raw in enumerate(value):
        if not isinstance(raw, list) or len(raw) != 2:
            raise RelationCertificateError(
                "invalid_point", f"lift.points[{index}] is not an affine pair"
            )
        x = _plain_integer(raw[0], f"lift.points[{index}][0]")
        y = _plain_integer(raw[1], f"lift.points[{index}][1]")
        points.append((Fraction(x), Fraction(y)))
    return points


def weierstrass_discriminant(ainvs: Iterable[int | Fraction]) -> int | Fraction:
    a1, a2, a3, a4, a6 = tuple(ainvs)
    b2 = a1 * a1 + 4 * a2
    b4 = 2 * a4 + a1 * a3
    b6 = a3 * a3 + 4 * a6
    b8 = a1 * a1 * a6 + 4 * a2 * a6 - a1 * a3 * a4 + a2 * a3 * a3 - a4 * a4
    return -b2 * b2 * b8 - 8 * b4**3 - 27 * b6 * b6 + 9 * b2 * b4 * b6


def on_curve(point: PointQ, ainvs: tuple[Fraction, ...]) -> bool:
    if point is None:
        return True
    x, y = point
    a1, a2, a3, a4, a6 = ainvs
    return y * y + a1 * x * y + a3 * y == x**3 + a2 * x * x + a4 * x + a6


def point_neg(point: PointQ, ainvs: tuple[Fraction, ...]) -> PointQ:
    if point is None:
        return None
    a1, _, a3, _, _ = ainvs
    x, y = point
    return x, -y - a1 * x - a3


def point_add(left: PointQ, right: PointQ, ainvs: tuple[Fraction, ...]) -> PointQ:
    """Exact affine group law for a nonsingular generalized Weierstrass curve."""
    if left is None:
        return right
    if right is None:
        return left
    x1, y1 = left
    x2, y2 = right
    a1, a2, a3, a4, _ = ainvs
    if x1 == x2:
        if y1 + y2 + a1 * x2 + a3 == 0:
            return None
        denominator = 2 * y1 + a1 * x1 + a3
        if denominator == 0:
            raise RelationCertificateError(
                "group_law", "doubling denominator vanished outside the inverse case"
            )
        slope = (3 * x1 * x1 + 2 * a2 * x1 + a4 - a1 * y1) / denominator
    else:
        slope = (y2 - y1) / (x2 - x1)
    intercept = y1 - slope * x1
    x3 = slope * slope + a1 * slope - a2 - x1 - x2
    y3 = -(slope + a1) * x3 - intercept - a3
    result = x3, y3
    if not on_curve(result, ainvs):
        raise RelationCertificateError("group_law", "exact addition left the curve")
    return result


def point_mul(scalar: int, point: PointQ, ainvs: tuple[Fraction, ...]) -> PointQ:
    scalar = _plain_integer(scalar, "scalar")
    if scalar < 0:
        return point_mul(-scalar, point_neg(point, ainvs), ainvs)
    total = None
    addend = point
    while scalar:
        if scalar & 1:
            total = point_add(total, addend, ainvs)
        addend = point_add(addend, addend, ainvs)
        scalar >>= 1
    return total


def relation_sum(
    coefficients: Iterable[int], points: Iterable[PointQ], ainvs: tuple[Fraction, ...]
) -> PointQ:
    coefficient_list = list(coefficients)
    point_list = list(points)
    if len(coefficient_list) != len(point_list):
        raise RelationCertificateError(
            "relation_length", "coefficient and point counts differ"
        )
    total = None
    for coefficient, point in zip(coefficient_list, point_list):
        total = point_add(total, point_mul(coefficient, point, ainvs), ainvs)
    return total


def _canonical_primitive(coefficients: list[int]) -> tuple[int, list[int]]:
    divisor = 0
    for coefficient in coefficients:
        divisor = math.gcd(divisor, abs(coefficient))
    if divisor == 0:
        return 0, list(coefficients)
    primitive = [coefficient // divisor for coefficient in coefficients]
    first = next(coefficient for coefficient in primitive if coefficient)
    if first < 0:
        primitive = [-coefficient for coefficient in primitive]
    return divisor, primitive


def _relation_class(
    supplied: list[int], primitive: list[int], primitive_replays: bool
) -> tuple[str, str]:
    basis = primitive if primitive_replays else supplied
    nonzero = [coefficient for coefficient in basis if coefficient]
    support = len(nonzero)
    l1_norm = sum(abs(coefficient) for coefficient in nonzero)
    if not primitive_replays:
        return "torsion", "division by the coefficient gcd leaves a torsion obstruction"
    if support == 1:
        return "torsion", "the relation is supported on one selected point"
    if l1_norm <= 3:
        return "line", "the primitive signed multiset has at most three points"
    if sorted(nonzero) == [-1, -1, 1, 1]:
        return "parallelogram", "the primitive vector is a two-by-two cancellation"
    return "nontrivial", "not unary torsion, a degree-three line relation, or a parallelogram"


def finder_status() -> dict:
    """Return the frozen absence record for a heuristic proposal backend."""
    return json.loads(json.dumps(FINDER_STATUS))


def propose_relations(*_args: Any, **_kwargs: Any) -> list[list[int]]:
    """Fail closed: no heuristic finder is implemented or silently simulated."""
    raise RelationCertificateError("finder_unavailable", FINDER_STATUS["reason"])


def _source_context(lift: dict, source: dict, r: int) -> dict:
    p = _plain_integer(source.get("p"), "source.p")
    curve = source.get("curve")
    if not isinstance(curve, dict):
        raise RelationCertificateError("source_curve", "source.curve is missing")
    a = _plain_integer(curve.get("a"), "source.curve.a")
    b = _plain_integer(curve.get("b"), "source.curve.b")
    q = _plain_integer(source.get("source_subgroup_order"), "source.source_subgroup_order")
    base_raw = source.get("base_point")
    if not isinstance(base_raw, list) or len(base_raw) != 2:
        raise RelationCertificateError("source_base", "source.base_point is malformed")
    base = (
        _plain_integer(base_raw[0], "source.base_point[0]"),
        _plain_integer(base_raw[1], "source.base_point[1]"),
    )
    indices = lift.get("selected_indices")
    if (
        not isinstance(indices, list)
        or len(indices) != r
        or any(isinstance(index, bool) or not isinstance(index, int) for index in indices)
        or len(set(indices)) != r
    ):
        raise RelationCertificateError("source_indices", "lift selected indices are malformed")
    raw_scalars = source.get("ordered_scalars")
    raw_points = source.get("ordered_points")
    if not isinstance(raw_scalars, list) or not isinstance(raw_points, list):
        raise RelationCertificateError("source_tuple", "source ordered tuple is missing")
    try:
        selected_scalars = [
            _plain_integer(raw_scalars[index], f"source.ordered_scalars[{index}]")
            for index in indices
        ]
        selected_points = [
            (
                _plain_integer(raw_points[index][0], f"source.ordered_points[{index}][0]"),
                _plain_integer(raw_points[index][1], f"source.ordered_points[{index}][1]"),
            )
            for index in indices
        ]
    except (IndexError, TypeError) as error:
        raise RelationCertificateError(
            "source_tuple", "source selected tuple is malformed"
        ) from error
    if lift.get("selected_source_scalars_for_replay_only") != selected_scalars:
        raise RelationCertificateError("source_scalars", "lift/source selected scalars disagree")
    target_source_index = lift.get("target_index")
    if target_source_index not in indices:
        raise RelationCertificateError("target_index", "target is absent from selected indices")
    target_position = indices.index(target_source_index)
    if target_position != r - 1:
        raise RelationCertificateError(
            "target_position", "frozen selected target must be the final tuple position"
        )
    for index, (scalar, point) in enumerate(zip(selected_scalars, selected_points)):
        if not field.on_curve(point, a, b, p):
            raise RelationCertificateError(
                "source_point", f"selected source point {index} is off curve"
            )
        if field.point_mul(scalar, base, a, p) != point:
            raise RelationCertificateError(
                "source_scalar", f"selected source scalar {index} does not replay"
            )
    return {
        "p": p,
        "a": a,
        "b": b,
        "q": q,
        "base": base,
        "indices": indices,
        "scalars": selected_scalars,
        "points": selected_points,
        "target_source_index": target_source_index,
        "target_position": target_position,
    }


def _source_relation_sum(
    coefficients: list[int], points: list[tuple[int, int]], a: int, p: int
) -> tuple[int, int] | None:
    total = None
    for coefficient, point in zip(coefficients, points):
        term = field.point_mul(coefficient, point, a, p)
        total = field.point_add(total, term, a, p)
    return total


def _certificate_without_digest(
    lift: dict,
    source: dict,
    local_config: dict | None,
    coefficients: list[int],
) -> dict:
    lift_errors = lift_builder.verify_lift(lift, source, local_config)
    if lift_errors:
        raise RelationCertificateError(
            "lift_certificate", "lift replay failed", {"errors": lift_errors}
        )
    if lift.get("certificate") != EXPECTED_LIFT_CERTIFICATE:
        raise RelationCertificateError(
            "lift_certificate_shape",
            "lift certificate flags are not the exact frozen set",
        )
    r = lift.get("r")
    if isinstance(r, bool) or not isinstance(r, int) or not MIN_R <= r <= MAX_R:
        raise RelationCertificateError("unsupported_r", "only r=2..6 is supported")
    coefficients = _integer_vector(coefficients, r, "relation")
    if not any(coefficients):
        raise RelationCertificateError("zero_relation", "the zero vector is not a relation event")

    ainvs = _ainvs(lift.get("ainvs"))
    if weierstrass_discriminant(ainvs) == 0:
        raise RelationCertificateError("singular_curve", "lift curve is singular")
    points = _points(lift.get("points"), r)
    if any(not on_curve(point, ainvs) for point in points):
        raise RelationCertificateError("rational_point", "a selected lift point is off curve")
    rational_total = relation_sum(coefficients, points, ainvs)
    if rational_total is not None:
        raise RelationCertificateError(
            "not_a_relation",
            "the supplied vector does not sum to the identity over Q",
        )

    coefficient_gcd, primitive = _canonical_primitive(coefficients)
    primitive_total = relation_sum(primitive, points, ainvs)
    primitive_replays = primitive_total is None
    certified_coefficients = primitive if primitive_replays else coefficients
    relation_class, class_reason = _relation_class(
        coefficients, primitive, primitive_replays
    )
    supplied_support_size = sum(coefficient != 0 for coefficient in coefficients)
    supplied_l1_norm = sum(abs(coefficient) for coefficient in coefficients)
    support_size = sum(coefficient != 0 for coefficient in certified_coefficients)
    l1_norm = sum(abs(coefficient) for coefficient in certified_coefficients)

    source_context = _source_context(lift, source, r)
    p = source_context["p"]
    q = source_context["q"]
    scalars = source_context["scalars"]
    source_points = source_context["points"]
    supplied_scalar_terms = [
        (coefficient * scalar) % q
        for coefficient, scalar in zip(coefficients, scalars)
    ]
    supplied_source_scalar_residue = sum(supplied_scalar_terms) % q
    supplied_source_group_total = _source_relation_sum(
        coefficients, source_points, source_context["a"], p
    )
    if supplied_source_scalar_residue != 0 or supplied_source_group_total is not None:
        raise RelationCertificateError(
            "source_reduction",
            "the supplied rational relation did not replay in the bound source subgroup",
            {
                "source_scalar_residue": supplied_source_scalar_residue,
                "source_group_total": supplied_source_group_total,
            },
        )
    scalar_terms = [
        (coefficient * scalar) % q
        for coefficient, scalar in zip(certified_coefficients, scalars)
    ]
    source_scalar_residue = sum(scalar_terms) % q
    source_group_total = _source_relation_sum(
        certified_coefficients, source_points, source_context["a"], p
    )
    if source_scalar_residue != 0 or source_group_total is not None:
        raise RelationCertificateError(
            "canonical_source_reduction",
            "the certified canonical relation did not replay in the source subgroup",
        )

    target_position = source_context["target_position"]
    target_coefficient = certified_coefficients[target_position] % q
    coefficient_gcd_q = math.gcd(target_coefficient, q)
    invertible = coefficient_gcd_q == 1
    known_sum = sum(
        coefficient * scalar
        for index, (coefficient, scalar) in enumerate(
            zip(certified_coefficients, scalars)
        )
        if index != target_position
    ) % q
    expected_scalar = scalars[target_position] % q
    if invertible:
        recovered_scalar = (-known_sum * pow(target_coefficient, -1, q)) % q
        scalar_matches = recovered_scalar == expected_scalar
        point_matches = (
            field.point_mul(recovered_scalar, source_context["base"], source_context["a"], p)
            == source_points[target_position]
        )
        if not scalar_matches or not point_matches:
            raise RelationCertificateError(
                "recovery_replay", "invertible target recovery did not replay"
            )
    else:
        recovered_scalar = None
        scalar_matches = None
        point_matches = None

    relation_binding = {
        "row_id": lift.get("row_id"),
        "coefficients": coefficients,
    }
    model_hash = lift.get("hashes", {}).get("model_sha256")
    if not isinstance(model_hash, str) or HEX64.fullmatch(model_hash) is None:
        raise RelationCertificateError("model_hash", "lift model hash is malformed")
    certificate = {
        "schema": SCHEMA,
        "status": STATUS,
        "scope": SCOPE,
        "row_id": lift.get("row_id"),
        "r": r,
        "input_binding": {
            "lift_record_sha256": object_sha256(lift),
            "source_record_sha256": object_sha256(source),
            "local_record_sha256": object_sha256(local_config),
            "lift_model_sha256": model_hash,
            "relation_input_sha256": object_sha256(relation_binding),
        },
        "relation": {
            "supplied_coefficients": coefficients,
            "coefficient_gcd": coefficient_gcd,
            "supplied_primitive": coefficient_gcd == 1,
            "canonical_primitive_coefficients": primitive,
            "primitive_replays_exactly": primitive_replays,
            "certified_coefficients": certified_coefficients,
            "certified_primitive": primitive_replays,
            "nonzero": True,
            "supplied_support_size": supplied_support_size,
            "supplied_l1_norm": supplied_l1_norm,
            "support_size": support_size,
            "l1_norm": l1_norm,
        },
        "rational_replay": {
            "field": "Q",
            "arithmetic": "fractions.Fraction",
            "curve_discriminant_nonzero": True,
            "all_selected_points_on_curve": True,
            "supplied_sum_is_identity": True,
            "canonical_primitive_sum_is_identity": primitive_replays,
            "certified_sum_is_identity": True,
            "final_sum": None,
        },
        "classification": {
            "relation_class": relation_class,
            "reason": class_reason,
            "nontrivial": relation_class == "nontrivial",
            "qualifies_as_primitive_nontrivial": (
                primitive_replays and relation_class == "nontrivial"
            ),
            "eligible_for_nontrivial_endpoint": (
                primitive_replays and relation_class == "nontrivial"
            ),
        },
        "source_reduction": {
            "field_prime": p,
            "subgroup_order": q,
            "selected_source_indices": source_context["indices"],
            "selected_source_scalars": scalars,
            "supplied_coefficient_residues_mod_q": [
                coefficient % q for coefficient in coefficients
            ],
            "supplied_scalar_terms_mod_q": supplied_scalar_terms,
            "supplied_scalar_relation_residue": supplied_source_scalar_residue,
            "certified_coefficient_residues_mod_q": [
                coefficient % q for coefficient in certified_coefficients
            ],
            "scalar_terms_mod_q": scalar_terms,
            "scalar_relation_residue": source_scalar_residue,
            "finite_field_group_sum_is_identity": True,
            "finite_field_group_sum": None,
        },
        "recovery": {
            "target_selected_position": target_position,
            "target_source_index": source_context["target_source_index"],
            "target_coefficient_mod_q": target_coefficient,
            "target_coefficient_gcd_q": coefficient_gcd_q,
            "target_coefficient_invertible": invertible,
            "known_sum_mod_q": known_sum,
            "induced_target_equation_residue": (
                known_sum + target_coefficient * expected_scalar
            )
            % q,
            "recovered_scalar": recovered_scalar,
            "expected_scalar_for_replay_only": expected_scalar,
            "scalar_matches": scalar_matches,
            "point_matches": point_matches,
            "recovered_scalar_replay": bool(scalar_matches and point_matches),
        },
        "outcome": {
            "selected_dependence": "CERT_YES",
            "relation_class": relation_class,
            "rational_relation_replay": "CERT_YES",
            "relation_certificate_sha256": None,
            "relation_proof_verified": True,
            "target_coefficient_invertible": "CERT_YES" if invertible else "CERT_NO",
            "scalar_replay": "CERT_YES" if invertible else "CERT_NO",
            "source_replay_sha256": None,
            "source_replay_proof_verified": bool(
                invertible and scalar_matches and point_matches
            ),
            "useful_recovery": (
                "CERT_YES"
                if invertible and scalar_matches and point_matches
                else "CERT_NO"
            ),
        },
        "finder": {
            "mode": "caller_supplied_vector",
            "finder_invoked": False,
            "heuristic_proposals": 0,
            "exact_replay_required_for_counting": True,
            "finder_status": finder_status(),
        },
        "certificate_flags": {
            "lift_hashes_and_certificate_replayed": True,
            "exact_rational_group_law_replayed": True,
            "primitive_canonicalization_replayed": True,
            "nonzero_relation": True,
            "source_reduction_replayed": True,
            "target_recovery_logic_replayed": True,
        },
    }
    certificate["outcome"]["relation_certificate_sha256"] = object_sha256(
        {
            "input_binding": certificate["input_binding"],
            "relation": certificate["relation"],
            "rational_replay": certificate["rational_replay"],
            "classification": certificate["classification"],
        }
    )
    certificate["outcome"]["source_replay_sha256"] = object_sha256(
        {
            "input_binding": certificate["input_binding"],
            "source_reduction": certificate["source_reduction"],
            "recovery": certificate["recovery"],
        }
    )
    return certificate


def build_relation_certificate(
    lift: dict,
    source: dict,
    coefficients: Iterable[int],
    local_config: dict | None = None,
) -> dict:
    """Certify one caller-supplied vector; never search for an alternative."""
    if not isinstance(lift, dict) or not isinstance(source, dict):
        raise RelationCertificateError("record_type", "lift and source must be objects")
    r = lift.get("r")
    if isinstance(r, bool) or not isinstance(r, int):
        raise RelationCertificateError("unsupported_r", "lift.r is malformed")
    vector = _integer_vector(list(coefficients), r, "relation")
    certificate = _certificate_without_digest(lift, source, local_config, vector)
    certificate["certificate_sha256"] = object_sha256(certificate)
    return certificate


def verify_relation_certificate(
    certificate: Any,
    lift: dict,
    source: dict,
    local_config: dict | None = None,
) -> list[str]:
    """Strictly rebuild a certificate; malformed or extra data fail closed."""
    if not isinstance(certificate, dict):
        return ["certificate_type"]
    if certificate.get("schema") != SCHEMA:
        return ["schema"]
    supplied_digest = certificate.get("certificate_sha256")
    if not isinstance(supplied_digest, str) or HEX64.fullmatch(supplied_digest) is None:
        return ["certificate_sha256"]
    without_digest = dict(certificate)
    without_digest.pop("certificate_sha256", None)
    errors: list[str] = []
    if object_sha256(without_digest) != supplied_digest:
        errors.append("certificate_sha256")
    relation = certificate.get("relation")
    coefficients = relation.get("supplied_coefficients") if isinstance(relation, dict) else None
    try:
        r = lift.get("r")
        if isinstance(r, bool) or not isinstance(r, int):
            raise RelationCertificateError("unsupported_r", "lift.r is malformed")
        vector = _integer_vector(coefficients, r, "certificate.relation")
        expected = _certificate_without_digest(lift, source, local_config, vector)
        expected["certificate_sha256"] = object_sha256(expected)
    except RelationCertificateError as error:
        errors.append(f"replay:{error.code}")
        return errors
    except Exception as error:
        errors.append(f"verification_exception:{type(error).__name__}")
        return errors
    if certificate != expected:
        errors.append("certificate_mismatch")
    return errors


def replay_supplied_candidates(
    lift: dict,
    source: dict,
    candidates: Iterable[Iterable[int]],
    local_config: dict | None = None,
) -> dict:
    """Replay external proposals; only exact certificates enter ``accepted``."""
    retained = []
    accepted = []
    for proposal_index, candidate in enumerate(candidates):
        vector = None
        try:
            vector = list(candidate)
            certificate = build_relation_certificate(
                lift, source, vector, local_config
            )
        except RelationCertificateError as error:
            retained.append(
                {
                    "proposal_index": proposal_index,
                    "candidate": vector,
                    "accepted": False,
                    "error_code": error.code,
                    "error": str(error),
                }
            )
            continue
        retained.append(
            {
                "proposal_index": proposal_index,
                "candidate": vector,
                "accepted": True,
                "certificate_sha256": certificate["certificate_sha256"],
            }
        )
        accepted.append(certificate)
    return {
        "schema": "xedni.relation-proposal-replay/v1",
        "status": "exact_replay_complete",
        "proposal_count": len(retained),
        "exact_replay_count": len(accepted),
        "counted_relation_count": len(accepted),
        "absence_certificate": False,
        "selected_dependence_if_no_exact_replay": "UNKNOWN",
        "proposals": retained,
        "accepted": accepted,
    }


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    status = subparsers.add_parser("finder-status")
    status.set_defaults(command="finder-status")
    certify = subparsers.add_parser("certify")
    certify.add_argument("--lift", type=Path, required=True)
    certify.add_argument("--source", type=Path, required=True)
    certify.add_argument("--local", type=Path)
    certify.add_argument("--relation", required=True, help="comma-separated integers")
    certify.add_argument("--output", type=Path)
    check = subparsers.add_parser("check")
    check.add_argument("--certificate", type=Path, required=True)
    check.add_argument("--lift", type=Path, required=True)
    check.add_argument("--source", type=Path, required=True)
    check.add_argument("--local", type=Path)
    args = parser.parse_args()

    if args.command == "finder-status":
        print(json.dumps(finder_status(), indent=2, sort_keys=True))
        return
    lift = _read_json(args.lift)
    source = _read_json(args.source)
    local = None if args.local is None else _read_json(args.local)
    if args.command == "certify":
        try:
            relation = [int(value) for value in args.relation.split(",")]
        except ValueError as error:
            raise SystemExit(f"invalid --relation: {error}") from error
        certificate = build_relation_certificate(lift, source, relation, local)
        rendered = json.dumps(certificate, indent=2, sort_keys=True) + "\n"
        if args.output is not None:
            args.output.write_text(rendered)
        print(rendered, end="")
        return
    certificate = _read_json(args.certificate)
    errors = verify_relation_certificate(certificate, lift, source, local)
    print(json.dumps({"status": "PASS" if not errors else "FAIL", "errors": errors}))
    if errors:
        raise SystemExit(1)


__all__ = [
    "FINDER_STATUS",
    "MAX_R",
    "MIN_R",
    "RelationCertificateError",
    "SCHEMA",
    "SCOPE",
    "STATUS",
    "build_relation_certificate",
    "finder_status",
    "object_sha256",
    "on_curve",
    "point_add",
    "point_mul",
    "point_neg",
    "propose_relations",
    "relation_sum",
    "replay_supplied_candidates",
    "verify_relation_certificate",
    "weierstrass_discriminant",
]


if __name__ == "__main__":
    main()
