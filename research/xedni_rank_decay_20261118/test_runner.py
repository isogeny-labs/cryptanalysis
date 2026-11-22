#!/usr/bin/env python3
"""Deterministic runner controls; no natural row or real checkpoint is run."""

from __future__ import annotations

import copy
import contextlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


sys.path.insert(0, str(Path(__file__).resolve().parent))
import local_conditions
import runner


def tiny_source() -> dict:
    points = [[2, 8], [12, 3], [16, 16], [8, 8], [7, 9], [6, 15]]
    return {
        "schema": "xedni-rank-decay-source/v1",
        "master_seed": "tiny-control-only",
        "source_id": "tiny-f17-runner-control",
        "source_index": 0,
        "p": 17,
        "bits": 5,
        "family": "generic",
        "curve": {"a": 1, "b": 3, "generation_attempts": 1},
        "cardinality": 17,
        "cardinality_factors": [[17, 1]],
        "cardinality_backend": "hand-certified-control",
        "source_subgroup_order": 17,
        "source_cofactor": 1,
        "base_point": [2, 8],
        "base_point_order": 17,
        "point_sampling_attempts": 1,
        "scalar_sampling_attempts": 6,
        "max_r": 6,
        "ordered_scalars": [1, 2, 3, 4, 5, 6],
        "ordered_points": points,
        "prefix_permutation": list(range(6)),
        "prefixes": {
            str(r): {"indices": list(range(r)), "target_index": r - 1}
            for r in range(2, 7)
        },
    }


def pari_tool() -> dict:
    return {
        "available": True,
        "executable_resolved": "/fake/pari",
        "version_returncode": 0,
        "version_timed_out": False,
        "version_stdout": "GP/PARI CALCULATOR Version 2.17.2",
        "version_stderr": "",
    }


def magma_tool() -> dict:
    return {
        "available": True,
        "executable_resolved": "/fake/magma",
        "version_returncode": 0,
        "version_timed_out": False,
        "version_stdout": "XEDNI_MAGMA_VERSION=2.29-10\n",
        "version_stderr": "",
    }


class RecordingOptimizer:
    def __call__(self, payload, *, radius, max_candidates):
        return {
            "schema_version": 1,
            "operation": "xedni-lift",
            "status": "complete",
            "model": "weierstrass",
            "search": {"radius": radius, "max_candidates": max_candidates},
            "result": {
                "optimized_coefficients": list(payload["particular"]),
                "optimized_score": {"nonsingular": True},
                "candidates_evaluated": 1,
                "exact_constraints_preserved": True,
                "congruence_preserved": True,
            },
        }


def rank_result(
    tool_name: str,
    row: dict,
    tool_record: dict,
    classification: str,
    lower,
    upper,
    timeout: float,
    effort: int,
) -> dict:
    module = runner.rank_pari if tool_name == "pari" else runner.rank_magma
    result = module._base(row, tool_record)
    row_id, r, ainvs = runner.rank_pari.validate_row(row)
    result.update(
        row_id=row_id,
        r=r,
        ainvs=[str(value) for value in ainvs],
        classification=classification,
        rank_bounds={"lower": lower, "upper": upper},
    )
    script = (
        runner.rank_pari.make_script(ainvs, effort)
        if tool_name == "pari"
        else runner.rank_magma.make_script(ainvs, effort)
    )
    if lower is None or upper is None:
        result["reason"] = "timeout"
        stdout = ""
        returncode = None
        timed_out = True
    else:
        _, result["reason"] = runner.rank_pari.classify(lower, upper, r)
        stdout = (
            "XEDNI_RANK_BEGIN\n"
            f"LOWER={lower}\nUPPER={upper}\n"
            "SHA2_RANK=0\nPOINT_COUNT=0\nPARISIZEMAX=2147483648\n"
            "XEDNI_RANK_END\n"
            if tool_name == "pari"
            else (
                "XEDNI_RANK_BEGIN\n"
                f"LOWER={lower}\nUPPER={upper}\n"
                "XEDNI_RANK_END\n"
            )
        )
        returncode = 0
        timed_out = False
    command = [tool_record["executable_resolved"], "-q", "-f"] if tool_name == "pari" else [tool_record["executable_resolved"], "-b"]
    result["execution"] = {
        "command": command,
        "returncode": returncode,
        "script": script,
        "script_sha256": runner.hashlib.sha256(script.encode()).hexdigest(),
        "stdout": stdout,
        "stderr": "",
        "timed_out": timed_out,
        "timeout_seconds": timeout,
        "wall_ns": 1,
    }
    return result


