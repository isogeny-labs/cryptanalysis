#!/usr/bin/env python3
"""Regression tests for the mandatory v11 pre-provider clean-build gate."""

from __future__ import annotations

import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SPEC = importlib.util.spec_from_file_location(
    "preflight_gpu_geometry_v11", HERE / "preflight_gpu_geometry_v11.py"
)
assert SPEC is not None and SPEC.loader is not None
MOD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MOD
SPEC.loader.exec_module(MOD)


class PreflightV11Tests(unittest.TestCase):
    def test_bootstrap_rejects_unpinned_rustup_bytes_before_execution(self) -> None:
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(MOD.urllib.request, "urlopen", return_value=io.BytesIO(b"wrong")), \
                mock.patch.object(MOD.subprocess, "run") as run:
            with self.assertRaisesRegex(MOD.PreflightError, "rustup-init"):
                MOD.bootstrap_toolchain(Path(directory))
            run.assert_not_called()

    def test_fresh_registered_archive_has_exact_identity_and_members(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "candidate.tar"
            MOD.create_archive(REPO, archive)
            observed = MOD.inspect_archive(archive)
        self.assertEqual(observed["roots"], list(MOD.ARCHIVE_ROOTS))
        self.assertEqual(observed["sha256"], MOD.ARCHIVE_SHA256)
        self.assertEqual(observed["bytes"], MOD.ARCHIVE_BYTES)
        self.assertEqual(observed["files"], MOD.ARCHIVE_FILES)

    def test_missing_cuda_or_challenges_is_rejected(self) -> None:
        for omitted, member in (
            ("cuda", "cuda/ca_device.cuh"),
            ("challenges", "challenges/elliptic/corpus.json"),
        ):
            roots = tuple(root for root in MOD.ARCHIVE_ROOTS if root != omitted)
            with tempfile.TemporaryDirectory() as directory:
                archive = Path(directory) / "candidate.tar"
                MOD.create_archive(REPO, archive, roots)
                names, _files = MOD.archive_member_inventory(archive)
            self.assertNotIn(member, names)
            with self.assertRaisesRegex(MOD.PreflightError, member.replace(".", r"\.")):
                MOD.require_closure_members(names)

    def test_constructed_arms_have_exact_single_source_delta(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "candidate.tar"
            MOD.create_archive(REPO, archive)
            MOD.inspect_archive(archive)
            observed = MOD.construct_arms(REPO, archive, root / "source")
        self.assertEqual(observed["differences"], [MOD.F4_PATH])
        self.assertEqual(observed["files_per_arm"], MOD.ARCHIVE_FILES)

    def test_perform_requires_two_distinct_builds_and_identical_aa_copy(self) -> None:
        def fake_build(arm: str, source: Path, target: Path,
                       environment: dict[str, str], cargo: Path) -> dict:
            self.assertEqual(environment["CARGO_INCREMENTAL"], "0")
            self.assertEqual(cargo.name, "cargo")
            binary = target / "release" / "examples" / "f4_matrix_bench"
            binary.parent.mkdir(parents=True)
            binary.write_bytes((arm + "-binary").encode())
            os.chmod(binary, 0o700)
            return {
                "arm": arm,
                "command": list(MOD.BUILD_COMMAND),
                "returncode": 0,
                "elapsed_seconds": 1.0,
                "log_sha256": "0" * 64,
                "log_bytes": 0,
                "binary_sha256": MOD.sha256_file(binary),
                "binary_bytes": binary.stat().st_size,
            }

        synthetic_toolchain = {
            "bootstrap": {"url": MOD.RUSTUP_INIT_URL, "sha256": MOD.RUSTUP_INIT_SHA256,
                          "log_sha256": "0" * 64, "log_bytes": 1},
            "rustc": {"toolchain": MOD.RUST_TOOLCHAIN, "sha256": MOD.RUSTC_SHA256,
                      "version": "rustc 1.91.1"},
            "cargo": {"toolchain": MOD.RUST_TOOLCHAIN, "sha256": MOD.CARGO_SHA256,
                      "version": "cargo 1.91.1"},
            "cc": {"realpath": MOD.CC_REALPATH, "sha256": MOD.CC_SHA256,
                   "version": MOD.CC_VERSION},
        }
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(MOD, "build_arm", side_effect=fake_build), \
                mock.patch.object(
                    MOD, "bootstrap_toolchain",
                    return_value=(synthetic_toolchain, {"CARGO_INCREMENTAL": "0"}, Path("/tmp/cargo")),
                ):
            record = MOD.perform(REPO, Path(directory))
        contract = record["binary_contract"]
        self.assertTrue(contract["baseline_aa_equals_baseline"])
        self.assertTrue(contract["candidate_differs"])
        self.assertNotEqual(contract["baseline_sha256"], contract["candidate_sha256"])

    def test_receipt_is_write_once_and_failure_is_recorded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "receipt.json"
            argv = [
                "run", "--repo", str(REPO),
                "--run-id", "gpu-geometry-http-rtx5090-v11-unit",
                "--protocol-sha256", "a" * 64, "--out", str(out),
            ]
            with mock.patch.object(MOD, "perform", side_effect=MOD.PreflightError("blocked")):
                self.assertEqual(MOD.main(argv), 2)
                self.assertEqual(MOD.main(argv), 2)
            record = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(record["status"], "failed")
            self.assertFalse(record["provider_actions"])
            self.assertEqual(record["error"]["type"], "PreflightError")


if __name__ == "__main__":
    unittest.main()
