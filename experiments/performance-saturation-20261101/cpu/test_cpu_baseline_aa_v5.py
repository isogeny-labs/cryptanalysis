#!/usr/bin/env python3
"""Synthetic-only adversarial tests for CPU baseline A/A v5."""

from __future__ import annotations

import hashlib
import json
import multiprocessing
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import analyze_cpu_baseline_aa_v5 as analyzer
import python_bootstrap_v5 as bootstrap

runner = analyzer.runner

T0 = "2026-11-01T00:00:00+00:00"
T1 = "2026-11-01T00:00:01+00:00"
PROTOCOL_DRAFT = Path(__file__).with_name("protocol-baseline-aa-orchestrated-v5.json")


def dump(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


def jsonl(path: Path, values: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(v, sort_keys=True) + "\n" for v in values), encoding="utf-8")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def registries(language: str) -> list[dict]:
    rows = analyzer.load_jsonl(runner.V4_ROOT / f"registry/{language}.jsonl")
    return [r for r in rows if r.get("tier") == "Quick"] if language == "rust" else rows


def system_snapshot(label: str, tick: int = 1) -> dict:
    return {
        "schema": "cpu-baseline-aa-v5-system-snapshot/v1", "label": label,
        "captured_at": T0 if label == "before" else T1,
        "platform": "synthetic", "uname": ["synthetic"],
        "affinity": [0, 1, 2, 3, 4], "online_cpus": "0-4\n",
        "smt_active": None, "smt_control": None, "numa_online": "0\n",
        "microcode": [], "governors": {}, "frequencies": {},
        "loadavg": "0 0 0 1/1 1\n", "proc_meminfo": "MemTotal: 1024 kB\n",
        "proc_interrupts": "synthetic\n", "proc_softirqs": "synthetic\n",
        "proc_stat": (
            f"cpu {tick} 0 0 10 0 0 0 0\n"
            f"intr {tick}\nctxt {tick}\nsoftirq {tick}\nprocesses {tick}\n"
        ),
        "pressure": {
            "cpu": f"some avg10=0 avg60=0 avg300=0 total={tick}\n",
            "io": f"some avg10=0 avg60=0 avg300=0 total={tick}\nfull avg10=0 avg60=0 avg300=0 total={tick}\n",
            "memory": f"some avg10=0 avg60=0 avg300=0 total={tick}\nfull avg10=0 avg60=0 avg300=0 total={tick}\n",
        },
        "self_cgroup": "0::/synthetic\n", "cgroup_path": "/sys/fs/cgroup/synthetic",
        "cgroup": {
            "cpu.stat": f"usage_usec {tick}\nnr_throttled 0\nthrottled_usec 0\n",
            "memory.events": "low 0\nhigh 0\nmax 0\noom 0\noom_kill 0\n",
            "cpu.max": "max 100000\n", "cpuset.cpus.effective": "0-4\n",
            "cpuset.mems.effective": "0\n", "memory.high": "max\n",
            "memory.max": "max\n", "memory.swap.max": "max\n", "pids.max": "max\n",
        },
    }


def boundaries(
    root: Path, protocol: dict | None = None, blocked_path: Path | None = None,
) -> list[str]:
    runtime = {
        "event_sources": ["breakpoint", "msr", "software"],
        "event_sources_error": None, "perf_event_paranoid": "2",
        "online_cpus": "0-4", "v4_affected_paths_present": [],
    }
    inventory = runner.identity_inventory(protocol) if protocol is not None else []
    if blocked_path is not None:
        for item in inventory:
            if item.get("path") == str(blocked_path):
                item.update({"exists": False, "bytes": None, "sha256": None, "mode": None})
    findings = runner.identity_findings(protocol, inventory, runtime) if protocol is not None else []
    dump(root / "orchestration/preflight.json", {
        "schema": "cpu-baseline-aa-v5-preflight/v1", "checked_at": T0,
        "status": "passed" if not findings else "blocked_identity_mismatch",
        "findings": findings, "required_files": inventory,
        "runtime_observations": runtime,
    })
    for label in ("before", "wall-after", "campaign-after"):
        dump(root / f"orchestration/identity-{label}.json", {
            "schema": "cpu-baseline-aa-v5-identity-snapshot/v1", "label": label,
            "captured_at": T0 if label == "before" else T1,
            "required_files": inventory,
        })
        dump(root / f"orchestration/system-{label}.json", system_snapshot(label))
    return findings


def frozen_protocol(root: Path) -> tuple[Path, dict]:
    protocol = json.loads(PROTOCOL_DRAFT.read_text(encoding="utf-8"))
    plan = runner.build_plan()
    protocol["extensions"]["cpu_baseline_aa_v5"]["runner_sha256"] = digest(runner.RUNNER)
    protocol["extensions"]["cpu_baseline_aa_v5"]["analyzer_sha256"] = digest(runner.ANALYZER)
    protocol["extensions"]["cpu_baseline_aa_v5"]["command_plan_digests"] = plan["digests"]
    protocol["analysis_plan"]["script"]["sha256"] = digest(Path(analyzer.__file__).resolve())
    for item in protocol["extensions"]["cpu_baseline_aa_v5"]["required_files"]:
        path = Path(item["path"])
        if path in {runner.RUNNER, runner.ANALYZER}:
            item.update({
                "bytes": path.stat().st_size,
                "mode": f"{path.stat().st_mode & 0o7777:04o}",
                "sha256": digest(path),
            })
    protocol["freeze"] = {
        "status": "frozen", "protocol_sha256": None,
        "commit": "0" * 40, "frozen_at": "2026-11-01T00:00:00Z",
        "filed_before_affected_data": True,
    }
    protocol["freeze"]["protocol_sha256"] = analyzer.tool.protocol_hash(protocol)
    path = root.parent / "protocol.json"
    dump(path, protocol)
    return path, protocol


def campaign_start(root: Path, protocol: dict) -> dict:
    plan = runner.build_plan()
    plan_path = root / "orchestration/command-plan.json"
    dump(plan_path, plan)
    dump(root / "orchestration/start.json", {
        "schema": "cpu-baseline-aa-v5-start/v1", "started_at": T0,
        "protocol_path": str(root.parent / "protocol.json"),
        "protocol_sha256": protocol["freeze"]["protocol_sha256"],
        "plan_sha256": digest(plan_path),
        "plan_preimage_sha256": plan["digests"]["plan_preimage"],
        "controller_entry": runner.expected_bootstrap_entry(
            "base", runner.RUNNER,
            [
                "run", "--protocol", str(root.parent / "protocol.json"),
                "--confirm-other-cpu-work-paused",
            ],
        ),
        "other_cpu_work_paused_confirmed": True, "resume_policy": "forbidden",
    })
    return plan


def failed_outer_attempt(root: Path, name: str, record: dict) -> None:
    outer = root / "orchestration/attempts" / name
    outer.mkdir(parents=True)
    (outer / "stdout.txt").write_text("", encoding="utf-8")
    (outer / "stderr.txt").write_text("synthetic diagnostic failure\n", encoding="utf-8")
    dump(outer / "started.json", {
        "schema": "cpu-baseline-aa-v5-attempt-start/v1", "record": record,
        "started_at": T0,
    })
    dump(outer / "launched.json", {
        "schema": "cpu-baseline-aa-v5-attempt-launch/v1", "record": record,
        "started_at": T0, "pid": 2000 + int(record.get("ordinal", 1)),
        "process_group": 2000 + int(record.get("ordinal", 1)),
    })
    dump(outer / "receipt.json", {
        "schema": "cpu-baseline-aa-v5-attempt/v1", "record": record,
        "started_at": T0, "finished_at": T1, "returncode": 1,
        "launch_error": None, "timeout_error": None,
        "stdout_sha256": digest(outer / "stdout.txt"),
        "stderr_sha256": digest(outer / "stderr.txt"),
    })
    jsonl(analyzer.isolation_path(record), [{
        "schema": "isolated-bench/1", "mode": "reserve",
        "label": record["argv"][record["argv"].index("--label") + 1],
        "reserved_cpus": [0, 1, 2, 3], "left_on_reserved": {},
        "command": analyzer.child_argv(record), "exit_status": 1,
        "contended_samples": 0, "samples": [],
    }])


