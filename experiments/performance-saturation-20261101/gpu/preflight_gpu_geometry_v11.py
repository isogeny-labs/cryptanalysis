#!/usr/bin/env python3
"""Clean-build the exact v11 GPU source closure before any provider call.

The preflight creates the registered candidate archive, extracts it into two
fresh trees outside the checkout, overlays only the baseline F4 source, proves
the one-file source delta, and performs isolated release builds of both arms.
It always attempts to write one immutable receipt.  No provider API is used.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from typing import Any
import urllib.request


SCHEMA = "gpu-geometry-build-preflight/v1"
PROTOCOL_ID = "gpu-f4-update-grid-ab-rtx5090-http-v11-20261101"
BASELINE_COMMIT = "7c712913b7e912494e87c35e854cfd0129bad89c"
CANDIDATE_COMMIT = "59b6d7e17100d4d16db5d25c2762a5d5cf45ef4f"
CANDIDATE_TREE = "af0ac7e239c0acaa063c1a1441d6fb374ebbf30b"
ARCHIVE_ROOTS = ("suite", "bindings/rust", "include", "src", "cuda", "challenges")
ARCHIVE_SHA256 = "554dcaacb7ff1fcfb27f4b49bb60b2d03ac9201978091c5e516fff356d1f9b8d"
ARCHIVE_BYTES = 19_435_520
ARCHIVE_FILES = 1_253
F4_PATH = "suite/src/cryptanalysis/f4_gpu.rs"
BASELINE_F4_SHA256 = "da8c53c757cac0dfd81d1f75bfc5845610b645338215e52710efa11d57783944"
CANDIDATE_F4_SHA256 = "77832323d4d5a2b6b49fa2ca26fe40de1a80c0a8e17a9bb1949081a30fa84953"
REQUIRED_MEMBERS = (
    F4_PATH,
    "cuda/ca_device.cuh",
    "challenges/elliptic/corpus.json",
    "suite/Cargo.lock",
    "bindings/rust/cryptanalysis-sys/build.rs",
)
BUILD_COMMAND = ("cargo", "build", "--release", "--locked", "--example", "f4_matrix_bench")
RUST_TOOLCHAIN = "1.91.1-x86_64-unknown-linux-gnu"
RUSTUP_INIT_URL = (
    "https://static.rust-lang.org/rustup/archive/1.29.2/"
    "x86_64-unknown-linux-gnu/rustup-init"
)
RUSTUP_INIT_SHA256 = "5be191e8c70a5007074254cb74d78dbfdd25cd5a61c27de7b8e5410122ec24f4"
RUSTC_SHA256 = "5eadaaf4fe086d76547b17dc3c1ba880d0082b93f7d8bc65612770da8e79fe8e"
CARGO_SHA256 = "e60b4010303c19a131c058e3f054b4b3311433c4b2ee94ba8e09e165ff2a3b3b"
CC_REALPATH = "/usr/bin/x86_64-linux-gnu-gcc-14"
CC_SHA256 = "a23ecab8ff08f09ad8c80602c2c5df7f49e09c25905cb8975902e101bf72635f"
CC_VERSION = "cc (Debian 14.2.0-19) 14.2.0"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
RUN_ID_RE = re.compile(r"^gpu-geometry-http-rtx5090-v11-[A-Za-z0-9._-]{1,80}$")


class PreflightError(RuntimeError):
    """The exact clean-build preflight cannot be admitted."""


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def git(repo: Path, *arguments: str, binary: bool = False) -> str | bytes:
    result = subprocess.run(
        ["git", *arguments], cwd=repo, capture_output=True, timeout=300, check=False,
    )
    if result.returncode:
        raise PreflightError(f"git {arguments[0] if arguments else ''} failed")
    return result.stdout if binary else result.stdout.decode("utf-8").strip()


def create_archive(repo: Path, destination: Path,
                   roots: tuple[str, ...] = ARCHIVE_ROOTS) -> None:
    result = subprocess.run(
        ["git", "archive", "--format=tar", "--output", str(destination),
         CANDIDATE_COMMIT, "--", *roots],
        cwd=repo, capture_output=True, timeout=300, check=False,
    )
    if result.returncode:
        raise PreflightError("git archive failed")


def archive_member_inventory(path: Path) -> tuple[set[str], int]:
    names: set[str] = set()
    files = 0
    with tarfile.open(path, "r:") as archive:
        for member in archive.getmembers():
            pure = PurePosixPath(member.name)
            if (pure.is_absolute() or ".." in pure.parts or member.issym()
                    or member.islnk() or not (member.isfile() or member.isdir())):
                raise PreflightError(f"unsafe archive member {member.name!r}")
            if member.name in names:
                raise PreflightError(f"duplicate archive member {member.name!r}")
            names.add(member.name)
            files += int(member.isfile())
    return names, files


def require_closure_members(names: set[str]) -> None:
    missing = set(REQUIRED_MEMBERS) - names
    if missing:
        raise PreflightError(f"candidate closure is missing required members: {sorted(missing)}")


def inspect_archive(path: Path) -> dict[str, Any]:
    digest = sha256_file(path)
    if digest != ARCHIVE_SHA256 or path.stat().st_size != ARCHIVE_BYTES:
        raise PreflightError(
            f"candidate closure identity mismatch: {digest}/{path.stat().st_size}"
        )
    names, files = archive_member_inventory(path)
    if files != ARCHIVE_FILES:
        raise PreflightError(f"candidate closure file count {files}, expected {ARCHIVE_FILES}")
    require_closure_members(names)
    return {
        "roots": list(ARCHIVE_ROOTS),
        "sha256": digest,
        "bytes": path.stat().st_size,
        "files": files,
        "required_members": list(REQUIRED_MEMBERS),
    }


def safe_extract(path: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=False)
    with tarfile.open(path, "r:") as archive:
        for member in archive.getmembers():
            pure = PurePosixPath(member.name)
            if (pure.is_absolute() or ".." in pure.parts or member.issym()
                    or member.islnk() or not (member.isfile() or member.isdir())):
                raise PreflightError(f"unsafe archive member {member.name!r}")
        archive.extractall(destination, filter="data")


def tree_inventory(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): sha256_file(path)
        for path in sorted(root.rglob("*")) if path.is_file()
    }


def construct_arms(repo: Path, archive: Path, source: Path) -> dict[str, Any]:
    baseline, candidate = source / "baseline", source / "candidate"
    safe_extract(archive, baseline)
    safe_extract(archive, candidate)
    baseline_bytes = git(repo, "show", f"{BASELINE_COMMIT}:{F4_PATH}", binary=True)
    assert isinstance(baseline_bytes, bytes)
    (baseline / F4_PATH).write_bytes(baseline_bytes)
    baseline_inventory = tree_inventory(baseline)
    candidate_inventory = tree_inventory(candidate)
    all_paths = set(baseline_inventory) | set(candidate_inventory)
    differences = sorted(
        path for path in all_paths
        if baseline_inventory.get(path) != candidate_inventory.get(path)
    )
    if differences != [F4_PATH]:
        raise PreflightError(f"arm source delta is not exact: {differences}")
    if baseline_inventory[F4_PATH] != BASELINE_F4_SHA256:
        raise PreflightError("baseline F4 identity mismatch")
    if candidate_inventory[F4_PATH] != CANDIDATE_F4_SHA256:
        raise PreflightError("candidate F4 identity mismatch")
    return {
        "baseline": baseline,
        "candidate": candidate,
        "differences": differences,
        "files_per_arm": len(candidate_inventory),
    }


def version(command: list[str], environment: dict[str, str] | None = None) -> str:
    result = subprocess.run(
        command, env=environment, capture_output=True, text=True, timeout=30, check=False,
    )
    if result.returncode:
        raise PreflightError(f"cannot query {command[0]} version")
    return (result.stdout or result.stderr).strip()


def bootstrap_toolchain(workspace: Path) -> tuple[dict[str, Any], dict[str, str], Path]:
    installer = workspace / "rustup-init"
    with urllib.request.urlopen(RUSTUP_INIT_URL, timeout=300) as response:
        data = response.read(64 * 1024 * 1024 + 1)
    if len(data) > 64 * 1024 * 1024 or hashlib.sha256(data).hexdigest() != RUSTUP_INIT_SHA256:
        raise PreflightError("rustup-init download identity mismatch")
    installer.write_bytes(data)
    installer.chmod(0o700)
    rustup_home = workspace / "rustup-home"
    cargo_home = workspace / "cargo-home"
    environment = os.environ.copy()
    environment.update({
        "RUSTUP_HOME": str(rustup_home),
        "CARGO_HOME": str(cargo_home),
    })
    install = subprocess.run(
        [str(installer), "-y", "--profile", "minimal", "--default-toolchain", "1.91.1",
         "--no-modify-path"],
        env=environment, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        timeout=1_800, check=False,
    )
    if install.returncode:
        tail = install.stdout[-4_096:].decode("utf-8", errors="replace")
        raise PreflightError(f"pinned rustup bootstrap exited {install.returncode}: {tail}")
    bin_dir = rustup_home / "toolchains" / RUST_TOOLCHAIN / "bin"
    rustc, cargo = bin_dir / "rustc", bin_dir / "cargo"
    if not rustc.is_file() or sha256_file(rustc) != RUSTC_SHA256:
        raise PreflightError("pinned rustc binary identity mismatch")
    if not cargo.is_file() or sha256_file(cargo) != CARGO_SHA256:
        raise PreflightError("pinned cargo binary identity mismatch")
    cc = Path("/usr/bin/cc").resolve()
    if str(cc) != CC_REALPATH or not cc.is_file() or sha256_file(cc) != CC_SHA256:
        raise PreflightError("controller C compiler identity mismatch")
    environment.update({
        "PATH": f"{cargo_home / 'bin'}:{os.environ.get('PATH', '')}",
        "RUSTC": str(rustc),
        "CC": str(cc),
        "CARGO_INCREMENTAL": "0",
    })
    record = {
        "bootstrap": {
            "url": RUSTUP_INIT_URL,
            "sha256": RUSTUP_INIT_SHA256,
            "log_sha256": hashlib.sha256(install.stdout).hexdigest(),
            "log_bytes": len(install.stdout),
        },
        "rustc": {
            "toolchain": RUST_TOOLCHAIN,
            "sha256": RUSTC_SHA256,
            "version": version([str(rustc), "-Vv"], environment),
        },
        "cargo": {
            "toolchain": RUST_TOOLCHAIN,
            "sha256": CARGO_SHA256,
            "version": version([str(cargo), "-V"], environment),
        },
        "cc": {
            "realpath": CC_REALPATH,
            "sha256": CC_SHA256,
            "version": version([str(cc), "--version"], environment).splitlines()[0],
        },
    }
    if record["cc"]["version"] != CC_VERSION:
        raise PreflightError("controller C compiler version mismatch")
    return record, environment, cargo


def build_arm(arm: str, source: Path, target: Path, environment_base: dict[str, str],
              cargo: Path) -> dict[str, Any]:
    environment = environment_base.copy()
    environment["CARGO_TARGET_DIR"] = str(target)
    started = time.monotonic()
    result = subprocess.run(
        [str(cargo), *BUILD_COMMAND[1:]], cwd=source / "suite", env=environment,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=7_200, check=False,
    )
    elapsed = time.monotonic() - started
    output = result.stdout
    if result.returncode:
        tail = output[-4_096:].decode("utf-8", errors="replace")
        raise PreflightError(f"{arm} clean build exited {result.returncode}: {tail}")
    binary = target / "release" / "examples" / "f4_matrix_bench"
    if not binary.is_file() or not os.access(binary, os.X_OK):
        raise PreflightError(f"{arm} build produced no executable")
    return {
        "arm": arm,
        "command": list(BUILD_COMMAND),
        "returncode": result.returncode,
        "elapsed_seconds": round(elapsed, 6),
        "log_sha256": hashlib.sha256(output).hexdigest(),
        "log_bytes": len(output),
        "binary_sha256": sha256_file(binary),
        "binary_bytes": binary.stat().st_size,
    }


def perform(repo: Path, workspace: Path) -> dict[str, Any]:
    if git(repo, "rev-parse", f"{CANDIDATE_COMMIT}^{{tree}}") != CANDIDATE_TREE:
        raise PreflightError("candidate commit/tree mismatch")
    archive = workspace / "candidate.tar"
    create_archive(repo, archive)
    archive_record = inspect_archive(archive)
    arms = construct_arms(repo, archive, workspace / "source")
    toolchain, environment, cargo = bootstrap_toolchain(workspace)
    builds = []
    for arm in ("baseline", "candidate"):
        builds.append(build_arm(
            arm, arms[arm], workspace / "target" / arm, environment, cargo,
        ))
    hashes = {item["arm"]: item["binary_sha256"] for item in builds}
    if hashes["baseline"] == hashes["candidate"]:
        raise PreflightError("baseline and candidate clean-build binaries are identical")
    baseline_aa = workspace / "baseline-aa"
    shutil.copyfile(
        workspace / "target" / "baseline" / "release" / "examples" / "f4_matrix_bench",
        baseline_aa,
    )
    if sha256_file(baseline_aa) != hashes["baseline"]:
        raise PreflightError("baseline-aa copy is not byte-identical")
    return {
        "archive": archive_record,
        "source_delta": arms["differences"],
        "files_per_arm": arms["files_per_arm"],
        "builds": builds,
        "binary_contract": {
            "baseline_sha256": hashes["baseline"],
            "baseline_aa_sha256": sha256_file(baseline_aa),
            "candidate_sha256": hashes["candidate"],
            "baseline_aa_equals_baseline": True,
            "candidate_differs": True,
        },
        "toolchain": toolchain,
    }


def write_once(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n"
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check-archive", help="recreate and inspect the frozen archive only")
    check.add_argument("--repo", type=Path, default=Path("."))
    run = sub.add_parser("run", help="perform both clean builds and write one receipt")
    run.add_argument("--repo", type=Path, default=Path("."))
    run.add_argument("--run-id", required=True)
    run.add_argument("--protocol-sha256", required=True)
    run.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "run":
        if RUN_ID_RE.fullmatch(args.run_id) is None:
            parser.error("run ID is outside the frozen v11 namespace")
        if SHA256_RE.fullmatch(args.protocol_sha256) is None:
            parser.error("protocol SHA-256 is malformed")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo = args.repo.resolve()
    if args.command == "check-archive":
        with tempfile.TemporaryDirectory(prefix="gpu-v11-archive-check-") as directory:
            archive = Path(directory) / "candidate.tar"
            create_archive(repo, archive)
            print(json.dumps(inspect_archive(archive), sort_keys=True))
        return 0

    started_at = utc_now()
    started = time.monotonic()
    record: dict[str, Any] = {
        "schema": SCHEMA,
        "protocol_id": PROTOCOL_ID,
        "protocol_sha256": args.protocol_sha256,
        "run_id": args.run_id,
        "provider_actions": False,
        "tool_sha256": sha256_file(Path(__file__).resolve()),
        "source": {
            "baseline_commit": BASELINE_COMMIT,
            "candidate_commit": CANDIDATE_COMMIT,
            "candidate_tree": CANDIDATE_TREE,
            "baseline_f4_sha256": BASELINE_F4_SHA256,
            "candidate_f4_sha256": CANDIDATE_F4_SHA256,
        },
        "build_contract": {
            "clean_extracted_closure": True,
            "isolated_source_trees": True,
            "isolated_target_dirs": True,
            "cargo_incremental": "0",
        },
        "started_at": started_at,
        "status": "failed",
        "error": None,
    }
    returncode = 2
    try:
        with tempfile.TemporaryDirectory(prefix="gpu-v11-clean-build-") as directory:
            record.update(perform(repo, Path(directory)))
        record["status"] = "passed"
        returncode = 0
    except (OSError, ValueError, PreflightError, subprocess.SubprocessError) as exc:
        record["error"] = {"type": type(exc).__name__, "detail": str(exc)[-4_096:]}
    finally:
        record["finished_at"] = utc_now()
        record["elapsed_seconds"] = round(time.monotonic() - started, 6)
        try:
            write_once(args.out, record)
        except OSError as exc:
            print(f"GPU v11 build preflight could not write receipt: {exc}", file=sys.stderr)
            return 2
    print(json.dumps({"out": str(args.out), "status": record["status"]}, sort_keys=True))
    return returncode


if __name__ == "__main__":
    raise SystemExit(main())
