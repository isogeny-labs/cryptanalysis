#!/usr/bin/env python3
"""Exact selected-point relation lattices, conditional on a certified MW basis.

This module does not find a Mordell--Weil basis.  It consumes a full-basis
attestation and a caller callback only as mutation-control inputs.  Those
producer-selectable inputs are not an independent trust anchor, so current
outputs remain ``UNKNOWN`` and production-ineligible.  Conditional on the
attested free basis being full and saturated and its torsion decomposition
being complete, the module replays every selected-point decomposition with
exact rational elliptic-curve arithmetic and verifies the complete integer
kernel structure.

Completeness uses a Smith/Hermite-style primitivity criterion.  For free
coordinate matrix ``A``, torsion-coordinate matrix ``T`` and torsion invariant
matrix ``D``, relations are projections of the integer kernel of

    [ A   0 ]
    [ T  -D ].

The supplied extended kernel has the full rational kernel dimension and gcd 1
among its maximal minors.  It is therefore the primitive lattice
``Z^n intersect ker_Q(M)``, not a finite-index sublattice.  Projection to the
selected coefficients is injective because ``D`` is nonsingular.
"""

from __future__ import annotations

from fractions import Fraction
import hashlib
import itertools
import json
import math
import re
from typing import Any, Callable, Iterable

import relation_certificate as ec

try:
    import verifier_receipts
except ImportError:  # standalone controls remain fail-closed
    verifier_receipts = None


INPUT_SCHEMA = "xedni.relation-lattice-input/v1"
CERTIFICATE_SCHEMA = "xedni.relation-lattice-certificate/v1"
RECEIPT_SCHEMA = "xedni.full-mw-basis-receipt/v1"
VERIFIER_SCHEMA = "xedni.full-mw-basis-verifier-result/v1"
CONTROL_ASSESSMENT_SCHEMA = "xedni.full-mw-basis-control-assessment/v1"
PRODUCTION_READY = False
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
FRACTION_TEXT = re.compile(r"-?(?:0|[1-9][0-9]*)(?:/[1-9][0-9]*)?\Z")

# V1 is a bounded exact-arithmetic verifier scaffold, not a general-purpose
# Mordell--Weil engine.  These ceilings prevent caller-supplied JSON, rational
# coordinates, scalar decompositions, or matrices from turning conditional
# replay into unbounded CPU/memory work.  They are verifier limits rather than
# mathematical rank or height bounds; a production backend would need a new,
# independently reviewed schema before widening them.
MAX_INPUT_NODES = 4_096
MAX_INPUT_DEPTH = 12
MAX_CONTAINER_ITEMS = 128
MAX_INPUT_TEXT_CHARS = 131_072
MAX_JSON_STRING_CHARS = 4_096
# Large invalid torsion invariants still reach the constant-size Mazur
# allowlist (and are rejected there before factorization); all group scalars
# have much tighter semantic limits below.
MAX_JSON_INTEGER_BITS = 8_192
MAX_RATIONAL_BITS = 4_096
MAX_FREE_BASIS_RANK = 32
MAX_TORSION_FACTORS = 2
MAX_RELATION_BASIS_VECTORS = 9
MAX_MATRIX_ENTRIES = 512
MAX_GROUP_SCALAR_ABS = 128
MAX_SUBGROUP_ORDER_BITS = 64
MAZUR_TORSION_INVARIANTS = frozenset(
    [()] + [(order,) for order in range(2, 11)] + [(12,)]
    + [(2, order) for order in (2, 4, 6, 8)]
)


class RelationLatticeError(RuntimeError):
    """Fail-closed relation-lattice validation error."""

    def __init__(self, code: str, message: str, details: dict | None = None):
        super().__init__(message)
        self.code = code
        self.details = {} if details is None else details


def _preflight_json(value: Any, context: str) -> None:
    """Bound strict-JSON shape before hashing or exact group arithmetic."""
    state = {"nodes": 0, "text_chars": 0}
    active: set[int] = set()

    def fail(reason: str) -> None:
        raise RelationLatticeError(
            "complexity", f"{context} complexity exceeds {reason} limit"
        )

    def walk(item: Any, depth: int) -> None:
        state["nodes"] += 1
        if state["nodes"] > MAX_INPUT_NODES:
            fail("node")
        if depth > MAX_INPUT_DEPTH:
            fail("depth")
        if item is None or isinstance(item, bool):
            return
        if isinstance(item, int):
            if abs(item).bit_length() > MAX_JSON_INTEGER_BITS:
                fail("integer-bit")
            state["text_chars"] += max(
                1, (abs(item).bit_length() * 30103) // 100000 + 1
            )
        elif isinstance(item, str):
            if len(item) > MAX_JSON_STRING_CHARS:
                fail("string")
            state["text_chars"] += len(item)
        elif isinstance(item, (list, dict)):
            if len(item) > MAX_CONTAINER_ITEMS:
                fail("container")
            identity = id(item)
            if identity in active:
                raise RelationLatticeError(
                    "json", f"{context} contains a cyclic value"
                )
            active.add(identity)
            try:
                if isinstance(item, list):
                    for child in item:
                        walk(child, depth + 1)
                else:
                    for key, child in item.items():
                        if not isinstance(key, str):
                            raise RelationLatticeError(
                                "json", f"{context} object key is not a string"
                            )
                        walk(key, depth + 1)
                        walk(child, depth + 1)
            finally:
                active.remove(identity)
        else:
            raise RelationLatticeError(
                "json", f"{context} contains a non-JSON value"
            )
        if state["text_chars"] > MAX_INPUT_TEXT_CHARS:
            fail("text-budget")

    walk(value, 0)


