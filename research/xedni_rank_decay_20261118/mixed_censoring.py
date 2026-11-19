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
  state limit.  Cluster-bootstrap optimization fails closed unless a future
  row-level implementation can allocate unresolved outcomes inside clusters;
  per-prime counts alone do not determine a cluster bootstrap statistic.

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
from typing import Any

import analyze
import sensitivity


SCHEMA = "xedni.mixed-censoring/v1"
Cell = dict[str, int]
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


def _plain_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def normalize_cells(cells: Iterable[Mapping[str, Any]]) -> list[Cell]:
    """Validate, aggregate duplicate primes, and return cells in prime order."""
    aggregated: dict[int, Cell] = {}
    required = {"p", "exposure", "certified_successes", "unresolved"}
    for index, source in enumerate(cells):
        if not isinstance(source, Mapping) or set(source) != required:
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


def integer_box_state_count(cells: Iterable[Mapping[str, Any]]) -> int:
    normalized = normalize_cells(cells)
    return math.prod(cell["unresolved"] + 1 for cell in normalized)


def _objective_number(value: float | str) -> float:
    if value == "-inf":
        return -math.inf
    if value == "+inf":
        return math.inf
    if isinstance(value, bool) or not isinstance(value, (int, float)):
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
    if not isinstance(method, str) or not method:
        raise MixedCensoringError("method must be a nonempty string")
    if not isinstance(objective, str) or not objective:
        raise MixedCensoringError("objective must be a nonempty string")
    if (
        not isinstance(evaluator_sha256, str)
        or len(evaluator_sha256) != 64
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
    if not isinstance(certificate, Mapping):
        return False
    copied = dict(certificate)
    claimed = copied.pop("certificate_sha256", None)
    return (
        copied.get("schema") == SCHEMA
        and copied.get("implementation_sha256") == implementation_sha256()
        and isinstance(claimed, str)
        and claimed == _sha256(copied)
    )

