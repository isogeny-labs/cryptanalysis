#!/usr/bin/env python3
"""Mechanically gate and analyse the prospective RTX 5090 F4 geometry A/B.

The analyzer is deliberately the executable registry for the five matrices,
the exact answer oracle, the numeric isolation gate, the finite paired
bootstrap, the Nsight Systems mechanism check, and the experiment.export/v1
writer.  Its timing classification is provisional: the controller-side
finalizer is the only terminal adjudicator because cleanup and the complete
transport archive do not exist while this process is running.  This program
uses only the Python standard library and never overwrites an artifact.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
import os
import re
import sqlite3
import statistics
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from typing import Any, Iterable


ARMS = ("baseline", "baseline-aa", "candidate")
PROFILE_ARMS = ("baseline", "candidate")
ARM_ROLES = {"baseline": "baseline", "baseline-aa": "control_aa", "candidate": "candidate"}
MEASURED_ROUNDS = tuple(range(1, 7))
EXPECTED_GPU = "NVIDIA GeForce RTX 5090"
PROTOCOL_ID = "gpu-f4-update-grid-ab-rtx5090-http-v11-20261101"
PROTOCOL_VERSION = 11
PROTOCOL_RELATIVE = "../../protocol-http-rtx5090-geometry-v11.json"
ANALYZER_RELATIVE = "../../analyze_gpu_geometry_ab_v11.py"
BASELINE_ORIGIN_COMMIT = "7c712913b7e912494e87c35e854cfd0129bad89c"
CANDIDATE_COMMIT = "59b6d7e17100d4d16db5d25c2762a5d5cf45ef4f"
CANDIDATE_TREE = "af0ac7e239c0acaa063c1a1441d6fb374ebbf30b"
CANDIDATE_BUILD_ARCHIVE_SHA256 = "554dcaacb7ff1fcfb27f4b49bb60b2d03ac9201978091c5e516fff356d1f9b8d"
BASELINE_F4_SHA256 = "da8c53c757cac0dfd81d1f75bfc5845610b645338215e52710efa11d57783944"
CANDIDATE_F4_SHA256 = "77832323d4d5a2b6b49fa2ca26fe40de1a80c0a8e17a9bb1949081a30fa84953"
PRODUCTION_DIFF_SHA256 = "34bf0033dd2bbd14b30ef2eaacaceb2d3bf9869504fca043585b1c78b48e43d3"
F4_PATH = "suite/src/cryptanalysis/f4_gpu.rs"
TOOLING_REF = "refs/heads/codex/runpod-http-gpu-geometry-v11-20261101"
HISTORY_DEEPEN_COMMITS = 64
AB_INTERVALS = 10
AA_INTERVALS = 10
FAMILY_INTERVALS = AB_INTERVALS + AA_INTERVALS
# Twenty two-sided simultaneous intervals: alpha / (2 * 20) = 1/800.
INTERVAL_TAIL = Fraction(1, 2 * 20 * FAMILY_INTERVALS)
PRIMARY_EFFECT = Fraction(51, 50)  # at least 1.02x baseline/candidate
NONREGRESSION = Fraction(50, 51)  # candidate no more than 2% slower
AA_RESOLUTION = Fraction(51, 50)  # same-session symmetric clock noise <=2%
EXPECTED_UPDATE_LAUNCHES = 2941
EXPECTED_ARCHIVE_FILES = 1253
EXPECTED_ARCHIVE_BYTES = 19_435_520
EXPECTED_PREFLIGHT_TOOL_SHA256 = "e52262dec35559e2c1e8f559c1b9817568a2b9e484dd6e76df5c8e9eaaf56572"
EXPECTED_RUSTUP_URL = (
    "https://static.rust-lang.org/rustup/archive/1.29.2/"
    "x86_64-unknown-linux-gnu/rustup-init"
)
EXPECTED_RUSTUP_SHA256 = "5be191e8c70a5007074254cb74d78dbfdd25cd5a61c27de7b8e5410122ec24f4"
EXPECTED_RUSTC_SHA256 = "5eadaaf4fe086d76547b17dc3c1ba880d0082b93f7d8bc65612770da8e79fe8e"
EXPECTED_CARGO_SHA256 = "e60b4010303c19a131c058e3f054b4b3311433c4b2ee94ba8e09e165ff2a3b3b"
RUST_TOOLCHAIN = "1.91.1-x86_64-unknown-linux-gnu"
NVRTC_WHEEL_URL = "https://files.pythonhosted.org/packages/b8/85/e4af82cc9202023862090bfca4ea827d533329e925c758f0cde964cb54b7/nvidia_cuda_nvrtc_cu12-12.9.86-py3-none-manylinux2010_x86_64.manylinux_2_12_x86_64.whl"
NVRTC_WHEEL_SHA256 = "210cf05005a447e29214e9ce50851e83fc5f4358df8b453155d5e1918094dcb4"
NVRTC_WHEEL_BYTES = 89_568_129
NVRTC_LIBRARY_MEMBER = "nvidia/cuda_nvrtc/lib/libnvrtc.so.12"
NVRTC_LIBRARY_SHA256 = "7c67c6b51ea0e0279634cebd676ff7efda1674806444520c84430ad5c35fe625"
NVRTC_LIBRARY_BYTES = 106_244_480
NVRTC_BUILTINS_MEMBER = "nvidia/cuda_nvrtc/lib/libnvrtc-builtins.so.12.9"
NVRTC_BUILTINS_SHA256 = "6507cf33450cfb22970c2c1e7aa8e7c0a33e39d864720277b05f61a92791e2e8"
NVRTC_BUILTINS_BYTES = 7_202_760
NSYS_PACKAGE = "nsight-systems-2026.3.2"
NSYS_PACKAGE_VERSION = "2026.3.2.476-263238834031v0"
NSYS_DEB_URL = (
    "https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/x86_64/"
    "nsight-systems-2026.3.2_2026.3.2.476-1_amd64.deb"
)
NSYS_DEB_SHA256 = "e9bf0ff9c613ff5545095a4177676a9579cb666e78c8621c3792f3559e2c1690"
NSYS_DEB_BYTES = 448_261_416
NSYS_BINARY_RELATIVE = "opt/nvidia/nsight-systems/2026.3.2/target-linux-x64/nsys"
NSYS_BINARY_CONTRACT = f"<remote-task-root>/nsys-package/{NSYS_BINARY_RELATIVE}"
NSYS_BINARY_SHA256 = "68a5fb843322bda1b090900a0297b9d5bee43daf8b870a809a6f8aa93059ae16"
NSYS_BINARY_BYTES = 87_282_816
NSYS_VERSION_OUTPUT = "NVIDIA Nsight Systems version 2026.3.2.476-263238834031v0"
NSYS_EXTRACTOR_SHA256 = "de9c0aa2024e0f5570a4f7138467d95ed7124b56453726d846b3be8c2b9e2900"
NETWORK_ENV_ALLOWLIST = (
    "ALL_PROXY", "HTTPS_PROXY", "HTTP_PROXY", "NO_PROXY", "SSL_CERT_FILE", "CURL_CA_BUNDLE",
)
FORBIDDEN_BUILD_ENV_PATTERNS = (
    "RUSTFLAGS", "CARGO_ENCODED_RUSTFLAGS", "CARGO_PROFILE_*", "CARGO_TARGET_DIR",
    "RUSTC_WRAPPER", "RUSTC_WORKSPACE_WRAPPER", "CFLAGS", "CXXFLAGS", "CPPFLAGS",
    "LDFLAGS", "LD_PRELOAD", "AR", "CC", "RANLIB", "RAYON_NUM_THREADS", "F4_*",
)

VERBOSE_RE = re.compile(
    r"^F4_F2_ECHELON: .*? upload ([0-9]+(?:\.[0-9]+)?) ms, "
    r"device ([0-9]+(?:\.[0-9]+)?) ms, download ([0-9]+(?:\.[0-9]+)?) ms,"
    r" ([0-9.eE+-]+) word XORs$",
    re.MULTILINE,
)
CUDA_BACKEND_RE = re.compile(
    r"^cuda:(?P<gpu>[^\r\n]+?) sm_[0-9]+ x(?P<sms>[1-9][0-9]*) "
    r"code=(?:sm_[0-9]+|compute_[0-9]+|CA_F4_PTX)$"
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


@dataclass(frozen=True)
class Workload:
    role: str
    tag: str
    cell: str
    degree: int
    curve: str
    m: int
    target_x: int
    rows: int
    cols: int
    rank: int
    refuted: bool
    pinned: int
    word_ops: int


WORKLOADS = (
    Workload("holdout", "k0n13m2d5", "0:13:2:1234", 5, "K_0/2^13", 2, 1234,
             30225, 53871, 27250, True, 0, 10745652033),
    Workload("holdout", "k0n9m3d5", "0:9:3:77", 5, "K_0/2^9", 3, 77,
             33147, 87118, 31069, False, 1, 1196809344),
    Workload("holdout", "k1n11m2d5", "1:11:2:301", 5, "K_1/2^11", 2, 301,
             14861, 21196, 12091, False, 0, 986408355),
    Workload("holdout", "k1n11m2d6", "1:11:2:301", 6, "K_1/2^11", 2, 301,
             68156, 60040, 46747, False, 0, 57968918179),
    Workload("primary", "k0n13m2d6", "0:13:2:1234", 6, "K_0/2^13", 2, 1234,
             168363, 188203, 130583, True, 0, 1110114894889),
)
BY_TAG = {workload.tag: workload for workload in WORKLOADS}


class GateError(RuntimeError):
    """An observed artifact violates a frozen gate."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_record(path: Path, base: Path, kind: str | None = None) -> dict[str, Any]:
    record: dict[str, Any] = {
        "path": os.path.relpath(path, base),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
    }
    if kind is not None:
        record["kind"] = kind
    return record


