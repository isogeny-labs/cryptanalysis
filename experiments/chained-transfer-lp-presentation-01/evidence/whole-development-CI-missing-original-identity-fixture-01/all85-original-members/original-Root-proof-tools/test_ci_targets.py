"""Regression controls for the Actions proof matrix transport."""

import importlib.util
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "ci_targets", Path(__file__).with_name("ci-targets.py")
)
ci = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ci)


class MatrixTests(unittest.TestCase):
    def test_public_paths_never_enter_job_output(self):
        targets = ["research/public-but-masked/Proof.lean", "project with spaces"]
        output = ci.address(targets)
        self.assertEqual(json.loads(output), [0, 1])
        self.assertFalse(any(path in output for path in targets))

    def test_every_target_is_selected_exactly_once_in_discovery_order(self):
        targets = ["z/Proof.lean", "a/project", "a/Other.lean"]
        self.assertEqual([ci.address(targets, i) for i in json.loads(ci.address(targets))], targets)

    def test_no_targets_produces_empty_matrix(self):
        self.assertEqual(ci.address([]), "[]")

    def test_invalid_indexes_fail_instead_of_selecting_another_target(self):
        for index in (-1, 1, 100):
            with self.subTest(index=index), self.assertRaises(ValueError):
                ci.address(["one.lean"], index)

    def test_duplicate_discovery_fails(self):
        with self.assertRaises(ValueError):
            ci.address(["one.lean", "one.lean"])

    def test_batches_cover_every_target_once_within_actions_limit(self):
        targets = [f"proof/{i}.lean" for i in range(766)]
        starts = json.loads(ci.batches(targets))
        self.assertEqual(len(starts), 192)
        self.assertEqual(
            [target for start in starts for target in ci.batches(targets, start).splitlines()],
            targets,
        )
        self.assertEqual(ci.batches([]), "[]")

    def test_batch_overflow_and_invalid_start_fail_closed(self):
        with self.assertRaises(ValueError):
            ci.batches([str(i) for i in range(1025)])
        for start in (-4, 1, 4):
            with self.subTest(start=start), self.assertRaises(ValueError):
                ci.batches(["one.lean"], start)

    def test_failed_discovery_is_not_an_empty_success(self):
        with patch.object(ci.subprocess, "check_output", side_effect=subprocess.CalledProcessError(3, "discover")):
            with self.assertRaises(subprocess.CalledProcessError):
                ci.discover()


if __name__ == "__main__":
    unittest.main()
