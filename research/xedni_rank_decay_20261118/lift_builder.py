#!/usr/bin/env python3
"""Exact short-Weierstrass lift construction for the rank-decay protocol.

This module constructs and certifies an *unranked* integral lift.  It does not
run a rank tool, emit a natural rank outcome, or implement amendment panels
M1--M6.  The seven-coefficient incidence solver and generalized-Weierstrass
conversion are the frozen paths from ``xedni_lift_success_20261112/sweep.py``.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any, Callable


# Support both ``python path/to/file.py`` and import from the repository root.
HERE = Path(__file__).resolve().parent
REPOSITORY = HERE.parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
if str(REPOSITORY) not in sys.path:
    sys.path.insert(0, str(REPOSITORY))

import field
import local_conditions
import source_generator
from research.xedni_lift_success_20261112.sweep import (
    on_curve as rational_on_curve,
    solve_affine,
    w_disc,
)


SCHEMA = "xedni.rank-decay-lift/v1"
STATUS = "control_only_no_natural_rank_rows"
STRATEGIES = ("balanced", "wide", "optimized")
MIN_R = 2
MAX_R = 6
OPTIMIZER_RADIUS = 1
OPTIMIZER_TIMEOUT_SECONDS = 60.0
PUBLIC_SEED = "xedni-rank-decay-lift-public-v1"
DECIMAL = re.compile(r"[+-]?(?:0|[1-9][0-9]*)\Z")


class LiftBuildError(RuntimeError):
    """Fail-closed construction error with a machine-readable reason."""

    def __init__(self, code: str, message: str, details: dict | None = None):
        super().__init__(message)
        self.code = code
        self.details = {} if details is None else details


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def object_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _integer(value: Any, name: str) -> int:
    if isinstance(value, bool):
        raise LiftBuildError("invalid_integer", f"{name} must not be bool")
    if isinstance(value, int):
        return value
    if isinstance(value, str) and DECIMAL.fullmatch(value):
        return int(value)
    raise LiftBuildError("invalid_integer", f"{name} must be an integer")


def balanced_residue(value: int, modulus: int) -> int:
    """Return the unique representative in ``(-modulus/2, modulus/2]``."""
    if modulus <= 0:
        raise ValueError("modulus must be positive")
    value %= modulus
    return value - modulus if value > modulus // 2 else value


def crt_combine(residues: list[int], moduli: list[int]) -> int:
    """Combine residues over pairwise-coprime positive moduli."""
    if len(residues) != len(moduli) or not residues:
        raise ValueError("CRT needs equally many nonempty residues and moduli")
    value = 0
    product = 1
    for index, (residue, modulus) in enumerate(zip(residues, moduli)):
        if modulus <= 1:
            raise ValueError(f"CRT modulus {index} must exceed one")
        if math.gcd(product, modulus) != 1:
            raise ValueError("CRT moduli must be pairwise coprime")
        multiplier = ((residue - value) * pow(product, -1, modulus)) % modulus
        value += multiplier * product
        product *= modulus
    return value % product


def incidence_row(point: tuple[int, int]) -> list[int]:
    x, y = point
    return [y * y, x * y, y, x**3, x * x, x, 1]


def _dot(left: list[int], right: list[int]) -> int:
    return sum(a * b for a, b in zip(left, right))


def _point(value: Any, name: str) -> tuple[int, int]:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise LiftBuildError("invalid_point", f"{name} must be an affine point")
    return _integer(value[0], f"{name}[0]"), _integer(value[1], f"{name}[1]")


def _validate_source(source: dict, r: int) -> dict:
    if not isinstance(source, dict) or source.get("schema") != source_generator.SCHEMA:
        raise LiftBuildError("source_schema", "source record has the wrong schema")
    prime = _integer(source.get("p"), "source.p")
    if not source_generator.is_prime_u32(prime) or prime == 2:
        raise LiftBuildError("source_prime", "source modulus is not an odd u32 prime")
    family = source.get("family")
    if family not in {"generic", "j0"}:
        raise LiftBuildError("source_family", "source family is unsupported")
    curve = source.get("curve")
    if not isinstance(curve, dict):
        raise LiftBuildError("source_curve", "source curve is missing")
    a = _integer(curve.get("a"), "source.curve.a")
    b = _integer(curve.get("b"), "source.curve.b")
    if not (0 <= a < prime and 0 <= b < prime):
        raise LiftBuildError("source_curve", "source coefficients are not reduced")
    if family == "j0" and a != 0:
        raise LiftBuildError("source_curve", "j0 source has nonzero a")
    if field.discriminant(a, b, prime) == 0:
        raise LiftBuildError("source_singular", "source curve is singular")

    cardinality = _integer(source.get("cardinality"), "source.cardinality")
    raw_factors = source.get("cardinality_factors")
    if not isinstance(raw_factors, list):
        raise LiftBuildError("source_factorization", "source factors are missing")
    factors = [
        (_integer(item[0], "source.factor.prime"), _integer(item[1], "source.factor.exp"))
        for item in raw_factors
        if isinstance(item, (list, tuple)) and len(item) == 2
    ]
    if len(factors) != len(raw_factors):
        raise LiftBuildError("source_factorization", "malformed factorization entry")
    try:
        source_generator.validate_factorization(cardinality, factors)
    except (TypeError, ValueError) as error:
        raise LiftBuildError("source_factorization", str(error)) from error
    radius = source_generator.hasse_radius(prime)
    if not prime + 1 - radius <= cardinality <= prime + 1 + radius:
        raise LiftBuildError("source_cardinality", "source cardinality violates Hasse")

    subgroup_order = _integer(
        source.get("source_subgroup_order"), "source.source_subgroup_order"
    )
    cofactor = _integer(source.get("source_cofactor"), "source.source_cofactor")
    if (
        not source_generator._factor_is_prime(subgroup_order)
        or subgroup_order < 2 * r + 1
        or subgroup_order * cofactor != cardinality
        or source.get("base_point_order") != subgroup_order
    ):
        raise LiftBuildError("source_subgroup", "source subgroup certificate is invalid")
    base = _point(source.get("base_point"), "source.base_point")
    if not field.on_curve(base, a, b, prime):
        raise LiftBuildError("source_base", "base point is off the source curve")
    if field.point_mul(subgroup_order, base, a, prime) is not None:
        raise LiftBuildError("source_base", "subgroup order does not annihilate base")

    max_r = _integer(source.get("max_r"), "source.max_r")
    if max_r < r:
        raise LiftBuildError("source_prefix", "source maximum tuple is too short")
    raw_points = source.get("ordered_points")
    raw_scalars = source.get("ordered_scalars")
    if not isinstance(raw_points, list) or not isinstance(raw_scalars, list):
        raise LiftBuildError("source_tuple", "source tuple is missing")
    if len(raw_points) != max_r or len(raw_scalars) != max_r:
        raise LiftBuildError("source_tuple", "source tuple length disagrees with max_r")
    points = [_point(value, f"source.ordered_points[{i}]") for i, value in enumerate(raw_points)]
    scalars = [_integer(value, f"source.ordered_scalars[{i}]") for i, value in enumerate(raw_scalars)]
    for index, (scalar, point) in enumerate(zip(scalars, points)):
        if not 1 <= scalar < subgroup_order:
            raise LiftBuildError("source_scalar", f"source scalar {index} is out of range")
        if field.point_mul(scalar, base, a, prime) != point:
            raise LiftBuildError("source_replay", f"source point {index} fails scalar replay")
    signed = set(points) | {field.point_neg(point, prime) for point in points}
    if len(signed) != 2 * len(points):
        raise LiftBuildError("source_tuple", "source points are not distinct up to sign")

    prefixes = source.get("prefixes")
    prefix = prefixes.get(str(r)) if isinstance(prefixes, dict) else None
    if not isinstance(prefix, dict):
        raise LiftBuildError("source_prefix", f"source prefix r={r} is missing")
    indices = prefix.get("indices")
    if (
        not isinstance(indices, list)
        or len(indices) != r
        or any(isinstance(index, bool) or not isinstance(index, int) for index in indices)
        or len(set(indices)) != r
        or any(index < 0 or index >= max_r for index in indices)
    ):
        raise LiftBuildError("source_prefix", "source prefix indices are invalid")
    if prefix.get("target_index") != indices[-1]:
        raise LiftBuildError("source_prefix", "prefix target is not its final point")
    selected_points = [points[index] for index in indices]
    selected_scalars = [scalars[index] for index in indices]
    rank = local_conditions.matrix_rank_mod(
        (local_conditions.weierstrass_incidence_row(point, prime) for point in selected_points),
        prime,
    )
    if rank != r:
        raise LiftBuildError(
            "source_incidence_rank",
            f"source seven-column incidence rank is {rank}, expected {r}",
        )
    return {
        "p": prime,
        "a": a,
        "b": b,
        "family": family,
        "base": base,
        "subgroup_order": subgroup_order,
        "indices": indices,
        "target_index": indices[-1],
        "points": selected_points,
        "scalars": selected_scalars,
        "all_point_count": len(points),
    }


def _validate_local(local_config: dict | None, r: int) -> dict:
    if local_config is None:
        return {"arm": "A_none", "M": 1, "entries": [], "config": None}
    if not isinstance(local_config, dict):
        raise LiftBuildError("local_schema", "local conditions must be an object")
    if (
        local_config.get("arm") == "I_incompatible"
        or local_config.get("primary_estimand_eligible") is False
    ):
        raise LiftBuildError(
            "unsupported_panel",
            "I_incompatible belongs to the unimplemented M2 mechanism panel",
        )
    if local_config.get("r") != r:
        raise LiftBuildError("local_r", "local-condition r does not match the lift")
    errors = local_conditions.check_local_conditions(local_config)
    if errors:
        raise LiftBuildError(
            "local_certificate", "local-condition checker failed", {"errors": errors}
        )
    entries = []
    for entry_index, entry in enumerate(local_config.get("local", [])):
        prime = _integer(entry.get("prime"), f"local[{entry_index}].prime")
        a = _integer(entry.get("a"), f"local[{entry_index}].a")
        b = _integer(entry.get("b"), f"local[{entry_index}].b")
        expected_coefficients = [1, 0, 0, -1, 0, -a, -b]
        raw_coefficients = entry.get("weierstrass_coefficient_vector")
        if not isinstance(raw_coefficients, list) or len(raw_coefficients) != 7:
            raise LiftBuildError("local_coefficients", "local coefficient vector is missing")
        coefficients = [
            _integer(value, f"local[{entry_index}].coefficient[{i}]")
            for i, value in enumerate(raw_coefficients)
        ]
        if any((left - right) % prime for left, right in zip(coefficients, expected_coefficients)):
            raise LiftBuildError(
                "local_coefficients", f"local coefficient replay failed at prime {prime}"
            )
        points = [
            _point(value, f"local[{entry_index}].selected_points[{i}]")
            for i, value in enumerate(entry.get("selected_points", []))
        ]
        if len(points) != r:
            raise LiftBuildError("local_points", f"local tuple at {prime} has wrong length")
        rank = local_conditions.matrix_rank_mod(
            (local_conditions.weierstrass_incidence_row(point, prime) for point in points),
            prime,
        )
        if rank != r:
            raise LiftBuildError(
                "local_incidence_rank",
                f"local seven-column incidence rank at {prime} is {rank}, expected {r}",
            )
        entries.append(
            {
                "prime": prime,
                "a": a,
                "b": b,
                "points": points,
                "coefficients": coefficients,
                "curve_attempts": copy.deepcopy(entry.get("curve_attempts", [])),
            }
        )
    product = math.prod(entry["prime"] for entry in entries)
    if local_config.get("M") != product:
        raise LiftBuildError("local_modulus", "local modulus product is inconsistent")
    return {
        "arm": local_config.get("arm"),
        "M": product,
        "entries": entries,
        "config": local_config,
    }


def _prepare_inputs(source: dict, local_config: dict | None, r: int) -> dict:
    source_data = _validate_source(source, r)
    local_data = _validate_local(local_config, r)
    moduli = [source_data["p"]] + [entry["prime"] for entry in local_data["entries"]]
    for index, modulus in enumerate(moduli):
        if any(math.gcd(modulus, previous) != 1 for previous in moduli[:index]):
            raise LiftBuildError("noncoprime_moduli", "source/local moduli are not coprime")
    modulus = math.prod(moduli)
    if modulus != source_data["p"] * local_data["M"]:
        raise LiftBuildError("crt_modulus", "full CRT modulus is inconsistent")
    source_coefficients = [
        1,
        0,
        0,
        -1,
        0,
        -source_data["a"],
        -source_data["b"],
    ]
    coefficient_residues = [source_coefficients] + [
        entry["coefficients"] for entry in local_data["entries"]
    ]
    point_residues = []
    for point_index, source_point in enumerate(source_data["points"]):
        point_residues.append(
            [source_point]
            + [entry["points"][point_index] for entry in local_data["entries"]]
        )
    return {
        "source": source_data,
        "local": local_data,
        "moduli": moduli,
        "modulus": modulus,
        "coefficient_residues": coefficient_residues,
        "point_residues": point_residues,
    }


def _public_selector_material(prepared: dict, source: dict, r: int, public_seed: str) -> dict:
    """Public selector input; deliberately excludes every source scalar."""
    source_data = prepared["source"]
    local_data = prepared["local"]
    return {
        "schema": "xedni.lift-public-selector/v1",
        "seed": public_seed,
        "source_id": source.get("source_id"),
        "source_index": source.get("source_index"),
        "p": source_data["p"],
        "family": source_data["family"],
        "source_curve": [source_data["a"], source_data["b"]],
        "r": r,
        "indices": source_data["indices"],
        "source_points": [list(point) for point in source_data["points"]],
        "local_arm": local_data["arm"],
        "local": [
            {
                "prime": entry["prime"],
                "curve": [entry["a"], entry["b"]],
                "points": [list(point) for point in entry["points"]],
                "coefficients": entry["coefficients"],
            }
            for entry in local_data["entries"]
        ],
    }


def _coordinate_representatives(
    prepared: dict,
    source: dict,
    r: int,
    strategy: str,
    public_seed: str,
) -> tuple[list[tuple[int, int]], list[list[int]], dict, str]:
    modulus = prepared["modulus"]
    balanced_points = []
    for residues in prepared["point_residues"]:
        balanced_points.append(
            (
                balanced_residue(crt_combine([point[0] for point in residues], prepared["moduli"]), modulus),
                balanced_residue(crt_combine([point[1] for point in residues], prepared["moduli"]), modulus),
            )
        )
    material = _public_selector_material(prepared, source, r, public_seed)
    material_hash = object_sha256(material)
    shifts = [[0, 0] for _ in range(r)]
    points = list(balanced_points)
    if strategy == "wide":
        stream = field.HashStream(f"{PUBLIC_SEED}|{material_hash}")
        shifts = [[stream.randbelow(3) - 1, stream.randbelow(3) - 1] for _ in range(r)]
        points = [
            (point[0] + modulus * shift[0], point[1] + modulus * shift[1])
            for point, shift in zip(balanced_points, shifts)
        ]
    return points, shifts, material, material_hash


def _solve_coset(prepared: dict, points: list[tuple[int, int]]) -> dict:
    modulus = prepared["modulus"]
    residue_coefficients = []
    for column in range(7):
        combined = crt_combine(
            [row[column] for row in prepared["coefficient_residues"]],
            prepared["moduli"],
        )
        residue_coefficients.append(balanced_residue(combined, modulus))
    rows = [incidence_row(point) for point in points]
    products = [_dot(row, residue_coefficients) for row in rows]
    if any(product % modulus for product in products):
        raise LiftBuildError(
            "incidence_crt", "combined point/coefficient residues violate incidence"
        )
    rhs = [-product // modulus for product in products]
    solution = solve_affine(rows, rhs, 7)
    if solution is None:
        raise LiftBuildError(
            "no_integer_solution",
            "the exact incidence coset has no integer particular solution",
            {"rhs": rhs},
        )
    correction, kernel, rank = solution
    if rank != len(points):
        raise LiftBuildError(
            "rank_deficient",
            f"exact incidence rank is {rank}, expected {len(points)}",
        )
    if len(kernel) != 7 - rank:
        raise LiftBuildError("kernel_dimension", "integer kernel has unexpected dimension")
    if any(_dot(row, correction) != target for row, target in zip(rows, rhs)):
        raise LiftBuildError("solver_replay", "integer particular correction does not replay")
    if any(_dot(row, vector) for row in rows for vector in kernel):
        raise LiftBuildError("solver_replay", "integer kernel does not replay")
    particular = [
        residue + modulus * delta
        for residue, delta in zip(residue_coefficients, correction)
    ]
    directions = [[modulus * value for value in vector] for vector in kernel]
    if any(_dot(row, particular) for row in rows):
        raise LiftBuildError("solver_replay", "lift particular misses an incidence row")
    if any(_dot(row, vector) for row in rows for vector in directions):
        raise LiftBuildError("solver_replay", "lift direction changes an incidence row")
    return {
        "rows": rows,
        "coefficient_residue_representative": residue_coefficients,
        "divided_rhs": rhs,
        "integer_correction": correction,
        "particular": particular,
        "directions": directions,
        "rank": rank,
        "kernel_dimension": len(kernel),
    }


def optimizer_payload(coset: dict, modulus: int) -> dict:
    return {
        "particular": [str(value) for value in coset["particular"]],
        "directions": [[str(value) for value in row] for row in coset["directions"]],
        "exact_constraints": [[str(value) for value in row] for row in coset["rows"]],
        "congruence_modulus": str(modulus),
    }


def _resolve_binary(binary: str | Path) -> Path:
    text = str(binary)
    resolved = shutil.which(text)
    path = Path(resolved) if resolved else Path(text).expanduser().resolve()
    if not path.is_file():
        raise LiftBuildError("optimizer_missing", f"ca-icx binary not found: {binary}")
    return path


def run_ca_icx(
    payload: dict,
    *,
    binary: str | Path,
    radius: int,
    max_candidates: int,
    timeout_seconds: float = OPTIMIZER_TIMEOUT_SECONDS,
) -> dict:
    """Invoke the frozen seven-coefficient optimizer and retain full evidence."""
    executable = _resolve_binary(binary)
    payload_bytes = (canonical_json(payload) + "\n").encode()
    with tempfile.TemporaryDirectory(prefix="xedni-lift-") as temporary:
        input_path = Path(temporary) / "input.json"
        input_path.write_bytes(payload_bytes)
        command = [
            str(executable),
            "--json",
            "xedni-lift",
            "--model",
            "weierstrass",
            "--input",
            str(input_path),
            "--radius",
            str(radius),
            "--max-candidates",
            str(max_candidates),
        ]
        started = time.perf_counter_ns()
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            raise LiftBuildError(
                "optimizer_timeout",
                f"ca-icx exceeded {timeout_seconds} seconds",
                {"command": command, "stdout": error.stdout, "stderr": error.stderr},
            ) from error
        wall_ns = time.perf_counter_ns() - started
    execution = {
        "command": command,
        "returncode": completed.returncode,
        "timeout_seconds": timeout_seconds,
        "wall_ns": wall_ns,
        "binary_sha256": file_sha256(executable),
        "payload_sha256": hashlib.sha256(payload_bytes).hexdigest(),
        "stdout": completed.stdout,
        "stdout_sha256": hashlib.sha256(completed.stdout.encode()).hexdigest(),
        "stderr": completed.stderr,
        "stderr_sha256": hashlib.sha256(completed.stderr.encode()).hexdigest(),
    }
    if completed.returncode != 0:
        raise LiftBuildError(
            "optimizer_nonzero",
            f"ca-icx exited with status {completed.returncode}",
            execution,
        )
    try:
        report = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise LiftBuildError("optimizer_json", "ca-icx output is not JSON", execution) from error
    return {"backend": "ca-icx", "report": report, "execution": execution}


def _normalize_optimizer_evidence(raw: dict, backend: str) -> dict:
    if not isinstance(raw, dict):
        raise LiftBuildError("optimizer_result", "optimizer returned a non-object")
    if "report" in raw:
        evidence = copy.deepcopy(raw)
        evidence.setdefault("backend", backend)
    else:
        evidence = {
            "backend": backend,
            "report": copy.deepcopy(raw),
            "execution": {
                "injected": True,
                "report_sha256": object_sha256(raw),
            },
        }
    return evidence


def _optimizer_coefficients(evidence: dict, max_candidates: int) -> list[int]:
    report = evidence.get("report")
    if not isinstance(report, dict):
        raise LiftBuildError("optimizer_result", "optimizer report is missing")
    if report.get("operation") != "xedni-lift" or report.get("model") != "weierstrass":
        raise LiftBuildError("optimizer_result", "optimizer report identifies the wrong operation")
    if report.get("status") != "complete":
        raise LiftBuildError("optimizer_result", "optimizer did not report completion")
    result = report.get("result")
    if not isinstance(result, dict):
        raise LiftBuildError("optimizer_result", "optimizer result object is missing")
    if result.get("exact_constraints_preserved") is not True:
        raise LiftBuildError("optimizer_certificate", "optimizer did not preserve incidence")
    if result.get("congruence_preserved") is not True:
        raise LiftBuildError("optimizer_certificate", "optimizer did not preserve congruence")
    score = result.get("optimized_score")
    if not isinstance(score, dict) or score.get("nonsingular") is not True:
        raise LiftBuildError("optimizer_certificate", "optimizer did not certify nonsingularity")
    evaluated = result.get("candidates_evaluated")
    if (
        isinstance(evaluated, bool)
        or not isinstance(evaluated, int)
        or evaluated < 1
        or evaluated > max_candidates
    ):
        raise LiftBuildError("optimizer_budget", "optimizer candidate count is outside its cap")
    raw_coefficients = result.get("optimized_coefficients")
    if not isinstance(raw_coefficients, list) or len(raw_coefficients) != 7:
        raise LiftBuildError("optimizer_result", "optimizer coefficient vector has wrong length")
    return [_integer(value, f"optimizer.coefficient[{i}]") for i, value in enumerate(raw_coefficients)]


def _convert_weierstrass(
    signed_coefficients: list[int], points: list[tuple[int, int]]
) -> tuple[list[int], list[list[int]], int]:
    a0, a1, a3 = signed_coefficients[:3]
    a00, a2, a4, a6 = (
        -signed_coefficients[3],
        -signed_coefficients[4],
        -signed_coefficients[5],
        -signed_coefficients[6],
    )
    c3 = a0 * a00
    if c3 == 0:
        raise LiftBuildError("degenerate_conversion", "a0*a00 vanishes")
    ainvs = [
        a1,
        a0 * a2,
        a3 * c3,
        a0 * a4 * c3,
        a0 * a6 * c3 * c3,
    ]
    converted = [[c3 * x, c3 * a0 * y] for x, y in points]
    discriminant = w_disc(tuple(ainvs))
    if discriminant == 0:
        raise LiftBuildError("singular_lift", "converted generalized curve is singular")
    if any(not rational_on_curve(tuple(point), tuple(ainvs)) for point in converted):
        raise LiftBuildError("point_off_lift", "converted point misses the generalized curve")
    return ainvs, converted, discriminant


def _unsupported_panel(panel: Any) -> bool:
    return isinstance(panel, str) and re.fullmatch(r"M[1-6](?:\b|[_:-].*)", panel) is not None


def build_lift(
    source: dict,
    r: int,
    strategy: str,
    local_config: dict | None = None,
    *,
    ca_icx: str | Path = "suite/target/release/ca-icx",
    optimizer: Callable[..., dict] | None = None,
    public_seed: str = PUBLIC_SEED,
    mechanism_panel: str | None = None,
    optimizer_timeout_seconds: float = OPTIMIZER_TIMEOUT_SECONDS,
) -> dict:
    """Build one exact unranked lift and independently certify every residue.

    An injected ``optimizer`` receives ``(payload, radius=1,
    max_candidates=3**(7-r))`` and must return the same report schema as
    ``ca-icx --json xedni-lift``.  It exists for deterministic controls only.
    """
    if isinstance(r, bool) or not isinstance(r, int) or not MIN_R <= r <= MAX_R:
        raise LiftBuildError(
            "unsupported_r",
            "only r=2..6 has a certified short-Weierstrass point-map path",
        )
    if strategy not in STRATEGIES:
        raise LiftBuildError("unsupported_strategy", f"unknown lift strategy {strategy!r}")
    if mechanism_panel is not None:
        if _unsupported_panel(mechanism_panel):
            raise LiftBuildError(
                "unsupported_panel",
                f"{mechanism_panel} is not implemented by the primary lift builder",
            )
        raise LiftBuildError("unsupported_panel", "mechanism panels are not supported")
    for value in (source, local_config or {}):
        for key in ("mechanism_panel", "panel"):
            if _unsupported_panel(value.get(key)):
                raise LiftBuildError("unsupported_panel", f"input requests {value[key]}")
    if not isinstance(public_seed, str) or not public_seed:
        raise LiftBuildError("public_seed", "public seed must be nonempty")

    prepared = _prepare_inputs(source, local_config, r)
    coordinate_strategy = "balanced" if strategy == "optimized" else strategy
    points, shifts, public_material, public_material_hash = _coordinate_representatives(
        prepared, source, r, coordinate_strategy, public_seed
    )
    coset = _solve_coset(prepared, points)
    payload = optimizer_payload(coset, prepared["modulus"])
    candidate_cap = 3 ** len(coset["directions"])
    expected_cap = 3 ** (7 - r)
    if candidate_cap != expected_cap:
        raise LiftBuildError("optimizer_budget", "kernel dimension changed the frozen cap")

    optimizer_evidence: dict
    if strategy == "optimized":
        if optimizer is None:
            raw_evidence = run_ca_icx(
                payload,
                binary=ca_icx,
                radius=OPTIMIZER_RADIUS,
                max_candidates=candidate_cap,
                timeout_seconds=optimizer_timeout_seconds,
            )
            optimizer_evidence = _normalize_optimizer_evidence(raw_evidence, "ca-icx")
        else:
            try:
                raw_report = optimizer(
                    copy.deepcopy(payload),
                    radius=OPTIMIZER_RADIUS,
                    max_candidates=candidate_cap,
                )
            except Exception as error:
                raise LiftBuildError(
                    "optimizer_exception", f"injected optimizer failed: {error}"
                ) from error
            optimizer_evidence = _normalize_optimizer_evidence(raw_report, "injected-control")
        signed_coefficients = _optimizer_coefficients(optimizer_evidence, candidate_cap)
    else:
        signed_coefficients = list(coset["particular"])
        optimizer_evidence = {
            "backend": "not-invoked",
            "reason": "strategy_retains_deterministic_particular",
            "radius": OPTIMIZER_RADIUS,
            "max_candidates": candidate_cap,
        }

    if any(_dot(row, signed_coefficients) for row in coset["rows"]):
        raise LiftBuildError("candidate_incidence", "final coefficient vector misses a point")
    if any(
        (candidate - particular) % prepared["modulus"]
        for candidate, particular in zip(signed_coefficients, coset["particular"])
    ):
        raise LiftBuildError("candidate_congruence", "final coefficient vector left its CRT class")

    ainvs, converted_points, discriminant = _convert_weierstrass(signed_coefficients, points)
    source_data = prepared["source"]
    local_data = prepared["local"]
    upstream_attempts = {
        "source": {
            "curve_generation": source.get("curve", {}).get("generation_attempts"),
            "point_sampling": source.get("point_sampling_attempts"),
            "scalar_sampling": source.get("scalar_sampling_attempts"),
        },
        "local_prime_rejections": copy.deepcopy(
            [] if local_config is None else local_config.get("prime_rejections", [])
        ),
        "local_curves": [
            {"prime": entry["prime"], "curve_attempts": entry["curve_attempts"]}
            for entry in local_data["entries"]
        ],
        "local_scalar_attempts": copy.deepcopy(
            [] if local_config is None else local_config.get("scalar_attempts", [])
        ),
    }
    source_hash = object_sha256(source)
    local_hash = object_sha256(local_config)
    model_hash = object_sha256(
        {
            "signed_coefficients": signed_coefficients,
            "ainvs": ainvs,
            "points": converted_points,
        }
    )
    row_id = (
        f"{source.get('source_id', 'source')}|r={r}|lift={strategy}|"
        f"local={local_data['arm']}|{model_hash[:16]}"
    )
    result = {
        "schema": SCHEMA,
        "status": STATUS,
        "scope": "certified_integral_lift_only; rank/dependence/recovery_not_run",
        "row_id": row_id,
        "rank_outcome": None,
        "source_id": source.get("source_id"),
        "p": source_data["p"],
        "family": source_data["family"],
        "r": r,
        "strategy": strategy,
        "coordinate_strategy": coordinate_strategy,
        "local_arm": local_data["arm"],
        "selected_indices": source_data["indices"],
        "target_index": source_data["target_index"],
        "selected_source_scalars_for_replay_only": source_data["scalars"],
        "moduli": prepared["moduli"],
        "local_modulus": local_data["M"],
        "crt_modulus": prepared["modulus"],
        "point_residues_by_modulus": [
            [list(point) for point in residues] for residues in prepared["point_residues"]
        ],
        "coefficient_residues_by_modulus": prepared["coefficient_residues"],
        "coordinate_representatives": [list(point) for point in points],
        "coordinate_shifts": shifts,
        "public_selector": {
            "seed": public_seed,
            "input": public_material,
            "input_sha256": public_material_hash,
            "uses_source_scalars": False,
        },
        "incidence_coset": coset,
        "optimizer": optimizer_evidence,
        "optimizer_parameters": {
            "radius": OPTIMIZER_RADIUS,
            "max_candidates": candidate_cap,
            "payload_sha256": object_sha256(payload),
        },
        "signed_coefficients": signed_coefficients,
        "ainvs": ainvs,
        "points": converted_points,
        "discriminant": discriminant,
        "coefficient_height_bits": max(abs(value).bit_length() for value in signed_coefficients),
        "discriminant_bits": abs(discriminant).bit_length(),
        "attempts": upstream_attempts,
        "cost_counters": {
            "crt_coordinate_combinations": 2 * r,
            "crt_coefficient_combinations": 7,
            "incidence_rows": r,
            "incidence_columns": 7,
            "integer_coset_solves": 1,
            "wide_coordinate_draws": 2 * r if strategy == "wide" else 0,
            "optimizer_invocations": 1 if strategy == "optimized" else 0,
            "optimizer_candidates": (
                optimizer_evidence["report"]["result"]["candidates_evaluated"]
                if strategy == "optimized"
                else 0
            ),
        },
        "hashes": {
            "source_record_sha256": source_hash,
            "local_record_sha256": local_hash,
            "public_selector_input_sha256": public_material_hash,
            "incidence_coset_sha256": object_sha256(coset),
            "optimizer_payload_sha256": object_sha256(payload),
            "model_sha256": model_hash,
        },
        "certificate": {
            "source_replay": True,
            "local_replay": True,
            "exact_incidence": True,
            "coefficient_congruence": True,
            "all_points_integral_and_on_curve": True,
            "nonsingular_over_q": True,
            "good_reduction_at_all_moduli": True,
            "all_reductions_replayed": True,
        },
    }
    errors = verify_lift(result, source, local_config)
    if errors:
        raise LiftBuildError(
            "internal_certificate", "constructed lift failed independent replay", {"errors": errors}
        )
    return result


def _verify_lift(lift: dict, source: dict, local_config: dict | None) -> list[str]:
    errors: list[str] = []
    if not isinstance(lift, dict) or lift.get("schema") != SCHEMA:
        return ["schema"]
    if lift.get("status") != STATUS or lift.get("rank_outcome") is not None:
        errors.append("status")
    r = lift.get("r")
    strategy = lift.get("strategy")
    if isinstance(r, bool) or not isinstance(r, int) or not MIN_R <= r <= MAX_R:
        return errors + ["r"]
    if strategy not in STRATEGIES:
        return errors + ["strategy"]
    prepared = _prepare_inputs(source, local_config, r)
    coordinate_strategy = "balanced" if strategy == "optimized" else strategy
    public_seed = lift.get("public_selector", {}).get("seed")
    expected_points, expected_shifts, material, material_hash = _coordinate_representatives(
        prepared, source, r, coordinate_strategy, public_seed
    )
    if lift.get("coordinate_strategy") != coordinate_strategy:
        errors.append("coordinate_strategy")
    if lift.get("coordinate_representatives") != [list(point) for point in expected_points]:
        errors.append("coordinate_representatives")
    if lift.get("coordinate_shifts") != expected_shifts:
        errors.append("coordinate_shifts")
    selector = lift.get("public_selector", {})
    if (
        selector.get("input") != material
        or selector.get("input_sha256") != material_hash
        or selector.get("uses_source_scalars") is not False
    ):
        errors.append("public_selector")
    if lift.get("moduli") != prepared["moduli"] or lift.get("crt_modulus") != prepared["modulus"]:
        errors.append("moduli")
    if lift.get("coefficient_residues_by_modulus") != prepared["coefficient_residues"]:
        errors.append("coefficient_residues")
    expected_point_residues = [
        [list(point) for point in residues] for residues in prepared["point_residues"]
    ]
    if lift.get("point_residues_by_modulus") != expected_point_residues:
        errors.append("point_residues")

    expected_coset = _solve_coset(prepared, expected_points)
    if lift.get("incidence_coset") != expected_coset:
        errors.append("incidence_coset")
    raw_coefficients = lift.get("signed_coefficients")
    if not isinstance(raw_coefficients, list) or len(raw_coefficients) != 7:
        return errors + ["signed_coefficients"]
    coefficients = [_integer(value, f"lift.signed_coefficients[{i}]") for i, value in enumerate(raw_coefficients)]
    if strategy in {"balanced", "wide"} and coefficients != expected_coset["particular"]:
        errors.append("deterministic_particular")
    if any(_dot(row, coefficients) for row in expected_coset["rows"]):
        errors.append("exact_incidence")
    if any(
        (value - base) % prepared["modulus"]
        for value, base in zip(coefficients, expected_coset["particular"])
    ):
        errors.append("coefficient_congruence")
    cap = 3 ** (7 - r)
    if lift.get("optimizer_parameters") != {
        "radius": OPTIMIZER_RADIUS,
        "max_candidates": cap,
        "payload_sha256": object_sha256(optimizer_payload(expected_coset, prepared["modulus"])),
    }:
        errors.append("optimizer_parameters")
    if strategy == "optimized":
        try:
            optimized = _optimizer_coefficients(lift.get("optimizer", {}), cap)
        except LiftBuildError:
            errors.append("optimizer_certificate")
        else:
            if optimized != coefficients:
                errors.append("optimizer_coefficients")
    elif lift.get("optimizer", {}).get("backend") != "not-invoked":
        errors.append("optimizer_unexpected")

    ainvs, converted_points, discriminant = _convert_weierstrass(coefficients, expected_points)
    if lift.get("ainvs") != ainvs:
        errors.append("ainvs")
    if lift.get("points") != converted_points:
        errors.append("points")
    if lift.get("discriminant") != discriminant:
        errors.append("discriminant")
    curves = [(prepared["source"]["a"], prepared["source"]["b"])] + [
        (entry["a"], entry["b"]) for entry in prepared["local"]["entries"]
    ]
    for modulus_index, (modulus, (a, b)) in enumerate(zip(prepared["moduli"], curves)):
        if discriminant % modulus == 0:
            errors.append(f"bad_reduction:{modulus}")
        if any((value - target) % modulus for value, target in zip(ainvs, (0, 0, 0, a, b))):
            errors.append(f"coefficient_reduction:{modulus}")
        for point_index, point in enumerate(converted_points):
            target = prepared["point_residues"][point_index][modulus_index]
            if (point[0] - target[0]) % modulus or (point[1] - target[1]) % modulus:
                errors.append(f"point_reduction:{modulus}:{point_index}")
    hashes = lift.get("hashes", {})
    expected_hashes = {
        "source_record_sha256": object_sha256(source),
        "local_record_sha256": object_sha256(local_config),
        "public_selector_input_sha256": material_hash,
        "incidence_coset_sha256": object_sha256(expected_coset),
        "optimizer_payload_sha256": object_sha256(
            optimizer_payload(expected_coset, prepared["modulus"])
        ),
        "model_sha256": object_sha256(
            {"signed_coefficients": coefficients, "ainvs": ainvs, "points": converted_points}
        ),
    }
    if hashes != expected_hashes:
        errors.append("hashes")
    certificate = lift.get("certificate")
    if not isinstance(certificate, dict) or not certificate or any(value is not True for value in certificate.values()):
        errors.append("certificate_flags")
    return errors


def verify_lift(lift: dict, source: dict, local_config: dict | None = None) -> list[str]:
    """Independently replay a lift; any malformed input returns an error list."""
    try:
        return _verify_lift(lift, source, local_config)
    except Exception as error:  # Fail closed for tampered/malformed records.
        return [f"verification_exception:{type(error).__name__}:{error}"]


__all__ = [
    "LiftBuildError",
    "MAX_R",
    "MIN_R",
    "OPTIMIZER_RADIUS",
    "PUBLIC_SEED",
    "SCHEMA",
    "STATUS",
    "STRATEGIES",
    "balanced_residue",
    "build_lift",
    "canonical_json",
    "crt_combine",
    "incidence_row",
    "object_sha256",
    "optimizer_payload",
    "run_ca_icx",
    "verify_lift",
]
