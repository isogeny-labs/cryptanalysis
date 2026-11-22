#!/usr/bin/env python3
"""Synthetic-only tests for the fail-closed rank-decay analyzer."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import analyze
from prime_manifest import derive_primes
import sensitivity


def _digest(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


TEST_FREEZE = {
    "schema": "synthetic-test-freeze/v1",
    "analysis": {
        "familywise_alpha": 0.05,
        "simultaneous_hypotheses": 48,
        "endpoints": ["rank_lt_r", "nontrivial_useful_recovery"],
        "denominators": ["admitted", "proposed"],
        "unresolved_allocations": ["all_failure", "all_success"],
        "methods": [
            "conditional_poisson",
            "binomial_cloglog",
            "cluster_robust_cloglog",
        ],
        "cluster_method": "cluster_bootstrap_cloglog",
        "cluster_keys": ["bits", "p", "source_id", "curve_id"],
        "cluster_replicates": 3,
        "cluster_seed": "synthetic-cluster-seed",
        "useful_event_min_bits": 20,
    },
}
TEST_ONLY_GATES = {
    "test_only_allow_small_bootstrap": True,
    "test_only_provenance_verified": True,
    "test_only_interval_allocation_verified": True,
    "test_only_relation_inventory_verified": True,
}


def _tool(
    lower: int | None = 0,
    upper: int | None = 0,
    *,
    status: str = "certified",
    version: str = "synthetic-1",
) -> dict[str, object]:
    if status != "certified":
        lower = upper = None
    return {
        "status": status,
        "version": version,
        "lower": lower,
        "upper": upper,
        "exact": status == "certified" and lower == upper,
        "wall_ns": 1,
    }


def _outcome_none() -> dict[str, object]:
    return {
        "selected_dependence": "CERT_NO",
        "relation_class": "none",
        "rational_relation_replay": "UNKNOWN",
        "relation_certificate_sha256": None,
        "relation_proof_verified": False,
        "target_coefficient_invertible": "UNKNOWN",
        "scalar_replay": "UNKNOWN",
        "source_replay_sha256": None,
        "source_replay_proof_verified": False,
        "useful_recovery": "CERT_NO",
    }


def _outcome_unknown() -> dict[str, object]:
    return {
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
    }


def _outcome_useful(relation_class: str = "nontrivial") -> dict[str, object]:
    return {
        "selected_dependence": "CERT_YES",
        "relation_class": relation_class,
        "rational_relation_replay": "CERT_YES",
        "relation_certificate_sha256": _digest(
            f"relation-proof-{relation_class}"
        ),
        "relation_proof_verified": True,
        "target_coefficient_invertible": "CERT_YES",
        "scalar_replay": "CERT_YES",
        "source_replay_sha256": _digest(f"source-proof-{relation_class}"),
        "source_replay_proof_verified": True,
        "useful_recovery": "CERT_YES",
    }


def _work(complete: bool = True) -> dict[str, object]:
    return {
        "complete": complete,
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
    }


def _row(
    label: str,
    *,
    prime: int,
    stage: str = "discovery",
    index: int = 0,
    planned: int = 1,
    lower: int = 0,
    upper: int = 3,
    r: int = 4,
    pari: dict[str, object] | None = None,
    magma: dict[str, object] | None = None,
    outcome: dict[str, object] | None = None,
) -> dict[str, object]:
    seed = f"seed-{stage}"
    return {
        "schema": analyze.ROW_SCHEMA,
        "trial_id": f"trial-{label}",
        "master_seed": seed,
        "stage": stage,
        "panel": "primary",
        "arm": "baseline",
        "p": prime,
        "bits": prime.bit_length(),
        "curve_family": "generic",
        "lift_strategy": "balanced",
        "local_arm": "A_none",
        "r": r,
        "index": index,
        "planned_trials": planned,
        "source_id": f"source-{label}",
        "curve_id": f"curve-{label}",
        "isomorphism_class_id": f"iso-{label}",
        "lift_digest": _digest(f"lift-{label}"),
        "status": "ranked",
        "rank": {
            "pari": pari if pari is not None else _tool(lower, upper),
            "magma": magma if magma is not None else _tool(lower, upper),
        },
        "outcome": outcome if outcome is not None else _outcome_none(),
        "work": _work(),
    }


def _prime_by_bits(seed: str, slot: int = 0) -> dict[int, int]:
    return {
        item["bits"]: item["prime"]
        for item in derive_primes(seed)
        if item["slot"] == slot
    }


class ValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.prime = _prime_by_bits("test-validation")[16]

    def test_rank_interval_classification_and_conflict(self) -> None:
        lt = analyze.validate_row(_row("lt", prime=self.prime))
        self.assertEqual(analyze.classify_rank(lt)["rank_class"], "CERT_LT")
        self.assertTrue(analyze.classify_rank(lt)["double_certified"])

        ge = analyze.validate_row(
            _row("ge", prime=self.prime, lower=4, upper=6)
        )
        self.assertEqual(analyze.classify_rank(ge)["rank_class"], "CERT_GE")

        unknown = analyze.validate_row(
            _row("unknown", prime=self.prime, lower=2, upper=5)
        )
        self.assertEqual(analyze.classify_rank(unknown)["rank_class"], "UNKNOWN")

        conflict = analyze.validate_row(
            _row(
                "conflict",
                prime=self.prime,
                pari=_tool(0, 2),
                magma=_tool(4, 5),
            )
        )
        classified = analyze.classify_rank(conflict)
        self.assertEqual(classified["rank_class"], "UNKNOWN")
        self.assertTrue(classified["conflict"])

    def test_one_tool_side_is_not_double_certified(self) -> None:
        row = analyze.validate_row(
            _row(
                "single",
                prime=self.prime,
                pari=_tool(0, 3),
                magma=_tool(status="timeout"),
            )
        )
        classified = analyze.classify_rank(row)
        self.assertEqual(classified["rank_class"], "UNKNOWN")
        self.assertEqual(classified["tool_sides"]["pari"], "CERT_LT")
        self.assertFalse(classified["double_certified"])

    def test_staged_pari_magma_rank_rule(self) -> None:
        pari_ge = analyze.validate_row(
            _row(
                "pari-ge",
                prime=self.prime,
                pari=_tool(4, 6),
                magma=_tool(status="unavailable"),
            )
        )
        self.assertEqual(analyze.classify_rank(pari_ge)["rank_class"], "CERT_GE")

        resolved_lt = analyze.validate_row(
            _row(
                "resolved-lt",
                prime=self.prime,
                pari=_tool(2, 5),
                magma=_tool(1, 3),
            )
        )
        self.assertEqual(
            analyze.classify_rank(resolved_lt)["rank_class"], "CERT_LT"
        )
        self.assertTrue(analyze.classify_rank(resolved_lt)["event_confirmed"])

        missing_pari = analyze.validate_row(
            _row(
                "missing-pari",
                prime=self.prime,
                pari=_tool(status="timeout"),
                magma=_tool(0, 3),
            )
        )
        self.assertEqual(
            analyze.classify_rank(missing_pari)["rank_class"], "UNKNOWN"
        )

    def test_failed_replay_is_preserved(self) -> None:
        outcome = {
            "selected_dependence": "CERT_YES",
            "relation_class": "nontrivial",
            "rational_relation_replay": "CERT_YES",
            "relation_certificate_sha256": _digest("failed-replay-relation"),
            "relation_proof_verified": True,
            "target_coefficient_invertible": "CERT_YES",
            "scalar_replay": "CERT_NO",
            "source_replay_sha256": _digest("failed-source-replay"),
            "source_replay_proof_verified": False,
            "useful_recovery": "CERT_NO",
        }
        row = analyze.validate_row(
            _row("failed-replay", prime=self.prime, outcome=outcome)
        )
        self.assertEqual(row["outcome"]["scalar_replay"], "CERT_NO")

    def test_outcome_unknown_is_not_certified_no(self) -> None:
        row = analyze.validate_row(
            _row("outcome-unknown", prime=self.prime, outcome=_outcome_unknown())
        )
        self.assertEqual(analyze.classify_useful_endpoint(row), "UNKNOWN")

    def test_replayed_nonuseful_candidate_is_not_exhaustive_negative(self) -> None:
        none_row = analyze.validate_row(
            _row("candidate-none", prime=self.prime, outcome=_outcome_none())
        )
        trivial_row = analyze.validate_row(
            _row(
                "candidate-trivial",
                prime=self.prime,
                outcome=_outcome_useful("line"),
            )
        )
        self.assertEqual(analyze.classify_useful_endpoint(none_row), "UNKNOWN")
        self.assertEqual(analyze.classify_useful_endpoint(trivial_row), "UNKNOWN")

    def test_useful_recovery_is_independent_of_curve_rank(self) -> None:
        row = analyze.validate_row(
            _row(
                "high-rank-useful",
                prime=self.prime,
                lower=4,
                upper=6,
                outcome=_outcome_useful(),
            )
        )
        self.assertEqual(analyze.classify_rank(row)["rank_class"], "CERT_GE")
        self.assertEqual(analyze.classify_useful_endpoint(row), "CERT_YES")
        self.assertTrue(analyze.is_doubly_certified_nontrivial_useful(row))

    def test_logical_outcome_mismatch_fails_closed(self) -> None:
        bad = _row("bad-outcome", prime=self.prime, outcome=_outcome_unknown())
        bad["outcome"]["useful_recovery"] = "CERT_NO"
        with self.assertRaises(analyze.AnalysisError):
            analyze.validate_row(bad)

    def test_unknown_key_fails_closed(self) -> None:
        bad = _row("extra", prime=self.prime)
        bad["surprise"] = True
        with self.assertRaises(analyze.AnalysisError):
            analyze.validate_row(bad)

    def test_blank_jsonl_line_fails_closed(self) -> None:
        row = _row("jsonl", prime=self.prime)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rows.jsonl"
            path.write_text(json.dumps(row) + "\n\n", encoding="utf-8")
            with self.assertRaises(analyze.AnalysisError):
                analyze.read_jsonl(path)

    def test_duplicate_json_key_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rows.jsonl"
            path.write_text('{"schema":"x","schema":"y"}\n', encoding="utf-8")
            with self.assertRaises(analyze.AnalysisError):
                analyze.read_jsonl(path)


class AggregationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.prime = _prime_by_bits("test-aggregation")[16]

    def test_agun_and_curve_weighting(self) -> None:
        rows = [
            _row("agg-lt", prime=self.prime, index=0, planned=3),
            _row(
                "agg-ge", prime=self.prime, index=1, planned=3, lower=4, upper=5
            ),
            _row(
                "agg-u", prime=self.prime, index=2, planned=3, lower=2, upper=5
            ),
        ]
        cell = analyze.aggregate_cells(
            [analyze.validate_row(row) for row in rows]
        )[0]
        self.assertEqual(
            {
                key: cell["configuration_weighted"][key]
                for key in ("A", "G", "U", "N")
            },
            {"A": 1, "G": 1, "U": 1, "N": 3},
        )
        self.assertEqual(cell["configuration_weighted"]["q_min"]["value"], 1 / 3)
        self.assertEqual(cell["configuration_weighted"]["q_max"]["value"], 2 / 3)
        self.assertEqual(cell["distinct_q_isomorphism_curve_weighted"]["N"], 3)

    def test_incomplete_cell_roster_fails_closed(self) -> None:
        row = _row("missing-index", prime=self.prime, index=0, planned=2)
        with self.assertRaises(analyze.AnalysisError):
            analyze.analyze(
                [row], familywise_alpha=0.05, simultaneous_hypotheses=8
            )

    def test_ranked_non_success_remains_unknown_for_useful_endpoint(self) -> None:
        rows = [
            _row(
                "recovery-u",
                prime=self.prime,
                index=0,
                planned=2,
                outcome=_outcome_unknown(),
            ),
            _row(
                "rank-u-outcome-no",
                prime=self.prime,
                index=1,
                planned=2,
                lower=2,
                upper=5,
                outcome=_outcome_none(),
            ),
        ]
        rows = [analyze.validate_row(row) for row in rows]
        useful = analyze._profile_inputs(
            rows, "nontrivial_useful_recovery", "admitted", "all_success"
        )
        rank = analyze._profile_inputs(rows, "rank_lt_r", "admitted", "all_success")
        # Neither a missing candidate nor replay of a non-useful candidate is
        # an exhaustive negative relation certificate.  Both remain censored.
        self.assertEqual(useful[0][1:], (2, 2))
        self.assertEqual(rank[0][1:], (2, 2))


class ProfileTests(unittest.TestCase):
    def test_signed_profile_slope_and_conservative_interval(self) -> None:
        fit = analyze.poisson_profile(
            [(2**16, 10_000, 1_000), (2**18, 10_000, 500), (2**20, 10_000, 250)],
            familywise_alpha=0.05,
            simultaneous_hypotheses=8,
        )
        self.assertTrue(fit["identifiable"])
        self.assertAlmostEqual(fit["beta_hat"], -0.5, places=10)
        self.assertLess(fit["confidence_interval"]["lower"], -0.5)
        self.assertGreater(fit["confidence_interval"]["upper"], -0.5)
        self.assertIn("finite-sample conservative", fit["interval_method"])

    def test_no_events_is_unidentifiable(self) -> None:
        fit = analyze.poisson_profile(
            [(2**16, 100, 0), (2**18, 100, 0)],
            familywise_alpha=0.05,
            simultaneous_hypotheses=1,
        )
        self.assertFalse(fit["identifiable"])
        self.assertIsNone(fit["confidence_interval"]["lower"])

    def test_too_small_simultaneous_count_fails(self) -> None:
        prime = _prime_by_bits("test-profile-count")[16]
        row = _row("profile-count", prime=prime)
        with self.assertRaises(analyze.AnalysisError):
            analyze.analyze(
                [row], familywise_alpha=0.05, simultaneous_hypotheses=23
            )

    def test_binomial_cloglog_profile_has_signed_slope(self) -> None:
        fit = sensitivity.fit_binomial_cloglog(
            [
                (2**16, 100_000, 1_000),
                (2**18, 100_000, 500),
                (2**20, 100_000, 250),
            ],
            familywise_alpha=0.05,
            simultaneous_hypotheses=1,
        )
        self.assertTrue(fit["identifiable"])
        self.assertLess(fit["beta_hat"], -0.49)
        self.assertGreater(fit["beta_hat"], -0.51)

    def test_uniform_unknown_corners_do_not_bound_mixed_slope(self) -> None:
        common = {
            "familywise_alpha": 0.05,
            "simultaneous_hypotheses": 1,
        }
        all_failure = analyze.poisson_profile(
            [(101, 100, 10), (404, 100, 7)], **common
        )
        all_success = analyze.poisson_profile(
            [(101, 100, 100), (404, 100, 100)], **common
        )
        adversarial_mixed = analyze.poisson_profile(
            [(101, 100, 100), (404, 100, 7)], **common
        )
        self.assertAlmostEqual(all_failure["beta_hat"], -0.2572865864, places=8)
        self.assertAlmostEqual(all_success["beta_hat"], 0.0, places=12)
        self.assertAlmostEqual(
            adversarial_mixed["beta_hat"], -1.9182506339, places=8
        )
        self.assertLess(adversarial_mixed["beta_hat"], -0.8)


def _passing_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    by_stage = {
        "discovery": _prime_by_bits("synthetic-discovery"),
        "replication": _prime_by_bits("synthetic-replication"),
    }
    for stage, primes in by_stage.items():
        for bits in (16, 18, 20, 22, 24):
            prime = primes[bits]
            for index in range(100):
                label = f"{stage}-{bits}-{index}"
                useful = index < 50
                row = _row(
                    label,
                    prime=prime,
                    stage=stage,
                    index=index,
                    planned=100,
                    lower=0 if useful else 4,
                    upper=3 if useful else 5,
                    outcome=_outcome_useful() if useful else _outcome_none(),
                )
                rows.append(row)
    return rows


def _robustness_artifact(
    rows: list[dict[str, object]],
    freeze: dict[str, object] = TEST_FREEZE,
) -> dict[str, object]:
    return sensitivity.compute_artifact(
        rows,
        artifact_id="synthetic-test-only",
        freeze_manifest_sha256=analyze.freeze_object_sha256(freeze),
        familywise_alpha=0.05,
        simultaneous_hypotheses=48,
        cluster_replicates=3,
        cluster_seed="synthetic-cluster-seed",
        useful_event_min_bits=freeze["analysis"]["useful_event_min_bits"],
    )


class DecisionTests(unittest.TestCase):
    def test_test_only_overrides_never_authorize_a_verdict(self) -> None:
        rows = _passing_rows()
        result = analyze.analyze(
            rows,
            familywise_alpha=0.05,
            simultaneous_hypotheses=48,
            robustness_artifact=_robustness_artifact(rows),
            trusted_freeze=TEST_FREEZE,
            **TEST_ONLY_GATES,
        )
        self.assertFalse(result["decision"]["defeated_in_scope"])
        self.assertEqual(
            result["decision"]["classification"], "NOT_DEFEATED_IN_SCOPE"
        )
        self.assertFalse(
            result["decision"]["synthetic_would_pass_if_verified"]
        )
        self.assertEqual(result["decision"]["passing_factor_cells"], [])
        candidate = result["decision"]["factor_cells"][0]
        self.assertFalse(candidate["passed"])
        self.assertFalse(candidate["synthetic_would_pass_if_verified"])
        self.assertIn(
            "test-only overrides cannot authorize a production verdict",
            candidate["reasons"],
        )
        self.assertEqual(
            candidate["doubly_certified_nontrivial_useful_recoveries"], 300
        )
        self.assertEqual(
            candidate["qualifying_useful_recoveries_by_stage"],
            {"discovery": 150, "replication": 150},
        )
        self.assertTrue(
            any(
                "nontrivial_useful_recovery/binomial_cloglog/admitted/"
                "all_success" in reason
                for reason in candidate["reasons"]
            )
        )

    def test_otherwise_qualifying_fixture_fails_without_sensitivity(self) -> None:
        result = analyze.analyze(
            _passing_rows(),
            familywise_alpha=0.05,
            simultaneous_hypotheses=48,
        )
        self.assertFalse(result["decision"]["defeated_in_scope"])
        self.assertIn(
            "frozen binomial-cloglog and cluster-robust sensitivity artifact is absent",
            result["decision"]["factor_cells"][0]["reasons"],
        )

    def test_production_rejects_underresolved_bootstrap(self) -> None:
        rows = _passing_rows()
        with self.assertRaises(analyze.AnalysisError):
            analyze.analyze(
                rows,
                familywise_alpha=0.05,
                simultaneous_hypotheses=48,
                robustness_artifact=_robustness_artifact(rows),
                trusted_freeze=TEST_FREEZE,
            )

    def test_unimplemented_production_gates_block_decision(self) -> None:
        rows = _passing_rows()
        result = analyze.analyze(
            rows,
            familywise_alpha=0.05,
            simultaneous_hypotheses=48,
            robustness_artifact=_robustness_artifact(rows),
            trusted_freeze=TEST_FREEZE,
            test_only_allow_small_bootstrap=True,
        )
        self.assertFalse(result["decision"]["defeated_in_scope"])
        reasons = result["decision"]["factor_cells"][0]["reasons"]
        self.assertTrue(any("provenance" in reason for reason in reasons))
        self.assertEqual(
            result["provenance_gate"]["status"],
            "BLOCKED_NO_FREEZE_BOUND_ROW_MANIFEST",
        )
        self.assertFalse(result["provenance_gate"]["production_verified"])
        self.assertTrue(any("mixed per-prime" in reason for reason in reasons))

    def test_incomplete_work_mutation_blocks_decision(self) -> None:
        rows = _passing_rows()
        rows[0]["work"]["complete"] = False
        result = analyze.analyze(
            rows,
            familywise_alpha=0.05,
            simultaneous_hypotheses=48,
            robustness_artifact=_robustness_artifact(rows),
            trusted_freeze=TEST_FREEZE,
            **TEST_ONLY_GATES,
        )
        self.assertFalse(result["decision"]["defeated_in_scope"])
        self.assertIn(
            "complete work accounting is false on at least one row",
            result["decision"]["factor_cells"][0]["reasons"],
        )

    def test_low_bit_event_mass_cannot_satisfy_frozen_cutoff(self) -> None:
        rows = _passing_rows()
        for row in rows:
            if row["bits"] >= 20 and row["index"] >= 2:
                row["outcome"] = _outcome_none()
        result = analyze.analyze(
            rows,
            familywise_alpha=0.05,
            simultaneous_hypotheses=48,
            robustness_artifact=_robustness_artifact(rows),
            trusted_freeze=TEST_FREEZE,
            **TEST_ONLY_GATES,
        )
        self.assertFalse(result["decision"]["defeated_in_scope"])
        candidate = result["decision"]["factor_cells"][0]
        self.assertEqual(
            candidate["doubly_certified_useful_recoveries_all_bits"], 212
        )
        self.assertEqual(
            candidate["doubly_certified_nontrivial_useful_recoveries"], 12
        )
        self.assertTrue(
            any("at or above the frozen bit cutoff" in reason for reason in candidate["reasons"])
        )

    def test_missing_tool_result_is_unknown_not_a_certified_event(self) -> None:
        rows = _passing_rows()
        rows[0]["rank"]["magma"] = _tool(status="timeout")
        result = analyze.analyze(
            rows,
            familywise_alpha=0.05,
            simultaneous_hypotheses=48,
            robustness_artifact=_robustness_artifact(rows),
            trusted_freeze=TEST_FREEZE,
            **TEST_ONLY_GATES,
        )
        first_cell = next(
            cell
            for cell in result["cells"]
            if cell["cell"]["stage"] == "discovery"
            and cell["cell"]["bits"] == 16
        )
        self.assertEqual(first_cell["configuration_weighted"]["U"], 1)
        self.assertFalse(result["decision"]["defeated_in_scope"])
        self.assertFalse(
            result["decision"]["synthetic_would_pass_if_verified"]
        )

    def test_frozen_cutoff_applies_to_both_co_primary_profiles(self) -> None:
        rows = _passing_rows()
        result = analyze.analyze(
            rows,
            familywise_alpha=0.05,
            simultaneous_hypotheses=48,
            robustness_artifact=_robustness_artifact(rows),
            trusted_freeze=TEST_FREEZE,
            **TEST_ONLY_GATES,
        )
        self.assertTrue(result["profiles"])
        for profile in result["profiles"]:
            self.assertEqual(profile["useful_event_min_bits"], 20)
            self.assertTrue(profile["fit"]["entries"])
            self.assertTrue(
                all(entry["p"].bit_length() >= 20 for entry in profile["fit"]["entries"])
            )

    def test_trivial_relation_dominance_mutation_blocks_decision(self) -> None:
        rows = _passing_rows()
        for row in rows:
            if row["outcome"]["useful_recovery"] == "CERT_NO":
                row["outcome"] = _outcome_useful("line")
        result = analyze.analyze(
            rows,
            familywise_alpha=0.05,
            simultaneous_hypotheses=48,
            robustness_artifact=_robustness_artifact(rows),
            trusted_freeze=TEST_FREEZE,
            **TEST_ONLY_GATES,
        )
        self.assertFalse(result["decision"]["defeated_in_scope"])
        self.assertIn(
            "useful outcomes are dominated by trivial relation classes",
            result["decision"]["factor_cells"][0]["reasons"],
        )

    def test_empty_input_never_defeats(self) -> None:
        result = analyze.analyze(
            [], familywise_alpha=0.05, simultaneous_hypotheses=1
        )
        self.assertFalse(result["decision"]["defeated_in_scope"])
        self.assertTrue(result["decision"]["no_natural_data"])

    def test_mutated_cluster_bound_is_rejected_not_trusted(self) -> None:
        rows = _passing_rows()
        artifact = _robustness_artifact(rows)
        profile = next(
            item
            for item in artifact["profiles"]
            if item["method"] == "cluster_robust_cloglog"
        )
        profile["signed_beta_lower"] = -0.9
        with self.assertRaises(analyze.AnalysisError):
            analyze.analyze(
                rows,
                familywise_alpha=0.05,
                simultaneous_hypotheses=48,
                robustness_artifact=artifact,
                trusted_freeze=TEST_FREEZE,
                **TEST_ONLY_GATES,
            )

    def test_robustness_artifact_is_bound_to_exact_rows(self) -> None:
        rows = _passing_rows()
        artifact = _robustness_artifact(rows)
        artifact["input_rowset_sha256"] = "0" * 64
        with self.assertRaises(analyze.AnalysisError):
            analyze.analyze(
                rows,
                familywise_alpha=0.05,
                simultaneous_hypotheses=48,
                robustness_artifact=artifact,
                trusted_freeze=TEST_FREEZE,
                **TEST_ONLY_GATES,
            )

    def test_robustness_implementation_hash_is_verified(self) -> None:
        rows = _passing_rows()
        artifact = _robustness_artifact(rows)
        artifact["sensitivity_implementation_sha256"] = "0" * 64
        with self.assertRaises(analyze.AnalysisError):
            analyze.analyze(
                rows,
                familywise_alpha=0.05,
                simultaneous_hypotheses=48,
                robustness_artifact=artifact,
                trusted_freeze=TEST_FREEZE,
                **TEST_ONLY_GATES,
            )

    def test_freeze_parameters_are_semantically_bound(self) -> None:
        rows = _passing_rows()
        artifact = _robustness_artifact(rows)
        mismatched = copy.deepcopy(TEST_FREEZE)
        mismatched["analysis"]["cluster_seed"] = "post-outcome-seed"
        artifact["freeze_manifest_sha256"] = analyze.freeze_object_sha256(mismatched)
        with self.assertRaises(analyze.AnalysisError):
            analyze.analyze(
                rows,
                familywise_alpha=0.05,
                simultaneous_hypotheses=48,
                robustness_artifact=artifact,
                trusted_freeze=mismatched,
                **TEST_ONLY_GATES,
            )


if __name__ == "__main__":
    unittest.main()
