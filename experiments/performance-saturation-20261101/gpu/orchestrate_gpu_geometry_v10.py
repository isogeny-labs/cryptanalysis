#!/usr/bin/env python3
"""Run the one-pod v10 HTTP controller, then always issue its terminal verdict.

This is the only registered launch entry point.  It contains no retry path:
exactly one controller invocation is followed by exactly one finalizer
invocation even when the controller or remote runner returns nonzero.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable


PROTOCOL_ID = "gpu-f4-update-grid-ab-rtx5090-http-v10-20261101"
SOURCE_REF = "refs/heads/codex/runpod-http-gpu-geometry-v10-20261101"
RUN_ID_RE = re.compile(r"^gpu-geometry-http-rtx5090-v10-[A-Za-z0-9._-]{1,80}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
STUDY = Path("experiments/performance-saturation-20261101/gpu")


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode("utf-8")


def protocol_hash(value: dict[str, Any]) -> str:
    body = {key: item for key, item in value.items() if key != "freeze"}
    return hashlib.sha256(canonical(body)).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load_frozen_protocol(path: Path, expected_sha: str) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("protocol is not an object")
    freeze = value.get("freeze") if isinstance(value.get("freeze"), dict) else {}
    if (
        value.get("protocol_id") != PROTOCOL_ID or value.get("version") != 10
        or freeze.get("status") != "frozen" or freeze.get("protocol_sha256") != expected_sha
        or protocol_hash(value) != expected_sha or freeze.get("filed_before_affected_data") is not True
    ):
        raise ValueError("protocol identity/freeze/hash is not the registered prospective v10")
    return value


def commands(repo: Path, protocol: Path, protocol_sha: str, protocol_tool: Path,
             run_id: str, value: dict[str, Any]) -> tuple[list[str], list[str]]:
    tooling = value.get("extensions", {}).get("tooling_source", {})
    if tooling.get("public_ref") != SOURCE_REF:
        raise ValueError("protocol tooling ref is not the registered v10 ref")
    source_commit = tooling.get("commit")
    if not isinstance(source_commit, str) or re.fullmatch(r"[0-9a-f]{40}", source_commit) is None:
        raise ValueError("protocol tooling commit is malformed")
    session = STUDY / "runs-http" / run_id
    receipt = STUDY / "http-receipts" / f"{run_id}.json"
    archive = STUDY / "http-receipts" / f"{run_id}.result.tar.gz"
    remote = STUDY / "http-receipts" / f"{run_id}.remote"
    verdict = STUDY / "final-verdicts" / f"{run_id}.json"
    command = (
        "bash ecc2k130/runner/codegen/install_nsys_tools.sh && "
        "GPU_STUDY_SECURE=1 bash "
        "experiments/performance-saturation-20261101/gpu/run_gpu_geometry_ab.sh "
        f"'experiments/performance-saturation-20261101/gpu/runs-http' '{run_id}' "
        f"'{protocol_sha}'"
    )
    controller = [
        "python3", "cloud/runpod_http_batch.py", "misagi-f4-geometry-v10",
        "--source-ref", SOURCE_REF, "--source-commit", source_commit,
        "--cloud", "SECURE", "--gpu", "NVIDIA GeForce RTX 5090", "--gpu-count", "1",
        "--min-vcpu", "16", "--min-ram", "62", "--image", "runpod/base:1.0.2-ubuntu2404",
        "--disk", "100", "--max-price", "1.19", "--max-hours", "3", "--wait", "900",
        "--timeout", "9000", "--reconcile-seconds", "60", "--max-result-mib", "4096",
        "--receipt", str(receipt), "--archive", str(archive), "--out", str(session),
        "--", command,
    ]
    finalizer = [
        "python3", str(STUDY / "finalize_gpu_geometry_ab.py"),
        "--protocol", str(protocol), "--protocol-sha256", protocol_sha,
        "--protocol-tool", str(protocol_tool), "--receipt", str(receipt),
        "--archive", str(archive), "--remote-metadata", str(remote),
        "--session", str(session), "--out", str(verdict),
    ]
    return controller, finalizer


def substitute_argv(template: list[Any], run_id: str, protocol_sha: str) -> list[str]:
    if not all(isinstance(item, str) for item in template):
        raise ValueError("frozen argv template contains a non-string token")
    return [item.replace("<run_id>", run_id).replace("<frozen_protocol_sha256>", protocol_sha)
            for item in template]


def verify_argv_templates(value: dict[str, Any], controller: list[str], finalizer: list[str],
                          run_id: str, protocol_sha: str) -> None:
    extensions = value.get("extensions") if isinstance(value.get("extensions"), dict) else {}
    launch = extensions.get("launch") if isinstance(extensions.get("launch"), dict) else {}
    finalization = extensions.get("finalization") if isinstance(extensions.get("finalization"), dict) else {}
    expected_controller = substitute_argv(launch.get("controller_argv_template", []), run_id, protocol_sha)
    expected_finalizer = substitute_argv(finalization.get("finalizer_argv_template", []), run_id, protocol_sha)
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
    for name, expected_name in (("script", "finalize_gpu_geometry_ab.py"),
                                ("orchestrator", "orchestrate_gpu_geometry_v10.py")):
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
    draft = json.loads(draft_result.stdout)
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


def preflight(repo: Path, protocol_path: Path, protocol_sha: str, protocol_tool: Path,
              run_id: str, value: dict[str, Any], controller: list[str],
              finalizer: list[str]) -> None:
    verify_argv_templates(value, controller, finalizer, run_id, protocol_sha)
    verify_tool_hashes(repo, value, protocol_tool)
    verify_freeze_chain(repo, protocol_path, value)
    result = subprocess.run(
        ["python3", str(protocol_tool), "validate", str(protocol_path)],
        cwd=repo, capture_output=True, text=True, timeout=120, check=False,
    )
    if result.returncode or "0 finding(s)" not in result.stdout:
        raise ValueError("canonical protocol validation did not return zero findings")


def invoke_pair(
    controller: list[str],
    finalizer: list[str],
    *,
    cwd: Path,
    run: Callable[..., subprocess.CompletedProcess[Any]] = subprocess.run,
) -> tuple[int, int]:
    """Invoke once each, with the finalizer unconditional after controller return."""
    controller_rc = 125
    pending: BaseException | None = None
    try:
        try:
            controller_rc = run(controller, cwd=cwd, check=False).returncode
        except (OSError, subprocess.SubprocessError):
            controller_rc = 125
        except BaseException as exc:
            pending = exc
            controller_rc = 130 if isinstance(exc, KeyboardInterrupt) else 125
    finally:
        finalizer_rc = run(finalizer, cwd=cwd, check=False).returncode
    if pending is not None:
        raise pending
    return controller_rc, finalizer_rc


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_id")
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--protocol-sha256", required=True)
    parser.add_argument("--protocol-tool", type=Path, required=True)
    args = parser.parse_args(argv)
    if RUN_ID_RE.fullmatch(args.run_id) is None:
        parser.error("run_id does not match the frozen v10 namespace")
    if SHA256_RE.fullmatch(args.protocol_sha256) is None:
        parser.error("protocol SHA-256 must be 64 lowercase hexadecimal characters")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo = Path(__file__).resolve().parents[3]
    try:
        expected_protocol = (repo / STUDY / "protocol-http-rtx5090-geometry-v10.json").resolve()
        if args.protocol.resolve() != expected_protocol:
            raise ValueError("--protocol is not the exact registered v10 path")
        value = load_frozen_protocol(args.protocol, args.protocol_sha256)
        controller, finalizer = commands(
            repo, args.protocol, args.protocol_sha256, args.protocol_tool, args.run_id, value,
        )
        preflight(
            repo, args.protocol, args.protocol_sha256, args.protocol_tool,
            args.run_id, value, controller, finalizer,
        )
        output_paths = [Path(controller[controller.index("--receipt") + 1]),
                        Path(controller[controller.index("--archive") + 1]),
                        Path(controller[controller.index("--out") + 1]),
                        Path(finalizer[finalizer.index("--remote-metadata") + 1]),
                        Path(finalizer[finalizer.index("--out") + 1])]
        if any((repo / path).exists() for path in output_paths):
            raise FileExistsError("a registered receipt/archive/session/metadata/verdict path already exists")
        controller_rc, finalizer_rc = invoke_pair(controller, finalizer, cwd=repo)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"GPU geometry v10 orchestration refused before allocation: {exc}", file=sys.stderr)
        return 2
    if finalizer_rc != 0:
        print(f"terminal finalizer failed after controller rc={controller_rc}", file=sys.stderr)
        return 2
    print(json.dumps({"controller_returncode": controller_rc, "terminal_record": "written"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