def invoke_analyzer(protocol_path: Path, root: Path) -> int:
    argv = [
        str(Path(analyzer.__file__).resolve()), "--protocol", str(protocol_path),
        "--run-root", str(root),
    ]
    with mock.patch.object(sys, "argv", argv), mock.patch.object(
        runner, "require_closed_bootstrap",
    ):
        return analyzer.main()


def concurrent_analyzer_worker(
    protocol_path: Path, root: Path, barrier: object, results: object,
    publication_log: Path,
) -> None:
    """Run one real analyzer contender and record every derived publication."""
    runner.RUN_ROOT = root
    original_publish = analyzer.atomic_publish

    def traced_publish(path: Path, data: bytes) -> None:
        descriptor = os.open(
            publication_log, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600,
        )
        try:
            os.write(descriptor, f"{os.getpid()}\t{path}\n".encode("utf-8"))
        finally:
            os.close(descriptor)
        original_publish(path, data)

    analyzer.atomic_publish = traced_publish
    try:
        barrier.wait(timeout=60)
        results.put(("ok", os.getpid(), invoke_analyzer(protocol_path, root)))
    except BaseException as error:
        results.put(("error", os.getpid(), f"{type(error).__name__}: {error}"))
        raise
    finally:
        analyzer.atomic_publish = original_publish


def assert_canonical_export(test: unittest.TestCase, protocol_path: Path,
                            protocol: dict, root: Path) -> None:
    export = analyzer.load_json(root / "export.json")
    test.assertEqual(analyzer.tool.schema_errors(export, "experiment.export/v1"), [])
    test.assertEqual(analyzer.tool.lint_export(export, protocol, root, True), [])
    checked = subprocess.run(
        runner.closed_python_command(
            runner.PROTOCOL_TOOL, "check-export", "--protocol", str(protocol_path),
            "--verify-files", str(root / "export.json"),
        ),
        cwd=root, capture_output=True, text=True, timeout=60,
    )
    test.assertEqual(checked.returncode, 0, checked.stderr)


def measured_row(kernel: str, round_index: int) -> dict:
    return {
        "id": kernel, "fingerprint": f"fingerprint:{kernel}",
        "median_ns": 1000, "samples_ns": [900, 1000, 1100], "round": round_index,
    }


def inner_attempt(compare: Path, spec: dict, sequence: int, round_index: int,
                  kernel: str, arm: str, finish: bool = True) -> tuple[dict, dict | None]:
    binary = runner.RUST_BINARY if spec["language"] == "rust" else runner.C_BINARY
    argv = [
        str(runner.TASKSET), "-c", "0" if spec["panel"] == "1t" else "0-3",
        str(binary), "run", "--filter", kernel, "--exact", "--samples", "5",
        "--max-seconds", "2.0",
    ]
    stem = f"{sequence:04d}_{arm}_{runner.safe_id(kernel)}"
    start = {
        "schema": "cpu-baseline-aa-v5-wall-attempt-start/v1", "event": "started",
        "sequence": sequence, "session": spec["id"], "round": round_index,
        "kernel": kernel, "arm": arm, "argv": argv, "started_at": T0,
    }
    dump(compare / f"attempts/{stem}.started.json", start)
    if not finish:
        return start, None
    row = measured_row(kernel, round_index)
    stdout_row = dict(row)
    stdout_row.pop("round")
    receipt = {
        "schema": "cpu-baseline-aa-v5-wall-attempt/v1", "event": "finished",
        "sequence": sequence, "session": spec["id"], "round": round_index,
        "kernel": kernel, "arm": arm, "argv": argv, "started_at": T0,
        "finished_at": T1, "child_returncode": 0, "effective_returncode": 0,
        "timed_out": False, "parse_error": None,
        "stdout": json.dumps(stdout_row) + "\n", "stderr": "", "row": row,
    }
    dump(compare / f"attempts/{stem}.json", receipt)
    return start, receipt


def full_session(root: Path, index: int, spec: dict) -> None:
    record = runner.build_plan()["wall"][index - 1]
    outer = root / f"orchestration/attempts/wall-{index:02d}-{spec['id']}"
    outer.mkdir(parents=True)
    (outer / "stdout.txt").write_text("", encoding="utf-8")
    lines = []
    for item in analyzer.expected_schedule(spec["ids"]):
        arms = " ".join(f"{arm}=0.001ms" for arm in item["arms"])
        lines.append(f"round {item['round']}/6 {item['id']}: {arms}")
    (outer / "stderr.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    dump(outer / "started.json", {
        "schema": "cpu-baseline-aa-v5-attempt-start/v1", "record": record,
        "started_at": T0,
    })
    dump(outer / "launched.json", {
        "schema": "cpu-baseline-aa-v5-attempt-launch/v1", "record": record,
        "started_at": T0, "pid": 1000 + index, "process_group": 1000 + index,
    })
    dump(outer / "receipt.json", {
        "schema": "cpu-baseline-aa-v5-attempt/v1", "record": record,
        "started_at": T0, "finished_at": T1, "returncode": 0,
        "launch_error": None, "timeout_error": None,
        "stdout_sha256": digest(outer / "stdout.txt"),
        "stderr_sha256": digest(outer / "stderr.txt"),
    })
    jsonl(analyzer.isolation_path(record), [{
        "schema": "isolated-bench/1", "mode": "reserve",
        "label": record["argv"][record["argv"].index("--label") + 1],
        "reserved_cpus": [0, 1, 2, 3], "left_on_reserved": {},
        "command": analyzer.child_argv(record), "exit_status": 0,
        "contended_samples": 0, "samples": [],
    }])

    compare = root / f"wall-{spec['panel']}/{spec['language']}/compare"
    rows = registries(spec["language"])
    binary = runner.RUST_BINARY if spec["language"] == "rust" else runner.C_BINARY
    binary_hash = runner.RUST_BINARY_SHA256 if spec["language"] == "rust" else runner.C_BINARY_SHA256
    registry_hash = runner.RUST_REGISTRY_SHA256 if spec["language"] == "rust" else runner.C_REGISTRY_SHA256
    threads = 1 if spec["panel"] == "1t" else 4
    environment = runner.wall_environment(threads)
    dump(compare / "session-start.json", {
        "schema": "cpu-baseline-aa-v5-wall-session-start/v1", "session": spec["id"],
        "binary": str(binary), "binary_sha256": binary_hash,
        "environment": environment, "environment_error": None,
        "registry_sha256": registry_hash, "perfindex_sha256": runner.PERFINDEX_SHA256,
        "started_at": T0,
    })
    list_argv = [str(binary), "list"] + (["--full"] if spec["language"] == "c" else [])
    for ordinal, role in enumerate(("base", "cand"), 1):
        dump(compare / f"prelude/{ordinal:02d}-{role}.started.json", {
            "schema": "cpu-baseline-aa-v5-registry-prelude-start/v1",
            "ordinal": ordinal, "role": role, "argv": list_argv, "started_at": T0,
        })
        dump(compare / f"prelude/{ordinal:02d}-{role}.json", {
            "schema": "cpu-baseline-aa-v5-registry-prelude/v1",
            "ordinal": ordinal, "role": role, "argv": list_argv,
            "started_at": T0, "finished_at": T1,
            "child_returncode": 0, "effective_returncode": 0,
            "timed_out": False, "parse_error": None,
            "stdout": "".join(json.dumps(row) + "\n" for row in rows),
            "stderr": "", "rows": rows,
        })
    host = analyzer.load_json(
        runner.V4_ROOT / (
            "build/base-rust/build.json" if spec["language"] == "rust"
            else "build/base-c/build.json"
        )
    )["host"]
    dump(compare / "session.json", {
        "schema": "cpu-baseline-aa-v5-wall-session/v1", "session": spec["id"],
        "binary": str(binary), "binary_sha256": binary_hash,
        "threads": threads, "taskset": "0" if threads == 1 else "0-3",
        "rounds": 6, "samples": 5, "max_seconds": 2.0,
        "invocation_timeout_seconds": 1800,
        "schedule_sha256": runner.digest_value(runner.wall_schedule(spec["id"])),
        "environment": environment, "host": host,
        "registry_sha256": registry_hash, "perfindex_sha256": runner.PERFINDEX_SHA256,
    })
    raw = {kernel: {"A": [], "B": [], "A2": []} for kernel in spec["ids"]}
    starts: list[dict] = []
    finishes: list[dict] = []
    events: list[dict] = []
    sequence = 0
    for item in runner.wall_schedule(spec["id"]):
        for arm in item["arms"]:
            sequence += 1
            start, finish = inner_attempt(
                compare, spec, sequence, item["round"], item["kernel"], arm,
            )
            starts.append(start)
            finishes.append(finish)
            events.extend((start, finish))
            raw[item["kernel"]][arm].append(finish["row"])
    jsonl(compare / "attempts.jsonl", finishes)
    jsonl(compare / "events.jsonl", events)
    registry = {row["id"]: row for row in rows}
    kernels = [registry[kernel] for kernel in sorted(spec["ids"])]
    rng = random.Random(20260926)
    for _ in range(6):
        order = kernels[:]
        rng.shuffle(order)
    weights = json.loads(analyzer.WEIGHTS_PATH.read_text(encoding="utf-8"))["areas"]
    summary = analyzer.load_frozen_perfindex().summarize(kernels, raw, weights, rng)
    summary.update({
        "mode": "wall", "unit": "ms", "base": str(binary), "cand": str(binary),
        "threads": threads, "samples_per_invocation": 5, "host": host, "raw": raw,
    })
    dump(compare / "compare.json", summary)
    dump(compare / "session-end.json", {
        "schema": "cpu-baseline-aa-v5-wall-session-end/v1", "session": spec["id"],
        "finished_at": T1, "binary_sha256": binary_hash,
        "registry_sha256": registry_hash, "perfindex_sha256": runner.PERFINDEX_SHA256,
        "completed_invocations": sequence,
    })


