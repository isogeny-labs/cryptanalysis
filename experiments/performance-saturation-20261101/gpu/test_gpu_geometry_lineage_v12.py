#!/usr/bin/env python3
"""Prove v12 extends immutable zero-data v11 evidence instead of rewriting it."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import unittest


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
V11_PROTOCOL = HERE / "protocol-http-rtx5090-geometry-v11.json"
V11_OUTCOME = HERE / "geometry-v11-outcome.json"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class V11ImmutableLineageTests(unittest.TestCase):
    def test_frozen_v11_protocol_and_tooling_blobs_are_immutable(self) -> None:
        protocol_bytes = V11_PROTOCOL.read_bytes()
        self.assertEqual(
            sha256(protocol_bytes),
            "de7fbfc47f4afbd3d51a1dc2d62cbf8bff6c200d701a7c66c4eb46abfe75bdf1",
        )
        protocol = json.loads(protocol_bytes)
        self.assertEqual(protocol["freeze"]["status"], "frozen")
        self.assertEqual(
            protocol["freeze"]["protocol_sha256"],
            "827b0c94c27ea85cd6d97876484cd7562cb8bf84e545c6c6b31ccb2836d87eef",
        )
        tooling = protocol["extensions"]["tooling_source"]
        commit = tooling["commit"]
        self.assertEqual(commit, "2049cec0101cfb0a313b7a6289556c3bb7bc0688")
        for path, expected in tooling["files"].items():
            result = subprocess.run(
                ["git", "show", f"{commit}:{path}"], cwd=REPO,
                capture_output=True, check=False,
            )
            self.assertEqual(result.returncode, 0, path)
            self.assertEqual(sha256(result.stdout), expected, path)

    def test_v11_outcome_binds_the_write_once_zero_data_artifacts(self) -> None:
        outcome = json.loads(V11_OUTCOME.read_text(encoding="utf-8"))
        self.assertEqual(outcome["scientific_rows"], 0)
        self.assertEqual(outcome["claims_admitted"], [])
        self.assertEqual(
            outcome["classification"],
            "incomplete_session/provider_create_failure_before_data",
        )
        retained = outcome["retained_diagnostics"]
        for path_key, sha_key in (
            ("preflight_receipt_path", "preflight_receipt_sha256"),
            ("receipt_path", "receipt_sha256"),
            ("terminal_verdict_path", "terminal_verdict_sha256"),
        ):
            path = HERE / retained[path_key]
            self.assertTrue(path.is_file(), path)
            self.assertEqual(sha256(path.read_bytes()), retained[sha_key], path)


if __name__ == "__main__":
    unittest.main()