def _preflight_input_complexity(value: Any) -> None:
    """Apply semantic size ceilings before validating points or receipts."""
    _preflight_json(value, "input")
    if not isinstance(value, dict):
        return

    free_basis = value.get("free_basis")
    if isinstance(free_basis, list) and len(free_basis) > MAX_FREE_BASIS_RANK:
        raise RelationLatticeError(
            "complexity", "free_basis exceeds verifier rank limit"
        )
    torsion = value.get("torsion")
    if isinstance(torsion, dict):
        for key in ("invariants", "generators"):
            entries = torsion.get(key)
            if isinstance(entries, list) and len(entries) > MAX_TORSION_FACTORS:
                raise RelationLatticeError(
                    "complexity", f"torsion.{key} exceeds factor limit"
                )
    relation_basis = value.get("relation_basis")
    if (
        isinstance(relation_basis, list)
        and len(relation_basis) > MAX_RELATION_BASIS_VECTORS
    ):
        raise RelationLatticeError(
            "complexity", "relation_basis exceeds vector-count limit"
        )

    matrix_entries = 0
    matrices: list[tuple[str, Any]] = [("relation_basis", relation_basis)]
    coordinates = value.get("coordinates")
    if isinstance(coordinates, dict):
        matrices.extend(
            (f"coordinates.{key}", coordinates.get(key))
            for key in ("free", "torsion")
        )
    for context, matrix in matrices:
        if not isinstance(matrix, list):
            continue
        for row in matrix:
            if not isinstance(row, list):
                continue
            matrix_entries += len(row)
            if matrix_entries > MAX_MATRIX_ENTRIES:
                raise RelationLatticeError(
                    "complexity", "matrix entry count exceeds verifier limit"
                )
            for entry in row:
                if (
                    isinstance(entry, int)
                    and not isinstance(entry, bool)
                    and abs(entry) > MAX_GROUP_SCALAR_ABS
                ):
                    raise RelationLatticeError(
                        "complexity",
                        f"{context} coefficient exceeds exact-replay scalar limit",
                    )

    subgroup_order = value.get("source_subgroup_order")
    if (
        isinstance(subgroup_order, int)
        and not isinstance(subgroup_order, bool)
        and abs(subgroup_order).bit_length() > MAX_SUBGROUP_ORDER_BITS
    ):
        raise RelationLatticeError(
            "complexity", "source_subgroup_order exceeds bit limit"
        )


def canonical_json(value: Any) -> str:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as error:
        raise RelationLatticeError("json", f"value is not strict JSON: {error}") from error


def object_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def _exact_keys(value: Any, expected: set[str], context: str) -> dict:
    if not isinstance(value, dict):
        raise RelationLatticeError("schema", f"{context} must be an object")
    actual = set(value)
    if actual != expected:
        raise RelationLatticeError(
            "schema",
            f"{context} keys differ",
            {"missing": sorted(expected - actual), "extra": sorted(actual - expected)},
        )
    return value


