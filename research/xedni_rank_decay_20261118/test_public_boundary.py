#!/usr/bin/env python3
"""Adversarial controls for the Xedni public/private boundary."""

from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import public_boundary as boundary
import lift_builder
import source_generator


PARI_IMAGE_ID = "sha256:923e7e41d2fe1716fc3f1a6e06486d469b608baa6d6b4b0fdbb6e43b132049cf"


class FixedCardinalityBackend:
    name = "test-fixed-cardinality"
    last_evidence = None

    def cardinality_and_factors(self, prime, a, b):
        if (prime, a, b) != (101, 72, 90):
            raise AssertionError((prime, a, b))
        return 92, [(2, 2), (23, 1)]


def private_source():
    return source_generator.generate_source(
        101,
        "generic",
        0,
        6,
        "integration-control-not-natural",
        FixedCardinalityBackend(),
    )


def public_candidate(public_source, public_lift, *, cpu_ns=1):
    return {
        "schema": boundary.PUBLIC_CANDIDATE_SCHEMA,
        "public_source_sha256": boundary._sha(public_source),
        "public_lift_sha256": public_lift["public_lift_sha256"],
        "ainvs": public_lift["ainvs"],
        "selected_points": public_lift["selected_points"],
        "construction_work": {
            "attempts": 1,
            "rejections": 0,
            "public_group_operations": 0,
            "cpu_ns": cpu_ns,
            "retained_bytes": 128,
        },
    }


def nonce(label: str) -> bytes:
    return hashlib.sha256(("test-nonce:" + label).encode()).digest()


def lift_fixture(label: str, *, production_link=False):
    private = private_source()
    if production_link:
        public, link = boundary.redact_private_source(private)
    else:
        public, link = boundary.redact_private_source(
            private, link_nonce=nonce(label), allow_test_nonce=True
        )
    private_lift = lift_builder.build_lift(private, 3, "balanced")
    public_lift = boundary.derive_public_lift(
        private_lift,
        private_source=private,
        public_source=public,
        link=link,
    )
    candidate = public_candidate(public, public_lift)
    return private, public, link, private_lift, public_lift, candidate


class RedactionTests(unittest.TestCase):
    def setUp(self):
        self.private = private_source()
        self.public, self.link = boundary.redact_private_source(
            self.private, link_nonce=bytes(range(32)), allow_test_nonce=True
        )

    def test_module_does_not_claim_unintegrated_production_readiness(self):
        self.assertFalse(boundary.PRODUCTION_READY)
        self.assertIn("not integrated", boundary.PRODUCTION_BLOCKER)

    def test_exact_redaction_replays(self):
        replay = boundary.verify_redaction_link(self.private, self.public, self.link)
        self.assertEqual(replay["link_id"], self.public["link_id"])
        rendered = json.dumps(self.public, sort_keys=True)
        for forbidden in (
            "master_seed",
            "ordered_scalars",
            "scalar_sampling_attempts",
            "source_index",
            "cardinality_evidence",
        ):
            self.assertNotIn(forbidden, rendered)

    def test_extra_innocuous_feature_is_rejected(self):
        tampered = copy.deepcopy(self.public)
        tampered["proxy_curvature"] = 314159
        with self.assertRaisesRegex(boundary.BoundaryError, "extra=.*proxy_curvature"):
            boundary.validate_public_source(tampered)

    def test_recursive_scalar_smuggling_is_rejected(self):
        private_lift = lift_builder.build_lift(self.private, 3, "balanced")
        public_lift = boundary.derive_public_lift(
            private_lift,
            private_source=self.private,
            public_source=self.public,
            link=self.link,
        )
        candidate = public_candidate(self.public, public_lift)
        candidate["construction_work"]["proxy_curvature"] = {
            "harmless": self.private["ordered_scalars"][0]
        }
        with self.assertRaises(boundary.BoundaryError):
            boundary.validate_public_candidate(
                candidate, public_source=self.public, public_lift=public_lift
            )

    def test_recursive_forbidden_name_is_rejected(self):
        with self.assertRaisesRegex(boundary.BoundaryError, "forbidden public key"):
            boundary.assert_no_forbidden_public_material(
                {"outer": [{"known_scalar": 17}]}
            )

    def test_public_hash_tamper_is_rejected(self):
        tampered = copy.deepcopy(self.public)
        tampered["ordered_points"][0][0] += 1
        with self.assertRaisesRegex(boundary.BoundaryError, "off curve|payload_sha256"):
            boundary.validate_public_source(tampered)

    def test_prefix_order_and_target_must_match_frozen_permutation(self):
        tampered = copy.deepcopy(self.private)
        tampered["prefixes"]["2"]["indices"] = list(
            reversed(tampered["prefixes"]["2"]["indices"])
        )
        tampered["prefixes"]["2"]["target_index"] = tampered["prefixes"]["2"]["indices"][-1]
        with self.assertRaisesRegex(boundary.BoundaryError, "prefix permutation"):
            boundary.validate_private_source(tampered)

    def test_generator_scalar_target_link_is_replayed(self):
        tampered = copy.deepcopy(self.private)
        target = tampered["prefixes"]["3"]["target_index"]
        tampered["ordered_scalars"][target] = (
            tampered["ordered_scalars"][target] % (tampered["source_subgroup_order"] - 1)
        ) + 1
        if tampered["ordered_scalars"][target] == self.private["ordered_scalars"][target]:
            tampered["ordered_scalars"][target] = 1
        with self.assertRaisesRegex(boundary.BoundaryError, "scalar replay"):
            boundary.validate_private_source(tampered)

    def test_link_nonce_tamper_is_rejected(self):
        tampered = copy.deepcopy(self.link)
        tampered["link_nonce_hex"] = nonce("tampered").hex()
        with self.assertRaisesRegex(boundary.BoundaryError, "does not replay"):
            boundary.verify_redaction_link(self.private, self.public, tampered)

    def test_zero_and_weak_caller_nonces_are_rejected(self):
        for bad in (b"\0" * 32, b"x" * 32):
            with self.subTest(bad=bad[:1]):
                with self.assertRaisesRegex(boundary.BoundaryError, "weak"):
                    boundary.redact_private_source(
                        self.private, link_nonce=bad, allow_test_nonce=True
                    )

    def test_production_nonce_records_os_entropy_provenance(self):
        _, link = boundary.redact_private_source(self.private)
        self.assertEqual(link["nonce_provenance"], "os.urandom")
        self.assertTrue(link["production_eligible"])


