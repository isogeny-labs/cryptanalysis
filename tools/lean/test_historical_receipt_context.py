#!/usr/bin/env python3
"""Metadata controls for historical receipt replay; no mathematical stand-ins."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock

SPEC = importlib.util.spec_from_file_location("receipt_gate", Path(__file__).with_name("current-corpus-gate.py"))
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class HistoricalReceiptContext(unittest.TestCase):
    PATH = "research/xedni_lift_optimizer_20261101/lean/XedniAffineCoset.lean"
    CHECKER = "research/xedni_lift_optimizer_20261101/lean/check.py"
    RECEIPT = "research/xedni_lift_optimizer_20261101/lean/receipt.json"
    BINDINGS = {
        "suite/src/cryptanalysis/xedni_lift.rs": ("rust_sha256", b"original source metadata fixture\n"),
        "suite/src/cryptanalysis/lattice.rs": ("lattice_sha256", b"original lattice metadata fixture\n"),
        "lean-toolchain": ("toolchain_sha256", b"metadata fixture toolchain\n"),
    }

    def git(self, *args: str) -> str:
        return subprocess.check_output(["git", *args], cwd=self.root,
                                       env={**os.environ, "GIT_NO_LAZY_FETCH": "1"}, text=True).strip()

    def write(self, name: str, data: bytes) -> None:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "Fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        for name, (_, data) in self.BINDINGS.items():
            self.write(name, data)
        self.git("add", "--", *self.BINDINGS)
        self.git("commit", "-qm", "original fixture")
        self.revision = self.git("rev-parse", "HEAD")
        for name in self.BINDINGS:
            self.write(name, b"current source is a different revision\n")
        self.git("add", "--", *self.BINDINGS)
        self.git("commit", "-qm", "current fixture")
        self.write(self.PATH, b"proof metadata fixture\n")
        self.write(self.CHECKER, b"checker metadata fixture\n")
        self.receipt = {
            "schema": "cryptanalysis.xedni-affine-lean-receipt/v1",
            "source_commit": self.revision,
            **{field: sha(data) for field, data in self.BINDINGS.values()},
        }
        self.record = {
            "sha256": sha((self.root / self.PATH).read_bytes()),
            "checker": self.CHECKER,
            "checker_sha256": sha((self.root / self.CHECKER).read_bytes()),
            "receipt": self.RECEIPT,
            "source_commit": self.revision,
        }
        self.save_receipt()
        patch = mock.patch.object(gate, "ROOT", self.root)
        patch.start()
        self.addCleanup(patch.stop)
        patch = mock.patch.dict(os.environ, {"LEAN_CORPUS_EVIDENCE_DIR": str(self.root / "evidence")})
        patch.start()
        self.addCleanup(patch.stop)

    def save_receipt(self):
        data = (json.dumps(self.receipt, indent=2) + "\n").encode()
        self.write(self.RECEIPT, data)
        self.record["receipt_sha256"] = sha(data)

    def context(self):
        return gate.receipt_source_context(self.PATH, self.record)

    def test_replays_original_git_revision_and_preserves_current_files(self):
        before = {name: (self.root / name).read_bytes() for name in self.BINDINGS}
        context, hashes = self.context()
        self.assertNotEqual(context, self.root)
        for name, (_, data) in self.BINDINGS.items():
            self.assertEqual((context / name).read_bytes(), data)
            self.assertEqual((self.root / name).read_bytes(), before[name])
        self.assertEqual(len(hashes), 7)
        self.assertEqual(json.loads((context / "context.json").read_text())["source_commit"], self.revision)
        gate.check_receipt_context(context, hashes)

    def test_unchanged_root_for_a_nonhistorical_checker(self):
        self.assertEqual(gate.receipt_source_context(self.PATH, {}), (self.root, {}))

    def test_blank_or_malformed_revision_is_refused(self):
        for value in ("", "HEAD", None, "-" * 40):
            with self.subTest(value=value):
                self.record["source_commit"] = value
                with self.assertRaisesRegex(ValueError, "invalid receipt source commit"):
                    self.context()

    def test_changed_receipt_is_refused(self):
        self.write(self.RECEIPT, (self.root / self.RECEIPT).read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "frozen receipt changed"):
            self.context()

    def test_receipt_revision_must_match_the_admission_pin(self):
        self.record["source_commit"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "does not match"):
            self.context()

    def test_missing_revision_cannot_fall_back_to_current_source(self):
        self.record["source_commit"] = "0" * 40
        self.receipt["source_commit"] = "0" * 40
        self.save_receipt()
        with self.assertRaisesRegex(ValueError, "historical source unavailable"):
            self.context()

    def test_historical_bytes_must_match_the_frozen_digest(self):
        self.receipt["rust_sha256"] = "0" * 64
        self.save_receipt()
        with self.assertRaisesRegex(ValueError, "historical source hash mismatch"):
            self.context()

    def test_changed_proof_or_checker_is_refused(self):
        for name in (self.PATH, self.CHECKER):
            before = (self.root / name).read_bytes()
            self.write(name, before + b"changed")
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "proof or checker changed"):
                self.context()
            self.write(name, before)

    def test_symlink_or_escaping_receipt_is_refused(self):
        original = self.root / self.RECEIPT
        backup = original.with_suffix(".bak")
        original.rename(backup)
        original.symlink_to(backup)
        with self.assertRaisesRegex(ValueError, "unsafe receipt input"):
            self.context()
        self.record["receipt"] = "../outside.json"
        with self.assertRaisesRegex(ValueError, "unsafe receipt input path"):
            self.context()

    def test_post_run_source_or_context_metadata_mutation_is_refused(self):
        for name in ("suite/src/cryptanalysis/xedni_lift.rs", "context.json"):
            context, hashes = self.context()
            (context / name).write_bytes(b"changed after native check\n")
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "changed during audit"):
                gate.check_receipt_context(context, hashes)


if __name__ == "__main__":
    unittest.main()