def require_nonempty(path: Path) -> None:
    if not path.is_file() or path.stat().st_size == 0:
        raise GateError(f"missing or empty artifact: {path}")


def load_json(path: Path) -> Any:
    require_nonempty(path)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GateError(f"invalid JSON {path}: {exc}") from exc


def finite_nonnegative(value: object) -> bool:
    return (
        isinstance(value, (int, float)) and not isinstance(value, bool)
        and math.isfinite(value) and value >= 0
    )


def parse_utc(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(
            value[:-1] + "+00:00" if value.endswith("Z") else value
        )
    except ValueError:
        return None
    return parsed.astimezone(timezone.utc) if parsed.tzinfo is not None else None


def read_status(path: Path) -> int:
    require_nonempty(path)
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError) as exc:
        raise GateError(f"invalid status {path}: {exc}") from exc


def exclusive_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write("\n")


def exclusive_jsonl(path: Path, values: Iterable[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        for value in values:
            stream.write(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")


def validate_gpu_inventory(session: Path, expected_gpu: str) -> dict[str, str]:
    path = session / "metadata" / "gpu.csv"
    require_nonempty(path)
    try:
        with path.open(newline="", encoding="utf-8") as stream:
            rows = [row for row in csv.reader(stream) if any(field.strip() for field in row)]
    except (OSError, csv.Error) as exc:
        raise GateError(f"invalid GPU inventory {path}: {exc}") from exc
    if len(rows) != 1 or len(rows[0]) != 11 or any(not field.strip() for field in rows[0]):
        raise GateError(f"{path}: expected exactly one complete eleven-field GPU row")
    row = [field.strip() for field in rows[0]]
    if row[2] != expected_gpu:
        raise GateError(f"{path}: GPU={row[2]!r}, expected {expected_gpu!r}")
    return {"uuid": row[1], "name": row[2], "driver": row[5], "compute_cap": row[3]}


def validate_backend(value: object, expected_gpu: str) -> tuple[str, int]:
    if not isinstance(value, str):
        raise GateError(f"malformed CUDA backend {value!r}")
    match = CUDA_BACKEND_RE.fullmatch(value)
    if match is None or match.group("gpu") != expected_gpu:
        raise GateError(f"unexpected CUDA backend {value!r}")
    return value, int(match.group("sms"))


def validate_source_identities(session: Path) -> dict[str, Any]:
    value = load_json(session / "source-identities.json")
    expected = {
        "baseline_origin_commit": BASELINE_ORIGIN_COMMIT,
        "candidate_commit": CANDIDATE_COMMIT,
        "candidate_tree": CANDIDATE_TREE,
        "candidate_archive_sha256": CANDIDATE_BUILD_ARCHIVE_SHA256,
        "baseline_f4_sha256": BASELINE_F4_SHA256,
        "candidate_f4_sha256": CANDIDATE_F4_SHA256,
        "production_diff_sha256": PRODUCTION_DIFF_SHA256,
        "production_path": F4_PATH,
        "only_production_path_differs": True,
        "tooling_ref": TOOLING_REF,
        "history_deepen_commits": HISTORY_DEEPEN_COMMITS,
    }
    exact_keys = set(expected) | {
        "schema", "archive_paths", "preflight_receipt_sha256",
        "remote_build_preflight_sha256", "construction",
    }
    if set(value) != exact_keys or value.get("schema") != "gpu-geometry-source-identities/v1":
        raise GateError("source identity key set/schema is not exact")
    for key, wanted in expected.items():
        if value.get(key) != wanted:
            raise GateError(f"source identity {key}={value.get(key)!r}, expected {wanted!r}")
    if value.get("archive_paths") != ["suite", "bindings/rust", "include", "src", "cuda", "challenges"]:
        raise GateError("source identity archive_paths is not the complete frozen v11 closure")
    if SHA256_RE.fullmatch(str(value.get("preflight_receipt_sha256", ""))) is None:
        raise GateError("source identity preflight receipt SHA-256 is malformed")
    if SHA256_RE.fullmatch(str(value.get("remote_build_preflight_sha256", ""))) is None:
        raise GateError("source identity remote build preflight SHA-256 is malformed")
    return value


def safe_system_tool_record(value: object, *, cc: bool = False) -> bool:
    if not isinstance(value, dict):
        return False
    keys = {"realpath", "sha256", "version"} | ({"target", "capabilities"} if cc else set())
    path = value.get("realpath")
    okay = (
        set(value) == keys and isinstance(path, str)
        and path.startswith(("/usr/bin/", "/usr/lib/", "/usr/libexec/"))
        and SHA256_RE.fullmatch(str(value.get("sha256", ""))) is not None
        and isinstance(value.get("version"), str) and bool(value["version"])
    )
    if not cc:
        return okay
    return (
        okay and re.fullmatch(r"x86_64(?:-[A-Za-z0-9_.]+)+", str(value.get("target"))) is not None
        and re.search(r"gcc|GCC|clang|Ubuntu|Debian", value["version"]) is not None
        and value.get("capabilities") == {
            "compile": True, "archive": True, "ranlib": True, "link": True, "execute": True,
        }
    )


def validate_remote_environment_policy(value: object) -> None:
    if not isinstance(value, dict):
        raise GateError("remote build environment policy is not an object")
    hashes = value.get("network_forwarded_value_sha256")
    if (not isinstance(hashes, dict) or set(hashes) - set(NETWORK_ENV_ALLOWLIST)
            or any(SHA256_RE.fullmatch(str(item)) is None for item in hashes.values())):
        raise GateError("remote build network environment hash policy is invalid")
    expected = {
        "bootstrap_fixed": {
            "PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C", "TZ": "UTC",
            "RUSTUP_HOME": "<fresh-task-root>/rustup-home",
            "CARGO_HOME": "<fresh-task-root>/cargo-home", "TMPDIR": "<fresh-task-root>/tmp",
        },
        "fetch_fixed": {
            "PATH": "<fresh-task-root>/cargo-home/bin:/usr/bin:/bin",
            "RUSTUP_HOME": "<fresh-task-root>/rustup-home",
            "CARGO_HOME": "<fresh-task-root>/cargo-home", "TMPDIR": "<fresh-task-root>/tmp",
            "LANG": "C", "LC_ALL": "C", "TZ": "UTC",
            "RUSTC": f"<fresh-task-root>/rustup-home/toolchains/{RUST_TOOLCHAIN}/bin/rustc",
        },
        "network_forward_allowlist": list(NETWORK_ENV_ALLOWLIST),
        "build_inherited_keys": [],
        "build_fixed": {
            "PATH": "<fresh-task-root>/cargo-home/bin:/usr/bin:/bin",
            "RUSTUP_HOME": "<fresh-task-root>/rustup-home",
            "CARGO_HOME": "<fresh-task-root>/cargo-home",
            "TMPDIR": "<fresh-task-root>/tmp/<arm>", "LANG": "C", "LC_ALL": "C", "TZ": "UTC",
            "RUSTC": f"<fresh-task-root>/rustup-home/toolchains/{RUST_TOOLCHAIN}/bin/rustc",
            "CC": "<resolved-remote-cc>", "AR": "<resolved-remote-ar>",
            "RANLIB": "<resolved-remote-ranlib>",
            "CARGO_TARGET_X86_64_UNKNOWN_LINUX_GNU_LINKER": "<resolved-remote-cc>",
            "CARGO_INCREMENTAL": "0", "CARGO_NET_OFFLINE": "true",
            "CARGO_TERM_COLOR": "never", "SOURCE_DATE_EPOCH": "0",
            "CARGO_TARGET_DIR": "<fresh-task-root>/target/<arm>",
        },
        "forbidden_inherited_patterns": list(FORBIDDEN_BUILD_ENV_PATTERNS),
        "cargo_config_policy": "fresh CARGO_HOME and no config/config.toml in source ancestors",
        "location_policy": "remote_pod",
    }
    if set(value) != set(expected) | {"network_forwarded_value_sha256", "launcher"}:
        raise GateError("remote build environment policy key set is not exact")
    for key, wanted in expected.items():
        if value.get(key) != wanted:
            raise GateError(f"remote build environment policy {key} differs from frozen value")
    launcher = value.get("launcher") if isinstance(value.get("launcher"), dict) else {}
    launcher_hashes = launcher.get("network_forwarded_value_sha256")
    expected_launcher_fixed = {
        "PATH": "/usr/bin:/bin", "HOME": "<caller-owned-fresh-home>",
        "TMPDIR": "<caller-owned-fresh-tmp>", "LANG": "C", "LC_ALL": "C", "TZ": "UTC",
    }
    expected_python = {
        "executable": "/usr/bin/python3", "flags": ["-I", "-S", "-B"],
        "isolated": True, "no_site": True, "dont_write_bytecode": True, "safe_path": True,
    }
    if (set(launcher) != {"fixed", "exact_keys", "network_forward_allowlist",
                          "network_forwarded_value_sha256", "python"}
            or launcher.get("fixed") != expected_launcher_fixed
            or launcher.get("network_forward_allowlist") != list(NETWORK_ENV_ALLOWLIST)
            or launcher_hashes != hashes
            or launcher.get("exact_keys") != sorted([*expected_launcher_fixed, *hashes])
            or launcher.get("python") != expected_python):
        raise GateError("remote preflight launcher environment is not exact and isolated")


def trusted_loader_entries(value: object, present: object) -> bool:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        return False
    if (present is True) != bool(value):
        return False
    prefixes = ("/usr/local/nvidia/", "/usr/local/cuda/", "/usr/lib/", "/lib/")
    for item in value:
        pure = Path(item)
        normalized = pure.as_posix()
        if (not item.startswith("/") or ".." in pure.parts or "//" in item
                or item.endswith("/") or normalized != item
                or not any((item + "/").startswith(prefix) for prefix in prefixes)):
            return False
    return True


def validate_nvrtc_install(session: Path) -> None:
    value = load_json(session / "metadata/nvrtc-install.json")
    expected = {
        "schema": "gpu-geometry-nvrtc-install/v1",
        "package": "nvidia-cuda-nvrtc-cu12",
        "version": "12.9.86",
        "wheel_url": NVRTC_WHEEL_URL,
        "wheel_sha256": NVRTC_WHEEL_SHA256,
        "wheel_bytes": NVRTC_WHEEL_BYTES,
        "libraries": [
            {
                "wheel_member": NVRTC_LIBRARY_MEMBER,
                "path": "<remote-task-root>/nvrtc-wheel/libnvrtc.so.12",
                "sha256": NVRTC_LIBRARY_SHA256,
                "bytes": NVRTC_LIBRARY_BYTES,
            },
            {
                "wheel_member": NVRTC_BUILTINS_MEMBER,
                "path": "<remote-task-root>/nvrtc-wheel/libnvrtc-builtins.so.12.9",
                "sha256": NVRTC_BUILTINS_SHA256,
                "bytes": NVRTC_BUILTINS_BYTES,
            },
        ],
        "compile_probe": {"architecture": "compute_120", "returncode": 0},
        "python_package_code_executed": False,
        "native_compile_probe_executed": True,
    }
    if value != expected:
        raise GateError("NVRTC wheel/library installation provenance is not exact")


def validate_nsys_install(session: Path, require_final_runtime: bool) -> None:
    value = load_json(session / "metadata/nsys-install.json")
    expected_static = {
        "schema": "gpu-geometry-nsys-install/v1",
        "package": NSYS_PACKAGE,
        "package_version": NSYS_PACKAGE_VERSION,
        "package_deb_url": NSYS_DEB_URL,
        "package_deb_sha256": NSYS_DEB_SHA256,
        "package_deb_bytes": NSYS_DEB_BYTES,
        "package_control": {
            "Package": NSYS_PACKAGE,
            "Version": NSYS_PACKAGE_VERSION,
            "Architecture": "amd64",
        },
        "extraction_root": "<remote-task-root>/nsys-package",
        "binary_path": NSYS_BINARY_CONTRACT,
        "binary_sha256": NSYS_BINARY_SHA256,
        "binary_bytes": NSYS_BINARY_BYTES,
        "version_output": NSYS_VERSION_OUTPUT,
        "installed": False,
        "maintainer_scripts_executed": False,
        "system_package_manager_mutation": False,
        "dependency_source": "digest-pinned image plus exact extracted deb; missing dependencies fail closed",
        "extractor_path": "ecc2k130/runner/codegen/extract_nsys_tools_v11.sh",
        "extractor_sha256": NSYS_EXTRACTOR_SHA256,
    }
    if (not isinstance(value, dict)
            or set(value) != set(expected_static) | {"extraction_root_realpath", "binary_realpath"}
            or any(value.get(key) != wanted for key, wanted in expected_static.items())
            or not isinstance(value.get("extraction_root_realpath"), str)
            or re.fullmatch(
                r"/tmp/cryptanalysis-gpu-geometry-v11\.[A-Za-z0-9_]+/nsys-package",
                value["extraction_root_realpath"],
            ) is None
            or value.get("binary_realpath")
            != f"{value['extraction_root_realpath']}/{NSYS_BINARY_RELATIVE}"):
        raise GateError("Nsight Systems package extraction provenance is not exact")
    version_path = session / "metadata/nsys-version.txt"
    require_nonempty(version_path)
    if version_path.read_text(encoding="utf-8").rstrip("\r\n") != NSYS_VERSION_OUTPUT:
        raise GateError("Nsight Systems runtime version output is not exact")
    final_path = session / "metadata/nsys-after.sha256"
    expected_final = f"{NSYS_BINARY_SHA256}  {NSYS_BINARY_CONTRACT}\n"
    if require_final_runtime:
        require_nonempty(final_path)
        if final_path.read_text(encoding="ascii") != expected_final:
            raise GateError("Nsight Systems binary drifted during registered profiles")
    elif final_path.exists() and final_path.read_text(encoding="ascii") != expected_final:
        raise GateError("present Nsight Systems final identity disagrees with install receipt")


def validate_measurement_environment(session: Path, require_final_runtime: bool) -> None:
    value = load_json(session / "metadata/measurement-environment.json")
    fixed = {
        "PATH": "/usr/bin:/bin",
        "HOME": "<remote-task-root>/measurement-home",
        "TMPDIR": "<remote-task-root>/measurement-tmp",
        "LANG": "C", "LC_ALL": "C", "TZ": "UTC", "CUDA_VISIBLE_DEVICES": "0",
        "F4_F2_ECHELON": "cuda", "F4_F2_ECHELON_VERBOSE": "1",
        "CA_NVRTC_LIB": "<remote-task-root>/nvrtc-wheel/libnvrtc.so.12",
    }
    loader = value.get("inherited_loader_path_present")
    expected_measurement_keys = sorted([*fixed, "LD_LIBRARY_PATH"])
    expected_system_keys = sorted([
        "PATH", "HOME", "TMPDIR", "LANG", "LC_ALL", "TZ",
        *(["LD_LIBRARY_PATH"] if loader is True else []),
    ])
    valid = (
        set(value) == {"schema", "construction", "measurement_fixed", "measurement_exact_keys",
                       "system_exact_keys", "inherited_loader_path_present",
                       "inherited_loader_path_value_sha256", "inherited_loader_path_entries",
                       "measurement_loader_first", "measurement_loader_value_sha256",
                       "nvrtc_root_realpath",
                       "nvrtc_library_realpath", "nvrtc_library_sha256",
                       "nvrtc_builtins_realpath", "nvrtc_builtins_sha256",
                       "forbidden_absent", "forbidden_prefixes_absent"}
        and value.get("schema") == "gpu-geometry-measurement-environment/v1"
        and value.get("construction") == "env -i exact allowlist for every timed binary; env -i system subset for analyzer and Nsys"
        and value.get("measurement_fixed") == fixed
        and value.get("measurement_exact_keys") == expected_measurement_keys
        and value.get("system_exact_keys") == expected_system_keys
        and type(loader) is bool
        and ((loader and SHA256_RE.fullmatch(str(value.get("inherited_loader_path_value_sha256", ""))) is not None)
             or (not loader and value.get("inherited_loader_path_value_sha256") is None))
        and trusted_loader_entries(value.get("inherited_loader_path_entries"), loader)
        and (
            value.get("inherited_loader_path_value_sha256")
            == (hashlib.sha256(":".join(value.get("inherited_loader_path_entries", [])).encode()).hexdigest()
                if loader else None)
        )
        and value.get("measurement_loader_first") == "<remote-task-root>/nvrtc-wheel"
        and SHA256_RE.fullmatch(str(value.get("measurement_loader_value_sha256", ""))) is not None
        and isinstance(value.get("nvrtc_root_realpath"), str)
        and re.fullmatch(
            r"/tmp/cryptanalysis-gpu-geometry-v11\.[A-Za-z0-9_]+/nvrtc-wheel",
            value["nvrtc_root_realpath"],
        ) is not None
        and value.get("measurement_loader_value_sha256") == hashlib.sha256(
            ":".join([
                value.get("nvrtc_root_realpath", ""),
                *value.get("inherited_loader_path_entries", []),
            ]).encode()
        ).hexdigest()
        and isinstance(value.get("nvrtc_library_realpath"), str)
        and re.fullmatch(
            r"/tmp/cryptanalysis-gpu-geometry-v11\.[A-Za-z0-9_]+/"
            r"nvrtc-wheel/libnvrtc\.so\.12",
            value["nvrtc_library_realpath"],
        ) is not None
        and value.get("nvrtc_library_sha256") == NVRTC_LIBRARY_SHA256
        and str(Path(value.get("nvrtc_library_realpath", "")).parent)
        == value.get("nvrtc_root_realpath")
        and isinstance(value.get("nvrtc_builtins_realpath"), str)
        and re.fullmatch(
            r"/tmp/cryptanalysis-gpu-geometry-v11\.[A-Za-z0-9_]+/"
            r"nvrtc-wheel/libnvrtc-builtins\.so\.12\.9",
            value["nvrtc_builtins_realpath"],
        ) is not None
        and value.get("nvrtc_builtins_sha256") == NVRTC_BUILTINS_SHA256
        and str(Path(value.get("nvrtc_builtins_realpath", "")).parent)
        == value.get("nvrtc_root_realpath")
        and value.get("forbidden_absent") == [
            "RUSTFLAGS", "CARGO_ENCODED_RUSTFLAGS", "CFLAGS", "CXXFLAGS", "CPPFLAGS",
            "LDFLAGS", "LD_PRELOAD", "RUSTC_WRAPPER", "RAYON_NUM_THREADS",
        ]
        and value.get("forbidden_prefixes_absent") == [
            "CARGO_PROFILE_", "F4_ except the two exact fixed keys",
        ]
    )
    if not valid:
        raise GateError("measurement/analyzer/Nsys environment closure is invalid")
    validate_nvrtc_install(session)
    validate_nsys_install(session, require_final_runtime)
    final_path = session / "metadata/nvrtc-after.sha256"
    expected_final = (
        f"{NVRTC_LIBRARY_SHA256}  libnvrtc.so.12\n"
        f"{NVRTC_BUILTINS_SHA256}  libnvrtc-builtins.so.12.9\n"
    )
    if require_final_runtime:
        require_nonempty(final_path)
        if final_path.read_text(encoding="ascii") != expected_final:
            raise GateError("NVRTC identity drifted between environment capture and final profile")
    elif final_path.exists() and final_path.read_text(encoding="ascii") != expected_final:
        raise GateError("present NVRTC final identity disagrees with environment capture")


def validate_remote_build_preflight(session: Path, identities: dict[str, Any],
                                    protocol_sha256: str | None = None,
                                    require_final_runtime: bool = False) -> None:
    path = session / "metadata/remote-build-preflight.json"
    value = load_json(path)
    required = {
        "schema", "protocol_id", "protocol_sha256", "run_id", "provider_actions", "location",
        "tool_sha256", "source", "build_contract", "started_at", "status", "error",
        "finished_at", "elapsed_seconds", "archive", "source_delta", "files_per_arm",
        "builds", "binary_contract", "toolchain", "dependency_fetch", "environment_policy",
    }
    if set(value) != required:
        raise GateError("remote build preflight key set is not exact")
    if (value.get("schema") != "gpu-geometry-build-preflight/v1"
            or value.get("protocol_id") != PROTOCOL_ID or value.get("run_id") != session.name
            or value.get("provider_actions") is not False or value.get("location") != "remote_pod"
            or value.get("status") != "passed" or value.get("error") is not None
            or SHA256_RE.fullmatch(str(value.get("protocol_sha256", ""))) is None
            or (protocol_sha256 is not None and value.get("protocol_sha256") != protocol_sha256)
            or value.get("tool_sha256") != EXPECTED_PREFLIGHT_TOOL_SHA256):
        raise GateError("remote build preflight identity/status is invalid")
    if sha256_file(path) != identities.get("remote_build_preflight_sha256"):
        raise GateError("remote build preflight receipt hash disagrees with source identity")
    started, finished = parse_utc(value.get("started_at")), parse_utc(value.get("finished_at"))
    if (started is None or finished is None or started > finished
            or not finite_nonnegative(value.get("elapsed_seconds"))):
        raise GateError("remote build preflight timestamps/duration are invalid")
    expected_source = {
        "baseline_commit": BASELINE_ORIGIN_COMMIT, "candidate_commit": CANDIDATE_COMMIT,
        "candidate_tree": CANDIDATE_TREE, "baseline_f4_sha256": BASELINE_F4_SHA256,
        "candidate_f4_sha256": CANDIDATE_F4_SHA256,
    }
    expected_contract = {
        "clean_extracted_closure": True, "isolated_source_trees": True,
        "isolated_target_dirs": True, "cargo_incremental": "0",
        "network_only_during_bootstrap_and_fetch": True, "offline_builds": True,
        "exact_environment_key_set": True,
    }
    if value.get("source") != expected_source or value.get("build_contract") != expected_contract:
        raise GateError("remote build source/contract differs from frozen values")
    expected_archive = {
        "roots": ["suite", "bindings/rust", "include", "src", "cuda", "challenges"],
        "sha256": CANDIDATE_BUILD_ARCHIVE_SHA256, "bytes": EXPECTED_ARCHIVE_BYTES,
        "files": EXPECTED_ARCHIVE_FILES,
        "required_members": [F4_PATH, "cuda/ca_device.cuh", "challenges/elliptic/corpus.json",
                             "suite/Cargo.lock", "bindings/rust/cryptanalysis-sys/build.rs"],
    }
    if (value.get("archive") != expected_archive or value.get("source_delta") != [F4_PATH]
            or value.get("files_per_arm") != EXPECTED_ARCHIVE_FILES):
        raise GateError("remote build closure archive/source delta is invalid")
    builds = value.get("builds")
    if not isinstance(builds, list) or len(builds) != 2:
        raise GateError("remote build receipt does not have two arm builds")
    for arm, item in zip(("baseline", "candidate"), builds):
        if (not isinstance(item, dict)
                or set(item) != {"arm", "command", "returncode", "elapsed_seconds",
                                 "log_sha256", "log_bytes", "binary_sha256", "binary_bytes"}
                or item.get("arm") != arm
                or item.get("command") != ["cargo", "build", "--release", "--locked", "--example", "f4_matrix_bench"]
                or item.get("returncode") != 0
                or not finite_nonnegative(item.get("elapsed_seconds"))
                or SHA256_RE.fullmatch(str(item.get("log_sha256", ""))) is None
                or type(item.get("log_bytes")) is not int or item["log_bytes"] < 0
                or SHA256_RE.fullmatch(str(item.get("binary_sha256", ""))) is None
                or type(item.get("binary_bytes")) is not int or item["binary_bytes"] <= 0):
            raise GateError(f"remote {arm} build record is invalid")
    hashes = parse_binary_hashes(session)
    contract = value.get("binary_contract") if isinstance(value.get("binary_contract"), dict) else {}
    if (set(contract) != {"baseline_sha256", "baseline_aa_sha256", "candidate_sha256",
                          "baseline_aa_equals_baseline", "candidate_differs"}
            or contract.get("baseline_sha256") != hashes["baseline"]
            or contract.get("baseline_aa_sha256") != hashes["baseline-aa"]
            or contract.get("candidate_sha256") != hashes["candidate"]
            or builds[0]["binary_sha256"] != hashes["baseline"]
            or builds[1]["binary_sha256"] != hashes["candidate"]
            or contract.get("baseline_aa_equals_baseline") is not True
            or contract.get("candidate_differs") is not True
            or hashes["baseline"] == hashes["candidate"]):
        raise GateError("remote build receipt/binary instrument hashes disagree")
    toolchain = value.get("toolchain") if isinstance(value.get("toolchain"), dict) else {}
    bootstrap = toolchain.get("bootstrap") if isinstance(toolchain.get("bootstrap"), dict) else {}
    rustc = toolchain.get("rustc") if isinstance(toolchain.get("rustc"), dict) else {}
    cargo = toolchain.get("cargo") if isinstance(toolchain.get("cargo"), dict) else {}
    if (set(toolchain) != {"system_policy", "bootstrap", "rustc", "cargo", "cc", "ar", "ranlib",
                           "linker", "collect2", "system_tools_unchanged_after_builds"}
            or toolchain.get("system_policy") != "remote_resolved_once_capability_checked_same_for_both_arms"
            or toolchain.get("system_tools_unchanged_after_builds") is not True
            or set(bootstrap) != {"url", "sha256", "log_sha256", "log_bytes"}
            or bootstrap.get("url") != EXPECTED_RUSTUP_URL
            or bootstrap.get("sha256") != EXPECTED_RUSTUP_SHA256
            or SHA256_RE.fullmatch(str(bootstrap.get("log_sha256", ""))) is None
            or type(bootstrap.get("log_bytes")) is not int or bootstrap["log_bytes"] < 0
            or set(rustc) != {"toolchain", "sha256", "version"}
            or rustc.get("toolchain") != RUST_TOOLCHAIN
            or rustc.get("sha256") != EXPECTED_RUSTC_SHA256
            or not isinstance(rustc.get("version"), str) or "rustc 1.91.1" not in rustc["version"]
            or set(cargo) != {"toolchain", "sha256", "version"}
            or cargo.get("toolchain") != RUST_TOOLCHAIN
            or cargo.get("sha256") != EXPECTED_CARGO_SHA256
            or not isinstance(cargo.get("version"), str) or not cargo["version"].startswith("cargo 1.91.1")
            or not safe_system_tool_record(toolchain.get("cc"), cc=True)
            or any(not safe_system_tool_record(toolchain.get(name))
                   for name in ("ar", "ranlib", "linker"))):
        raise GateError("remote resolved toolchain identity/capability record is invalid")
    collect2 = toolchain.get("collect2") if isinstance(toolchain.get("collect2"), dict) else {}
    if (set(collect2) != {"realpath", "sha256"}
            or not str(collect2.get("realpath", "")).startswith(("/usr/lib/", "/usr/libexec/"))
            or SHA256_RE.fullmatch(str(collect2.get("sha256", ""))) is None):
        raise GateError("remote collect2 identity is invalid")
    dependency = value.get("dependency_fetch") if isinstance(value.get("dependency_fetch"), dict) else {}
    if (set(dependency) != {"command", "returncode", "log_sha256", "log_bytes",
                            "cargo_config_candidates_checked", "cargo_config_all_absent"}
            or dependency.get("command") != ["cargo", "fetch", "--locked", "--manifest-path", "suite/Cargo.toml"]
            or dependency.get("returncode") != 0
            or SHA256_RE.fullmatch(str(dependency.get("log_sha256", ""))) is None
            or type(dependency.get("log_bytes")) is not int or dependency["log_bytes"] < 0
            or type(dependency.get("cargo_config_candidates_checked")) is not int
            or dependency["cargo_config_candidates_checked"] < 8
            or dependency.get("cargo_config_all_absent") is not True):
        raise GateError("remote locked dependency fetch/config gate is invalid")
    validate_remote_environment_policy(value.get("environment_policy"))
    validate_measurement_environment(session, require_final_runtime)


def parse_binary_hashes(session: Path) -> dict[str, str]:
    path = session / "binary-sha256.tsv"
    require_nonempty(path)
    hashes: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split("\t")
        if len(fields) != 2 or fields[0] not in ARMS or SHA256_RE.fullmatch(fields[1]) is None:
            raise GateError(f"malformed binary hash row: {line!r}")
        hashes[fields[0]] = fields[1]
    if set(hashes) != set(ARMS):
        raise GateError(f"missing binary hashes: {hashes}")
    if hashes["baseline"] != hashes["baseline-aa"]:
        raise GateError("same-session A/A instruments are not byte-identical")
    if hashes["baseline"] == hashes["candidate"]:
        raise GateError("the one-factor candidate unexpectedly matches baseline bytes")
    return hashes


def parse_psi_line(text: str, kind: str) -> dict[str, float]:
    for line in text.splitlines():
        fields = line.split()
        if fields and fields[0] == kind:
            out: dict[str, float] = {}
            for field in fields[1:]:
                key, value = field.split("=", 1)
                if key.startswith("avg"):
                    out[key] = float(value)
            if "avg10" not in out:
                break
            return out
    raise GateError(f"missing pressure {kind!r} line")


def capture_isolation() -> dict[str, Any]:
    """Capture one read-only cgroup/pressure/steal snapshot."""
    cgroup_rel = None
    for line in Path("/proc/self/cgroup").read_text(encoding="utf-8").splitlines():
        if line.startswith("0::"):
            cgroup_rel = line[3:]
            break
    if cgroup_rel is None:
        raise GateError("cgroup v2 unified path is unavailable")
    cgroup = Path("/sys/fs/cgroup") / cgroup_rel.lstrip("/")

    def key_values(path: Path) -> dict[str, int]:
        require_nonempty(path)
        out: dict[str, int] = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            fields = line.split()
            if len(fields) == 2:
                out[fields[0]] = int(fields[1])
        return out

    cpu_pressure = Path("/proc/pressure/cpu").read_text(encoding="utf-8")
    memory_pressure = Path("/proc/pressure/memory").read_text(encoding="utf-8")
    cpu_line = Path("/proc/stat").read_text(encoding="utf-8").splitlines()[0].split()
    if not cpu_line or cpu_line[0] != "cpu" or len(cpu_line) < 9:
        raise GateError("malformed aggregate /proc/stat CPU line")
    return {
        "captured_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "cgroup": str(cgroup),
        "cpu_psi": {
            "some": parse_psi_line(cpu_pressure, "some"),
            "full": parse_psi_line(cpu_pressure, "full"),
        },
        "memory_psi": {
            "some": parse_psi_line(memory_pressure, "some"),
            "full": parse_psi_line(memory_pressure, "full"),
        },
        "cpu_stat": key_values(cgroup / "cpu.stat"),
        "memory_events": key_values(cgroup / "memory.events"),
        "steal_jiffies": int(cpu_line[8]),
    }


def validate_isolation(before_path: Path, after_path: Path) -> dict[str, Any]:
    before, after = load_json(before_path), load_json(after_path)
    if before.get("cgroup") != after.get("cgroup"):
        raise GateError("cgroup changed during an execution")
    for snap_name, snap in (("before", before), ("after", after)):
        if float(snap["cpu_psi"]["some"]["avg10"]) > 10.0:
            raise GateError(f"{snap_name} CPU PSI some avg10 exceeds 10")
        if float(snap["cpu_psi"]["full"]["avg10"]) != 0.0:
            raise GateError(f"{snap_name} CPU PSI full avg10 is nonzero")
        for kind in ("some", "full"):
            if float(snap["memory_psi"][kind]["avg10"]) != 0.0:
                raise GateError(f"{snap_name} memory PSI {kind} avg10 is nonzero")
    deltas: dict[str, int] = {}
    for field in ("nr_throttled", "throttled_usec"):
        delta = int(after["cpu_stat"].get(field, 0)) - int(before["cpu_stat"].get(field, 0))
        deltas[f"cpu.{field}"] = delta
        if delta != 0:
            raise GateError(f"cgroup CPU throttling changed: {field}={delta}")
    for field in ("high", "max", "oom", "oom_kill", "oom_group_kill"):
        delta = int(after["memory_events"].get(field, 0)) - int(before["memory_events"].get(field, 0))
        deltas[f"memory.{field}"] = delta
        if delta != 0:
            raise GateError(f"cgroup memory event changed: {field}={delta}")
    steal_delta = int(after["steal_jiffies"]) - int(before["steal_jiffies"])
    deltas["steal_jiffies"] = steal_delta
    if steal_delta != 0:
        raise GateError(f"aggregate CPU steal changed by {steal_delta} jiffies")
    return {"tier": "tierB", "contended": False, "deltas": deltas}


def validate_smi(path: Path, gpu_uuid: str) -> dict[str, Any]:
    require_nonempty(path)
    with path.open(newline="", encoding="utf-8") as stream:
        try:
            rows = list(csv.DictReader(stream))
        except csv.Error as exc:
            raise GateError(f"malformed telemetry {path}: {exc}") from exc
    if not rows:
        raise GateError(f"no GPU telemetry samples in {path}")
    temperatures: list[float] = []
    pstates: set[str] = set()
    for row in rows:
        observed_uuid = (row.get("uuid") or "").strip()
        if observed_uuid != gpu_uuid:
            raise GateError(f"{path}: telemetry UUID {observed_uuid!r} != {gpu_uuid!r}")
        temperatures.append(float((row.get("temperature.gpu") or "nan").strip()))
        pstates.add((row.get("pstate") or "").strip())
    if not all(math.isfinite(value) and value < 90.0 for value in temperatures):
        raise GateError(f"{path}: invalid or >=90C GPU temperature")
    if "" in pstates:
        raise GateError(f"{path}: missing GPU pstate")
    return {"samples": len(rows), "max_temperature_c": max(temperatures), "pstates": sorted(pstates)}


def expected_fields(workload: Workload) -> dict[str, Any]:
    return {
        "harness": "f4_matrix_bench",
        "curve": workload.curve,
        "m": workload.m,
        "target_x": workload.target_x,
        "degree": workload.degree,
        "rows": workload.rows,
        "cols": workload.cols,
        "rank": workload.rank,
        "refuted": workload.refuted,
        "pinned": workload.pinned,
        "word_ops": workload.word_ops,
    }


def validate_execution(prefix: Path, workload: Workload, gpu: dict[str, str]) -> dict[str, Any]:
    suffixes = (
        ".json", ".log", ".smi.csv", ".status", ".started-at", ".finished-at",
        ".isolation-before.json", ".isolation-after.json",
    )
    paths = [prefix.parent / f"{prefix.name}{suffix}" for suffix in suffixes]
    for path in paths:
        require_nonempty(path)
    if read_status(prefix.parent / f"{prefix.name}.status") != 0:
        raise GateError(f"execution failed: {prefix}")
    report = load_json(prefix.parent / f"{prefix.name}.json")
    for field, expected in expected_fields(workload).items():
        if report.get(field) != expected:
            raise GateError(f"{prefix}: {field}={report.get(field)!r}, expected {expected!r}")
    if report.get("echelon_mode") != "cuda":
        raise GateError(f"{prefix}: not forced through CUDA")
    backend, sm_count = validate_backend(report.get("echelon_backend"), gpu["name"])
    log_path = prefix.parent / f"{prefix.name}.log"
    matches = list(VERBOSE_RE.finditer(log_path.read_text(encoding="utf-8", errors="replace")))
    if len(matches) != 1:
        raise GateError(f"{log_path}: expected one verbose timing line, found {len(matches)}")
    upload, device, download = (Fraction(value) for value in matches[0].groups()[:3])
    if min(upload, device, download) < 0:
        raise GateError(f"{log_path}: negative timing")
    isolation = validate_isolation(
        prefix.parent / f"{prefix.name}.isolation-before.json",
        prefix.parent / f"{prefix.name}.isolation-after.json",
    )
    telemetry = validate_smi(prefix.parent / f"{prefix.name}.smi.csv", gpu["uuid"])
    return {
        "prefix": prefix,
        "report": report,
        "backend": backend,
        "sm_count": sm_count,
        "upload_ms": upload,
        "device_ms": device,
        "download_ms": download,
        "complete_ms": upload + device + download,
        "isolation": isolation,
        "telemetry": telemetry,
        "artifacts": paths,
    }


def raw_prefix(session: Path, phase: str, round_index: int, tag: str, arm: str) -> Path:
    return session / "raw" / phase / f"r{round_index:02d}" / tag / arm


def gate_raw(session: Path, phase: str, expected_gpu: str) -> list[dict[str, Any]]:
    rounds = (0,) if phase == "warmup" else MEASURED_ROUNDS if phase == "measure" else None
    if rounds is None:
        raise GateError(f"unknown raw phase {phase!r}")
    gpu = validate_gpu_inventory(session, expected_gpu)
    rows: list[dict[str, Any]] = []
    for round_index in rounds:
        for workload in WORKLOADS:
            for arm in ARMS:
                observed = validate_execution(
                    raw_prefix(session, phase, round_index, workload.tag, arm), workload, gpu
                )
                rows.append({
                    "phase": phase,
                    "round": round_index,
                    "workload": workload,
                    "arm": arm,
                    **observed,
                })
    return rows


def median_fraction(values: Iterable[Fraction]) -> Fraction:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("median of empty values")
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2


def bootstrap_interval(baseline: list[Fraction], comparison: list[Fraction]) -> tuple[Fraction, Fraction]:
    if len(baseline) != 6 or len(comparison) != 6:
        raise ValueError("the frozen design requires exactly six pairs")
    if min(baseline) <= 0 or min(comparison) <= 0:
        raise ValueError("paired timing is non-positive")
    ratios = [base / other for base, other in zip(baseline, comparison)]
    distribution = [
        median_fraction(ratios[index] for index in indices)
        for indices in itertools.product(range(6), repeat=6)
    ]
    distribution.sort()
    lower_index = max(
        0,
        (len(distribution) * INTERVAL_TAIL.numerator + INTERVAL_TAIL.denominator - 1)
        // INTERVAL_TAIL.denominator - 1,
    )
    upper_probability = 1 - INTERVAL_TAIL
    upper_index = max(
        0,
        (len(distribution) * upper_probability.numerator + upper_probability.denominator - 1)
        // upper_probability.denominator - 1,
    )
    return distribution[lower_index], distribution[min(upper_index, len(distribution) - 1)]


def fraction_record(value: Fraction) -> dict[str, Any]:
    return {
        "numerator": value.numerator,
        "denominator": value.denominator,
        "decimal": format(float(value), ".17g"),
    }


def aa_interval_admissible(lower: Fraction, upper: Fraction) -> bool:
    return (
        lower <= 1 <= upper
        and lower >= Fraction(1, 1) / AA_RESOLUTION
        and upper <= AA_RESOLUTION
    )


def primary_geometry_pass(observed: Fraction, lower: Fraction,
                          aa_noise_floor: Fraction) -> bool:
    return observed >= PRIMARY_EFFECT and lower > aa_noise_floor


def kernel_rows(path: Path) -> list[dict[str, Any]]:
    require_nonempty(path)
    try:
        connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        query = """
            SELECT k.start, s.value AS name, k.gridX, k.gridY, k.gridZ,
                   k.blockX, k.blockY, k.blockZ, k.registersPerThread,
                   k.staticSharedMemory, k.dynamicSharedMemory,
                   k.localMemoryPerThread
            FROM CUPTI_ACTIVITY_KIND_KERNEL AS k
            JOIN StringIds AS s ON k.shortName = s.id
            ORDER BY k.start
        """
        rows = [dict(row) for row in connection.execute(query)]
        connection.close()
    except sqlite3.Error as exc:
        raise GateError(f"cannot read Nsys SQLite {path}: {exc}") from exc
    if not rows:
        raise GateError(f"no CUDA kernels in {path}")
    return rows


def parts_for(sm_count: int, tiles: int, blocks_per_sm: int) -> int:
    return max(1, min(32, (blocks_per_sm * sm_count + tiles - 1) // tiles))


def infer_tile_candidates(materialise_grid: int, update_grid: int, sm_count: int) -> tuple[int, ...]:
    candidates = []
    for tiles in range(max(1, 4 * materialise_grid - 3), 4 * materialise_grid + 1):
        if tiles * parts_for(sm_count, tiles, 4) == update_grid:
            candidates.append(tiles)
    if not candidates:
        raise GateError(
            f"cannot infer any word-tile count from materialise={materialise_grid}, "
            f"baseline update={update_grid}, sm_count={sm_count}"
        )
    return tuple(candidates)


def infer_tiles(materialise_grid: int, update_grid: int, sm_count: int) -> int:
    """Return the tile count only when the baseline trace determines it uniquely."""
    candidates = infer_tile_candidates(materialise_grid, update_grid, sm_count)
    if len(candidates) != 1:
        raise GateError(
            f"word tiles are ambiguous for materialise={materialise_grid}, "
            f"baseline update={update_grid}, sm_count={sm_count}: {list(candidates)}"
        )
    return candidates[0]


def validate_update_resource(row: dict[str, Any]) -> None:
    expected = {
        "blockX": 256,
        "blockY": 1,
        "blockZ": 1,
        "registersPerThread": 31,
        "staticSharedMemory": 16384,
        "dynamicSharedMemory": 0,
        "localMemoryPerThread": 0,
    }
    for field, value in expected.items():
        if row[field] != value:
            raise GateError(f"f4e_update {field}={row[field]}, expected {value}")


def mechanism_gate(baseline_path: Path, candidate_path: Path, sm_count: int) -> dict[str, Any]:
    baseline, candidate = kernel_rows(baseline_path), kernel_rows(candidate_path)
    expected_total = EXPECTED_UPDATE_LAUNCHES * 4 + 1
    if len(baseline) != expected_total or len(candidate) != expected_total:
        raise GateError(
            f"expected {expected_total} kernels per trace, got {len(baseline)} and {len(candidate)}"
        )
    expected_names = ["f4e_gather", "f4e_panel_block", "f4e_materialise", "f4e_update"]
    transitions: dict[str, int] = {}
    changed = 0
    for launch in range(EXPECTED_UPDATE_LAUNCHES):
        offset = launch * 4
        bgroup, cgroup = baseline[offset:offset + 4], candidate[offset:offset + 4]
        if [row["name"] for row in bgroup] != expected_names:
            raise GateError(f"baseline kernel order differs at update launch {launch}")
        if [row["name"] for row in cgroup] != expected_names:
            raise GateError(f"candidate kernel order differs at update launch {launch}")
        for index in range(3):
            fields = (
                "name", "gridX", "gridY", "gridZ", "blockX", "blockY", "blockZ",
                "registersPerThread", "staticSharedMemory", "dynamicSharedMemory",
                "localMemoryPerThread",
            )
            if tuple(bgroup[index][field] for field in fields) != tuple(
                cgroup[index][field] for field in fields
            ):
                raise GateError(f"non-update kernel geometry/resource differs at launch {launch}")
        bupdate, cupdate = bgroup[3], cgroup[3]
        validate_update_resource(bupdate)
        validate_update_resource(cupdate)
        remaining_words = EXPECTED_UPDATE_LAUNCHES - launch
        expected_materialise = (remaining_words + 127) // 128
        tiles = (remaining_words + 31) // 32
        expected_baseline = tiles * parts_for(sm_count, tiles, 4)
        expected_candidate = tiles * parts_for(sm_count, tiles, 6)
        if bgroup[2]["gridX"] != expected_materialise:
            raise GateError(
                f"materialise grid mismatch at launch {launch}: "
                f"{bgroup[2]['gridX']} != {expected_materialise}"
            )
        if bupdate["gridX"] != expected_baseline or cupdate["gridX"] != expected_candidate:
            raise GateError(
                f"update grid mismatch at launch {launch}: tiles={tiles}, "
                f"baseline={bupdate['gridX']}/{expected_baseline}, "
                f"candidate={cupdate['gridX']}/{expected_candidate}"
            )
        if cupdate["gridX"] < bupdate["gridX"]:
            raise GateError(f"candidate update grid shrank at launch {launch}")
        if cupdate["gridX"] > bupdate["gridX"]:
            changed += 1
        key = f"{tiles}:{bupdate['gridX']}->{cupdate['gridX']}"
        transitions[key] = transitions.get(key, 0) + 1
    if baseline[-1]["name"] != "f4e_low" or candidate[-1]["name"] != "f4e_low":
        raise GateError("the final f4e_low launch is missing")
    fields = (
        "name", "gridX", "gridY", "gridZ", "blockX", "blockY", "blockZ",
        "registersPerThread", "staticSharedMemory", "dynamicSharedMemory",
        "localMemoryPerThread",
    )
    if tuple(baseline[-1][field] for field in fields) != tuple(candidate[-1][field] for field in fields):
        raise GateError("final f4e_low geometry/resource differs")
    if changed == 0:
        raise GateError("the candidate did not change any update launch grid")
    return {
        "status": "passed",
        "sm_count": sm_count,
        "kernel_launches_per_arm": expected_total,
        "update_launches_per_arm": EXPECTED_UPDATE_LAUNCHES,
        "update_sequence_verified": True,
        "non_update_geometry_unchanged": True,
        "changed_update_launches": changed,
        "unchanged_update_launches": EXPECTED_UPDATE_LAUNCHES - changed,
        "transitions": dict(sorted(transitions.items())),
        "resources": {
            "threads_per_block": 256,
            "registers_per_thread": 31,
            "static_shared_bytes": 16384,
            "dynamic_shared_bytes": 0,
            "local_bytes_per_thread": 0,
        },
    }


def gate_nsys(session: Path, expected_gpu: str) -> dict[str, Any]:
    gpu = validate_gpu_inventory(session, expected_gpu)
    observations: dict[str, dict[str, Any]] = {}
    sm_counts: set[int] = set()
    for arm in PROFILE_ARMS:
        prefix = session / "profiles" / "nsys" / arm / "k0n13m2d6"
        observed = validate_execution(prefix, BY_TAG["k0n13m2d6"], gpu)
        observations[arm] = observed
        sm_counts.add(observed["sm_count"])
        for suffix in (".nsys-rep", ".sqlite", ".stats.csv", ".stats.status"):
            require_nonempty(prefix.parent / f"{prefix.name}{suffix}")
        if read_status(prefix.parent / f"{prefix.name}.stats.status") != 0:
            raise GateError(f"Nsys stats failed: {prefix}")
    if len(sm_counts) != 1:
        raise GateError(f"Nsys arms observed different SM counts: {sm_counts}")
    return mechanism_gate(
        session / "profiles" / "nsys" / "baseline" / "k0n13m2d6.sqlite",
        session / "profiles" / "nsys" / "candidate" / "k0n13m2d6.sqlite",
        sm_counts.pop(),
    )


def keyed_rows(rows: Iterable[dict[str, Any]]) -> dict[tuple[str, int, str], dict[str, Any]]:
    out: dict[tuple[str, int, str], dict[str, Any]] = {}
    for row in rows:
        key = (row["workload"].tag, row["round"], row["arm"])
        if key in out:
            raise GateError(f"duplicate execution cell {key}")
        out[key] = row
    return out


def row_artifacts(row: dict[str, Any], session: Path) -> list[dict[str, Any]]:
    return sorted(
        (file_record(path, session, "raw") for path in row["artifacts"]),
        key=lambda item: item["path"],
    )


def row_record(row: dict[str, Any], session: Path, timing_admissible: bool) -> dict[str, Any]:
    workload: Workload = row["workload"]
    warmup = row["phase"] == "warmup"
    replicate = 0 if warmup else row["round"] - 1
    prefix: Path = row["prefix"]
    started = (prefix.parent / f"{prefix.name}.started-at").read_text(encoding="utf-8").strip()
    finished = (prefix.parent / f"{prefix.name}.finished-at").read_text(encoding="utf-8").strip()
    report = row["report"]
    return {
        "run_id": f"{session.name}-{row['phase']}-r{row['round']:02d}-{workload.tag}-{row['arm']}",
        "arm": row["arm"],
        "instance_id": workload.tag,
        "seed": 0,
        "replicate": replicate,
        "warmup": warmup,
        "status": "succeeded",
        "outcome_class": "completed",
        "attempts": 1,
        "resumed": 0,
        "checkpoint": None,
        "measurements": {
            "counted": {
                "word_ops": str(report["word_ops"]),
                "rank": report["rank"],
                "refuted": 1 if report["refuted"] else 0,
                "pinned": report["pinned"],
                "rows": report["rows"],
                "cols": report["cols"],
            },
            "wall_seconds": float(row["complete_ms"] / 1000),
            "wall_valid": not warmup and timing_admissible,
            "cpu_user_seconds": None,
            "cpu_sys_seconds": None,
            "max_rss_bytes": None,
            "counters": {
                "upload_ms": float(row["upload_ms"]),
                "device_ms": float(row["device_ms"]),
                "download_ms": float(row["download_ms"]),
                "complete_ms": float(row["complete_ms"]),
                "gpu_telemetry_samples": row["telemetry"]["samples"],
                "gpu_max_temperature_c": row["telemetry"]["max_temperature_c"],
            },
        },
        "isolation": {"tier": "tierB", "contended": False, "blockers": []},
        "verification": {
            "status": "verified",
            "verifier": "exact matrix shape/rank/refuted/pinned/word_ops plus forced CUDA backend",
        },
        "exclusion": {"excluded": False, "rule": None},
        "artifacts": row_artifacts(row, session),
        "started_at": started,
        "finished_at": finished,
        "worker": None,
        "backend_ref": None,
    }


def write_export(
    session: Path,
    protocol_sha256: str,
    hashes: dict[str, str],
    rows: list[dict[str, Any]],
    analysis_path: Path,
) -> dict[str, Any]:
    host_path = session / "host.json"
    host = load_json(host_path)
    gpu = validate_gpu_inventory(session, EXPECTED_GPU)
    analysis_script = (session / ANALYZER_RELATIVE).resolve()
    require_nonempty(analysis_script)
    # Hash every artifact that is immutable at export time.  Four files are
    # written by the surrounding shell after/while this command returns and
    # are instead bound by the authenticated transport archive manifest.
    mutable_after_export = {
        "analysis-gate.json",
        "completed-at.txt",
        "export.json",
        "runner-exit.status",
    }
    files = [
        file_record(path, session, "other")
        for path in sorted(session.rglob("*"))
        if path.is_file() and str(path.relative_to(session)) not in mutable_after_export
    ]
    return {
        "schema": "experiment.export/v1",
        "export_id": f"{session.name}-export",
        "created": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "protocol": {
            "path": PROTOCOL_RELATIVE,
            "sha256": protocol_sha256,
            "protocol_id": PROTOCOL_ID,
            "version": PROTOCOL_VERSION,
        },
        "producer": {
            "runtime": "runpod-http-batch",
            "model": None,
            "session": session.name,
            "role": "executor",
        },
        "source": {"repo": "cryptanalysis", "commit": CANDIDATE_COMMIT, "dirty": False},
        "backend": "runpod",
        "host": {
            "path": "host.json",
            "sha256": sha256_file(host_path),
            "class_id": host.get("machine_id"),
            "summary": {
                "cpu_model": host.get("cpu_model"),
                "logical_cpus": host.get("logical_cpus"),
                "memory_bytes": host.get("memory_bytes"),
                "kernel": host.get("kernel"),
                "hypervisor": "Runpod Secure Cloud",
                "isolation_tier_max": "tierB",
                "gpu": gpu["name"],
                "instance_type": host.get("machine_id"),
                "spot": False,
            },
        },
        "arms": [
            {"id": arm, "role": ARM_ROLES[arm], "binary_sha256": hashes[arm], "commit": CANDIDATE_COMMIT}
            for arm in ARMS
        ],
        "runs": rows,
        "flow": {
            "planned": len(rows),
            "attempted": len(rows),
            "completed": len(rows),
            "not_completed": 0,
            "interrupted": 0,
            "resumed": 0,
            "excluded": [],
        },
        "files": files,
        "analysis": {
            "script": file_record(analysis_script, session, "analysis"),
            "blinded": False,
            "blinding_key_sha256": None,
            "outputs": [file_record(analysis_path, session, "analysis")],
            "unmasked_at": None,
        },
        "notes": [
            {
                "kind": "observation",
                "text": "wall_seconds is the charged upload+device+download F4 stage, not process lifetime; profiled durations are excluded.",
                "by": "frozen analyzer",
            },
            {
                "kind": "observation",
                "text": "tierB denotes the frozen per-process numeric PSI/cgroup/steal/temperature/no-foreign-process gates; it is not a claim about exclusive physical-host or L2-cache topology.",
                "by": "frozen analyzer",
            }
        ],
        "reviews_dir": "reviews",
    }


def calculate(session: Path, expected_gpu: str, protocol_sha256: str) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, str]]:
    if SHA256_RE.fullmatch(protocol_sha256) is None:
        raise GateError("protocol SHA-256 is malformed")
    validate_gpu_inventory(session, expected_gpu)
    identities = validate_source_identities(session)
    validate_remote_build_preflight(
        session, identities, protocol_sha256, require_final_runtime=True,
    )
    hashes = parse_binary_hashes(session)
    warmups = gate_raw(session, "warmup", expected_gpu)
    measured = gate_raw(session, "measure", expected_gpu)
    mechanism = gate_nsys(session, expected_gpu)
    keyed = keyed_rows(measured)

    cells: dict[str, Any] = {}
    gates: list[dict[str, Any]] = []
    aa_gates: list[dict[str, Any]] = []
    for workload in WORKLOADS:
        metrics: dict[str, Any] = {}
        for metric in ("device_ms", "complete_ms"):
            baseline = [keyed[(workload.tag, round_index, "baseline")][metric]
                        for round_index in MEASURED_ROUNDS]
            baseline_aa = [keyed[(workload.tag, round_index, "baseline-aa")][metric]
                           for round_index in MEASURED_ROUNDS]
            candidate = [keyed[(workload.tag, round_index, "candidate")][metric]
                         for round_index in MEASURED_ROUNDS]
            pair_ratios = [base / cand for base, cand in zip(baseline, candidate)]
            observed = median_fraction(pair_ratios)
            lower, upper = bootstrap_interval(baseline, candidate)
            aa_ratios = [base / aa for base, aa in zip(baseline, baseline_aa)]
            aa_observed = median_fraction(aa_ratios)
            aa_lower, aa_upper = bootstrap_interval(baseline, baseline_aa)
            aa_passed = aa_interval_admissible(aa_lower, aa_upper)
            noise_floor = max(aa_upper, Fraction(1, 1) / aa_lower)
            metrics[metric] = {
                "baseline_ms": [format(float(value), ".17g") for value in baseline],
                "baseline_aa_ms": [format(float(value), ".17g") for value in baseline_aa],
                "candidate_ms": [format(float(value), ".17g") for value in candidate],
                "paired_baseline_over_candidate": [fraction_record(value) for value in pair_ratios],
                "median_pair_speedup": fraction_record(observed),
                "simultaneous_two_sided_interval": {
                    "lower": fraction_record(lower),
                    "upper": fraction_record(upper),
                },
                "paired_baseline_over_baseline_aa": [fraction_record(value) for value in aa_ratios],
                "aa_median_ratio": fraction_record(aa_observed),
                "aa_simultaneous_two_sided_interval": {
                    "lower": fraction_record(aa_lower),
                    "upper": fraction_record(aa_upper),
                },
                "aa_symmetric_noise_floor": fraction_record(noise_floor),
                "bootstrap_resamples": 6 ** 6,
                "two_sided_tail_probability": fraction_record(INTERVAL_TAIL),
            }
            aa_gates.append({
                "workload": workload.tag,
                "metric": metric,
                "kind": "same_session_aa_interval_admissible",
                "resolution_ceiling": fraction_record(AA_RESOLUTION),
                "median": fraction_record(aa_observed),
                "lower": fraction_record(aa_lower),
                "upper": fraction_record(aa_upper),
                "noise_floor": fraction_record(noise_floor),
                "passed": aa_passed,
            })
            decisive = (workload.role == "primary" and metric == "device_ms") or metric == "complete_ms" or workload.role == "holdout"
            if decisive:
                threshold = PRIMARY_EFFECT if workload.role == "primary" and metric == "device_ms" else NONREGRESSION
                passed = primary_geometry_pass(observed, lower, noise_floor) if threshold == PRIMARY_EFFECT else (
                    observed >= threshold and lower >= threshold
                )
                gates.append({
                    "workload": workload.tag,
                    "metric": metric,
                    "kind": "primary_improvement" if threshold == PRIMARY_EFFECT else "nonregression",
                    "threshold": fraction_record(threshold),
                    "median": fraction_record(observed),
                    "lower": fraction_record(lower),
                    "upper": fraction_record(upper),
                    "aa_noise_floor": fraction_record(noise_floor),
                    "passed": passed,
                })
        cells[workload.tag] = {"role": workload.role, "metrics": metrics}
    if len(gates) != AB_INTERVALS or len(aa_gates) != AA_INTERVALS:
        raise GateError(
            f"internal interval family has {len(gates)} A/B and {len(aa_gates)} A/A cells, "
            f"expected {AB_INTERVALS} and {AA_INTERVALS}"
        )
    aa_admissible = all(gate["passed"] for gate in aa_gates)
    provisional = (
        "invalid_measurement" if not aa_admissible else
        "geometry_supported" if all(gate["passed"] for gate in gates) else
        "geometry_not_supported"
    )
    analysis = {
        "schema": "gpu-f4-update-grid-ab-analysis/v2",
        "protocol_id": PROTOCOL_ID,
        "protocol_version": PROTOCOL_VERSION,
        "protocol_sha256": protocol_sha256,
        "session": session.name,
        "terminal": False,
        "classification_status": "provisional_mechanical",
        "timing_classification_provisional": provisional,
        "terminal_adjudicator": "finalize_gpu_geometry_ab_v11.py",
        "correctness_gate": "passed",
        "source_identity_gate": "passed",
        "numeric_isolation_gate": "passed",
        "same_session_aa_gate": "passed" if aa_admissible else "failed",
        "mechanism_gate": mechanism,
        "multiplicity": {
            "family_intervals": FAMILY_INTERVALS,
            "ab_intervals": AB_INTERVALS,
            "aa_intervals": AA_INTERVALS,
            "family_alpha": "0.05",
            "correction": "Bonferroni",
            "sides": 2,
            "per_tail_probability": fraction_record(INTERVAL_TAIL),
        },
        "decision_gates": gates,
        "aa_control_gates": aa_gates,
        "cells": cells,
        "profiled_timings_in_decision": False,
        "hardware_counters": "not collected; NCU is outside this protocol",
    }
    rows = [row_record(row, session, aa_admissible) for row in [*warmups, *measured]]
    return analysis, rows, hashes


def analyze(session: Path, expected_gpu: str, protocol_sha256: str) -> dict[str, Any]:
    analysis, rows, hashes = calculate(session, expected_gpu, protocol_sha256)
    rows_path = session / "rows.jsonl"
    analysis_path = session / "analysis.json"
    exclusive_jsonl(rows_path, rows)
    exclusive_json(analysis_path, analysis)
    export = write_export(session, protocol_sha256, hashes, rows, analysis_path)
    exclusive_json(session / "export.json", export)
    return analysis


def command_plan(args: argparse.Namespace) -> int:
    if args.tsv:
        for workload in WORKLOADS:
            print("\t".join((workload.role, workload.tag, workload.cell, str(workload.degree))))
    else:
        print(json.dumps([workload.__dict__ for workload in WORKLOADS], sort_keys=True, indent=2))
    return 0


def command_snapshot(args: argparse.Namespace) -> int:
    exclusive_json(args.out, capture_isolation())
    return 0


def command_gate(args: argparse.Namespace) -> int:
    session = args.session.resolve()
    identities = validate_source_identities(session)
    validate_remote_build_preflight(
        session, identities, require_final_runtime=args.phase == "nsys",
    )
    parse_binary_hashes(session)
    if args.phase in ("warmup", "measure"):
        count = len(gate_raw(session, args.phase, args.expected_gpu))
        extra: dict[str, Any] = {}
    else:
        extra = gate_nsys(session, args.expected_gpu)
        count = 2
    print(json.dumps({"gate": "passed", "phase": args.phase, "executions": count, **extra}, sort_keys=True))
    return 0


def command_analyze(args: argparse.Namespace) -> int:
    analysis = analyze(args.session.resolve(), args.expected_gpu, args.protocol_sha256)
    print(json.dumps({
        "analysis": "written",
        "export": "written",
        "session": analysis["session"],
        "terminal": False,
        "classification_status": analysis["classification_status"],
        "timing_classification_provisional": analysis["timing_classification_provisional"],
    }, sort_keys=True))
    return 0


def command_verify(args: argparse.Namespace) -> int:
    """Re-derive timing, correctness, isolation, and Nsys results read-only."""
    session = args.session.resolve()
    expected_analysis, expected_rows, _hashes = calculate(
        session, args.expected_gpu, args.protocol_sha256
    )
    observed_analysis = load_json(session / "analysis.json")
    rows_path = session / "rows.jsonl"
    require_nonempty(rows_path)
    try:
        observed_rows = [json.loads(line) for line in rows_path.read_text(encoding="utf-8").splitlines()]
    except (OSError, json.JSONDecodeError) as exc:
        raise GateError(f"invalid rows.jsonl: {exc}") from exc
    if observed_analysis != expected_analysis:
        raise GateError("analysis.json differs from read-only recomputation over raw/Nsys evidence")
    if observed_rows != expected_rows:
        raise GateError("rows.jsonl differs from read-only recomputation over raw evidence")
    print(json.dumps({
        "classification_status": "provisional_mechanical",
        "read_only_recomputation": "passed",
        "session": session.name,
        "timing_classification_provisional": expected_analysis["timing_classification_provisional"],
    }, sort_keys=True))
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    plan = sub.add_parser("plan", help="print the immutable five-cell plan")
    plan.add_argument("--tsv", action="store_true")
    plan.set_defaults(func=command_plan)
    snapshot = sub.add_parser("snapshot-isolation", help="write one isolation snapshot")
    snapshot.add_argument("--out", type=Path, required=True)
    snapshot.set_defaults(func=command_snapshot)
    gate = sub.add_parser("gate", help="check one completed phase")
    gate.add_argument("--session", type=Path, required=True)
    gate.add_argument("--phase", choices=("warmup", "measure", "nsys"), required=True)
    gate.add_argument("--expected-gpu", default=EXPECTED_GPU)
    gate.set_defaults(func=command_gate)
    summary = sub.add_parser("analyze", help="gate all artifacts and write analysis/export")
    summary.add_argument("--session", type=Path, required=True)
    summary.add_argument("--expected-gpu", default=EXPECTED_GPU)
    summary.add_argument("--protocol-sha256", required=True)
    summary.set_defaults(func=command_analyze)
    verify = sub.add_parser("verify", help="read-only recomputation of rows and provisional analysis")
    verify.add_argument("--session", type=Path, required=True)
    verify.add_argument("--expected-gpu", default=EXPECTED_GPU)
    verify.add_argument("--protocol-sha256", required=True)
    verify.set_defaults(func=command_verify)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        return args.func(args)
    except (GateError, OSError, ValueError, KeyError, TypeError) as exc:
        print(f"GPU geometry A/B analysis refused: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
