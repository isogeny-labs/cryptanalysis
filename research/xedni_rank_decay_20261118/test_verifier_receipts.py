#!/usr/bin/env python3

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import unittest
from unittest import mock


HERE = Path(__file__).resolve().parent
REPOSITORY = HERE.parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
if str(REPOSITORY) not in sys.path:
    sys.path.insert(0, str(REPOSITORY))

from tools.pcc import pcc as pcc_tool

import verifier_receipts as vr


class ReceiptTests(unittest.TestCase):
    def setUp(self):
        self.secret = bytes(range(32))
        self.public = pcc_tool.ed25519_public(self.secret).hex()
        self.verifier_sha = "11" * 32
        self.keyring = {
            "schema": "pcc.keyring/v1",
            "keys": [
                {
                    "id": "control-verifier",
                    "algo": "ed25519",
                    "public_key": self.public,
                    "role": "verifier",
                }
            ],
            "trusted_verifiers": [
                {
                    "name": "xedni-row-verifier",
                    "kind": "execution",
                    "sha256": self.verifier_sha,
                }
            ],
        }
        self.keyring_raw = vr.render_keyring(self.keyring)
        self.now = datetime(2026, 11, 19, 12, 0, 0, tzinfo=timezone.utc)
        self.expected = vr.ExpectedBindings(
            run_id="calibration-row-0001",
            purpose="natural-row-verification",
            input_sha256="22" * 32,
            output_sha256="33" * 32,
            details_sha256="44" * 32,
            checkpoint_sha256="55" * 32,
            verifier_name="xedni-row-verifier",
            verifier_kind="execution",
            verifier_sha256=self.verifier_sha,
            keyring_sha256=hashlib.sha256(self.keyring_raw).hexdigest(),
            base_commit="CONTROL",
        )

    def _receipt(
        self,
        *,
        keyring_raw=None,
        secret=None,
        key_id="control-verifier",
        verdict="PASS",
        issued_at="2026-11-19T11:00:00Z",
        expires_at="2026-11-19T13:00:00Z",
        changes=None,
    ):
        raw = self.keyring_raw if keyring_raw is None else keyring_raw
        payload = vr.make_payload(
            run_id=self.expected.run_id,
            purpose=self.expected.purpose,
            input_sha256=self.expected.input_sha256,
            output_sha256=self.expected.output_sha256,
            details_sha256=self.expected.details_sha256,
            checkpoint_sha256=self.expected.checkpoint_sha256,
            verifier_name=self.expected.verifier_name,
            verifier_kind=self.expected.verifier_kind,
            verifier_sha256=self.expected.verifier_sha256,
            keyring_sha256=hashlib.sha256(raw).hexdigest(),
            base_commit=self.expected.base_commit,
            issued_at=issued_at,
            expires_at=expires_at,
            verdict=verdict,
        )
        if changes:
            changes(payload)
            payload["receipt_id"] = vr.expected_receipt_id(payload)
            payload = vr.validate_payload(payload)
        signing_secret = self.secret if secret is None else secret
        signature = pcc_tool.ed25519_sign(
            signing_secret,
            vr.signing_message(payload, key_id),
        ).hex()
        return vr.assemble_receipt(payload, key_id, signature)

    def _verify(self, receipt, *, expected=None, keyring_raw=None, now=None):
        return vr.verify_control_receipt(
            receipt,
            self.expected if expected is None else expected,
            self.keyring_raw if keyring_raw is None else keyring_raw,
            now=self.now if now is None else now,
        )

    def _expected_for_keyring(self, raw):
        return vr.ExpectedBindings(
            **{
                **self.expected.__dict__,
                "keyring_sha256": hashlib.sha256(raw).hexdigest(),
            }
        )

    def test_valid_control_signature_is_never_independent(self):
        result = self._verify(self._receipt())
        self.assertEqual(result["standing"], "NOT_COVERED")
        self.assertTrue(result["signature_valid"])
        self.assertTrue(result["signer_in_keyring"])
        self.assertTrue(result["verifier_trusted"])
        self.assertFalse(result["production_eligible"])
        self.assertEqual(result["trust_anchor"], "SUPPLIED_CONTROL_KEYRING")
        self.assertIn("not an independent", result["notes"][0])

    def test_input_output_details_checkpoint_and_identity_are_bound(self):
        receipt = self._receipt()
        mutations = {
            "run_id": {"run_id": "calibration-row-0002"},
            "purpose": {"purpose": "different-purpose"},
            "input": {"input_sha256": "aa" * 32},
            "output": {"output_sha256": "aa" * 32},
            "details": {"details_sha256": "aa" * 32},
            "checkpoint": {"checkpoint_sha256": "aa" * 32},
            "verifier_name": {"verifier_name": "other-verifier"},
            "verifier_kind": {"verifier_kind": "replay"},
            "verifier_sha": {"verifier_sha256": "aa" * 32},
        }
        for name, changes in mutations.items():
            with self.subTest(name=name):
                expected = vr.ExpectedBindings(**{**self.expected.__dict__, **changes})
                result = self._verify(receipt, expected=expected)
                self.assertEqual(result["standing"], "INVALID")
                self.assertFalse(result["production_eligible"])

    def test_resealed_payload_mutation_still_fails_expected_binding(self):
        receipt = self._receipt(changes=lambda p: p.__setitem__("input_sha256", "aa" * 32))
        result = self._verify(receipt)
        self.assertEqual(result["standing"], "INVALID")
        self.assertIn("payload.input_sha256", result["reasons"][0])

    def test_expired_not_yet_valid_and_excessive_lifetime_fail(self):
        expired = self._receipt(
            issued_at="2026-11-18T10:00:00Z",
            expires_at="2026-11-19T11:59:59Z",
        )
        self.assertEqual(self._verify(expired)["standing"], "INVALID")
        future = self._receipt(
            issued_at="2026-11-19T12:00:01Z",
            expires_at="2026-11-19T13:00:00Z",
        )
        self.assertEqual(self._verify(future)["standing"], "INVALID")
        with self.assertRaises(vr.ReceiptError):
            self._receipt(
                issued_at="2026-11-01T00:00:00Z",
                expires_at="2026-11-19T00:00:00Z",
            )

    def test_validity_boundaries_are_inclusive(self):
        receipt = self._receipt()
        issued = datetime(2026, 11, 19, 11, 0, 0, tzinfo=timezone.utc)
        expires = datetime(2026, 11, 19, 13, 0, 0, tzinfo=timezone.utc)
        self.assertEqual(self._verify(receipt, now=issued)["standing"], "NOT_COVERED")
        self.assertEqual(self._verify(receipt, now=expires)["standing"], "NOT_COVERED")

    def test_domain_and_receipt_id_are_replayed(self):
        receipt = deepcopy(self._receipt())
        receipt["payload"]["domain"] = "other-domain"
        receipt["payload"]["receipt_id"] = vr.expected_receipt_id(receipt["payload"])
        result = self._verify(receipt)
        self.assertEqual(result["standing"], "INVALID")
        self.assertIn("domain", result["reasons"][0])
        receipt = deepcopy(self._receipt())
        receipt["payload"]["receipt_id"] = "aa" * 32
        result = self._verify(receipt)
        self.assertEqual(result["standing"], "INVALID")
        self.assertIn("receipt_id", result["reasons"][0])

    def test_signature_and_receipt_hash_mutations_fail(self):
        receipt = deepcopy(self._receipt())
        receipt["signature"]["signature"] = "00" * 64
        body = {key: receipt[key] for key in ("schema", "payload", "signature")}
        receipt["receipt_sha256"] = vr.object_sha256(body)
        result = self._verify(receipt)
        self.assertEqual(result["standing"], "INVALID")
        self.assertIn("signature", result["reasons"][0])
        receipt = deepcopy(self._receipt())
        receipt["receipt_sha256"] = "aa" * 32
        self.assertEqual(self._verify(receipt)["standing"], "INVALID")

    def test_unknown_and_wrong_signer_fail(self):
        unknown = self._receipt(key_id="unknown")
        result = self._verify(unknown)
        self.assertEqual(result["standing"], "INVALID")
        self.assertIn("signer", result["reasons"][0])
        wrong = self._receipt(secret=bytes(reversed(range(32))))
        result = self._verify(wrong)
        self.assertEqual(result["standing"], "INVALID")
        self.assertIn("signature", result["reasons"][0].lower())

    def test_key_id_relabel_with_same_public_key_fails_signature(self):
        alias_keyring = deepcopy(self.keyring)
        alias_keyring["keys"][0]["id"] = "alias-verifier"
        raw = vr.render_keyring(alias_keyring)
        receipt = self._receipt(keyring_raw=raw)
        receipt["signature"]["key_id"] = "alias-verifier"
        body = {key: receipt[key] for key in ("schema", "payload", "signature")}
        receipt["receipt_sha256"] = vr.object_sha256(body)
        result = self._verify(
            receipt,
            expected=self._expected_for_keyring(raw),
            keyring_raw=raw,
        )
        self.assertEqual(result["standing"], "INVALID")
        self.assertIn("signature", result["reasons"][0].lower())

    def test_untrusted_verifier_is_not_covered(self):
        keyring = deepcopy(self.keyring)
        keyring["trusted_verifiers"] = []
        raw = vr.render_keyring(keyring)
        result = self._verify(
            self._receipt(keyring_raw=raw),
            expected=self._expected_for_keyring(raw),
            keyring_raw=raw,
        )
        self.assertEqual(result["standing"], "NOT_COVERED")
        self.assertTrue(result["signature_valid"])
        self.assertFalse(result["verifier_trusted"])
        self.assertFalse(result["production_eligible"])

    def test_keyring_bytes_are_signed_payload_binding(self):
        receipt = self._receipt()
        changed = deepcopy(self.keyring)
        changed["note"] = "same key, different keyring bytes"
        changed_raw = vr.render_keyring(changed)
        result = self._verify(receipt, keyring_raw=changed_raw)
        self.assertEqual(result["standing"], "INVALID")
        self.assertIn("different keyring", result["reasons"][0])

    def test_signed_failure_never_authorizes(self):
        result = self._verify(self._receipt(verdict="FAIL"))
        self.assertEqual(result["standing"], "NOT_COVERED")
        self.assertFalse(result["production_eligible"])
        self.assertEqual(result["verdict"], "FAIL")

    def test_strict_json_rejects_duplicates_nonfinite_and_extra_keys(self):
        duplicate = '{"schema":"x","schema":"y"}'
        with self.assertRaises(vr.ReceiptError):
            vr.strict_json_loads(duplicate)
        with self.assertRaises(vr.ReceiptError):
            vr.strict_json_loads('{"x":NaN}')
        receipt = deepcopy(self._receipt())
        receipt["extra"] = 1
        self.assertEqual(self._verify(receipt)["standing"], "INVALID")

    def test_keyring_schema_duplicate_and_role_controls(self):
        duplicate = deepcopy(self.keyring)
        duplicate["keys"].append(deepcopy(duplicate["keys"][0]))
        with self.assertRaises(vr.ReceiptError):
            vr.validate_keyring(duplicate)
        duplicate_public = deepcopy(self.keyring)
        alias = deepcopy(duplicate_public["keys"][0])
        alias["id"] = "alias-verifier"
        duplicate_public["keys"].append(alias)
        with self.assertRaises(vr.ReceiptError):
            vr.validate_keyring(duplicate_public)
        role = deepcopy(self.keyring)
        role["keys"][0]["role"] = "producer"
        raw = vr.render_keyring(role)
        receipt = self._receipt(keyring_raw=raw)
        result = self._verify(
            receipt,
            expected=self._expected_for_keyring(raw),
            keyring_raw=raw,
        )
        self.assertEqual(result["standing"], "INVALID")
        self.assertIn("signer", result["reasons"][0])

    def test_small_order_identity_public_key_forgery_is_rejected(self):
        malicious = deepcopy(self.keyring)
        malicious["keys"][0]["public_key"] = "01" + "00" * 31
        malicious_raw = (vr.canonical_json(malicious) + "\n").encode("ascii")
        receipt = self._receipt(keyring_raw=malicious_raw)
        # For the identity public key, R=G and s=1 satisfies the lax Ed25519
        # equation for every message without knowledge of a signing secret.
        receipt["signature"]["signature"] = "58" + "66" * 31 + "01" + "00" * 31
        body = {key: receipt[key] for key in ("schema", "payload", "signature")}
        receipt["receipt_sha256"] = vr.object_sha256(body)
        result = self._verify(
            receipt,
            expected=self._expected_for_keyring(malicious_raw),
            keyring_raw=malicious_raw,
        )
        self.assertEqual(result["standing"], "INVALID")
        self.assertFalse(result["signature_valid"])
        self.assertIn("identity point", result["reasons"][0])

    def test_signature_shape_is_exact(self):
        receipt = deepcopy(self._receipt())
        receipt["signature"]["extra"] = True
        self.assertEqual(self._verify(receipt)["standing"], "INVALID")
        receipt = deepcopy(self._receipt())
        receipt["signature"]["algorithm"] = "rsa"
        self.assertEqual(self._verify(receipt)["standing"], "INVALID")

    def test_assessment_self_hash_replays(self):
        result = self._verify(self._receipt())
        digest = result.pop("assessment_sha256")
        self.assertEqual(digest, vr.object_sha256(result))

    def test_repository_keyring_has_no_trusted_execution_verifier(self):
        summary = vr.repository_trust_summary()
        self.assertEqual(summary["status"], "NOT_COVERED")
        self.assertEqual(summary["trusted_verifier_count"], 0)
        self.assertEqual(summary["active_verifier_keys"], 1)
        self.assertFalse(summary["production_ready"])
        self.assertFalse(vr.PRODUCTION_READY)
        digest = summary.pop("summary_sha256")
        self.assertEqual(digest, vr.object_sha256(summary))

    def test_repository_path_cannot_promote_control_key(self):
        result = vr.verify_repository_receipt(
            self._receipt(),
            self.expected,
        )
        self.assertFalse(result["production_eligible"])
        self.assertIn(result["standing"], {"INVALID", "NOT_COVERED"})

    def test_production_api_has_fixed_time_purpose_and_kind(self):
        with self.assertRaises(TypeError):
            vr.verify_repository_receipt(
                self._receipt(),
                self.expected,
                now=self.now,
            )
        wrong_purpose = vr.ExpectedBindings(
            **{**self.expected.__dict__, "purpose": "arbitrary-purpose"}
        )
        result = vr.verify_repository_receipt(self._receipt(), wrong_purpose)
        self.assertEqual(result["standing"], "INVALID")
        self.assertIn("purpose", result["reasons"][0])
        wrong_kind = vr.ExpectedBindings(
            **{**self.expected.__dict__, "verifier_kind": "documentation"}
        )
        result = vr.verify_repository_receipt(self._receipt(), wrong_kind)
        self.assertEqual(result["standing"], "INVALID")
        self.assertIn("verifier_kind", result["reasons"][0])

    def test_base_commit_and_keyring_digest_are_frozen_expected_bindings(self):
        receipt = self._receipt()
        changed_commit = vr.ExpectedBindings(
            **{**self.expected.__dict__, "base_commit": "a" * 40}
        )
        result = self._verify(receipt, expected=changed_commit)
        self.assertEqual(result["standing"], "INVALID")
        self.assertIn("base_commit", result["reasons"][0])
        changed_keyring = vr.ExpectedBindings(
            **{**self.expected.__dict__, "keyring_sha256": "aa" * 32}
        )
        result = self._verify(receipt, expected=changed_keyring)
        self.assertEqual(result["standing"], "INVALID")
        self.assertTrue(any("keyring_sha256" in reason for reason in result["reasons"]))

    def test_repository_base_commit_must_match_frozen_receipt(self):
        frozen_commit = "b" * 40
        actual_commit = "a" * 40
        expected = vr.ExpectedBindings(
            **{**self.expected.__dict__, "base_commit": frozen_commit}
        )
        receipt = self._receipt(
            changes=lambda payload: payload.__setitem__("base_commit", frozen_commit)
        )
        with mock.patch.object(
            vr,
            "load_origin_main_keyring",
            return_value=(actual_commit, self.keyring_raw),
        ):
            result = vr.verify_repository_receipt(receipt, expected)
        self.assertEqual(result["standing"], "INVALID")
        self.assertIn("different base commit", result["reasons"][0])

    def test_repository_keyring_load_disables_git_replace_objects(self):
        commit = "a" * 40
        calls = [
            mock.Mock(returncode=0, stdout=(commit + "\n").encode("ascii")),
            mock.Mock(returncode=0, stdout=self.keyring_raw),
        ]
        hostile_git_environment = {
            "GIT_DIR": "/attacker/repository",
            "GIT_COMMON_DIR": "/attacker/common",
            "GIT_NAMESPACE": "attacker",
            "GIT_OBJECT_DIRECTORY": "/attacker/objects",
            "GIT_CONFIG_COUNT": "1",
        }
        with mock.patch.dict(os.environ, hostile_git_environment):
            with mock.patch.object(vr.subprocess, "run", side_effect=calls) as run:
                got_commit, got_keyring = vr.load_origin_main_keyring(REPOSITORY)
        self.assertEqual(got_commit, commit)
        self.assertEqual(got_keyring, self.keyring_raw)
        self.assertEqual(run.call_count, 2)
        for call in run.call_args_list:
            self.assertEqual(call.kwargs["env"]["GIT_NO_REPLACE_OBJECTS"], "1")
            for name in hostile_git_environment:
                self.assertNotIn(name, call.kwargs["env"])
        self.assertEqual(
            run.call_args_list[1].args[0],
            ["git", "show", f"{commit}:pcc/keyring.json"],
        )

    def test_repository_git_failure_is_fail_closed(self):
        with mock.patch.object(
            vr.subprocess,
            "run",
            side_effect=vr.subprocess.TimeoutExpired("git", 10),
        ):
            result = vr.verify_repository_receipt(self._receipt(), self.expected)
        self.assertEqual(result["standing"], "NOT_COVERED")
        self.assertFalse(result["production_eligible"])
        self.assertIn("cannot resolve", result["notes"][0])

    def test_naive_now_and_invalid_expected_are_rejected(self):
        result = self._verify(self._receipt(), now=datetime(2026, 11, 19, 12, 0, 0))
        self.assertEqual(result["standing"], "INVALID")
        self.assertIn("timezone-aware", result["reasons"][0])
        with self.assertRaises(vr.ReceiptError):
            vr.ExpectedBindings(**{**self.expected.__dict__, "input_sha256": "ABC"})

    def test_no_signing_secret_or_key_generation_api_is_exported(self):
        self.assertNotIn("sign_receipt", vr.__all__)
        self.assertNotIn("keygen", vr.__all__)
        self.assertFalse(any("secret" in name.lower() for name in vr.__all__))


if __name__ == "__main__":
    unittest.main()
