#!/usr/bin/env python3
"""Freeze the host-specific Tier 0 manifest for volcano-jobs-native-v1."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STUDY = Path(__file__).resolve().parent
BASE_ROOT = Path("/workspace/cryptanalysis-pr963-bench-base")
BASE_BUILD = Path("/workspace/cryptanalysis-pr963-bench-base-build")
CAND_BUILD = ROOT / "build-pr963"
BASE_SHA = "b3d9c4fdece5ff698581c478d646a50c61eef029"
CAND_SHA = "d805fe6036bfefad6eabc74130df48366d4ae354"


def command(ca: Path, case: dict, job_mode: str,
            trials: int, per_level: int, controls: int) -> list[str]:
    return [str(STUDY / "run_case.py"), "--ca", str(ca), "--case", case["id"],
            "--jobs", job_mode, "--trials", str(trials),
            "--per-level", str(per_level), "--controls", str(controls)]


def parse_cpu_set(spec: str) -> set[int]:
    out = set()
    for part in spec.split(","):
        if "-" in part:
            lo, hi = (int(x) for x in part.split("-", 1))
            if lo < 0 or hi < lo:
                raise ValueError("invalid CPU range")
            out.update(range(lo, hi + 1))
        else:
            cpu = int(part)
            if cpu < 0:
                raise ValueError("invalid CPU id")
            out.add(cpu)
    if not out:
        raise ValueError("empty CPU set")
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cgroup", required=True)
    parser.add_argument("--cpus", required=True,
                        help="four or more fully isolated logical CPUs")
    parser.add_argument("--mem-nodes", required=True,
                        help="one isolated NUMA node")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cpus = parse_cpu_set(args.cpus)
    if len(cpus) < 4:
        parser.error("Tier 0 volcano-jobs campaign requires at least four isolated CPUs")
    workloads = json.loads((STUDY / "workloads.json").read_text())["cases"]

    cases = []
    for workload in workloads:
        if workload["id"] == "hist-shape-33bit-36solves":
            trials, per_level, controls = 36, 0, 0
        else:
            trials, per_level, controls = 6, 2, 1
        common = {"workload_id": workload["workload_id"],
                  "generator": ",".join(map(str, workload["generator"])),
                  "target": ",".join(map(str, workload["target"])),
                  "solves": "36"}
        known_answer = {"expected_fields": common,
                        "expected_result": str(workload["known_scalar"])}
        modes = (
            ("aa", BASE_BUILD / "ca", "serial", BASE_BUILD / "ca", "serial"),
            ("jobs1", BASE_BUILD / "ca", "serial", CAND_BUILD / "ca", "1"),
            ("jobs4", BASE_BUILD / "ca", "serial", CAND_BUILD / "ca", "4"),
        )
        for label, ref_bin, ref_jobs, cand_bin, cand_jobs in modes:
            cases.append({
                "id": workload["id"] + "-" + label,
                **known_answer,
                "reference": command(ref_bin, workload, ref_jobs,
                                     trials, per_level, controls),
                "candidate": command(cand_bin, workload, cand_jobs,
                                     trials, per_level, controls),
            })

    artifacts = [
        str(STUDY / "protocol.md"),
        str(STUDY / "workloads.json"),
        str(STUDY / "make_workloads.py"),
        str(STUDY / "run_case.py"),
        str(STUDY / "make_manifest.py"),
        str(STUDY / "build.json"),
        str(ROOT / "scripts" / "isolated_bench.py"),
        str(ROOT / "tests" / "test_isolated_bench.py"),
        str(BASE_BUILD / "ca"), str(CAND_BUILD / "ca"),
        str(BASE_BUILD / "CMakeCache.txt"), str(CAND_BUILD / "CMakeCache.txt"),
    ]
    for source_root in (ROOT, BASE_ROOT):
        for relative in ("tools/ca_cli.c", "src/group_ec.c", "src/rho.c", "src/volcano.c"):
            artifacts.append(str(source_root / relative))

    manifest = {
        "schema": 1,
        "measurement_tier": "tier0_host",
        "workdir": str(ROOT),
        "measurement_boundary": (
            "Monotonic wall time immediately around the pinned native `ca volcano` process; "
            "includes CLI setup, all 36 rho solves, trials CSV and diagram writes; excludes "
            "Python wrapper startup and its post-run parsing/correctness checks."),
        "timeout_s": 120,
        "repetitions": 12,
        "result_field": "answer",
        "pair_fields": ["workload_id", "answer", "generator", "target", "solves",
                        "ops_sha256"],
        "isolation": {"cpus": args.cpus, "execution_cpu": min(cpus),
                      "execution_cpus": args.cpus, "mem_nodes": args.mem_nodes,
                      "cgroup": args.cgroup},
        "artifacts": artifacts,
        "cases": cases,
        "campaign": "volcano-jobs-native-v1",
        "baseline_commit": BASE_SHA,
        "candidate_commit": CAND_SHA,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
