#!/usr/bin/env python3
"""Exact prospective power/cost arithmetic for the Xedni decay program.

This module deliberately separates an expected-event scale calculation from a
powered and resourced execution allocation.  The checked-in manifest remains
``UNALLOCATED`` until a concrete resource commitment, checkpoint transport,
licensed Magma runtime, and the other production gates are supplied.

The reference rate is ``q(2^b) = kappa * 2^(b*beta)`` with ``kappa=1`` and
``beta`` in ``{-1,-3/4,-1/2}``.  Since every frozen b-bit prime is smaller
than ``2^b`` and beta is negative, using ``2^b`` is conservative for the
expected count under this reference model.  It is not a theorem-derived lower
bound on the true event rate.
"""

from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
import math
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any


SCHEMA = "xedni.rank-decay-power-allocation/v1"
PRODUCTION_READY = False
HERE = Path(__file__).resolve().parent
PRIME_MANIFEST_PATH = HERE / "PRIMES.json"
FAMILYWISE_ALPHA = Fraction(1, 20)
SIMULTANEOUS_PROFILES = 4320
BOOTSTRAP_REPLICATES = 172800
BITS = tuple(range(16, 33, 2))
INFERENCE_BITS = (20, 22, 24)
MATRIX_BITS = (16, 18, 20, 22, 24)
STAGES = ("discovery", "replication")
CURVE_FAMILIES = 2
LIFT_STRATEGIES = 3
PRIMARY_LOCAL_ARMS = 3
EXECUTABLE_R_VALUES = 5
FACTOR_CELLS = CURVE_FAMILIES * LIFT_STRATEGIES * PRIMARY_LOCAL_ARMS * EXECUTABLE_R_VALUES
PROTOCOL_MINIMUM_OBSERVED_USEFUL_EVENTS = 30
REFERENCE_EXPECTED_EVENTS_AT_TOP_BIT = 30
EVENT_BUCKETS = len(STAGES) * len(INFERENCE_BITS)
OPTIONAL_EXPECTED_EVENTS_PER_STAGE_BIT = 5
BETAS = (Fraction(-1, 1), Fraction(-3, 4), Fraction(-1, 2))
CALIBRATION_ROWS = 1080
PARI_TIMEOUT_SECONDS = 60 + 300
MAGMA_TIMEOUT_SECONDS = 300 + 1800
RANK_TIMEOUT_SECONDS_PER_ROW = PARI_TIMEOUT_SECONDS + MAGMA_TIMEOUT_SECONDS
AVAILABLE_LOGICAL_CPUS = 5


class AllocationError(ValueError):
    """Invalid power/allocation input."""


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


