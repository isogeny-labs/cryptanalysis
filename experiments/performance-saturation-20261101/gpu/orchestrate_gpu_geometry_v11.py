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
import re
import subprocess
import sys
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
        "python3", str(STUDY / "preflight_gpu_geometry_v11.py"), "run",
        "--repo", str(repo), "--run-id", run_id,
        "--protocol-sha256", protocol_sha, "--out", str(paths["preflight"]),
    ]


def finalizer_command(protocol: Path, protocol_sha: str, protocol_tool: Path,
                      run_id: str) -> list[str]:
    paths = campaign_paths(run_id)
    return [
        "python3", str(STUDY / "finalize_gpu_geometry_ab_v11.py"),
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
        "GPU_STUDY_SECURE=1 bash "
        "experiments/performance-saturation-20261101/gpu/run_gpu_geometry_ab_v11.sh "
        f"'experiments/performance-saturation-20261101/gpu/runs-http' '{run_id}' "
        f"'{protocol_sha}' '{preflight_sha}'"
    )
    return [
        "python3", "cloud/runpod_http_batch.py", "misagi-f4-geometry-v11",
        "--source-ref", SOURCE_REF, "--source-commit", source_commit,
        "--cloud", "SECURE", "--gpu", "NVIDIA GeForce RTX 5090", "--gpu-count", "1",
        "--min-vcpu", "16", "--min-ram", "62", "--image", "runpod/base:1.0.2-ubuntu2404",
        "--disk", "100", "--max-price", "1.19", "--max-hours", "3", "--wait", "900",
        "--timeout", "9000", "--reconcile-seconds", "60", "--max-result-mib", "4096",
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


def git_text(repo: Path, *arguments: str) -> str:
    result = subprocess.run(["git", *arguments], cwd=repo, capture_output=True,
                            text=True, timeout=120, check=False)
    if result.returncode:
        raise ValueError(f"git {' '.join(arguments[:2])} failed")
    return result.stdout.strip()


def verify_freeze_chain(repo: Path, protocol: Path, value: dict[str, Any]) -> None:
    relative = protocol.resolve().relative_to(repo).as_posix()
    freeze = value.get("freeze") if isinstance(value.get("freeze"), dict) else {}
    registration = freeze.get("commit")
    if not isinstance(registration, str) or re.fullmatch(r"[0-9a-f]{40}", registration) is None:
        raise ValueError("freeze.commit is not a full registration commit")
    draft_result = subprocess.run(["git", "show", f"{registration}:{relative}"], cwd=repo,
                                  capture_output=True, timeout=120, check=False)
    if draft_result.returncode:
        raise ValueError("registered draft is unavailable")
    draft = strict_json(draft_result.stdout)
    if not isinstance(draft, dict) or draft.get("freeze", {}).get("status") != "draft" or protocol_hash(draft) != protocol_hash(value):
        raise ValueError("registration commit does not contain the matching draft")
    if git_text(repo, "diff-tree", "--root", "--no-commit-id", "--name-only", "-r", registration).splitlines() != [relative]:
        raise ValueError("registration commit scope is not exact")
    later = git_text(repo, "log", "--format=%H", "--reverse", f"{registration}..HEAD", "--", relative).splitlines()
    if len(later) != 1 or git_text(repo, "rev-parse", f"{later[0]}^") != registration:
        raise ValueError("freeze is not the one immediate post-registration protocol commit")
    if git_text(repo, "diff-tree", "--no-commit-id", "--name-only", "-r", later[0]).splitlines() != [relative]:
        raise ValueError("freeze commit scope is not exact")
    frozen = subprocess.run(["git", "show", f"{later[0]}:{relative}"], cwd=repo,
                            capture_output=True, timeout=120, check=True).stdout
    if frozen != protocol.read_bytes():
        raise ValueError("working protocol bytes differ from authenticated freeze commit")


def static_preflight(repo: Path, protocol_path: Path, protocol_sha: str,
                     protocol_tool: Path, run_id: str, value: dict[str, Any],
                     preflight: list[str], finalizer: list[str]) -> None:
    launch = value.get("extensions", {}).get("launch", {})
    finalization = value.get("extensions", {}).get("finalization", {})
    if preflight != substitute_argv(launch.get("preflight_argv_template", []), run_id, protocol_sha):
        raise ValueError("constructed preflight argv differs from frozen template")
    if finalizer != substitute_argv(finalization.get("finalizer_argv_template", []), run_id, protocol_sha):
        raise ValueError("constructed finalizer argv differs from frozen template")
    verify_tool_hashes(repo, value, protocol_tool)
    verify_freeze_chain(repo, protocol_path, value)
    result = subprocess.run(
        ["python3", str(protocol_tool), "validate", str(protocol_path)],
        cwd=repo, capture_output=True, text=True, timeout=120, check=False,
    )
    if result.returncode or "0 finding(s)" not in result.stdout:
        raise ValueError("canonical protocol validation did not return zero findings")


def validate_preflight_receipt(path: Path, run_id: str, protocol_sha: str) -> dict[str, Any]:
    value = strict_json(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("build preflight receipt is not an object")
    expected_keys = {
        "schema", "protocol_id", "protocol_sha256", "run_id", "provider_actions", "tool_sha256",
        "source", "build_contract", "started_at", "status", "error", "finished_at",
        "elapsed_seconds", "archive", "source_delta", "files_per_arm", "builds",
        "binary_contract", "toolchain",
    }
    if set(value) != expected_keys:
        raise ValueError("build preflight receipt key set is not exact")
    expected = {
        "schema": PREFLIGHT_SCHEMA, "protocol_id": PROTOCOL_ID,
        "protocol_sha256": protocol_sha, "run_id": run_id,
        "provider_actions": False, "status": "passed", "error": None,
        "source_delta": [F4_PATH], "files_per_arm": ARCHIVE_FILES,
        "source": PREFLIGHT_SOURCE, "build_contract": BUILD_CONTRACT,
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
    toolchain = value.get("toolchain") if isinstance(value.get("toolchain"), dict) else {}
    bootstrap = toolchain.get("bootstrap") if isinstance(toolchain.get("bootstrap"), dict) else {}
    rustc = toolchain.get("rustc") if isinstance(toolchain.get("rustc"), dict) else {}
    cargo = toolchain.get("cargo") if isinstance(toolchain.get("cargo"), dict) else {}
    cc = toolchain.get("cc") if isinstance(toolchain.get("cc"), dict) else {}
    if not (
        set(toolchain) == {"bootstrap", "rustc", "cargo", "cc"}
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
        and set(cc) == {"realpath", "sha256", "version"}
        and cc.get("realpath") == "/usr/bin/x86_64-linux-gnu-gcc-14"
        and cc.get("sha256") == CC_SHA256 and cc.get("version") == "cc (Debian 14.2.0-19) 14.2.0"
    ):
        raise ValueError("build preflight toolchain is invalid")
    started, finished = parse_utc(value.get("started_at")), parse_utc(value.get("finished_at"))
    elapsed = value.get("elapsed_seconds")
    if (started is None or finished is None or started > finished
            or not isinstance(elapsed, (int, float)) or isinstance(elapsed, bool)
            or not math.isfinite(elapsed) or elapsed < 0):
        raise ValueError("build preflight timestamps are invalid")
    return value


def invoke_campaign(
    preflight: list[str], controller_factory: Callable[[], list[str]], finalizer: list[str],
    *, cwd: Path, run: Callable[..., subprocess.CompletedProcess[Any]] = subprocess.run,
) -> tuple[int, int | None, int]:
    """Run once each; controller is conditional, finalizer is unconditional."""
    preflight_rc = 125
    controller_rc: int | None = None
    pending: BaseException | None = None
    phase = "preflight"
    try:
        try:
            preflight_rc = run(preflight, cwd=cwd, check=False).returncode
            if preflight_rc == 0:
                phase = "controller"
                controller = controller_factory()
                controller_rc = run(controller, cwd=cwd, check=False).returncode
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
        finalizer_rc = run(finalizer, cwd=cwd, check=False).returncode
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


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo = Path(__file__).resolve().parents[3]
    try:
        expected_protocol = (repo / STUDY / "protocol-http-rtx5090-geometry-v11.json").resolve()
        if args.protocol.resolve() != expected_protocol:
            raise ValueError("--protocol is not the exact registered v11 path")
        value = load_frozen_protocol(args.protocol, args.protocol_sha256)
        preflight = preflight_command(repo, args.protocol_sha256, args.run_id)
        finalizer = finalizer_command(args.protocol, args.protocol_sha256, args.protocol_tool, args.run_id)
        static_preflight(
            repo, args.protocol, args.protocol_sha256, args.protocol_tool,
            args.run_id, value, preflight, finalizer,
        )
        paths = campaign_paths(args.run_id)
        if any((repo / path).exists() for path in paths.values()):
            raise FileExistsError("a registered preflight/receipt/archive/session/metadata/verdict path already exists")

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

        preflight_rc, controller_rc, finalizer_rc = invoke_campaign(
            preflight, make_controller, finalizer, cwd=repo,
        )
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"GPU geometry v11 orchestration refused before allocation: {exc}", file=sys.stderr)
        return 2
    if finalizer_rc != 0:
        print(
            f"terminal finalizer failed after preflight rc={preflight_rc}, controller rc={controller_rc}",
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
