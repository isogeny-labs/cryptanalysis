#!/usr/bin/env python3
"""Exact-box and fail-closed controls for mixed unresolved allocations."""

from __future__ import annotations

import itertools
import hashlib
import inspect
import math
import random
import unittest
from unittest import mock

import analyze
import mixed_censoring as mixed
import sensitivity


DIGEST = "1" * 64
CONTROL_SERIES = {
    "stage": "discovery",
    "panel": "primary",
    "arm": "baseline",
    "curve_family": "generic",
    "lift_strategy": "balanced",
    "local_arm": "A_none",
    "r": 4,
}
CONTROL_BINDING = {
    "series": CONTROL_SERIES,
    "endpoint": "rank_lt_r",
    "denominator": "admitted",
    "input_rowset_sha256": "2" * 64,
}


class LyingFloat(float):
    def __eq__(self, other):
        return True


class LyingStr(str):
    def __eq__(self, other):
        return True

    __hash__ = str.__hash__


class LyingInt(int):
    def __eq__(self, other):
        return True

    __hash__ = int.__hash__


class Stage(str):
    def __eq__(self, other):
        return other == "discovery" or super().__eq__(other)

    __hash__ = str.__hash__


class EqualPrime(int):
    def __eq__(self, other):
        return other == 2

    def __hash__(self):
        return hash(2)


class DistinctSameStr(str):
    def __new__(cls, value, identity):
        instance = super().__new__(cls, value)
        instance.identity = identity
        return instance

    def __eq__(self, other):
        return self is other

    def __hash__(self):
        return hash(self.identity)


class SubclassList(list):
    pass


class SubclassDict(dict):
    pass


def analysis_row(label: str, prime: int, *, lower: int, upper: int, index: int):
    tool = {
        "status": "certified",
        "version": "synthetic-1",
        "lower": lower,
        "upper": upper,
        "exact": lower == upper,
        "wall_ns": 1,
    }
    return {
        "schema": analyze.ROW_SCHEMA,
        "trial_id": f"trial-{label}",
        "master_seed": "seed-discovery",
        "stage": "discovery",
        "panel": "primary",
        "arm": "baseline",
        "p": prime,
        "bits": prime.bit_length(),
        "curve_family": "generic",
        "lift_strategy": "balanced",
        "local_arm": "A_none",
        "r": 4,
        "index": index,
        "planned_trials": 4,
        "source_id": f"source-{label}",
        "curve_id": f"curve-{label}",
        "isomorphism_class_id": f"iso-{label}",
        "lift_digest": hashlib.sha256(f"lift-{label}".encode()).hexdigest(),
        "status": "ranked",
        "rank": {"pari": dict(tool), "magma": dict(tool)},
        "outcome": {
            "selected_dependence": "UNKNOWN",
            "relation_class": "unknown",
            "rational_relation_replay": "UNKNOWN",
            "relation_certificate_sha256": None,
            "relation_proof_verified": False,
            "target_coefficient_invertible": "UNKNOWN",
            "scalar_replay": "UNKNOWN",
            "source_replay_sha256": None,
            "source_replay_proof_verified": False,
            "useful_recovery": "UNKNOWN",
        },
        "work": {
            "complete": True,
            "source_generation_candidates": 1,
            "local_construction_candidates": 1,
            "lift_candidates": 1,
            "rejected_candidates": 0,
            "duplicate_candidates": 0,
            "public_group_operations": 1,
            "rank_calls": 2,
            "cpu_seconds": 0.001,
            "peak_rss_bytes": 1024,
            "retained_bytes": 256,
        },
    }


def cell(p: int, exposure: int, certified: int, unresolved: int) -> dict[str, int]:
    return {
        "p": p,
        "exposure": exposure,
        "certified_successes": certified,
        "unresolved": unresolved,
    }


def objective_number(value):
    if value == "-inf" or value is None:
        return -math.inf
    if value == "+inf":
        return math.inf
    return float(value)


def cluster_row(
    row_id: str,
    bits: int,
    p: int,
    source_id: str,
    curve_id: str,
    exposure: int,
    certified: int,
    unresolved: int,
):
    return {
        "schema": mixed.CLUSTER_ROW_SCHEMA,
        "row_id": row_id,
        "bits": bits,
        "p": p,
        "source_id": source_id,
        "curve_id": curve_id,
        "exposure": exposure,
        "certified_successes": certified,
        "unresolved": unresolved,
    }