class FormulaTests(unittest.TestCase):
    def setUp(self):
        (
            self.private,
            self.public,
            self.link,
            self.private_lift,
            self.public_lift,
            self.candidate,
        ) = lift_fixture("formula")
        self.formula_input = boundary.derive_m3_formula_input(
            self.candidate,
            public_source=self.public,
            public_lift=self.public_lift,
        )
        self.spec = boundary.freeze_m3_formula()

    def test_formula_is_bound_and_replays(self):
        first = boundary.compute_m3_feature(self.formula_input, self.spec)
        second = boundary.compute_m3_feature(copy.deepcopy(self.formula_input), self.spec)
        self.assertEqual(first, second)
        self.assertEqual(
            first["value"],
            boundary._independent_fraction_text(
                boundary._m3_ast_replay(self.formula_input, self.spec["formula_ast"])
            ),
        )

    def test_arbitrary_public_features_are_not_an_input(self):
        tampered = copy.deepcopy(self.candidate)
        tampered["public_features"] = {"proxy_curvature": 271828}
        with self.assertRaisesRegex(boundary.BoundaryError, "public_features"):
            boundary.derive_m3_formula_input(
                tampered, public_source=self.public, public_lift=self.public_lift
            )

    def test_formula_implementation_tamper_is_rejected(self):
        tampered = copy.deepcopy(self.spec)
        tampered["implementation_sha256"] = "0" * 64
        with self.assertRaisesRegex(boundary.BoundaryError, "implementation digest"):
            boundary.compute_m3_feature(self.formula_input, tampered)

    def test_ids_and_work_values_cannot_smuggle_into_formula_input(self):
        baseline_binding = boundary.bind_candidate_outside_selector(
            self.candidate, public_source=self.public, public_lift=self.public_lift
        )
        tampered = copy.deepcopy(self.candidate)
        tampered["construction_work"]["cpu_ns"] = 314159
        formula_input = boundary.derive_m3_formula_input(
            tampered, public_source=self.public, public_lift=self.public_lift
        )
        self.assertNotIn("314159", json.dumps(formula_input, sort_keys=True))
        binding = boundary.bind_candidate_outside_selector(
            tampered, public_source=self.public, public_lift=self.public_lift
        )
        self.assertTrue(binding["candidate_id"].startswith("candidate-"))
        self.assertEqual(binding["candidate_id"], baseline_binding["candidate_id"])
        self.assertEqual(binding["tie_break_key"], baseline_binding["tie_break_key"])
        self.assertNotIn("314159", json.dumps(binding["tie_break_key"]))
        tampered["candidate_id"] = "c314159"
        with self.assertRaisesRegex(boundary.BoundaryError, "candidate_id"):
            boundary.derive_m3_formula_input(
                tampered, public_source=self.public, public_lift=self.public_lift
            )

    def test_monkeypatched_helper_same_digest_fails_ast_replay(self):
        original_fraction = boundary._fraction
        original_digest_function = boundary.m3_implementation_sha256
        frozen_digest = self.spec["implementation_sha256"]
        try:
            boundary._fraction = lambda value, context: boundary.Fraction(0)
            boundary.m3_implementation_sha256 = lambda: frozen_digest
            with self.assertRaisesRegex(boundary.BoundaryError, "independent AST replay"):
                boundary.compute_m3_feature(self.formula_input, self.spec)
        finally:
            boundary._fraction = original_fraction
            boundary.m3_implementation_sha256 = original_digest_function

    def test_monkeypatched_formatter_same_digest_fails_independent_replay(self):
        original_formatter = boundary._fraction_text
        original_digest_function = boundary.m3_implementation_sha256
        frozen_digest = self.spec["implementation_sha256"]
        try:
            boundary._fraction_text = lambda value: "0"
            boundary.m3_implementation_sha256 = lambda: frozen_digest
            with self.assertRaisesRegex(boundary.BoundaryError, "independent AST replay"):
                boundary.compute_m3_feature(self.formula_input, self.spec)
        finally:
            boundary._fraction_text = original_formatter
            boundary.m3_implementation_sha256 = original_digest_function

    def test_host_control_feature_is_rejected_for_production(self):
        feature = boundary.compute_m3_feature(self.formula_input, self.spec)
        with self.assertRaisesRegex(boundary.BoundaryError, "not production eligible"):
            boundary.validate_m3_feature(
                feature, spec=self.spec, formula_input=self.formula_input
            )
        boundary.validate_m3_feature(
            feature,
            spec=self.spec,
            formula_input=self.formula_input,
            production=False,
        )

    def test_public_lift_point_curve_and_reduction_are_replayed(self):
        tampered = copy.deepcopy(self.public_lift)
        value = boundary._fraction(tampered["selected_points"][0][0], "test")
        tampered["selected_points"][0][0] = boundary._fraction_text(value + 1)
        payload = {
            key: tampered[key]
            for key in boundary.PUBLIC_LIFT_KEYS - {"public_lift_sha256"}
        }
        tampered["public_lift_sha256"] = boundary._sha(payload)
        with self.assertRaisesRegex(boundary.BoundaryError, "off lifted curve|reduction mismatch"):
            boundary.validate_public_lift(tampered, public_source=self.public)

    def test_candidate_must_match_bound_lift(self):
        tampered = copy.deepcopy(self.candidate)
        tampered["public_lift_sha256"] = "f" * 64
        with self.assertRaisesRegex(boundary.BoundaryError, "lift hash mismatch"):
            boundary.validate_public_candidate(
                tampered,
                public_source=self.public,
                public_lift=self.public_lift,
            )


