#!/usr/bin/env python3
"""Tests for tools/pcc/pcc.py: the canary corpus end to end through the CLI,
plus the producer/verifier round trip (keygen, claim new, verify, verdict,
ledger verify with a base, standing, lint-prose) in a scratch repository.

    python3 tools/pcc/test_pcc.py
"""
from __future__ import annotations

import io
import hashlib
import json
import os
import shlex
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pcc  # noqa: E402

PCC = [sys.executable, str(HERE / "pcc.py")]


def scratch_env(cwd: Path) -> dict[str, str]:
    e = dict(os.environ, PCC_REPO=str(cwd))
    # The gate's own keyring settings do not belong to the scratch repositories.
    e.pop("PCC_KEYRING_REF", None)
    e.pop("PCC_KEYRING_SHA256", None)
    return e


def run(args: list[str], cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    e = scratch_env(cwd)
    if env:
        e.update(env)
    return subprocess.run(PCC + args, cwd=cwd, capture_output=True, text=True, env=e)


class Ed25519Tests(unittest.TestCase):
    def test_rfc8032_vector(self):
        # RFC 8032 section 7.1, test 1 (empty message).
        secret = bytes.fromhex("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60")
        self.assertEqual(pcc.ed25519_public(secret).hex(),
                         "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a")
        sig = pcc.ed25519_sign(secret, b"")
        self.assertEqual(sig.hex(), "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e06522490155"
                                    "5fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b")
        self.assertTrue(pcc.ed25519_verify(pcc.ed25519_public(secret), b"", sig))
        self.assertFalse(pcc.ed25519_verify(pcc.ed25519_public(secret), b"x", sig))

    def test_cross_check_with_cryptography_when_available(self):
        try:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        except ImportError:
            self.skipTest("cryptography not installed")
        secret = os.urandom(32)
        msg = b"pcc cross-check"
        theirs = Ed25519PrivateKey.from_private_bytes(secret)
        self.assertEqual(theirs.sign(msg), pcc.ed25519_sign(secret, msg))


class CertificateSubgroupTests(unittest.TestCase):
    def setUp(self):
        self.curve = pcc.Curve(97, 2, 3, 5)
        self.p = (3, 6)
        assert self.curve.mul(5, self.p) is None

    def certificate(self, q, proof):
        return {"schema": pcc.ZK_SOLVE_CERT_SCHEMA,
                "curve": {"p": 97, "a": 2, "b": 3, "n": 5},
                "P": list(self.p), "Q": list(q), "proof": proof}

    def test_rejects_target_outside_declared_subgroup_even_when_challenge_is_zero(self):
        q = (0, 87)
        r = (80, 10)
        self.assertIsNotNone(self.curve.mul(5, q))
        self.assertEqual(pcc.schnorr_challenge(self.curve, self.p, q, r), 0)
        cert = self.certificate(q, {"R": list(r), "s": 2})
        reasons = []
        self.assertFalse(pcc.verify_zk_solve_certificate(cert, reasons))
        self.assertIn("certificate: [n]Q is not the point at infinity", reasons)

    def test_rejects_proof_point_outside_declared_subgroup(self):
        q = self.curve.mul(2, self.p)
        r = (0, 87)
        self.assertIsNotNone(self.curve.mul(5, r))
        cert = self.certificate(q, {"R": list(r), "s": 2})
        reasons = []
        self.assertFalse(pcc.verify_zk_solve_certificate(cert, reasons))
        self.assertIn("zk certificate: [n]R is not the point at infinity", reasons)

    def test_valid_subgroup_proof_still_passes(self):
        q = self.curve.mul(2, self.p)
        cert = self.certificate(q, pcc.schnorr_prove(self.curve, self.p, q, 2, r=1))
        reasons = []
        self.assertTrue(pcc.verify_zk_solve_certificate(cert, reasons), reasons)


class CanaryTests(unittest.TestCase):
    def test_every_sabotage_class_is_rejected(self):
        out = io.StringIO()
        rc = pcc.run_canary(out)
        self.assertEqual(rc, 0, out.getvalue())
        self.assertNotIn("WRONG", out.getvalue())


class RoundTripTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.repo = Path(self.td.name) / "repo"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q", "-b", "main", str(self.repo)], check=True)
        subprocess.run(["git", "-C", str(self.repo), "config", "user.email", "t@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "config", "user.name", "t"], check=True)
        (self.repo / "pcc").mkdir()
        self.key = self.repo / "ci.key"
        r = run(["keygen", "--out", str(self.key), "--key-id", "ci-main"], self.repo)
        self.assertEqual(r.returncode, 0, r.stderr)
        pub = json.loads(r.stdout)
        (self.repo / pcc.KEYRING_PATH).write_text(json.dumps(
            {"schema": pcc.KEYRING_SCHEMA, "keys": [pub], "trusted_verifiers": []}))
        self.assertEqual(run(["ledger", "init"], self.repo).returncode, 0)
        self.commit("genesis")

    def tearDown(self):
        self.td.cleanup()

    def commit(self, msg: str) -> None:
        subprocess.run(["git", "-C", str(self.repo), "add", "-A"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "commit", "-q", "-m", msg], check=True)

    def make_solve(self) -> str:
        curve = pcc.Curve(pcc._SECP_P, 0, 7, pcc._SECP_N)
        k = 123456789
        Q = curve.mul(k, pcc._SECP_G)
        cert = {"schema": pcc.SOLVE_CERT_SCHEMA, "curve": {"p": pcc._SECP_P, "a": 0, "b": 7, "n": pcc._SECP_N},
                "P": list(pcc._SECP_G), "Q": list(Q), "k": k}
        (self.repo / "cert.json").write_text(json.dumps(cert))
        r = run(["claim", "new", "--kind", "solve", "--statement", "k is the discrete log of Q",
                 "--claim-type", "data", "--proof", "certificate:cert.json"], self.repo)
        self.assertEqual(r.returncode, 0, r.stderr)
        return Path(r.stdout.strip()).stem

    def test_claim_verify_verdict_standing(self):
        cid = self.make_solve()
        r = run(["verify", cid, "--json"], self.repo)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(json.loads(r.stdout)["verdict"], "pass")
        # Unsigned: the standing is unverified however the verify went.
        self.assertEqual(run(["standing", cid], self.repo).returncode, 2)
        r = run(["verdict", cid, "--sign-key", str(self.key), "--key-id", "ci-main"], self.repo)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = run(["standing", cid, "--json"], self.repo)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(json.loads(r.stdout)["standing"], "verified")
        # Editing the claim after the verdict drops it back to unverified.
        path = self.repo / pcc.CLAIMS_DIR / f"{cid}.json"
        c = json.loads(path.read_text())
        c["statement"] = "a stronger statement"
        path.write_text(json.dumps(c))
        self.assertEqual(run(["standing", cid], self.repo).returncode, 2)

    def test_verdict_refuses_a_key_outside_the_keyring(self):
        cid = self.make_solve()
        stranger = self.repo / "stranger.key"
        run(["keygen", "--out", str(stranger), "--key-id", "stranger"], self.repo)
        r = run(["verdict", cid, "--sign-key", str(stranger), "--key-id", "ci-main"], self.repo)
        self.assertEqual(r.returncode, 3)
        self.assertIn("not the keyring key", r.stderr)

    def test_attestation_path_shorthand_and_immutable_legacy_record(self):
        artifact = self.repo / "artifact.txt"
        artifact.write_text("producer observation, no independent signature\n")
        made = run(["claim", "new", "--kind", "statement", "--statement", "scoped observation",
                    "--claim-type", "data", "--proof", "attestation:artifact.txt"], self.repo)
        self.assertEqual(made.returncode, 0, made.stderr)
        path = self.repo / made.stdout.strip()
        claim = json.loads(path.read_text())
        self.assertEqual(claim["proofs"][0]["subject"],
                         {"path": "artifact.txt", "sha256": pcc.sha256_file(artifact)})
        checked = run(["verify", claim["id"], "--json"], self.repo)
        self.assertEqual(checked.returncode, 2, checked.stdout + checked.stderr)
        self.assertEqual(json.loads(checked.stdout)["verdict"], "not_covered")
        legacy = json.loads(path.read_text())
        legacy["proofs"][0].update(legacy["proofs"][0].pop("subject"))
        verdict = pcc.verify_claim(legacy, self.repo, pcc.load_keyring(self.repo / pcc.KEYRING_PATH))
        self.assertEqual(verdict["verdict"], "not_covered", verdict)
        self.assertEqual(json.loads(path.read_text()), claim)
        artifact.write_text("edited artifact\n")
        bad = pcc.verify_claim(legacy, self.repo, pcc.load_keyring(self.repo / pcc.KEYRING_PATH))
        self.assertEqual(bad["verdict"], "fail", bad)

    def test_execution_creation_rejects_incomplete_inputs_before_writes(self):
        artifact = self.repo / "artifact.txt"
        artifact.write_text('{"synthetic": true}\n')
        pin = {"path": "artifact.txt", "sha256": pcc.sha256_file(artifact)}
        complete = {"receipt": pin, "verifier": pin, "journal_binds": pin,
                    "image_id": "synthetic-untrusted-image"}
        bad = ["execution:artifact.txt", "execution:{}"]
        for field in complete:
            missing = dict(complete)
            del missing[field]
            bad.append("execution:" + json.dumps(missing))
        bad.append("execution:" + json.dumps(dict(complete, receipt={"path": "artifact.txt", "sha256": "bad"})))
        before = (self.repo / pcc.LEDGER_PATH).read_bytes()
        for spec in bad:
            with self.subTest(spec=spec):
                result = run(["claim", "new", "--kind", "execution", "--statement", "fixture",
                              "--proof", "attestation:artifact.txt", "--proof", spec], self.repo)
                self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
                self.assertIn("execution requires", result.stderr)
                self.assertEqual((self.repo / pcc.LEDGER_PATH).read_bytes(), before)
                self.assertFalse((self.repo / pcc.CLAIMS_DIR).exists())
        made = run(["claim", "new", "--kind", "execution", "--statement", "fixture",
                    "--claim-type", "data", "--proof", "execution:" + json.dumps(complete)], self.repo)
        self.assertEqual(made.returncode, 0, made.stderr)
        checked = run(["verify", Path(made.stdout.strip()).stem, "--json"], self.repo)
        self.assertEqual(checked.returncode, 2, checked.stdout + checked.stderr)
        self.assertEqual(json.loads(checked.stdout)["verdict"], "not_covered")

    def test_ledger_prefix_against_base(self):
        cid = self.make_solve()
        self.commit("claim")
        subprocess.run(["git", "-C", str(self.repo), "checkout", "-q", "-b", "work"], check=True)
        run(["verdict", cid, "--sign-key", str(self.key), "--key-id", "ci-main"], self.repo)
        r = run(["ledger", "verify", "--base", "main"], self.repo)
        self.assertEqual(r.returncode, 0, r.stdout)
        # Rewrite history: drop the claim entry from the middle.
        led = self.repo / pcc.LEDGER_PATH
        lines = led.read_text().splitlines()
        led.write_text("\n".join([lines[0]] + lines[2:]) + "\n")
        r = run(["ledger", "verify", "--base", "main"], self.repo)
        self.assertEqual(r.returncode, 1)
        self.assertIn("seq", r.stdout)
        # Truncate below the base: chain is fine, prefix is not.
        led.write_text(lines[0] + "\n")
        r = run(["ledger", "verify", "--base", "main"], self.repo)
        self.assertEqual(r.returncode, 1)
        self.assertIn("history removed", r.stdout)

    def test_ledger_prefix_decrypts_vaulted_base_and_fails_closed(self):
        filter_script = self.repo / "vault_filter.py"
        filter_script.write_text(
            "import sys\n"
            "data = sys.stdin.buffer.read()\n"
            "if sys.argv[1] == 'clean':\n"
            "    sys.stdout.buffer.write(b'VLT1' + data)\n"
            "elif data.startswith(b'VLT1'):\n"
            "    sys.stdout.buffer.write(data[4:])\n"
            "else:\n"
            "    sys.exit(1)\n"
        )
        command = f"{shlex.quote(sys.executable)} {shlex.quote(str(filter_script))}"
        for direction in ("clean", "smudge"):
            subprocess.run(["git", "-C", str(self.repo), "config", f"filter.vault.{direction}",
                            f"{command} {direction}"], check=True)
        (self.repo / ".gitattributes").write_text("pcc/ledger.jsonl filter=vault\n")
        cid = self.make_solve()
        self.commit("vaulted claim")
        stored = subprocess.check_output(["git", "-C", str(self.repo), "show", "main:pcc/ledger.jsonl"])
        self.assertTrue(stored.startswith(b"VLT1"))
        subprocess.run(["git", "-C", str(self.repo), "checkout", "-q", "-b", "work"], check=True)
        self.assertEqual(run(["verdict", cid, "--sign-key", str(self.key), "--key-id", "ci-main"],
                             self.repo).returncode, 0)
        verified = run(["ledger", "verify", "--base", "main"], self.repo)
        self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)
        subprocess.run(["git", "-C", str(self.repo), "config", "filter.vault.smudge", "false"], check=True)
        rejected = run(["ledger", "verify", "--base", "main"], self.repo)
        self.assertEqual(rejected.returncode, 3)
        self.assertIn("could not decrypt", rejected.stderr)

    def add_own_key(self, cid: str) -> None:
        """What a producer that controls its tree can do: add a key, sign its own verdict."""
        evil = self.repo / "evil.key"
        r = run(["keygen", "--out", str(evil), "--key-id", "evil"], self.repo)
        kr = json.loads((self.repo / pcc.KEYRING_PATH).read_text())
        kr["keys"].append(json.loads(r.stdout))
        (self.repo / pcc.KEYRING_PATH).write_text(json.dumps(kr))
        r = run(["verdict", cid, "--sign-key", str(evil), "--key-id", "evil"], self.repo)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_self_added_key_counts_in_the_tree_but_not_under_the_base_keyring(self):
        cid = self.make_solve()
        self.commit("claim")
        subprocess.run(["git", "-C", str(self.repo), "checkout", "-q", "-b", "work"], check=True)
        self.add_own_key(cid)
        # Read from the working tree, the producer's key is as good as the owner's ...
        self.assertEqual(run(["standing", cid], self.repo).returncode, 0)
        # ... read from the base, it is nobody's.
        r = run(["--keyring-ref", "main", "standing", cid, "--json"], self.repo)
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertEqual(json.loads(r.stdout)["standing"], "unverified")
        r = run(["standing", cid], self.repo, env={"PCC_KEYRING_REF": "main"})
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        # A citation of it does not pass the prose lint either.
        r = subprocess.run(PCC + ["--keyring-ref", "main", "lint-prose", "--stdin"],
                           input=f"This proves the log [pcc:{cid}].\n", cwd=self.repo, capture_output=True,
                           text=True, env=scratch_env(self.repo))
        self.assertEqual(r.returncode, 1, r.stdout)
        # The owner's own key still counts under the base keyring.
        run(["verdict", cid, "--sign-key", str(self.key), "--key-id", "ci-main"], self.repo)
        self.assertEqual(run(["--keyring-ref", "main", "standing", cid], self.repo).returncode, 0)

    def test_keyring_change_fails_ledger_verify_unless_the_owner_pinned_it(self):
        cid = self.make_solve()
        self.commit("claim")
        subprocess.run(["git", "-C", str(self.repo), "checkout", "-q", "-b", "work"], check=True)
        self.assertEqual(run(["ledger", "verify", "--base", "main"], self.repo).returncode, 0)
        self.add_own_key(cid)
        r = run(["ledger", "verify", "--base", "main"], self.repo)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("keyring", r.stdout)
        digest = pcc.sha256_file(self.repo / pcc.KEYRING_PATH)
        r = run(["ledger", "verify", "--base", "main"], self.repo, env={"PCC_KEYRING_SHA256": digest})
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = run(["ledger", "verify", "--base", "main"], self.repo, env={"PCC_KEYRING_SHA256": "0" * 64})
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        self.assertIn("pinned keyring", r.stderr)
        # Reformatting the same keys is a change too: bytes, not meaning.
        subprocess.run(["git", "-C", str(self.repo), "checkout", "-q", "main", "--", pcc.KEYRING_PATH], check=True)
        self.assertEqual(run(["ledger", "verify", "--base", "main"], self.repo).returncode, 0)
        kr = json.loads((self.repo / pcc.KEYRING_PATH).read_text())
        (self.repo / pcc.KEYRING_PATH).write_text(json.dumps(kr, indent=2))
        r = run(["ledger", "verify", "--base", "main"], self.repo)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("keyring", r.stdout)

    def test_a_base_or_keyring_ref_that_does_not_resolve_fails(self):
        cid = self.make_solve()
        r = run(["ledger", "verify", "--base", "origin/no-such-branch"], self.repo)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("does not resolve", r.stdout)
        r = run(["--keyring-ref", "origin/no-such-branch", "standing", cid], self.repo)
        self.assertEqual(r.returncode, 3)
        self.assertIn("does not resolve", r.stderr)
        # A base that resolves but has no ledger is still "nothing to compare".
        subprocess.run(["git", "-C", str(self.repo), "checkout", "-q", "--orphan", "empty"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "rm", "-rqf", "--cached", "."], check=True)
        (self.repo / "note.txt").write_text("x")
        subprocess.run(["git", "-C", str(self.repo), "add", "note.txt"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "commit", "-q", "-m", "no pcc here"], check=True)
        (self.repo / pcc.KEYRING_PATH).unlink()
        r = run(["ledger", "verify", "--base", "empty"], self.repo)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("nothing to compare", r.stdout)

    def test_keygen_and_canary_ignore_the_gate_keyring_settings(self):
        env = {"PCC_KEYRING_SHA256": "0" * 64, "PCC_KEYRING_REF": "origin/no-such-branch"}
        r = run(["keygen", "--out", str(self.repo / "k2.key"), "--key-id", "k2"], self.repo, env=env)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_lint_prose_uses_ledger_standings(self):
        cid = self.make_solve()
        bad = f"This proves the log [pcc:{cid}].\n"
        r = subprocess.run(PCC + ["lint-prose", "--stdin"], input=bad, cwd=self.repo, capture_output=True,
                           text=True, env=scratch_env(self.repo))
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("unverified", r.stdout)
        run(["verdict", cid, "--sign-key", str(self.key), "--key-id", "ci-main"], self.repo)
        r = subprocess.run(PCC + ["lint-prose", "--stdin"], input=bad, cwd=self.repo, capture_output=True,
                           text=True, env=scratch_env(self.repo))
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_bypass_is_a_ledger_entry(self):
        r = run(["ledger", "append-bypass", "--reason", "smoke", "--command", "scripts/run_x.sh"], self.repo)
        self.assertEqual(r.returncode, 0, r.stderr)
        entries = pcc.read_ledger(self.repo / pcc.LEDGER_PATH)
        self.assertEqual(entries[-1]["type"], "bypass")
        self.assertEqual(entries[-1]["body"]["reason"], "smoke")
        self.assertEqual(run(["ledger", "verify"], self.repo).returncode, 0)

    def test_broken_ledger_refuses_appends(self):
        led = self.repo / pcc.LEDGER_PATH
        led.write_text(led.read_text().replace('"type":"genesis"', '"type":"note"'))
        r = run(["ledger", "append-bypass", "--reason", "x", "--command", "y"], self.repo)
        self.assertEqual(r.returncode, 3)
        self.assertIn("broken ledger", r.stderr)


class ClaimIdentityTests(unittest.TestCase):
    def claim(self):
        return {"schema": pcc.CLAIM_SCHEMA, "id": "PCC-20261120-abcdef",
                "kind": "statement", "statement": "identity control", "claim_type": "data",
                "proofs": [], "producer": {"commit": "a" * 40},
                "created_at": "2026-11-20T00:00:00Z"}

    def test_producer_commit_is_an_exact_string(self):
        for value in ("0" * 40, "a" * 40):
            with self.subTest(valid=value):
                c = self.claim()
                c["producer"]["commit"] = value
                reasons = []
                self.assertTrue(pcc.validate_claim(c, reasons), reasons)
        for value in (int("1" * 40), None, True, [], {}, "a" * 39,
                      "a" * 41, "A" * 40, "a" * 40 + "\n"):
            with self.subTest(invalid=value):
                c = self.claim()
                c["producer"]["commit"] = value
                reasons = []
                self.assertFalse(pcc.validate_claim(c, reasons))
                self.assertIn("claim: producer.commit must be a 40-hex commit", reasons)

    def test_claim_id_has_no_trailing_linebreak(self):
        c = self.claim()
        c["id"] += "\n"
        reasons = []
        self.assertFalse(pcc.validate_claim(c, reasons))
        self.assertIn("claim: id must match PCC-YYYYMMDD-xxxxxx", reasons)

    def test_cli_rejects_malformed_identity_before_proofs(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / "pcc").mkdir()
            (repo / pcc.KEYRING_PATH).write_text(json.dumps(
                {"schema": pcc.KEYRING_SCHEMA, "keys": [], "trusted_verifiers": []}))
            for field, value in (("commit", int("1" * 40)), ("commit", "a" * 40 + "\n"),
                                 ("id", "PCC-20261120-abcdef\n")):
                with self.subTest(field=field, value=value):
                    c = self.claim()
                    (c["producer"] if field == "commit" else c)[field] = value
                    path = repo / "claim.json"
                    path.write_text(json.dumps(c))
                    result = run(["verify", str(path), "--json"], repo)
                    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                    verdict = json.loads(result.stdout)
                    self.assertEqual(verdict["verdict"], "fail")
                    self.assertEqual(verdict["proofs"], [])

    def test_cli_preserves_canonical_statement_result(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / "pcc").mkdir()
            (repo / pcc.KEYRING_PATH).write_text(json.dumps(
                {"schema": pcc.KEYRING_SCHEMA, "keys": [], "trusted_verifiers": []}))
            path = repo / "claim.json"
            path.write_text(json.dumps(self.claim()))
            result = run(["verify", str(path), "--json"], repo)
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertEqual(json.loads(result.stdout)["verdict"], "not_covered")


class ClaimTypeTests(unittest.TestCase):
    setUp = RoundTripTests.setUp
    tearDown = RoundTripTests.tearDown
    commit = RoundTripTests.commit
    make_solve = RoundTripTests.make_solve
    """claim_type, ledger verify, standing-by-type, sample-for-validation."""

    def write_claim(self, cid: str, created: str, claim_type: str | None, kind: str = "statement") -> None:
        c = {"schema": pcc.CLAIM_SCHEMA, "id": cid, "kind": kind, "statement": "s", "scope": "", "proofs": [],
             "producer": {"commit": "a" * 40, "session": "", "model": ""}, "created_at": created}
        if claim_type:
            c["claim_type"] = claim_type
        (self.repo / pcc.CLAIMS_DIR).mkdir(parents=True, exist_ok=True)
        (self.repo / pcc.CLAIMS_DIR / f"{cid}.json").write_text(json.dumps(c))

    def test_legacy_claim_without_type_is_data(self):
        self.write_claim("PCC-20261105-aaaaaa", "2026-11-05T00:00:00Z", None)
        r = run(["ledger", "verify"], self.repo)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertEqual(json.loads(run(["standing-by-type", "--json"], self.repo).stdout)["data"],
                         {"unverified": 1})

    def test_new_claim_without_type_fails_ledger_verify(self):
        self.write_claim("PCC-20261112-bbbbbb", "2026-11-12T00:00:00Z", None)
        r = run(["ledger", "verify"], self.repo)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("claim_type is missing", r.stdout)

    def test_backdated_created_at_does_not_exempt(self):
        self.write_claim("PCC-20261112-cccccc", "2026-01-01T00:00:00Z", None)
        self.assertEqual(run(["ledger", "verify"], self.repo).returncode, 1)

    def test_invalid_type_fails_and_valid_new_passes(self):
        self.write_claim("PCC-20261112-dddddd", "2026-11-12T00:00:00Z", "opinion")
        self.assertEqual(run(["ledger", "verify"], self.repo).returncode, 1)
        self.write_claim("PCC-20261112-dddddd", "2026-11-12T00:00:00Z", "literature")
        self.assertEqual(run(["ledger", "verify"], self.repo).returncode, 0)

    def test_validate_claim_rejects_new_untyped(self):
        reasons: list[str] = []
        c = {"schema": pcc.CLAIM_SCHEMA, "id": "PCC-20261112-eeeeee", "kind": "statement", "statement": "s",
             "proofs": [], "producer": {"commit": "a" * 40}, "created_at": "2026-11-12T00:00:00Z"}
        self.assertFalse(pcc.validate_claim(c, reasons))
        self.assertTrue(any("claim_type" in r for r in reasons))
        self.assertTrue(pcc.validate_claim(dict(c, claim_type="interpretive"), []))

    def test_claim_new_records_type(self):
        cid = self.make_solve()
        c = json.loads((self.repo / pcc.CLAIMS_DIR / f"{cid}.json").read_text())
        self.assertEqual(c["claim_type"], "data")

    def reject_missing_type(self, cid):
        path = self.repo / pcc.CLAIMS_DIR / f"{cid}.json"
        manifest = {"schema": pcc.SCHEMA_REJECTIONS_SCHEMA, "records": {
            path.relative_to(self.repo).as_posix(): {
                "sha256": pcc.sha256_file(path), "issue": "missing_claim_type",
                "disposition": "rejected", "reason": "Retained untyped payload is ineligible as evidence."}}}
        (self.repo / pcc.SCHEMA_REJECTIONS_PATH).write_text(json.dumps(manifest))
        return manifest

    def test_historical_rejection_preserves_payload_and_never_admits_claim(self):
        cid = "PCC-20261112-111111"
        self.write_claim(cid, "2026-11-12T00:00:00Z", None)
        path = self.repo / pcc.CLAIMS_DIR / f"{cid}.json"
        original = path.read_bytes()
        self.commit("inherited untyped payload")
        self.reject_missing_type(cid)
        result = run(["ledger", "verify", "--base", "HEAD"], self.repo)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("ineligible as evidence", result.stdout)
        claim = json.loads(original)
        self.assertIsNone(pcc.claim_type_of(claim))
        self.assertFalse(pcc.validate_claim(claim, []))
        self.assertEqual(pcc.standing(claim, [], {})["standing"], "failed")
        self.assertEqual(path.read_bytes(), original)

    def test_rejection_cannot_cover_a_new_claim_or_mutated_payload(self):
        cid = "PCC-20261112-222222"
        self.write_claim(cid, "2026-11-12T00:00:00Z", None)
        self.reject_missing_type(cid)
        result = run(["ledger", "verify", "--base", "HEAD"], self.repo)
        self.assertEqual(result.returncode, 1)
        self.assertIn("already present in the base", result.stdout)
        self.commit("retained rejection")
        path = self.repo / pcc.CLAIMS_DIR / f"{cid}.json"
        path.write_bytes(path.read_bytes() + b" ")
        result = run(["ledger", "verify", "--base", "HEAD"], self.repo)
        self.assertEqual(result.returncode, 1)
        self.assertIn("payload or expected", result.stdout)

    def test_rejection_manifest_cannot_drop_or_rewrite_existing_entries(self):
        cid = "PCC-20261112-333333"
        self.write_claim(cid, "2026-11-12T00:00:00Z", None)
        manifest = self.reject_missing_type(cid)
        self.commit("retained rejection")
        manifest["records"] = {}
        (self.repo / pcc.SCHEMA_REJECTIONS_PATH).write_text(json.dumps(manifest))
        result = run(["ledger", "verify", "--base", "HEAD"], self.repo)
        self.assertEqual(result.returncode, 1)
        self.assertIn("only be appended", result.stdout)

    def test_malformed_kinds_return_failed_verdict_with_real_signed_pass(self):
        cid = "PCC-20261119-666666"
        self.write_claim(cid, "2026-11-19T00:00:00Z", "data")
        path = self.repo / pcc.CLAIMS_DIR / f"{cid}.json"
        original = json.loads(path.read_text())
        keyring = pcc.load_keyring(self.repo / pcc.KEYRING_PATH)
        for field in ("claim", "proof"):
            for value in (None, True, 0, [], {}, "", "unknown"):
                with self.subTest(field=field, value=value):
                    claim = dict(original)
                    if field == "claim":
                        claim["kind"] = value
                    else:
                        claim["proofs"] = [{"kind": value}]
                    path.write_text(json.dumps(claim))
                    verdict = {"type": "verdict", "body": {"claim_id": cid,
                        "claim_sha256": pcc.claim_digest(claim), "verdict": "pass",
                        "commit": "a" * 40}}
                    verdict["sig"] = pcc.make_signature(
                        pcc.read_secret(self.key), "ci-main", "verdict",
                        pcc.verdict_subject(verdict["body"]),
                    )
                    standing = pcc.standing(claim, [verdict], keyring)
                    self.assertTrue(standing["verdicts"][0]["signed"])
                    self.assertEqual(standing["standing"], "failed")
                    self.assertTrue(standing["schema_rejected"])
                    checked = run(["verify", cid, "--json"], self.repo)
                    self.assertEqual(checked.returncode, 1, checked.stdout + checked.stderr)
                    self.assertNotIn("Traceback", checked.stderr)
                    result = json.loads(checked.stdout)
                    self.assertEqual(result["verdict"], "fail")
                    self.assertTrue(result["reasons"])

    def test_current_signed_pass_cannot_promote_schema_invalid_payload(self):
        cid = "PCC-20261112-444444"
        self.write_claim(cid, "2026-11-12T00:00:00Z", None)
        claim = json.loads((self.repo / pcc.CLAIMS_DIR / f"{cid}.json").read_text())
        verdict = {"type": "verdict", "body": {"claim_id": cid,
            "claim_sha256": pcc.claim_digest(claim), "verdict": "pass", "commit": "a" * 40}}
        # The key and keyring belong only to this disposable test repository.
        verdict["sig"] = pcc.make_signature(pcc.read_secret(self.key), "ci-main", "verdict",
                                            pcc.verdict_subject(verdict["body"]))
        result = pcc.standing(claim, [verdict], pcc.load_keyring(self.repo / pcc.KEYRING_PATH))
        self.assertTrue(result["verdicts"][0]["signed"])
        self.assertEqual(result["standing"], "failed")
        self.assertTrue(result["schema_rejected"])

    def populate(self):
        for i in range(30):
            self.write_claim(f"PCC-20261112-{i:06x}", "2026-11-12T00:00:00Z",
                             ("data", "literature", "interpretive")[i % 3])

    def test_standing_by_type_counts(self):
        self.populate()
        r = run(["standing-by-type"], self.repo)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("data: 10 claim(s): unverified=10", r.stdout)
        self.assertIn("interpretive: 10 claim(s): unverified=10", r.stdout)

    def test_sample_is_seeded_stratified_and_oversamples_interpretive(self):
        self.populate()
        out = self.repo / "sample.json"
        args = ["sample-for-validation", "--rate-data", "1", "--rate-interpretive", "3", "--seed", "7",
                "--base", "0.2", "--out", str(out)]
        self.assertEqual(run(args, self.repo).returncode, 0)
        first = out.read_text()
        run(args, self.repo)
        self.assertEqual(out.read_text(), first)  # deterministic given the seed
        s = json.loads(first)
        self.assertAlmostEqual(s["strata"]["interpretive"]["probability"], 0.6)
        self.assertAlmostEqual(s["strata"]["data"]["probability"], 0.2)
        for t in pcc.CLAIM_TYPES:
            self.assertGreaterEqual(s["strata"][t]["sampled"], 1)
        self.assertEqual(len(s["claims"]), sum(v["sampled"] for v in s["strata"].values()))
        # Across seeds the interpretive stratum is drawn more often than data.
        tot = {"data": 0, "interpretive": 0}
        for seed in range(40):
            st = pcc.sample_for_validation(self.repo, pcc.load_keyring(self.repo / pcc.KEYRING_PATH),
                                           1, 3, seed, base=0.2)["strata"]
            for t in tot:
                tot[t] += st[t]["sampled"]
        self.assertGreater(tot["interpretive"], 2 * tot["data"])

    def test_sample_refuses_under_3x(self):
        self.populate()
        r = run(["sample-for-validation", "--rate-data", "1", "--rate-interpretive", "2", "--seed", "1",
                 "--out", str(self.repo / "x.json")], self.repo)
        self.assertEqual(r.returncode, 3)
        self.assertIn("3x", r.stderr)


class LeanScanTests(unittest.TestCase):
    def test_qualified_declarations_do_not_bind_another_namespace(self):
        with tempfile.TemporaryDirectory() as td:
            a, b = Path(td) / "A.lean", Path(td) / "B.lean"
            a.write_text("namespace First\ntheorem same (n : Nat) : n = n := rfl\nend First\n")
            b.write_text("namespace Second\nsection Local\ntheorem same (n : Nat) : n + 0 = n := by simp\nend Local\nend Second\n")
            self.assertEqual(pcc.lean_find_declaration([a, b], "Second.same")[0], b)
            self.assertEqual(pcc.lean_find_declaration([a, b], "First.same")[0], a)
            self.assertIsNone(pcc.lean_find_declaration([a, b], "Missing.same"))
            self.assertIsNone(pcc.lean_find_declaration([a, b], "_root_.same"))
            self.assertIsNone(pcc.lean_find_declaration([a, b], "same"))

    def test_nested_namespaces_sections_and_root_qualified_names(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "Names.lean"
            p.write_text("namespace Outer\npublic section\nnamespace Inner\n"
                         "theorem one : True := by trivial\nend Inner\nend\n"
                         "theorem two : True := by trivial\n"
                         "theorem _root_.Elsewhere.three : True := by trivial\nend Outer\n"
                         "theorem Explicit.four : True := by trivial\n")
            for name in ["Outer.Inner.one", "Outer.two", "Elsewhere.three", "Explicit.four"]:
                self.assertIsNotNone(pcc.lean_find_declaration([p], name), name)
            for name in ["Outer.one", "Outer.Inner.two", "Outer.Elsewhere.three", "Wrong.four"]:
                self.assertIsNone(pcc.lean_find_declaration([p], name), name)

    def test_unsupported_scope_layout_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "Inline.lean"
            p.write_text("namespace Hidden theorem rootLooking : True := by trivial\nend Hidden\n")
            self.assertIsNone(pcc.lean_find_declaration([p], "_root_.rootLooking"))

    def test_comment_and_string_lookalikes_are_not_holes(self):
        src = "theorem t : 1 = 1 := rfl\n-- sorry here is a comment\n/- block sorry -/\ndef s := \"sorry\"\n"
        text = pcc.strip_lean_comments_and_strings(src)
        self.assertIsNone(pcc.LEAN_HOLE_RES["sorry"].search(text))
        self.assertIsNotNone(pcc.LEAN_HOLE_RES["sorry"].search(pcc.strip_lean_comments_and_strings(
            "theorem t : 1 = 1 := by sorry\n")))

    def test_declaration_binding_ignores_whitespace_but_not_content(self):
        a = pcc.lean_find_declaration.__wrapped__ if hasattr(pcc.lean_find_declaration, "__wrapped__") else None
        self.assertIsNone(a)
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "A.lean"
            p.write_text("theorem foo (n : Nat) :\n    n + 0 = n := by simp\n")
            _, s1 = pcc.lean_find_declaration([p], "foo")
            p.write_text("theorem foo (n : Nat) : n + 0 = n := by simp\n")
            _, s2 = pcc.lean_find_declaration([p], "foo")
            self.assertEqual(s1, s2)
            p.write_text("theorem foo (n : Nat) : n + 1 = n := by simp\n")
            _, s3 = pcc.lean_find_declaration([p], "foo")
            self.assertNotEqual(s1, s3)


class RegistrationDateTests(unittest.TestCase):
    setUp = RoundTripTests.setUp
    tearDown = RoundTripTests.tearDown
    commit = RoundTripTests.commit

    def fixture(self, *, typed=False, historical_registration=False):
        ledger = self.repo / pcc.LEDGER_PATH
        ledger.unlink()
        with mock.patch.object(pcc, 'utcnow', return_value='2026-11-01T00:00:00Z'):
            pcc.append_entry(ledger, 'genesis', {'repo': 'registration-date-control'})
        curve = pcc.Curve(pcc._SECP_P, 0, 7, pcc._SECP_N)
        cert = {'schema': pcc.SOLVE_CERT_SCHEMA,
                'curve': {'p': curve.p, 'a': 0, 'b': 7, 'n': curve.n},
                'P': list(pcc._SECP_G), 'Q': list(curve.mul(17, pcc._SECP_G)), 'k': 17}
        raw = json.dumps(cert).encode()
        (self.repo / 'boundary-cert.json').write_bytes(raw)
        cid = 'PCC-20261105-c0ffee'
        claim = {'schema': pcc.CLAIM_SCHEMA, 'id': cid, 'kind': 'solve',
                 'statement': 'Disposable certificate boundary control',
                 'scope': 'Software test fixture',
                 'proofs': [{'kind': 'certificate', 'path': 'boundary-cert.json',
                             'sha256': hashlib.sha256(raw).hexdigest()}],
                 'producer': {'commit': pcc.head_commit(self.repo), 'session': 'fixture', 'model': 'none'},
                 'created_at': '2026-11-05T00:00:00Z'}
        if typed:
            claim['claim_type'] = 'data'
        path = self.repo / pcc.CLAIMS_DIR / (cid + '.json')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(claim))
        body = {'claim_id': cid, 'claim_sha256': pcc.claim_digest(claim),
                'path': path.relative_to(self.repo).as_posix()}
        if historical_registration:
            with mock.patch.object(pcc, 'utcnow', return_value='2026-11-05T00:00:00Z'):
                pcc.append_entry(ledger, 'claim', body)
        else:
            pcc.append_entry(ledger, 'claim', body)
        self.commit('disposable registration-date control')
        return cid

    def rejected(self, args):
        result = run(args, self.repo)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        verdict = json.loads(result.stdout)
        self.assertEqual(verdict['verdict'], 'fail')
        self.assertTrue(any('claim_type' in reason for reason in verdict['reasons']), verdict)
        self.assertEqual(verdict['proofs'], [])
        return verdict

    def test_verify_rejects_new_registration_with_backdated_untyped_payload(self):
        cid = self.fixture()
        self.rejected(['verify', cid, '--json'])

    def test_verify_all_uses_the_registration_cutoff(self):
        self.fixture()
        result = run(['verify-all', '--json'], self.repo)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        verdict = json.loads(result.stdout)
        self.assertEqual(verdict['verdict'], 'fail')
        self.assertEqual(verdict['proofs'], [])

    def test_signed_verdict_records_failure_at_the_registration_cutoff(self):
        cid = self.fixture()
        self.rejected(['verdict', cid, '--sign-key', str(self.key), '--key-id', 'ci-main', '--json'])
        result = run(['standing', cid, '--json'], self.repo)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        standing = json.loads(result.stdout)
        self.assertEqual(standing['standing'], 'failed')
        self.assertTrue(standing['verdicts'][-1]['signed'])
        self.assertEqual(standing['verdicts'][-1]['verdict'], 'fail')

    def test_original_legacy_registration_still_passes(self):
        cid = self.fixture(historical_registration=True)
        result = run(['verify', cid, '--json'], self.repo)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)['verdict'], 'pass')

    def test_explicitly_typed_new_registration_still_passes(self):
        cid = self.fixture(typed=True)
        result = run(['verify', cid, '--json'], self.repo)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)['verdict'], 'pass')



if __name__ == "__main__":
    unittest.main(verbosity=1)