def independent_nested_minimum(
    rows,
    *,
    familywise_alpha,
    simultaneous_hypotheses,
    cluster_replicates,
    cluster_seed,
):
    """Independent reference using sensitivity's row resampler directly."""
    normalized = mixed.normalize_cluster_rows(rows)
    ranges = [range(row["unresolved"] + 1) for row in normalized]
    candidates = []
    tail = familywise_alpha / (2 * simultaneous_hypotheses)
    series_key = tuple(CONTROL_SERIES[field] for field in analyze.SERIES_FIELDS)
    derived_seed = f"{cluster_seed}|{series_key!r}"
    for extras in itertools.product(*ranges):
        successes = tuple(
            row["certified_successes"] + extra
            for row, extra in zip(normalized, extras, strict=True)
        )
        materialized = [
            {**row, "successes": count}
            for row, count in zip(normalized, successes, strict=True)
        ]
        rng = random.Random(derived_seed)
        values = []
        for _ in range(cluster_replicates):
            sampled = sensitivity._bootstrap_rows(materialized, rng)
            by_prime = {}
            for row in sampled:
                aggregate = by_prime.setdefault(row["p"], [0, 0])
                aggregate[0] += row["exposure"]
                aggregate[1] += row["successes"]
            entries = [
                (prime, by_prime[prime][0], by_prime[prime][1])
                for prime in sorted(by_prime)
            ]
            fit = sensitivity.fit_binomial_cloglog(
                entries,
                familywise_alpha=familywise_alpha,
                simultaneous_hypotheses=simultaneous_hypotheses,
            )
            values.append(
                fit["beta_hat"]
                if fit["identifiable"] and isinstance(fit["beta_hat"], float)
                else "-inf"
            )
        lower = sensitivity._bootstrap_lower(values, tail)
        candidates.append((objective_number(lower), successes, lower))
    return min(candidates, key=lambda item: (item[0], item[1]))