class RosterTests(unittest.TestCase):
    def test_frozen_primary_roster_counts_hash_and_determinism(self):
        calibration = runner.build_roster("calibration")
        repeated = runner.build_roster("calibration")
        sentinel = runner.build_roster("sentinel")
        self.assertEqual(calibration, repeated)
        self.assertEqual(calibration["counts"], {"executable": 1080, "blocked": 648})
        self.assertEqual(sentinel["counts"], {"executable": 12150, "blocked": 7290})
        self.assertEqual(
            calibration["roster_sha256"],
            runner.object_sha256({k: v for k, v in calibration.items() if k != "roster_sha256"}),
        )
        self.assertTrue(all(row["r"] <= 6 for row in calibration["executable_roster"]))
        self.assertTrue(all(row["r"] >= 7 for row in calibration["blocked_roster"]))

    def test_pairing_keys_share_source_and_local_seed_across_lifts(self):
        rows = runner.build_roster("calibration")["executable_roster"]
        anchor = rows[0]
        paired = [
            row
            for row in rows
            if row["p"] == anchor["p"]
            and row["family"] == anchor["family"]
            and row["index"] == anchor["index"]
            and row["r"] == anchor["r"]
            and row["local_arm"] == anchor["local_arm"]
        ]
        self.assertEqual({row["lift"] for row in paired}, set(runner.LIFTS))
        self.assertEqual(len({row["source_key"] for row in paired}), 1)
        self.assertEqual(len({row["local_seed"] for row in paired}), 1)
        different_r = next(
            row
            for row in rows
            if row["p"] == anchor["p"]
            and row["family"] == anchor["family"]
            and row["index"] == anchor["index"]
            and row["r"] != anchor["r"]
        )
        self.assertEqual(different_r["source_key"], anchor["source_key"])
        self.assertNotEqual(different_r["local_seed"], anchor["local_seed"])

    def test_unfrozen_stages_are_explicitly_blocked(self):
        for stage in ("discovery", "replication"):
            with self.subTest(stage=stage):
                plan = runner.build_roster(stage)
                self.assertEqual(plan["status"], "BLOCKED")
                self.assertEqual(plan["counts"], {"executable": 0, "blocked": 0})


