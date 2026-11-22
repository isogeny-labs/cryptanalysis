#!/usr/bin/env python3
"""Mock-controlled integration tests for the natural executor skeleton.

No natural source, rank tool, relation search, or checkpoint transport runs in
this test module.
"""

from __future__ import annotations

import copy
from dataclasses import replace
import json
from pathlib import Path
import sys
import tempfile
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parent))
import natural_executor as executor
import public_boundary
import runner
import test_public_boundary as boundary_controls
import test_runner as runner_controls


FULL_COMMIT = "e8a6ee3addf237aac101e1eb2b56e230ea34ffcd"
ROW_TOKEN_NONCE = bytes(range(32))


def frozen_roster() -> dict:
    return runner.build_roster("calibration")


def config(roster: dict, authorized: bool = True) -> executor.ExecutorConfig:
    return executor.ExecutorConfig(
        run_id="mock-natural-executor-control-v1",
        stage="calibration",
        natural_rows_authorized=authorized,
        freeze_sha256="a" * 64,
        roster_sha256=roster["roster_sha256"],
        implementation_commit=FULL_COMMIT,
        command=("python3", "runner.py", "run-natural", "--stage", "calibration"),
        tool_pins={
            "pari": {
                "version": "2.17.2",
                "image_digest": "sha256:" + "b" * 64,
                "wrapper_sha256": "c" * 64,
            },
            "magma": {
                "version": "2.29-10",
                "executable_sha256": "d" * 64,
                "license_fingerprint_sha256": "e" * 64,
            },
        },
        row_token_nonce_sha256=executor.hashlib.sha256(ROW_TOKEN_NONCE).hexdigest(),
        verifier_identity_sha256="9" * 64,
        production=False,
    )


def stage(value, *, status="PASS", work=None, execution=None) -> dict:
    result = {
        "status": status,
        "adapter_status": "PASS",
        "value": value,
        "work": {"calls": 1, "cpu_ns": 1} if work is None else work,
    }
    if execution is not None:
        result["execution"] = execution
    return result


