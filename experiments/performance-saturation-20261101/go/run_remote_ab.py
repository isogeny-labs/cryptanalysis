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
import signal
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
STABLE_PLACEMENT_SCHEMA = "go-cpu-placement-identity/v1"
STABLE_TOPOLOGY_FIELDS = (
    "cpu", "package", "die", "numa", "core", "thread_siblings",
)
# A constant-binding wrapper may set this to its own absolute file path before
# calling ``main``.  Direct historical build/run invocations intentionally
# leave it unset.
RUNNER_BINDING_PATH: str | None = None
EXPORTER_PATH: str | None = None
ANALYZER_PATH: str | None = None
SUPPORT_PATHS: tuple[str, ...] = ()
OUTPUT_BUDGET_BYTES: int | None = None
REMOTE_SUMMARY_RESERVE_BYTES = 65_536
CAMPAIGN_RUNNER_PATH: str | None = None
L2_MEASURE_PATH: str | None = None
ENABLE_AA_CONTROLS = False
EXCLUDE_CPU_ZERO = False
CURRENT_STAGE = "argument_validation"
CURRENT_SOURCE_COMMIT: str | None = None


class WorkflowAbort(BaseException):
    pass


def abort_on_signal(signum: int, _frame: object) -> None:
    raise WorkflowAbort(f"combined workflow received signal {signum}")


def set_stage(stage: str) -> None:
    global CURRENT_STAGE
    CURRENT_STAGE = stage


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


def parse_cpu_set(text: str | None) -> set[int]:
    result: set[int] = set()
    if not text:
        return result
    try:
        for field in text.split(","):
            if "-" in field:
                left, right = field.split("-", 1)
                result.update(range(int(left), int(right) + 1))
            elif field:
                result.add(int(field))
    except ValueError:
        return set()
    return result


