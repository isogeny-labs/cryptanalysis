#!/usr/bin/env python3
"""Regression tests for the mandatory v12 pre-provider clean-build gate."""

from __future__ import annotations

import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SPEC = importlib.util.spec_from_file_location(
    "preflight_gpu_geometry_v12", HERE / "preflight_gpu_geometry_v12.py"
)
assert SPEC is not None and SPEC.loader is not None
MOD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MOD
SPEC.loader.exec_module(MOD)


class PreflightV12Tests(unittest.TestCase):
    def test_launcher_policy_accepts_only_isolated_exact_process(self) -> None:
        code = (
            "import importlib.util;"
            f"p={str(HERE / 'preflight_gpu_geometry_v12.py')!r};"
            "s=importlib.util.spec_from_file_location('p',p);"
            "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
            "m.validate_launcher_environment()"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            home, temporary = root / "home", root / "tmp"
            home.mkdir(); temporary.mkdir()
            environment = {
                "PATH": "/usr/bin:/bin", "HOME": str(home), "TMPDIR": str(temporary),
                "LANG": "C", "LC_ALL": "C", "TZ": "UTC",
            }
            accepted = subprocess.run(
                ["/usr/bin/python3", "-I", "-S", "-B", "-c", code],
                env=environment, capture_output=True, text=True, check=False,
            )
            self.assertEqual(accepted.returncode, 0, accepted.stderr)
            hostile = dict(environment, PYTHONPATH="/tmp/injected")
            rejected = subprocess.run(
                ["/usr/bin/python3", "-I", "-S", "-B", "-c", code],
                env=hostile, capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(rejected.returncode, 0)

    def test_build_environment_drops_injected_compiler_runtime_and_f4_variables(self) -> None:
        injected = {
            "RUSTFLAGS": "-C target-cpu=native", "CARGO_ENCODED_RUSTFLAGS": "bad",
            "CARGO_PROFILE_RELEASE_LTO": "true", "CFLAGS": "-march=native",
            "LD_PRELOAD": "/tmp/evil.so", "RAYON_NUM_THREADS": "99",
            "F4_F2_ECHELON": "cpu", "HTTP_PROXY": "http://proxy.invalid",
        }
        with tempfile.TemporaryDirectory() as directory, mock.patch.dict(
            MOD.os.environ, injected, clear=True,
        ):
            root = Path(directory)
            environment, hashes = MOD.exact_base_environment(
                root, root / "rustup", root / "cargo", network=True,
            )
        self.assertEqual(set(environment) & set(injected), {"HTTP_PROXY"})
        self.assertEqual(set(hashes), {"HTTP_PROXY"})

    def test_system_tool_drift_between_arms_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tool"
            path.write_bytes(b"one")
            item = {"realpath": str(path), "sha256": MOD.sha256_file(path)}
            record = {name: dict(item) for name in ("cc", "ar", "ranlib", "linker", "collect2")}
            MOD.verify_system_tools_unchanged(record)
            path.write_bytes(b"two")
            with self.assertRaisesRegex(MOD.PreflightError, "drifted"):
                MOD.verify_system_tools_unchanged(record)

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
            "system_policy": "controller_exact_hashes",
            "bootstrap": {"url": MOD.RUSTUP_INIT_URL, "sha256": MOD.RUSTUP_INIT_SHA256,
                          "log_sha256": "0" * 64, "log_bytes": 1},
            "rustc": {"toolchain": MOD.RUST_TOOLCHAIN, "sha256": MOD.RUSTC_SHA256,
                      "version": "rustc 1.91.1"},
            "cargo": {"toolchain": MOD.RUST_TOOLCHAIN, "sha256": MOD.CARGO_SHA256,
                      "version": "cargo 1.91.1"},
            "cc": {"realpath": MOD.CC_REALPATH, "sha256": MOD.CC_SHA256,
                   "version": MOD.CC_VERSION},
            "ar": {"realpath": MOD.AR_REALPATH, "sha256": MOD.AR_SHA256},
            "ranlib": {"realpath": MOD.RANLIB_REALPATH, "sha256": MOD.RANLIB_SHA256},
            "linker": {"realpath": MOD.LINKER_REALPATH, "sha256": MOD.LINKER_SHA256},
            "collect2": {"realpath": MOD.COLLECT2_REALPATH, "sha256": MOD.COLLECT2_SHA256},
        }
        dependency = {"command": list(MOD.FETCH_COMMAND), "returncode": 0,
                      "log_sha256": "0" * 64, "log_bytes": 0,
                      "cargo_config_candidates_checked": 10, "cargo_config_all_absent": True}
        launcher = {
            "fixed": {"PATH": "/usr/bin:/bin", "HOME": "<caller-owned-fresh-home>",
                      "TMPDIR": "<caller-owned-fresh-tmp>", "LANG": "C", "LC_ALL": "C", "TZ": "UTC"},
            "exact_keys": sorted(["PATH", "HOME", "TMPDIR", "LANG", "LC_ALL", "TZ"]),
            "network_forward_allowlist": list(MOD.NETWORK_ENV_ALLOWLIST),
            "network_forwarded_value_sha256": {},
            "python": {"executable": "/usr/bin/python3", "flags": ["-I", "-S", "-B"],
                       "isolated": True, "no_site": True, "dont_write_bytecode": True,
                       "safe_path": True},
        }
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(MOD, "validate_launcher_environment", return_value=launcher), \
                mock.patch.object(MOD, "build_arm", side_effect=fake_build), \
                mock.patch.object(MOD, "fetch_dependencies", return_value=dependency), \
                mock.patch.object(
                    MOD, "bootstrap_toolchain",
                    return_value=(
                        synthetic_toolchain, {}, {
                            "CARGO_INCREMENTAL": "0", "CARGO_HOME": "/tmp/cargo-home",
                        },
                        Path("/tmp/cargo"), {
                            "location_policy": "local_controller",
                            "network_forwarded_value_sha256": {},
                        },
                    ),
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
                "--run-id", "gpu-geometry-http-rtx5090-v12-unit",
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
