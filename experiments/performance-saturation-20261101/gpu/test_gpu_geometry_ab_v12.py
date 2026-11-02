#!/usr/bin/env python3
"""Focused standard-library tests for the frozen GPU geometry analyzer."""

from __future__ import annotations

import importlib.util
import hashlib
import json
import sqlite3
import sys
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "analyze_gpu_geometry_ab_v12", HERE / "analyze_gpu_geometry_ab_v12.py"
)
assert SPEC is not None and SPEC.loader is not None
MOD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MOD
SPEC.loader.exec_module(MOD)


def make_trace(path: Path, blocks_per_sm: int) -> None:
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE StringIds (id INTEGER PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE CUPTI_ACTIVITY_KIND_KERNEL (
            start INTEGER NOT NULL,
            shortName INTEGER NOT NULL,
            gridX INTEGER NOT NULL, gridY INTEGER NOT NULL, gridZ INTEGER NOT NULL,
            blockX INTEGER NOT NULL, blockY INTEGER NOT NULL, blockZ INTEGER NOT NULL,
            registersPerThread INTEGER NOT NULL,
            staticSharedMemory INTEGER NOT NULL,
            dynamicSharedMemory INTEGER NOT NULL,
            localMemoryPerThread INTEGER NOT NULL
        );
        """
    )
    names = {
        "f4e_gather": 1,
        "f4e_panel_block": 2,
        "f4e_materialise": 3,
        "f4e_update": 4,
        "f4e_low": 5,
    }
    connection.executemany(
        "INSERT INTO StringIds(id, value) VALUES (?, ?)",
        [(identifier, name) for name, identifier in names.items()],
    )
    rows = []
    start = 0
    for launch in range(MOD.EXPECTED_UPDATE_LAUNCHES):
        remaining_words = MOD.EXPECTED_UPDATE_LAUNCHES - launch
        materialise_grid = (remaining_words + 127) // 128
        tiles = (remaining_words + 31) // 32
        update_grid = tiles * MOD.parts_for(170, tiles, blocks_per_sm)
        rows.extend([
            (start, names["f4e_gather"], 658, 1, 1, 256, 1, 1, 39, 0, 0, 0),
            (start + 1, names["f4e_panel_block"], 1, 1, 1, 1024, 1, 1, 47, 47392, 0, 0),
            (start + 2, names["f4e_materialise"], materialise_grid, 1, 1, 128, 1, 1, 40, 0, 0, 0),
            (start + 3, names["f4e_update"], update_grid, 1, 1, 256, 1, 1, 31, 16384, 0, 0),
        ])
        start += 4
    rows.append((start, names["f4e_low"], 658, 1, 1, 256, 1, 1, 30, 0, 0, 0))
    connection.executemany(
        """
        INSERT INTO CUPTI_ACTIVITY_KIND_KERNEL
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    connection.commit()
    connection.close()


class GeometryAnalyzerTests(unittest.TestCase):
    def test_remote_system_tool_policy_is_not_controller_hash_pinned(self) -> None:
        record = {
            "realpath": "/usr/bin/x86_64-linux-gnu-gcc-13",
            "sha256": "a" * 64,
            "version": "cc (Ubuntu 13.3.0) 13.3.0",
            "target": "x86_64-linux-gnu",
            "capabilities": {"compile": True, "archive": True, "ranlib": True,
                             "link": True, "execute": True},
        }
        self.assertTrue(MOD.safe_system_tool_record(record, cc=True))
        record["realpath"] = "/tmp/injected-cc"
        self.assertFalse(MOD.safe_system_tool_record(record, cc=True))

    def test_measurement_environment_requires_trusted_loader_and_nvrtc(self) -> None:
        loader_entries = ["/usr/local/nvidia/lib", "/usr/lib/x86_64-linux-gnu"]
        fixed = {
            "PATH": "/usr/bin:/bin",
            "HOME": "<remote-task-root>/measurement-home",
            "TMPDIR": "<remote-task-root>/measurement-tmp",
            "LANG": "C", "LC_ALL": "C", "TZ": "UTC", "CUDA_VISIBLE_DEVICES": "0",
            "F4_F2_ECHELON": "cuda", "F4_F2_ECHELON_VERBOSE": "1",
            "CA_NVRTC_LIB": "<remote-task-root>/nvrtc-wheel/libnvrtc.so.12",
        }
        with tempfile.TemporaryDirectory(
            prefix="cryptanalysis-gpu-geometry-v12.", dir="/tmp",
        ) as directory:
            root = Path(directory)
            nvrtc_root = root / "nvrtc-wheel"
            value = {
                "schema": "gpu-geometry-measurement-environment/v1",
                "construction": "env -i exact allowlist for every timed binary; env -i system subset for analyzer and Nsys",
                "measurement_fixed": fixed,
                "measurement_exact_keys": sorted([*fixed, "LD_LIBRARY_PATH"]),
                "system_exact_keys": sorted(["PATH", "HOME", "TMPDIR", "LANG", "LC_ALL", "TZ", "LD_LIBRARY_PATH"]),
                "inherited_loader_path_present": True,
                "inherited_loader_path_entries": loader_entries,
                "inherited_loader_path_value_sha256": hashlib.sha256(":".join(loader_entries).encode()).hexdigest(),
                "measurement_loader_first": "<remote-task-root>/nvrtc-wheel",
                "measurement_loader_value_sha256": hashlib.sha256(
                    ":".join([str(nvrtc_root), *loader_entries]).encode()
                ).hexdigest(),
                "nvrtc_root_realpath": str(nvrtc_root),
                "nvrtc_library_realpath": str(nvrtc_root / "libnvrtc.so.12"),
                "nvrtc_library_sha256": MOD.NVRTC_LIBRARY_SHA256,
                "nvrtc_builtins_realpath": str(nvrtc_root / "libnvrtc-builtins.so.12.9"),
                "nvrtc_builtins_sha256": MOD.NVRTC_BUILTINS_SHA256,
                "forbidden_absent": ["RUSTFLAGS", "CARGO_ENCODED_RUSTFLAGS", "CFLAGS", "CXXFLAGS",
                                     "CPPFLAGS", "LDFLAGS", "LD_PRELOAD", "RUSTC_WRAPPER", "RAYON_NUM_THREADS"],
                "forbidden_prefixes_absent": ["CARGO_PROFILE_", "F4_ except the two exact fixed keys"],
            }
            metadata = root / "metadata"
            metadata.mkdir()
            path = metadata / "measurement-environment.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            (metadata / "nvrtc-install.json").write_text(json.dumps({
                "schema": "gpu-geometry-nvrtc-install/v1",
                "package": "nvidia-cuda-nvrtc-cu12", "version": "12.9.86",
                "wheel_url": MOD.NVRTC_WHEEL_URL,
                "wheel_sha256": MOD.NVRTC_WHEEL_SHA256,
                "wheel_bytes": MOD.NVRTC_WHEEL_BYTES,
                "libraries": [
                    {"wheel_member": MOD.NVRTC_LIBRARY_MEMBER,
                     "path": "<remote-task-root>/nvrtc-wheel/libnvrtc.so.12",
                     "sha256": MOD.NVRTC_LIBRARY_SHA256, "bytes": MOD.NVRTC_LIBRARY_BYTES},
                    {"wheel_member": MOD.NVRTC_BUILTINS_MEMBER,
                     "path": "<remote-task-root>/nvrtc-wheel/libnvrtc-builtins.so.12.9",
                     "sha256": MOD.NVRTC_BUILTINS_SHA256, "bytes": MOD.NVRTC_BUILTINS_BYTES},
                ],
                "compile_probe": {"architecture": "compute_120", "returncode": 0},
                "python_package_code_executed": False,
                "native_compile_probe_executed": True,
            }), encoding="utf-8")
            (metadata / "nsys-install.json").write_text(json.dumps({
                "schema": "gpu-geometry-nsys-install/v1", "package": MOD.NSYS_PACKAGE,
                "package_version": MOD.NSYS_PACKAGE_VERSION,
                "package_deb_url": MOD.NSYS_DEB_URL,
                "package_deb_sha256": MOD.NSYS_DEB_SHA256,
                "package_deb_bytes": MOD.NSYS_DEB_BYTES,
                "package_control": {
                    "Package": MOD.NSYS_PACKAGE, "Version": MOD.NSYS_PACKAGE_VERSION,
                    "Architecture": "amd64",
                },
                "extraction_root": "<remote-task-root>/nsys-package",
                "extraction_root_realpath": str(root / "nsys-package"),
                "binary_path": MOD.NSYS_BINARY_CONTRACT,
                "binary_realpath": str(root / "nsys-package" / MOD.NSYS_BINARY_RELATIVE),
                "binary_sha256": MOD.NSYS_BINARY_SHA256,
                "binary_bytes": MOD.NSYS_BINARY_BYTES,
                "version_output": MOD.NSYS_VERSION_OUTPUT,
                "installed": False, "maintainer_scripts_executed": False,
                "system_package_manager_mutation": False,
                "dependency_source": "digest-pinned image plus exact extracted deb; missing dependencies fail closed",
                "extractor_path": "ecc2k130/runner/codegen/extract_nsys_tools_v12.sh",
                "extractor_sha256": MOD.NSYS_EXTRACTOR_SHA256,
            }), encoding="utf-8")
            (metadata / "nsys-version.txt").write_text(MOD.NSYS_VERSION_OUTPUT + "\n", encoding="utf-8")
            MOD.validate_measurement_environment(root, False)
            nsys_path = metadata / "nsys-install.json"
            nsys_receipt = json.loads(nsys_path.read_text(encoding="utf-8"))
            for key, bad in (
                ("package_deb_sha256", "0" * 64),
                ("package_deb_bytes", MOD.NSYS_DEB_BYTES - 1),
                ("extraction_root_realpath", "/tmp/injected/nsys-package"),
                ("binary_realpath", "/tmp/injected/nsys"),
                ("binary_sha256", "0" * 64),
                ("binary_bytes", MOD.NSYS_BINARY_BYTES - 1),
            ):
                changed = dict(nsys_receipt)
                changed[key] = bad
                nsys_path.write_text(json.dumps(changed), encoding="utf-8")
                with self.assertRaises(MOD.GateError):
                    MOD.validate_nsys_install(root, False)
            nsys_path.write_text(json.dumps(nsys_receipt), encoding="utf-8")
            for key, bad in (
                ("inherited_loader_path_entries", ["relative/injected"]),
                ("inherited_loader_path_entries", ["/tmp/injected"]),
                ("measurement_loader_value_sha256", "0" * 64),
                ("nvrtc_library_realpath", "/tmp/libnvrtc.so.12"),
                ("nvrtc_library_sha256", "0" * 63),
                ("nvrtc_builtins_realpath", "/tmp/libnvrtc-builtins.so.12.9"),
                ("nvrtc_builtins_sha256", "0" * 64),
            ):
                changed = dict(value)
                changed[key] = bad
                path.write_text(json.dumps(changed), encoding="utf-8")
                with self.assertRaises(MOD.GateError):
                    MOD.validate_measurement_environment(root, False)

            # The required sibling is a separately bound wheel member.
            receipt_path = metadata / "nvrtc-install.json"
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt["libraries"] = receipt["libraries"][:1]
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaises(MOD.GateError):
                MOD.validate_measurement_environment(root, False)

    def test_registered_grid_math(self) -> None:
        self.assertEqual(MOD.parts_for(170, 92, 4), 8)
        self.assertEqual(MOD.parts_for(170, 92, 6), 12)
        self.assertEqual(MOD.infer_tiles(23, 736, 170), 92)

    def test_exact_bootstrap_identity(self) -> None:
        values = [Fraction(index, 10) for index in range(10, 16)]
        self.assertEqual(
            MOD.bootstrap_interval(values, values),
            (Fraction(1, 1), Fraction(1, 1)),
        )

    def test_primary_must_strictly_clear_same_session_aa_floor(self) -> None:
        effect = Fraction(103, 100)
        noise = Fraction(101, 100)
        self.assertFalse(MOD.primary_geometry_pass(effect, noise, noise))
        self.assertTrue(MOD.primary_geometry_pass(effect, Fraction(102, 100), noise))

    def test_aa_interval_must_contain_identity(self) -> None:
        self.assertTrue(MOD.aa_interval_admissible(Fraction(99, 100), Fraction(101, 100)))
        self.assertFalse(MOD.aa_interval_admissible(Fraction(1001, 1000), Fraction(101, 100)))

    def test_wide_aa_interval_containing_identity_is_inadmissible(self) -> None:
        self.assertFalse(MOD.aa_interval_admissible(Fraction(9, 10), Fraction(11, 10)))
        self.assertFalse(MOD.aa_interval_admissible(Fraction(49, 50), Fraction(51, 50)))

    def test_mechanism_gate_accepts_only_registered_change(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline = root / "baseline.sqlite"
            candidate = root / "candidate.sqlite"
            make_trace(baseline, 4)
            make_trace(candidate, 6)
            result = MOD.mechanism_gate(baseline, candidate, 170)
            self.assertEqual(result["update_launches_per_arm"], 2941)
            self.assertGreater(result["changed_update_launches"], 0)
            self.assertEqual(result["transitions"]["92:736->1104"], 29)

    def test_mechanism_gate_rejects_baseline_grid_in_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline = root / "baseline.sqlite"
            candidate = root / "candidate.sqlite"
            make_trace(baseline, 4)
            make_trace(candidate, 4)
            with self.assertRaises(MOD.GateError):
                MOD.mechanism_gate(baseline, candidate, 170)


if __name__ == "__main__":
    unittest.main()