class MockPipeline:
    def __init__(self, *, exact_recovery=False, rank_class="CERT_GE", rank_timeout=False):
        self.calls = []
        self.exact_recovery = exact_recovery
        self.rank_class = rank_class
        self.rank_timeout = rank_timeout
        self.fail_gate = None
        self.fail_stage = None
        self.provenance_pass = True
        self.boolean_only_recovery = False
        self.nan_stage = None
        self.work_shape_conflict = False
        self.inject_public_secret = False

    def gate(self, name, **kwargs):
        self.calls.append(f"gate:{name}")
        passed = self.fail_gate != name
        return {
            "schema": executor.GATE_RESULT_SCHEMA,
            "name": name,
            "status": "PASS" if passed else "FAIL",
            "binding_sha256": executor.object_sha256(kwargs["binding"]),
            "checks": {"mock_gate_passed": passed},
            "evidence": (
                {
                    "formula_spec": public_boundary.freeze_m3_formula(),
                    "module_sha256": executor.file_sha256(Path(public_boundary.__file__)),
                    "production_ready": False,
                }
                if name == "public_boundary" and passed
                else {"adapter": "mock"}
            ),
        }

    def verifier(self, name, **kwargs):
        self.calls.append(f"verify:{name}:{kwargs['mode']}")
        return {
            "schema": executor.VALIDATOR_RESULT_SCHEMA,
            "name": name,
            "status": "PASS",
            "subject_sha256": kwargs["subject_sha256"],
            "current_input_sha256": kwargs["subject_sha256"],
            "verifier_identity_sha256": "9" * 64,
            "signature_backend": "UNVERIFIED_CONTROL",
            "signature": executor.object_sha256(
                {"name": name, "subject": kwargs["subject_sha256"]}
            ),
            "checks": {"strict_schema_replayed": True},
            "evidence": {"adapter": "mock-independent-verifier"},
        }

    def preflight_verifier(self, **kwargs):
        return self.verifier("preflight", **kwargs)

    def artifact_verifier(self, **kwargs):
        return self.verifier("artifact", **kwargs)

    def checkpoint_gate(self, **kwargs):
        return self.gate("checkpoint", **kwargs)

    def tool_gate(self, **kwargs):
        return self.gate("tools", **kwargs)

    def public_boundary_gate(self, **kwargs):
        return self.gate("public_boundary", **kwargs)

    def provenance_gate(self, **kwargs):
        return self.gate("provenance", **kwargs)

    def _enter(self, name):
        self.calls.append(name)
        if self.fail_stage == name:
            raise RuntimeError(f"mock failure in {name}")

    def source(self, **kwargs):
        self._enter("source")
        return stage(
            boundary_controls.private_source(),
            work=(
                {"calls": float("nan"), "cpu_ns": 1}
                if self.nan_stage == "source"
                else ({"shape": {"calls": 1}} if self.work_shape_conflict else None)
            ),
        )

    def redact(self, **kwargs):
        self._enter("redact")
        private_source = kwargs["private_source"]
        public_source, link = public_boundary.redact_private_source(
            private_source,
            link_nonce=bytes(range(32)),
            allow_test_nonce=True,
        )
        if self.inject_public_secret:
            public_source["source_scalar_hint"] = private_source["ordered_scalars"][0]
        return stage(
            {
                "public_source": public_source,
                "private_link": link,
            },
            work={"shape": 1} if self.work_shape_conflict else None,
        )

    def local(self, **kwargs):
        self._enter("local")
        self.assert_no_private_kwargs(kwargs)
        return stage({"arm": kwargs["row"]["local_arm"], "certificate": "mock"})

    def lift(self, **kwargs):
        self._enter("lift")
        self.assert_no_private_kwargs(kwargs)
        return stage(
            {
                "row_id": kwargs["context"]["row_token"],
                "ainvs": [0, 0, 0, 1, 2],
                "points": [[1, 2], [3, 4]],
            }
        )

    def invariants(self, **kwargs):
        self._enter("invariants")
        self.assert_no_private_kwargs(kwargs)
        return stage({"minimal_discriminant": "-496", "height_status": "numerical"})

    def relation(self, **kwargs):
        self._enter("relation")
        self.assert_no_private_kwargs(kwargs)
        candidates = []
        if self.exact_recovery:
            vector = [1, -1]
            candidate_id = executor.object_sha256(
                {
                    "vector": vector,
                    "public_input_sha256": kwargs["relation_input_sha256"],
                }
            )
            candidate = {
                "candidate_id": candidate_id,
                "vector": vector,
                "public_input_sha256": kwargs["relation_input_sha256"],
            }
            candidate["proposal_sha256"] = executor.object_sha256(candidate)
            candidates.append(candidate)
        return stage(
            {
                "schema": executor.RELATION_VALUE_SCHEMA,
                "public_input_sha256": kwargs["relation_input_sha256"],
                "finder_outcome": (
                    "EXACT_Q_RELATION_PROPOSED"
                    if candidates
                    else "NO_EXACT_Q_RELATION_WITHIN_FROZEN_BUDGET"
                ),
                "bounded_search_only": True,
                "candidates": candidates,
                "candidate_set_sha256": executor.object_sha256(candidates),
            },
            status="PASS",
        )

    def rank(self, **kwargs):
        self._enter("rank")
        self.assert_no_private_kwargs(kwargs)
        classification = "UNKNOWN" if self.rank_timeout else self.rank_class
        rank_row = {
            "row_id": kwargs["lift"]["row_id"],
            "r": kwargs["row"]["r"],
            "ainvs": kwargs["lift"]["ainvs"],
        }
        pari = runner_controls.rank_result(
            "pari", rank_row, runner_controls.pari_tool(), classification,
            None if self.rank_timeout else (0 if classification == "CERT_LT" else rank_row["r"]),
            None if self.rank_timeout else (rank_row["r"] - 1 if classification == "CERT_LT" else rank_row["r"]),
            60, 0,
        )
        magma = runner_controls.rank_result(
            "magma", rank_row, runner_controls.magma_tool(), classification,
            None if self.rank_timeout else (0 if classification == "CERT_LT" else rank_row["r"]),
            None if self.rank_timeout else (rank_row["r"] - 1 if classification == "CERT_LT" else rank_row["r"]),
            300, 1,
        )
        return stage(
            {
                "schema": executor.RANK_VALUE_SCHEMA,
                "status": "PASS",
                "row": rank_row,
                "pari": pari,
                "magma": magma,
                "classification": classification,
            },
            status="PASS",
        )

    def evaluate(self, **kwargs):
        self._enter("evaluate")
        if "private_source" not in kwargs:
            raise AssertionError("private evaluator did not receive private source")
        if self.boolean_only_recovery:
            return stage(
                {
                    "certificate_status": "EXACT_REPLAY_CERTIFIED",
                    "source_replay_ok": True,
                    "relation_nontrivial": True,
                    "target_coefficient_invertible": True,
                    "useful_recovery": True,
                }
            )
        if self.exact_recovery:
            candidate = kwargs["relation"]["candidates"][0]
            rational_replay = {"status": "EXACT_IDENTITY", "steps": ["mock-Q"]}
            source_replay = {"status": "EXACT_IDENTITY", "steps": ["mock-Fp"]}
            certificate = {
                "candidate_id": candidate["candidate_id"],
                "relation_vector": candidate["vector"],
                "source_subgroup_order": 17,
                "target_index": 1,
                "target_coefficient": -1,
                "rational_replay": rational_replay,
                "rational_replay_sha256": executor.object_sha256(rational_replay),
                "source_replay": source_replay,
                "source_replay_sha256": executor.object_sha256(source_replay),
            }
            value = {
                "schema": executor.EVALUATOR_VALUE_SCHEMA,
                "status": "EXACT_REPLAY_CERTIFIED",
                "public_input_sha256": kwargs["relation_input_sha256"],
                "private_link_sha256": executor.object_sha256(kwargs["private_link"]),
                "candidate_id": candidate["candidate_id"],
                "proposal_sha256": candidate["proposal_sha256"],
                "certificate": certificate,
                "certificate_sha256": executor.object_sha256(certificate),
            }
        else:
            value = {
                "schema": executor.EVALUATOR_VALUE_SCHEMA,
                "status": "NO_CERTIFIED_CANDIDATE",
                "public_input_sha256": kwargs["relation_input_sha256"],
                "private_link_sha256": executor.object_sha256(kwargs["private_link"]),
                "candidate_id": None,
                "proposal_sha256": None,
                "certificate": None,
                "certificate_sha256": None,
            }
        return stage(value)

    def provenance(self, **kwargs):
        self._enter("provenance")
        artifact = kwargs["artifact"]
        return stage(
            {
                "schema": executor.PROVENANCE_VALUE_SCHEMA,
                "status": "PASS" if self.provenance_pass else "FAIL",
                "subject_sha256": kwargs["subject_sha256"],
                "checks": {"row_and_stage_hashes_bound": self.provenance_pass},
            },
            status="PASS",
        )

    @staticmethod
    def assert_no_private_kwargs(kwargs):
        if "private_source" in kwargs or "private_link" in kwargs:
            raise AssertionError("private material reached public stage")
        row = kwargs.get("row", {})
        forbidden_row = {
            "row_id",
            "index",
            "source_index",
            "source_key",
            "source_master_seed",
            "local_seed",
        }
        if forbidden_row.intersection(row):
            raise AssertionError("seed-bearing row metadata reached public stage")
        context = kwargs.get("context", {})
        if "row_id" in context or "row_sha256" in context:
            raise AssertionError("semantic private row context reached public stage")

    def bundle(self) -> executor.ExecutorAdapters:
        return executor.ExecutorAdapters(
            checkpoint_gate=self.checkpoint_gate,
            tool_gate=self.tool_gate,
            public_boundary_gate=self.public_boundary_gate,
            provenance_gate=self.provenance_gate,
            source=self.source,
            redact=self.redact,
            local=self.local,
            lift=self.lift,
            invariants=self.invariants,
            relation=self.relation,
            rank=self.rank,
            evaluate=self.evaluate,
            provenance=self.provenance,
            preflight_verifier=self.preflight_verifier,
            artifact_verifier=self.artifact_verifier,
        )