def stable_placement_identity(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Return the canonical, frequency-independent CPU placement identity.

    Raw ``/proc/cpuinfo`` bytes are useful provenance, but fields such as
    ``cpu MHz`` change while a process is running.  Only this explicit
    allowlist is allowed to decide whether the placement stayed unchanged.
    """

    model = snapshot.get("cpu_model")
    logical_cpus = snapshot.get("logical_cpus")
    affinity = snapshot.get("affinity")
    raw_topology = snapshot.get("cpu_topology")
    order = snapshot.get("topology_order")
    cpuset = snapshot.get("cpuset_cpus")
    memory_max = snapshot.get("memory_max")
    devices = snapshot.get("nvidia_devices")
    if not isinstance(model, str) or not model.strip():
        raise ValueError("stable placement requires a nonempty CPU model")
    if type(logical_cpus) is not int or logical_cpus <= 0:
        raise ValueError("stable placement requires a positive logical CPU count")
    if (
        not isinstance(affinity, list)
        or not affinity
        or any(type(cpu) is not int or cpu < 0 for cpu in affinity)
        or len(set(affinity)) != len(affinity)
    ):
        raise ValueError("stable placement affinity is malformed")
    if logical_cpus < len(affinity):
        raise ValueError("logical CPU count is smaller than the allowed affinity")
    if not isinstance(raw_topology, list) or len(raw_topology) != len(affinity):
        raise ValueError("stable placement topology is malformed")
    topology: list[dict[str, Any]] = []
    for raw in raw_topology:
        if not isinstance(raw, dict):
            raise ValueError("stable placement topology row is malformed")
        row = {field: raw.get(field) for field in STABLE_TOPOLOGY_FIELDS}
        if type(row["cpu"]) is not int or row["cpu"] < 0:
            raise ValueError("stable placement topology CPU is malformed")
        for field in ("package", "die", "numa", "core"):
            if row[field] is not None and (
                type(row[field]) is not int or row[field] < 0
            ):
                raise ValueError(f"stable placement topology {field} is malformed")
        if row["thread_siblings"] is not None and not isinstance(
            row["thread_siblings"], str
        ):
            raise ValueError("stable placement thread-sibling set is malformed")
        topology.append(row)
    if {row["cpu"] for row in topology} != set(affinity):
        raise ValueError("stable placement topology does not cover affinity")
    if (
        not isinstance(order, list)
        or any(type(cpu) is not int or cpu < 0 for cpu in order)
        or len(order) != len(affinity)
        or set(order) != set(affinity)
        or order != ordered_cpus(affinity, topology)
    ):
        raise ValueError("stable placement topology order is malformed")
    if not isinstance(cpuset, str) or parse_cpu_set(cpuset) != set(affinity):
        raise ValueError("stable placement cgroup cpuset differs from affinity")
    if not isinstance(memory_max, str) or re.fullmatch(r"[1-9][0-9]*", memory_max) is None:
        raise ValueError("stable placement memory limit is malformed")
    if (
        not isinstance(devices, list)
        or any(not isinstance(path, str) or not path for path in devices)
        or len(set(devices)) != len(devices)
    ):
        raise ValueError("stable placement GPU inventory is malformed")
    return {
        "schema": STABLE_PLACEMENT_SCHEMA,
        "cpu_model": model.strip(),
        "logical_cpus": logical_cpus,
        "affinity": list(affinity),
        "cpu_topology": topology,
        "topology_order": list(order),
        "cpuset_cpus": sorted(parse_cpu_set(cpuset)),
        "memory_limit_bytes": int(memory_max),
        "nvidia_devices": sorted(devices),
    }


def stable_placement_sha256(identity: dict[str, Any]) -> str:
    return bytes_sha256(json.dumps(
        identity, sort_keys=True, separators=(",", ":"),
        ensure_ascii=True, allow_nan=False,
    ).encode("utf-8"))


def bind_stable_placement_identity(snapshot: dict[str, Any]) -> dict[str, Any]:
    identity = stable_placement_identity(snapshot)
    snapshot["placement_identity"] = identity
    snapshot["placement_identity_sha256"] = stable_placement_sha256(identity)
    return snapshot


def stable_placement_snapshot_valid(snapshot: dict[str, Any]) -> bool:
    try:
        identity = stable_placement_identity(snapshot)
    except (KeyError, TypeError, ValueError):
        return False
    return (
        snapshot.get("placement_identity") == identity
        and snapshot.get("placement_identity_sha256")
        == stable_placement_sha256(identity)
    )


def stable_placement_unchanged(*snapshots: dict[str, Any]) -> bool:
    if not snapshots or not all(stable_placement_snapshot_valid(item) for item in snapshots):
        return False
    identity = snapshots[0]["placement_identity"]
    digest = snapshots[0]["placement_identity_sha256"]
    return all(
        item["placement_identity"] == identity
        and item["placement_identity_sha256"] == digest
        for item in snapshots[1:]
    )


def host_snapshot() -> dict[str, Any]:
    affinity = sorted(os.sched_getaffinity(0))
    topology = cpu_topology(affinity)
    cpu_stat = (read_text("/proc/stat") or "").splitlines()
    cpu_fields = cpu_stat[0].split()[1:] if cpu_stat else []
    snapshot = {
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
    return bind_stable_placement_identity(snapshot)


def validate_host(snapshot: dict[str, Any], cpus: int, memory_bytes: int) -> dict[str, Any]:
    # os.cpu_count() can report the physical host rather than the container's
    # cpuset.  The schedulable affinity is the in-container execution contract.
    if not stable_placement_snapshot_valid(snapshot):
        raise RuntimeError("stable placement identity is missing or inconsistent")
    affinity = snapshot["affinity"]
    if len(affinity) != cpus or len(set(affinity)) != cpus or any(cpu < 0 for cpu in affinity):
        raise RuntimeError(f"CPU identity mismatch: affinity={affinity}, want {cpus} distinct CPUs")
    order = ordered_cpus(affinity, snapshot["cpu_topology"])
    if snapshot.get("topology_order") != order:
        raise RuntimeError("recorded CPU topology order is inconsistent")
    if EXCLUDE_CPU_ZERO:
        by_cpu = {row["cpu"]: row for row in snapshot["cpu_topology"]}
        eligible = []
        allowed = set(affinity)
        for cpu in order:
            siblings = parse_cpu_set(by_cpu[cpu].get("thread_siblings"))
            if (
                siblings
                and cpu in siblings
                and siblings <= allowed
                and 0 not in siblings
                and allowed - siblings
            ):
                eligible.append((cpu, sorted(siblings)))
        if len(eligible) < BENCHMARK_CPU_COUNT:
            raise RuntimeError("no eligible complete non-housekeeping SMT core")
        benchmark_cpus = [item[0] for item in eligible[:BENCHMARK_CPU_COUNT]]
        reservation_cpus = eligible[0][1]
    else:
        benchmark_cpus = order[:BENCHMARK_CPU_COUNT]
        reservation_cpus = benchmark_cpus
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
        "benchmark_cpus": benchmark_cpus,
        "reservation_cpus": reservation_cpus,
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


def git_archive_receipt(repo: Path, commit: str) -> dict[str, Any]:
    """Stream-hash the exact registered source archive without retaining 878 MB."""

    process = subprocess.Popen(
        ["git", "-C", str(repo), "archive", "--format=tar", commit],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert process.stdout is not None
    digest = hashlib.sha256()
    size = 0
    for block in iter(lambda: process.stdout.read(1024 * 1024), b""):
        size += len(block)
        digest.update(block)
    _, stderr = process.communicate()
    if process.returncode != 0:
        raise RuntimeError(f"failed to hash exact Git source archive: {stderr[-500:]!r}")
    return {
        "commit": commit,
        "tree": git(repo, "rev-parse", f"{commit}^{{tree}}"),
        "bytes": size,
        "sha256": digest.hexdigest(),
        "retained": False,
    }


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


def build_environment(go: Path, work: Path) -> dict[str, str]:
    """Return the complete allowlisted environment used by every Go command.

    Starting from an empty mapping is deliberate: provider/controller values
    such as GOEXPERIMENT, GOAMD64, GOWORK, CC, and CGO_* cannot reach a build.
    All writable roots are shared by both arms and both test commands.
    """

    roots = {
        "HOME": work / "go-home",
        "TMPDIR": work / "tmp",
        "GOPATH": work / "gopath",
        "GOCACHE": work / "gocache",
        "GOMODCACHE": work / "gomodcache",
    }
    for path in roots.values():
        path.mkdir(parents=True, exist_ok=False)
    goroot = go.resolve().parent.parent
    environment = {
        "PATH": "/usr/bin:/bin",
        "HOME": str(roots["HOME"]),
        "TMPDIR": str(roots["TMPDIR"]),
        "LANG": "C",
        "LC_ALL": "C",
        "TZ": "UTC",
        "CGO_ENABLED": "1",
        "CGO_CFLAGS": "-O2 -g",
        "CGO_CPPFLAGS": "",
        "CGO_CXXFLAGS": "-O2 -g",
        "CGO_FFLAGS": "-O2 -g",
        "CGO_LDFLAGS": "-O2 -g",
        "GO111MODULE": "on",
        "GOENV": "off",
        "GOEXPERIMENT": "",
        "GOWORK": "off",
        "GOTOOLCHAIN": "local",
        "GOFLAGS": "-buildvcs=false -mod=readonly",
        "GOMAXPROCS": "1",
        "GOOS": "linux",
        "GOARCH": "amd64",
        "GOAMD64": "v1",
        "GOROOT": str(goroot),
        "GOPATH": str(roots["GOPATH"]),
        "GOCACHE": str(roots["GOCACHE"]),
        "GOMODCACHE": str(roots["GOMODCACHE"]),
        "GOPROXY": "https://proxy.golang.org",
        "GOSUMDB": "sum.golang.org",
        "GONOSUMDB": "",
        "GONOPROXY": "",
        "GOPRIVATE": "",
        "GOVCS": "*:off",
        "CC": "/usr/bin/gcc",
        "CXX": "/usr/bin/g++",
        "AR": "/usr/bin/ar",
    }
    required_tools = (environment["CC"], environment["CXX"], environment["AR"])
    if any(not Path(path).is_file() for path in required_tools):
        raise RuntimeError("pinned compiler toolchain path is absent")
    return environment


def environment_sha256(environment: dict[str, str]) -> str:
    return bytes_sha256(
        json.dumps(environment, sort_keys=True, separators=(",", ":")).encode()
    )


def build_arm(
    go: Path,
    source: Path,
    output: Path,
    environment: dict[str, str],
) -> dict[str, Any]:
    argv = [str(go), "test", "-c", "-trimpath", "-o", str(output), "."]
    log = command(argv, cwd=source / "bindings/go", env=environment)
    return {
        "command": argv,
        "cwd": "bindings/go",
        "environment_sha256": environment_sha256(environment),
        "stdout": log,
        "binary": output.name,
        "binary_bytes": output.stat().st_size,
        "binary_sha256": sha256(output),
    }


def run_tests(
    go: Path,
    source: Path,
    environment: dict[str, str],
    log: Path,
) -> dict[str, Any]:
    result = subprocess.run(
        [str(go), "test", "./..."], cwd=source / "bindings/go", env=environment,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    log.write_text(result.stdout, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(f"tests failed for {source.name}")
    return {
        "command": [str(go), "test", "./..."],
        "cwd": "bindings/go",
        "environment_sha256": environment_sha256(environment),
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


def tree_inventory(root: Path, *, exclude: set[str] | None = None) -> dict[str, int]:
    excluded = exclude or set()
    files = 0
    total = 0
    for path in root.rglob("*"):
        relative = path.relative_to(root).as_posix()
        if relative in excluded:
            continue
        if path.is_symlink() or (path.exists() and not path.is_file() and not path.is_dir()):
            raise RuntimeError(f"output tree contains a non-regular entry: {relative}")
        if path.is_file():
            files += 1
            total += path.stat().st_size
    return {"files": files, "bytes": total}


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


def run(options: argparse.Namespace) -> int:
    global CURRENT_SOURCE_COMMIT
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
    exporter = Path(EXPORTER_PATH).resolve() if EXPORTER_PATH else None
    analyzer = Path(ANALYZER_PATH).resolve() if ANALYZER_PATH else None
    support = tuple(Path(path).resolve() for path in SUPPORT_PATHS)
    campaign_binding = (
        Path(CAMPAIGN_RUNNER_PATH).resolve() if CAMPAIGN_RUNNER_PATH else None
    )
    l2_binding = Path(L2_MEASURE_PATH).resolve() if L2_MEASURE_PATH else None
    for label, path in (("runner binding", binding), ("exporter", exporter), ("analyzer", analyzer)):
        if path is not None and not path.is_file():
            raise SystemExit(f"{label} is not a regular file: {path}")
    if (exporter is None) != (analyzer is None):
        raise SystemExit("exporter and analyzer bindings must be configured together")
    if any(not path.is_file() for path in support):
        raise SystemExit("every support binding must be a regular file")
    if any(path is not None and not path.is_file() for path in (campaign_binding, l2_binding)):
        raise SystemExit("campaign and L2 bindings must be regular files")
    if (campaign_binding is None) != (l2_binding is None):
        raise SystemExit("campaign and L2 bindings must be configured together")
    if support and (exporter is None or analyzer is None or binding is None):
        raise SystemExit("support bindings require the complete wrapper/export/analyzer binding")
    bound_paths = tuple(
        path
        for path in (
            Path(__file__).resolve(), binding, exporter, analyzer,
            campaign_binding, l2_binding, *support,
        )
        if path is not None
    )
    if len({path.name for path in bound_paths}) != len(bound_paths):
        raise SystemExit("bound tooling basenames must be unique for retained evidence")
    source_commit = git(repo, "rev-parse", "HEAD")
    if re.fullmatch(r"[0-9a-f]{40}", source_commit) is None:
        raise RuntimeError("source commit is not a lowercase SHA-1 object id")
    CURRENT_SOURCE_COMMIT = source_commit
    output = options.out.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    retained_tooling: dict[str, dict[str, Any]] = {}
    # Publish the owned output root atomically only after every formal tool,
    # especially the registered analyzer, has been copied and authenticated.
    # Thus every observable owned root can seal a canonical failure export.
    staging = Path(
        tempfile.mkdtemp(prefix=f".{output.name}.staging-", dir=output.parent)
    )
    try:
        if bound_paths:
            tooling_dir = staging / "tooling"
            tooling_dir.mkdir()
            ordered_bound_paths = tuple(
                sorted(bound_paths, key=lambda path: (path != analyzer, path.name))
            )
            for source_path in ordered_bound_paths:
                retained = tooling_dir / source_path.name
                shutil.copy2(source_path, retained)
                if sha256(retained) != sha256(source_path):
                    raise RuntimeError(f"retained tooling SHA-256 mismatch: {source_path}")
                retained_tooling[str(source_path.relative_to(repo))] = {
                    "path": f"tooling/{retained.name}",
                    "bytes": retained.stat().st_size,
                    "sha256": sha256(retained),
                }
        staging.replace(output)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    set_stage("host_validation")
    initial_host = host_snapshot()
    placement = validate_host(
        initial_host, options.expected_cpus, options.expected_memory_bytes
    )
    expected_affinity = placement["allowed_cpus"]
    tools = require_tools()

    with tempfile.TemporaryDirectory(prefix="go-coord-remote-ab-") as temporary:
        work = Path(temporary)
        set_stage("toolchain_install")
        go, toolchain = install_go(work)
        go_environment = build_environment(go, work)
        go_environment_digest = environment_sha256(go_environment)
        assert_affinity(expected_affinity)
        set_stage("source_construction")
        baseline_source, candidate_source, sources = prepare_sources(repo, work)
        assert_affinity(expected_affinity)
        build_dir = output / "build"
        build_dir.mkdir()
        if exporter is not None:
            source_archive = git_archive_receipt(repo, source_commit)
        else:
            source_archive = None
        baseline_binary = build_dir / "coord-baseline.test"
        candidate_binary = build_dir / "coord-candidate.test"
        set_stage("build_baseline")
        baseline_build = build_arm(go, baseline_source, baseline_binary, go_environment)
        assert_affinity(expected_affinity)
        set_stage("build_candidate")
        candidate_build = build_arm(go, candidate_source, candidate_binary, go_environment)
        assert_affinity(expected_affinity)
        build_arms = {"go-baseline": baseline_build, "go-candidate": candidate_build}
        aa_left_binary = aa_right_binary = None
        if ENABLE_AA_CONTROLS:
            aa_left_binary = build_dir / "coord-baseline-aa-left.test"
            aa_right_binary = build_dir / "coord-baseline-aa-right.test"
            for aa_binary in (aa_left_binary, aa_right_binary):
                shutil.copy2(baseline_binary, aa_binary)
                if sha256(aa_binary) != baseline_build["binary_sha256"]:
                    raise RuntimeError("A/A control is not byte-identical to the baseline")
            build_arms.update(
                {
                    "go-baseline-aa-left": {
                        **baseline_build,
                        "command": ["byte-identical copy", baseline_binary.name],
                        "binary": aa_left_binary.name,
                        "binary_bytes": aa_left_binary.stat().st_size,
                        "binary_sha256": sha256(aa_left_binary),
                        "derived_from": baseline_binary.name,
                    },
                    "go-baseline-aa-right": {
                        **baseline_build,
                        "command": ["byte-identical copy", baseline_binary.name],
                        "binary": aa_right_binary.name,
                        "binary_bytes": aa_right_binary.stat().st_size,
                        "binary_sha256": sha256(aa_right_binary),
                        "derived_from": baseline_binary.name,
                    },
                }
            )
        build_receipt = {
            "schema": "go-coordinator-remote-build/v1",
            "runner_sha256": sha256(Path(__file__).resolve()),
            "runner": {
                "engine": str(Path(__file__).resolve().relative_to(repo)),
                "engine_sha256": sha256(Path(__file__).resolve()),
                "binding": str(binding.relative_to(repo)) if binding is not None else None,
                "binding_sha256": sha256(binding) if binding is not None else None,
                "exporter": str(exporter.relative_to(repo)) if exporter is not None else None,
                "exporter_sha256": sha256(exporter) if exporter is not None else None,
                "analyzer": str(analyzer.relative_to(repo)) if analyzer is not None else None,
                "analyzer_sha256": sha256(analyzer) if analyzer is not None else None,
                "campaign": (
                    str(campaign_binding.relative_to(repo))
                    if campaign_binding is not None else None
                ),
                "campaign_sha256": (
                    sha256(campaign_binding) if campaign_binding is not None else None
                ),
                "l2_measure": (
                    str(l2_binding.relative_to(repo)) if l2_binding is not None else None
                ),
                "l2_measure_sha256": sha256(l2_binding) if l2_binding is not None else None,
                "support": [
                    {
                        "path": str(path.relative_to(repo)),
                        "sha256": sha256(path),
                    }
                    for path in support
                ],
                "retained": retained_tooling,
            },
            "mode": options.mode,
            "expected_cpu_flavor": options.expected_cpu_flavor,
            "host": initial_host,
            "placement": placement,
            "tools": tools,
            "toolchain": toolchain,
            "source_archive": source_archive,
            "sources": sources,
            "build_environment": go_environment,
            "build_environment_sha256": go_environment_digest,
            "arms": build_arms,
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
        set_stage("test_baseline")
        baseline_tests = run_tests(go, baseline_source, go_environment, tests / "baseline.txt")
        assert_affinity(expected_affinity)
        set_stage("test_candidate")
        candidate_tests = run_tests(go, candidate_source, go_environment, tests / "candidate.txt")
        assert_affinity(expected_affinity)
        write_json(
            tests / "manifest.json",
            {
                "schema": "go-coordinator-remote-tests/v1",
                "protocol_sha256": options.protocol_sha256,
                "build_environment": go_environment,
                "build_environment_sha256": go_environment_digest,
                "arms": {
                    "go-baseline": baseline_tests,
                    "go-candidate": candidate_tests,
                },
            },
        )

        before = host_snapshot()
        assert_affinity(expected_affinity, before["affinity"])
        campaign = output / "campaign"
        runner = (
            campaign_binding
            if campaign_binding is not None
            else Path(__file__).with_name("run_remote_campaign.py")
        )
        benchmark_cpu = placement["benchmark_cpus"][0]
        if ENABLE_AA_CONTROLS:
            assert aa_left_binary is not None and aa_right_binary is not None
            argv = [
                sys.executable, str(runner),
                "--out", str(campaign),
                "--phase", options.phase,
                "--protocol-sha256", options.protocol_sha256,
                "--baseline-binary", str(baseline_binary),
                "--baseline-sha256", baseline_campaign_sha,
                "--candidate-binary", str(candidate_binary),
                "--candidate-sha256", candidate_campaign_sha,
                "--aa-left-binary", str(aa_left_binary),
                "--aa-left-sha256", baseline_campaign_sha,
                "--aa-right-binary", str(aa_right_binary),
                "--aa-right-sha256", baseline_campaign_sha,
                "--warmups", "3", "--replicates", "20", "--cpu", str(benchmark_cpu),
                "--reserved-cpus", ",".join(
                    str(cpu) for cpu in placement["reservation_cpus"]
                ),
                "--expected-affinity", ",".join(str(cpu) for cpu in expected_affinity),
                "--timeout-seconds", "1800",
            ]
        else:
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
        set_stage("campaign_execution")
        campaign_process = subprocess.run(
            argv,
            cwd=repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        if campaign_process.stdout:
            print(campaign_process.stdout, end="")
        campaign_returncode = campaign_process.returncode
        set_stage("campaign_validation")
        after = host_snapshot()
        assert_affinity(expected_affinity, after["affinity"])
        rows = [
            json.loads(line) for line in (campaign / "rows.jsonl").read_text().splitlines() if line
        ]
        if campaign_returncode != 0:
            raise RuntimeError(
                f"campaign sealed a mechanical failure with return code {campaign_returncode}"
            )
        if len(rows) != 552 or any(row.get("status") != "completed" for row in rows):
            raise RuntimeError("campaign did not seal exactly 552 completed attempts")
        mismatch_counts = {"all_four_or_case_invariant": 0}
        for case in sorted({row["case"] for row in rows}):
            case_reference = None
            for warmup, replicates in ((True, range(1, 4)), (False, range(1, 21))):
                for replicate in replicates:
                    pair_rows = {
                        row["arm"]: row
                        for row in rows
                        if row["warmup"] is warmup
                        and row["case"] == case
                        and row["replicate"] == replicate
                    }
                    arms = (
                        "go-baseline", "go-candidate",
                        "go-baseline-aa-left", "go-baseline-aa-right",
                    )
                    if set(pair_rows) != set(arms) or not all(
                        item.get("status") == "completed"
                        and item.get("exit_status") == 0
                        and item.get("timed_out") is False
                        for item in (pair_rows[arm] for arm in arms)
                    ):
                        continue
                    fingerprints = [pair_rows[arm]["parsed"]["fingerprints"] for arm in arms]
                    if case_reference is None:
                        case_reference = fingerprints[0]
                    mismatch_counts["all_four_or_case_invariant"] += int(
                        any(value != fingerprints[0] for value in fingerprints[1:])
                        or any(value != case_reference for value in fingerprints)
                    )
        mismatches = mismatch_counts["all_four_or_case_invariant"]
        throttled_before = cgroup_counter(before["cpu_stat"], "nr_throttled")
        throttled_after = cgroup_counter(after["cpu_stat"], "nr_throttled")
        throttled_delta = (
            throttled_after - throttled_before
            if throttled_before is not None and throttled_after is not None else None
        )
        memory_event_deltas = counter_deltas(
            before["memory_events"], after["memory_events"]
        )
        placement_unchanged = stable_placement_unchanged(initial_host, before, after)
        if ENABLE_AA_CONTROLS:
            l2_failures = sum(not row.get("isolation", {}).get("passes", False) for row in rows)
            blocking: dict[str, int] = {}
            for row in rows:
                for name in row.get("isolation", {}).get("blocking", []):
                    blocking[name] = blocking.get(name, 0) + 1
            campaign_manifest = json.loads((campaign / "manifest.json").read_text())
            campaign_summary = json.loads((campaign / "summary.json").read_text())
            restoration = campaign_summary.get("restoration", {})
            timing_valid = (
                campaign_returncode == 0
                and len(rows) == 552
                and l2_failures == 0
                and restoration.get("passes") is True
                and before["steal_ticks"] == after["steal_ticks"]
                and throttled_delta == 0
                and memory_event_deltas is not None
                and all(delta == 0 for delta in memory_event_deltas.values())
                and placement_unchanged
            )
            isolation = {
                "schema": "go-coordinator-remote-isolation/v2",
                "required_level": "L2",
                "before": before,
                "after": after,
                "placement": placement,
                "preflight": campaign_manifest["preflight"],
                "l2_thresholds": campaign_manifest["l2_thresholds"],
                "session_lock": campaign_manifest["session_lock"],
                "restoration": restoration,
                "rows": len(rows),
                "rows_passing_l2": len(rows) - l2_failures,
                "rows_failing_l2": l2_failures,
                "l2_blocking_counts": dict(sorted(blocking.items())),
                "cgroup_nr_throttled_delta": throttled_delta,
                "memory_event_deltas": memory_event_deltas,
                "placement_unchanged": placement_unchanged,
                "fingerprint_pair_mismatches": mismatches,
                "fingerprint_mismatches_by_comparison": mismatch_counts,
                "timing_valid": timing_valid,
            }
        else:
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
            timing_valid = (
                campaign_returncode == 0 and steal_rows == 0
                and before["steal_ticks"] == after["steal_ticks"]
                and affinity_rows == 0 and pressure_rows == 0
                and throttled_delta == 0 and memory_event_deltas is not None
                and all(delta == 0 for delta in memory_event_deltas.values())
                and placement_unchanged
            )
            isolation = {
                "schema": "go-coordinator-remote-isolation/v1",
                "before": before, "after": after, "placement": placement,
                "rows": len(rows), "row_pressure_observations": len(rows) * 2,
                "rows_with_nonzero_steal_delta": steal_rows,
                "measured_rows_with_nonzero_steal_delta": measured_steal_rows,
                "rows_with_affinity_change": affinity_rows,
                "pressure_observations_failing_numeric_gate": pressure_rows,
                "pressure_gate": {"cpu_some_avg10_max": "10.0", "cpu_full_avg10": "0.0",
                                  "memory_some_avg10": "0.0", "memory_full_avg10": "0.0"},
                "cgroup_nr_throttled_delta": throttled_delta,
                "memory_event_deltas": memory_event_deltas,
                "placement_unchanged": placement_unchanged,
                "fingerprint_pair_mismatches": mismatches,
                "timing_valid": timing_valid,
            }
        write_json(output / "isolation.json", isolation)
        export_sha256 = None
        export_relative = None
        if exporter is not None and analyzer is not None:
            set_stage("canonical_export")
            export_path = campaign / "export.json"
            command(
                [
                    sys.executable,
                    str(exporter),
                    "--run",
                    str(output),
                    "--protocol-sha256",
                    options.protocol_sha256,
                    "--source-commit",
                    git(repo, "rev-parse", "HEAD"),
                    "--output",
                    str(export_path),
                ],
                cwd=repo,
            )
            export_sha256 = sha256(export_path)
            export_relative = str(export_path.relative_to(output))
        remote_summary = {
            "schema": "go-coordinator-remote-summary/v1",
            "status": "complete",
            "protocol_sha256": options.protocol_sha256,
            "build_manifest_sha256": sha256(build_dir / "manifest.json"),
            "tests_manifest_sha256": sha256(tests / "manifest.json"),
            "campaign_rows_sha256": sha256(campaign / "rows.jsonl"),
            "isolation_sha256": sha256(output / "isolation.json"),
            "fingerprint_pair_mismatches": mismatches,
            "fingerprint_mismatches_by_comparison": mismatch_counts,
            "campaign_returncode": campaign_returncode,
            "timing_valid": timing_valid,
        }
        if OUTPUT_BUDGET_BYTES is not None:
            if type(OUTPUT_BUDGET_BYTES) is not int or OUTPUT_BUDGET_BYTES <= 0:
                raise RuntimeError("output budget must be a positive integer")
            pre_summary = tree_inventory(output, exclude={"remote-summary.json"})
            if pre_summary["bytes"] + REMOTE_SUMMARY_RESERVE_BYTES > OUTPUT_BUDGET_BYTES:
                raise RuntimeError("scientific output exceeds the frozen byte budget")
            remote_summary.update(
                {
                    "output_budget_bytes": OUTPUT_BUDGET_BYTES,
                    "output_bytes_before_summary": pre_summary["bytes"],
                    "output_files_before_summary": pre_summary["files"],
                    "remote_summary_reserve_bytes": REMOTE_SUMMARY_RESERVE_BYTES,
                }
            )
        if export_sha256 is not None:
            remote_summary.update(
                {
                    "export_path": export_relative,
                    "export_sha256": export_sha256,
                }
            )
        write_json(
            output / "remote-summary.json",
            remote_summary,
        )
        if OUTPUT_BUDGET_BYTES is not None and tree_inventory(output)["bytes"] > OUTPUT_BUDGET_BYTES:
            raise RuntimeError("sealed scientific output exceeds the frozen byte budget")
        if mismatches and campaign_returncode == 0:
            return 1
        return campaign_returncode
    return 0


def seal_failure(options: argparse.Namespace, error: BaseException) -> None:
    """Seal a canonical export and summary for an owned failed invocation."""

    output = options.out.resolve()
    repo = Path(__file__).resolve().parents[3]
    exporter = Path(EXPORTER_PATH).resolve() if EXPORTER_PATH else None
    if (
        options.mode not in {"run", "combined"}
        or exporter is None
        or options.protocol_sha256 is None
        or re.fullmatch(r"[0-9a-f]{64}", options.protocol_sha256) is None
    ):
        return
    source_commit = CURRENT_SOURCE_COMMIT
    if source_commit is None or re.fullmatch(r"[0-9a-f]{40}", source_commit) is None:
        raise RuntimeError("authenticated source commit is unavailable for failure sealing")
    failure_path = output / "failure.json"
    failure = {
        "schema": "go-coordinator-remote-failure/v1",
        "protocol_sha256": options.protocol_sha256,
        "source_commit": source_commit,
        "phase": options.phase,
        "stage": CURRENT_STAGE,
        "error": {
            "type": type(error).__name__,
            "detail": str(error)[:2048],
        },
        "usable_prefix_rows": None,
    }
    write_json(failure_path, failure)
    campaign = output / "campaign"
    campaign.mkdir(parents=True, exist_ok=True)
    export_path = campaign / "export.json"
    if export_path.exists():
        export_path.replace(campaign / "pre-failure-export.json")
    prior_summary = output / "remote-summary.json"
    if prior_summary.exists():
        prior_summary.replace(output / "pre-failure-remote-summary.json")
    result = subprocess.run(
        [
            sys.executable,
            str(exporter),
            "--run",
            str(output),
            "--protocol-sha256",
            options.protocol_sha256,
            "--source-commit",
            source_commit,
            "--output",
            str(export_path),
            "--failure-record",
            str(failure_path),
        ],
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    if result.returncode != 0 or not export_path.is_file():
        raise RuntimeError("canonical failure export could not be sealed: " + result.stdout)
    # The exporter updates the receipt with its authenticated usable-prefix count.
    failure = json.loads(failure_path.read_text(encoding="utf-8"))
    summary = {
        "schema": "go-coordinator-remote-summary/v1",
        "status": "mechanical_failure",
        "protocol_sha256": options.protocol_sha256,
        "source_commit": source_commit,
        "failure_path": "failure.json",
        "failure_sha256": sha256(failure_path),
        "failure_stage": failure["stage"],
        "usable_prefix_rows": failure["usable_prefix_rows"],
        "export_path": "campaign/export.json",
        "export_sha256": sha256(export_path),
        "remote_returncode": 2,
        "claims_evaluated": False,
    }
    if OUTPUT_BUDGET_BYTES is not None:
        pre_summary = tree_inventory(output, exclude={"remote-summary.json"})
        if pre_summary["bytes"] + REMOTE_SUMMARY_RESERVE_BYTES > OUTPUT_BUDGET_BYTES:
            raise RuntimeError("failure evidence exceeds the frozen output byte budget")
        summary.update(
            {
                "output_budget_bytes": OUTPUT_BUDGET_BYTES,
                "output_bytes_before_summary": pre_summary["bytes"],
                "output_files_before_summary": pre_summary["files"],
                "remote_summary_reserve_bytes": REMOTE_SUMMARY_RESERVE_BYTES,
            }
        )
    write_json(output / "remote-summary.json", summary)
    if OUTPUT_BUDGET_BYTES is not None and tree_inventory(output)["bytes"] > OUTPUT_BUDGET_BYTES:
        raise RuntimeError("sealed failure evidence exceeds the frozen output byte budget")


def main() -> int:
    options = arguments()
    output_preexisted = options.out.exists()
    previous_term = signal.signal(signal.SIGTERM, abort_on_signal)
    try:
        return run(options)
    except BaseException as error:
        if not output_preexisted:
            if options.out.exists():
                try:
                    seal_failure(options, error)
                except BaseException as sealing_error:
                    print(
                        f"fatal: workflow failed and failure sealing failed: {sealing_error}",
                        file=sys.stderr,
                    )
                    return 3
                print(
                    f"mechanical failure sealed at stage {CURRENT_STAGE}: "
                    f"{type(error).__name__}: {error}",
                    file=sys.stderr,
                )
            else:
                print(
                    f"mechanical failure before output publication at stage {CURRENT_STAGE}: "
                    f"{type(error).__name__}: {error}",
                    file=sys.stderr,
                )
            return 2
        raise
    finally:
        signal.signal(signal.SIGTERM, previous_term)


if __name__ == "__main__":
    sys.exit(main())