class PreflightTests(unittest.TestCase):
    def test_pinned_gp_wrapper_reports_exact_image_without_docker(self):
        wrapper = Path(runner.DEFAULT_GP)
        completed = subprocess.run(
            [str(wrapper), "--xedni-image-id"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(
            completed.stdout.strip(),
            "sha256:923e7e41d2fe1716fc3f1a6e06486d469b608baa6d6b4b0fdbb6e43b132049cf",
        )
        contents = wrapper.read_text()
        self.assertIn("--network=none", contents)
        self.assertNotIn(":latest", contents)

        observed = runner.rank_pari.probe_tool(str(wrapper))
        self.assertEqual(
            observed["image_digest"],
            "sha256:923e7e41d2fe1716fc3f1a6e06486d469b608baa6d6b4b0fdbb6e43b132049cf",
        )
        self.assertEqual(observed["image_probe_returncode"], 0)

    def test_required_freeze_includes_relation_proposer(self):
        self.assertIn(
            "research/xedni_rank_decay_20261118/relation_pari.py",
            runner.REQUIRED_FROZEN_FILES,
        )

    def test_pari_banner_on_stderr_is_parsed_and_exact_pinned(self):
        observed = pari_tool()
        observed["version_stdout"] = ""
        observed["version_stderr"] = "GP/PARI CALCULATOR Version 2.17.2 (released)\n"
        self.assertTrue(runner._tool_is_available(observed, "PARI"))
        self.assertEqual(runner._parsed_tool_version("pari", observed), "2.17.2")
        self.assertEqual(
            runner._match_tool_pin("pari", {"version": "2.17.2"}, observed)[
                "status"
            ],
            "PASS",
        )
        with self.assertRaises(runner.RunnerError):
            runner._match_tool_pin("pari", {"version": "2.17.1"}, observed)

    def _run(self, events, r_values=(2, 3, 4, 5, 6), magma_record=None, gate=None):
        def freeze_check(path, stage, roster, binary):
            events.append("freeze")
            return {
                "status": "PASS",
                "roster_sha256": roster["roster_sha256"],
                "freeze": {
                    "tools": {
                        "magma": {
                            "version": "2.29-10"
                        },
                        "pari": {"version": "2.17.2"},
                    }
                },
            }

        def magma_probe(executable):
            events.append("magma")
            return magma_tool() if magma_record is None else magma_record

        def pari_probe(executable):
            events.append("pari")
            return pari_tool()

        def gate_check():
            events.append("gate")
            if gate is not None:
                return gate()
            return {
                "status": "PASS",
                "command": ["checkpoint.sh", "gate"],
                "returncode": 0,
                "stdout": "checkpoint control",
                "stderr": "",
            }

        return runner._preflight_core(
            "calibration",
            tuple(r_values),
            freeze_path=Path("control-freeze.json"),
            ca_icx="control-ca-icx",
            gp="control-gp",
            magma="control-magma",
            freeze_check=freeze_check,
            pari_probe=pari_probe,
            magma_probe=magma_probe,
            gate_check=gate_check,
        )

    def test_missing_magma_blocks_before_gate_or_source(self):
        events = []
        missing = copy.deepcopy(magma_tool())
        missing["available"] = False
        with self.assertRaises(runner.RunnerError) as caught:
            self._run(events, magma_record=missing)
        self.assertEqual(caught.exception.code, "magma_unavailable")
        self.assertEqual(events, ["freeze", "magma"])
        self.assertEqual(caught.exception.evidence["natural_rows_started"], 0)

    def test_r7_map_blocks_before_tools_gate_or_source(self):
        events = []
        with self.assertRaises(runner.RunnerError) as caught:
            self._run(events, r_values=(7,))
        self.assertEqual(caught.exception.code, "missing_point_map")
        self.assertEqual(events, ["freeze"])
        self.assertEqual(caught.exception.evidence["natural_rows_started"], 0)

    def test_gate_failure_retains_transcript_and_starts_no_row(self):
        events = []

        def failed_gate():
            evidence = {
                "command": ["checkpoint.sh", "gate"],
                "returncode": 2,
                "stdout": "",
                "stderr": "checkpoint blocked",
            }
            raise runner.RunnerError("checkpoint_gate", "gate failed", evidence)

        with self.assertRaises(runner.RunnerError) as caught:
            self._run(events, gate=failed_gate)
        self.assertEqual(caught.exception.code, "checkpoint_gate")
        self.assertEqual(events, ["freeze", "magma", "pari", "gate"])
        self.assertEqual(caught.exception.evidence["returncode"], 2)
        self.assertIn("checkpoint blocked", caught.exception.evidence["stderr"])

    def test_successful_preflight_order_and_authorization_hash(self):
        events = []
        result = self._run(events)
        self.assertEqual(events, ["freeze", "magma", "pari", "gate"])
        self.assertEqual(result["status"], "BLOCKED_NO_NATURAL_EXECUTOR")
        self.assertEqual(result["natural_rows_started"], 0)
        self.assertRegex(result["preflight_sha256"], r"^[0-9a-f]{64}$")
        self.assertTrue(result["implementation_gaps"])

    def test_empty_and_duplicate_r_values_are_rejected_before_tools(self):
        for values in ((), (2, 2)):
            events = []
            with self.subTest(values=values):
                with self.assertRaises(runner.RunnerError) as caught:
                    self._run(events, r_values=values)
                self.assertEqual(caught.exception.code, "r_values")
                self.assertEqual(events, ["freeze"])

    def test_production_freeze_is_currently_missing_and_blocks(self):
        with tempfile.TemporaryDirectory() as temporary:
            missing = Path(temporary) / "FREEZE.json"
            roster = runner.build_roster("calibration")
            with self.assertRaises(runner.RunnerError) as caught:
                runner.validate_freeze(missing, "calibration", roster, "missing-ca-icx")
        self.assertEqual(caught.exception.code, "freeze_missing")

    def test_freeze_must_explicitly_authorize_natural_rows(self):
        with tempfile.TemporaryDirectory() as temporary:
            freeze = Path(temporary) / "FREEZE.json"
            freeze.write_text('{"natural_rows_authorized":false}\n')
            with self.assertRaises(runner.RunnerError) as caught:
                runner.validate_freeze(
                    freeze,
                    "calibration",
                    runner.build_roster("calibration"),
                    "missing-ca-icx",
                )
        self.assertEqual(caught.exception.code, "natural_rows_not_authorized")


class ExecutorIntegrationTests(unittest.TestCase):
    def _committed_component_state(self):
        """Model the post-commit state while this change is still uncommitted."""
        stack = contextlib.ExitStack()
        stack.enter_context(
            mock.patch.object(
                runner,
                "_head_file_sha256",
                side_effect=lambda relative: runner.file_sha256(
                    runner.REPOSITORY / relative
                ),
            )
        )
        stack.enter_context(
            mock.patch.object(
                runner,
                "_git_file_state",
                return_value={
                    "path": "prospective-post-commit",
                    "tracked": True,
                    "clean_against_head": True,
                    "ls_files_returncode": 0,
                    "diff_returncode": 0,
                },
            )
        )
        return stack

    def test_validation_binds_committed_components_and_starts_zero_rows(self):
        with self._committed_component_state(), mock.patch.object(
            runner,
            "checkpoint_gate",
            side_effect=AssertionError("checkpoint must not be invoked"),
        ):
            report = runner.validate_executor_integration()
        self.assertEqual(report["schema"], runner.EXECUTOR_VALIDATION_SCHEMA)
        self.assertEqual(report["status"], "BLOCKED_NON_PRODUCTION")
        self.assertEqual(report["natural_rows_started"], 0)
        self.assertFalse(report["checkpoint_invoked"])
        self.assertFalse(report["scientific_tools_invoked"])
        self.assertFalse(report["stage_adapters_invoked"])
        self.assertEqual(
            len(report["administrative_git_commands"]),
            3 * len(runner.EXECUTOR_COMPONENTS) + 1,
        )
        self.assertEqual(
            report["administrative_git_commands"][-1]["command"],
            ["git", "rev-parse", "HEAD"],
        )
        for retained in report["administrative_git_commands"]:
            self.assertEqual(retained["command"][0], "git")
        self.assertEqual(len(report["components"]), len(runner.EXECUTOR_COMPONENTS))
        self.assertEqual(
            {component["component"] for component in report["components"]},
            set(runner.EXECUTOR_COMPONENTS),
        )
        for component in report["components"]:
            self.assertTrue(component["tracked"])
            self.assertTrue(component["clean_against_head"])
            self.assertTrue(component["committed_bytes_match"])
            self.assertTrue(component["schemas_match"])
            self.assertFalse(component["freeze_bound"])
            self.assertEqual(
                component["production_blocker"],
                runner.EXECUTOR_COMPONENTS[component["component"]]["blocker"],
            )
            self.assertIn(
                "component_gate:"
                f"{component['component']}:"
                f"{component['production_blocker']}",
                report["blockers"],
            )
        self.assertFalse(report["tool_pins"]["pari"]["pin_schema_complete"])
        self.assertFalse(report["tool_pins"]["magma"]["pin_schema_complete"])
        self.assertFalse(report["tool_pins"]["pari"]["runtime_identity_observed"])
        self.assertFalse(report["tool_pins"]["magma"]["runtime_identity_observed"])
        self.assertIn(
            "wrapper_sha256", report["tool_pins"]["pari"]["missing"]
        )
        self.assertIn(
            "license_fingerprint_sha256",
            report["tool_pins"]["magma"]["missing"],
        )
        self.assertEqual(
            report["gate_canaries"]["executor_production"]["code"],
            "production_blocked",
        )
        provenance = report["gate_canaries"]["row_provenance_diagnostic"]
        self.assertEqual(provenance["status"], "HASH_GRAPH_ONLY")
        self.assertFalse(provenance["production_eligible"])
        self.assertFalse(provenance["files_verified"])
        self.assertIn("constants", report["gate_canaries"]["schema_scope"])
        expected_hash = runner.object_sha256(
            {key: value for key, value in report.items() if key != "validation_sha256"}
        )
        self.assertEqual(report["validation_sha256"], expected_hash)

    def test_component_hash_and_schema_mutations_fail_closed(self):
        with self._committed_component_state(), mock.patch.object(
            runner, "_head_file_sha256", return_value="0" * 64
        ):
            with self.assertRaises(runner.RunnerError) as caught:
                runner.validate_executor_integration()
        self.assertEqual(caught.exception.code, "executor_component_mismatch")
        self.assertEqual(caught.exception.evidence["natural_rows_started"], 0)

        with self._committed_component_state(), mock.patch.object(
            runner.public_boundary,
            "PUBLIC_SOURCE_SCHEMA",
            "forged-public-source/v1",
        ):
            with self.assertRaises(runner.RunnerError) as caught:
                runner.validate_executor_integration()
        self.assertEqual(caught.exception.code, "executor_component_mismatch")
        self.assertEqual(caught.exception.evidence["natural_rows_started"], 0)

    def test_each_new_component_byte_mutation_fails_closed(self):
        new_components = {
            "mixed_censoring",
            "cubic_jacobian_map",
            "relation_lattice",
            "verifier_receipts",
            "allocation_planner",
        }
        for selected in sorted(new_components):
            selected_path = runner.EXECUTOR_COMPONENTS[selected]["path"]

            def head_hash(relative, *, changed=selected_path):
                if relative == changed:
                    return "0" * 64
                return runner.file_sha256(runner.REPOSITORY / relative)

            with self.subTest(component=selected), self._committed_component_state(), mock.patch.object(
                runner, "_head_file_sha256", side_effect=head_hash
            ):
                with self.assertRaises(runner.RunnerError) as caught:
                    runner.validate_executor_integration()
                self.assertEqual(caught.exception.code, "executor_component_mismatch")
                self.assertEqual(caught.exception.evidence["errors"], [selected])
                self.assertEqual(caught.exception.evidence["natural_rows_started"], 0)

    def test_each_new_component_schema_mutation_fails_closed(self):
        mutations = {
            "mixed_censoring": (runner.mixed_censoring, "SCHEMA"),
            "cubic_jacobian_map": (runner.cubic_jacobian_map, "VERIFY_SCHEMA"),
            "relation_lattice": (runner.relation_lattice, "CERTIFICATE_SCHEMA"),
            "verifier_receipts": (runner.verifier_receipts, "RECEIPT_SCHEMA"),
            "allocation_planner": (runner.allocation_planner, "SCHEMA"),
        }
        for selected, (module, attribute) in mutations.items():
            with self.subTest(component=selected), self._committed_component_state(), mock.patch.object(
                module, attribute, "forged-schema/v1"
            ):
                with self.assertRaises(runner.RunnerError) as caught:
                    runner.validate_executor_integration()
                self.assertEqual(caught.exception.code, "executor_component_mismatch")
                self.assertEqual(caught.exception.evidence["errors"], [selected])
                self.assertEqual(caught.exception.evidence["natural_rows_started"], 0)

    def test_production_flag_mutation_is_rejected_before_any_gate(self):
        modules = {
            "runner": runner,
            "public_boundary": runner.public_boundary,
            "natural_executor": runner.natural_executor,
            "mixed_censoring": runner.mixed_censoring,
            "cubic_jacobian_map": runner.cubic_jacobian_map,
            "relation_lattice": runner.relation_lattice,
            "verifier_receipts": runner.verifier_receipts,
            "allocation_planner": runner.allocation_planner,
        }
        for selected, module in modules.items():
            with self.subTest(component=selected), self._committed_component_state(), mock.patch.object(
                module, "PRODUCTION_READY", True
            ), mock.patch.object(
                runner,
                "checkpoint_gate",
                side_effect=AssertionError("checkpoint must not be invoked"),
            ):
                with self.assertRaises(runner.RunnerError) as caught:
                    runner.validate_executor_integration()
                self.assertEqual(caught.exception.code, "executor_component_mismatch")
                self.assertEqual(caught.exception.evidence["errors"], [selected])
                self.assertEqual(caught.exception.evidence["natural_rows_started"], 0)

    def test_strict_tool_pin_shape_and_version_mutations_are_rejected(self):
        freeze = {
            "tools": {
                "pari": {
                    "available": True,
                    "version": "x",
                    "image_digest": "x",
                    "wrapper_sha256": "x",
                },
                "magma": {
                    "available": True,
                    "version": "x",
                    "executable_sha256": "x",
                    "license_fingerprint_sha256": "x",
                },
            }
        }
        report = runner._strict_tool_pin_status(freeze)
        self.assertFalse(report["pari"]["pin_schema_complete"])
        self.assertFalse(report["magma"]["pin_schema_complete"])
        self.assertEqual(
            set(report["pari"]["invalid"]),
            {"version", "image_digest", "wrapper_sha256"},
        )
        self.assertEqual(
            set(report["magma"]["invalid"]),
            {"version", "executable_sha256", "license_fingerprint_sha256"},
        )

        zero_identity = copy.deepcopy(freeze)
        zero_identity["tools"]["pari"].update(
            version="2.17.2",
            image_digest="sha256:" + "0" * 64,
            wrapper_sha256="0" * 64,
        )
        zero_identity["tools"]["magma"].update(
            version="2.29-10",
            executable_sha256="0" * 64,
            license_fingerprint_sha256="0" * 64,
        )
        zero_report = runner._strict_tool_pin_status(zero_identity)
        self.assertFalse(zero_report["pari"]["pin_schema_complete"])
        self.assertFalse(zero_report["magma"]["pin_schema_complete"])

        valid = copy.deepcopy(freeze)
        valid["tools"]["pari"].update(
            version=runner.STRICT_PARI_VERSION,
            image_digest=runner.STRICT_PARI_IMAGE_DIGEST,
            wrapper_sha256=runner.file_sha256(Path(runner.DEFAULT_GP)),
        )
        valid["tools"]["magma"].update(
            version=runner.STRICT_MAGMA_VERSION,
            executable_sha256="1" * 64,
            license_fingerprint_sha256="2" * 64,
        )
        valid_report = runner._strict_tool_pin_status(valid)
        self.assertTrue(valid_report["pari"]["pin_schema_complete"])
        self.assertTrue(valid_report["magma"]["pin_schema_complete"])
        self.assertFalse(valid_report["pari"]["runtime_identity_observed"])
        self.assertFalse(valid_report["magma"]["runtime_identity_observed"])

        pari_unavailable = copy.deepcopy(valid)
        pari_unavailable["tools"]["pari"]["available"] = False
        unavailable_report = runner._strict_tool_pin_status(pari_unavailable)
        self.assertFalse(unavailable_report["pari"]["pin_schema_complete"])
        self.assertIn("available", unavailable_report["pari"]["invalid"])
        self.assertIn("available=true", unavailable_report["pari"]["missing"])

    def test_validate_executor_cli_writes_only_blocked_zero_row_evidence(self):
        with self._committed_component_state(), tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "executor-validation.json"
            exit_code = runner.main(
                ["validate-executor", "--output", str(output)]
            )
            retained = json.loads(output.read_text())
        self.assertEqual(exit_code, 2)
        self.assertEqual(retained["status"], "BLOCKED_NON_PRODUCTION")
        self.assertEqual(retained["natural_rows_started"], 0)
        self.assertFalse(retained["checkpoint_invoked"])


class IntegrationTests(unittest.TestCase):
    def test_source_cardinality_evidence_replays_and_mutations_fail(self):
        source = tiny_source()
        program = runner.source_generator.cardinality_program(17, 1, 3)
        stdout = "17\n17 1\n"
        evidence = {
            "status": "complete",
            "backend": "control",
            "command": ["fake-gp", "-q", "-f"],
            "program": program,
            "program_sha256": runner.hashlib.sha256(program.encode()).hexdigest(),
            "returncode": 0,
            "stdout": stdout,
            "stdout_sha256": runner.hashlib.sha256(stdout.encode()).hexdigest(),
            "stderr": "",
            "stderr_sha256": runner.hashlib.sha256(b"").hexdigest(),
            "timed_out": False,
            "timeout_seconds": 60,
            "wall_ns": 1,
            "tool_identity": {
                "kind": "host_executable",
                "executable_sha256": "0" * 64,
                "version_returncode": 0,
                "version_stdout": "GP/PARI CALCULATOR Version 2.17.2",
                "version_stderr": "",
                "wrapper_image_id": "sha256:" + "1" * 64,
            },
        }
        evidence["evidence_sha256"] = runner.object_sha256(evidence)
        source["cardinality_evidence"] = evidence
        self.assertEqual(
            runner.validate_source_cardinality_evidence(source)["status"], "PASS"
        )
        changed = copy.deepcopy(source)
        changed["cardinality_evidence"]["stdout"] = "18\n17 1\n"
        with self.assertRaises(runner.RunnerError):
            runner.validate_source_cardinality_evidence(changed)

        forged = copy.deepcopy(source)
        forged_program = "print(17); print(17, \\\" \\\", 1); quit\n"
        forged["cardinality_evidence"]["program"] = forged_program
        forged["cardinality_evidence"]["program_sha256"] = runner.hashlib.sha256(
            forged_program.encode()
        ).hexdigest()
        forged_evidence = forged["cardinality_evidence"]
        forged_evidence.pop("evidence_sha256")
        forged_evidence["evidence_sha256"] = runner.object_sha256(forged_evidence)
        with self.assertRaises(runner.RunnerError) as caught:
            runner.validate_source_cardinality_evidence(forged)
        self.assertIn("program_replay", caught.exception.evidence["errors"])

    def test_control_runs_local_lift_and_both_rank_adapters_with_transcripts(self):
        conditions = local_conditions.build_local_conditions("A_none", 3)
        pari_calls = []
        magma_calls = []

        def pari_process(row, tool, timeout, effort):
            pari_calls.append((timeout, effort))
            if len(pari_calls) == 1:
                return rank_result(
                    "pari", row, tool, "UNKNOWN", 0, 3, timeout, effort
                )
            return rank_result(
                "pari", row, tool, "CERT_LT", 1, 1, timeout, effort
            )

        def magma_process(row, tool, timeout, effort):
            magma_calls.append((timeout, effort))
            return rank_result(
                "magma", row, tool, "CERT_LT", 1, 1, timeout, effort
            )

        result = runner.run_control(
            tiny_source(),
            3,
            "optimized",
            conditions,
            pari_tool(),
            magma_tool(),
            optimizer=RecordingOptimizer(),
            pari_process=pari_process,
            magma_process=magma_process,
        )
        self.assertEqual(result["status"], "CONTROL_ONLY_NO_NATURAL_ROW")
        self.assertFalse(result["inference_eligible"])
        self.assertEqual(pari_calls, [(60.0, 0), (300.0, 1)])
        self.assertEqual(magma_calls, [(300.0, 1)])
        self.assertEqual(result["rank"]["classification"], "CERT_LT")
        self.assertEqual(len(result["rank"]["calls"]), 3)
        for call in result["rank"]["calls"]:
            execution = call["result"]["execution"]
            self.assertIn("script", execution)
            self.assertIn("stdout", execution)
            self.assertIn("stderr", execution)
        self.assertEqual(
            result["lift"]["attempts"]["source"]["scalar_sampling"], 6
        )
        self.assertTrue(result["implementation_gaps"])

    def test_apparent_pari_event_without_magma_confirmation_is_unknown(self):
        row = {"row_id": "rank-control", "r": 3, "ainvs": [0, 0, 0, 0, 1]}

        def pari_process(row, tool, timeout, effort):
            return rank_result(
                "pari", row, tool, "CERT_LT", 0, 2, timeout, effort
            )

        def magma_process(row, tool, timeout, effort):
            return rank_result(
                "magma", row, tool, "UNKNOWN", None, None, timeout, effort
            )

        result = runner.rank_cascade(
            row,
            pari_tool(),
            magma_tool(),
            pari_process=pari_process,
            magma_process=magma_process,
        )
        self.assertEqual(result["classification"], "UNKNOWN")
        self.assertEqual(result["reason"], "required_magma_resolution_missing")
        self.assertEqual(result["work"]["magma_calls"], 2)
        self.assertEqual(result["work"]["timeouts"], 2)

    def test_adapter_label_bounds_mismatch_forces_unknown(self):
        row = {"row_id": "mismatch-control", "r": 3, "ainvs": [0, 0, 0, 0, 1]}

        def pari_process(row, tool, timeout, effort):
            return rank_result(
                "pari", row, tool, "CERT_GE", 0, 1, timeout, effort
            )

        def magma_process(row, tool, timeout, effort):
            return rank_result(
                "magma", row, tool, "UNKNOWN", 0, 3, timeout, effort
            )

        result = runner.rank_cascade(
            row,
            pari_tool(),
            magma_tool(),
            pari_process=pari_process,
            magma_process=magma_process,
        )
        self.assertEqual(result["classification"], "UNKNOWN")
        self.assertEqual(result["work"]["pari_calls"], 2)
        self.assertEqual(result["work"]["magma_calls"], 2)
        self.assertEqual(
            result["calls"][0]["validation_reason"],
            "adapter_classification_mismatch",
        )

    def test_adapter_row_binding_spoof_forces_unknown(self):
        row = {"row_id": "binding-control", "r": 3, "ainvs": [0, 0, 0, 0, 1]}
        result = rank_result(
            "pari", row, pari_tool(), "CERT_GE", 3, 3, 60.0, 0
        )
        result["input_sha256"] = "0" * 64
        classification, interval, reason = runner._validated_tool_class(
            result,
            3,
            tool_name="pari",
            row=row,
            tool=pari_tool(),
            effort=0,
            timeout=60.0,
        )
        self.assertEqual(classification, "UNKNOWN")
        self.assertIsNone(interval)
        self.assertIn("input_sha256", reason)


if __name__ == "__main__":
    unittest.main()