def _integer(value: Any, context: str, *, minimum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise RelationLatticeError("integer", f"{context} must be an integer")
    if minimum is not None and value < minimum:
        raise RelationLatticeError("integer", f"{context} must be at least {minimum}")
    return value


def _hash(value: Any, context: str) -> str:
    if not isinstance(value, str) or HEX64.fullmatch(value) is None:
        raise RelationLatticeError("hash", f"{context} must be lowercase SHA-256")
    return value


def _fraction(value: Any, context: str) -> Fraction:
    if isinstance(value, bool):
        raise RelationLatticeError("fraction", f"{context} is Boolean")
    if isinstance(value, int):
        return Fraction(value)
    if not isinstance(value, str) or FRACTION_TEXT.fullmatch(value) is None:
        raise RelationLatticeError("fraction", f"{context} is not canonical rational text")
    result = Fraction(value)
    if (
        abs(result.numerator).bit_length() > MAX_RATIONAL_BITS
        or result.denominator.bit_length() > MAX_RATIONAL_BITS
    ):
        raise RelationLatticeError(
            "complexity", f"{context} rational exceeds bit limit"
        )
    if str(result) != value:
        raise RelationLatticeError("fraction", f"{context} is not reduced canonical text")
    return result


def _caller_control_assessment(
    result: dict, subject_sha256: str, receipt: dict, trusted_identity: str
) -> dict:
    # A caller-supplied callback and caller-supplied identity pin are useful
    # mutation controls, but they are not an independent trust anchor.  In
    # particular, the producer can implement the callback, select its digest,
    # and make both Boolean fields true.  Never promote those assertions to a
    # production basis verdict.  A future production path must consume a
    # cryptographically verified receipt anchored in origin/main's PCC keyring.
    return {
        "schema": CONTROL_ASSESSMENT_SCHEMA,
        "standing": "CALLER_SUPPLIED_NOT_INDEPENDENT",
        "production_eligible": False,
        "subject_sha256": subject_sha256,
        "receipt_sha256": object_sha256(receipt),
        "caller_identity_pin_sha256": trusted_identity,
        "callback_assertion": result,
        "reason": (
            "callback booleans and a caller-chosen digest do not establish a "
            "repository-trusted signed full-basis verdict"
        ),
    }


def _point(value: Any, context: str) -> ec.PointQ:
    if value is None:
        return None
    if not isinstance(value, list) or len(value) != 2:
        raise RelationLatticeError("point", f"{context} must be null or an affine pair")
    return _fraction(value[0], f"{context}[0]"), _fraction(value[1], f"{context}[1]")


def _matrix(value: Any, rows: int, cols: int, context: str) -> list[list[int]]:
    if not isinstance(value, list) or len(value) != rows:
        raise RelationLatticeError("matrix", f"{context} must have {rows} rows")
    result = []
    for i, row in enumerate(value):
        if not isinstance(row, list) or len(row) != cols:
            raise RelationLatticeError("matrix", f"{context}[{i}] must have {cols} entries")
        parsed = [
            _integer(entry, f"{context}[{i}][{j}]")
            for j, entry in enumerate(row)
        ]
        if any(abs(entry) > MAX_GROUP_SCALAR_ABS for entry in parsed):
            raise RelationLatticeError(
                "complexity", f"{context}[{i}] exceeds exact-replay scalar limit"
            )
        result.append(parsed)
    return result


def _transpose(matrix: list[list[int]], columns: int | None = None) -> list[list[int]]:
    if not matrix:
        return [] if columns is None else [[] for _ in range(columns)]
    return [list(column) for column in zip(*matrix)]


def matrix_rank(matrix: list[list[int]]) -> int:
    """Exact rank over Q."""
    if not matrix:
        return 0
    width = len(matrix[0])
    if any(len(row) != width for row in matrix):
        raise RelationLatticeError("matrix", "ragged matrix")
    work = [[Fraction(value) for value in row] for row in matrix]
    pivot_row = 0
    for column in range(width):
        pivot = next((i for i in range(pivot_row, len(work)) if work[i][column]), None)
        if pivot is None:
            continue
        work[pivot_row], work[pivot] = work[pivot], work[pivot_row]
        scale = work[pivot_row][column]
        work[pivot_row] = [value / scale for value in work[pivot_row]]
        for i in range(len(work)):
            if i == pivot_row or work[i][column] == 0:
                continue
            factor = work[i][column]
            work[i] = [left - factor * right for left, right in zip(work[i], work[pivot_row])]
        pivot_row += 1
        if pivot_row == len(work):
            break
    return pivot_row


def independent_row_indices(matrix: list[list[int]], columns: int) -> list[int]:
    """Find one independent row set without combinatorial subset search."""
    chosen_rows: list[list[int]] = []
    chosen_indices: list[int] = []
    current_rank = 0
    for index, row in enumerate(matrix):
        candidate_rank = matrix_rank(chosen_rows + [row])
        if candidate_rank > current_rank:
            chosen_rows.append(row)
            chosen_indices.append(index)
            current_rank = candidate_rank
            if current_rank == columns:
                break
    return chosen_indices


def determinant(matrix: list[list[int]]) -> int:
    """Exact determinant using fraction-free Bareiss elimination."""
    size = len(matrix)
    if any(len(row) != size for row in matrix):
        raise RelationLatticeError("matrix", "determinant requires a square matrix")
    if size == 0:
        return 1
    work = [list(row) for row in matrix]
    sign = 1
    previous = 1
    for column in range(size - 1):
        pivot = next((i for i in range(column, size) if work[i][column]), None)
        if pivot is None:
            return 0
        if pivot != column:
            work[column], work[pivot] = work[pivot], work[column]
            sign = -sign
        pivot_value = work[column][column]
        for i in range(column + 1, size):
            for j in range(column + 1, size):
                numerator = work[i][j] * pivot_value - work[i][column] * work[column][j]
                if numerator % previous:
                    raise RelationLatticeError("determinant", "Bareiss division was not exact")
                work[i][j] = numerator // previous
        previous = pivot_value
        for i in range(column + 1, size):
            work[i][column] = 0
    return sign * work[-1][-1]


def maximal_minor_gcd(
    columns: list[list[int]], rank: int
) -> tuple[int, list[int] | None, int | None]:
    """GCD of maximal minors for a column matrix represented by rows."""
    if rank == 0:
        return 1, [], 1
    if not columns or any(len(row) != rank for row in columns):
        raise RelationLatticeError("kernel", "extended kernel has the wrong width")
    divisor = 0
    witness_rows = None
    witness_det = None
    for row_indices in itertools.combinations(range(len(columns)), rank):
        minor = [[columns[i][j] for j in range(rank)] for i in row_indices]
        value = determinant(minor)
        divisor = math.gcd(divisor, abs(value))
        if value and witness_rows is None:
            witness_rows = list(row_indices)
            witness_det = value
    return divisor, witness_rows, witness_det


def _prime_divisors(value: int) -> list[int]:
    divisors = []
    candidate = 2
    remaining = value
    while candidate * candidate <= remaining:
        if remaining % candidate == 0:
            divisors.append(candidate)
            while remaining % candidate == 0:
                remaining //= candidate
        candidate += 1 if candidate == 2 else 2
    if remaining > 1:
        divisors.append(remaining)
    return divisors


def _validate_rational_torsion_structure(invariants: list[int]) -> None:
    """Apply Mazur's classification before any order factorization.

    Trivial invariant factors are omitted by this schema, so the only valid
    invariant-factor tuples are (), (n) for n=2..10 or 12, and
    (2, 2m) for m=1..4.  Besides checking the mathematical precondition, this
    constant-size allowlist prevents adversarial large integers from reaching
    trial division or scalar multiplication.
    """
    if tuple(invariants) not in MAZUR_TORSION_INVARIANTS:
        raise RelationLatticeError(
            "torsion_structure",
            "torsion invariants are not allowed for an elliptic curve over Q by Mazur's theorem",
            {"allowed_invariant_factor_shapes": "(), (2..10), (12), (2,2|4|6|8)"},
        )


def _sum_points(
    coefficients: Iterable[int],
    points: Iterable[ec.PointQ],
    ainvs: tuple[Fraction, ...],
) -> ec.PointQ:
    return ec.relation_sum(coefficients, points, ainvs)


def _basis_subject(value: dict) -> dict:
    return {
        "curve": value["curve"],
        "free_basis": value["free_basis"],
        "torsion": value["torsion"],
    }


def _repository_trust_summary() -> dict:
    if verifier_receipts is None:
        return {
            "schema": "xedni.verifier-trust-summary/v1",
            "status": "NOT_COVERED",
            "production_ready": False,
            "reason": "verifier_receipts module is unavailable",
        }
    try:
        return verifier_receipts.repository_trust_summary()
    except Exception as error:  # trust discovery must fail closed
        return {
            "schema": "xedni.verifier-trust-summary/v1",
            "status": "NOT_COVERED",
            "production_ready": False,
            "reason": f"repository trust lookup failed: {type(error).__name__}",
        }


def _validate_basis_receipt(
    value: dict,
    receipt: Any,
    verifier: Callable[[dict, dict], dict] | None,
    trusted_verifier_sha256: str | None,
) -> dict:
    receipt = _exact_keys(
        receipt,
        {
            "schema",
            "status",
            "subject_sha256",
            "method",
            "proof_artifact_sha256",
        },
        "full_basis_receipt",
    )
    if receipt["schema"] != RECEIPT_SCHEMA or receipt["status"] != "CERTIFIED_FULL_SATURATED":
        raise RelationLatticeError("basis_receipt", "full saturated basis receipt is absent")
    subject_sha256 = object_sha256(_basis_subject(value))
    if _hash(receipt["subject_sha256"], "receipt.subject_sha256") != subject_sha256:
        raise RelationLatticeError("basis_receipt", "basis receipt subject does not match")
    if not isinstance(receipt["method"], str) or not receipt["method"].strip():
        raise RelationLatticeError("basis_receipt", "basis receipt method is empty")
    _hash(receipt["proof_artifact_sha256"], "receipt.proof_artifact_sha256")
    if verifier is None:
        raise RelationLatticeError(
            "basis_verifier_unavailable", "no full-basis verifier was supplied"
        )
    trusted_identity = _hash(trusted_verifier_sha256, "trusted_verifier_sha256")
    request = {
        "subject_sha256": subject_sha256,
        "receipt_sha256": object_sha256(receipt),
        "proof_artifact_sha256": receipt["proof_artifact_sha256"],
    }
    result = verifier(json.loads(canonical_json(receipt)), json.loads(canonical_json(request)))
    result = _exact_keys(
        result,
        {
            "schema",
            "status",
            "subject_sha256",
            "receipt_sha256",
            "verifier_identity_sha256",
            "signature_verified",
            "independent",
        },
        "basis_verifier_result",
    )
    if result["schema"] != VERIFIER_SCHEMA or result["status"] != "PASS":
        raise RelationLatticeError("basis_verifier", "full-basis verifier did not pass")
    if result["subject_sha256"] != subject_sha256:
        raise RelationLatticeError("basis_verifier", "verifier subject mismatch")
    if result["receipt_sha256"] != object_sha256(receipt):
        raise RelationLatticeError("basis_verifier", "verifier receipt mismatch")
    if _hash(result["verifier_identity_sha256"], "verifier identity") != trusted_identity:
        raise RelationLatticeError("basis_verifier", "verifier identity is not the trusted pin")
    if result["signature_verified"] is not True or result["independent"] is not True:
        raise RelationLatticeError("basis_verifier", "signed independent basis verdict required")
    return _caller_control_assessment(
        result, subject_sha256, receipt, trusted_identity
    )


def _validate_input(
    value: Any,
    basis_verifier: Callable[[dict, dict], dict] | None,
    trusted_verifier_sha256: str | None,
) -> dict:
    _preflight_input_complexity(value)
    value = _exact_keys(
        value,
        {
            "schema",
            "curve",
            "free_basis",
            "torsion",
            "selected_points",
            "coordinates",
            "relation_basis",
            "target_index",
            "source_subgroup_order",
            "full_basis_receipt",
        },
        "input",
    )
    if value["schema"] != INPUT_SCHEMA:
        raise RelationLatticeError("schema", "input schema mismatch")
    curve = _exact_keys(value["curve"], {"ainvs"}, "curve")
    if not isinstance(curve["ainvs"], list) or len(curve["ainvs"]) != 5:
        raise RelationLatticeError("curve", "curve.ainvs must have five entries")
    ainvs = tuple(_fraction(entry, f"curve.ainvs[{i}]") for i, entry in enumerate(curve["ainvs"]))
    if ec.weierstrass_discriminant(ainvs) == 0:
        raise RelationLatticeError("curve", "curve is singular")

    if not isinstance(value["free_basis"], list):
        raise RelationLatticeError("basis", "free_basis must be a list")
    if len(value["free_basis"]) > MAX_FREE_BASIS_RANK:
        raise RelationLatticeError(
            "complexity", "free_basis exceeds verifier rank limit"
        )
    free_basis = [
        _point(point, f"free_basis[{i}]")
        for i, point in enumerate(value["free_basis"])
    ]
    if any(point is None or not ec.on_curve(point, ainvs) for point in free_basis):
        raise RelationLatticeError("basis", "free basis contains identity or off-curve point")
    if len(set(free_basis)) != len(free_basis):
        raise RelationLatticeError("basis", "free basis points are duplicated")

    torsion = _exact_keys(value["torsion"], {"invariants", "generators"}, "torsion")
    if not isinstance(torsion["invariants"], list) or not isinstance(torsion["generators"], list):
        raise RelationLatticeError("torsion", "torsion fields must be lists")
    if (
        len(torsion["invariants"]) > MAX_TORSION_FACTORS
        or len(torsion["generators"]) > MAX_TORSION_FACTORS
    ):
        raise RelationLatticeError("complexity", "torsion exceeds factor limit")
    invariants = [
        _integer(entry, f"torsion.invariants[{i}]", minimum=2)
        for i, entry in enumerate(torsion["invariants"])
    ]
    _validate_rational_torsion_structure(invariants)
    if len(invariants) != len(torsion["generators"]):
        raise RelationLatticeError("torsion", "torsion invariant/generator counts differ")
    if any(right % left for left, right in zip(invariants, invariants[1:])):
        raise RelationLatticeError("torsion", "torsion invariants are not a divisibility chain")
    torsion_generators = [
        _point(point, f"torsion.generators[{i}]")
        for i, point in enumerate(torsion["generators"])
    ]
    for i, (order, point) in enumerate(zip(invariants, torsion_generators)):
        if point is None or not ec.on_curve(point, ainvs):
            raise RelationLatticeError("torsion", f"torsion generator {i} is invalid")
        if ec.point_mul(order, point, ainvs) is not None:
            raise RelationLatticeError("torsion", f"torsion generator {i} is not annihilated")
        for prime in _prime_divisors(order):
            if ec.point_mul(order // prime, point, ainvs) is None:
                raise RelationLatticeError("torsion", f"torsion generator {i} has smaller order")
    torsion_elements = {
        _sum_points(coefficients, torsion_generators, ainvs)
        for coefficients in itertools.product(*(range(order) for order in invariants))
    }
    if len(torsion_elements) != math.prod(invariants):
        raise RelationLatticeError(
            "torsion",
            "torsion generators do not realize the claimed direct-product structure",
        )

    if not isinstance(value["selected_points"], list) or not 2 <= len(
        value["selected_points"]
    ) <= 9:
        raise RelationLatticeError("selected", "selected_points must contain 2..9 points")
    selected = [
        _point(point, f"selected_points[{i}]")
        for i, point in enumerate(value["selected_points"])
    ]
    if any(point is None or not ec.on_curve(point, ainvs) for point in selected):
        raise RelationLatticeError("selected", "selected point is identity or off curve")
    r = len(selected)
    rank = len(free_basis)
    torsion_rank = len(invariants)
    coordinates = _exact_keys(value["coordinates"], {"free", "torsion"}, "coordinates")
    free_coordinates = _matrix(coordinates["free"], r, rank, "coordinates.free")
    torsion_coordinates = _matrix(coordinates["torsion"], r, torsion_rank, "coordinates.torsion")
    for i, row in enumerate(torsion_coordinates):
        for j, entry in enumerate(row):
            if not 0 <= entry < invariants[j]:
                raise RelationLatticeError(
                    "coordinates", f"torsion coordinate [{i}][{j}] is not reduced"
                )
    for i, point in enumerate(selected):
        terms = list(free_basis) + list(torsion_generators)
        coefficients = free_coordinates[i] + torsion_coordinates[i]
        if _sum_points(coefficients, terms, ainvs) != point:
            raise RelationLatticeError("decomposition", f"selected point {i} decomposition failed")

    if not isinstance(value["relation_basis"], list):
        raise RelationLatticeError("relation_basis", "relation_basis must be a list")
    if len(value["relation_basis"]) > MAX_RELATION_BASIS_VECTORS:
        raise RelationLatticeError(
            "complexity", "relation_basis exceeds vector-count limit"
        )
    relation_basis = _matrix(
        value["relation_basis"], len(value["relation_basis"]), r, "relation_basis"
    )
    if any(not any(vector) for vector in relation_basis):
        raise RelationLatticeError("relation_basis", "zero relation vector is not a basis vector")
    target_index = _integer(value["target_index"], "target_index", minimum=0)
    if target_index >= r:
        raise RelationLatticeError("target_index", "target_index is out of range")
    subgroup_order = _integer(
        value["source_subgroup_order"], "source_subgroup_order", minimum=2
    )
    if subgroup_order.bit_length() > MAX_SUBGROUP_ORDER_BITS:
        raise RelationLatticeError(
            "complexity", "source_subgroup_order exceeds bit limit"
        )
    verifier_result = _validate_basis_receipt(
        value, value["full_basis_receipt"], basis_verifier, trusted_verifier_sha256
    )
    return {
        "value": json.loads(canonical_json(value)),
        "ainvs": ainvs,
        "free_basis": free_basis,
        "torsion_generators": torsion_generators,
        "invariants": invariants,
        "selected": selected,
        "free_coordinates": free_coordinates,
        "torsion_coordinates": torsion_coordinates,
        "relation_basis": relation_basis,
        "target_index": target_index,
        "subgroup_order": subgroup_order,
        "verifier_result": verifier_result,
    }


def _bezout_many(values: list[int]) -> tuple[int, list[int]]:
    if not values:
        return 0, []
    gcd_value = 0
    coefficients: list[int] = []
    for value in values:
        old = gcd_value
        a, b = old, value
        x0, x1 = 1, 0
        y0, y1 = 0, 1
        while b:
            quotient = a // b
            a, b = b, a - quotient * b
            x0, x1 = x1, x0 - quotient * x1
            y0, y1 = y1, y0 - quotient * y1
        if a < 0:
            a, x0, y0 = -a, -x0, -y0
        coefficients = [entry * x0 for entry in coefficients] + [y0]
        gcd_value = a
    return gcd_value, coefficients


def _bounded_target_witness(
    relation_basis: list[list[int]], target_index: int, vector_width: int
) -> tuple[int, list[int], list[int]]:
    """Construct a Bezout witness only when its derived scalars stay bounded."""
    target_values = [vector[target_index] for vector in relation_basis]
    target_gcd, combination = _bezout_many(target_values)
    if any(abs(value) > MAX_GROUP_SCALAR_ABS for value in combination):
        raise RelationLatticeError(
            "complexity",
            "derived target-gcd combination exceeds exact-replay scalar limit",
        )
    target_relation = [
        sum(multiplier * vector[i] for multiplier, vector in zip(combination, relation_basis))
        for i in range(vector_width)
    ]
    if any(abs(value) > MAX_GROUP_SCALAR_ABS for value in target_relation):
        raise RelationLatticeError(
            "complexity",
            "derived target-gcd relation exceeds exact-replay scalar limit",
        )
    return target_gcd, combination, target_relation


def _certificate_payload(validated: dict) -> dict:
    value = validated["value"]
    r = len(validated["selected"])
    torsion_rank = len(validated["invariants"])
    free_matrix = _transpose(validated["free_coordinates"], len(validated["free_basis"]))
    torsion_matrix = _transpose(validated["torsion_coordinates"], torsion_rank)
    extended_matrix = [row + [0] * torsion_rank for row in free_matrix]
    for index, (row, invariant) in enumerate(zip(torsion_matrix, validated["invariants"])):
        tail = [0] * torsion_rank
        tail[index] = -invariant
        extended_matrix.append(row + tail)
    matrix_width = r + torsion_rank
    rational_rank = matrix_rank(extended_matrix)
    expected_kernel_rank = matrix_width - rational_rank
    relation_basis = validated["relation_basis"]
    if len(relation_basis) != expected_kernel_rank:
        raise RelationLatticeError(
            "kernel_rank",
            "supplied relation basis has the wrong rank",
            {"expected": expected_kernel_rank, "observed": len(relation_basis)},
        )

    extended_columns = []
    for relation_index, vector in enumerate(relation_basis):
        free_sums = [sum(a * n for a, n in zip(row, vector)) for row in free_matrix]
        if any(free_sums):
            raise RelationLatticeError(
                "kernel", f"relation {relation_index} has nonzero free coordinates"
            )
        quotient_coordinates = []
        for row, invariant in zip(torsion_matrix, validated["invariants"]):
            total = sum(t * n for t, n in zip(row, vector))
            if total % invariant:
                raise RelationLatticeError(
                    "kernel", f"relation {relation_index} violates torsion congruence"
                )
            quotient_coordinates.append(total // invariant)
        if _sum_points(vector, validated["selected"], validated["ainvs"]) is not None:
            raise RelationLatticeError(
                "kernel", f"relation {relation_index} fails exact group replay"
            )
        extended_columns.append(vector + quotient_coordinates)

    extended_kernel = _transpose(extended_columns, matrix_width)
    if matrix_rank(extended_kernel) != expected_kernel_rank:
        raise RelationLatticeError("kernel_rank", "relation basis vectors are dependent")
    minor_gcd, witness_rows, witness_det = maximal_minor_gcd(
        extended_kernel, expected_kernel_rank
    )
    if minor_gcd != 1:
        raise RelationLatticeError(
            "kernel_not_primitive",
            "supplied basis is a finite-index sublattice of the full integer kernel",
            {"maximal_minor_gcd": minor_gcd},
        )

    independence_minor = None
    if expected_kernel_rank == 0:
        if len(free_matrix) < r:
            raise RelationLatticeError("independence", "no full-rank free-coordinate minor exists")
        row_indices = independent_row_indices(free_matrix, r)
        if len(row_indices) != r:
            raise RelationLatticeError("independence", "selected points lack a nonzero free minor")
        candidate = [[free_matrix[i][j] for j in range(r)] for i in row_indices]
        value_det = determinant(candidate)
        if not value_det:
            raise RelationLatticeError(
                "independence", "selected points lack a nonzero free minor"
            )
        independence_minor = {
            "row_indices": row_indices,
            "determinant": value_det,
        }

    target_gcd, combination, target_relation = _bounded_target_witness(
        relation_basis, validated["target_index"], r
    )
    if relation_basis:
        if target_relation[validated["target_index"]] != target_gcd:
            raise RelationLatticeError("target_gcd", "Bezout target witness is inconsistent")
        if _sum_points(target_relation, validated["selected"], validated["ainvs"]) is not None:
            raise RelationLatticeError("target_gcd", "target-gcd relation fails exact replay")
    conditional_dependence = "CERT_NO" if expected_kernel_rank == 0 else "CERT_YES"
    source_binding = {
        "status": "UNBOUND",
        "conditional_invertibility_suppressed": True,
        "claimed_source_subgroup_order": validated["subgroup_order"],
        "selected_target_position": validated["target_index"],
        "missing_required_evidence": [
            "frozen_source_subgroup_order_certificate",
            "frozen_source_selected_point_ordering_and_target",
            "good_reduction_and_exact_selected_point_reductions",
            "source_base_point_order_and_selected_scalar_replay",
        ],
        "reason": (
            "a claimed subgroup order and a rational tuple position do not bind "
            "this relation to the frozen finite-field source experiment"
        ),
    }
    return {
        "schema": CERTIFICATE_SCHEMA,
        "status": "CONDITIONAL_STRUCTURE_ONLY",
        "scope": "conditional_on_unverified_caller_supplied_full_mw_basis_assertion",
        "input": value,
        "input_sha256": object_sha256(value),
        "basis_verifier": validated["verifier_result"],
        "basis_verifier_sha256": object_sha256(validated["verifier_result"]),
        "repository_trust": _repository_trust_summary(),
        "matrix_certificate": {
            "free_coordinate_matrix": free_matrix,
            "torsion_coordinate_matrix": torsion_matrix,
            "extended_presentation_matrix": extended_matrix,
            "rational_rank": rational_rank,
            "kernel_rank": expected_kernel_rank,
            "relation_basis": relation_basis,
            "extended_kernel_basis": extended_kernel,
            "extended_kernel_rank": matrix_rank(extended_kernel),
            "maximal_minor_gcd": minor_gcd,
            "primitive_kernel": True,
            "minor_witness_rows": witness_rows,
            "minor_witness_determinant": witness_det,
        },
        "point_replay": {
            "all_basis_points_on_curve": True,
            "torsion_orders_exact": True,
            "torsion_direct_product_exact": True,
            "all_selected_decompositions_exact": True,
            "all_relation_basis_vectors_exact": True,
        },
        "source_binding": source_binding,
        "outcome": {
            "selected_dependence": "UNKNOWN",
            "conditional_selected_dependence": conditional_dependence,
            "complete_relation_lattice": False,
            "conditional_complete_relation_lattice": True,
            "selected_independent": None,
            "conditional_selected_independent": expected_kernel_rank == 0,
            "independence_minor": independence_minor,
            "target_index": validated["target_index"],
            "source_subgroup_order": "UNBOUND",
            "claimed_source_subgroup_order": validated["subgroup_order"],
            "target_coefficient_gcd": target_gcd,
            "target_gcd_combination": combination,
            "target_gcd_relation": target_relation,
            "invertible_target_relation_exists": "UNKNOWN",
            "conditional_invertibility_scope": "UNBOUND_SUPPRESSED",
            "conditional_invertible_target_relation_exists": None,
            "conditional_target_gcd_coprime_to_subgroup_order": None,
        },
        "production_eligible": False,
        "assumptions": [
            "the caller assertion that the supplied Mordell-Weil basis is full and saturated",
            "the caller assertion that the supplied torsion structure is complete",
        ],
        "production_blocker": (
            "this module did not consume a repository-trusted signed "
            "full-Mordell-Weil-basis receipt for this subject"
        ),
    }


def build_relation_lattice_certificate(
    value: Any,
    *,
    basis_verifier: Callable[[dict, dict], dict] | None,
    trusted_verifier_sha256: str | None,
) -> dict:
    """Build conditional lattice structure; never promote caller trust."""
    validated = _validate_input(value, basis_verifier, trusted_verifier_sha256)
    certificate = _certificate_payload(validated)
    certificate["certificate_sha256"] = object_sha256(certificate)
    return certificate


def verify_relation_lattice_certificate(
    certificate: Any,
    *,
    basis_verifier: Callable[[dict, dict], dict] | None,
    trusted_verifier_sha256: str | None,
) -> list[str]:
    """Strictly rebuild conditional structure and its untrusted control input."""
    try:
        _preflight_json(certificate, "certificate")
    except RelationLatticeError as error:
        return [f"certificate_preflight:{error.code}"]
    if not isinstance(certificate, dict):
        return ["certificate_type"]
    supplied_hash = certificate.get("certificate_sha256")
    if not isinstance(supplied_hash, str) or HEX64.fullmatch(supplied_hash) is None:
        return ["certificate_sha256"]
    without_hash = dict(certificate)
    without_hash.pop("certificate_sha256", None)
    errors = []
    try:
        if object_sha256(without_hash) != supplied_hash:
            errors.append("certificate_sha256")
        expected = build_relation_lattice_certificate(
            certificate.get("input"),
            basis_verifier=basis_verifier,
            trusted_verifier_sha256=trusted_verifier_sha256,
        )
    except RelationLatticeError as error:
        return errors + [f"replay:{error.code}"]
    except Exception as error:  # fail closed on unexpected verifier errors
        return errors + [f"verification_exception:{type(error).__name__}"]
    if certificate != expected:
        errors.append("certificate_mismatch")
    return errors