class NaturalExecutorTests(unittest.TestCase):
    def setUp(self):
        self.roster = frozen_roster()
        self.row = self.roster["executable_roster"][0]
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.output = Path(self.temporary.name)

    def make_executor(self, pipeline, *, authorized=True):
        return executor.NaturalExecutor(
            config(self.roster, authorized=authorized),
            self.roster,
            pipeline.bundle(),
            self.output,
            row_token_nonce=ROW_TOKEN_NONCE,
        )

    def test_full_bounded_no_hit_remains_unknown_and_resumes(self):
        pipeline = MockPipeline(rank_class="CERT_GE")
        engine = self.make_executor(pipeline)
        result = engine.run_row(self.row)
        self.assertEqual(result["status"], "COMPLETE")
        artifact = result["artifact"]
        self.assertEqual(artifact["endpoints"]["curve_rank"], "CERT_GE")
        self.assertEqual(artifact["endpoints"]["selected_dependence"], "UNKNOWN")
        self.assertEqual(artifact["endpoints"]["useful_recovery"], "UNKNOWN")
        self.assertNotIn("CERTIFIED_ABSENT", executor.canonical_json(artifact))
        self.assertEqual(artifact["work"]["calls"], 9)
        self.assertEqual(artifact["work"]["cpu_ns"], 9)
        self.assertNotIn("ordered_scalars", executor.canonical_json(artifact))
        self.assertEqual(
            pipeline.calls,
            [
                "gate:checkpoint",
                "gate:tools",
                "gate:public_boundary",
                "gate:provenance",
                "verify:preflight:create",
                "source",
                "redact",
                "local",
                "lift",
                "invariants",
                "relation",
                "rank",
                "evaluate",
                "provenance",
                "verify:artifact:create",
            ],
        )

        before = list(pipeline.calls)
        resumed = engine.run_row(self.row)
        self.assertEqual(resumed["status"], "RESUMED")
        self.assertEqual(resumed["artifact"]["artifact_sha256"], artifact["artifact_sha256"])
        self.assertEqual(
            pipeline.calls,
            before + ["verify:preflight:resume", "verify:artifact:resume"],
        )

    def test_unreplayed_mock_certificate_cannot_be_useful_success(self):
        pipeline = MockPipeline(exact_recovery=True, rank_class="CERT_GE")
        result = self.make_executor(pipeline).run_row(self.row)
        self.assertEqual(result["status"], "FAILED")
        self.assertEqual(
            result["artifact"]["failure"]["code"], "evaluator_certificate"
        )
        self.assertEqual(result["artifact"]["endpoints"]["useful_recovery"], "UNKNOWN")

    def test_rank_timeout_is_retained_and_unknown(self):
        pipeline = MockPipeline(rank_timeout=True)
        result = self.make_executor(pipeline).run_row(self.row)
        artifact = result["artifact"]
        self.assertEqual(artifact["endpoints"]["curve_rank"], "UNKNOWN")
        execution = artifact["stages"]["rank"]["result"]["value"]["pari"]["execution"]
        self.assertTrue(execution["timed_out"])
        self.assertEqual(execution["timeout_seconds"], 60)
        self.assertEqual(
            execution["script_sha256"],
            executor.hashlib.sha256(execution["script"].encode()).hexdigest(),
        )

    def test_gate_failure_starts_no_row_and_writes_no_row_artifact(self):
        pipeline = MockPipeline()
        pipeline.fail_gate = "checkpoint"
        engine = self.make_executor(pipeline)
        with self.assertRaisesRegex(executor.ExecutorError, "preflight gate"):
            engine.run_row(self.row)
        self.assertTrue((self.output / "preflight.json").exists())
        self.assertFalse((self.output / "rows").exists())
        retained = json.loads((self.output / "preflight.json").read_text())
        self.assertEqual(retained["status"], "FAILED")
        self.assertEqual(
            pipeline.calls,
            ["gate:checkpoint", "verify:preflight:create"],
        )

    def test_stage_exception_is_durable_unknown_failure_and_resumes(self):
        pipeline = MockPipeline()
        pipeline.fail_stage = "relation"
        engine = self.make_executor(pipeline)
        first = engine.run_row(self.row)
        self.assertEqual(first["status"], "FAILED")
        self.assertEqual(first["artifact"]["failure"]["stage"], "relation")
        self.assertEqual(first["artifact"]["failure"]["code"], "adapter_exception")
        self.assertEqual(
            first["artifact"]["endpoints"],
            {
                "curve_rank": "UNKNOWN",
                "selected_dependence": "UNKNOWN",
                "useful_recovery": "UNKNOWN",
            },
        )
        before = list(pipeline.calls)
        second = engine.run_row(self.row)
        self.assertEqual(second["status"], "RESUMED")
        self.assertEqual(second["artifact"]["status"], "FAILED")
        self.assertEqual(
            pipeline.calls,
            before + ["verify:preflight:resume", "verify:artifact:resume"],
        )

    def test_public_forbidden_key_is_retained_as_failed_row(self):
        pipeline = MockPipeline()
        pipeline.inject_public_secret = True
        result = self.make_executor(pipeline).run_row(self.row)
        self.assertEqual(result["status"], "FAILED")
        self.assertEqual(result["artifact"]["failure"]["code"], "private_link")
        self.assertIsNotNone(result["artifact"]["failure"]["rejected_stage_sha256"])
        self.assertNotIn("source_scalar_hint", executor.canonical_json(result["artifact"]))

    def test_existing_artifact_tamper_is_rejected(self):
        pipeline = MockPipeline()
        engine = self.make_executor(pipeline)
        result = engine.run_row(self.row)
        path = Path(result["path"])
        value = json.loads(path.read_text())
        value["endpoints"]["useful_recovery"] = "CERTIFIED_RECOVERY"
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(executor.ExecutorError, "artifact_sha256 mismatch"):
            engine.run_row(self.row)

    def test_row_must_equal_exact_frozen_roster_entry(self):
        pipeline = MockPipeline()
        changed = copy.deepcopy(self.row)
        changed["p"] += 2
        result_engine = self.make_executor(pipeline)
        with self.assertRaisesRegex(executor.ExecutorError, "differs from its frozen"):
            result_engine.run_row(changed)
        self.assertFalse((self.output / "rows").exists())

    def test_authorization_false_fails_before_gate_or_row(self):
        pipeline = MockPipeline()
        with self.assertRaisesRegex(executor.ExecutorError, "authorizing freeze"):
            self.make_executor(pipeline, authorized=False)
        self.assertEqual(pipeline.calls, [])

    def test_roster_self_hash_is_replayed(self):
        pipeline = MockPipeline()
        malformed = copy.deepcopy(self.roster)
        malformed["counts"]["executable"] -= 1
        with self.assertRaisesRegex(executor.ExecutorError, "self-hash"):
            executor.NaturalExecutor(
                config(self.roster),
                malformed,
                pipeline.bundle(),
                self.output,
                row_token_nonce=ROW_TOKEN_NONCE,
            )

    def test_nan_work_is_rejected_and_retained_unknown(self):
        pipeline = MockPipeline()
        pipeline.nan_stage = "source"
        result = self.make_executor(pipeline).run_row(self.row)
        self.assertEqual(result["status"], "FAILED")
        self.assertEqual(result["artifact"]["failure"]["code"], "nonfinite_or_nonjson")
        self.assertNotIn("NaN", executor.canonical_json(result["artifact"]))

    def test_source_scalar_redaction_work_shape_conflict_retains_failure(self):
        pipeline = MockPipeline()
        pipeline.work_shape_conflict = True
        engine = self.make_executor(pipeline)
        result = engine.run_row(self.row)
        self.assertEqual(result["status"], "FAILED")
        self.assertEqual(result["artifact"]["work"]["aggregation_failed"], 1)
        rendered = executor.canonical_json(result["artifact"])
        self.assertNotIn("ordered_scalars", rendered)
        self.assertNotIn("master_seed", rendered)
        self.assertFalse(Path(result["path"] + ".lock").exists())

    def test_duplicate_batch_is_rejected_before_preflight(self):
        pipeline = MockPipeline()
        engine = self.make_executor(pipeline)
        with self.assertRaisesRegex(executor.ExecutorError, "duplicates"):
            engine.run_rows([self.row, self.row])
        self.assertEqual(pipeline.calls, [])

    def test_failed_preflight_is_replayed_without_gate_rerun(self):
        pipeline = MockPipeline()
        pipeline.fail_gate = "checkpoint"
        engine = self.make_executor(pipeline)
        with self.assertRaises(executor.ExecutorError):
            engine.run_row(self.row)
        before = list(pipeline.calls)
        with self.assertRaisesRegex(executor.ExecutorError, "retained preflight"):
            engine.run_row(self.row)
        self.assertEqual(pipeline.calls, before + ["verify:preflight:resume"])

    def test_provenance_must_be_top_level_pass(self):
        pipeline = MockPipeline()
        pipeline.provenance_pass = False
        result = self.make_executor(pipeline).run_row(self.row)
        self.assertEqual(result["status"], "FAILED")
        self.assertEqual(result["artifact"]["failure"]["code"], "provenance_failed")

    def test_boolean_only_recovery_is_rejected(self):
        pipeline = MockPipeline(exact_recovery=True)
        pipeline.boolean_only_recovery = True
        result = self.make_executor(pipeline).run_row(self.row)
        self.assertEqual(result["status"], "FAILED")
        self.assertNotEqual(
            result["artifact"]["endpoints"]["useful_recovery"],
            "CERTIFIED_RECOVERY",
        )

    def test_config_rejects_secrets_and_non_strict_tool_pins(self):
        pipeline = MockPipeline()
        secret = replace(
            config(self.roster),
            command=("runner", "--checkpoint-token=do-not-retain"),
        )
        with self.assertRaisesRegex(executor.ExecutorError, "sensitive string"):
            executor.NaturalExecutor(
                secret,
                self.roster,
                pipeline.bundle(),
                self.output,
                row_token_nonce=ROW_TOKEN_NONCE,
            )
        pins = copy.deepcopy(config(self.roster).tool_pins)
        pins["pari"]["extra"] = "x"
        with self.assertRaisesRegex(executor.ExecutorError, "keys differ"):
            executor.NaturalExecutor(
                replace(config(self.roster), tool_pins=pins),
                self.roster,
                pipeline.bundle(),
                self.output,
                row_token_nonce=ROW_TOKEN_NONCE,
            )

    def test_row_token_is_nonce_bound_not_plain_row_hash(self):
        pipeline = MockPipeline()
        engine = self.make_executor(pipeline)
        token = engine._public_context(self.row)["row_token"]
        self.assertNotEqual(token, executor.object_sha256(self.row))
        other_nonce = b"z" * 32
        other_config = replace(
            config(self.roster),
            row_token_nonce_sha256=executor.hashlib.sha256(other_nonce).hexdigest(),
        )
        other = executor.NaturalExecutor(
            other_config,
            self.roster,
            pipeline.bundle(),
            self.output / "other",
            row_token_nonce=other_nonce,
        )
        self.assertNotEqual(token, other._public_context(self.row)["row_token"])

    def test_active_lock_is_not_reclaimed_and_stale_lock_is_archived(self):
        pipeline = MockPipeline()
        engine = self.make_executor(pipeline)
        engine.preflight()
        path = executor._artifact_path(self.output, self.row["row_id"])
        lock = path.with_suffix(path.suffix + ".lock")
        lock.parent.mkdir(parents=True, exist_ok=True)
        active = executor._lock_record(engine.binding_sha256, executor.object_sha256(self.row))
        lock.write_text(executor.canonical_json(active) + "\n")
        with self.assertRaisesRegex(executor.ExecutorError, "active in PID"):
            engine.run_row(self.row)
        lock.unlink()
        stale = dict(active)
        stale["pid"] = 999999999
        stale["process_start_ticks"] = "0"
        stale = executor._bind_hash(stale, "lock_sha256")
        lock.write_text(executor.canonical_json(stale) + "\n")
        result = engine.run_row(self.row)
        self.assertEqual(result["status"], "COMPLETE")
        self.assertEqual(result["artifact"]["lock_evidence"][0]["reason"], "process_absent")
        self.assertTrue(Path(result["artifact"]["lock_evidence"][0]["archive"]).exists())

    def test_nested_stage_self_rehash_cannot_bypass_verifier(self):
        pipeline = MockPipeline()
        engine = self.make_executor(pipeline)
        result = engine.run_row(self.row)
        path = Path(result["path"])
        value = json.loads(path.read_text())
        rank = value["stages"]["rank"]
        rank["result"]["value"]["classification"] = "CERT_LT"
        rank["result_sha256"] = executor.object_sha256(rank["result"])
        rank = executor._bind_hash(rank, "stage_sha256")
        value["stages"]["rank"] = rank
        value = executor._bind_hash(value, "artifact_sha256")
        path.write_text(executor.canonical_json(value) + "\n")
        with self.assertRaises(executor.ExecutorError):
            engine.run_row(self.row)

    def test_self_rehashed_failed_gate_cannot_be_promoted(self):
        pipeline = MockPipeline()
        engine = self.make_executor(pipeline)
        engine.preflight()
        path = engine.preflight_path
        value = json.loads(path.read_text())
        gate = value["gates"]["checkpoint"]
        gate["result"]["status"] = "FAIL"
        gate["result"]["checks"] = {"mock_gate_passed": False}
        gate["result_sha256"] = executor.object_sha256(gate["result"])
        gate = executor._bind_hash(gate, "receipt_sha256")
        gate["status"] = "PASS"
        gate = executor._bind_hash(gate, "receipt_sha256")
        value["gates"]["checkpoint"] = gate
        value = executor._bind_hash(value, "artifact_sha256")
        path.write_text(executor.canonical_json(value) + "\n")
        with self.assertRaises(executor.ExecutorError):
            engine.preflight()


if __name__ == "__main__":
    unittest.main()

