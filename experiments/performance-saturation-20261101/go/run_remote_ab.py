#!/usr/bin/env python3
"""Build and run a frozen Go coordinator A/B campaign on a clean CPU pod.

Build mode creates prospective artifact receipts only. Run mode refuses to
start without a frozen protocol hash and the two build-mode binary hashes.
Combined mode builds both exact arms, records their hashes, runs correctness
tests, and then executes the fixed campaign in the same pod.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from typing import Any


GO_VERSION = "go1.27.3"
GO_ARCHIVE = "go1.27.3.linux-amd64.tar.gz"
GO_URL = f"https://go.dev/dl/{GO_ARCHIVE}"
GO_ARCHIVE_BYTES = 70_588_678
GO_ARCHIVE_SHA256 = "65efbc80fdc1fa2cd2631cad5b481777a68e8725f34e89f50fc6ac714e379b40"

BASELINE_COMMIT = "c273e62140071fe4370fbe6946dcb898c95b4eb2"
BASELINE_TREE = "03b5376c742f80298e124997addec10801bd57bb"
BASELINE_COORD_BLOB = "c49b9af5cf6a2b2c8e2415e17864f9eba7a22420"
BENCHMARK_COMMIT = "050af6a5edbaccee4028574492597049a06cfd83"
BENCHMARK_BLOB = "650f6a4a953d5adef537ce87aa3e114b432f32d7"
BENCHMARK_SHA256 = "b13eafcc112ada81b104c3fde3ad51a75cb80e9a051f9644a66fc27d30218dbd"
CANDIDATE_COMMIT = "f481cdf8561b0cb18b197d56425af6f9f11b4d9f"
CANDIDATE_PARENT = "e0f200f7af1ffa2aeb59dd5d4d4c90c7f5ea4ef5"
CANDIDATE_TREE = "568a9802a4db7da921862a4234e7b1b579df5534"
CANDIDATE_COORD_BLOB = "0d3f53806361e7442bc1d108c16b8b847f029918"
CANDIDATE_DIFF_SHA256 = "38b069f6f1fc2c728b872d79a3694f6552c9f4dba44c597b4b518c266a39f471"
# A prospective binding can overlay one exact correctness-test blob onto both
# synthetic arms.  Historical direct build/run invocations retain their old
# source construction when these remain unset.
COMMON_TEST_COMMIT: str | None = None
COMMON_TEST_BLOB: str | None = None
COMMON_TEST_SHA256: str | None = None
BENCHMARK_CPU_COUNT = 1
AFFINITY_POLICY = (
    "require exactly N distinct allowed CPU ids; order by "
    "(package,die,numa,core,cpu), with missing topology sorting last; "
    "pin the benchmark to the first ordered CPU"
)
# A constant-binding wrapper may set this to its own absolute file path before
# calling ``main``.  Direct historical build/run invocations intentionally
# leave it unset.
RUNNER_BINDING_PATH: str | None = None


def arguments(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("build", "run", "combined"), required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--phase")
    parser.add_argument("--protocol-sha256")
    parser.add_argument("--baseline-binary-sha256")
    parser.add_argument("--candidate-binary-sha256")
    parser.add_argument("--expected-cpus", type=int, default=32)
    parser.add_argument(
        "--expected-memory-bytes", type=int, default=64_000_000_000,
        help="exact cgroup v2 memory.max value required for this placement",
    )
    parser.add_argument("--expected-cpu-flavor", default="cpu3c")
    return parser.parse_args(argv)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def bytes_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_text(path: str) -> str | None:
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return None


def command(argv: list[str], cwd: Path | None = None, env: dict[str, str] | None = None) -> str:
    result = subprocess.run(
        argv, cwd=cwd, env=env, check=True, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, text=True,
    )
    return result.stdout.strip()


def git(repo: Path, *argv: str) -> str:
    return command(["git", "-C", str(repo), *argv])


def commit_parents(repo: Path, commit: str) -> list[str]:
    """Read parent ids from the commit object's raw header.

    Pretty-format placeholders such as ``%P`` intentionally hide parents at
    a shallow boundary.  The parent header remains part of the commit object
    and is therefore the identity source that works for an exact depth-one
    HTTP checkout without fetching or dereferencing the parent object.
    """
    raw = subprocess.check_output(
        ["git", "-C", str(repo), "cat-file", "commit", commit]
    )
    headers, separator, _ = raw.partition(b"\n\n")
    if not separator:
        raise RuntimeError(f"commit object has no header terminator: {commit}")
    parents = []
    for line in headers.splitlines():
        if not line.startswith(b"parent "):
            continue
        try:
            parent = line.removeprefix(b"parent ").decode("ascii")
        except UnicodeDecodeError as error:
            raise RuntimeError(f"commit has a non-ASCII parent id: {commit}") from error
        if re.fullmatch(r"[0-9a-f]{40,64}", parent) is None:
            raise RuntimeError(f"commit has an invalid parent id: {parent!r}")
        parents.append(parent)
    return parents


def require_tools() -> dict[str, str]:
    versions = {}
    probes = {
        "git": ["git", "--version"],
        "gcc": ["gcc", "--version"],
        "tar": ["tar", "--version"],
        "taskset": ["taskset", "--version"],
    }
    for name, probe in probes.items():
        if shutil.which(name) is None:
            raise RuntimeError(f"required tool is missing: {name}")
        versions[name] = command(probe).splitlines()[0]
    versions["libc"] = command(["ldd", "--version"]).splitlines()[0]
    return versions


def cgroup_value(name: str) -> str | None:
    for root in (Path("/sys/fs/cgroup"), Path("/sys/fs/cgroup/unified")):
        value = read_text(str(root / name))
        if value is not None:
            return value
    return None


def integer_file(path: Path) -> int | None:
    try:
        return int(path.read_text().strip())
    except (OSError, ValueError):
        return None


def cpu_topology(affinity: list[int]) -> list[dict[str, Any]]:
    topology = []
    for cpu in affinity:
        root = Path(f"/sys/devices/system/cpu/cpu{cpu}")
        nodes = sorted(root.glob("node[0-9]*"))
        numa = int(nodes[0].name[4:]) if nodes else None
        topology.append({
            "cpu": cpu,
            "package": integer_file(root / "topology/physical_package_id"),
            "die": integer_file(root / "topology/die_id"),
            "numa": numa,
            "core": integer_file(root / "topology/core_id"),
            "thread_siblings": read_text(str(root / "topology/thread_siblings_list")),
        })
    return topology


def ordered_cpus(affinity: list[int], topology: list[dict[str, Any]]) -> list[int]:
    if len(affinity) != len(set(affinity)) or any(cpu < 0 for cpu in affinity):
        raise RuntimeError(f"allowed CPU ids are not distinct nonnegative integers: {affinity}")
    by_cpu = {row.get("cpu"): row for row in topology}
    if set(by_cpu) != set(affinity) or len(by_cpu) != len(topology):
        raise RuntimeError("CPU topology does not cover the allowed affinity exactly once")

    def value(row: dict[str, Any], field: str) -> int:
        item = row.get(field)
        return item if isinstance(item, int) and item >= 0 else 1 << 62

    return sorted(
        affinity,
        key=lambda cpu: (
            value(by_cpu[cpu], "package"),
            value(by_cpu[cpu], "die"),
            value(by_cpu[cpu], "numa"),
            value(by_cpu[cpu], "core"),
            cpu,
        ),
    )


def host_snapshot() -> dict[str, Any]:
    affinity = sorted(os.sched_getaffinity(0))
    topology = cpu_topology(affinity)
    cpu_stat = (read_text("/proc/stat") or "").splitlines()
    cpu_fields = cpu_stat[0].split()[1:] if cpu_stat else []
    return {
        "uname": command(["uname", "-a"]),
        "affinity": affinity,
        "cpu_topology": topology,
        "topology_order": ordered_cpus(affinity, topology),
        "logical_cpus": os.cpu_count(),
        "cpuinfo_sha256": bytes_sha256(Path("/proc/cpuinfo").read_bytes()),
        "cpu_model": next(
            (line.split(":", 1)[1].strip() for line in Path("/proc/cpuinfo").read_text().splitlines()
             if line.startswith("model name")),
            None,
        ),
        "meminfo": read_text("/proc/meminfo"),
        "loadavg": read_text("/proc/loadavg"),
        "pressure_cpu": read_text("/proc/pressure/cpu"),
        "pressure_memory": read_text("/proc/pressure/memory"),
        "steal_ticks": int(cpu_fields[7]) if len(cpu_fields) > 7 else None,
        "cpu_stat": cgroup_value("cpu.stat"),
        "cpu_max": cgroup_value("cpu.max"),
        "cpuset_cpus": cgroup_value("cpuset.cpus.effective"),
        "memory_max": cgroup_value("memory.max"),
        "memory_events": cgroup_value("memory.events"),
        "nvidia_devices": sorted(str(path) for path in Path("/dev").glob("nvidia*")),
    }


def validate_host(snapshot: dict[str, Any], cpus: int, memory_bytes: int) -> dict[str, Any]:
    # os.cpu_count() can report the physical host rather than the container's
    # cpuset.  The schedulable affinity is the in-container execution contract.
    affinity = snapshot["affinity"]
    if len(affinity) != cpus or len(set(affinity)) != cpus or any(cpu < 0 for cpu in affinity):
        raise RuntimeError(f"CPU identity mismatch: affinity={affinity}, want {cpus} distinct CPUs")
    order = ordered_cpus(affinity, snapshot["cpu_topology"])
    if snapshot.get("topology_order") != order:
        raise RuntimeError("recorded CPU topology order is inconsistent")
    if type(memory_bytes) is not int or memory_bytes <= 0:
        raise RuntimeError(f"invalid expected memory byte limit: {memory_bytes!r}")
    memory_max = snapshot["memory_max"]
    if not isinstance(memory_max, str) or re.fullmatch(r"[1-9][0-9]*", memory_max) is None:
        raise RuntimeError(f"memory.max={memory_max!r}, want exact {memory_bytes}")
    if int(memory_max) != memory_bytes:
        raise RuntimeError(f"memory.max={memory_max}, want exact {memory_bytes}")
    if snapshot["nvidia_devices"]:
        raise RuntimeError(f"CPU campaign found GPU devices: {snapshot['nvidia_devices']}")
    return {
        "policy": AFFINITY_POLICY,
        "allowed_cpus": affinity,
        "topology_order": order,
        "benchmark_cpus": order[:BENCHMARK_CPU_COUNT],
        "memory_limit_bytes": memory_bytes,
    }


def assert_affinity(expected: list[int], observed: list[int] | None = None) -> None:
    current = sorted(os.sched_getaffinity(0)) if observed is None else sorted(observed)
    if current != expected:
        raise RuntimeError(f"allowed CPU affinity changed: observed={current}, expected={expected}")


def install_go(work: Path) -> tuple[Path, dict[str, Any]]:
    archive = work / GO_ARCHIVE
    with urllib.request.urlopen(GO_URL, timeout=120) as response, archive.open("wb") as output:
        shutil.copyfileobj(response, output)
    if archive.stat().st_size != GO_ARCHIVE_BYTES or sha256(archive) != GO_ARCHIVE_SHA256:
        raise RuntimeError("Go toolchain archive identity mismatch")
    toolchain = work / "toolchain"
    toolchain.mkdir()
    with tarfile.open(archive, "r:gz") as bundle:
        for member in bundle.getmembers():
            target = (toolchain / member.name).resolve()
            if toolchain.resolve() not in target.parents and target != toolchain.resolve():
                raise RuntimeError(f"Go archive path escapes toolchain: {member.name}")
        bundle.extractall(toolchain)
    go = toolchain / "go/bin/go"
    observed = command([str(go), "version"])
    if observed != "go version go1.27.3 linux/amd64":
        raise RuntimeError(f"unexpected Go version: {observed}")
    receipt = {
        "url": GO_URL,
        "archive": GO_ARCHIVE,
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": sha256(archive),
        "go_version": observed,
        "go_env": json.loads(command([str(go), "env", "-json"])),
    }
    archive.unlink()
    return go, receipt


def ensure_commit(repo: Path, commit: str) -> None:
    found = subprocess.run(
        ["git", "-C", str(repo), "cat-file", "-e", f"{commit}^{{commit}}"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    ).returncode == 0
    if not found:
        command(["git", "-C", str(repo), "fetch", "--quiet", "--no-tags", "--depth=1", "origin", commit])
    observed = git(repo, "rev-parse", "--verify", f"{commit}^{{commit}}")
    if observed != commit:
        raise RuntimeError(f"commit identity mismatch: expected {commit}, observed {observed}")


def require_object_type(repo: Path, object_id: str, expected_type: str) -> None:
    observed_type = git(repo, "cat-file", "-t", object_id)
    if observed_type != expected_type:
        raise RuntimeError(
            f"object type mismatch for {object_id}: "
            f"expected {expected_type}, observed {observed_type}"
        )


def archive_commit(repo: Path, commit: str, destination: Path) -> None:
    destination.mkdir()
    producer = subprocess.Popen(
        ["git", "-C", str(repo), "archive", "--format=tar", commit],
        stdout=subprocess.PIPE,
    )
    assert producer.stdout is not None
    consumer = subprocess.run(["tar", "-x", "-C", str(destination)], stdin=producer.stdout)
    producer.stdout.close()
    producer_rc = producer.wait()
    if producer_rc != 0 or consumer.returncode != 0:
        raise RuntimeError("failed to materialize source archive")


def tree_manifest(root: Path) -> dict[str, str]:
    manifest = {}
    for path in sorted(root.rglob("*")):
        relative = str(path.relative_to(root))
        if path.is_symlink():
            manifest[relative] = "symlink:" + os.readlink(path)
        elif path.is_file():
            manifest[relative] = sha256(path)
    return manifest


def prepare_sources(repo: Path, work: Path) -> tuple[Path, Path, dict[str, Any]]:
    commits = [BASELINE_COMMIT, BENCHMARK_COMMIT, CANDIDATE_COMMIT]
    if COMMON_TEST_COMMIT is not None:
        commits.append(COMMON_TEST_COMMIT)
    if any(value is None for value in (COMMON_TEST_COMMIT, COMMON_TEST_BLOB, COMMON_TEST_SHA256)) \
            and any(value is not None for value in (COMMON_TEST_COMMIT, COMMON_TEST_BLOB, COMMON_TEST_SHA256)):
        raise RuntimeError("common correctness-test binding must set commit, blob, and SHA-256")
    for commit in commits:
        ensure_commit(repo, commit)
    candidate_parents = commit_parents(repo, CANDIDATE_COMMIT)
    if len(candidate_parents) != 1:
        raise RuntimeError(
            f"candidate must have exactly one recorded parent: {candidate_parents}"
        )
    identities = {
        "baseline_commit": git(repo, "rev-parse", BASELINE_COMMIT),
        "baseline_tree": git(repo, "rev-parse", f"{BASELINE_COMMIT}^{{tree}}"),
        "baseline_coord_blob": git(repo, "rev-parse", f"{BASELINE_COMMIT}:bindings/go/coord.go"),
        "benchmark_commit": git(repo, "rev-parse", BENCHMARK_COMMIT),
        "benchmark_blob": git(repo, "rev-parse", f"{BENCHMARK_COMMIT}:bindings/go/coord_benchmark_test.go"),
        "candidate_commit": git(repo, "rev-parse", CANDIDATE_COMMIT),
        # The raw commit header retains this id at a shallow boundary even
        # though pretty-format %P reports an empty parent list there.
        "candidate_parent": candidate_parents[0],
        "candidate_tree": git(repo, "rev-parse", f"{CANDIDATE_COMMIT}^{{tree}}"),
        "candidate_coord_blob": git(repo, "rev-parse", f"{CANDIDATE_COMMIT}:bindings/go/coord.go"),
        # The merge base was derived before this runner was committed. The
        # synthetic arms below do not depend on history traversal: both begin
        # at this exact baseline tree and differ by one pinned blob.
        "candidate_merge_base": BASELINE_COMMIT,
    }
    expected = {
        "baseline_commit": BASELINE_COMMIT,
        "baseline_tree": BASELINE_TREE,
        "baseline_coord_blob": BASELINE_COORD_BLOB,
        "benchmark_commit": BENCHMARK_COMMIT,
        "benchmark_blob": BENCHMARK_BLOB,
        "candidate_commit": CANDIDATE_COMMIT,
        "candidate_parent": CANDIDATE_PARENT,
        "candidate_tree": CANDIDATE_TREE,
        "candidate_coord_blob": CANDIDATE_COORD_BLOB,
        "candidate_merge_base": BASELINE_COMMIT,
    }
    if identities != expected:
        raise RuntimeError(f"source identity mismatch: {identities}")
    blobs = [BASELINE_COORD_BLOB, BENCHMARK_BLOB, CANDIDATE_COORD_BLOB]
    if COMMON_TEST_BLOB is not None:
        observed_test_blob = git(
            repo, "rev-parse", f"{COMMON_TEST_COMMIT}:bindings/go/coord_test.go"
        )
        if observed_test_blob != COMMON_TEST_BLOB:
            raise RuntimeError("common correctness-test blob mismatch")
        blobs.append(COMMON_TEST_BLOB)
    for blob in blobs:
        require_object_type(repo, blob, "blob")

    baseline = work / "baseline-source"
    candidate = work / "candidate-source"
    archive_commit(repo, BASELINE_COMMIT, baseline)
    benchmark = subprocess.check_output(
        ["git", "-C", str(repo), "show", f"{BENCHMARK_COMMIT}:bindings/go/coord_benchmark_test.go"]
    )
    if bytes_sha256(benchmark) != BENCHMARK_SHA256:
        raise RuntimeError("benchmark source hash mismatch")
    (baseline / "bindings/go/coord_benchmark_test.go").write_bytes(benchmark)
    common_test = None
    if COMMON_TEST_COMMIT is not None:
        common_test = subprocess.check_output(
            ["git", "-C", str(repo), "show", f"{COMMON_TEST_COMMIT}:bindings/go/coord_test.go"]
        )
        if bytes_sha256(common_test) != COMMON_TEST_SHA256:
            raise RuntimeError("common correctness-test source hash mismatch")
        (baseline / "bindings/go/coord_test.go").write_bytes(common_test)
    shutil.copytree(baseline, candidate, symlinks=True)
    candidate_coord = subprocess.check_output(
        ["git", "-C", str(repo), "show", f"{CANDIDATE_COMMIT}:bindings/go/coord.go"]
    )
    (candidate / "bindings/go/coord.go").write_bytes(candidate_coord)
    baseline_manifest = tree_manifest(baseline)
    candidate_manifest = tree_manifest(candidate)
    changed = sorted(
        path for path in set(baseline_manifest) | set(candidate_manifest)
        if baseline_manifest.get(path) != candidate_manifest.get(path)
    )
    if changed != ["bindings/go/coord.go"]:
        raise RuntimeError(f"synthetic source arms differ in {changed}")
    patch = subprocess.check_output(
        ["git", "-C", str(repo), "diff", "--binary", BASELINE_COMMIT, CANDIDATE_COMMIT,
         "--", "bindings/go/coord.go"]
    )
    if bytes_sha256(patch) != CANDIDATE_DIFF_SHA256:
        raise RuntimeError("candidate production diff hash mismatch")
    receipt = {
        **identities,
        "benchmark_sha256": bytes_sha256(benchmark),
        "candidate_diff_sha256": bytes_sha256(patch),
        "baseline_source_manifest_sha256": bytes_sha256(
            json.dumps(baseline_manifest, sort_keys=True, separators=(",", ":")).encode()
        ),
        "candidate_source_manifest_sha256": bytes_sha256(
            json.dumps(candidate_manifest, sort_keys=True, separators=(",", ":")).encode()
        ),
        "only_changed_path": changed[0],
    }
    if common_test is not None:
        receipt.update({
            "common_test_commit": COMMON_TEST_COMMIT,
            "common_test_blob": COMMON_TEST_BLOB,
            "common_test_sha256": bytes_sha256(common_test),
            "common_test_path": "bindings/go/coord_test.go",
        })
    return baseline, candidate, receipt


def build_arm(go: Path, source: Path, output: Path, cache: Path) -> dict[str, Any]:
    env = os.environ.copy()
    env.update({
        "CGO_ENABLED": "1",
        "GOCACHE": str(cache),
        "GOFLAGS": "-buildvcs=false",
        "GOMAXPROCS": "1",
    })
    argv = [str(go), "test", "-c", "-trimpath", "-o", str(output), "."]
    log = command(argv, cwd=source / "bindings/go", env=env)
    return {
        "command": argv,
        "cwd": "bindings/go",
        "env": {key: env[key] for key in ("CGO_ENABLED", "GOFLAGS", "GOMAXPROCS")},
        "stdout": log,
        "binary": output.name,
        "binary_bytes": output.stat().st_size,
        "binary_sha256": sha256(output),
    }


def run_tests(go: Path, source: Path, cache: Path, log: Path) -> dict[str, Any]:
    env = os.environ.copy()
    env.update({"CGO_ENABLED": "1", "GOCACHE": str(cache), "GOFLAGS": "-buildvcs=false"})
    result = subprocess.run(
        [str(go), "test", "./..."], cwd=source / "bindings/go", env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    log.write_text(result.stdout, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(f"tests failed for {source.name}")
    return {
        "command": [str(go), "test", "./..."],
        "cwd": "bindings/go",
        "exit_status": result.returncode,
        "log": log.name,
        "log_bytes": log.stat().st_size,
        "log_sha256": sha256(log),
    }


def cgroup_counter(text: str | None, name: str) -> int | None:
    if text is None:
        return None
    for line in text.splitlines():
        fields = line.split()
        if len(fields) == 2 and fields[0] == name:
            return int(fields[1])
    return None


def cgroup_counters(text: str | None) -> dict[str, int] | None:
    if text is None:
        return None
    counters: dict[str, int] = {}
    for line in text.splitlines():
        fields = line.split()
        if len(fields) != 2 or re.fullmatch(r"[A-Za-z0-9_.-]+", fields[0]) is None:
            return None
        try:
            counters[fields[0]] = int(fields[1])
        except ValueError:
            return None
    return counters


def counter_deltas(before: str | None, after: str | None) -> dict[str, int] | None:
    left = cgroup_counters(before)
    right = cgroup_counters(after)
    if left is None or right is None or set(left) != set(right):
        return None
    return {key: right[key] - left[key] for key in sorted(left)}


def pressure_avg10(text: str | None) -> dict[str, str] | None:
    if text is None:
        return None
    result: dict[str, str] = {}
    for line in text.splitlines():
        fields = line.split()
        if not fields or fields[0] not in {"some", "full"}:
            return None
        values = dict(field.split("=", 1) for field in fields[1:] if "=" in field)
        value = values.get("avg10")
        if value is None or re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", value) is None:
            return None
        result[fields[0]] = value
    return result if set(result) == {"some", "full"} else None


def row_pressure_valid(snapshot: dict[str, Any]) -> bool:
    cpu = pressure_avg10(snapshot.get("psi_cpu"))
    memory = pressure_avg10(snapshot.get("psi_memory"))
    if cpu is None or memory is None:
        return False
    return (
        float(cpu["some"]) <= 10.0
        and float(cpu["full"]) == 0.0
        and float(memory["some"]) == 0.0
        and float(memory["full"]) == 0.0
    )


def main() -> int:
    options = arguments()
    if options.out.exists():
        raise SystemExit(f"refusing to overwrite {options.out}")
    if options.mode in {"run", "combined"}:
        if options.protocol_sha256 is None or re.fullmatch(
            r"[0-9a-f]{64}", options.protocol_sha256
        ) is None:
            raise SystemExit(f"{options.mode} mode requires a frozen protocol SHA-256")
        if options.phase is None or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,120}", options.phase):
            raise SystemExit(f"{options.mode} mode requires a safe explicit --phase")
    if options.mode == "run":
        binary_hashes = (
            options.baseline_binary_sha256,
            options.candidate_binary_sha256,
        )
        if any(value is None or not re.fullmatch(r"[0-9a-f]{64}", value) for value in binary_hashes):
            raise SystemExit("run mode requires two binary SHA-256 values")
    if options.mode == "combined" and (
        options.baseline_binary_sha256 is not None
        or options.candidate_binary_sha256 is not None
    ):
        raise SystemExit("combined mode derives both binary hashes in the same invocation")
    repo = Path(__file__).resolve().parents[3]
    binding = Path(RUNNER_BINDING_PATH).resolve() if RUNNER_BINDING_PATH else None
    if binding is not None and not binding.is_file():
        raise SystemExit(f"runner binding is not a regular file: {binding}")
    output = options.out.resolve()
    output.mkdir(parents=True)
    initial_host = host_snapshot()
    placement = validate_host(
        initial_host, options.expected_cpus, options.expected_memory_bytes
    )
    expected_affinity = placement["allowed_cpus"]
    tools = require_tools()

    with tempfile.TemporaryDirectory(prefix="go-coord-remote-ab-") as temporary:
        work = Path(temporary)
        go, toolchain = install_go(work)
        assert_affinity(expected_affinity)
        baseline_source, candidate_source, sources = prepare_sources(repo, work)
        assert_affinity(expected_affinity)
        build_dir = output / "build"
        build_dir.mkdir()
        baseline_binary = build_dir / "coord-baseline.test"
        candidate_binary = build_dir / "coord-candidate.test"
        baseline_build = build_arm(go, baseline_source, baseline_binary, work / "cache-baseline")
        assert_affinity(expected_affinity)
        candidate_build = build_arm(go, candidate_source, candidate_binary, work / "cache-candidate")
        assert_affinity(expected_affinity)
        build_receipt = {
            "schema": "go-coordinator-remote-build/v1",
            "runner_sha256": sha256(Path(__file__).resolve()),
            "runner": {
                "engine": str(Path(__file__).resolve().relative_to(repo)),
                "engine_sha256": sha256(Path(__file__).resolve()),
                "binding": str(binding.relative_to(repo)) if binding is not None else None,
                "binding_sha256": sha256(binding) if binding is not None else None,
            },
            "mode": options.mode,
            "expected_cpu_flavor": options.expected_cpu_flavor,
            "host": initial_host,
            "placement": placement,
            "tools": tools,
            "toolchain": toolchain,
            "sources": sources,
            "arms": {"go-baseline": baseline_build, "go-candidate": candidate_build},
        }
        write_json(build_dir / "manifest.json", build_receipt)

        if options.mode == "build":
            return 0
        if options.mode == "run":
            if baseline_build["binary_sha256"] != options.baseline_binary_sha256:
                raise RuntimeError("baseline binary differs from frozen artifact hash")
            if candidate_build["binary_sha256"] != options.candidate_binary_sha256:
                raise RuntimeError("candidate binary differs from frozen artifact hash")
        baseline_campaign_sha = baseline_build["binary_sha256"]
        candidate_campaign_sha = candidate_build["binary_sha256"]
        tests = output / "tests"
        tests.mkdir()
        baseline_tests = run_tests(
            go, baseline_source, work / "test-cache-baseline", tests / "baseline.txt"
        )
        assert_affinity(expected_affinity)
        candidate_tests = run_tests(
            go, candidate_source, work / "test-cache-candidate", tests / "candidate.txt"
        )
        assert_affinity(expected_affinity)
        write_json(
            tests / "manifest.json",
            {
                "schema": "go-coordinator-remote-tests/v1",
                "protocol_sha256": options.protocol_sha256,
                "arms": {
                    "go-baseline": baseline_tests,
                    "go-candidate": candidate_tests,
                },
            },
        )

        before = host_snapshot()
        assert_affinity(expected_affinity, before["affinity"])
        campaign = output / "campaign"
        runner = Path(__file__).with_name("run_remote_campaign.py")
        benchmark_cpu = placement["benchmark_cpus"][0]
        argv = [
            sys.executable, str(runner),
            "--out", str(campaign),
            "--phase", options.phase,
            "--protocol-sha256", options.protocol_sha256,
            "--left-arm", "go-baseline",
            "--left-binary", str(baseline_binary),
            "--left-sha256", baseline_campaign_sha,
            "--right-arm", "go-candidate",
            "--right-binary", str(candidate_binary),
            "--right-sha256", candidate_campaign_sha,
            "--warmups", "3", "--replicates", "20", "--cpu", str(benchmark_cpu),
            "--expected-affinity", ",".join(str(cpu) for cpu in expected_affinity),
            "--timeout-seconds", "1800",
        ]
        command(argv, cwd=repo)
        after = host_snapshot()
        assert_affinity(expected_affinity, after["affinity"])
        rows = [
            json.loads(line) for line in (campaign / "rows.jsonl").read_text().splitlines() if line
        ]
        mismatches = 0
        for case in {row["case"] for row in rows if not row["warmup"]}:
            for replicate in range(1, 21):
                pair = {
                    row["arm"]: row["parsed"]["fingerprints"]
                    for row in rows
                    if not row["warmup"] and row["case"] == case and row["replicate"] == replicate
                }
                mismatches += int(pair.get("go-baseline") != pair.get("go-candidate"))
        measured_steal_rows = sum(
            row["host_after"]["steal_ticks"] != row["host_before"]["steal_ticks"]
            for row in rows if not row["warmup"]
        )
        steal_rows = sum(
            row["host_after"]["steal_ticks"] != row["host_before"]["steal_ticks"]
            for row in rows
        )
        affinity_rows = sum(
            row.get("expected_affinity") != expected_affinity
            or row["host_before"].get("self_affinity") != expected_affinity
            or row["host_after"].get("self_affinity") != expected_affinity
            for row in rows
        )
        pressure_rows = sum(
            not row_pressure_valid(row[side])
            for row in rows
            for side in ("host_before", "host_after")
        )
        throttled_before = cgroup_counter(before["cpu_stat"], "nr_throttled")
        throttled_after = cgroup_counter(after["cpu_stat"], "nr_throttled")
        throttled_delta = (
            throttled_after - throttled_before
            if throttled_before is not None and throttled_after is not None else None
        )
        memory_event_deltas = counter_deltas(
            before["memory_events"], after["memory_events"]
        )
        placement_unchanged = (
            before["affinity"] == after["affinity"] == expected_affinity
            and before["topology_order"] == after["topology_order"] == placement["topology_order"]
            and before["cpuinfo_sha256"] == after["cpuinfo_sha256"] == initial_host["cpuinfo_sha256"]
            and before["cpu_model"] == after["cpu_model"] == initial_host["cpu_model"]
            and before["cpuset_cpus"] == after["cpuset_cpus"] == initial_host["cpuset_cpus"]
            and before["memory_max"] == after["memory_max"] == str(options.expected_memory_bytes)
            and before["nvidia_devices"] == after["nvidia_devices"] == []
        )
        timing_valid = (
            steal_rows == 0
            and before["steal_ticks"] == after["steal_ticks"]
            and affinity_rows == 0
            and pressure_rows == 0
            and throttled_delta == 0
            and memory_event_deltas is not None
            and all(delta == 0 for delta in memory_event_deltas.values())
            and placement_unchanged
            and mismatches == 0
        )
        isolation = {
            "schema": "go-coordinator-remote-isolation/v1",
            "before": before,
            "after": after,
            "placement": placement,
            "rows": len(rows),
            "row_pressure_observations": len(rows) * 2,
            "rows_with_nonzero_steal_delta": steal_rows,
            "measured_rows_with_nonzero_steal_delta": measured_steal_rows,
            "rows_with_affinity_change": affinity_rows,
            "pressure_observations_failing_numeric_gate": pressure_rows,
            "pressure_gate": {
                "cpu_some_avg10_max": "10.0",
                "cpu_full_avg10": "0.0",
                "memory_some_avg10": "0.0",
                "memory_full_avg10": "0.0",
            },
            "cgroup_nr_throttled_delta": throttled_delta,
            "memory_event_deltas": memory_event_deltas,
            "placement_unchanged": placement_unchanged,
            "fingerprint_pair_mismatches": mismatches,
            "timing_valid": timing_valid,
        }
        write_json(output / "isolation.json", isolation)
        write_json(
            output / "remote-summary.json",
            {
                "schema": "go-coordinator-remote-summary/v1",
                "protocol_sha256": options.protocol_sha256,
                "build_manifest_sha256": sha256(build_dir / "manifest.json"),
                "tests_manifest_sha256": sha256(tests / "manifest.json"),
                "campaign_rows_sha256": sha256(campaign / "rows.jsonl"),
                "isolation_sha256": sha256(output / "isolation.json"),
                "fingerprint_pair_mismatches": mismatches,
                "timing_valid": timing_valid,
            },
        )
        if mismatches:
            raise RuntimeError(f"{mismatches} measured correctness fingerprint pairs differ")
    return 0


if __name__ == "__main__":
    sys.exit(main())