class StageTests(unittest.TestCase):
    def test_rank_and_replay_cannot_precede_selection(self):
        ledger = boundary.StageLedger("row-0001")
        ledger.advance("private_validated", {"artifact": 1})
        ledger.advance("public_redacted", {"artifact": 2})
        with self.assertRaisesRegex(boundary.BoundaryError, "public_selected"):
            ledger.advance("private_replayed", {"artifact": 3})
        with self.assertRaisesRegex(boundary.BoundaryError, "public_selected"):
            ledger.advance("public_ranked", {"artifact": 3})

    def test_arbitrary_hash_string_is_not_a_stage_artifact(self):
        ledger = boundary.StageLedger("row-0001")
        with self.assertRaisesRegex(boundary.BoundaryError, "actual JSON object"):
            ledger.advance("private_validated", "4" * 64)

    def test_private_replay_requires_matching_public_proposal(self):
        private = private_source()
        public, link = boundary.redact_private_source(private)
        selection = {"schema": "selection-test/v1", "choice": 1}
        proposal = {"schema": "proposal-test/v1", "coefficients": [1, -1]}
        ledger = boundary.StageLedger("row-0001")
        ledger.advance("private_validated", private)
        ledger.advance("public_redacted", public)
        ledger.advance("public_selected", selection)
        ledger.advance("public_relation_proposed", proposal)
        result = boundary.verify_private_replay_link(
            private,
            public,
            link,
            ledger.snapshot(),
            selection_artifact=selection,
            proposal_artifact=proposal,
        )
        self.assertEqual(result["proposal_sha256"], boundary._sha(proposal))
        with self.assertRaisesRegex(boundary.BoundaryError, "do not match"):
            boundary.verify_private_replay_link(
                private,
                public,
                link,
                ledger.snapshot(),
                selection_artifact=selection,
                proposal_artifact={"schema": "proposal-test/v1", "coefficients": [9]},
            )

    def test_private_replay_rejects_nonproduction_link(self):
        private, public, link, _, _, _ = lift_fixture("nonproduction")
        selection = {"schema": "selection-test/v1", "choice": 1}
        proposal = {"schema": "proposal-test/v1", "coefficients": [1]}
        ledger = boundary.StageLedger("row-0002")
        for stage, artifact in zip(
            boundary.STAGES[:4], (private, public, selection, proposal)
        ):
            ledger.advance(stage, artifact)
        with self.assertRaisesRegex(boundary.BoundaryError, "production link"):
            boundary.verify_private_replay_link(
                private,
                public,
                link,
                ledger.snapshot(),
                selection_artifact=selection,
                proposal_artifact=proposal,
            )


class ContainerIsolationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docker = shutil.which("docker")
        cls.image_present = False
        if cls.docker:
            probe = subprocess.run(
                [cls.docker, "image", "inspect", PARI_IMAGE_ID],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
                close_fds=True,
            )
            cls.image_present = probe.returncode == 0

    def test_command_rejects_host_paths(self):
        private = private_source()
        public, _ = boundary.redact_private_source(
            private, link_nonce=nonce("host-path"), allow_test_nonce=True
        )
        with self.assertRaisesRegex(boundary.BoundaryError, "host path"):
            boundary.run_public_container(
                public,
                image=PARI_IMAGE_ID,
                tool_command=["python3", "/workspace/steal.py", "<PUBLIC_INPUT>"],
                expected_output_schema=boundary.ISOLATION_CANARY_SCHEMA,
            )

    def test_image_declared_volumes_are_rejected(self):
        with self.assertRaisesRegex(boundary.BoundaryError, "Config.Volumes"):
            boundary._validate_image_inspect(
                [{"Id": PARI_IMAGE_ID, "Config": {"Volumes": {"/data": {}}}}],
                PARI_IMAGE_ID,
            )

    def test_direct_search_complete_zero_or_unbound_work_is_rejected(self):
        if not self.image_present:
            self.skipTest("pinned PARI image is unavailable")
        source = self._public_source("direct-cost")
        bundle = boundary.run_direct_source_search_adapter(
            source, image=PARI_IMAGE_ID, timeout_seconds=30
        )
        valid = bundle["cost"]
        spec = bundle["adapter_spec"]
        zero = copy.deepcopy(valid)
        zero["counters"]["group_operations"] = 0
        zero["transcript"]["group_operations"] = 0
        zero["transcript_sha256"] = boundary._sha(zero["transcript"])
        zero["cost_sha256"] = boundary._sha(
            {key: zero[key] for key in boundary.DIRECT_SEARCH_COST_KEYS - {"cost_sha256"}}
        )
        with self.assertRaisesRegex(boundary.BoundaryError, "positive"):
            boundary.validate_direct_search_cost(
                zero,
                expected_public_source=source,
                expected_adapter_spec=spec,
            )
        other_source = self._public_source("direct-cost-other")
        with self.assertRaisesRegex(boundary.BoundaryError, "source binding"):
            boundary.validate_direct_search_cost(
                valid,
                expected_public_source=other_source,
                expected_adapter_spec=spec,
            )
        tampered = copy.deepcopy(valid)
        tampered["transcript"]["candidates_tested"] += 1
        with self.assertRaisesRegex(boundary.BoundaryError, "counter mismatch"):
            boundary.validate_direct_search_cost(
                tampered,
                expected_public_source=source,
                expected_adapter_spec=spec,
            )
        inconsistent = copy.deepcopy(valid)
        inconsistent["transcript"]["status"] = "no_relation"
        with self.assertRaisesRegex(boundary.BoundaryError, "coefficients require relation"):
            boundary.validate_direct_search_cost(
                inconsistent,
                expected_public_source=source,
                expected_adapter_spec=spec,
            )

    def test_container_cannot_see_env_fd_network_or_known_host_path(self):
        if not self.image_present:
            self.skipTest("pinned PARI image is unavailable")
        private = private_source()
        public, _ = boundary.redact_private_source(
            private, link_nonce=nonce("container"), allow_test_nonce=True
        )
        script = (
            "import json,os,socket,sys;"
            "json.load(open(sys.argv[1]));"
            "a=os.getenv('XEDNI_BOUNDARY_CANARY');"
            "b=os.path.exists('/workspace/cryptanalysis/.git/config');"
            "c=any('fd-canary-' in os.readlink('/proc/self/fd/'+x) "
            "for x in os.listdir('/proc/self/fd') if os.path.islink('/proc/self/fd/'+x));"
            "d=socket.socket().connect_ex(('1.1.1.1',53))==0;"
            "print(json.dumps({'schema':'xedni-public-isolation-canary/v1','a':a,'b':b,'c':c,'d':d},sort_keys=True))"
        )
        old = os.environ.get("XEDNI_BOUNDARY_CANARY")
        os.environ["XEDNI_BOUNDARY_CANARY"] = "must-not-cross"
        try:
            with tempfile.NamedTemporaryFile(mode="w+", prefix="fd-canary-") as canary:
                canary.write("fd-canary")
                canary.flush()
                evidence = boundary.run_public_container(
                    public,
                    image=PARI_IMAGE_ID,
                    tool_command=["python3", "-c", script, "<PUBLIC_INPUT>"],
                    expected_output_schema=boundary.ISOLATION_CANARY_SCHEMA,
                    timeout_seconds=30,
                )
        finally:
            if old is None:
                os.environ.pop("XEDNI_BOUNDARY_CANARY", None)
            else:
                os.environ["XEDNI_BOUNDARY_CANARY"] = old
        self.assertEqual(evidence["status"], "complete", evidence["stderr"])
        self.assertEqual(
            evidence["output"],
            {
                "schema": boundary.ISOLATION_CANARY_SCHEMA,
                "a": None,
                "b": False,
                "c": False,
                "d": False,
            },
        )
        self.assertEqual(evidence["sandbox"]["host_mounts"], ["public_input_read_only"])
        self.assertEqual(evidence["sandbox"]["extra_volumes"], [])
        self.assertEqual(evidence["sandbox"]["user"], "65534:65534")

    def _public_source(self, label):
        private = private_source()
        return boundary.redact_private_source(
            private, link_nonce=nonce(label), allow_test_nonce=True
        )[0]

    def test_duplicate_json_keys_are_rejected(self):
        if not self.image_present:
            self.skipTest("pinned PARI image is unavailable")
        duplicate = (
            "import sys;print('{\"schema\":\"xedni-public-isolation-canary/v1\","
            "\"schema\":\"xedni-public-isolation-canary/v1\","
            "\"a\":null,\"b\":false,\"c\":false,\"d\":false}')"
        )
        with self.assertRaisesRegex(boundary.BoundaryError, "duplicate JSON key"):
            boundary.run_public_container(
                self._public_source("duplicate"),
                image=PARI_IMAGE_ID,
                tool_command=["python3", "-c", duplicate, "<PUBLIC_INPUT>"],
                expected_output_schema=boundary.ISOLATION_CANARY_SCHEMA,
            )

    def test_nonfinite_json_is_rejected(self):
        with self.assertRaisesRegex(boundary.BoundaryError, "non-finite"):
            boundary._strict_json_loads('{"schema":"x","value":NaN}')

    def test_output_schema_extra_key_is_rejected(self):
        if not self.image_present:
            self.skipTest("pinned PARI image is unavailable")
        extra = (
            "import json;print(json.dumps({'schema':'xedni-public-isolation-canary/v1',"
            "'a':None,'b':False,'c':False,'d':False,'extra':1}))"
        )
        with self.assertRaisesRegex(boundary.BoundaryError, "extra=.*extra"):
            boundary.run_public_container(
                self._public_source("extra"),
                image=PARI_IMAGE_ID,
                tool_command=["python3", "-c", extra, "<PUBLIC_INPUT>"],
                expected_output_schema=boundary.ISOLATION_CANARY_SCHEMA,
            )

    def test_output_flood_is_killed_and_capped(self):
        if not self.image_present:
            self.skipTest("pinned PARI image is unavailable")
        flood = "print('x'*100000)"
        evidence = boundary.run_public_container(
            self._public_source("flood"),
            image=PARI_IMAGE_ID,
            tool_command=["python3", "-c", flood, "<PUBLIC_INPUT>"],
            expected_output_schema=boundary.ISOLATION_CANARY_SCHEMA,
            stdout_limit_bytes=1024,
        )
        self.assertEqual(evidence["status"], "output_limit")
        self.assertEqual(evidence["output_overflow_stream"], "stdout")
        self.assertLessEqual(len(evidence["stdout"].encode()), 1024)

    def test_m3_launcher_binds_script_formula_executable_and_direct_cost(self):
        if not self.image_present:
            self.skipTest("pinned PARI image is unavailable")
        _, public, _, _, public_lift, candidate = lift_fixture("m3")
        formula_input = boundary.derive_m3_formula_input(
            candidate, public_source=public, public_lift=public_lift
        )
        spec = boundary.freeze_m3_formula()
        direct_bundle = boundary.run_direct_source_search_adapter(
            public, image=PARI_IMAGE_ID, timeout_seconds=30
        )
        mutated = copy.deepcopy(direct_bundle)
        q = public["source_subgroup_order"]
        mutated["cost"]["transcript"]["result_coefficients"][0] = (
            mutated["cost"]["transcript"]["result_coefficients"][0] + 1
        ) % q
        mutated["cost"]["transcript_sha256"] = boundary._sha(
            mutated["cost"]["transcript"]
        )
        mutated["cost"]["cost_sha256"] = boundary._sha(
            {
                key: mutated["cost"][key]
                for key in boundary.DIRECT_SEARCH_COST_KEYS - {"cost_sha256"}
            }
        )
        mutated["execution"]["output"] = mutated["cost"]
        mutated["execution"]["output_sha256"] = boundary._sha(mutated["cost"])
        mutated["execution"]["evidence_sha256"] = boundary._sha(
            {
                key: mutated["execution"][key]
                for key in mutated["execution"]
                if key != "evidence_sha256"
            }
        )
        mutated["bundle_sha256"] = boundary._sha(
            {
                key: mutated[key]
                for key in boundary.DIRECT_BUNDLE_KEYS - {"bundle_sha256"}
            }
        )
        with self.assertRaisesRegex(boundary.BoundaryError, "stdout/output/cost"):
            boundary.validate_direct_search_bundle(
                mutated, expected_public_source=public
            )

        replay_mutated = copy.deepcopy(mutated)
        replay_mutated["execution"]["stdout"] = (
            boundary._canonical_bytes(replay_mutated["cost"]).decode() + "\n"
        )
        replay_mutated["execution"]["stdout_sha256"] = hashlib.sha256(
            replay_mutated["execution"]["stdout"].encode()
        ).hexdigest()
        replay_mutated["execution"]["evidence_sha256"] = boundary._sha(
            {
                key: replay_mutated["execution"][key]
                for key in replay_mutated["execution"]
                if key != "evidence_sha256"
            }
        )
        replay_mutated["bundle_sha256"] = boundary._sha(
            {
                key: replay_mutated[key]
                for key in boundary.DIRECT_BUNDLE_KEYS - {"bundle_sha256"}
            }
        )
        with self.assertRaisesRegex(boundary.BoundaryError, "DLP replay failed"):
            boundary.validate_direct_search_bundle(
                replay_mutated, expected_public_source=public
            )
        cost = direct_bundle["cost"]
        evidence = boundary.run_m3_formula_container(
            formula_input,
            formula_spec=spec,
            direct_source_search_cost=direct_bundle,
            public_source=public,
            image=PARI_IMAGE_ID,
            timeout_seconds=30,
        )
        self.assertEqual(evidence["status"], "complete", evidence["stderr"])
        self.assertEqual(
            evidence["m3_binding"]["script_sha256"],
            hashlib.sha256(boundary.M3_CONTAINER_SCRIPT.encode()).hexdigest(),
        )
        self.assertEqual(
            evidence["m3_binding"]["direct_source_search_cost"], cost
        )
        self.assertEqual(
            evidence["output"]["formula_input_sha256"],
            formula_input["formula_input_sha256"],
        )


if __name__ == "__main__":
    unittest.main()
