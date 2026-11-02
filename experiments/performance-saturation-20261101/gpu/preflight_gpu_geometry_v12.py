#!/usr/bin/env python3
"""Clean-build the exact v12 GPU source closure before any provider call.

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
PROTOCOL_ID = "gpu-f4-update-grid-ab-rtx5090-http-v12-20261101"
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
CC_VERSION = "x86_64-linux-gnu-gcc-14 (Debian 14.2.0-19) 14.2.0"
AR_REALPATH = "/usr/bin/x86_64-linux-gnu-ar"
AR_SHA256 = "f8fe09d485b40b1d47c534c96f5cbaaa9148e247aa0494c087104421f48ac5eb"
AR_VERSION = "GNU ar (GNU Binutils for Debian) 2.44"
RANLIB_REALPATH = "/usr/bin/x86_64-linux-gnu-ranlib"
RANLIB_SHA256 = "4610e832470b987c8c9d82d78c1c16e5e2bc9b8c64db455fad0cf63d420ec86e"
RANLIB_VERSION = "GNU ranlib (GNU Binutils for Debian) 2.44"
LINKER_REALPATH = "/usr/bin/x86_64-linux-gnu-ld.bfd"
LINKER_SHA256 = "d2766988b6a1b1d1518cdc09242e726d1f24e151e16410ada3092b11ffd9081b"
LINKER_VERSION = "GNU ld (GNU Binutils for Debian) 2.44"
COLLECT2_REALPATH = "/usr/libexec/gcc/x86_64-linux-gnu/14/collect2"
COLLECT2_SHA256 = "ea31a4cebd9df1b6428c463428d461ccecfe66c897936409d5b2cde0b3af9e27"
SYSTEM_PATH = "/usr/bin:/bin"
NETWORK_ENV_ALLOWLIST = (
    "ALL_PROXY", "HTTPS_PROXY", "HTTP_PROXY", "NO_PROXY",
    "SSL_CERT_FILE", "CURL_CA_BUNDLE",
)
FORBIDDEN_BUILD_ENV_PATTERNS = (
    "RUSTFLAGS", "CARGO_ENCODED_RUSTFLAGS", "CARGO_PROFILE_*", "CARGO_TARGET_DIR",
    "RUSTC_WRAPPER", "RUSTC_WORKSPACE_WRAPPER", "CFLAGS", "CXXFLAGS", "CPPFLAGS",
    "LDFLAGS", "LD_PRELOAD", "AR", "CC", "RANLIB", "RAYON_NUM_THREADS", "F4_*",
)
FETCH_COMMAND = ("cargo", "fetch", "--locked", "--manifest-path", "suite/Cargo.toml")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
RUN_ID_RE = re.compile(r"^gpu-geometry-http-rtx5090-v12-[A-Za-z0-9._-]{1,80}$")


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


def network_environment() -> tuple[dict[str, str], dict[str, str]]:
    forwarded = {
        key: os.environ[key] for key in NETWORK_ENV_ALLOWLIST if key in os.environ
    }
    hashes = {
        key: hashlib.sha256(value.encode("utf-8")).hexdigest()
        for key, value in sorted(forwarded.items())
    }
    return forwarded, hashes


def exact_base_environment(workspace: Path, rustup_home: Path, cargo_home: Path,
                           *, network: bool) -> tuple[dict[str, str], dict[str, str]]:
    temporary = workspace / "tmp"
    temporary.mkdir(parents=True, exist_ok=True)
    environment = {
        "PATH": SYSTEM_PATH,
        "RUSTUP_HOME": str(rustup_home),
        "CARGO_HOME": str(cargo_home),
        "TMPDIR": str(temporary),
        "LANG": "C",
        "LC_ALL": "C",
        "TZ": "UTC",
    }
    hashes: dict[str, str] = {}
    if network:
        forwarded, hashes = network_environment()
        environment.update(forwarded)
    return environment, hashes


def validate_launcher_environment() -> dict[str, Any]:
    """Refuse ambient process state before any source or network operation."""
    fixed = {"PATH", "HOME", "TMPDIR", "LANG", "LC_ALL", "TZ"}
    allowed = fixed | set(NETWORK_ENV_ALLOWLIST)
    if set(os.environ) - allowed or not fixed.issubset(os.environ):
        raise PreflightError("preflight launcher environment key set is not exact")
    expected = {"PATH": SYSTEM_PATH, "LANG": "C", "LC_ALL": "C", "TZ": "UTC"}
    if any(os.environ.get(key) != value for key, value in expected.items()):
        raise PreflightError("preflight launcher fixed environment differs from policy")
    for key in ("HOME", "TMPDIR"):
        path = Path(os.environ[key])
        if not path.is_absolute() or not path.is_dir():
            raise PreflightError(f"preflight launcher {key} is not an absolute existing directory")
    flags = sys.flags
    if (Path(sys.executable).resolve() != Path("/usr/bin/python3").resolve()
            or flags.isolated != 1 or flags.no_site != 1
            or flags.dont_write_bytecode != 1 or getattr(flags, "safe_path", 0) != 1):
        raise PreflightError("preflight Python interpreter is not the isolated registered executable")
    network_hashes = {
        key: hashlib.sha256(os.environ[key].encode()).hexdigest()
        for key in NETWORK_ENV_ALLOWLIST if key in os.environ
    }
    return {
        "fixed": {
            "PATH": SYSTEM_PATH, "HOME": "<caller-owned-fresh-home>",
            "TMPDIR": "<caller-owned-fresh-tmp>", "LANG": "C", "LC_ALL": "C", "TZ": "UTC",
        },
        "exact_keys": sorted(os.environ),
        "network_forward_allowlist": list(NETWORK_ENV_ALLOWLIST),
        "network_forwarded_value_sha256": network_hashes,
        "python": {
            "executable": "/usr/bin/python3", "flags": ["-I", "-S", "-B"],
            "isolated": True, "no_site": True, "dont_write_bytecode": True,
            "safe_path": True,
        },
    }


def require_exact_tool(path: str, digest: str, label: str) -> Path:
    resolved = Path(path)
    if not resolved.is_file() or sha256_file(resolved) != digest:
        raise PreflightError(f"{label} binary identity mismatch")
    return resolved


def resolve_remote_tool(name: str, label: str) -> Path:
    raw = shutil.which(name, path=SYSTEM_PATH)
    if raw is None:
        raise PreflightError(f"remote {label} is unavailable in the exact system PATH")
    resolved = Path(raw).resolve()
    if not resolved.is_file() or not str(resolved).startswith(("/usr/bin/", "/usr/lib/", "/usr/libexec/")):
        raise PreflightError(f"remote {label} resolves outside frozen system roots")
    return resolved


def command_output(command: list[str], environment: dict[str, str]) -> str:
    result = subprocess.run(
        command, env=environment, capture_output=True, text=True, timeout=30, check=False,
    )
    if result.returncode:
        raise PreflightError(f"tool identity command failed: {command[0]}")
    return (result.stdout or result.stderr).strip()


def probe_c_toolchain(workspace: Path, environment: dict[str, str], cc: Path,
                      ar: Path, ranlib: Path) -> dict[str, Any]:
    probe = workspace / "c-toolchain-probe"
    probe.mkdir(exist_ok=False)
    source = probe / "probe.c"
    source.write_text("int gpu_v12_probe(void){return 0;}\nint main(void){return gpu_v12_probe();}\n",
                      encoding="ascii")
    obj, archive, executable = probe / "probe.o", probe / "libprobe.a", probe / "probe"
    commands = (
        [str(cc), "-c", str(source), "-o", str(obj)],
        [str(ar), "rcs", str(archive), str(obj)],
        [str(ranlib), str(archive)],
        [str(cc), str(source), "-o", str(executable)],
        [str(executable)],
    )
    for command in commands:
        result = subprocess.run(
            command, env=environment, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            timeout=60, check=False,
        )
        if result.returncode:
            raise PreflightError(f"C toolchain capability probe failed: {command[0]}")
    return {"compile": True, "archive": True, "ranlib": True, "link": True, "execute": True}


def bootstrap_toolchain(
    workspace: Path, location: str = "local_controller",
) -> tuple[dict[str, Any], dict[str, str], dict[str, str], Path, dict[str, Any]]:
    if location not in {"local_controller", "remote_pod"}:
        raise PreflightError("unknown build location policy")
    installer = workspace / "rustup-init"
    with urllib.request.urlopen(RUSTUP_INIT_URL, timeout=300) as response:
        data = response.read(64 * 1024 * 1024 + 1)
    if len(data) > 64 * 1024 * 1024 or hashlib.sha256(data).hexdigest() != RUSTUP_INIT_SHA256:
        raise PreflightError("rustup-init download identity mismatch")
    installer.write_bytes(data)
    installer.chmod(0o700)
    rustup_home = workspace / "rustup-home"
    cargo_home = workspace / "cargo-home"
    network_env, network_hashes = exact_base_environment(
        workspace, rustup_home, cargo_home, network=True,
    )
    install = subprocess.run(
        [str(installer), "-y", "--profile", "minimal", "--default-toolchain", "1.91.1",
         "--no-modify-path"],
        env=network_env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
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
    if location == "local_controller":
        cc = require_exact_tool(CC_REALPATH, CC_SHA256, "controller C compiler")
        ar = require_exact_tool(AR_REALPATH, AR_SHA256, "controller archiver")
        ranlib = require_exact_tool(RANLIB_REALPATH, RANLIB_SHA256, "controller ranlib")
        linker = require_exact_tool(LINKER_REALPATH, LINKER_SHA256, "controller linker")
        collect2 = require_exact_tool(COLLECT2_REALPATH, COLLECT2_SHA256, "controller collect2")
    else:
        cc = resolve_remote_tool("cc", "C compiler")
        ar = resolve_remote_tool("ar", "archiver")
        ranlib = resolve_remote_tool("ranlib", "ranlib")
        raw_linker = command_output([str(cc), "-print-prog-name=ld"], network_env)
        linker = (Path(raw_linker).resolve() if Path(raw_linker).is_absolute()
                  else resolve_remote_tool(raw_linker, "linker"))
        raw_collect2 = command_output([str(cc), "-print-prog-name=collect2"], network_env)
        collect2 = (Path(raw_collect2).resolve() if Path(raw_collect2).is_absolute()
                    else resolve_remote_tool(raw_collect2, "collect2"))
        for tool, label in ((linker, "linker"), (collect2, "collect2")):
            if not tool.is_file() or not str(tool).startswith(("/usr/bin/", "/usr/lib/", "/usr/libexec/")):
                raise PreflightError(f"remote {label} resolves outside frozen system roots")
    build_env, _unused = exact_base_environment(
        workspace, rustup_home, cargo_home, network=False,
    )
    build_env.update({
        "PATH": f"{cargo_home / 'bin'}:{SYSTEM_PATH}",
        "RUSTC": str(rustc),
        "CC": str(cc),
        "AR": str(ar),
        "RANLIB": str(ranlib),
        "CARGO_TARGET_X86_64_UNKNOWN_LINUX_GNU_LINKER": str(cc),
        "CARGO_INCREMENTAL": "0",
        "CARGO_NET_OFFLINE": "true",
        "CARGO_TERM_COLOR": "never",
        "SOURCE_DATE_EPOCH": "0",
    })
    network_env.update({
        "PATH": f"{cargo_home / 'bin'}:{SYSTEM_PATH}",
        "RUSTC": str(rustc),
    })
    cc_version = version([str(cc), "--version"], build_env).splitlines()[0]
    cc_target = command_output([str(cc), "-dumpmachine"], build_env)
    if not re.fullmatch(r"x86_64(?:-[A-Za-z0-9_.]+)+", cc_target):
        raise PreflightError(f"remote/controller C compiler target is inadmissible: {cc_target!r}")
    if location == "remote_pod" and re.search(r"gcc|GCC|clang|Ubuntu|Debian", cc_version) is None:
        raise PreflightError(f"remote C compiler version family is inadmissible: {cc_version!r}")
    capabilities = probe_c_toolchain(workspace, build_env, cc, ar, ranlib)
    record = {
        "system_policy": (
            "controller_exact_hashes" if location == "local_controller"
            else "remote_resolved_once_capability_checked_same_for_both_arms"
        ),
        "bootstrap": {
            "url": RUSTUP_INIT_URL,
            "sha256": RUSTUP_INIT_SHA256,
            "log_sha256": hashlib.sha256(install.stdout).hexdigest(),
            "log_bytes": len(install.stdout),
        },
        "rustc": {
            "toolchain": RUST_TOOLCHAIN,
            "sha256": RUSTC_SHA256,
            "version": version([str(rustc), "-Vv"], build_env),
        },
        "cargo": {
            "toolchain": RUST_TOOLCHAIN,
            "sha256": CARGO_SHA256,
            "version": version([str(cargo), "-V"], build_env),
        },
        "cc": {
            "realpath": str(cc),
            "sha256": sha256_file(cc),
            "version": cc_version,
            "target": cc_target,
            "capabilities": capabilities,
        },
        "ar": {"realpath": str(ar), "sha256": sha256_file(ar),
               "version": version([str(ar), "--version"], build_env).splitlines()[0]},
        "ranlib": {"realpath": str(ranlib), "sha256": sha256_file(ranlib),
                   "version": version([str(ranlib), "--version"], build_env).splitlines()[0]},
        "linker": {"realpath": str(linker), "sha256": sha256_file(linker),
                   "version": version([str(linker), "--version"], build_env).splitlines()[0]},
        "collect2": {"realpath": str(collect2), "sha256": sha256_file(collect2)},
    }
    if location == "local_controller" and record["cc"]["version"] != CC_VERSION:
        raise PreflightError("controller C compiler version mismatch")
    if (location == "local_controller"
            and (record["ar"]["version"] != AR_VERSION or record["ranlib"]["version"] != RANLIB_VERSION)):
        raise PreflightError("controller binutils archive tool version mismatch")
    if location == "local_controller" and record["linker"]["version"] != LINKER_VERSION:
        raise PreflightError("controller linker version mismatch")
    policy = {
        "bootstrap_fixed": {
            "PATH": SYSTEM_PATH, "LANG": "C", "LC_ALL": "C", "TZ": "UTC",
            "RUSTUP_HOME": "<fresh-task-root>/rustup-home",
            "CARGO_HOME": "<fresh-task-root>/cargo-home",
            "TMPDIR": "<fresh-task-root>/tmp",
        },
        "fetch_fixed": {
            "PATH": "<fresh-task-root>/cargo-home/bin:/usr/bin:/bin",
            "RUSTUP_HOME": "<fresh-task-root>/rustup-home",
            "CARGO_HOME": "<fresh-task-root>/cargo-home",
            "TMPDIR": "<fresh-task-root>/tmp",
            "LANG": "C", "LC_ALL": "C", "TZ": "UTC",
            "RUSTC": f"<fresh-task-root>/rustup-home/toolchains/{RUST_TOOLCHAIN}/bin/rustc",
        },
        "network_forwarded_value_sha256": network_hashes,
        "network_forward_allowlist": list(NETWORK_ENV_ALLOWLIST),
        "build_inherited_keys": [],
        "build_fixed": {
            "PATH": "<fresh-task-root>/cargo-home/bin:/usr/bin:/bin",
            "RUSTUP_HOME": "<fresh-task-root>/rustup-home",
            "CARGO_HOME": "<fresh-task-root>/cargo-home",
            "TMPDIR": "<fresh-task-root>/tmp/<arm>",
            "LANG": "C", "LC_ALL": "C", "TZ": "UTC",
            "RUSTC": f"<fresh-task-root>/rustup-home/toolchains/{RUST_TOOLCHAIN}/bin/rustc",
            "CC": str(cc) if location == "local_controller" else "<resolved-remote-cc>",
            "AR": str(ar) if location == "local_controller" else "<resolved-remote-ar>",
            "RANLIB": str(ranlib) if location == "local_controller" else "<resolved-remote-ranlib>",
            "CARGO_TARGET_X86_64_UNKNOWN_LINUX_GNU_LINKER": (
                str(cc) if location == "local_controller" else "<resolved-remote-cc>"
            ),
            "CARGO_INCREMENTAL": "0", "CARGO_NET_OFFLINE": "true",
            "CARGO_TERM_COLOR": "never", "SOURCE_DATE_EPOCH": "0",
            "CARGO_TARGET_DIR": "<fresh-task-root>/target/<arm>",
        },
        "forbidden_inherited_patterns": list(FORBIDDEN_BUILD_ENV_PATTERNS),
        "cargo_config_policy": "fresh CARGO_HOME and no config/config.toml in source ancestors",
        "location_policy": location,
    }
    return record, network_env, build_env, cargo, policy


def cargo_config_candidates(cargo_home: Path, source: Path) -> list[Path]:
    candidates = [cargo_home / "config", cargo_home / "config.toml"]
    for ancestor in (source, *source.parents):
        candidates.extend((ancestor / ".cargo" / "config", ancestor / ".cargo" / "config.toml"))
    return candidates


def fetch_dependencies(cargo: Path, source: Path, network_env: dict[str, str],
                       cargo_home: Path) -> dict[str, Any]:
    candidates = cargo_config_candidates(cargo_home, source / "suite")
    if any(path.exists() for path in candidates):
        raise PreflightError("Cargo configuration exists outside the frozen source/environment policy")
    command = [str(cargo), "fetch", "--locked", "--manifest-path", str(source / "suite/Cargo.toml")]
    result = subprocess.run(
        command, env=network_env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        timeout=1_800, check=False,
    )
    if result.returncode:
        tail = result.stdout[-4_096:].decode("utf-8", errors="replace")
        raise PreflightError(f"locked dependency fetch exited {result.returncode}: {tail}")
    return {
        "command": list(FETCH_COMMAND),
        "returncode": 0,
        "log_sha256": hashlib.sha256(result.stdout).hexdigest(),
        "log_bytes": len(result.stdout),
        "cargo_config_candidates_checked": len(candidates),
        "cargo_config_all_absent": True,
    }


def build_arm(arm: str, source: Path, target: Path, environment_base: dict[str, str],
              cargo: Path) -> dict[str, Any]:
    environment = environment_base.copy()
    environment["CARGO_TARGET_DIR"] = str(target)
    arm_tmp = target.parent.parent / "tmp" / arm
    arm_tmp.mkdir(parents=True, exist_ok=False)
    environment["TMPDIR"] = str(arm_tmp)
    expected_keys = {
        "PATH", "RUSTUP_HOME", "CARGO_HOME", "TMPDIR", "LANG", "LC_ALL", "TZ",
        "RUSTC", "CC", "AR", "RANLIB", "CARGO_TARGET_X86_64_UNKNOWN_LINUX_GNU_LINKER",
        "CARGO_INCREMENTAL", "CARGO_NET_OFFLINE", "CARGO_TERM_COLOR", "SOURCE_DATE_EPOCH",
        "CARGO_TARGET_DIR",
    }
    if set(environment) != expected_keys:
        raise PreflightError(f"{arm} build environment key set is not exact")
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


def verify_system_tools_unchanged(toolchain: dict[str, Any]) -> None:
    for name in ("cc", "ar", "ranlib", "linker", "collect2"):
        item = toolchain.get(name) if isinstance(toolchain.get(name), dict) else {}
        path, expected = item.get("realpath"), item.get("sha256")
        if (not isinstance(path, str) or not isinstance(expected, str)
                or not Path(path).is_file() or sha256_file(Path(path)) != expected):
            raise PreflightError(f"system tool drifted between isolated arm builds: {name}")


def perform(repo: Path, workspace: Path, location: str = "local_controller") -> dict[str, Any]:
    launcher_policy = validate_launcher_environment()
    if git(repo, "rev-parse", f"{CANDIDATE_COMMIT}^{{tree}}") != CANDIDATE_TREE:
        raise PreflightError("candidate commit/tree mismatch")
    archive = workspace / "candidate.tar"
    create_archive(repo, archive)
    archive_record = inspect_archive(archive)
    arms = construct_arms(repo, archive, workspace / "source")
    toolchain, network_env, build_env, cargo, environment_policy = bootstrap_toolchain(
        workspace, location,
    )
    environment_policy["launcher"] = launcher_policy
    if (launcher_policy["network_forwarded_value_sha256"]
            != environment_policy["network_forwarded_value_sha256"]):
        raise PreflightError("launcher/bootstrap network environment identity differs")
    dependency_fetch = fetch_dependencies(
        cargo, arms["candidate"], network_env, Path(build_env["CARGO_HOME"]),
    )
    builds = []
    for arm in ("baseline", "candidate"):
        builds.append(build_arm(
            arm, arms[arm], workspace / "target" / arm, build_env, cargo,
        ))
    verify_system_tools_unchanged(toolchain)
    toolchain["system_tools_unchanged_after_builds"] = True
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
        "dependency_fetch": dependency_fetch,
        "environment_policy": environment_policy,
    }


def write_once(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    fd, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent,
    )
    temporary_path = Path(temporary)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
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
    remote = sub.add_parser(
        "prepare-remote", help="build both remote arms into a caller-owned fresh workspace",
    )
    remote.add_argument("--repo", type=Path, default=Path("."))
    remote.add_argument("--workspace", type=Path, required=True)
    remote.add_argument("--run-id", required=True)
    remote.add_argument("--protocol-sha256", required=True)
    remote.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command in {"run", "prepare-remote"}:
        if RUN_ID_RE.fullmatch(args.run_id) is None:
            parser.error("run ID is outside the frozen v12 namespace")
        if SHA256_RE.fullmatch(args.protocol_sha256) is None:
            parser.error("protocol SHA-256 is malformed")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo = args.repo.resolve()
    if args.command == "check-archive":
        with tempfile.TemporaryDirectory(prefix="gpu-v12-archive-check-") as directory:
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
        "location": "local_controller" if args.command == "run" else "remote_pod",
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
            "network_only_during_bootstrap_and_fetch": True,
            "offline_builds": True,
            "exact_environment_key_set": True,
        },
        "started_at": started_at,
        "status": "failed",
        "error": None,
    }
    returncode = 2
    try:
        if args.command == "run":
            with tempfile.TemporaryDirectory(prefix="gpu-v12-clean-build-") as directory:
                record.update(perform(repo, Path(directory), "local_controller"))
        else:
            workspace = args.workspace.resolve()
            workspace.mkdir(parents=True, exist_ok=False)
            record.update(perform(repo, workspace, "remote_pod"))
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
            print(f"GPU v12 build preflight could not write receipt: {exc}", file=sys.stderr)
            return 2
    print(json.dumps({"out": str(args.out), "status": record["status"]}, sort_keys=True))
    return returncode


if __name__ == "__main__":
    raise SystemExit(main())