class CpuBaselineAaV5Tests(unittest.TestCase):
    def test_schedule_and_profile_order(self) -> None:
        self.assertEqual(
            analyzer.canonical_sha256(analyzer.expected_schedule(runner.RUST_IDS)),
            analyzer.RUST_SCHEDULE_SHA256,
        )
        self.assertEqual(
            analyzer.canonical_sha256(analyzer.expected_schedule(runner.C_IDS)),
            analyzer.C_SCHEDULE_SHA256,
        )
        plan = runner.build_plan()
        callgrind_pairs = [(kernel, arm) for kernel in runner.PROFILE_IDS for arm in ("A", "B")]
        perf_pairs = [(kernel, arm) for kernel in runner.ALL_IDS for arm in ("A", "B")]
        self.assertEqual([(row["kernel"], row["arm"]) for row in plan["callgrind"]], callgrind_pairs)
        self.assertEqual([(row["kernel"], row["arm"]) for row in plan["perf_stat"]], perf_pairs)
        self.assertEqual(plan["counts"], {
            "wall_sessions": 4, "callgrind_attempts": 88,
            "perf_stat_attempts": 88, "perf_record_attempts": 8,
        })
        self.assertEqual(len({row["output"] for row in plan["callgrind"]}), 88)
        self.assertEqual(len({row["output"] for row in plan["perf_stat"]}), 88)
        self.assertEqual(len(plan["callgrind_inner"]), 88)
        self.assertEqual(
            plan["digests"]["callgrind_inner"],
            runner.digest_value(plan["callgrind_inner"]),
        )
        self.assertEqual(
            [len(row["registry_preludes"]) for row in plan["callgrind_inner"]].count(2),
            2,
        )
        seed_table = runner.export_seed_table()
        self.assertEqual(len(seed_table), 1056)
        self.assertEqual({row["replicate"] for row in seed_table}, set(range(1, 7)))
        self.assertEqual({row["instance_id"] for row in seed_table}, set(runner.ALL_IDS))
        self.assertEqual(plan["export_seed_table"]["sha256"], runner.digest_value(seed_table))
        self.assertEqual(plan["digests"], runner.build_plan()["digests"])
        for row in [*plan["wall"], *plan["callgrind"]]:
            self.assertIn(str(runner.DASH), row["argv"])
            self.assertIn(str(runner.PYTHON_PREFLIGHT), row["argv"])
            self.assertNotIn(str(runner.PYTHON), row["argv"])
        for row in plan["callgrind"]:
            self.assertEqual(
                analyzer.child_argv(row)[:4],
                [str(runner.TASKSET), "-c", "0", str(runner.SYSTEM_ENV)],
            )

    def test_runtime_dependency_manifest_is_content_bound(self) -> None:
        protocol = json.loads(PROTOCOL_DRAFT.read_text(encoding="utf-8"))
        manifest = runner.load_dependency_manifest(protocol)
        contract = protocol["extensions"]["cpu_baseline_aa_v5"][
            "runtime_dependency_manifest"
        ]
        self.assertEqual(len(manifest["files"]), contract["file_count"])
        self.assertEqual(runner.digest_value(manifest["files"]), contract["entries_sha256"])
        inventory = runner.identity_inventory(protocol)
        runtime_item = next(
            item for item in inventory if item.get("scope") == "runtime_dependency"
        )
        runtime_item["sha256"] = "0" * 64
        findings = runner.identity_findings(
            protocol, inventory, runner.runtime_identity_observations(),
        )
        self.assertIn(
            "runtime dependency inventory differs from the frozen manifest", findings,
        )

    def test_analyzer_identity_bindings_must_all_equal_observed_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "run"
            protocol_path, baseline = frozen_protocol(root)
            mutations = {
                "extension": lambda value: value["extensions"]["cpu_baseline_aa_v5"].__setitem__(
                    "analyzer_sha256", "1" * 64,
                ),
                "analysis-plan": lambda value: value["analysis_plan"]["script"].__setitem__(
                    "sha256", "2" * 64,
                ),
                "required-file": lambda value: next(
                    item for item in value["extensions"]["cpu_baseline_aa_v5"]["required_files"]
                    if item["path"] == str(runner.ANALYZER)
                ).__setitem__("sha256", "3" * 64),
                "duplicate-required-file": lambda value: value["extensions"]
                ["cpu_baseline_aa_v5"]["required_files"].append({
                    **next(
                        item for item in value["extensions"]["cpu_baseline_aa_v5"]
                        ["required_files"] if item["path"] == str(runner.ANALYZER)
                    ),
                    "sha256": "4" * 64,
                }),
            }
            for label, mutate in mutations.items():
                with self.subTest(binding=label):
                    protocol = json.loads(json.dumps(baseline))
                    mutate(protocol)
                    protocol["freeze"]["protocol_sha256"] = None
                    protocol["freeze"]["protocol_sha256"] = analyzer.tool.protocol_hash(protocol)
                    dump(protocol_path, protocol)
                    with self.assertRaisesRegex(RuntimeError, "analyzer identities differ"):
                        runner.validate_protocol(protocol_path)
                    with self.assertRaisesRegex(ValueError, "analyzer identities differ"):
                        analyzer.verify_protocol(protocol_path)

    def test_closed_python_preflight_rejects_preimport_tamper(self) -> None:
        checked = subprocess.run(
            runner.closed_python_command(
                runner.PROTOCOL_TOOL, "hash", str(PROTOCOL_DRAFT),
            ),
            cwd=runner.REPO, capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(checked.returncode, 0, checked.stderr)
        self.assertRegex(checked.stdout.strip(), r"^[0-9a-f]{64}$")
        direct = subprocess.run(
            runner.clean_env() + [
                str(runner.PYTHON), "-S", "-B", "-P", "-X",
                "pycache_prefix=/dev/null", str(runner.PYTHON_BOOTSTRAP),
                "base", str(runner.PROTOCOL_TOOL), "hash", str(PROTOCOL_DRAFT),
            ],
            cwd=runner.REPO, capture_output=True, text=True, timeout=60,
        )
        self.assertNotEqual(direct.returncode, 0)
        self.assertIn("environment differs", direct.stderr)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dependency = root / "dependency.py"
            dependency.write_text("trusted = True\n", encoding="utf-8")
            closure = root / "closure.sha256"
            closure.write_text(
                f"{digest(dependency)}  {dependency}\n", encoding="ascii",
            )
            source = runner.PYTHON_PREFLIGHT.read_text(encoding="utf-8")
            source = source.replace(
                f"manifest={runner.PYTHON_CLOSURE}", f"manifest={closure}",
            ).replace(
                "expected_manifest_sha256="
                + digest(runner.PYTHON_CLOSURE),
                "expected_manifest_sha256=" + digest(closure),
            )
            preflight = root / "preflight.sh"
            preflight.write_text(source, encoding="utf-8")
            dependency.write_text("trusted = False\n", encoding="utf-8")
            failed = subprocess.run(
                runner.clean_env() + [
                    str(runner.DASH), str(preflight), "base",
                    str(runner.PROTOCOL_TOOL), "hash", str(PROTOCOL_DRAFT),
                ],
                cwd=runner.REPO, capture_output=True, text=True, timeout=60,
            )
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn("did NOT match", failed.stderr)
            self.assertNotIn("not allow-listed", failed.stderr)

    def test_closed_import_routes_reject_shadow_and_optional_activation(self) -> None:
        expected = runner.PYTHON_IMPORT_INVENTORY.read_text(encoding="utf-8").splitlines()
        self.assertEqual(bootstrap.import_inventory(), expected)
        closure_paths = {
            line.split("  ", 1)[1]
            for line in runner.PYTHON_CLOSURE.read_text(encoding="utf-8").splitlines()
            if line
        }
        executable_inventory = {
            row.split("\t", 1)[1] for row in expected
            if row.startswith(("P\t", "F\t"))
        }
        self.assertTrue(executable_inventory.issubset(closure_paths))
        self.assertFalse(any(row.startswith(("A\t", "L\t", "X\t")) for row in expected))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stdlib = root / "stdlib"
            site = root / "site"
            package = site / "jsonschema"
            package.mkdir(parents=True)
            stdlib.mkdir()
            (stdlib / "json.py").write_text("value = 1\n", encoding="utf-8")
            (package / "__init__.py").write_text("value = 1\n", encoding="utf-8")
            (site / "typing_extensions.py").write_text("value = 1\n", encoding="utf-8")
            baseline = bootstrap.import_inventory(
                str(stdlib), str(site), ("jsonschema",), ("typing_extensions.py",),
            )
            self.assertTrue(any(row.startswith("D\t") for row in baseline))
            empty = package / "empty-routing-node"
            empty.mkdir()
            with_empty_directory = bootstrap.import_inventory(
                str(stdlib), str(site), ("jsonschema",), ("typing_extensions.py",),
            )
            self.assertNotEqual(with_empty_directory, baseline)
            empty.rmdir()

            target_a = root / "optional-a"
            target_b = root / "optional-b"
            for target in (target_a, target_b):
                target.mkdir()
                (target / "__init__.py").write_text("value = 7\n", encoding="utf-8")
            stdlib_link = stdlib / "cpu_v5_optional"
            package_link = package / "optional"
            stdlib_link.symlink_to(target_a, target_is_directory=True)
            package_link.symlink_to(target_a, target_is_directory=True)
            from importlib.machinery import PathFinder
            self.assertIsNotNone(PathFinder.find_spec("cpu_v5_optional", [str(stdlib)]))
            self.assertIsNotNone(PathFinder.find_spec("jsonschema.optional", [str(package)]))
            linked = bootstrap.import_inventory(
                str(stdlib), str(site), ("jsonschema",), ("typing_extensions.py",),
            )
            self.assertNotEqual(linked, baseline)
            self.assertTrue(any(
                row.startswith("L\t") and str(stdlib_link) in row for row in linked
            ))
            self.assertTrue(any(
                row.startswith("L\t") and str(package_link) in row for row in linked
            ))
            stdlib_link.unlink()
            stdlib_link.symlink_to(target_b, target_is_directory=True)
            retargeted = bootstrap.import_inventory(
                str(stdlib), str(site), ("jsonschema",), ("typing_extensions.py",),
            )
            self.assertNotEqual(retargeted, linked)
            self.assertTrue(any(
                row.startswith("L\t") and str(target_b) in row for row in retargeted
            ))
            package_link.unlink()
            package_link.symlink_to(target_b, target_is_directory=True)
            package_retargeted = bootstrap.import_inventory(
                str(stdlib), str(site), ("jsonschema",), ("typing_extensions.py",),
            )
            self.assertNotEqual(package_retargeted, retargeted)
            stdlib_link.unlink()
            package_link.unlink()

            (package / "rogue.py").write_text("value = 2\n", encoding="utf-8")
            nested_extra = bootstrap.import_inventory(
                str(stdlib), str(site), ("jsonschema",), ("typing_extensions.py",),
            )
            self.assertNotEqual(nested_extra, baseline)
            (site / "jsonschema.py").write_text("value = 3\n", encoding="utf-8")
            alternate = bootstrap.import_inventory(
                str(stdlib), str(site), ("jsonschema",), ("typing_extensions.py",),
            )
            self.assertTrue(any(row.startswith("A\t") for row in alternate))

            marker = root / "shadow-loaded"
            shadow = (
                "from pathlib import Path\n"
                f"Path({str(marker)!r}).write_text('loaded')\n"
            )
            (root / "json.py").write_text(shadow, encoding="utf-8")
            (root / "fqdn.py").write_text(shadow, encoding="utf-8")
            checked = subprocess.run(
                runner.closed_python_command(
                    runner.PROTOCOL_TOOL, "hash", str(PROTOCOL_DRAFT),
                ),
                cwd=root, capture_output=True, text=True, timeout=60,
            )
            self.assertEqual(checked.returncode, 0, checked.stderr)
            self.assertFalse(marker.exists())

        planned = subprocess.run(
            runner.closed_python_command(runner.RUNNER, "plan"),
            cwd=runner.REPO, capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(planned.returncode, 0, planned.stderr)
        self.assertEqual(json.loads(planned.stdout)["schema"], "cpu-baseline-aa-v5-command-plan/v1")

    def test_profiler_configuration_sources_are_closed(self) -> None:
        callgrind = runner.callgrind_inner_argv(runner.RUST_BINARY, runner.RUST_IDS[0])
        self.assertIn("--command-line-only=yes", callgrind)
        baseline_plan = runner.build_plan()
        with mock.patch.dict(os.environ, {
            "HOME": "/tmp/untrusted-home", "VALGRIND_OPTS": "--tool=none",
            "PERF_CONFIG": "/tmp/untrusted-perfconfig",
        }, clear=False):
            plan = runner.build_plan()
        with tempfile.TemporaryDirectory() as hostile_directory:
            hostile = Path(hostile_directory)
            (hostile / ".valgrindrc").write_text("--tool=none\n", encoding="utf-8")
            (hostile / ".perfconfig").write_text("[ui]\nshow-headers=false\n", encoding="utf-8")
            with mock.patch.object(runner, "REPO", hostile):
                hostile_plan = runner.build_plan()
        self.assertEqual(hostile_plan["digests"], baseline_plan["digests"])
        for record in [
            *plan["perf_stat"], *plan["perf_record"]["fixed"],
            *plan["perf_record"]["derived_candidates"],
        ]:
            self.assertIn("PERF_CONFIG_NOSYSTEM=1", record["argv"])
            self.assertIn("PERF_CONFIG_NOGLOBAL=1", record["argv"])
            self.assertIn("PERF_CONFIG=/dev/null", record["argv"])
            self.assertFalse(any(item.startswith("HOME=") for item in record["argv"]))

        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory) / "perf.data"
            data.write_bytes(b"PERFILE2" + b"\0" * 200)
            responses = [
                subprocess.CompletedProcess([], 0, stdout="cpu-clock\n", stderr=""),
                subprocess.CompletedProcess(
                    [], 0, stdout="x 1 [000] 1.0: cpu-clock:\n\tframe\n", stderr="",
                ),
            ]
            with mock.patch.object(analyzer.subprocess, "run", side_effect=responses) as execute:
                self.assertEqual(analyzer.validate_perf_data(data), [])
            self.assertEqual(execute.call_count, 2)
            for call in execute.call_args_list:
                argv = call.args[0]
                self.assertIn("PERF_CONFIG_NOSYSTEM=1", argv)
                self.assertIn("PERF_CONFIG_NOGLOBAL=1", argv)
                self.assertIn("PERF_CONFIG=/dev/null", argv)

    def test_start_receipt_binds_full_controller_entry(self) -> None:
        original = runner.RUN_ROOT
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "run"
            runner.RUN_ROOT = root
            try:
                protocol_path, protocol = frozen_protocol(root)
                plan = campaign_start(root, protocol)
                plan_path = root / "orchestration/command-plan.json"
                analyzer.verify_start(root, protocol_path, protocol, plan_path, plan)
                start_path = root / "orchestration/start.json"
                start = analyzer.load_json(start_path)
                start["controller_entry"]["environment"]["PATH"] = "/tmp/shadow"
                dump(start_path, start)
                with self.assertRaises(ValueError):
                    analyzer.verify_start(root, protocol_path, protocol, plan_path, plan)
            finally:
                runner.RUN_ROOT = original

    def test_callgrind_stream_binding_and_positive_selection(self) -> None:
        with self.assertRaises(ValueError):
            runner.select_perf_record_from_counts({kernel: 0 for kernel in runner.C_IDS})
        counts = {kernel: 7 for kernel in runner.C_IDS}
        self.assertEqual(runner.select_perf_record_from_counts(counts)[3:], sorted(runner.C_IDS)[:5])
        original = runner.RUN_ROOT
        with tempfile.TemporaryDirectory() as directory:
            runner.RUN_ROOT = Path(directory) / "run"
            try:
                record = next(
                    row for row in runner.callgrind_commands()
                    if not runner.callgrind_requires_registry_prelude(row)
                )
                outer = runner.RUN_ROOT / f"orchestration/attempts/callgrind-{record['ordinal']:03d}-{record['arm']}"
                output = Path(record["output"])
                dump(outer / "receipt.json", {"record": record, "returncode": 0})
                dump(output / "command.json", {
                    "schema": "cpu-baseline-aa-v5-callgrind-command/v1",
                    "argv": runner.callgrind_inner_argv(runner.binary_for(record["kernel"]), record["kernel"]),
                })
                (output / "stdout.txt").write_text(
                    json.dumps({"id": record["kernel"], "fingerprint": "fp"}) + "\n",
                    encoding="utf-8",
                )
                (output / "stderr.txt").write_text("Collected : 42\n", encoding="utf-8")
                dump(output / "receipt.json", {
                    "schema": "cpu-baseline-aa-v5-callgrind-receipt/v1",
                    "child_returncode": 0, "effective_returncode": 0, "parse_error": None,
                    "stdout_sha256": digest(output / "stdout.txt"),
                    "stderr_sha256": digest(output / "stderr.txt"),
                })
                (output / "status.txt").write_text("0\n", encoding="utf-8")
                dump(output / "result.json", {
                    "id": record["kernel"], "fingerprint": "fp", "ir": 42,
                })
                row, error = runner.validated_callgrind_result(runner.RUN_ROOT, record, "fp")
                self.assertIsNone(error)
                self.assertEqual(row["ir"], 42)
                (output / "stderr.txt").write_text("Collected : 43\n", encoding="utf-8")
                row, error = runner.validated_callgrind_result(runner.RUN_ROOT, record, "fp")
                self.assertIsNone(row)
                self.assertIn("hash", error)
            finally:
                runner.RUN_ROOT = original

    def test_complete_wall_recomputes_every_cell(self) -> None:
        original = runner.RUN_ROOT
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "run"
            runner.RUN_ROOT = root
            try:
                boundaries(root)
                for index, spec in enumerate(analyzer.session_specs(root), 1):
                    full_session(root, index, spec)
                gate, rows, _, fingerprints = analyzer.analyze_wall(root)
                self.assertEqual(gate["verdict"], "baseline_aa_complete_nonqualified")
                self.assertEqual(gate["retained_attempts"], 1056)
                self.assertEqual(gate["completed_successes"], 1056)
                self.assertEqual(gate["observed_cells"], 88)
                self.assertEqual(len(gate["cell_analysis"]), 88)
                self.assertEqual(len(rows), 1056)
                self.assertEqual(len(fingerprints), 44)
                self.assertFalse(gate["provenance_findings"])
                self.assertFalse(gate["incomplete_findings"])
            finally:
                runner.RUN_ROOT = original

    def test_partial_crash_prefix_and_inflight_are_recovered(self) -> None:
        original = runner.RUN_ROOT
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "run"
            runner.RUN_ROOT = root
            try:
                spec = analyzer.session_specs(root)[0]
                compare = root / "wall-1t/rust/compare"
                flattened = [
                    (item["round"], item["kernel"], arm)
                    for item in runner.wall_schedule(spec["id"]) for arm in item["arms"]
                ]
                finishes, events = [], []
                for sequence, (round_index, kernel, arm) in enumerate(flattened[:4], 1):
                    start, finish = inner_attempt(
                        compare, spec, sequence, round_index, kernel, arm, finish=sequence < 4,
                    )
                    events.append(start)
                    if finish is not None:
                        finishes.append(finish)
                        events.append(finish)
                jsonl(compare / "attempts.jsonl", finishes[:-1])
                jsonl(compare / "events.jsonl", events[:-2])
                rows, _, provenance, incomplete = analyzer.read_retained_wall_attempts(
                    root, spec, analyzer.validate_registry_contract()[0],
                )
                self.assertEqual([row["status"] for row in rows], [
                    "succeeded", "succeeded", "succeeded", "interrupted",
                ])
                self.assertFalse(provenance)
                self.assertTrue(any("crash-consistent prefix" in item for item in incomplete))
            finally:
                runner.RUN_ROOT = original

    def test_split_brain_and_stdout_tamper_are_provenance(self) -> None:
        original = runner.RUN_ROOT
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "run"
            runner.RUN_ROOT = root
            try:
                spec = analyzer.session_specs(root)[0]
                compare = root / "wall-1t/rust/compare"
                item = runner.wall_schedule(spec["id"])[0]
                start, finish = inner_attempt(
                    compare, spec, 1, item["round"], item["kernel"], item["arms"][0],
                )
                jsonl(compare / "attempts.jsonl", [dict(finish, kernel="wrong")])
                jsonl(compare / "events.jsonl", [start, finish])
                receipt_path = next(
                    p for p in (compare / "attempts").glob("*.json")
                    if not p.name.endswith(".started.json")
                )
                receipt = analyzer.load_json(receipt_path)
                receipt["stdout"] = json.dumps({
                    "id": item["kernel"], "fingerprint": "wrong",
                    "median_ns": 1, "samples_ns": [1, 1, 1],
                }) + "\n"
                dump(receipt_path, receipt)
                _, _, provenance, _ = analyzer.read_retained_wall_attempts(
                    root, spec, analyzer.validate_registry_contract()[0],
                )
                self.assertTrue(any("contradicts" in item for item in provenance))
                self.assertTrue(any("row/stream mismatch" in item for item in provenance))
            finally:
                runner.RUN_ROOT = original

    def test_perf_parsers_and_profile_stdout_are_semantic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stat = root / "stat.csv"
            stat.write_text(
                "1,msec,task-clock\n1,msec,cpu-clock\n0,,context-switches\n0,,page-faults\n",
                encoding="utf-8",
            )
            self.assertEqual(analyzer.validate_perf_stat_csv(stat), [])
            stat.write_text(
                "0,msec,task-clock\n1,msec,cpu-clock\n0,,context-switches\n0,,page-faults\n",
                encoding="utf-8",
            )
            self.assertIn("positive", analyzer.validate_perf_stat_csv(stat)[0])
            data = root / "perf.data"
            data.write_bytes(b"NOTPERF!" + b"\0" * 200)
            self.assertIn("wrong magic", analyzer.validate_perf_data(data, False)[0])
            data.write_bytes(b"PERFILE2" + b"\0" * 200)
            self.assertEqual(analyzer.validate_perf_data(data, False), [])
            self.assertTrue(analyzer.validate_benchmark_row({
                "id": "x", "fingerprint": "fp", "median_ns": 1,
                "samples_ns": [1, 1, 1],
            }, "x", expected_samples=5))

    def test_system_noise_stable_fields_and_failures(self) -> None:
        before = system_snapshot("before", 1)
        after = system_snapshot("wall-after", 2)
        after["cgroup"]["cpu.stat"] = "usage_usec 2\nnr_throttled 1\nthrottled_usec 5\n"
        after["cgroup"]["memory.events"] = "low 0\nhigh 0\nmax 0\noom 1\noom_kill 0\n"
        after["online_cpus"] = "0-3\n"
        detail, provenance, incomplete = analyzer.analyze_system_noise({
            "before": before, "after": after,
        })
        self.assertTrue(any("online_cpus" in item for item in provenance))
        self.assertTrue(any("CPU-throttled" in item for item in incomplete))
        self.assertTrue(any("memory" in item for item in incomplete))
        self.assertIn("deltas", detail)

    def test_cancelled_suffix_is_not_fabricated_as_timed(self) -> None:
        original = runner.RUN_ROOT
        with tempfile.TemporaryDirectory() as directory:
            runner.RUN_ROOT = Path(directory) / "run"
            try:
                rows = analyzer.complete_planned_rows(runner.RUN_ROOT, [], [])
                self.assertEqual(len(rows), 1056)
                self.assertEqual({row["status"] for row in rows}, {"cancelled"})
                self.assertTrue(all(row["started_at"] is None for row in rows))
                self.assertTrue(all(isinstance(row["work_contract"], str) for row in rows))
            finally:
                runner.RUN_ROOT = original

    def test_finalization_receipt_and_cmdline_guard(self) -> None:
        self.assertTrue(runner.is_campaign_cmdline(
            f"/workspace/.tools/perf/usr/bin/perf record -o {runner.RUN_ROOT}/x.data".encode()
        ))
        self.assertTrue(runner.is_campaign_cmdline(
            f"{runner.RUST_BINARY} run --filter x".encode()
        ))
        self.assertFalse(runner.is_campaign_cmdline(b"/usr/bin/sleep 10"))
        original = runner.RUN_ROOT
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "run"
            runner.RUN_ROOT = root
            try:
                terminal = root / "orchestration/terminal.json"
                export = root / "export.json"
                terminal_row = {
                    "schema": "cpu-baseline-aa-v5-terminal/v1",
                    "status": "wall_command_failed", "finished_at": T1,
                    "continuation": "forbidden",
                }
                dump(terminal, terminal_row)
                dump(root / "analysis/analysis.json", {
                    "schema": "cpu-baseline-aa-v5-analysis/v1",
                    "campaign_status": "sealed_terminal_incomplete",
                    "terminal": terminal_row,
                    "wall": {"verdict": "inconclusive_contention_or_incomplete"},
                    "verdict": "inconclusive_contention_or_incomplete",
                })
                dump(export, {
                    "files": [{"path": "orchestration/terminal.json", "sha256": digest(terminal)}],
                })
                dump(root / "orchestration/finalization.json", {
                    "schema": "cpu-baseline-aa-v5-finalization/v1", "status": "validated",
                    "export_sha256": digest(export), "analyzer_sha256": digest(runner.ANALYZER),
                    "scientific_returncode": 1, "completed_at": T1,
                })
                with mock.patch.object(runner.subprocess, "run") as execute:
                    execute.return_value.returncode = 0
                    execute.return_value.stderr = ""
                    valid, reason = runner.validate_finalization(Path("protocol.json"), 1, True)
                self.assertTrue(valid, reason)
                receipt = analyzer.load_json(root / "orchestration/finalization.json")
                receipt["scientific_returncode"] = 0
                dump(root / "orchestration/finalization.json", receipt)
                valid, _ = runner.validate_finalization(Path("protocol.json"), 1, True)
                self.assertFalse(valid)
                receipt["scientific_returncode"] = True
                dump(root / "orchestration/finalization.json", receipt)
                valid, _ = runner.validate_finalization(Path("protocol.json"), None, True)
                self.assertFalse(valid)
                receipt["scientific_returncode"] = 1
                receipt["completed_at"] = "not-a-time"
                dump(root / "orchestration/finalization.json", receipt)
                valid, _ = runner.validate_finalization(Path("protocol.json"), None, True)
                self.assertFalse(valid)
            finally:
                runner.RUN_ROOT = original

    def test_outer_receipt_launch_and_timeout_causality(self) -> None:
        original = runner.RUN_ROOT
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "run"
            runner.RUN_ROOT = root
            try:
                record = runner.build_plan()["wall"][0]
                name = "synthetic"
                outer = root / "orchestration/attempts" / name
                outer.mkdir(parents=True)
                (outer / "stdout.txt").write_text("", encoding="utf-8")
                (outer / "stderr.txt").write_text("", encoding="utf-8")
                dump(outer / "started.json", {
                    "schema": "cpu-baseline-aa-v5-attempt-start/v1",
                    "record": record, "started_at": T0,
                })
                receipt = {
                    "schema": "cpu-baseline-aa-v5-attempt/v1", "record": record,
                    "started_at": T0, "finished_at": T1, "returncode": 0,
                    "launch_error": "synthetic launch failure", "timeout_error": None,
                    "stdout_sha256": digest(outer / "stdout.txt"),
                    "stderr_sha256": digest(outer / "stderr.txt"),
                }
                dump(outer / "receipt.json", receipt)
                _, provenance, _ = analyzer.validate_attempt(root, name, record, False)
                self.assertTrue(any("launch error must bind" in row for row in provenance))

                receipt.update({
                    "returncode": 124, "launch_error": None,
                    "timeout_error": {
                        "seconds": record["timeout_seconds"],
                        "process_group_terminated": False,
                    },
                })
                dump(outer / "receipt.json", receipt)
                dump(outer / "launched.json", {
                    "schema": "cpu-baseline-aa-v5-attempt-launch/v1",
                    "record": record, "started_at": T0, "pid": 1,
                    "process_group": 1,
                })
                _, provenance, _ = analyzer.validate_attempt(root, name, record, False)
                self.assertTrue(any("timeout evidence must bind" in row for row in provenance))
            finally:
                runner.RUN_ROOT = original

    def test_controller_never_returns_success_after_failed_revalidation(self) -> None:
        original = runner.RUN_ROOT
        with tempfile.TemporaryDirectory() as directory:
            runner.RUN_ROOT = Path(directory) / "run"
            (runner.RUN_ROOT / "orchestration").mkdir(parents=True)
            completed = subprocess.CompletedProcess([], 0)
            try:
                with (
                    mock.patch.object(runner, "run_attempt", return_value=0),
                    mock.patch.object(runner, "write_identity_snapshot_once"),
                    mock.patch.object(runner, "write_system_snapshot_once"),
                    mock.patch.object(runner, "choose_perf_record", return_value=(None, {
                        "status": "not_attempted_missing_c_callgrind_a",
                        "missing": list(runner.C_IDS),
                    })),
                    mock.patch.object(runner.subprocess, "run", return_value=completed),
                    mock.patch.object(
                        runner, "validate_finalization",
                        return_value=(False, "synthetic post-analyzer rejection"),
                    ),
                ):
                    code = runner.execute_campaign(Path("protocol.json"), {})
                self.assertEqual(code, 2)
                failure = analyzer.load_json(
                    runner.RUN_ROOT / "orchestration/finalization-failure.json"
                )
                self.assertEqual(failure["reason"], "analysis_or_export_failed")
            finally:
                runner.RUN_ROOT = original

    def test_post_complete_analysis_failure_is_retry_only(self) -> None:
        original = runner.RUN_ROOT
        with tempfile.TemporaryDirectory() as directory:
            runner.RUN_ROOT = Path(directory) / "run"
            options = runner.argparse.Namespace(
                protocol=Path(directory) / "protocol.json",
                confirm_other_cpu_work_paused=True,
            )

            def fail_after_complete(*_args: object) -> int:
                dump(runner.RUN_ROOT / "orchestration/complete.json", {
                    "schema": "cpu-baseline-aa-v5-complete/v1",
                    "status": "orchestration_complete", "finished_at": T1,
                })
                raise subprocess.TimeoutExpired("analyzer", 1)

            try:
                with (
                    mock.patch.object(runner, "validate_protocol", return_value={}),
                    mock.patch.object(runner, "initialize_campaign", return_value=True),
                    mock.patch.object(runner, "execute_campaign", side_effect=fail_after_complete),
                ):
                    self.assertEqual(runner.command_run(options), 2)
                self.assertFalse((runner.RUN_ROOT / "orchestration/terminal.json").exists())
                self.assertTrue(
                    (runner.RUN_ROOT / "orchestration/finalization-failure.json").is_file()
                )
                finalize = runner.argparse.Namespace(
                    protocol=options.protocol, confirm_no_campaign_process_live=True,
                )
                with (
                    mock.patch.object(runner, "validate_protocol", return_value={}),
                    mock.patch.object(runner, "live_campaign_processes", return_value=[]),
                    mock.patch.object(
                        runner.subprocess, "run",
                        return_value=subprocess.CompletedProcess([], 0),
                    ),
                    mock.patch.object(
                        runner, "validate_finalization", return_value=(True, "validated"),
                    ),
                ):
                    self.assertEqual(runner.command_finalize(finalize), 0)
            finally:
                runner.RUN_ROOT = original

    def test_profile_schedule_is_one_cross_phase_exact_prefix(self) -> None:
        original = runner.RUN_ROOT
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "run"
            runner.RUN_ROOT = root
            try:
                plan = runner.build_plan()
                first = plan["callgrind"][0]
                later = plan["callgrind"][2]
                perf = plan["perf_stat"][0]
                failed_outer_attempt(
                    root, f"callgrind-{first['ordinal']:03d}-{first['arm']}", first,
                )
                failed_outer_attempt(
                    root, f"callgrind-{later['ordinal']:03d}-{later['arm']}", later,
                )
                failed_outer_attempt(
                    root, f"perf_stat-{perf['ordinal']:03d}-{perf['arm']}", perf,
                )
                findings = analyzer.validate_profile_schedule(root, plan, None)
                self.assertTrue(any("after the first incomplete" in row for row in findings))
                self.assertTrue(any("before both prior phases" in row for row in findings) is False)

                isolation = analyzer.isolation_path(first)
                rows = analyzer.load_jsonl(isolation)
                rows[0]["contended_samples"] = 1
                rows[0]["left_on_reserved"] = {"1": [1]}
                jsonl(isolation, rows)
                _, incomplete = analyzer.validate_isolation(first, 1, True)
                self.assertTrue(any("contended" in row for row in incomplete))
                self.assertTrue(any("remained" in row for row in incomplete))

                dump(root / "orchestration/perf-record-selection.json", {
                    "status": "not_attempted_missing_c_callgrind_a",
                    "missing": list(runner.C_IDS),
                })
                (root / "profiles/perf-record").mkdir(parents=True)
                profiles = analyzer.profile_inventory(root, {})
                self.assertTrue(any(
                    "without a complete frozen selection" in row
                    for row in profiles["perf_record"]["diagnostic_findings"]
                ))
                self.assertFalse(profiles["schedule_complete"])
            finally:
                runner.RUN_ROOT = original

    def test_atomic_publish_leaves_no_partial_final_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "analysis.json"
            with mock.patch.object(analyzer.os, "replace", side_effect=OSError("injected")):
                with self.assertRaises(OSError):
                    analyzer.atomic_publish(path, b"partial-never-published")
            self.assertFalse(path.exists())
            self.assertEqual(list(path.parent.glob(".analysis.json.tmp-*")), [])
            analyzer.atomic_publish(path, b"{\"ok\":true}\n")
            self.assertEqual(path.read_text(encoding="utf-8"), '{"ok":true}\n')
            self.assertEqual(list(path.parent.glob(".analysis.json.tmp-*")), [])

    def test_signaled_isolation_status_uses_frozen_normalization(self) -> None:
        original = runner.RUN_ROOT
        with tempfile.TemporaryDirectory() as directory:
            runner.RUN_ROOT = Path(directory) / "run"
            try:
                record = runner.build_plan()["wall"][0]
                jsonl(analyzer.isolation_path(record), [{
                    "schema": "isolated-bench/1", "mode": "reserve",
                    "label": record["argv"][record["argv"].index("--label") + 1],
                    "reserved_cpus": [0, 1, 2, 3], "left_on_reserved": {},
                    "command": analyzer.child_argv(record), "exit_status": -9,
                    "contended_samples": 0,
                }])
                provenance, _ = analyzer.validate_isolation(record, 247, False)
                self.assertFalse(provenance)
            finally:
                runner.RUN_ROOT = original

    def test_wall_failure_allows_only_an_unstarted_suffix(self) -> None:
        original = runner.RUN_ROOT
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "run"
            runner.RUN_ROOT = root
            try:
                boundaries(root)
                plan = runner.build_plan()["wall"]
                record = plan[0]
                outer = root / "orchestration/attempts/wall-01-rust-1t"
                outer.mkdir(parents=True)
                (outer / "stdout.txt").write_text("", encoding="utf-8")
                (outer / "stderr.txt").write_text("failed\n", encoding="utf-8")
                dump(outer / "started.json", {
                    "schema": "cpu-baseline-aa-v5-attempt-start/v1", "record": record,
                    "started_at": T0,
                })
                dump(outer / "launched.json", {
                    "schema": "cpu-baseline-aa-v5-attempt-launch/v1", "record": record,
                    "started_at": T0, "pid": 1, "process_group": 1,
                })
                dump(outer / "receipt.json", {
                    "schema": "cpu-baseline-aa-v5-attempt/v1", "record": record,
                    "started_at": T0, "finished_at": T1, "returncode": 1,
                    "launch_error": None, "timeout_error": None,
                    "stdout_sha256": digest(outer / "stdout.txt"),
                    "stderr_sha256": digest(outer / "stderr.txt"),
                })
                jsonl(analyzer.isolation_path(record), [{
                    "schema": "isolated-bench/1", "mode": "reserve",
                    "label": record["argv"][record["argv"].index("--label") + 1],
                    "reserved_cpus": [0, 1, 2, 3], "left_on_reserved": {},
                    "command": analyzer.child_argv(record), "exit_status": 1,
                    "contended_samples": 0,
                }])
                gate, _, _, _ = analyzer.analyze_wall(root)
                self.assertEqual(gate["verdict"], "inconclusive_contention_or_incomplete")
                # A later start contradicts the prospective stop-on-wall-failure rule.
                later = root / "orchestration/attempts/wall-02-c-1t"
                dump(later / "started.json", {
                    "schema": "cpu-baseline-aa-v5-attempt-start/v1", "record": plan[1],
                    "started_at": T1,
                })
                gate, _, _, _ = analyzer.analyze_wall(root)
                self.assertEqual(gate["verdict"], "invalid_exactness_or_provenance")
                self.assertTrue(any("after the frozen stop" in item for item in gate["provenance_findings"]))
            finally:
                runner.RUN_ROOT = original

    def test_inner_failure_forbids_extra_start_and_outer_start_is_mandatory(self) -> None:
        original = runner.RUN_ROOT
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "run"
            runner.RUN_ROOT = root
            try:
                boundaries(root)
                spec = analyzer.session_specs(root)[0]
                compare = root / "wall-1t/rust/compare"
                flattened = [
                    (item["round"], item["kernel"], arm)
                    for item in runner.wall_schedule(spec["id"]) for arm in item["arms"]
                ]
                start, failed = inner_attempt(compare, spec, 1, *flattened[0])
                failed.update({
                    "child_returncode": 1, "effective_returncode": 1,
                    "stdout": "", "row": None,
                })
                terminal = next(
                    p for p in (compare / "attempts").glob("*.json")
                    if not p.name.endswith(".started.json")
                )
                dump(terminal, failed)
                extra, _ = inner_attempt(compare, spec, 2, *flattened[1], finish=False)
                jsonl(compare / "attempts.jsonl", [failed])
                jsonl(compare / "events.jsonl", [start, failed, extra])
                _, _, provenance, _ = analyzer.read_retained_wall_attempts(
                    root, spec, analyzer.validate_registry_contract()[0],
                )
                self.assertTrue(any("started after a failed" in item for item in provenance))
                gate, _, _, _ = analyzer.analyze_wall(root)
                self.assertTrue(any(
                    "evidence exists without an outer start" in item
                    for item in gate["provenance_findings"]
                ))
            finally:
                runner.RUN_ROOT = original

    def test_complete_root_emits_a_canonical_checked_export(self) -> None:
        """Exercise all 1,056 descriptive cells without launching a workload."""
        original = runner.RUN_ROOT
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "run"
            runner.RUN_ROOT = root
            try:
                protocol_path, protocol = frozen_protocol(root)
                plan = campaign_start(root, protocol)
                self.assertEqual(boundaries(root, protocol), [])
                for index, spec in enumerate(analyzer.session_specs(root), 1):
                    full_session(root, index, spec)
                for phase in ("callgrind", "perf_stat"):
                    for record in plan[phase]:
                        failed_outer_attempt(
                            root, f"{phase}-{record['ordinal']:03d}-{record['arm']}", record,
                        )
                dump(root / "orchestration/perf-record-selection.json", {
                    "status": "not_attempted_missing_c_callgrind_a",
                    "missing": list(runner.C_IDS),
                })
                dump(root / "orchestration/complete.json", {
                    "schema": "cpu-baseline-aa-v5-complete/v1",
                    "status": "orchestration_complete", "finished_at": T1,
                })
                dump(root / "orchestration/finalization-failure.json", {
                    "schema": "cpu-baseline-aa-v5-finalization-failure/v1",
                    "status": "derived_finalization_incomplete",
                    "reason": "analysis_exception_after_completed_measurement",
                    "finished_at": T1, "measurement_continuation": "forbidden",
                    "analysis_only_retry": "allowed_until_validated_finalization_exists",
                    "error_type": "TimeoutExpired", "error": "synthetic timeout",
                })
                context = multiprocessing.get_context("fork")
                barrier = context.Barrier(2)
                results = context.Queue()
                publication_log = Path(directory) / "analyzer-publications.log"
                contenders = [
                    context.Process(
                        target=concurrent_analyzer_worker,
                        args=(protocol_path, root, barrier, results, publication_log),
                    )
                    for _ in range(2)
                ]
                for contender in contenders:
                    contender.start()
                for contender in contenders:
                    contender.join(timeout=180)
                    self.assertFalse(contender.is_alive(), "concurrent analyzer did not finish")
                    self.assertEqual(contender.exitcode, 0)
                outcomes = [results.get(timeout=5) for _ in contenders]
                self.assertEqual({row[0] for row in outcomes}, {"ok"})
                self.assertEqual([row[2] for row in outcomes], [0, 0])
                publishing_processes = {
                    line.split("\t", 1)[0]
                    for line in publication_log.read_text(encoding="utf-8").splitlines()
                }
                self.assertEqual(len(publishing_processes), 1)
                export = analyzer.load_json(root / "export.json")
                self.assertEqual(len(export["runs"]), 1056)
                self.assertEqual(
                    {(row["arm"], row["instance_id"], row["replicate"], row["seed"])
                     for row in export["runs"]},
                    {(row["arm"], row["instance_id"], row["replicate"], row["seed"])
                     for row in runner.export_seed_table()},
                )
                self.assertFalse((root / "orchestration/terminal.json").exists())
                self.assertTrue((root / "orchestration/finalization.json").is_file())
                self.assertTrue(any(
                    item["path"] == "orchestration/finalization-failure.json"
                    for item in export["files"]
                ))
                assert_canonical_export(self, protocol_path, protocol, root)
                sealed = [
                    root / "analysis/wall-gate.json", root / "rows.jsonl",
                    root / "analysis/analysis.json", root / "analysis/cells.json",
                    root / "analysis/REPORT.md", root / "export.json",
                    root / "orchestration/finalization.json",
                ]
                before = {path: path.read_bytes() for path in sealed}
                self.assertEqual(invoke_analyzer(protocol_path, root), 0)
                self.assertEqual({path: path.read_bytes() for path in sealed}, before)
                raw = root / "wall-1t/rust/compare/attempts/0001_A_gf2_la_rref_macaulay_k5m3d5.json"
                if not raw.is_file():
                    raw = next(
                        path for path in (root / "wall-1t/rust/compare/attempts").glob("*.json")
                        if not path.name.endswith(".started.json")
                    )
                raw.write_bytes(raw.read_bytes() + b" ")
                with self.assertRaises(ValueError):
                    invoke_analyzer(protocol_path, root)
                self.assertEqual({path: path.read_bytes() for path in sealed}, before)
            finally:
                runner.RUN_ROOT = original

    def test_blocked_root_checks_export_when_perfindex_is_unavailable(self) -> None:
        """A failed measurement identity must not become an analysis dependency."""
        original_root = runner.RUN_ROOT
        original_perfindex = runner.PERFINDEX
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "run"
            runner.RUN_ROOT = root
            try:
                protocol_path, protocol = frozen_protocol(root)
                campaign_start(root, protocol)
                findings = boundaries(root, protocol, blocked_path=original_perfindex)
                self.assertTrue(any("required identity mismatch" in item for item in findings))
                dump(root / "orchestration/terminal.json", {
                    "schema": "cpu-baseline-aa-v5-terminal/v1",
                    "status": "preflight_identity_blocked", "finished_at": T1,
                    "continuation": "forbidden", "findings": findings,
                })
                terminal_path = root / "orchestration/terminal.json"
                terminal = analyzer.load_json(terminal_path)
                dump(terminal_path, {**terminal, "findings": []})
                bad_gate, _, _, _ = analyzer.analyze_wall(root, protocol)
                self.assertEqual(bad_gate["verdict"], "invalid_exactness_or_provenance")
                dump(terminal_path, terminal)
                unexpected_profile = root / "profiles/perf-stat/unexpected.csv"
                unexpected_profile.parent.mkdir(parents=True)
                unexpected_profile.write_text("forbidden\n", encoding="utf-8")
                bad_gate, _, _, _ = analyzer.analyze_wall(root, protocol)
                self.assertEqual(bad_gate["verdict"], "invalid_exactness_or_provenance")
                unexpected_profile.unlink()
                unexpected_profile.parent.rmdir()
                unexpected_profile.parent.parent.rmdir()
                runner.PERFINDEX = root / "deliberately-unavailable-perfindex.py"
                self.assertEqual(invoke_analyzer(protocol_path, root), 1)
                gate = analyzer.load_json(root / "analysis/wall-gate.json")
                self.assertEqual(gate["verdict"], "blocked_artifact_or_isolation")
                export = analyzer.load_json(root / "export.json")
                self.assertEqual(len(export["runs"]), 1056)
                self.assertTrue(any(
                    item["path"] == "orchestration/terminal.json"
                    for item in export["files"]
                ))
                assert_canonical_export(self, protocol_path, protocol, root)
            finally:
                runner.PERFINDEX = original_perfindex
                runner.RUN_ROOT = original_root

    def test_operational_terminal_roots_emit_canonical_checked_exports(self) -> None:
        """Exercise wall failure, in-flight orphan, and post-wall interruption."""
        original = runner.RUN_ROOT
        for case in ("wall-failure", "wall-orphan", "profile-interruption"):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as directory:
                root = Path(directory) / "run"
                runner.RUN_ROOT = root
                try:
                    protocol_path, protocol = frozen_protocol(root)
                    plan = campaign_start(root, protocol)
                    self.assertEqual(boundaries(root, protocol), [])
                    if case == "wall-failure":
                        record = plan["wall"][0]
                        failed_outer_attempt(root, "wall-01-rust-1t", record)
                        terminal = {
                            "schema": "cpu-baseline-aa-v5-terminal/v1",
                            "status": "wall_command_failed", "finished_at": T1,
                            "continuation": "forbidden", "record": record,
                        }
                    elif case == "wall-orphan":
                        record = plan["wall"][0]
                        outer = root / "orchestration/attempts/wall-01-rust-1t"
                        dump(outer / "started.json", {
                            "schema": "cpu-baseline-aa-v5-attempt-start/v1",
                            "record": record, "started_at": T0,
                        })
                        dump(outer / "launched.json", {
                            "schema": "cpu-baseline-aa-v5-attempt-launch/v1",
                            "record": record, "started_at": T0,
                            "pid": 1234, "process_group": 1234,
                        })
                        terminal = {
                            "schema": "cpu-baseline-aa-v5-terminal/v1",
                            "status": "orphaned_after_process_loss", "finished_at": T1,
                            "continuation": "forbidden",
                            "reason": "synthetic process loss",
                        }
                    else:
                        for index, spec in enumerate(analyzer.session_specs(root), 1):
                            full_session(root, index, spec)
                        record = plan["callgrind"][0]
                        outer = root / (
                            "orchestration/attempts/"
                            f"callgrind-{record['ordinal']:03d}-{record['arm']}"
                        )
                        dump(outer / "started.json", {
                            "schema": "cpu-baseline-aa-v5-attempt-start/v1",
                            "record": record, "started_at": T0,
                        })
                        dump(outer / "launched.json", {
                            "schema": "cpu-baseline-aa-v5-attempt-launch/v1",
                            "record": record, "started_at": T0,
                            "pid": 1234, "process_group": 1234,
                        })
                        terminal = {
                            "schema": "cpu-baseline-aa-v5-terminal/v1",
                            "status": "interrupted_by_operator", "finished_at": T1,
                            "continuation": "forbidden", "error": "KeyboardInterrupt",
                        }
                    dump(root / "orchestration/terminal.json", terminal)
                    self.assertEqual(invoke_analyzer(protocol_path, root), 1)
                    analysis = analyzer.load_json(root / "analysis/analysis.json")
                    self.assertEqual(analysis["campaign_status"], "sealed_terminal_incomplete")
                    self.assertEqual(analysis["terminal"], terminal)
                    assert_canonical_export(self, protocol_path, protocol, root)
                finally:
                    runner.RUN_ROOT = original


if __name__ == "__main__":
    unittest.main()
