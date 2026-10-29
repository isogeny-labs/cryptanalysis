import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

from quartic_sage_replay import MODES, checked_command, docker_command, execute, positive_seconds, prepare


class SageReplayIOTests(unittest.TestCase):
    """Transport/refusal controls only: these do not execute or certify Sage."""

    def test_all_four_original_workers_keep_protocol_and_source_bytes(self):
        for mode, (study, worker, generated) in MODES.items():
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temp:
                root = Path(temp) / "source"
                directory = root / study
                directory.mkdir(parents=True)
                files = {worker: "# frozen worker\n", "protocol.json": '{"path":"/Volumes/SSD990/cryptanalysis/input.json"}',
                         "retained_input.json": "original pinned certificate"}
                files.update({name: "old output" for name in generated})
                expected = {}
                for name, text in files.items():
                    path = directory / name
                    path.write_text(text)
                    expected[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
                script = prepare(root, Path(temp) / "copy", {"inputs": expected}, mode)
                self.assertEqual(script.read_text(), files[worker])
                self.assertEqual((script.parent / "protocol.json").read_text(), files["protocol.json"])
                self.assertEqual((script.parent / "retained_input.json").read_text(), files["retained_input.json"])
                for name in generated:
                    self.assertFalse((script.parent / name).exists())
                    self.assertEqual((directory / name).read_text(), "old output")
                for name, digest in expected.items():
                    self.assertEqual(hashlib.sha256((root / name).read_bytes()).hexdigest(), digest)

    def test_checked_launcher_is_mandatory_and_arguments_remain_literal(self):
        script = Path("/Volumes/SSD990/cryptanalysis/study with spaces/worker.py")
        command = checked_command("/opt/checked-sage", script, Path("/source"))
        self.assertEqual(command[1:], ["/source/scripts/sage_release.py", "run", "--sage",
                                      "/opt/checked-sage", "--", "-python", str(script)])
        with self.assertRaises(ValueError):
            checked_command("relative/sage", script)

    def test_image_digest_and_sandbox_are_required(self):
        image = "registry.example/accepted-sage@sha256:" + "a" * 64
        command = docker_command(image, "/opt/sage", "resolvent-check", 120, Path("/new evidence"))
        self.assertIn("--network=none", command)
        self.assertIn("--read-only", command)
        self.assertIn("--entrypoint", command)
        self.assertIn("python3", command)
        self.assertTrue(any(x.endswith("dst=/source,readonly") for x in command))
        for invalid in ("sage:latest", "sage@sha256:abc", "sage@sha256:" + "A" * 64):
            with self.assertRaises(ValueError):
                docker_command(invalid, "/opt/sage", "sqrt2-check", 120, Path("/out"))

    def test_invalid_caps_fail_before_a_worker_can_start(self):
        for value in (0, -1, "nan", "inf", "-inf"):
            with self.assertRaises(ValueError):
                positive_seconds(value)

    def synthetic(self, body, timeout=10):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            work, evidence = root / "work", root / "evidence"
            work.mkdir()
            evidence.mkdir()
            result = execute([sys.executable, "-c", body], work, evidence, ("result.json",), timeout)
            self.assertTrue((evidence / "stdout.txt").is_file())
            self.assertTrue((evidence / "stderr.txt").is_file())
            return result

    def test_failed_worker_does_not_become_success(self):
        result = self.synthetic("raise SystemExit(7)")
        self.assertEqual(result["returncode"], 7)
        self.assertEqual(result["outputs"], {})

    def test_success_requires_fresh_outputs(self):
        result = self.synthetic("pass")
        self.assertEqual(result["status"], "MISSING_OUTPUT")
        self.assertEqual(result["returncode"], 1)

    def test_timeout_is_recorded(self):
        result = self.synthetic("import time; time.sleep(5)", timeout=0.05)
        self.assertEqual(result["status"], "TIME_LIMIT")
        self.assertEqual(result["returncode"], 124)

    def test_synthetic_output_is_exported_and_hashed(self):
        result = self.synthetic("from pathlib import Path; Path('result.json').write_text('{}')")
        self.assertEqual(result["returncode"], 0)
        self.assertEqual(result["outputs"]["result.json"], hashlib.sha256(b"{}").hexdigest())


if __name__ == "__main__":
    unittest.main()
