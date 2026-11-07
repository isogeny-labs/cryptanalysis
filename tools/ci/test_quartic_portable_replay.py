import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import quartic_successor as successor

from quartic_portable_replay import copy_verified, new_output
from quartic_successor import prepare, STUDY


class PortableReplayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.source = self.base / "source"
        study = self.source / STUDY
        study.mkdir(parents=True)
        files = {"protocol.json": '{"timeout_seconds": 240}',
                 "basis_protocol.json": '{"timeout_seconds": 120}',
                 "run_sage.py": "# unchanged original field producer\n",
                 "basis_audit_sage.py": "# unchanged original basis producer\n",
                 "attempt.json": "original field attempt",
                 "result.json": "original field result",
                 "polynomial_result.json": "original partial result",
                 "basis_attempt.json": "original basis attempt",
                 "basis_result.json": "original basis result"}
        self.expected = {}
        for name, text in files.items():
            path = study / name
            path.write_text(text)
            self.expected[str(path.relative_to(self.source))] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.manifest = {"inputs": self.expected}

    def assert_originals(self):
        for path, digest in self.expected.items():
            self.assertEqual(hashlib.sha256((self.source / path).read_bytes()).hexdigest(), digest)

    def test_copy_preserves_exact_bytes_and_refuses_reuse(self):
        target = self.base / "copy"
        copy_verified(self.source, target, self.expected)
        for path, digest in self.expected.items():
            self.assertEqual(hashlib.sha256((target / path).read_bytes()).hexdigest(), digest)
        with self.assertRaises(FileExistsError):
            copy_verified(self.source, target, self.expected)

    def test_corrupt_or_missing_inputs_fail_before_copy(self):
        path = self.source / next(iter(self.expected))
        for corrupt in (True, False):
            if corrupt:
                path.write_text("corrupt")
            else:
                path.unlink()
            with self.assertRaises(ValueError):
                copy_verified(self.source, self.base / "copy", self.expected)
            self.assertFalse((self.base / "copy").exists())

    def test_parent_and_symlink_escapes_fail(self):
        for expected in ({"../escape": "0" * 64}, {"/escape": "0" * 64}):
            with self.assertRaises(ValueError):
                copy_verified(self.source, self.base / "copy", expected)
        (self.source / "escape").symlink_to(self.base)
        with self.assertRaises(ValueError):
            copy_verified(self.source, self.base / "copy", {"escape/anything": "0" * 64})

    def test_outputs_cannot_reuse_or_enter_frozen_tree(self):
        with self.assertRaises(ValueError):
            new_output(self.source / STUDY / "rerun", self.source)
        output = new_output(self.base / "new", self.source)
        with self.assertRaises(FileExistsError):
            new_output(output, self.source)

    def test_field_successor_has_no_stale_receipt_or_result(self):
        output, script, protocol, timeout = prepare(self.source, self.base / "field", self.manifest, "field")
        self.assertEqual(timeout, 240)
        self.assertTrue(script.is_file())
        self.assertTrue(protocol.is_file())
        for name in ("attempt.json", "polynomial_result.json", "result.json"):
            self.assertFalse((script.parent / name).exists())
            self.assertTrue((output / "originals" / STUDY / name).is_file())
        self.assert_originals()

    def test_basis_keeps_its_pinned_field_input_but_no_old_basis_result(self):
        output, script, _, timeout = prepare(self.source, self.base / "basis", self.manifest, "basis")
        self.assertEqual(timeout, 120)
        self.assertEqual((script.parent / "result.json").read_text(), "original field result")
        for name in ("basis_attempt.json", "basis_result.json"):
            self.assertFalse((script.parent / name).exists())
            self.assertTrue((output / "originals" / STUDY / name).is_file())
        self.assert_originals()

    def test_successor_cannot_write_inside_original_checkout(self):
        with self.assertRaises(ValueError):
            prepare(self.source, self.source / "new", self.manifest, "field")
        self.assert_originals()

    def synthetic_launcher(self, producer, runtime_code=0, timeout=240):
        """A Python I/O test double; this never runs or certifies Sage."""
        study = self.source / STUDY
        (study / "run_sage.py").write_text(producer)
        (study / "protocol.json").write_text(json.dumps({"timeout_seconds": timeout}))
        for name in ("run_sage.py", "protocol.json"):
            path = study / name
            self.expected[str(path.relative_to(self.source))] = hashlib.sha256(path.read_bytes()).hexdigest()
        launcher = self.source / "sage"
        launcher.write_text(
            "#!/usr/bin/env python3\nimport os,sys\n"
            f"if sys.argv[1]=='--runtime-info':\n print('synthetic I/O control, not Sage'); sys.exit({runtime_code})\n"
            "os.execv(sys.executable,[sys.executable,*sys.argv[2:]])\n")
        launcher.chmod(0o755)
        manifest = self.source / "manifest.json"
        manifest.write_text(json.dumps(self.manifest))
        return patch.multiple(successor, REPOSITORY=self.source, MANIFEST=manifest)

    def test_synthetic_runtime_refusal_is_recorded_without_a_producer(self):
        with self.synthetic_launcher("raise RuntimeError('must not execute')\n", runtime_code=5):
            with self.assertRaisesRegex(ValueError, "runtime verification failed"):
                successor.main(["field", "--out", str(self.base / "refused")])
        receipt = json.loads((self.base / "refused/attempt.json").read_text())
        self.assertEqual(receipt["status"], "CHECKED_RUNTIME_REFUSED")
        self.assertEqual(receipt["returncode"], 5)
        self.assert_originals()

    def test_synthetic_failed_producer_cannot_inherit_a_successful_result(self):
        with self.synthetic_launcher("raise SystemExit(7)\n"):
            code = successor.main(["field", "--out", str(self.base / "failed")])
        self.assertEqual(code, 7)
        receipt = json.loads((self.base / "failed/attempt.json").read_text())
        self.assertEqual(receipt["status"], "SAGE_ERROR")
        self.assertEqual(receipt["outputs"], {})
        self.assertFalse((self.base / "failed/worktree" / STUDY / "result.json").exists())
        self.assert_originals()

    def test_synthetic_timeout_records_no_stale_result(self):
        with self.synthetic_launcher("import time\ntime.sleep(2)\n", timeout=0.1):
            code = successor.main(["field", "--out", str(self.base / "timeout")])
        self.assertEqual(code, 124)
        receipt = json.loads((self.base / "timeout/attempt.json").read_text())
        self.assertEqual(receipt["status"], "TIME_LIMIT")
        self.assertEqual(receipt["outputs"], {})
        self.assertEqual(receipt["timeout_seconds"], 0.1)
        self.assert_originals()


if __name__ == "__main__":
    unittest.main()
