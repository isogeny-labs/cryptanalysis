#!/usr/bin/env python3
"""Worst-case optimization over mixed unresolved-success allocations.

The two uniform allocations used by the original sensitivity artifact are not
extrema of a decay slope in general.  This module treats every prime's success
count as an integer interval

    certified_successes <= S_p <= certified_successes + unresolved

and minimizes a named signed-slope statistic over the full Cartesian product.

There are deliberately three execution modes.

* :func:`exact_box_optimize` enumerates every integer state.  It is suitable
  for the frozen calibration, where each series has only a few unresolved
  rows per prime.  It refuses before evaluating a state when the declared
  limit is exceeded.
* :func:`optimize_poisson_hoeffding` is scalable.  The conditional-Poisson
  lower endpoint is monotone in

      mean(log(p) among events) - C / sqrt(total events).

  For a fixed event total the smallest mean is obtained by assigning unknown
  successes to the smallest primes first (an exchange argument).  Between two
  successive capacity breakpoints the displayed expression is

      x + c / T - C / sqrt(T),

  so its integer minimum is at an interval endpoint or next to its sole
  stationary point.  Evaluating those candidates is therefore a global
  minimization over the integer box, not a corner heuristic.
* Binomial-cloglog uses exhaustive enumeration and fails closed above the
  state limit.
* :func:`optimize_nested_cluster_bootstrap` preserves each unresolved row's
  ``(bits, p, source_id, curve_id)`` membership, freezes the complete bootstrap
  resampling plan before inspecting an allocation, and exhausts the row-level
  integer box when both the allocation and bootstrap-evaluation ceilings fit.
  Above either exact ceiling it returns a certificate of the required state
  count and stops before sampling.  There is deliberately no fallback to
  per-prime totals: no monotone envelope for the nested bootstrap percentile
  has been proved.

"Exact" below refers to coverage of every discrete allocation under the
named deterministic numerical evaluator.  It is not a claim that binary
floating-point likelihood evaluation is exact real arithmetic.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
import hashlib
import itertools
import json
import math
from pathlib import Path
import random
from typing import Any

import analyze
import prime_manifest
import sensitivity


SCHEMA = "xedni.mixed-censoring/v1"
PRODUCTION_READY = False
CLUSTER_ROW_SCHEMA = "xedni.mixed-censoring-cluster-row/v1"
FROZEN_CLUSTER_KEYS = ("bits", "p", "source_id", "curve_id")
FROZEN_FAMILYWISE_ALPHA = 0.05
FROZEN_SIMULTANEOUS_HYPOTHESES = 4_320
FROZEN_CLUSTER_REPLICATES = 172_800
FROZEN_CLUSTER_SEED = "xedni-rank-decay-cluster-bootstrap-20261118-v1"
ENDPOINTS = ("rank_lt_r", "nontrivial_useful_recovery")
DENOMINATORS = ("admitted", "proposed")
PLAIN_JSON_MAX_DEPTH = 64
PLAIN_JSON_MAX_NODES = 5_000_000
PLAIN_JSON_MAX_CONTAINER_LENGTH = 1_000_000
Cell = dict[str, int]
ClusterRow = dict[str, Any]
Evaluator = Callable[[tuple[int, ...]], float | str]


class MixedCensoringError(ValueError):
    """Raised when an allocation box or evaluator result is malformed."""


def implementation_sha256() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def _module_sha256(module: Any) -> str:
    path = getattr(module, "__file__", None)
    if not isinstance(path, str):  # pragma: no cover - ordinary imports have paths
        raise MixedCensoringError("bound evaluator module has no source path")
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _plain_json(value: Any, context: str) -> Any:
    """Return a plain-JSON copy, rejecting every scalar/container subclass."""

    active_containers: set[int] = set()
    nodes = 0

    def visit(current: Any, current_context: str, depth: int) -> Any:
        nonlocal nodes
        if depth > PLAIN_JSON_MAX_DEPTH:
            raise MixedCensoringError(
                f"{context} exceeds plain-JSON depth limit "
                f"{PLAIN_JSON_MAX_DEPTH}"
            )
        nodes += 1
        if nodes > PLAIN_JSON_MAX_NODES:
            raise MixedCensoringError(
                f"{context} exceeds plain-JSON node limit "
                f"{PLAIN_JSON_MAX_NODES}"
            )

        value_type = type(current)
        if current is None or value_type in (bool, int, str):
            return current
        if value_type is float:
            if not math.isfinite(current):
                raise MixedCensoringError(
                    f"{current_context} must contain only finite floats"
                )
            return current
        if value_type not in (list, dict):
            raise MixedCensoringError(
                f"{current_context} must use exact built-in JSON "
                "scalar/container types"
            )
        if len(current) > PLAIN_JSON_MAX_CONTAINER_LENGTH:
            raise MixedCensoringError(
                f"{current_context} exceeds plain-JSON container length limit "
                f"{PLAIN_JSON_MAX_CONTAINER_LENGTH}"
            )
        identity = id(current)
        if identity in active_containers:
            raise MixedCensoringError(f"{context} contains a container cycle")
        active_containers.add(identity)
        try:
            if value_type is list:
                return [
                    visit(item, f"{current_context}[{index}]", depth + 1)
                    for index, item in enumerate(current)
                ]
            output: dict[str, Any] = {}
            for key, item in current.items():
                if type(key) is not str:
                    raise MixedCensoringError(
                        f"{current_context} keys must be exact built-in strings"
                    )
                output[key] = visit(
                    item, f"{current_context}.{key}", depth + 1
                )
            return output
        finally:
            active_containers.remove(identity)

    return visit(value, context, 0)


def _plain_json_list(value: Any, context: str) -> list[Any]:
    normalized = _plain_json(value, context)
    if type(normalized) is not list:
        raise MixedCensoringError(f"{context} must be an exact built-in list")
    return normalized


def _plain_json_dict(value: Any, context: str) -> dict[str, Any]:
    normalized = _plain_json(value, context)
    if type(normalized) is not dict:
        raise MixedCensoringError(f"{context} must be an exact built-in dict")
    return normalized


def _plain_json_scalar(value: Any, expected: type, context: str) -> Any:
    normalized = _plain_json(value, context)
    if type(normalized) is not expected:
        raise MixedCensoringError(
            f"{context} must be an exact built-in {expected.__name__}"
        )
    return normalized


def _plain_int(value: Any) -> bool:
    return type(value) is int


def normalize_cells(cells: Iterable[Mapping[str, Any]]) -> list[Cell]:
    """Validate, aggregate duplicate primes, and return cells in prime order."""
    plain_cells = _plain_json_list(cells, "cells")
    aggregated: dict[int, Cell] = {}
    required = {"p", "exposure", "certified_successes", "unresolved"}
    for index, source in enumerate(plain_cells):
        if type(source) is not dict or set(source) != required:
            raise MixedCensoringError(
                f"cell[{index}] must have exactly {sorted(required)}"
            )
        p = source["p"]
        exposure = source["exposure"]
        certified = source["certified_successes"]
        unresolved = source["unresolved"]
        if not _plain_int(p) or p <= 1:
            raise MixedCensoringError(f"cell[{index}].p must be an integer > 1")
        if not _plain_int(exposure) or exposure <= 0:
            raise MixedCensoringError(
                f"cell[{index}].exposure must be a positive integer"
            )
        if not _plain_int(certified) or certified < 0:
            raise MixedCensoringError(
                f"cell[{index}].certified_successes must be a nonnegative integer"
            )
        if not _plain_int(unresolved) or unresolved < 0:
            raise MixedCensoringError(
                f"cell[{index}].unresolved must be a nonnegative integer"
            )
        if certified + unresolved > exposure:
            raise MixedCensoringError(
                f"cell[{index}] success interval exceeds exposure"
            )
        if p not in aggregated:
            aggregated[p] = {
                "p": p,
                "exposure": exposure,
                "certified_successes": certified,
                "unresolved": unresolved,
            }
        else:
            target = aggregated[p]
            target["exposure"] += exposure
            target["certified_successes"] += certified
            target["unresolved"] += unresolved
    if not aggregated:
        raise MixedCensoringError("at least one cell is required")
    return [aggregated[p] for p in sorted(aggregated)]


def _token(value: Any, context: str) -> str:
    if (
        type(value) is not str
        or not value
        or len(value) > 256
        or any(character.isspace() or ord(character) < 33 for character in value)
    ):
        raise MixedCensoringError(
            f"{context} must be a nonempty whitespace-free string of at most 256 characters"
        )
    return value


def normalize_cluster_rows(
    rows: Iterable[Mapping[str, Any]],
) -> list[ClusterRow]:
    """Validate row-level intervals without erasing cluster membership.

    A record may aggregate trials only when they share the exact frozen
    cluster key.  Its unresolved count therefore remains an integer interval
    inside one source/curve cluster; this function never aggregates records
    across row IDs, primes, or clusters.
    """

    plain_rows = _plain_json_list(rows, "cluster_rows")
    required = {
        "schema",
        "row_id",
        "bits",
        "p",
        "source_id",
        "curve_id",
        "exposure",
        "certified_successes",
        "unresolved",
    }
    normalized: list[ClusterRow] = []
    seen_ids: set[str] = set()
    for index, source in enumerate(plain_rows):
        if type(source) is not dict or set(source) != required:
            raise MixedCensoringError(
                f"cluster_row[{index}] must have exactly {sorted(required)}"
            )
        if source["schema"] != CLUSTER_ROW_SCHEMA:
            raise MixedCensoringError(
                f"cluster_row[{index}].schema must be {CLUSTER_ROW_SCHEMA!r}"
            )
        row_id = _token(source["row_id"], f"cluster_row[{index}].row_id")
        if row_id in seen_ids:
            raise MixedCensoringError(f"duplicate cluster row_id {row_id!r}")
        seen_ids.add(row_id)
        bits = source["bits"]
        prime = source["p"]
        if not _plain_int(bits) or bits <= 1:
            raise MixedCensoringError(
                f"cluster_row[{index}].bits must be an integer > 1"
            )
        if (
            not _plain_int(prime)
            or prime <= 1
            or prime > 0xFFFFFFFF
            or prime.bit_length() != bits
            or not prime_manifest.is_prime_u32(prime)
        ):
            raise MixedCensoringError(
                f"cluster_row[{index}].p must be a prime of the declared bit size"
            )
        source_id = _token(
            source["source_id"], f"cluster_row[{index}].source_id"
        )
        curve_id = _token(source["curve_id"], f"cluster_row[{index}].curve_id")
        exposure = source["exposure"]
        certified = source["certified_successes"]
        unresolved = source["unresolved"]
        if not _plain_int(exposure) or exposure <= 0:
            raise MixedCensoringError(
                f"cluster_row[{index}].exposure must be a positive integer"
            )
        if not _plain_int(certified) or certified < 0:
            raise MixedCensoringError(
                f"cluster_row[{index}].certified_successes must be nonnegative"
            )
        if not _plain_int(unresolved) or unresolved < 0:
            raise MixedCensoringError(
                f"cluster_row[{index}].unresolved must be nonnegative"
            )
        if certified + unresolved > exposure:
            raise MixedCensoringError(
                f"cluster_row[{index}] success interval exceeds exposure"
            )
        normalized.append(
            {
                "schema": CLUSTER_ROW_SCHEMA,
                "row_id": row_id,
                "bits": bits,
                "p": prime,
                "source_id": source_id,
                "curve_id": curve_id,
                "exposure": exposure,
                "certified_successes": certified,
                "unresolved": unresolved,
            }
        )
    if not normalized:
        raise MixedCensoringError("at least one cluster row is required")
    normalized.sort(
        key=lambda row: (
            row["bits"],
            row["p"],
            row["source_id"],
            row["curve_id"],
            row["row_id"],
        )
    )
    return normalized


def nested_cluster_state_count(rows: Iterable[Mapping[str, Any]]) -> int:
    normalized = normalize_cluster_rows(rows)
    return math.prod(row["unresolved"] + 1 for row in normalized)


def _validate_series(series: Mapping[str, Any]) -> tuple[dict[str, Any], tuple[Any, ...]]:
    plain_series = _plain_json_dict(series, "series")
    if set(plain_series) != set(analyze.SERIES_FIELDS):
        raise MixedCensoringError(
            f"series must have exactly {sorted(analyze.SERIES_FIELDS)}"
        )
    normalized: dict[str, Any] = {}
    for field in analyze.SERIES_FIELDS:
        value = plain_series[field]
        if field == "r":
            if not _plain_int(value) or not 2 <= value <= 9:
                raise MixedCensoringError("series.r must be an integer in [2, 9]")
            normalized[field] = value
        else:
            normalized[field] = _token(value, f"series.{field}")
    key = tuple(normalized[field] for field in analyze.SERIES_FIELDS)
    return normalized, key


def _lower_hex_digest(value: Any, context: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise MixedCensoringError(f"{context} must be 64 lowercase hex digits")
    return value


def cluster_rows_from_analysis_rows(
    rows: Iterable[Mapping[str, Any]],
    *,
    endpoint: str,
    denominator: str,
) -> tuple[list[ClusterRow], dict[str, Any], str]:
    """Derive exact cluster intervals from strict analysis rows.

    This is the production-facing conversion: it derives the series identity
    and rowset digest from the same validated rows used by ``analyze.py`` and
    applies the endpoint/denominator semantics row by row.  The lower-level
    optimizer never has to infer them from aggregate counts.
    """

    plain_rows = _plain_json_list(rows, "analysis_rows")
    endpoint = _plain_json_scalar(endpoint, str, "endpoint")
    denominator = _plain_json_scalar(denominator, str, "denominator")
    if endpoint not in ENDPOINTS:
        raise MixedCensoringError(f"unsupported endpoint {endpoint!r}")
    if denominator not in DENOMINATORS:
        raise MixedCensoringError(f"unsupported denominator {denominator!r}")
    try:
        validated = [analyze.validate_row(row) for row in plain_rows]
    except (analyze.AnalysisError, TypeError, ValueError) as error:
        raise MixedCensoringError(f"analysis row validation failed: {error}") from error
    if not validated:
        raise MixedCensoringError("at least one analysis row is required")
    trial_ids = [row["trial_id"] for row in validated]
    if len(set(trial_ids)) != len(trial_ids):
        raise MixedCensoringError("analysis rows contain duplicate trial_id values")
    keys = {analyze._series_key(row) for row in validated}
    if len(keys) != 1:
        raise MixedCensoringError("analysis rows must belong to exactly one series")
    series_key = next(iter(keys))
    series = dict(zip(analyze.SERIES_FIELDS, series_key, strict=True))
    cluster_rows: list[ClusterRow] = []
    for row in validated:
        if denominator == "admitted" and row["status"] != "ranked":
            continue
        if endpoint == "rank_lt_r":
            if row["status"] == "ranked":
                classification = analyze.classify_rank(row)["rank_class"]
                certified = int(classification == "CERT_LT")
                unresolved = int(classification == "UNKNOWN")
            else:
                certified = 0
                unresolved = int(row["status"] == "certificate_failed")
        else:
            classification = analyze.classify_useful_endpoint(row)
            certified = int(classification == "CERT_YES")
            unresolved = int(classification == "UNKNOWN")
        cluster_rows.append(
            {
                "schema": CLUSTER_ROW_SCHEMA,
                "row_id": row["trial_id"],
                "bits": row["bits"],
                "p": row["p"],
                "source_id": row["source_id"],
                "curve_id": row["curve_id"],
                "exposure": 1,
                "certified_successes": certified,
                "unresolved": unresolved,
            }
        )
    if not cluster_rows:
        raise MixedCensoringError(
            "endpoint/denominator selection produced no exposed cluster rows"
        )
    return (
        normalize_cluster_rows(cluster_rows),
        series,
        analyze.rowset_sha256(validated),
    )


def integer_box_state_count(cells: Iterable[Mapping[str, Any]]) -> int:
    normalized = normalize_cells(cells)
    return math.prod(cell["unresolved"] + 1 for cell in normalized)


def _objective_number(value: float | str) -> float:
    if type(value) is str:
        if value == "-inf":
            return -math.inf
        if value == "+inf":
            return math.inf
        raise MixedCensoringError(
            "evaluator must return a finite number, '-inf', or '+inf'"
        )
    if type(value) not in (int, float):
        raise MixedCensoringError(
            "evaluator must return a finite number, '-inf', or '+inf'"
        )
    number = float(value)
    if math.isnan(number):
        raise MixedCensoringError("evaluator returned NaN")
    return number


def _json_objective(value: float | str) -> float | str:
    number = _objective_number(value)
    if number == -math.inf:
        return "-inf"
    if number == math.inf:
        return "+inf"
    return number


def _base_certificate(
    cells: list[Cell], *, method: str, objective: str, evaluator_sha256: str
) -> dict[str, Any]:
    method = _plain_json_scalar(method, str, "method")
    objective = _plain_json_scalar(objective, str, "objective")
    evaluator_sha256 = _plain_json_scalar(
        evaluator_sha256, str, "evaluator_sha256"
    )
    if not method:
        raise MixedCensoringError("method must be a nonempty string")
    if not objective:
        raise MixedCensoringError("objective must be a nonempty string")
    if (
        len(evaluator_sha256) != 64
        or any(ch not in "0123456789abcdef" for ch in evaluator_sha256)
    ):
        raise MixedCensoringError("evaluator_sha256 must be 64 lowercase hex digits")
    return {
        "schema": SCHEMA,
        "method": method,
        "objective": objective,
        "cells": cells,
        "box_sha256": _sha256(cells),
        "implementation_sha256": implementation_sha256(),
        "evaluator_sha256": evaluator_sha256,
        "state_count": math.prod(cell["unresolved"] + 1 for cell in cells),
    }


def _finish(certificate: dict[str, Any]) -> dict[str, Any]:
    output = dict(certificate)
    output["certificate_sha256"] = _sha256(output)
    return output


def exact_box_optimize(
    cells: Iterable[Mapping[str, Any]],
    evaluator: Evaluator,
    *,
    method: str,
    objective: str,
    evaluator_sha256: str,
    max_states: int = 2_000_000,
) -> dict[str, Any]:
    """Enumerate and minimize over every integer allocation in the box."""
    normalized = normalize_cells(cells)
    max_states = _plain_json_scalar(max_states, int, "max_states")
    if not _plain_int(max_states) or max_states <= 0:
        raise MixedCensoringError("max_states must be a positive integer")
    base = _base_certificate(
        normalized,
        method=method,
        objective=objective,
        evaluator_sha256=evaluator_sha256,
    )
    if base["state_count"] > max_states:
        return _finish(
            {
                **base,
                "status": "BLOCKED_STATE_LIMIT",
                "exact_integer_box": False,
                "max_states": max_states,
                "evaluated_states": 0,
                "minimum": None,
                "reason": (
                    f"integer box has {base['state_count']} states, exceeding "
                    f"the fail-closed limit {max_states}"
                ),
            }
        )

    ranges = [range(cell["unresolved"] + 1) for cell in normalized]
    best_number = math.inf
    best_value: float | str = "+inf"
    best_successes: tuple[int, ...] | None = None
    trace = hashlib.sha256()
    evaluated = 0
    for extras in itertools.product(*ranges):
        successes = tuple(
            cell["certified_successes"] + extra
            for cell, extra in zip(normalized, extras, strict=True)
        )
        raw_value = evaluator(successes)
        value = _json_objective(raw_value)
        number = _objective_number(value)
        trace.update(_canonical({"successes": successes, "objective": value}) + b"\n")
        evaluated += 1
        if number < best_number or (
            number == best_number
            and (best_successes is None or successes < best_successes)
        ):
            best_number = number
            best_value = value
            best_successes = successes

    if best_successes is None:  # pragma: no cover - product is never empty
        raise AssertionError("nonempty integer box produced no state")
    allocation = [
        {
            "p": cell["p"],
            "exposure": cell["exposure"],
            "successes": successes,
            "certified_successes": cell["certified_successes"],
            "allocated_unresolved_successes": (
                successes - cell["certified_successes"]
            ),
            "unresolved": cell["unresolved"],
        }
        for cell, successes in zip(normalized, best_successes, strict=True)
    ]
    return _finish(
        {
            **base,
            "status": "COMPLETE",
            "exact_integer_box": True,
            "max_states": max_states,
            "evaluated_states": evaluated,
            "minimum": {"value": best_value, "allocation": allocation},
            "trace_sha256": trace.hexdigest(),
            "reason": None,
        }
    )


def _entries(cells: list[Cell], successes: tuple[int, ...]) -> list[tuple[int, int, int]]:
    return [
        (cell["p"], cell["exposure"], count)
        for cell, count in zip(cells, successes, strict=True)
    ]


def optimize_binomial_cloglog(
    cells: Iterable[Mapping[str, Any]],
    *,
    familywise_alpha: float,
    simultaneous_hypotheses: int,
    max_states: int = 2_000_000,
) -> dict[str, Any]:
    """Exhaustively minimize the profile binomial-cloglog lower endpoint."""
    normalized = normalize_cells(cells)
    familywise_alpha = _plain_json_scalar(
        familywise_alpha, float, "familywise_alpha"
    )
    simultaneous_hypotheses = _plain_json_scalar(
        simultaneous_hypotheses, int, "simultaneous_hypotheses"
    )
    max_states = _plain_json_scalar(max_states, int, "max_states")
    if not 0 < familywise_alpha < 1:
        raise MixedCensoringError("familywise_alpha must lie in (0, 1)")
    if not _plain_int(simultaneous_hypotheses) or simultaneous_hypotheses <= 0:
        raise MixedCensoringError(
            "simultaneous_hypotheses must be a positive integer"
        )

    def evaluate(successes: tuple[int, ...]) -> float | str:
        fit = sensitivity.fit_binomial_cloglog(
            _entries(normalized, successes),
            familywise_alpha=familywise_alpha,
            simultaneous_hypotheses=simultaneous_hypotheses,
        )
        return fit["signed_beta_lower"]

    evaluator_contract = {
        "implementation_sha256": sensitivity.implementation_sha256(),
        "model": sensitivity.BINOMIAL_MODEL,
        "familywise_alpha": familywise_alpha,
        "simultaneous_hypotheses": simultaneous_hypotheses,
    }
    result = exact_box_optimize(
        normalized,
        evaluate,
        method="exhaustive_binomial_cloglog",
        objective="minimum signed_beta_lower",
        evaluator_sha256=_sha256(evaluator_contract),
        max_states=max_states,
    )
    # Bind all numerical parameters without changing the generic certificate.
    result["evaluator_contract"] = evaluator_contract
    result["certificate_sha256"] = _sha256(
        {key: value for key, value in result.items() if key != "certificate_sha256"}
    )
    return result


def _greedy_successes(cells: list[Cell], extra_total: int) -> tuple[int, ...]:
    if not _plain_int(extra_total) or not 0 <= extra_total <= sum(
        cell["unresolved"] for cell in cells
    ):
        raise MixedCensoringError("extra_total lies outside the unresolved box")
    remaining = extra_total
    successes: list[int] = []
    for cell in cells:
        add = min(remaining, cell["unresolved"])
        successes.append(cell["certified_successes"] + add)
        remaining -= add
    if remaining:  # pragma: no cover - validated capacity arithmetic
        raise AssertionError("greedy allocation left unresolved successes")
    return tuple(successes)


def _poisson_candidate_extra_totals(
    cells: list[Cell], *, familywise_alpha: float, simultaneous_hypotheses: int
) -> list[int]:
    xs = [math.log(cell["p"]) for cell in cells]
    base_total = sum(cell["certified_successes"] for cell in cells)
    base_weight = sum(
        cell["certified_successes"] * x
        for cell, x in zip(cells, xs, strict=True)
    )
    width = max(xs) - min(xs)
    tail_alpha = familywise_alpha / (2 * simultaneous_hypotheses)
    radius_constant = width * math.sqrt(math.log(1 / tail_alpha) / 2)

    candidates = {0}
    prefix_extra = 0
    prefix_weight = 0.0
    for cell, x in zip(cells, xs, strict=True):
        capacity = cell["unresolved"]
        if capacity == 0:
            continue
        low_extra = prefix_extra
        high_extra = prefix_extra + capacity
        candidates.update((low_extra, high_extra))
        # On this capacity segment, h(T) = x + c/T - C/sqrt(T).
        c = base_weight + prefix_weight - x * (base_total + prefix_extra)
        if c > 0 and radius_constant > 0:
            stationary_total = (2 * c / radius_constant) ** 2
            stationary_extra = stationary_total - base_total
            if low_extra <= stationary_extra <= high_extra:
                center = math.floor(stationary_extra)
                # The wider guard makes the candidate set stable against a
                # last-bit error in log/sqrt evaluation.
                for value in range(center - 2, center + 4):
                    if low_extra <= value <= high_extra:
                        candidates.add(value)
        prefix_extra = high_extra
        prefix_weight += capacity * x
    return sorted(candidates)


def _poisson_target(
    cells: list[Cell], successes: tuple[int, ...], *, tail_alpha: float
) -> float:
    total = sum(successes)
    if total == 0:
        return -math.inf
    xs = [math.log(cell["p"]) for cell in cells]
    event_mean = sum(
        count * x for count, x in zip(successes, xs, strict=True)
    ) / total
    radius = (max(xs) - min(xs)) * math.sqrt(
        math.log(1 / tail_alpha) / (2 * total)
    )
    return event_mean - radius


def optimize_poisson_hoeffding(
    cells: Iterable[Mapping[str, Any]],
    *,
    familywise_alpha: float,
    simultaneous_hypotheses: int,
) -> dict[str, Any]:
    """Globally minimize the conditional-Poisson Hoeffding lower endpoint."""
    normalized = normalize_cells(cells)
    familywise_alpha = _plain_json_scalar(
        familywise_alpha, float, "familywise_alpha"
    )
    simultaneous_hypotheses = _plain_json_scalar(
        simultaneous_hypotheses, int, "simultaneous_hypotheses"
    )
    if len(normalized) < 2:
        base = _base_certificate(
            normalized,
            method="structural_conditional_poisson",
            objective="minimum simultaneous Hoeffding signed-beta lower endpoint",
            evaluator_sha256=_sha256({"analyze": _module_sha256(analyze)}),
        )
        return _finish(
            {
                **base,
                "status": "BLOCKED_UNIDENTIFIABLE_DESIGN",
                "exact_integer_box": False,
                "evaluated_states": 0,
                "minimum": None,
                "reason": "at least two distinct primes are required",
            }
        )
    if not 0 < familywise_alpha < 1:
        raise MixedCensoringError("familywise_alpha must lie in (0, 1)")
    if not _plain_int(simultaneous_hypotheses) or simultaneous_hypotheses <= 0:
        raise MixedCensoringError(
            "simultaneous_hypotheses must be a positive integer"
        )
    evaluator_contract = {
        "implementation_sha256": _module_sha256(analyze),
        "model": "conditional Poisson with Bonferroni-Hoeffding inversion",
        "familywise_alpha": familywise_alpha,
        "simultaneous_hypotheses": simultaneous_hypotheses,
        "optimization_proof": (
            "exchange smallest log(p) first; each capacity segment has one "
            "stationary point for x+c/T-C/sqrt(T)"
        ),
    }
    base = _base_certificate(
        normalized,
        method="structural_conditional_poisson",
        objective="minimum simultaneous Hoeffding signed-beta lower endpoint",
        evaluator_sha256=_sha256(evaluator_contract),
    )
    candidates = _poisson_candidate_extra_totals(
        normalized,
        familywise_alpha=familywise_alpha,
        simultaneous_hypotheses=simultaneous_hypotheses,
    )
    tail_alpha = familywise_alpha / (2 * simultaneous_hypotheses)
    scored: list[tuple[float, tuple[int, ...], int]] = []
    for extra_total in candidates:
        successes = _greedy_successes(normalized, extra_total)
        scored.append(
            (
                _poisson_target(normalized, successes, tail_alpha=tail_alpha),
                successes,
                extra_total,
            )
        )
    target, successes, extra_total = min(scored, key=lambda item: (item[0], item[1]))
    profile = analyze.poisson_profile(
        _entries(normalized, successes),
        familywise_alpha=familywise_alpha,
        simultaneous_hypotheses=simultaneous_hypotheses,
    )
    lower = profile["confidence_interval"]["lower"]
    value: float | str = "-inf" if lower is None else lower
    allocation = [
        {
            "p": cell["p"],
            "exposure": cell["exposure"],
            "successes": count,
            "certified_successes": cell["certified_successes"],
            "allocated_unresolved_successes": count - cell["certified_successes"],
            "unresolved": cell["unresolved"],
        }
        for cell, count in zip(normalized, successes, strict=True)
    ]
    return _finish(
        {
            **base,
            "status": "COMPLETE",
            "exact_integer_box": True,
            "evaluated_states": len(scored),
            "candidate_extra_totals": candidates,
            "minimum": {
                "value": _json_objective(value),
                "allocation": allocation,
                "extra_successes": extra_total,
                "lower_target_log_prime_mean": _json_objective(target),
            },
            "evaluator_contract": evaluator_contract,
            "profile_at_minimizer": profile,
            "reason": None,
        }
    )


def _cluster_certificate_base(
    rows: list[ClusterRow],
    *,
    series: Mapping[str, Any],
    endpoint: str,
    denominator: str,
    input_rowset_sha256: str,
    evaluator_contract: Mapping[str, Any],
    cluster_replicates: int,
    cluster_seed: str,
    derived_cluster_seed: str,
) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "method": "exact_nested_cluster_bootstrap_cloglog",
        "objective": "minimum cluster-bootstrap signed-beta lower endpoint",
        "cluster_rows": rows,
        "cluster_rowset_sha256": _sha256(rows),
        "input_rowset_sha256": input_rowset_sha256,
        "series": dict(series),
        "series_key": [series[field] for field in analyze.SERIES_FIELDS],
        "endpoint": endpoint,
        "denominator": denominator,
        "box_sha256": _sha256(
            [
                {
                    "row_id": row["row_id"],
                    "certified_successes": row["certified_successes"],
                    "unresolved": row["unresolved"],
                }
                for row in rows
            ]
        ),
        "implementation_sha256": implementation_sha256(),
        "evaluator_sha256": _sha256(evaluator_contract),
        "evaluator_contract": dict(evaluator_contract),
        "cluster_keys": list(FROZEN_CLUSTER_KEYS),
        "cluster_replicates": cluster_replicates,
        "frozen_cluster_replicates": FROZEN_CLUSTER_REPLICATES,
        "frozen_replicates_satisfied": (
            cluster_replicates == FROZEN_CLUSTER_REPLICATES
        ),
        "cluster_seed": cluster_seed,
        "derived_cluster_seed": derived_cluster_seed,
        "state_count": math.prod(row["unresolved"] + 1 for row in rows),
        # This producer-side module is not integrated into the signed
        # robustness artifact gate.  Exact bounded coverage is recorded below
        # without promoting it to a production verdict.
        "production_eligible": False,
    }


def _iter_bootstrap_plan(
    rows: list[ClusterRow], *, cluster_replicates: int, cluster_seed: str
) -> Iterable[tuple[int, ...]]:
    """Stream row multiplicities for every nested bootstrap replicate."""

    by_bits: dict[
        int, dict[int, dict[tuple[str, str], list[int]]]
    ] = {}
    for index, row in enumerate(rows):
        by_prime = by_bits.setdefault(row["bits"], {}).setdefault(row["p"], {})
        by_prime.setdefault((row["source_id"], row["curve_id"]), []).append(
            index
        )
    rng = random.Random(cluster_seed)
    for _ in range(cluster_replicates):
        multiplicities = [0] * len(rows)
        for bits in sorted(by_bits):
            prime_map = by_bits[bits]
            primes = sorted(prime_map)
            for _ in range(len(primes)):
                prime = primes[rng.randrange(len(primes))]
                cluster_map = prime_map[prime]
                cluster_keys = sorted(cluster_map)
                for _ in range(len(cluster_keys)):
                    selected_key = cluster_keys[rng.randrange(len(cluster_keys))]
                    for row_index in cluster_map[selected_key]:
                        multiplicities[row_index] += 1
        yield tuple(multiplicities)


def _bootstrap_plan_sha256(
    rows: list[ClusterRow], *, cluster_replicates: int, cluster_seed: str
) -> str:
    digest = hashlib.sha256()
    for multiplicities in _iter_bootstrap_plan(
        rows,
        cluster_replicates=cluster_replicates,
        cluster_seed=cluster_seed,
    ):
        digest.update(_canonical(multiplicities) + b"\n")
    return digest.hexdigest()


def _entries_from_cluster_plan(
    rows: list[ClusterRow],
    successes: tuple[int, ...],
    multiplicities: tuple[int, ...],
) -> list[tuple[int, int, int]]:
    by_prime: dict[int, list[int]] = {}
    for row, count, multiplicity in zip(
        rows, successes, multiplicities, strict=True
    ):
        if multiplicity == 0:
            continue
        aggregate = by_prime.setdefault(row["p"], [0, 0])
        aggregate[0] += multiplicity * row["exposure"]
        aggregate[1] += multiplicity * count
    return [
        (prime, by_prime[prime][0], by_prime[prime][1])
        for prime in sorted(by_prime)
    ]


def _nested_bootstrap_lower(
    rows: list[ClusterRow],
    successes: tuple[int, ...],
    *,
    familywise_alpha: float,
    simultaneous_hypotheses: int,
    cluster_replicates: int,
    derived_cluster_seed: str,
) -> tuple[float | str, str]:
    values: list[float | str] = []
    trace = hashlib.sha256()
    for multiplicities in _iter_bootstrap_plan(
        rows,
        cluster_replicates=cluster_replicates,
        cluster_seed=derived_cluster_seed,
    ):
        entries = _entries_from_cluster_plan(rows, successes, multiplicities)
        fit = sensitivity.fit_binomial_cloglog(
            entries,
            familywise_alpha=familywise_alpha,
            simultaneous_hypotheses=simultaneous_hypotheses,
        )
        beta_hat: float | str = (
            fit["beta_hat"]
            if fit["identifiable"] and type(fit["beta_hat"]) is float
            else "-inf"
        )
        values.append(beta_hat)
        trace.update(
            _canonical(
                {
                    "multiplicities": multiplicities,
                    "entries": entries,
                    "beta_hat": beta_hat,
                }
            )
            + b"\n"
        )
    tail_probability = familywise_alpha / (2 * simultaneous_hypotheses)
    return sensitivity._bootstrap_lower(values, tail_probability), trace.hexdigest()


def optimize_nested_cluster_bootstrap(
    rows: Iterable[Mapping[str, Any]],
    *,
    series: Mapping[str, Any],
    endpoint: str,
    denominator: str,
    input_rowset_sha256: str,
    familywise_alpha: float,
    simultaneous_hypotheses: int,
    cluster_replicates: int,
    cluster_seed: str,
    max_states: int = 100_000,
    max_bootstrap_evaluations: int = 5_000_000,
    max_plan_entries: int = 20_000_000,
    max_row_visits: int = 100_000_000,
) -> dict[str, Any]:
    """Minimize a nested-cluster percentile as a non-production control.

    The complete bootstrap sampling plan is outcome-independent and is frozen
    from ``cluster_seed`` before the first allocation is evaluated.  The exact
    path covers every row-level integer allocation and every planned replicate.
    If either finite product exceeds its declared ceiling, this function stops
    before constructing the bootstrap plan; it never replaces cluster rows by
    per-prime totals or uniform corner allocations.
    """

    normalized = normalize_cluster_rows(rows)
    normalized_series, series_key = _validate_series(series)
    endpoint = _plain_json_scalar(endpoint, str, "endpoint")
    denominator = _plain_json_scalar(denominator, str, "denominator")
    input_rowset_sha256 = _plain_json_scalar(
        input_rowset_sha256, str, "input_rowset_sha256"
    )
    familywise_alpha = _plain_json_scalar(
        familywise_alpha, float, "familywise_alpha"
    )
    simultaneous_hypotheses = _plain_json_scalar(
        simultaneous_hypotheses, int, "simultaneous_hypotheses"
    )
    cluster_replicates = _plain_json_scalar(
        cluster_replicates, int, "cluster_replicates"
    )
    cluster_seed = _plain_json_scalar(cluster_seed, str, "cluster_seed")
    max_states = _plain_json_scalar(max_states, int, "max_states")
    max_bootstrap_evaluations = _plain_json_scalar(
        max_bootstrap_evaluations, int, "max_bootstrap_evaluations"
    )
    max_plan_entries = _plain_json_scalar(
        max_plan_entries, int, "max_plan_entries"
    )
    max_row_visits = _plain_json_scalar(
        max_row_visits, int, "max_row_visits"
    )
    if endpoint not in ENDPOINTS:
        raise MixedCensoringError(f"unsupported endpoint {endpoint!r}")
    if denominator not in DENOMINATORS:
        raise MixedCensoringError(f"unsupported denominator {denominator!r}")
    input_rowset_sha256 = _lower_hex_digest(
        input_rowset_sha256, "input_rowset_sha256"
    )
    if not 0 < familywise_alpha < 1:
        raise MixedCensoringError("familywise_alpha must lie in (0, 1)")
    if not _plain_int(simultaneous_hypotheses) or simultaneous_hypotheses <= 0:
        raise MixedCensoringError(
            "simultaneous_hypotheses must be a positive integer"
        )
    if not _plain_int(cluster_replicates) or cluster_replicates <= 0:
        raise MixedCensoringError("cluster_replicates must be a positive integer")
    if not cluster_seed or len(cluster_seed) > 512:
        raise MixedCensoringError(
            "cluster_seed must be a nonempty string of at most 512 characters"
        )
    for name, value in (
        ("max_states", max_states),
        ("max_bootstrap_evaluations", max_bootstrap_evaluations),
        ("max_plan_entries", max_plan_entries),
        ("max_row_visits", max_row_visits),
    ):
        if not _plain_int(value) or value <= 0:
            raise MixedCensoringError(f"{name} must be a positive integer")

    derived_cluster_seed = f"{cluster_seed}|{series_key!r}"
    binding_mode = "control_cluster_rows"
    production_parameters_satisfied = False

    evaluator_contract = {
        "sensitivity_implementation_sha256": sensitivity.implementation_sha256(),
        "model": sensitivity.BINOMIAL_MODEL,
        "bootstrap_method": "prime-within-bits then source/curve-within-prime",
        "cluster_keys": list(FROZEN_CLUSTER_KEYS),
        "familywise_alpha": familywise_alpha,
        "simultaneous_hypotheses": simultaneous_hypotheses,
        "tail_probability": familywise_alpha / (2 * simultaneous_hypotheses),
        "cluster_replicates": cluster_replicates,
        "cluster_seed": cluster_seed,
        "derived_cluster_seed": derived_cluster_seed,
        "series": normalized_series,
        "endpoint": endpoint,
        "denominator": denominator,
        "input_rowset_sha256": input_rowset_sha256,
        "binding_mode": binding_mode,
    }
    base = _cluster_certificate_base(
        normalized,
        series=normalized_series,
        endpoint=endpoint,
        denominator=denominator,
        input_rowset_sha256=input_rowset_sha256,
        evaluator_contract=evaluator_contract,
        cluster_replicates=cluster_replicates,
        cluster_seed=cluster_seed,
        derived_cluster_seed=derived_cluster_seed,
    )
    minimum_replicates = sensitivity.minimum_cluster_replicates(
        familywise_alpha, simultaneous_hypotheses
    )
    evaluation_count = base["state_count"] * cluster_replicates
    plan_entries = cluster_replicates * len(normalized)
    row_visits = evaluation_count * len(normalized)
    common = {
        **base,
        "binding_mode": binding_mode,
        "production_parameters_satisfied": production_parameters_satisfied,
        "minimum_cluster_replicates": minimum_replicates,
        "max_states": max_states,
        "max_bootstrap_evaluations": max_bootstrap_evaluations,
        "max_plan_entries": max_plan_entries,
        "max_row_visits": max_row_visits,
        "required_plan_entries": plan_entries,
        "required_bootstrap_evaluations": evaluation_count,
        "required_row_visits": row_visits,
    }

    if cluster_replicates < minimum_replicates:
        return _finish(
            {
                **common,
                "status": "BLOCKED_TAIL_RESOLUTION",
                "exact_nested_cluster_box": False,
                "evaluated_states": 0,
                "evaluated_bootstrap_fits": 0,
                "minimum": None,
                "reason": (
                    f"need at least {minimum_replicates} replicates for one "
                    "Bonferroni-tail order statistic"
                ),
                "production_blockers": [
                    "frozen cluster-bootstrap tail resolution not met",
                    "module is not integrated into the signed robustness gate",
                ],
            }
        )
    if plan_entries > max_plan_entries:
        return _finish(
            {
                **common,
                "status": "BLOCKED_BOOTSTRAP_PLAN_LIMIT",
                "exact_nested_cluster_box": False,
                "evaluated_states": 0,
                "evaluated_bootstrap_fits": 0,
                "minimum": None,
                "reason": (
                    f"streamed bootstrap plan contains {plan_entries} row "
                    f"multiplicity entries, exceeding the ceiling "
                    f"{max_plan_entries}; stopped before plan generation"
                ),
                "production_blockers": [
                    "bootstrap plan processing/memory budget not allocated",
                    "module is not integrated into the signed robustness gate",
                ],
            }
        )
    if base["state_count"] > max_states:
        return _finish(
            {
                **common,
                "status": "BLOCKED_NESTED_STATE_LIMIT",
                "exact_nested_cluster_box": False,
                "evaluated_states": 0,
                "evaluated_bootstrap_fits": 0,
                "minimum": None,
                "reason": (
                    f"row-level allocation box has {base['state_count']} states, "
                    f"exceeding the exact ceiling {max_states}; no valid "
                    "aggregate or corner substitute exists"
                ),
                "production_blockers": [
                    "no proved monotone bound for nested bootstrap percentile",
                    "module is not integrated into the signed robustness gate",
                ],
            }
        )
    if evaluation_count > max_bootstrap_evaluations:
        return _finish(
            {
                **common,
                "status": "BLOCKED_BOOTSTRAP_EVALUATION_LIMIT",
                "exact_nested_cluster_box": False,
                "evaluated_states": 0,
                "evaluated_bootstrap_fits": 0,
                "minimum": None,
                "reason": (
                    f"exact nested evaluation requires {evaluation_count} fits, "
                    f"exceeding the ceiling {max_bootstrap_evaluations}; no "
                    "unproved pruning or per-prime aggregation was used"
                ),
                "production_blockers": [
                    "exact nested bootstrap fit budget not allocated",
                    "module is not integrated into the signed robustness gate",
                ],
            }
        )
    if row_visits > max_row_visits:
        return _finish(
            {
                **common,
                "status": "BLOCKED_ROW_VISIT_LIMIT",
                "exact_nested_cluster_box": False,
                "evaluated_states": 0,
                "evaluated_bootstrap_fits": 0,
                "minimum": None,
                "reason": (
                    f"exact nested evaluation requires {row_visits} row visits "
                    f"({base['state_count']} states x {cluster_replicates} "
                    f"replicates x {len(normalized)} rows), exceeding the "
                    f"ceiling {max_row_visits}; stopped before plan generation"
                ),
                "production_blockers": [
                    "exact nested bootstrap row-visit budget not allocated",
                    "module is not integrated into the signed robustness gate",
                ],
            }
        )

    plan_sha256 = _bootstrap_plan_sha256(
        normalized,
        cluster_replicates=cluster_replicates,
        cluster_seed=derived_cluster_seed,
    )
    ranges = [range(row["unresolved"] + 1) for row in normalized]
    best_number = math.inf
    best_value: float | str = "+inf"
    best_successes: tuple[int, ...] | None = None
    best_trace_sha256: str | None = None
    allocation_trace = hashlib.sha256()
    evaluated_states = 0
    for extras in itertools.product(*ranges):
        successes = tuple(
            row["certified_successes"] + extra
            for row, extra in zip(normalized, extras, strict=True)
        )
        raw_value, bootstrap_trace_sha256 = _nested_bootstrap_lower(
            normalized,
            successes,
            familywise_alpha=familywise_alpha,
            simultaneous_hypotheses=simultaneous_hypotheses,
            cluster_replicates=cluster_replicates,
            derived_cluster_seed=derived_cluster_seed,
        )
        value = _json_objective(raw_value)
        number = _objective_number(value)
        allocation_trace.update(
            _canonical(
                {
                    "successes": successes,
                    "objective": value,
                    "bootstrap_trace_sha256": bootstrap_trace_sha256,
                }
            )
            + b"\n"
        )
        evaluated_states += 1
        if number < best_number or (
            number == best_number
            and (best_successes is None or successes < best_successes)
        ):
            best_number = number
            best_value = value
            best_successes = successes
            best_trace_sha256 = bootstrap_trace_sha256

    if best_successes is None:  # pragma: no cover - nonempty product
        raise AssertionError("nonempty nested allocation box produced no state")
    allocation = [
        {
            "row_id": row["row_id"],
            "bits": row["bits"],
            "p": row["p"],
            "source_id": row["source_id"],
            "curve_id": row["curve_id"],
            "exposure": row["exposure"],
            "successes": count,
            "certified_successes": row["certified_successes"],
            "allocated_unresolved_successes": count
            - row["certified_successes"],
            "unresolved": row["unresolved"],
        }
        for row, count in zip(normalized, best_successes, strict=True)
    ]
    blockers = ["module is not integrated into the signed robustness gate"]
    if not production_parameters_satisfied:
        blockers.insert(0, "exact frozen production parameters not used")
    return _finish(
        {
            **common,
            "status": "COMPLETE_BOUNDED_CONTROL",
            "exact_nested_cluster_box": True,
            "evaluated_states": evaluated_states,
            "evaluated_bootstrap_fits": evaluation_count,
            "bootstrap_plan_sha256": plan_sha256,
            "allocation_trace_sha256": allocation_trace.hexdigest(),
            "minimum": {
                "value": best_value,
                "allocation": allocation,
                "bootstrap_trace_sha256": best_trace_sha256,
            },
            "reason": None,
            "production_blockers": blockers,
        }
    )


def optimize_nested_cluster_bootstrap_rows(
    rows: Iterable[Mapping[str, Any]],
    *,
    endpoint: str,
    denominator: str,
    familywise_alpha: float,
    simultaneous_hypotheses: int,
    cluster_replicates: int,
    cluster_seed: str,
    max_states: int = 100_000,
    max_bootstrap_evaluations: int = 5_000_000,
    max_plan_entries: int = 20_000_000,
    max_row_visits: int = 100_000_000,
) -> dict[str, Any]:
    """Strict analysis-row entry point with derived series/rowset bindings."""

    plain_rows = _plain_json_list(rows, "analysis_rows")
    endpoint = _plain_json_scalar(endpoint, str, "endpoint")
    denominator = _plain_json_scalar(denominator, str, "denominator")
    familywise_alpha = _plain_json_scalar(
        familywise_alpha, float, "familywise_alpha"
    )
    simultaneous_hypotheses = _plain_json_scalar(
        simultaneous_hypotheses, int, "simultaneous_hypotheses"
    )
    cluster_replicates = _plain_json_scalar(
        cluster_replicates, int, "cluster_replicates"
    )
    cluster_seed = _plain_json_scalar(cluster_seed, str, "cluster_seed")
    max_states = _plain_json_scalar(max_states, int, "max_states")
    max_bootstrap_evaluations = _plain_json_scalar(
        max_bootstrap_evaluations, int, "max_bootstrap_evaluations"
    )
    max_plan_entries = _plain_json_scalar(
        max_plan_entries, int, "max_plan_entries"
    )
    max_row_visits = _plain_json_scalar(
        max_row_visits, int, "max_row_visits"
    )
    cluster_rows, series, rowset_sha256 = cluster_rows_from_analysis_rows(
        plain_rows,
        endpoint=endpoint,
        denominator=denominator,
    )
    control = optimize_nested_cluster_bootstrap(
        cluster_rows,
        series=series,
        endpoint=endpoint,
        denominator=denominator,
        input_rowset_sha256=rowset_sha256,
        familywise_alpha=familywise_alpha,
        simultaneous_hypotheses=simultaneous_hypotheses,
        cluster_replicates=cluster_replicates,
        cluster_seed=cluster_seed,
        max_states=max_states,
        max_bootstrap_evaluations=max_bootstrap_evaluations,
        max_plan_entries=max_plan_entries,
        max_row_visits=max_row_visits,
    )
    analysis_replay = {
        "validator": "analyze.validate_row",
        "analyze_implementation_sha256": _module_sha256(analyze),
        "series_fields": list(analyze.SERIES_FIELDS),
        "series_key": [series[field] for field in analyze.SERIES_FIELDS],
        "endpoint": endpoint,
        "denominator": denominator,
        "input_rowset_sha256": rowset_sha256,
        "cluster_rowset_sha256": control["cluster_rowset_sha256"],
    }
    production_parameters_satisfied = (
        familywise_alpha == FROZEN_FAMILYWISE_ALPHA
        and simultaneous_hypotheses == FROZEN_SIMULTANEOUS_HYPOTHESES
        and cluster_replicates == FROZEN_CLUSTER_REPLICATES
        and cluster_seed == FROZEN_CLUSTER_SEED
        and series["stage"] in analyze.INFERENCE_STAGES
    )
    annotated = dict(control)
    annotated.pop("certificate_sha256")
    evaluator_contract = dict(control["evaluator_contract"])
    evaluator_contract["binding_mode"] = "validated_analysis_rows"
    evaluator_contract["analysis_replay"] = dict(analysis_replay)
    annotated["evaluator_contract"] = evaluator_contract
    annotated["evaluator_sha256"] = _sha256(evaluator_contract)
    annotated["binding_mode"] = "validated_analysis_rows"
    annotated["analysis_replay"] = dict(analysis_replay)
    annotated["production_parameters_satisfied"] = (
        production_parameters_satisfied
    )
    annotated["production_eligible"] = False
    parameter_blocker = "exact frozen production parameters not used"
    blockers = [
        blocker
        for blocker in control["production_blockers"]
        if blocker != parameter_blocker
    ]
    if not production_parameters_satisfied:
        blockers.insert(0, parameter_blocker)
    annotated["production_blockers"] = blockers
    return _finish(annotated)


def cluster_bootstrap_fail_closed(
    cells: Iterable[Mapping[str, Any]],
    *,
    evaluator_sha256: str,
) -> dict[str, Any]:
    """Record why aggregate per-prime intervals cannot certify a cluster bound."""
    normalized = normalize_cells(cells)
    base = _base_certificate(
        normalized,
        method="cluster_bootstrap_cloglog",
        objective="minimum cluster-bootstrap signed-beta lower endpoint",
        evaluator_sha256=evaluator_sha256,
    )
    return _finish(
        {
            **base,
            "status": "BLOCKED_NEEDS_ROW_LEVEL_CLUSTER_ALLOCATION",
            "exact_integer_box": False,
            "evaluated_states": 0,
            "minimum": None,
            "reason": (
                "per-prime success totals do not determine which source/curve "
                "clusters receive unresolved successes; a nested row-level "
                "adversarial allocation is required"
            ),
        }
    )


def verify_certificate_digest(certificate: Mapping[str, Any]) -> bool:
    """Verify the self-digest and implementation binding of a certificate."""
    try:
        copied = _plain_json_dict(certificate, "certificate")
    except MixedCensoringError:
        return False
    claimed = copied.pop("certificate_sha256", None)
    return (
        copied.get("schema") == SCHEMA
        and copied.get("implementation_sha256") == implementation_sha256()
        and type(claimed) is str
        and claimed == _sha256(copied)
    )

