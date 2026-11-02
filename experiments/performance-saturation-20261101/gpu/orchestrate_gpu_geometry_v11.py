#!/usr/bin/env python3
"""Run the mandatory v11 clean-build gate, one controller, and finalizer.

The extracted-closure build receipt is created before any provider call.  A
failed or interrupted preflight suppresses allocation and still invokes the
terminal finalizer.  There is no retry path for either preflight or controller.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable


PROTOCOL_ID = "gpu-f4-update-grid-ab-rtx5090-http-v11-20261101"
SOURCE_REF = "refs/heads/codex/runpod-http-gpu-geometry-v11-20261101"
RUN_ID_RE = re.compile(r"^gpu-geometry-http-rtx5090-v11-[A-Za-z0-9._-]{1,80}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
STUDY = Path("experiments/performance-saturation-20261101/gpu")
PREFLIGHT_SCHEMA = "gpu-geometry-build-preflight/v1"
ARCHIVE_ROOTS = ["suite", "bindings/rust", "include", "src", "cuda", "challenges"]
ARCHIVE_SHA256 = "554dcaacb7ff1fcfb27f4b49bb60b2d03ac9201978091c5e516fff356d1f9b8d"
ARCHIVE_BYTES = 19_435_520
ARCHIVE_FILES = 1_253
F4_PATH = "suite/src/cryptanalysis/f4_gpu.rs"
BUILD_COMMAND = ["cargo", "build", "--release", "--locked", "--example", "f4_matrix_bench"]
PREFLIGHT_SOURCE = {
    "baseline_commit": "7c712913b7e912494e87c35e854cfd0129bad89c",
    "candidate_commit": "59b6d7e17100d4d16db5d25c2762a5d5cf45ef4f",
    "candidate_tree": "af0ac7e239c0acaa063c1a1441d6fb374ebbf30b",
    "baseline_f4_sha256": "da8c53c757cac0dfd81d1f75bfc5845610b645338215e52710efa11d57783944",
    "candidate_f4_sha256": "77832323d4d5a2b6b49fa2ca26fe40de1a80c0a8e17a9bb1949081a30fa84953",
}
BUILD_CONTRACT = {
    "clean_extracted_closure": True,
    "isolated_source_trees": True,
    "isolated_target_dirs": True,
    "cargo_incremental": "0",
    "network_only_during_bootstrap_and_fetch": True,
    "offline_builds": True,
    "exact_environment_key_set": True,
}
RUSTUP_URL = (
    "https://static.rust-lang.org/rustup/archive/1.29.2/"
    "x86_64-unknown-linux-gnu/rustup-init"
)
RUSTUP_SHA256 = "5be191e8c70a5007074254cb74d78dbfdd25cd5a61c27de7b8e5410122ec24f4"
RUSTC_SHA256 = "5eadaaf4fe086d76547b17dc3c1ba880d0082b93f7d8bc65612770da8e79fe8e"
CARGO_SHA256 = "e60b4010303c19a131c058e3f054b4b3311433c4b2ee94ba8e09e165ff2a3b3b"
CC_SHA256 = "a23ecab8ff08f09ad8c80602c2c5df7f49e09c25905cb8975902e101bf72635f"
RUST_TOOLCHAIN = "1.91.1-x86_64-unknown-linux-gnu"
AR_SHA256 = "f8fe09d485b40b1d47c534c96f5cbaaa9148e247aa0494c087104421f48ac5eb"
RANLIB_SHA256 = "4610e832470b987c8c9d82d78c1c16e5e2bc9b8c64db455fad0cf63d420ec86e"
LINKER_SHA256 = "d2766988b6a1b1d1518cdc09242e726d1f24e151e16410ada3092b11ffd9081b"
COLLECT2_SHA256 = "ea31a4cebd9df1b6428c463428d461ccecfe66c897936409d5b2cde0b3af9e27"
NETWORK_ALLOWLIST = [
    "ALL_PROXY", "HTTPS_PROXY", "HTTP_PROXY", "NO_PROXY", "SSL_CERT_FILE", "CURL_CA_BUNDLE",
]
FORBIDDEN_BUILD_PATTERNS = [
    "RUSTFLAGS", "CARGO_ENCODED_RUSTFLAGS", "CARGO_PROFILE_*", "CARGO_TARGET_DIR",
    "RUSTC_WRAPPER", "RUSTC_WORKSPACE_WRAPPER", "CFLAGS", "CXXFLAGS", "CPPFLAGS",
    "LDFLAGS", "LD_PRELOAD", "AR", "CC", "RANLIB", "RAYON_NUM_THREADS", "F4_*",
]
PYTHON = "/usr/bin/python3"
ISOLATED_PYTHON = [PYTHON, "-I", "-S", "-B"]
CANONICAL_PYTHON = [PYTHON, "-I", "-B"]
LOCAL_FIXED_ENV = {
    "PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C", "TZ": "UTC",
}
CONTROLLER_SECRET_ALLOWLIST = ("RUNPOD_API_KEY",)
CANONICAL_SCHEMAS = {
    "/workspace/crypto-autoresearcher/schemas/experiment-protocol.v1.json":
        "a9b948f2be323f862b98301eb7a5aa147ecc29db35041737f0aa3dfd03ad2443",
    "/workspace/crypto-autoresearcher/schemas/experiment-export.v1.json":
        "108f0ae9c1be3ed141bca3c22216eba049f2c76677f11013109a4740f19bd757",
}


def exact_phase_environments(root: Path, inherited: dict[str, str]) -> dict[str, dict[str, str]]:
    """Construct caller-owned, exact environments for every local subprocess phase."""
    root.mkdir(mode=0o700, parents=True, exist_ok=False)
    result: dict[str, dict[str, str]] = {}
    for phase in ("orchestrator", "canonical", "preflight", "controller", "finalizer"):
        phase_root = root / phase
        home, temporary = phase_root / "home", phase_root / "tmp"
        home.mkdir(mode=0o700, parents=True)
        temporary.mkdir(mode=0o700)
        environment = {
            **LOCAL_FIXED_ENV, "HOME": str(home), "TMPDIR": str(temporary),
        }
        if phase in {"preflight", "controller"}:
            environment.update({
                key: inherited[key] for key in NETWORK_ALLOWLIST if key in inherited
            })
        if phase == "controller":
            environment.update({
                key: inherited[key] for key in CONTROLLER_SECRET_ALLOWLIST if key in inherited
            })
        result[phase] = environment
    return result


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode("utf-8")


def protocol_hash(value: dict[str, Any]) -> str:
    body = {key: item for key, item in value.items() if key != "freeze"}
    return hashlib.sha256(canonical(body)).hexdigest()


def strict_json(value: str | bytes) -> Any:
    return json.loads(
        value, parse_constant=lambda token: (_ for _ in ()).throw(
            ValueError(f"non-finite JSON token {token}")),
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_utc(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
    except ValueError:
        return None
    return parsed.astimezone(timezone.utc) if parsed.tzinfo is not None else None


def load_frozen_protocol(path: Path, expected_sha: str) -> dict[str, Any]:
    value = strict_json(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("protocol is not an object")
    freeze = value.get("freeze") if isinstance(value.get("freeze"), dict) else {}
    if (
        value.get("protocol_id") != PROTOCOL_ID or value.get("version") != 11
        or freeze.get("status") != "frozen" or freeze.get("protocol_sha256") != expected_sha
        or protocol_hash(value) != expected_sha or freeze.get("filed_before_affected_data") is not True
    ):
        raise ValueError("protocol identity/freeze/hash is not the registered prospective v11")
    return value


def campaign_paths(run_id: str) -> dict[str, Path]:
    return {
        "preflight": STUDY / "preflight-receipts" / f"{run_id}.json",
        "session": STUDY / "runs-http" / run_id,
        "receipt": STUDY / "http-receipts" / f"{run_id}.json",
        "archive": STUDY / "http-receipts" / f"{run_id}.result.tar.gz",
        "remote": STUDY / "http-receipts" / f"{run_id}.remote",
        "verdict": STUDY / "final-verdicts" / f"{run_id}.json",
    }


def preflight_command(repo: Path, protocol_sha: str, run_id: str) -> list[str]:
    paths = campaign_paths(run_id)
    return [
        *ISOLATED_PYTHON, str(STUDY / "preflight_gpu_geometry_v11.py"), "run",
        "--repo", str(repo), "--run-id", run_id,
        "--protocol-sha256", protocol_sha, "--out", str(paths["preflight"]),
    ]


def finalizer_command(protocol: Path, protocol_sha: str, protocol_tool: Path,
                      run_id: str) -> list[str]:
    paths = campaign_paths(run_id)
    return [
        *ISOLATED_PYTHON, str(STUDY / "finalize_gpu_geometry_ab_v11.py"),
        "--protocol", str(protocol), "--protocol-sha256", protocol_sha,
        "--protocol-tool", str(protocol_tool),
        "--preflight-receipt", str(paths["preflight"]),
        "--receipt", str(paths["receipt"]), "--archive", str(paths["archive"]),
        "--remote-metadata", str(paths["remote"]), "--session", str(paths["session"]),
        "--out", str(paths["verdict"]),
    ]


def controller_command(protocol_sha: str, run_id: str, value: dict[str, Any],
                       preflight_sha: str) -> list[str]:
    tooling = value.get("extensions", {}).get("tooling_source", {})
    if tooling.get("public_ref") != SOURCE_REF:
        raise ValueError("protocol tooling ref is not the registered v11 ref")
    source_commit = tooling.get("commit")
    if not isinstance(source_commit, str) or re.fullmatch(r"[0-9a-f]{40}", source_commit) is None:
        raise ValueError("protocol tooling commit is malformed")
    if SHA256_RE.fullmatch(preflight_sha) is None:
        raise ValueError("preflight receipt SHA-256 is malformed")
    paths = campaign_paths(run_id)
    command = (
        "GPU_STUDY_SECURE=1 /usr/bin/bash --noprofile --norc "
        "experiments/performance-saturation-20261101/gpu/run_gpu_geometry_ab_v11.sh "
        f"'experiments/performance-saturation-20261101/gpu/runs-http' '{run_id}' "
        f"'{protocol_sha}' '{preflight_sha}'"
    )
    return [
        *ISOLATED_PYTHON, "cloud/runpod_http_batch.py", "misagi-f4-geometry-v11",
        "--source-ref", SOURCE_REF, "--source-commit", source_commit,
        "--cloud", "SECURE", "--gpu", "NVIDIA GeForce RTX 5090", "--gpu-count", "1",
        "--min-vcpu", "16", "--min-ram", "62", "--image",
        "runpod/base:1.0.2-ubuntu2404@sha256:e93bf61149910d35407fc865078ceb9b2887e986befd2b7c0eee322abe47ac59",
        "--disk", "100", "--max-price", "1.19", "--max-hours", "3", "--wait", "900",
        "--timeout", "9000", "--reconcile-seconds", "60", "--max-result-mib", "4096",
        "--minimal-bootstrap",
        "--receipt", str(paths["receipt"]), "--archive", str(paths["archive"]),
        "--out", str(paths["session"]), "--", command,
    ]


def commands(repo: Path, protocol: Path, protocol_sha: str, protocol_tool: Path,
             run_id: str, value: dict[str, Any], preflight_sha: str
             ) -> tuple[list[str], list[str], list[str]]:
    return (
        preflight_command(repo, protocol_sha, run_id),
        controller_command(protocol_sha, run_id, value, preflight_sha),
        finalizer_command(protocol, protocol_sha, protocol_tool, run_id),
    )


def substitute_argv(template: list[Any], run_id: str, protocol_sha: str,
                    preflight_sha: str = "<preflight_receipt_sha256>") -> list[str]:
    if not all(isinstance(item, str) for item in template):
        raise ValueError("frozen argv template contains a non-string token")
    return [
        item.replace("<run_id>", run_id)
        .replace("<frozen_protocol_sha256>", protocol_sha)
        .replace("<preflight_receipt_sha256>", preflight_sha)
        for item in template
    ]


def verify_argv_templates(value: dict[str, Any], preflight: list[str], controller: list[str],
                          finalizer: list[str], run_id: str, protocol_sha: str,
                          preflight_sha: str) -> None:
    extensions = value.get("extensions") if isinstance(value.get("extensions"), dict) else {}
    launch = extensions.get("launch") if isinstance(extensions.get("launch"), dict) else {}
    finalization = extensions.get("finalization") if isinstance(extensions.get("finalization"), dict) else {}
    expected_preflight = substitute_argv(launch.get("preflight_argv_template", []), run_id, protocol_sha)
    expected_controller = substitute_argv(
        launch.get("controller_argv_template", []), run_id, protocol_sha, preflight_sha
    )
    expected_finalizer = substitute_argv(
        finalization.get("finalizer_argv_template", []), run_id, protocol_sha, preflight_sha
    )
    if preflight != expected_preflight:
        raise ValueError("constructed preflight argv differs from the frozen exact template")
    if controller != expected_controller:
        raise ValueError("constructed controller argv differs from the frozen exact template")
    if finalizer != expected_finalizer:
        raise ValueError("constructed finalizer argv differs from the frozen exact template")


def verify_tool_hashes(repo: Path, value: dict[str, Any], protocol_tool: Path) -> None:
    extensions = value.get("extensions") if isinstance(value.get("extensions"), dict) else {}
    tooling = extensions.get("tooling_source") if isinstance(extensions.get("tooling_source"), dict) else {}
    files = tooling.get("files") if isinstance(tooling.get("files"), dict) else {}
    required = extensions.get("finalization", {}).get("preflight_files", [])
    if not isinstance(required, list) or not required or set(required) - set(files):
        raise ValueError("frozen preflight tooling file registry is incomplete")
    for relative in required:
        path = repo / relative
        if not path.is_file() or sha256_file(path) != files[relative]:
            raise ValueError(f"preflight tooling hash mismatch: {relative}")
    finalization = extensions.get("finalization", {})
    canonical_tool = finalization.get("canonical_protocol_tool", {})
    if (protocol_tool.resolve() != Path(canonical_tool.get("path", "")).resolve()
            or not protocol_tool.is_file()
            or sha256_file(protocol_tool) != canonical_tool.get("sha256")):
        raise ValueError("canonical protocol tool path/hash mismatch")
    if finalization.get("canonical_protocol_schemas") != CANONICAL_SCHEMAS:
        raise ValueError("canonical protocol schema registry differs from the frozen identities")
    for raw_path, expected in CANONICAL_SCHEMAS.items():
        path = Path(raw_path)
        if not path.is_file() or sha256_file(path) != expected:
            raise ValueError(f"canonical protocol schema path/hash mismatch: {raw_path}")
    analysis = value.get("analysis_plan", {}).get("script", {})
    analyzer_path = repo / STUDY / str(analysis.get("path", ""))
    if not analyzer_path.is_file() or sha256_file(analyzer_path) != analysis.get("sha256"):
        raise ValueError("frozen remote analyzer path/hash mismatch")
    for name, expected_name in (
        ("script", "finalize_gpu_geometry_ab_v11.py"),
        ("orchestrator", "orchestrate_gpu_geometry_v11.py"),
        ("build_preflight", "preflight_gpu_geometry_v11.py"),
    ):
        spec = finalization.get(name, {})
        path = repo / STUDY / expected_name
        if spec.get("path") != expected_name or not path.is_file() or sha256_file(path) != spec.get("sha256"):
            raise ValueError(f"frozen {name} path/hash mismatch")


def git_text(repo: Path, *arguments: str, environment: dict[str, str]) -> str:
    result = subprocess.run(["git", *arguments], cwd=repo, capture_output=True,
                            text=True, timeout=120, check=False, env=environment)
    if result.returncode:
        raise ValueError(f"git {' '.join(arguments[:2])} failed")
    return result.stdout.strip()


def verify_freeze_chain(repo: Path, protocol: Path, value: dict[str, Any],
                        environment: dict[str, str]) -> None:
    relative = protocol.resolve().relative_to(repo).as_posix()
    freeze = value.get("freeze") if isinstance(value.get("freeze"), dict) else {}
    registration = freeze.get("commit")
    if not isinstance(registration, str) or re.fullmatch(r"[0-9a-f]{40}", registration) is None:
        raise ValueError("freeze.commit is not a full registration commit")
    draft_result = subprocess.run(["git", "show", f"{registration}:{relative}"], cwd=repo,
                                  capture_output=True, timeout=120, check=False,
                                  env=environment)
    if draft_result.returncode:
        raise ValueError("registered draft is unavailable")
    draft = strict_json(draft_result.stdout)
    if not isinstance(draft, dict) or draft.get("freeze", {}).get("status") != "draft" or protocol_hash(draft) != protocol_hash(value):
        raise ValueError("registration commit does not contain the matching draft")
    if git_text(repo, "diff-tree", "--root", "--no-commit-id", "--name-only", "-r",
                registration, environment=environment).splitlines() != [relative]:
        raise ValueError("registration commit scope is not exact")
    later = git_text(repo, "log", "--format=%H", "--reverse", f"{registration}..HEAD",
                     "--", relative, environment=environment).splitlines()
    if (len(later) != 1
            or git_text(repo, "rev-parse", f"{later[0]}^", environment=environment) != registration):
        raise ValueError("freeze is not the one immediate post-registration protocol commit")
    if git_text(repo, "diff-tree", "--no-commit-id", "--name-only", "-r", later[0],
                environment=environment).splitlines() != [relative]:
        raise ValueError("freeze commit scope is not exact")
    frozen = subprocess.run(["git", "show", f"{later[0]}:{relative}"], cwd=repo,
                            capture_output=True, timeout=120, check=True,
                            env=environment).stdout
    if frozen != protocol.read_bytes():
        raise ValueError("working protocol bytes differ from authenticated freeze commit")


def static_preflight(repo: Path, protocol_path: Path, protocol_sha: str,
                     protocol_tool: Path, run_id: str, value: dict[str, Any],
                     preflight: list[str], finalizer: list[str],
                     environment: dict[str, str], canonical_environment: dict[str, str]) -> None:
    launch = value.get("extensions", {}).get("launch", {})
    finalization = value.get("extensions", {}).get("finalization", {})
    if preflight != substitute_argv(launch.get("preflight_argv_template", []), run_id, protocol_sha):
        raise ValueError("constructed preflight argv differs from frozen template")
    if finalizer != substitute_argv(finalization.get("finalizer_argv_template", []), run_id, protocol_sha):
        raise ValueError("constructed finalizer argv differs from frozen template")
    verify_tool_hashes(repo, value, protocol_tool)
    verify_freeze_chain(repo, protocol_path, value, environment)
    result = subprocess.run(
        [*CANONICAL_PYTHON, str(protocol_tool), "validate", str(protocol_path)],
        cwd=repo, capture_output=True, text=True, timeout=120, check=False,
        env=canonical_environment,
    )
    if result.returncode or "0 finding(s)" not in result.stdout:
        raise ValueError("canonical protocol validation did not return zero findings")


def environment_policy_valid(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    hashes = value.get("network_forwarded_value_sha256")
    if (not isinstance(hashes, dict) or set(hashes) - set(NETWORK_ALLOWLIST)
            or any(SHA256_RE.fullmatch(str(item)) is None for item in hashes.values())):
        return False
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
        "network_forward_allowlist": NETWORK_ALLOWLIST,
        "build_inherited_keys": [],
        "build_fixed": {
            "PATH": "<fresh-task-root>/cargo-home/bin:/usr/bin:/bin",
            "RUSTUP_HOME": "<fresh-task-root>/rustup-home",
            "CARGO_HOME": "<fresh-task-root>/cargo-home",
            "TMPDIR": "<fresh-task-root>/tmp/<arm>", "LANG": "C", "LC_ALL": "C", "TZ": "UTC",
            "RUSTC": f"<fresh-task-root>/rustup-home/toolchains/{RUST_TOOLCHAIN}/bin/rustc",
            "CC": "/usr/bin/x86_64-linux-gnu-gcc-14", "AR": "/usr/bin/x86_64-linux-gnu-ar",
            "RANLIB": "/usr/bin/x86_64-linux-gnu-ranlib",
            "CARGO_TARGET_X86_64_UNKNOWN_LINUX_GNU_LINKER": "/usr/bin/x86_64-linux-gnu-gcc-14",
            "CARGO_INCREMENTAL": "0", "CARGO_NET_OFFLINE": "true",
            "CARGO_TERM_COLOR": "never", "SOURCE_DATE_EPOCH": "0",
            "CARGO_TARGET_DIR": "<fresh-task-root>/target/<arm>",
        },
        "forbidden_inherited_patterns": FORBIDDEN_BUILD_PATTERNS,
        "cargo_config_policy": "fresh CARGO_HOME and no config/config.toml in source ancestors",
        "location_policy": "local_controller",
    }
    launcher = value.get("launcher") if isinstance(value.get("launcher"), dict) else {}
    launcher_hashes = launcher.get("network_forwarded_value_sha256")
    launcher_fixed = {
        "PATH": "/usr/bin:/bin", "HOME": "<caller-owned-fresh-home>",
        "TMPDIR": "<caller-owned-fresh-tmp>", "LANG": "C", "LC_ALL": "C", "TZ": "UTC",
    }
    launcher_python = {
        "executable": PYTHON, "flags": ["-I", "-S", "-B"], "isolated": True,
        "no_site": True, "dont_write_bytecode": True, "safe_path": True,
    }
    return (
        set(value) == set(expected) | {"network_forwarded_value_sha256", "launcher"}
        and all(value.get(key) == item for key, item in expected.items())
        and set(launcher) == {"fixed", "exact_keys", "network_forward_allowlist",
                              "network_forwarded_value_sha256", "python"}
        and launcher.get("fixed") == launcher_fixed
        and launcher.get("exact_keys") == sorted([*launcher_fixed, *hashes])
        and launcher.get("network_forward_allowlist") == NETWORK_ALLOWLIST
        and launcher_hashes == hashes
        and launcher.get("python") == launcher_python
    )


def validate_preflight_receipt(path: Path, run_id: str, protocol_sha: str) -> dict[str, Any]:
    value = strict_json(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("build preflight receipt is not an object")
    expected_keys = {
        "schema", "protocol_id", "protocol_sha256", "run_id", "provider_actions", "location", "tool_sha256",
        "source", "build_contract", "started_at", "status", "error", "finished_at",
        "elapsed_seconds", "archive", "source_delta", "files_per_arm", "builds",
        "binary_contract", "toolchain", "dependency_fetch", "environment_policy",
    }
    if set(value) != expected_keys:
        raise ValueError("build preflight receipt key set is not exact")
    expected = {
        "schema": PREFLIGHT_SCHEMA, "protocol_id": PROTOCOL_ID,
        "protocol_sha256": protocol_sha, "run_id": run_id,
        "provider_actions": False, "status": "passed", "error": None,
        "source_delta": [F4_PATH], "files_per_arm": ARCHIVE_FILES,
        "source": PREFLIGHT_SOURCE, "build_contract": BUILD_CONTRACT,
        "location": "local_controller",
        "tool_sha256": sha256_file(Path(__file__).resolve().with_name("preflight_gpu_geometry_v11.py")),
    }
    if any(value.get(key) != wanted for key, wanted in expected.items()):
        raise ValueError("build preflight receipt identity/status is invalid")
    archive = value.get("archive") if isinstance(value.get("archive"), dict) else {}
    if archive != {
        "roots": ARCHIVE_ROOTS, "sha256": ARCHIVE_SHA256,
        "bytes": ARCHIVE_BYTES, "files": ARCHIVE_FILES,
        "required_members": [
            F4_PATH, "cuda/ca_device.cuh", "challenges/elliptic/corpus.json",
            "suite/Cargo.lock", "bindings/rust/cryptanalysis-sys/build.rs",
        ],
    }:
        raise ValueError("build preflight archive contract is invalid")
    builds = value.get("builds")
    if not isinstance(builds, list) or len(builds) != 2 or [item.get("arm") for item in builds if isinstance(item, dict)] != ["baseline", "candidate"]:
        raise ValueError("build preflight does not contain both ordered arms")
    for item in builds:
        if (set(item) != {"arm", "command", "returncode", "elapsed_seconds", "log_sha256",
                          "log_bytes", "binary_sha256", "binary_bytes"}
                or item.get("command") != BUILD_COMMAND or item.get("returncode") != 0
                or SHA256_RE.fullmatch(str(item.get("binary_sha256", ""))) is None
                or SHA256_RE.fullmatch(str(item.get("log_sha256", ""))) is None
                or type(item.get("binary_bytes")) is not int or item["binary_bytes"] <= 0
                or type(item.get("log_bytes")) is not int or item["log_bytes"] < 0
                or not isinstance(item.get("elapsed_seconds"), (int, float))
                or isinstance(item.get("elapsed_seconds"), bool)
                or not math.isfinite(item["elapsed_seconds"]) or item["elapsed_seconds"] < 0):
            raise ValueError("build preflight arm evidence is invalid")
    contract = value.get("binary_contract") if isinstance(value.get("binary_contract"), dict) else {}
    if (contract.get("baseline_sha256") != builds[0]["binary_sha256"]
            or contract.get("baseline_aa_sha256") != builds[0]["binary_sha256"]
            or contract.get("candidate_sha256") != builds[1]["binary_sha256"]
            or contract.get("baseline_aa_equals_baseline") is not True
            or contract.get("candidate_differs") is not True
            or builds[0]["binary_sha256"] == builds[1]["binary_sha256"]):
        raise ValueError("build preflight binary identity contract is invalid")
    dependency = value.get("dependency_fetch") if isinstance(value.get("dependency_fetch"), dict) else {}
    if not (
        set(dependency) == {"command", "returncode", "log_sha256", "log_bytes",
                            "cargo_config_candidates_checked", "cargo_config_all_absent"}
        and dependency.get("command") == [
            "cargo", "fetch", "--locked", "--manifest-path", "suite/Cargo.toml",
        ]
        and dependency.get("returncode") == 0
        and SHA256_RE.fullmatch(str(dependency.get("log_sha256", ""))) is not None
        and type(dependency.get("log_bytes")) is int and dependency["log_bytes"] >= 0
        and type(dependency.get("cargo_config_candidates_checked")) is int
        and dependency["cargo_config_candidates_checked"] >= 8
        and dependency.get("cargo_config_all_absent") is True
    ):
        raise ValueError("build preflight dependency fetch is invalid")
    if not environment_policy_valid(value.get("environment_policy")):
        raise ValueError("build preflight environment closure is invalid")
    toolchain = value.get("toolchain") if isinstance(value.get("toolchain"), dict) else {}
    bootstrap = toolchain.get("bootstrap") if isinstance(toolchain.get("bootstrap"), dict) else {}
    rustc = toolchain.get("rustc") if isinstance(toolchain.get("rustc"), dict) else {}
    cargo = toolchain.get("cargo") if isinstance(toolchain.get("cargo"), dict) else {}
    cc = toolchain.get("cc") if isinstance(toolchain.get("cc"), dict) else {}
    if not (
        set(toolchain) == {"system_policy", "bootstrap", "rustc", "cargo", "cc", "ar",
                           "ranlib", "linker", "collect2", "system_tools_unchanged_after_builds"}
        and toolchain.get("system_policy") == "controller_exact_hashes"
        and toolchain.get("system_tools_unchanged_after_builds") is True
        and set(bootstrap) == {"url", "sha256", "log_sha256", "log_bytes"}
        and bootstrap.get("url") == RUSTUP_URL and bootstrap.get("sha256") == RUSTUP_SHA256
        and SHA256_RE.fullmatch(str(bootstrap.get("log_sha256", ""))) is not None
        and type(bootstrap.get("log_bytes")) is int and bootstrap["log_bytes"] >= 0
        and set(rustc) == {"toolchain", "sha256", "version"}
        and rustc.get("toolchain") == RUST_TOOLCHAIN and rustc.get("sha256") == RUSTC_SHA256
        and isinstance(rustc.get("version"), str) and "rustc 1.91.1" in rustc["version"]
        and set(cargo) == {"toolchain", "sha256", "version"}
        and cargo.get("toolchain") == RUST_TOOLCHAIN and cargo.get("sha256") == CARGO_SHA256
        and isinstance(cargo.get("version"), str) and cargo["version"].startswith("cargo 1.91.1")
        and set(cc) == {"realpath", "sha256", "version", "target", "capabilities"}
        and cc.get("realpath") == "/usr/bin/x86_64-linux-gnu-gcc-14"
        and cc.get("sha256") == CC_SHA256
        and cc.get("version") == "x86_64-linux-gnu-gcc-14 (Debian 14.2.0-19) 14.2.0"
        and cc.get("target") == "x86_64-linux-gnu"
        and cc.get("capabilities") == {"compile": True, "archive": True, "ranlib": True,
                                       "link": True, "execute": True}
        and toolchain.get("ar") == {"realpath": "/usr/bin/x86_64-linux-gnu-ar",
                                    "sha256": AR_SHA256,
                                    "version": "GNU ar (GNU Binutils for Debian) 2.44"}
        and toolchain.get("ranlib") == {"realpath": "/usr/bin/x86_64-linux-gnu-ranlib",
                                        "sha256": RANLIB_SHA256,
                                        "version": "GNU ranlib (GNU Binutils for Debian) 2.44"}
        and toolchain.get("linker") == {"realpath": "/usr/bin/x86_64-linux-gnu-ld.bfd",
                                        "sha256": LINKER_SHA256,
                                        "version": "GNU ld (GNU Binutils for Debian) 2.44"}
        and toolchain.get("collect2") == {
            "realpath": "/usr/libexec/gcc/x86_64-linux-gnu/14/collect2",
            "sha256": COLLECT2_SHA256,
        }
    ):
        raise ValueError("build preflight toolchain is invalid")
    started, finished = parse_utc(value.get("started_at")), parse_utc(value.get("finished_at"))
    elapsed = value.get("elapsed_seconds")
    if (started is None or finished is None or started > finished
            or not isinstance(elapsed, (int, float)) or isinstance(elapsed, bool)
            or not math.isfinite(elapsed) or elapsed < 0):
        raise ValueError("build preflight timestamps are invalid")
    return value


def write_once(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(
        value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False,
    ) + "\n").encode("utf-8")
    fd, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent,
    )
    temporary_path = Path(temporary)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary_path, path)
    finally:
        try:
            temporary_path.unlink()
        except FileNotFoundError:
            pass
        directory_fd = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)


def valid_existing_terminal(path: Path, run_id: str) -> bool:
    try:
        value = strict_json(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        return False
    return (
        isinstance(value, dict)
        and value.get("schema") == "gpu-f4-update-grid-ab-final-verdict/v1"
        and value.get("run_id") == run_id
        and value.get("terminal") is True
        and value.get("verdict") in {
            "incomplete_session", "invalid_measurement",
            "geometry_not_supported", "geometry_supported",
        }
        and isinstance(value.get("checks"), list)
        and isinstance(value.get("summary"), dict)
    )


def maybe_sha256(path: Path) -> str | None:
    try:
        return sha256_file(path) if path.is_file() else None
    except OSError:
        return None


def ensure_terminal_fallback(
    path: Path, *, protocol: Path, protocol_sha: str, run_id: str,
    preflight_rc: int, controller_rc: int | None, finalizer_rc: int, detail: str,
) -> bool:
    """Write one minimal terminal incomplete record iff the finalizer wrote none."""
    if path.exists():
        if valid_existing_terminal(path, run_id):
            return False
        raise ValueError("existing terminal verdict is malformed or belongs to another run")
    record = {
        "schema": "gpu-f4-update-grid-ab-final-verdict/v1",
        "protocol": {
            "path": str(protocol), "protocol_id": PROTOCOL_ID, "version": 11,
            "sha256": protocol_sha, "file_sha256": maybe_sha256(protocol),
        },
        "run_id": run_id,
        "created": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "terminal": True,
        "verdict": "incomplete_session",
        "precedence": [
            "incomplete_session", "invalid_measurement",
            "geometry_not_supported", "geometry_supported",
        ],
        "provisional_remote_classification": None,
        "evidence": {
            "preflight_returncode": preflight_rc,
            "controller_returncode": controller_rc,
            "finalizer_returncode": finalizer_rc,
            "orchestrator_sha256": maybe_sha256(Path(__file__).resolve()),
        },
        "checks": [{
            "code": "orchestrator.finalizer_totality",
            "category": "completion",
            "status": "failed",
            "detail": detail[:1000] or "finalizer returned without creating its terminal record",
        }],
        "summary": {"completion_failures": 1, "validity_failures": 0, "checks": 1},
    }
    try:
        write_once(path, record)
    except FileExistsError:
        # An independently successful finalizer may have won the publication race.
        if valid_existing_terminal(path, run_id):
            return False
        raise ValueError("racing terminal verdict is malformed or belongs to another run")
    return True


def invoke_campaign(
    preflight: list[str], controller_factory: Callable[[], list[str]], finalizer: list[str],
    *, cwd: Path, environments: dict[str, dict[str, str]],
    ensure_terminal: Callable[[int, int | None, int, str], None],
    run: Callable[..., subprocess.CompletedProcess[Any]] = subprocess.run,
) -> tuple[int, int | None, int]:
    """Run once each; controller is conditional, finalizer is unconditional."""
    preflight_rc = 125
    controller_rc: int | None = None
    pending: BaseException | None = None
    phase = "preflight"
    try:
        try:
            preflight_rc = run(
                preflight, cwd=cwd, check=False, env=environments["preflight"],
            ).returncode
            if preflight_rc == 0:
                phase = "controller"
                controller = controller_factory()
                controller_rc = run(
                    controller, cwd=cwd, check=False, env=environments["controller"],
                ).returncode
        except (OSError, subprocess.SubprocessError):
            if phase == "preflight":
                preflight_rc = 125
            else:
                controller_rc = 125
        except BaseException as exc:
            pending = exc
            if phase == "controller":
                controller_rc = 130 if isinstance(exc, KeyboardInterrupt) else 125
            else:
                preflight_rc = 130 if isinstance(exc, KeyboardInterrupt) else 125
    finally:
        finalizer_rc = 125
        finalizer_detail = ""
        try:
            finalizer_rc = run(
                finalizer, cwd=cwd, check=False, env=environments["finalizer"],
            ).returncode
            if finalizer_rc != 0:
                finalizer_detail = f"finalizer returned {finalizer_rc}"
        except (OSError, subprocess.SubprocessError) as exc:
            finalizer_detail = f"finalizer could not execute: {type(exc).__name__}: {exc}"
        except BaseException as exc:
            finalizer_rc = 130 if isinstance(exc, KeyboardInterrupt) else 125
            finalizer_detail = f"finalizer interrupted: {type(exc).__name__}: {exc}"
            if pending is None:
                pending = exc
        try:
            ensure_terminal(preflight_rc, controller_rc, finalizer_rc, finalizer_detail)
        except BaseException as exc:
            if pending is None:
                pending = exc
    if pending is not None:
        raise pending
    return preflight_rc, controller_rc, finalizer_rc


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_id")
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--protocol-sha256", required=True)
    parser.add_argument("--protocol-tool", type=Path, required=True)
    args = parser.parse_args(argv)
    if RUN_ID_RE.fullmatch(args.run_id) is None:
        parser.error("run_id does not match the frozen v11 namespace")
    if SHA256_RE.fullmatch(args.protocol_sha256) is None:
        parser.error("protocol SHA-256 must be 64 lowercase hexadecimal characters")
    return args


def validate_own_interpreter() -> None:
    flags = sys.flags
    if (Path(sys.executable).resolve() != Path(PYTHON).resolve()
            or flags.isolated != 1 or flags.no_site != 1
            or flags.dont_write_bytecode != 1 or getattr(flags, "safe_path", 0) != 1):
        raise ValueError("orchestrator must run under /usr/bin/python3 -I -S -B")


def main(argv: list[str] | None = None) -> int:
    try:
        validate_own_interpreter()
    except ValueError as exc:
        print(f"GPU geometry v11 orchestration refused before allocation: {exc}", file=sys.stderr)
        return 2
    args = parse_args(argv)
    repo = Path(__file__).resolve().parents[3]
    fallback_written = False
    try:
        with tempfile.TemporaryDirectory(
            prefix="gpu-v11-orchestrator-", dir="/tmp",
        ) as directory:
            environments = exact_phase_environments(
                Path(directory) / "phases", dict(os.environ),
            )
            expected_protocol = (
                repo / STUDY / "protocol-http-rtx5090-geometry-v11.json"
            ).resolve()
            if args.protocol.resolve() != expected_protocol:
                raise ValueError("--protocol is not the exact registered v11 path")
            value = load_frozen_protocol(args.protocol, args.protocol_sha256)
            preflight = preflight_command(repo, args.protocol_sha256, args.run_id)
            finalizer = finalizer_command(
                args.protocol, args.protocol_sha256, args.protocol_tool, args.run_id,
            )
            static_preflight(
                repo, args.protocol, args.protocol_sha256, args.protocol_tool,
                args.run_id, value, preflight, finalizer,
                environments["orchestrator"], environments["canonical"],
            )
            paths = campaign_paths(args.run_id)
            if any((repo / path).exists() for path in paths.values()):
                raise FileExistsError(
                    "a registered preflight/receipt/archive/session/metadata/verdict path already exists"
                )

            def make_controller() -> list[str]:
                preflight_path = repo / paths["preflight"]
                validate_preflight_receipt(preflight_path, args.run_id, args.protocol_sha256)
                preflight_sha = sha256_file(preflight_path)
                built_preflight, controller, built_finalizer = commands(
                    repo, args.protocol, args.protocol_sha256, args.protocol_tool,
                    args.run_id, value, preflight_sha,
                )
                verify_argv_templates(
                    value, built_preflight, controller, built_finalizer,
                    args.run_id, args.protocol_sha256, preflight_sha,
                )
                return controller

            def ensure_terminal(
                preflight_returncode: int, controller_returncode: int | None,
                finalizer_returncode: int, detail: str,
            ) -> None:
                nonlocal fallback_written
                fallback_written = ensure_terminal_fallback(
                    repo / paths["verdict"], protocol=args.protocol,
                    protocol_sha=args.protocol_sha256, run_id=args.run_id,
                    preflight_rc=preflight_returncode,
                    controller_rc=controller_returncode,
                    finalizer_rc=finalizer_returncode, detail=detail,
                )

            preflight_rc, controller_rc, finalizer_rc = invoke_campaign(
                preflight, make_controller, finalizer, cwd=repo,
                environments=environments, ensure_terminal=ensure_terminal,
            )
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"GPU geometry v11 orchestration refused before allocation: {exc}", file=sys.stderr)
        return 2
    if finalizer_rc != 0 or fallback_written:
        print(
            f"terminal finalizer failed after preflight rc={preflight_rc}, "
            f"controller rc={controller_rc}; fallback_written={fallback_written}",
            file=sys.stderr,
        )
        return 2
    print(json.dumps({
        "preflight_returncode": preflight_rc,
        "controller_returncode": controller_rc,
        "terminal_record": "written",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