def prime_slots() -> dict[int, list[dict[str, int]]]:
    try:
        manifest = json.loads(PRIME_MANIFEST_PATH.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise AllocationError(f"cannot read PRIMES.json: {error}") from error
    rows = manifest.get("primes") if isinstance(manifest, dict) else None
    if not isinstance(rows, list):
        raise AllocationError("PRIMES.json has no prime row list")
    result: dict[int, list[dict[str, int]]] = {bits: [] for bits in MATRIX_BITS}
    for row in rows:
        if not isinstance(row, dict) or set(row) != {
            "bits",
            "slot",
            "prime",
            "hash_candidate",
            "downward_odd_steps",
        }:
            raise AllocationError("PRIMES.json row schema mismatch")
        bits, slot, prime = row["bits"], row["slot"], row["prime"]
        if bits in result:
            if (
                isinstance(slot, bool)
                or not isinstance(slot, int)
                or slot not in (0, 1, 2)
                or isinstance(prime, bool)
                or not isinstance(prime, int)
            ):
                raise AllocationError("PRIMES.json slot/prime mismatch")
            result[bits].append({"slot": slot, "prime": prime})
    for bits, selected in result.items():
        selected.sort(key=lambda row: row["slot"])
        if [row["slot"] for row in selected] != [0, 1, 2]:
            raise AllocationError(f"PRIMES.json missing slots at {bits} bits")
    return result


def split_integer_across_slots(total: int, slots: int = 3) -> list[int]:
    total = _plain_nonnegative_int(total, "total")
    slots = _plain_nonnegative_int(slots, "slots")
    if slots == 0:
        raise AllocationError("slots must be positive")
    quotient, remainder = divmod(total, slots)
    return [quotient + (index < remainder) for index in range(slots)]


def _plain_nonnegative_int(value: Any, context: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise AllocationError(f"{context} must be a nonnegative integer")
    return value


def ceil_nth_root(value: int, degree: int) -> int:
    """Return the exact least integer n with n**degree >= value."""
    value = _plain_nonnegative_int(value, "value")
    degree = _plain_nonnegative_int(degree, "degree")
    if degree == 0:
        raise AllocationError("degree must be positive")
    if value <= 1:
        return value
    low = 0
    high = 1 << ((value.bit_length() + degree - 1) // degree)
    while low + 1 < high:
        middle = (low + high) // 2
        if middle**degree >= value:
            high = middle
        else:
            low = middle
    return high


def trials_for_expected_events(bits: int, beta: Fraction, events: int) -> int:
    """Exact ceil(events / q(2**bits)) for kappa=1 and negative beta."""
    bits = _plain_nonnegative_int(bits, "bits")
    events = _plain_nonnegative_int(events, "events")
    if bits == 0 or events == 0:
        return events
    if not isinstance(beta, Fraction) or beta >= 0:
        raise AllocationError("beta must be a negative Fraction")
    exponent_numerator = (-beta.numerator) * bits
    denominator = beta.denominator
    radicand = (events**denominator) << exponent_numerator
    return ceil_nth_root(radicand, denominator)


def beta_text(beta: Fraction) -> str:
    return f"{beta.numerator}/{beta.denominator}"


def rational_record(value: Fraction) -> dict[str, int | str]:
    with localcontext() as context:
        context.prec = 20
        decimal = Decimal(value.numerator) / Decimal(value.denominator)
    return {
        "numerator": value.numerator,
        "denominator": value.denominator,
        "decimal": format(decimal, ".12g"),
    }


def seconds_record(seconds: int, workers: int) -> dict[str, Any]:
    seconds = _plain_nonnegative_int(seconds, "seconds")
    workers = _plain_nonnegative_int(workers, "workers")
    if workers == 0:
        raise AllocationError("workers must be positive")
    ideal_wall = Fraction(seconds, workers)
    return {
        "worker_seconds": seconds,
        "worker_hours": rational_record(Fraction(seconds, 3600)),
        "ideal_wall_seconds_at_workers": rational_record(ideal_wall),
        "ideal_wall_hours_at_workers": rational_record(ideal_wall / 3600),
        "ideal_wall_days_at_workers": rational_record(ideal_wall / 86400),
        "workers": workers,
        "scope": "rank timeout ceiling only; excludes all other charged work",
    }


def expected_count_allocation(beta: Fraction) -> dict[str, Any]:
    if beta not in BETAS:
        raise AllocationError("beta is not a frozen scenario")
    buckets = []
    rows_per_factor_cell_stage = 0
    high_bit_rows_per_factor_cell_stage = 0
    for bits in MATRIX_BITS:
        rows = trials_for_expected_events(
            bits, beta, OPTIONAL_EXPECTED_EVENTS_PER_STAGE_BIT
        )
        rows_per_factor_cell_stage += rows
        if bits in INFERENCE_BITS:
            high_bit_rows_per_factor_cell_stage += rows
        buckets.append(
            {
                "bits": bits,
                "reference_prime_scale": f"2^{bits}",
                "target_expected_events_per_factor_cell_stage": OPTIONAL_EXPECTED_EVENTS_PER_STAGE_BIT,
                "rows_per_factor_cell_stage": rows,
                "rate_expression": f"2^({bits}*{beta_text(beta)})",
            }
        )
    rows_per_factor_cell_both_stages = rows_per_factor_cell_stage * len(STAGES)
    total_rows = rows_per_factor_cell_both_stages * FACTOR_CELLS
    timeout_seconds = total_rows * RANK_TIMEOUT_SECONDS_PER_ROW
    return {
        "beta": beta_text(beta),
        "kappa": 1,
        "allocation_kind": "OPTIONAL_STRONGER_FULL_FACTORIAL_EXPECTED_EVENT_SCALE",
        "stages_with_identical_exposure_targets": list(STAGES),
        "matrix_bits": list(MATRIX_BITS),
        "buckets": buckets,
        "rows_per_factor_cell_per_stage": rows_per_factor_cell_stage,
        "rows_per_factor_cell_both_stages": rows_per_factor_cell_both_stages,
        "high_bit_rows_per_factor_cell_per_stage": high_bit_rows_per_factor_cell_stage,
        "total_factor_cells": FACTOR_CELLS,
        "total_rows_all_factor_cells_both_stages_if_executed": total_rows,
        "optional_expected_events_per_factor_cell_all_bits_combined_stages": (
            OPTIONAL_EXPECTED_EVENTS_PER_STAGE_BIT * len(MATRIX_BITS) * len(STAGES)
        ),
        "optional_expected_high_bit_events_per_factor_cell_combined_stages": (
            OPTIONAL_EXPECTED_EVENTS_PER_STAGE_BIT
            * len(INFERENCE_BITS)
            * len(STAGES)
        ),
        "rank_timeout_ceiling": seconds_record(timeout_seconds, AVAILABLE_LOGICAL_CPUS),
        "status": "SCALE_ONLY",
        "scope_warning": (
            "This allocates the expected-event scale to every one of 90 factor cells. "
            "It is stronger than the protocol observation rule and is not the committed design."
        ),
        "not_powered_reason": (
            "Thirty expected events does not fix the probability of observing thirty, "
            "the intercept kappa is not theorem-bounded, and cluster/censoring power is unspecified."
        ),
    }


def execution_matrix(expected_allocations: list[dict[str, Any]]) -> dict[str, Any]:
    """Bind scale arithmetic to available prime slots without inventing resources.

    The frozen ``PRIMES.json`` names discovery slots.  Protocol requires fresh
    replication primes, and no such manifest exists, so replication is an
    exact exposure requirement with unbound slot labels rather than a silent
    reuse of discovery primes.
    """
    slots_by_bits = prime_slots()
    by_beta = {allocation["beta"]: allocation for allocation in expected_allocations}
    exposure_rows = []
    for bits in MATRIX_BITS:
        scenarios = []
        for beta, allocation in by_beta.items():
            bucket = next(
                item for item in allocation["buckets"] if item["bits"] == bits
            )
            total = bucket["rows_per_factor_cell_stage"]
            split = split_integer_across_slots(total)
            scenarios.append(
                {
                    "beta": beta,
                    "rows_per_factor_cell_stage": total,
                    "trials_per_factor_cell_stage_by_slot": split,
                    "unique_sources_per_curve_family_by_slot": split,
                    "unique_sources_all_curve_families_by_slot": [
                        CURVE_FAMILIES * trials for trials in split
                    ],
                    "factor_rows_all_cells_by_slot": [
                        FACTOR_CELLS * trials for trials in split
                    ],
                    "source_index_stop_exclusive_per_curve_family_by_slot": split,
                    "status": "OPTIONAL_SCALE_ONLY_UNALLOCATED",
                }
            )
        exposure_rows.append({"bits": bits, "scenarios": scenarios})

    discovery_bindings = [
        {
            "bits": bits,
            "slot_primes": [row["prime"] for row in slots_by_bits[bits]],
        }
        for bits in MATRIX_BITS
    ]
    replication_bindings = [
        {"bits": bits, "slot_primes": [None, None, None]} for bits in MATRIX_BITS
    ]

    return {
        "stages_with_identical_exposure_targets": list(STAGES),
        "bits": list(MATRIX_BITS),
        "slot_order_for_all_arrays": [0, 1, 2],
        "slot_split_rule": "quotient plus one for the lowest remainder slots",
        "source_sharing": {
            "rows_per_unique_source": (
                LIFT_STRATEGIES * PRIMARY_LOCAL_ARMS * EXECUTABLE_R_VALUES
            ),
            "families_per_prime_slot": CURVE_FAMILIES,
            "source_identity": "stage|p|family|source_index",
            "source_index_rule": (
                "within each bound stage/prime/family, allocate consecutive source_index "
                "values from zero through trials_per_factor_cell-1"
            ),
        },
        "prime_identity_reuse_between_stages_permitted": False,
        "shared_exposure_matrix_by_bit": exposure_rows,
        "stage_matrices": [
            {
                "stage": "discovery",
                "status": "SCALE_ONLY_UNALLOCATED",
                "reason": (
                    "prime identities exist, but execution resources are not committed"
                ),
                "exposure_matrix_reference": "shared_exposure_matrix_by_bit",
                "prime_binding": {
                    "status": "FROZEN_MANIFEST_AVAILABLE_SCALE_ONLY",
                    "path": "PRIMES.json",
                    "sha256": file_sha256(PRIME_MANIFEST_PATH),
                    "rows": discovery_bindings,
                },
            },
            {
                "stage": "replication",
                "status": "UNALLOCATED",
                "reason": (
                    "protocol requires fresh replication seed/primes; no fresh prime "
                    "manifest or execution resources are committed"
                ),
                "exposure_matrix_reference": "shared_exposure_matrix_by_bit",
                "prime_binding": {
                    "status": "UNALLOCATED_MISSING_FRESH_PRIME_MANIFEST",
                    "path": None,
                    "sha256": None,
                    "rows": replication_bindings,
                },
            },
        ],
        "status": "DISCOVERY_SCALE_ONLY_REPLICATION_UNALLOCATED",
    }


def reference_top_bit_rows(beta: Fraction) -> int:
    return trials_for_expected_events(
        32, beta, REFERENCE_EXPECTED_EVENTS_AT_TOP_BIT
    )


def zero_event_exposure() -> dict[str, Any]:
    """Recompute the one-cell exact-binomial zero-event threshold.

    Decimal logarithms identify the integer and high-precision powers check
    minimality.  This is a fixed independent-Bernoulli calculation only.
    """
    precision = 120
    q = Fraction(1, 1 << 24)
    with localcontext() as context:
        context.prec = precision
        one_minus_q = Decimal(q.denominator - q.numerator) / Decimal(q.denominator)
        alpha = Decimal(1) / Decimal(20)
        candidate = math.ceil(alpha.ln() / one_minus_q.ln())
        at_candidate = one_minus_q**candidate
        at_previous = one_minus_q ** (candidate - 1)
    if not (at_candidate <= alpha < at_previous):
        raise AllocationError("zero-event minimality check failed")
    return {
        "scope": (
            "one fixed-rate independent Bernoulli cell; not a multi-profile "
            "power calculation"
        ),
        "bits": 32,
        "beta": "-3/4",
        "q0": "2^-24",
        "alpha": rational_record(FAMILYWISE_ALPHA),
        "formula": "ceil(log(alpha)/log(1-q0))",
        "trials": candidate,
        "minimality_certificate": (
            f"(1-2^-24)^{candidate} <= 0.05 < (1-2^-24)^{candidate-1}"
        ),
        "decimal_precision": precision,
        "multiplicity_cluster_censoring_included": False,
    }


def two_phase_scenario(
    population_rows: int,
    positive_fraction: Fraction,
    negative_inclusion: Fraction,
) -> dict[str, Any]:
    """Return exact scenario arithmetic for an outcome-blind two-phase design.

    ``positive_fraction`` is an assumed proxy-positive fraction, not a measured
    value.  Positives have inclusion one; negatives have fixed inclusion pi.
    The Kish value is only an expected-denominator design-effect proxy.
    """
    population_rows = _plain_nonnegative_int(population_rows, "population_rows")
    for value, name in (
        (positive_fraction, "positive_fraction"),
        (negative_inclusion, "negative_inclusion"),
    ):
        if not isinstance(value, Fraction) or value <= 0 or value > 1:
            raise AllocationError(f"{name} must lie in (0,1]")
    positives = math.ceil(population_rows * positive_fraction)
    negatives = population_rows - positives
    expected_retained = Fraction(positives, 1) + negative_inclusion * negatives
    expected_weight_square_sum = Fraction(positives, 1) + Fraction(
        negatives, 1
    ) / negative_inclusion
    kish = (
        Fraction(population_rows * population_rows, 1)
        / expected_weight_square_sum
        if population_rows
        else Fraction(0, 1)
    )
    equivalent = negative_inclusion == 1
    return {
        "population_rows": population_rows,
        "assumed_proxy_positive_fraction": rational_record(positive_fraction),
        "assumed_proxy_positive_rows": positives,
        "proxy_negative_rows": negatives,
        "negative_inclusion_probability": rational_record(negative_inclusion),
        "expected_retained_rows": rational_record(expected_retained),
        "expected_retained_rows_ceiling": math.ceil(expected_retained),
        "negative_inverse_probability_weight": rational_record(
            1 / negative_inclusion
        ),
        "kish_effective_rows_proxy": rational_record(kish),
        "kish_effective_fraction_proxy": rational_record(
            kish / population_rows if population_rows else Fraction(0, 1)
        ),
        "equivalent_exposure_established": equivalent,
        "status": "FULL_CENSUS" if equivalent else "SCENARIO_ONLY_NOT_POWER_EQUIVALENT",
        "caveat": (
            "Power equivalence requires proxy-stratum event rates, clustering, and the "
            "weighted estimator variance; the Kish proxy is not a power certificate."
        ),
    }


def two_phase_options(total_rows: int) -> list[dict[str, Any]]:
    return [
        two_phase_scenario(total_rows, positive, inclusion)
        for positive in (Fraction(1, 100), Fraction(1, 10), Fraction(1, 2))
        for inclusion in (Fraction(1, 1), Fraction(1, 10))
    ]


def compact_two_phase_grid(expected_allocations: list[dict[str, Any]]) -> dict[str, Any]:
    populations = {
        allocation["beta"]: allocation[
            "total_rows_all_factor_cells_both_stages_if_executed"
        ]
        for allocation in expected_allocations
    }
    sampled = []
    for positive in (Fraction(1, 100), Fraction(1, 10), Fraction(1, 2)):
        rows = []
        for beta, population in populations.items():
            scenario = two_phase_scenario(population, positive, Fraction(1, 10))
            rows.append(
                {
                    "beta": beta,
                    "full_population_rows": population,
                    "expected_retained_rows_ceiling": scenario[
                        "expected_retained_rows_ceiling"
                    ],
                    "rank_timeout_ceiling_at_retained_rows_ceiling": seconds_record(
                        scenario["expected_retained_rows_ceiling"]
                        * RANK_TIMEOUT_SECONDS_PER_ROW,
                        AVAILABLE_LOGICAL_CPUS,
                    ),
                    "kish_effective_rows_proxy": scenario[
                        "kish_effective_rows_proxy"
                    ],
                    "kish_effective_fraction_proxy": scenario[
                        "kish_effective_fraction_proxy"
                    ],
                }
            )
        sampled.append(
            {
                "assumed_proxy_positive_fraction": rational_record(positive),
                "negative_inclusion_probability": rational_record(Fraction(1, 10)),
                "negative_inverse_probability_weight": 10,
                "rows_by_beta": rows,
                "status": "SCENARIO_ONLY_NOT_POWER_EQUIVALENT",
            }
        )
    return {
        "full_census_rows_by_beta": [
            {
                "beta": beta,
                "rows": rows,
                "rank_timeout_ceiling": seconds_record(
                    rows * RANK_TIMEOUT_SECONDS_PER_ROW, AVAILABLE_LOGICAL_CPUS
                ),
            }
            for beta, rows in populations.items()
        ],
        "sampled_negative_scenarios": sampled,
        "equivalent_power_status": "NOT_ESTABLISHED",
        "reason": (
            "No proxy-positive fraction, proxy-stratum event rate, or weighted "
            "cluster variance is measured or committed. Only inclusion 1 is "
            "generically exposure-equivalent."
        ),
        "formula": {
            "expected_retained": "H + pi*(N-H)",
            "negative_weight": "1/pi",
            "kish_proxy": "N^2/(H+(N-H)/pi)",
        },
    }


def calibration_budget() -> dict[str, Any]:
    timeout = CALIBRATION_ROWS * RANK_TIMEOUT_SECONDS_PER_ROW
    return {
        "rows": CALIBRATION_ROWS,
        "row_formula": "2 bit sizes * 3 prime slots * 90 factor cells * 2 rows",
        "bit_sizes": [16, 18],
        "prime_slots_per_bit": 3,
        "factor_cells": FACTOR_CELLS,
        "rows_per_factor_cell_prime": 2,
        "executable_r_values": [2, 3, 4, 5, 6],
        "rank_timeout_seconds_per_row": RANK_TIMEOUT_SECONDS_PER_ROW,
        "pari_timeout_seconds_per_row": PARI_TIMEOUT_SECONDS,
        "magma_timeout_seconds_per_row": MAGMA_TIMEOUT_SECONDS,
        "rank_timeout_ceiling": seconds_record(timeout, AVAILABLE_LOGICAL_CPUS),
        "hardware_logical_cpus_available_not_committed": AVAILABLE_LOGICAL_CPUS,
        "feasibility": "NOT_ESTABLISHED",
        "reason": (
            "The ideal five-worker timeout ceiling exceeds six days and excludes "
            "construction/relation/verification work; Magma and checkpoint transport are absent."
        ),
    }


def validate_resource_commitment(value: Any) -> dict[str, Any]:
    """Fail closed unless a complete externally committed allocation is supplied."""
    required = {
        "workers",
        "wall_seconds",
        "storage_bytes",
        "checkpoint_transport_verified",
        "licensed_magma_verified",
        "signed_commitment_sha256",
    }
    if value is None:
        return {
            "status": "UNALLOCATED",
            "reason": "no external resource commitment was supplied",
        }
    if not isinstance(value, dict) or set(value) != required:
        return {
            "status": "UNALLOCATED",
            "reason": "resource commitment schema is incomplete or has extra fields",
        }
    workers = value["workers"]
    wall = value["wall_seconds"]
    storage = value["storage_bytes"]
    digest = value["signed_commitment_sha256"]
    valid = (
        isinstance(workers, int)
        and not isinstance(workers, bool)
        and workers > 0
        and isinstance(wall, int)
        and not isinstance(wall, bool)
        and wall > 0
        and isinstance(storage, int)
        and not isinstance(storage, bool)
        and storage > 0
        and value["checkpoint_transport_verified"] is True
        and value["licensed_magma_verified"] is True
        and isinstance(digest, str)
        and len(digest) == 64
        and all(character in "0123456789abcdef" for character in digest)
    )
    if not valid:
        return {
            "status": "UNALLOCATED",
            "reason": "resource commitment values or external gate evidence are invalid",
        }
    return {
        "status": "UNALLOCATED",
        "reason": (
            "Commitment-shaped input does not establish signer authority or that resources "
            "are actually reserved."
        ),
        "schema_valid_claim_received": True,
    }


def build_manifest(resource_commitment: Any = None) -> dict[str, Any]:
    expected = [expected_count_allocation(beta) for beta in BETAS]
    top_bit = [
        {
            "beta": beta_text(beta),
            "bits": 32,
            "reference_target_expected_events_per_single_cell": (
                REFERENCE_EXPECTED_EVENTS_AT_TOP_BIT
            ),
            "trials": reference_top_bit_rows(beta),
        }
        for beta in BETAS
    ]
    two_phase = compact_two_phase_grid(expected)
    body: dict[str, Any] = {
        "schema": SCHEMA,
        "date": "2026-11-19",
        "natural_rows_included": False,
        "status": "UNALLOCATED",
        "resource_commitment": validate_resource_commitment(resource_commitment),
        "frozen_requirements": {
            "familywise_alpha": rational_record(FAMILYWISE_ALPHA),
            "simultaneous_profiles": SIMULTANEOUS_PROFILES,
            "bootstrap_replicates": BOOTSTRAP_REPLICATES,
            "bootstrap_minimum_formula": "ceil(2*M/alpha)",
            "bootstrap_minimum_recomputed": math.ceil(
                Fraction(2 * SIMULTANEOUS_PROFILES, 1) / FAMILYWISE_ALPHA
            ),
            "bit_sizes": list(BITS),
            "inference_bit_sizes": list(INFERENCE_BITS),
            "stages": list(STAGES),
            "factor_cells": FACTOR_CELLS,
            "factor_cell_formula": "2 curve families * 3 lifts * 3 local arms * 5 r values",
            "minimum_observed_high_bit_useful_events_combined_stages": PROTOCOL_MINIMUM_OBSERVED_USEFUL_EVENTS,
            "observation_rule_scope": "global protocol rule; not an expected-event sample-size formula",
            "analyzer_note": (
                "The current analyzer evaluates a decision candidate within one factor cell; "
                "it does not require all 90 factor cells to each pass."
            ),
            "required_useful_event_sizes_per_stage": list(INFERENCE_BITS),
            "signed_beta_lower_gate": "beta_lower > -0.8",
        },
        "reference_model": {
            "model": "q(p)=kappa*p^beta",
            "kappa": 1,
            "intercept_alpha": "log(kappa)=0",
            "beta_scenarios": [beta_text(beta) for beta in BETAS],
            "prime_scale": "p=2^b (conservative within each b-bit manifest stratum for beta<0)",
            "scope": "transparent expected-event arithmetic, not a theorem-derived rate lower bound",
        },
        "top_bit_expected_count_check": {
            "scope": (
                "legacy one-cell expected-count reference arithmetic; distinct from "
                "the global protocol observation rule"
            ),
            "rows": top_bit,
            "status": "REFERENCE_SCALE_ONLY_NOT_POWERED",
        },
        "zero_event_reference_check": zero_event_exposure(),
        "optional_stronger_full_factorial_scale": expected,
        "optional_execution_matrix": execution_matrix(expected),
        "calibration": calibration_budget(),
        "two_phase_scenarios": two_phase,
        "allocation_decision": {
            "status": "UNALLOCATED",
            "reasons": [
                "no checkpoint upload transport",
                "no licensed pinned Magma runtime",
                "no externally committed workers, wall time, or storage",
                "kappa and proxy-stratum event rates are not bounded",
                "no target probability for observing at least thirty events is frozen",
                "cluster/censoring power and two-phase variance equivalence are not established",
            ],
            "no_downscaling": True,
            "next_admissible_stage": (
                "the frozen 1080-row calibration after every production gate passes; "
                "it is not discovery or a decay result"
            ),
        },
    }
    body["manifest_sha256"] = object_sha256(body)
    return body


def validate_manifest(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise AllocationError("manifest must be an object")
    expected = build_manifest()
    if set(value) != set(expected):
        raise AllocationError("manifest root schema mismatch")
    supplied_hash = value.get("manifest_sha256")
    body = dict(value)
    body.pop("manifest_sha256", None)
    if supplied_hash != object_sha256(body):
        raise AllocationError("manifest digest mismatch")
    if value != expected:
        raise AllocationError("manifest differs from executable recomputation")
    return {
        "status": "PASS_PROSPECTIVE_UNALLOCATED",
        "manifest_sha256": supplied_hash,
        "natural_rows_included": False,
        "resource_status": "UNALLOCATED",
    }


def render_manifest() -> str:
    return json.dumps(
        build_manifest(),
        indent=2,
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
    ) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate or validate the exact prospective allocation manifest."
    )
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--output", type=Path, help="write the generated manifest")
    action.add_argument("--check", type=Path, help="validate a generated manifest")
    arguments = parser.parse_args(argv)
    if arguments.check is not None:
        try:
            supplied = json.loads(arguments.check.read_text())
            result = validate_manifest(supplied)
        except (OSError, json.JSONDecodeError, AllocationError) as error:
            parser.error(str(error))
        print(canonical_json(result))
        return 0
    rendered = render_manifest()
    if arguments.output is None:
        print(rendered, end="")
        return 0
    temporary = arguments.output.with_name(f".{arguments.output.name}.tmp")
    temporary.write_text(rendered)
    temporary.replace(arguments.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