class MixedCensoringTests(unittest.TestCase):
    def test_normalize_aggregates_duplicate_primes(self):
        self.assertEqual(
            mixed.normalize_cells(
                [cell(5, 7, 1, 2), cell(3, 4, 0, 1), cell(5, 9, 2, 3)]
            ),
            [cell(3, 4, 0, 1), cell(5, 16, 3, 5)],
        )

    def test_schema_and_integer_validation(self):
        bad = cell(3, 4, 1, 1)
        bad["extra"] = 0
        with self.assertRaises(mixed.MixedCensoringError):
            mixed.normalize_cells([bad])
        with self.assertRaises(mixed.MixedCensoringError):
            mixed.normalize_cells([cell(3, 1, True, 0)])
        with self.assertRaises(mixed.MixedCensoringError):
            mixed.normalize_cells([cell(3, 2, 1, 2)])

    def test_exact_enumeration_finds_interior_not_uniform_corner(self):
        cells = [cell(3, 3, 0, 2), cell(5, 2, 0, 1)]

        def evaluator(successes):
            return (successes[0] - 1) ** 2 + (successes[1] - 1) ** 2

        result = mixed.exact_box_optimize(
            cells,
            evaluator,
            method="synthetic",
            objective="interior quadratic",
            evaluator_sha256=DIGEST,
            max_states=6,
        )
        self.assertEqual(result["status"], "COMPLETE")
        self.assertTrue(result["exact_integer_box"])
        self.assertEqual(result["state_count"], 6)
        self.assertEqual(result["evaluated_states"], 6)
        self.assertEqual(result["minimum"]["value"], 0.0)
        self.assertEqual(
            [row["successes"] for row in result["minimum"]["allocation"]],
            [1, 1],
        )
        self.assertTrue(mixed.verify_certificate_digest(result))
        result["minimum"]["value"] = 1.0
        self.assertFalse(mixed.verify_certificate_digest(result))

    def test_state_limit_fails_before_evaluation(self):
        calls = 0

        def evaluator(_successes):
            nonlocal calls
            calls += 1
            return 0.0

        result = mixed.exact_box_optimize(
            [cell(3, 10, 0, 9), cell(5, 10, 0, 9)],
            evaluator,
            method="synthetic",
            objective="zero",
            evaluator_sha256=DIGEST,
            max_states=99,
        )
        self.assertEqual(result["status"], "BLOCKED_STATE_LIMIT")
        self.assertEqual(result["state_count"], 100)
        self.assertEqual(result["evaluated_states"], 0)
        self.assertEqual(calls, 0)
        self.assertTrue(mixed.verify_certificate_digest(result))

    def test_binomial_matches_independent_full_product(self):
        cells = [
            cell(101, 80, 3, 2),
            cell(211, 90, 2, 2),
            cell(431, 100, 1, 2),
        ]
        alpha = 0.5
        hypotheses = 1
        result = mixed.optimize_binomial_cloglog(
            cells,
            familywise_alpha=alpha,
            simultaneous_hypotheses=hypotheses,
            max_states=27,
        )
        brute = []
        normalized = mixed.normalize_cells(cells)
        for extras in itertools.product(range(3), repeat=3):
            successes = tuple(
                row["certified_successes"] + extra
                for row, extra in zip(normalized, extras, strict=True)
            )
            fit = sensitivity.fit_binomial_cloglog(
                [
                    (row["p"], row["exposure"], count)
                    for row, count in zip(normalized, successes, strict=True)
                ],
                familywise_alpha=alpha,
                simultaneous_hypotheses=hypotheses,
            )
            brute.append((objective_number(fit["signed_beta_lower"]), successes))
        expected = min(brute)
        self.assertEqual(result["status"], "COMPLETE")
        self.assertEqual(result["evaluated_states"], 27)
        self.assertEqual(
            objective_number(result["minimum"]["value"]), expected[0]
        )
        self.assertEqual(
            tuple(row["successes"] for row in result["minimum"]["allocation"]),
            expected[1],
        )
        self.assertTrue(mixed.verify_certificate_digest(result))

    def test_poisson_structural_optimizer_matches_full_product(self):
        cases = [
            [
                cell(101, 500, 80, 3),
                cell(211, 500, 50, 4),
                cell(431, 500, 30, 2),
            ],
            [
                cell(1009, 1000, 20, 2),
                cell(2003, 1000, 25, 3),
                cell(4001, 1000, 35, 2),
                cell(8009, 1000, 45, 1),
            ],
        ]
        alpha = 0.5
        hypotheses = 1
        for cells in cases:
            with self.subTest(cells=cells):
                normalized = mixed.normalize_cells(cells)
                result = mixed.optimize_poisson_hoeffding(
                    normalized,
                    familywise_alpha=alpha,
                    simultaneous_hypotheses=hypotheses,
                )
                brute = []
                ranges = [range(row["unresolved"] + 1) for row in normalized]
                for extras in itertools.product(*ranges):
                    successes = tuple(
                        row["certified_successes"] + extra
                        for row, extra in zip(normalized, extras, strict=True)
                    )
                    fit = analyze.poisson_profile(
                        [
                            (row["p"], row["exposure"], count)
                            for row, count in zip(normalized, successes, strict=True)
                        ],
                        familywise_alpha=alpha,
                        simultaneous_hypotheses=hypotheses,
                    )
                    brute.append(
                        (
                            objective_number(fit["confidence_interval"]["lower"]),
                            successes,
                        )
                    )
                expected_value = min(item[0] for item in brute)
                self.assertEqual(result["status"], "COMPLETE")
                self.assertTrue(result["exact_integer_box"])
                self.assertAlmostEqual(
                    objective_number(result["minimum"]["value"]),
                    expected_value,
                    places=11,
                )
                self.assertTrue(mixed.verify_certificate_digest(result))

    def test_zero_certified_events_has_global_negative_infinity(self):
        result = mixed.optimize_poisson_hoeffding(
            [cell(101, 10, 0, 4), cell(211, 10, 0, 4)],
            familywise_alpha=0.05,
            simultaneous_hypotheses=4320,
        )
        self.assertEqual(result["minimum"]["value"], "-inf")
        self.assertEqual(result["minimum"]["extra_successes"], 0)

    def test_nested_cluster_exact_matches_independent_resampler(self):
        rows = [
            cluster_row("a", 3, 5, "s0", "c0", 20, 4, 1),
            cluster_row("b", 3, 7, "s1", "c1", 22, 5, 1),
            cluster_row("c", 4, 11, "s2", "c2", 24, 6, 1),
            cluster_row("d", 4, 13, "s3", "c3", 26, 7, 1),
        ]
        parameters = {
            "familywise_alpha": 0.9,
            "simultaneous_hypotheses": 1,
            "cluster_replicates": 12,
            "cluster_seed": "nested-control",
        }
        result = mixed.optimize_nested_cluster_bootstrap(
            rows,
            **CONTROL_BINDING,
            **parameters,
            max_states=16,
            max_bootstrap_evaluations=192,
        )
        expected = independent_nested_minimum(rows, **parameters)
        self.assertEqual(result["status"], "COMPLETE_BOUNDED_CONTROL")
        self.assertTrue(result["exact_nested_cluster_box"])
        self.assertEqual(result["state_count"], 16)
        self.assertEqual(result["evaluated_states"], 16)
        self.assertEqual(result["evaluated_bootstrap_fits"], 192)
        self.assertEqual(
            objective_number(result["minimum"]["value"]), expected[0]
        )
        self.assertEqual(
            tuple(row["successes"] for row in result["minimum"]["allocation"]),
            expected[1],
        )
        self.assertEqual(
            result["cluster_keys"], ["bits", "p", "source_id", "curve_id"]
        )
        series_key = tuple(CONTROL_SERIES[field] for field in analyze.SERIES_FIELDS)
        self.assertEqual(
            result["derived_cluster_seed"],
            f"nested-control|{series_key!r}",
        )
        self.assertEqual(result["series"], CONTROL_SERIES)
        self.assertEqual(result["endpoint"], "rank_lt_r")
        self.assertEqual(result["denominator"], "admitted")
        self.assertEqual(result["input_rowset_sha256"], "2" * 64)
        self.assertFalse(result["production_parameters_satisfied"])
        self.assertFalse(result["production_eligible"])
        self.assertTrue(mixed.verify_certificate_digest(result))

    def test_strict_analysis_rows_bind_series_endpoint_and_rowset(self):
        rows = [
            analysis_row("a", 40759, lower=0, upper=3, index=0),
            analysis_row("b", 40759, lower=2, upper=5, index=1),
            analysis_row("c", 232189, lower=0, upper=3, index=2),
            analysis_row("d", 232189, lower=2, upper=5, index=3),
        ]
        result = mixed.optimize_nested_cluster_bootstrap_rows(
            rows,
            endpoint="rank_lt_r",
            denominator="admitted",
            familywise_alpha=0.9,
            simultaneous_hypotheses=1,
            cluster_replicates=4,
            cluster_seed="analysis-control",
            max_states=4,
            max_bootstrap_evaluations=16,
            max_plan_entries=16,
        )
        validated = [analyze.validate_row(row) for row in rows]
        expected_series = dict(
            zip(
                analyze.SERIES_FIELDS,
                analyze._series_key(validated[0]),
                strict=True,
            )
        )
        expected_key = tuple(
            expected_series[field] for field in analyze.SERIES_FIELDS
        )
        self.assertEqual(result["binding_mode"], "validated_analysis_rows")
        self.assertEqual(
            result["analysis_replay"]["series_fields"],
            list(analyze.SERIES_FIELDS),
        )
        self.assertEqual(
            result["analysis_replay"],
            result["evaluator_contract"]["analysis_replay"],
        )
        self.assertEqual(result["series"], expected_series)
        self.assertEqual(result["endpoint"], "rank_lt_r")
        self.assertEqual(result["denominator"], "admitted")
        self.assertEqual(
            result["input_rowset_sha256"], analyze.rowset_sha256(validated)
        )
        self.assertEqual(
            result["derived_cluster_seed"],
            f"analysis-control|{expected_key!r}",
        )
        self.assertEqual(result["status"], "COMPLETE_BOUNDED_CONTROL")
        self.assertFalse(result["production_parameters_satisfied"])
        self.assertTrue(mixed.verify_certificate_digest(result))

    def test_nested_cluster_exposes_no_production_promotion_capability(self):
        self.assertIs(mixed.PRODUCTION_READY, False)
        forbidden_fragments = (
            "receipt",
            "capability",
            "authority",
            "registry",
            "weakset",
        )
        for name in vars(mixed):
            self.assertFalse(
                any(fragment in name.lower() for fragment in forbidden_fragments),
                name,
            )
        module_source = inspect.getsource(mixed).lower()
        for fragment in forbidden_fragments:
            self.assertNotIn(fragment, module_source)

        forbidden_parameters = {
            "binding_mode",
            "production_parameters_satisfied",
            "production_eligible",
            "receipt",
            "capability",
            "_analysis_binding",
        }
        for name, function in inspect.getmembers(mixed, inspect.isfunction):
            if function.__module__ != mixed.__name__:
                continue
            parameters = set(inspect.signature(function).parameters)
            self.assertTrue(
                forbidden_parameters.isdisjoint(parameters),
                f"{name} exposes {sorted(forbidden_parameters & parameters)}",
            )

    def test_plain_json_boundary_rejects_subclass_attacks(self):
        raw_rows = [
            cluster_row("a", 3, 5, "s0", "c0", 20, 3, 0),
            cluster_row("b", 3, 7, "s1", "c1", 20, 3, 0),
            cluster_row("c", 4, 11, "s2", "c2", 20, 3, 0),
        ]
        raw_parameters = {
            **CONTROL_BINDING,
            "familywise_alpha": 0.9,
            "simultaneous_hypotheses": 1,
            "cluster_replicates": 4,
            "cluster_seed": "plain-json-control",
        }
        analysis_rows = [
            analysis_row("a", 40759, lower=0, upper=3, index=0),
            analysis_row("b", 232189, lower=2, upper=5, index=1),
        ]
        strict_parameters = {
            "endpoint": "rank_lt_r",
            "denominator": "admitted",
            "familywise_alpha": 0.9,
            "simultaneous_hypotheses": 1,
            "cluster_replicates": 4,
            "cluster_seed": "plain-json-control",
        }

        scalar_attacks = {
            "familywise_alpha": LyingFloat(0.9),
            "simultaneous_hypotheses": LyingInt(1),
            "cluster_replicates": LyingInt(4),
            "cluster_seed": LyingStr("caller-seed"),
            "max_row_visits": LyingInt(100),
        }
        for field, attack in scalar_attacks.items():
            with self.subTest(api="raw", field=field):
                parameters = {**raw_parameters, field: attack}
                with self.assertRaises(mixed.MixedCensoringError) as raised:
                    mixed.optimize_nested_cluster_bootstrap(
                        raw_rows,
                        **parameters,
                    )
                self.assertIs(type(raised.exception), mixed.MixedCensoringError)
            with self.subTest(api="strict", field=field):
                parameters = {**strict_parameters, field: attack}
                with self.assertRaises(mixed.MixedCensoringError) as raised:
                    mixed.optimize_nested_cluster_bootstrap_rows(
                        analysis_rows,
                        **parameters,
                    )
                self.assertIs(type(raised.exception), mixed.MixedCensoringError)

        raw_stage_series = {**CONTROL_SERIES, "stage": Stage("sentinel")}
        raw_r_series = {**CONTROL_SERIES, "r": LyingInt(4)}
        for series in (raw_stage_series, raw_r_series, SubclassDict(CONTROL_SERIES)):
            with self.assertRaises(mixed.MixedCensoringError):
                mixed.optimize_nested_cluster_bootstrap(
                    raw_rows,
                    **{**raw_parameters, "series": series},
                )

        strict_stage_rows = [dict(row) for row in analysis_rows]
        strict_stage_rows[0]["stage"] = Stage("sentinel")
        strict_r_rows = [dict(row) for row in analysis_rows]
        strict_r_rows[0]["r"] = LyingInt(4)
        for attacked_rows in (strict_stage_rows, strict_r_rows):
            with self.assertRaises(mixed.MixedCensoringError):
                mixed.optimize_nested_cluster_bootstrap_rows(
                    attacked_rows,
                    **strict_parameters,
                )

        raw_prime_rows = [dict(row) for row in raw_rows]
        raw_prime_rows[0]["p"] = EqualPrime(65535)
        raw_prime_rows[0]["bits"] = 16
        with self.assertRaises(mixed.MixedCensoringError):
            mixed.optimize_nested_cluster_bootstrap(
                raw_prime_rows,
                **raw_parameters,
            )
        strict_prime_rows = [dict(row) for row in analysis_rows]
        strict_prime_rows[0]["p"] = EqualPrime(65535)
        strict_prime_rows[0]["bits"] = 16
        with self.assertRaises(mixed.MixedCensoringError):
            mixed.optimize_nested_cluster_bootstrap_rows(
                strict_prime_rows,
                **strict_parameters,
            )

        raw_duplicate_rows = [dict(raw_rows[0]), dict(raw_rows[1])]
        raw_duplicate_rows[0]["row_id"] = DistinctSameStr("same", "a")
        raw_duplicate_rows[1]["row_id"] = DistinctSameStr("same", "b")
        with self.assertRaises(mixed.MixedCensoringError):
            mixed.optimize_nested_cluster_bootstrap(
                raw_duplicate_rows,
                **raw_parameters,
            )
        strict_duplicate_rows = [dict(row) for row in analysis_rows]
        strict_duplicate_rows[0]["trial_id"] = DistinctSameStr("same", "a")
        strict_duplicate_rows[1]["trial_id"] = DistinctSameStr("same", "b")
        with self.assertRaises(mixed.MixedCensoringError):
            mixed.optimize_nested_cluster_bootstrap_rows(
                strict_duplicate_rows,
                **strict_parameters,
            )
        exact_duplicate_rows = [dict(row) for row in analysis_rows]
        exact_duplicate_rows[1]["trial_id"] = exact_duplicate_rows[0]["trial_id"]
        with self.assertRaises(mixed.MixedCensoringError):
            mixed.optimize_nested_cluster_bootstrap_rows(
                exact_duplicate_rows,
                **strict_parameters,
            )

        container_attacks = (
            SubclassList(raw_rows),
            [SubclassDict(raw_rows[0]), *raw_rows[1:]],
        )
        for attacked_rows in container_attacks:
            with self.assertRaises(mixed.MixedCensoringError):
                mixed.optimize_nested_cluster_bootstrap(
                    attacked_rows,
                    **raw_parameters,
                )
        strict_container_attacks = (
            SubclassList(analysis_rows),
            [SubclassDict(analysis_rows[0]), analysis_rows[1]],
        )
        for attacked_rows in strict_container_attacks:
            with self.assertRaises(mixed.MixedCensoringError):
                mixed.optimize_nested_cluster_bootstrap_rows(
                    attacked_rows,
                    **strict_parameters,
                )

        self.assertGreaterEqual(mixed.PLAIN_JSON_MAX_DEPTH, 32)
        self.assertGreaterEqual(mixed.PLAIN_JSON_MAX_NODES, 1_000_000)
        self.assertGreaterEqual(
            mixed.PLAIN_JSON_MAX_CONTAINER_LENGTH,
            100_000,
        )
        cyclic_rows = []
        cyclic_rows.append(cyclic_rows)
        with self.assertRaises(mixed.MixedCensoringError):
            mixed.optimize_nested_cluster_bootstrap(
                cyclic_rows,
                **raw_parameters,
            )
        with self.assertRaises(mixed.MixedCensoringError):
            mixed.optimize_nested_cluster_bootstrap_rows(
                cyclic_rows,
                **strict_parameters,
            )

        overdeep_rows = [[[None]]]
        with mock.patch.object(mixed, "PLAIN_JSON_MAX_DEPTH", 2):
            with self.assertRaises(mixed.MixedCensoringError):
                mixed.optimize_nested_cluster_bootstrap(
                    overdeep_rows,
                    **raw_parameters,
                )
        with mock.patch.object(mixed, "PLAIN_JSON_MAX_CONTAINER_LENGTH", 1):
            with self.assertRaises(mixed.MixedCensoringError):
                mixed.optimize_nested_cluster_bootstrap_rows(
                    analysis_rows,
                    **strict_parameters,
                )
        with mock.patch.object(mixed, "PLAIN_JSON_MAX_NODES", 2):
            with self.assertRaises(mixed.MixedCensoringError):
                mixed.optimize_nested_cluster_bootstrap(
                    raw_rows,
                    **raw_parameters,
                )

    def test_nested_cluster_randomized_bruteforce_crosscheck(self):
        generator = random.Random(20261119)
        layout = [
            (3, 5, 0),
            (3, 5, 1),
            (3, 7, 0),
            (4, 11, 0),
            (4, 11, 1),
            (4, 13, 0),
        ]
        for case in range(8):
            rows = []
            for index, (bits, prime, cluster_index) in enumerate(layout):
                exposure = generator.randrange(16, 28)
                certified = generator.randrange(3, min(9, exposure - 1))
                unresolved = generator.randrange(0, 2)
                rows.append(
                    cluster_row(
                        f"case{case}-row{index}",
                        bits,
                        prime,
                        f"source{prime}-{cluster_index}",
                        f"curve{case}-{prime}-{cluster_index}",
                        exposure,
                        certified,
                        unresolved,
                    )
                )
            parameters = {
                "familywise_alpha": 0.9,
                "simultaneous_hypotheses": 1,
                "cluster_replicates": 8,
                "cluster_seed": f"random-case-{case}",
            }
            with self.subTest(case=case):
                expected = independent_nested_minimum(rows, **parameters)
                result = mixed.optimize_nested_cluster_bootstrap(
                    rows,
                    **CONTROL_BINDING,
                    **parameters,
                    max_states=64,
                    max_bootstrap_evaluations=512,
                )
                self.assertEqual(result["status"], "COMPLETE_BOUNDED_CONTROL")
                self.assertEqual(
                    objective_number(result["minimum"]["value"]), expected[0]
                )
                self.assertEqual(
                    tuple(
                        row["successes"]
                        for row in result["minimum"]["allocation"]
                    ),
                    expected[1],
                )

    def test_nested_cluster_minimum_is_not_forced_to_uniform_corners(self):
        rows = [
            cluster_row("0", 3, 5, "s0", "c0", 33, 9, 2),
            cluster_row("1", 3, 7, "s1", "c1", 21, 4, 1),
            cluster_row("2", 4, 11, "s0", "c2", 17, 3, 1),
            cluster_row("3", 4, 13, "s1", "c3", 27, 2, 2),
        ]
        result = mixed.optimize_nested_cluster_bootstrap(
            rows,
            **CONTROL_BINDING,
            familywise_alpha=0.9,
            simultaneous_hypotheses=1,
            cluster_replicates=8,
            cluster_seed="s0",
            max_states=54,
            max_bootstrap_evaluations=432,
        )
        allocation = tuple(
            row["successes"] for row in result["minimum"]["allocation"]
        )
        normalized = mixed.normalize_cluster_rows(rows)
        all_failure = tuple(row["certified_successes"] for row in normalized)
        all_success = tuple(
            row["certified_successes"] + row["unresolved"]
            for row in normalized
        )
        self.assertEqual(allocation, (11, 4, 3, 2))
        self.assertNotIn(allocation, (all_failure, all_success))

    def test_nested_cluster_preserves_rows_and_rejects_bad_schema(self):
        rows = [
            cluster_row("a", 3, 5, "same", "curve-a", 10, 1, 1),
            cluster_row("b", 3, 5, "same", "curve-b", 11, 2, 0),
            cluster_row("c", 3, 7, "other", "curve-c", 12, 2, 0),
            cluster_row("d", 4, 11, "third", "curve-d", 13, 3, 0),
        ]
        result = mixed.optimize_nested_cluster_bootstrap(
            rows,
            **CONTROL_BINDING,
            familywise_alpha=0.9,
            simultaneous_hypotheses=1,
            cluster_replicates=4,
            cluster_seed="membership",
            max_states=2,
            max_bootstrap_evaluations=8,
        )
        self.assertEqual(len(result["cluster_rows"]), 4)
        self.assertEqual(
            {row["row_id"] for row in result["minimum"]["allocation"]},
            {"a", "b", "c", "d"},
        )
        bad = dict(rows[0])
        bad["extra"] = 1
        with self.assertRaises(mixed.MixedCensoringError):
            mixed.normalize_cluster_rows([bad])
        duplicate = [rows[0], {**rows[1], "row_id": "a"}]
        with self.assertRaises(mixed.MixedCensoringError):
            mixed.normalize_cluster_rows(duplicate)
        composite = cluster_row("composite", 4, 15, "s", "c", 10, 1, 0)
        with self.assertRaises(mixed.MixedCensoringError):
            mixed.normalize_cluster_rows([composite])
        too_large_p = (1 << 32) + 15
        too_large = cluster_row(
            "too-large",
            too_large_p.bit_length(),
            too_large_p,
            "s",
            "c",
            10,
            1,
            0,
        )
        with self.assertRaises(mixed.MixedCensoringError) as raised:
            mixed.optimize_nested_cluster_bootstrap(
                [too_large],
                **CONTROL_BINDING,
                familywise_alpha=0.9,
                simultaneous_hypotheses=1,
                cluster_replicates=4,
                cluster_seed="too-large-prime",
            )
        self.assertIs(type(raised.exception), mixed.MixedCensoringError)

    def test_nested_cluster_limits_fail_before_bootstrap_sampling(self):
        rows = [
            cluster_row("a", 3, 5, "s0", "c0", 20, 3, 4),
            cluster_row("b", 3, 7, "s1", "c1", 20, 3, 4),
            cluster_row("c", 4, 11, "s2", "c2", 20, 3, 0),
        ]
        with mock.patch.object(
            mixed,
            "_iter_bootstrap_plan",
            side_effect=AssertionError("must not sample"),
        ):
            state_block = mixed.optimize_nested_cluster_bootstrap(
                rows,
                **CONTROL_BINDING,
                familywise_alpha=0.9,
                simultaneous_hypotheses=1,
                cluster_replicates=4,
                cluster_seed="state-limit",
                max_states=24,
                max_bootstrap_evaluations=1_000,
            )
            evaluation_block = mixed.optimize_nested_cluster_bootstrap(
                rows,
                **CONTROL_BINDING,
                familywise_alpha=0.9,
                simultaneous_hypotheses=1,
                cluster_replicates=4,
                cluster_seed="evaluation-limit",
                max_states=25,
                max_bootstrap_evaluations=99,
            )
            plan_block = mixed.optimize_nested_cluster_bootstrap(
                rows,
                **CONTROL_BINDING,
                familywise_alpha=0.9,
                simultaneous_hypotheses=1,
                cluster_replicates=4,
                cluster_seed="plan-limit",
                max_states=25,
                max_bootstrap_evaluations=100,
                max_plan_entries=11,
            )
            row_visit_block = mixed.optimize_nested_cluster_bootstrap(
                rows,
                **CONTROL_BINDING,
                familywise_alpha=0.9,
                simultaneous_hypotheses=1,
                cluster_replicates=4,
                cluster_seed="row-visit-limit",
                max_states=25,
                max_bootstrap_evaluations=100,
                max_plan_entries=12,
                max_row_visits=299,
            )
        self.assertEqual(state_block["status"], "BLOCKED_NESTED_STATE_LIMIT")
        self.assertEqual(
            evaluation_block["status"],
            "BLOCKED_BOOTSTRAP_EVALUATION_LIMIT",
        )
        self.assertEqual(plan_block["status"], "BLOCKED_BOOTSTRAP_PLAN_LIMIT")
        self.assertEqual(plan_block["required_plan_entries"], 12)
        self.assertEqual(
            row_visit_block["status"], "BLOCKED_ROW_VISIT_LIMIT"
        )
        self.assertEqual(row_visit_block["required_row_visits"], 300)
        for result in (
            state_block,
            evaluation_block,
            plan_block,
            row_visit_block,
        ):
            self.assertEqual(result["evaluated_states"], 0)
            self.assertEqual(result["evaluated_bootstrap_fits"], 0)
            self.assertFalse(result["production_eligible"])
            self.assertTrue(mixed.verify_certificate_digest(result))

    def test_nested_cluster_tail_and_frozen_production_fail_closed(self):
        rows = [
            cluster_row("a", 3, 5, "s0", "c0", 20, 3, 1),
            cluster_row("b", 3, 7, "s1", "c1", 20, 3, 0),
            cluster_row("c", 4, 11, "s2", "c2", 20, 3, 0),
        ]
        tail_block = mixed.optimize_nested_cluster_bootstrap(
            rows,
            **CONTROL_BINDING,
            familywise_alpha=0.05,
            simultaneous_hypotheses=10,
            cluster_replicates=399,
            cluster_seed="tail-block",
        )
        self.assertEqual(tail_block["minimum_cluster_replicates"], 400)
        self.assertEqual(tail_block["status"], "BLOCKED_TAIL_RESOLUTION")
        with mock.patch.object(
            mixed,
            "_iter_bootstrap_plan",
            side_effect=AssertionError("must not sample"),
        ):
            frozen_block = mixed.optimize_nested_cluster_bootstrap(
                rows,
                **CONTROL_BINDING,
                familywise_alpha=0.05,
                simultaneous_hypotheses=4320,
                cluster_replicates=mixed.FROZEN_CLUSTER_REPLICATES,
                cluster_seed=mixed.FROZEN_CLUSTER_SEED,
                max_states=2,
                max_bootstrap_evaluations=100,
            )
        self.assertTrue(frozen_block["frozen_replicates_satisfied"])
        self.assertFalse(frozen_block["production_parameters_satisfied"])
        self.assertEqual(frozen_block["binding_mode"], "control_cluster_rows")
        self.assertEqual(
            frozen_block["required_bootstrap_evaluations"], 345_600
        )
        self.assertEqual(
            frozen_block["status"], "BLOCKED_BOOTSTRAP_EVALUATION_LIMIT"
        )
        self.assertFalse(frozen_block["production_eligible"])

        analysis_rows = [
            analysis_row("a", 40759, lower=0, upper=3, index=0),
            analysis_row("b", 40759, lower=2, upper=5, index=1),
            analysis_row("c", 232189, lower=0, upper=3, index=2),
            analysis_row("d", 232189, lower=2, upper=5, index=3),
        ]
        genuine_rows, genuine_series, genuine_digest = (
            mixed.cluster_rows_from_analysis_rows(
                analysis_rows,
                endpoint="rank_lt_r",
                denominator="admitted",
            )
        )
        exploit_parameters = {
            "series": genuine_series,
            "endpoint": "rank_lt_r",
            "denominator": "admitted",
            "input_rowset_sha256": genuine_digest,
            "familywise_alpha": mixed.FROZEN_FAMILYWISE_ALPHA,
            "simultaneous_hypotheses": mixed.FROZEN_SIMULTANEOUS_HYPOTHESES,
            "cluster_replicates": mixed.FROZEN_CLUSTER_REPLICATES,
            "cluster_seed": mixed.FROZEN_CLUSTER_SEED,
            "max_row_visits": 100,
        }
        genuine_raw_block = mixed.optimize_nested_cluster_bootstrap(
            genuine_rows, **exploit_parameters
        )
        self.assertFalse(
            genuine_raw_block["production_parameters_satisfied"]
        )
        self.assertEqual(
            genuine_raw_block["binding_mode"], "control_cluster_rows"
        )
        self.assertNotIn("analysis_replay", genuine_raw_block)
        promotion_arguments = {
            "binding_mode": "validated_analysis_rows",
            "production_parameters_satisfied": True,
            "production_eligible": True,
            "receipt": object(),
            "capability": object(),
            "_analysis_binding": object(),
        }
        for argument, value in promotion_arguments.items():
            with self.subTest(promotion_argument=argument):
                with self.assertRaises(TypeError):
                    mixed.optimize_nested_cluster_bootstrap(
                        genuine_rows,
                        **exploit_parameters,
                        **{argument: value},
                    )

        strict_parameters = {
            "endpoint": "rank_lt_r",
            "denominator": "admitted",
            "familywise_alpha": mixed.FROZEN_FAMILYWISE_ALPHA,
            "simultaneous_hypotheses": (
                mixed.FROZEN_SIMULTANEOUS_HYPOTHESES
            ),
            "cluster_replicates": mixed.FROZEN_CLUSTER_REPLICATES,
            "cluster_seed": mixed.FROZEN_CLUSTER_SEED,
            "max_row_visits": 100,
        }
        with self.assertRaises(mixed.MixedCensoringError):
            mixed.optimize_nested_cluster_bootstrap_rows(
                genuine_rows,
                **strict_parameters,
            )
        altered_rows = [dict(row) for row in analysis_rows]
        altered_rows[0]["unvalidated_extra"] = True
        with self.assertRaises(mixed.MixedCensoringError):
            mixed.optimize_nested_cluster_bootstrap_rows(
                altered_rows,
                **strict_parameters,
            )
        with self.assertRaises(TypeError):
            mixed.optimize_nested_cluster_bootstrap_rows(
                analysis_rows,
                **strict_parameters,
                production_parameters_satisfied=True,
            )
        with mock.patch.object(
            mixed,
            "_iter_bootstrap_plan",
            side_effect=AssertionError("must not sample"),
        ):
            validated_block = mixed.optimize_nested_cluster_bootstrap_rows(
                analysis_rows,
                **strict_parameters,
            )
        self.assertTrue(validated_block["production_parameters_satisfied"])
        self.assertEqual(
            validated_block["binding_mode"], "validated_analysis_rows"
        )
        self.assertEqual(
            validated_block["status"], "BLOCKED_ROW_VISIT_LIMIT"
        )
        self.assertEqual(validated_block["required_row_visits"], 2_764_800)
        self.assertFalse(validated_block["production_eligible"])
        for field in (
            "status",
            "state_count",
            "required_plan_entries",
            "required_bootstrap_evaluations",
            "required_row_visits",
            "cluster_rowset_sha256",
            "derived_cluster_seed",
            "minimum",
        ):
            self.assertEqual(
                validated_block[field],
                genuine_raw_block[field],
                field,
            )
        self.assertTrue(mixed.verify_certificate_digest(validated_block))

    def test_cluster_bootstrap_fails_closed_on_aggregate_box(self):
        result = mixed.cluster_bootstrap_fail_closed(
            [cell(101, 10, 1, 2), cell(211, 10, 1, 2)],
            evaluator_sha256=DIGEST,
        )
        self.assertEqual(
            result["status"], "BLOCKED_NEEDS_ROW_LEVEL_CLUSTER_ALLOCATION"
        )
        self.assertFalse(result["exact_integer_box"])
        self.assertEqual(result["evaluated_states"], 0)
        self.assertTrue(mixed.verify_certificate_digest(result))

    def test_single_prime_poisson_fails_closed(self):
        result = mixed.optimize_poisson_hoeffding(
            [cell(101, 10, 1, 2)],
            familywise_alpha=0.05,
            simultaneous_hypotheses=1,
        )
        self.assertEqual(result["status"], "BLOCKED_UNIDENTIFIABLE_DESIGN")
        self.assertTrue(mixed.verify_certificate_digest(result))


if __name__ == "__main__":
    unittest.main()
