#!/usr/bin/env python3
"""Dry/unit validation for the CPU baseline A/A v5 orchestration.

These tests synthesize receipts and compare rows.  They never execute a
retained benchmark, profiler, registry command, isolation tool, or provider.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import analyze_cpu_baseline_aa_v5 as analyzer
import run_cpu_baseline_aa_v5 as runner


def dump(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CpuBaselineAaV5Tests(unittest.TestCase):
    def test_schedule_hashes_reproduce_v4(self) -> None:
        self.assertEqual(
            analyzer.canonical_sha256(analyzer.expected_schedule(runner.RUST_IDS)),
            analyzer.RUST_SCHEDULE_SHA256,
        )
        self.assertEqual(
            analyzer.canonical_sha256(analyzer.expected_schedule(runner.C_IDS)),
            analyzer.C_SCHEDULE_SHA256,
        )

    def test_plan_expansion_order_paths_and_digests(self) -> None:
        plan = runner.build_plan()
        self.assertEqual(plan["counts"], {
            "wall_sessions": 4,
            "callgrind_attempts": 88,
            "perf_stat_attempts": 88,
            "perf_record_attempts": 8,
        })
        self.assertEqual(len(plan["wall"]), 4)
        self.assertEqual(len(plan["callgrind"]), 88)
        self.assertEqual(len(plan["perf_stat"]), 88)
        self.assertEqual(len(plan["perf_record"]["fixed"]), 3)
        self.assertEqual(len(plan["perf_record"]["derived_candidates"]), 170)
        expected_pairs = [
            (kernel, arm)
            for kernel in sorted((*runner.RUST_IDS, *runner.C_IDS))
            for arm in ("A", "B")
        ]
        self.assertEqual(
            [(record["kernel"], record["arm"]) for record in plan["callgrind"]],
            expected_pairs,
        )
        self.assertEqual(
            [(record["kernel"], record["arm"]) for record in plan["perf_stat"]],
            expected_pairs,
        )
        self.assertEqual(
            [record["ordinal"] for record in plan["callgrind"]], list(range(1, 89)),
        )
        self.assertEqual(
            len({record["output"] for record in plan["callgrind"]}), 88,
        )
        self.assertEqual(
            len({record["output"] for record in plan["perf_stat"]}), 88,
        )
        for record in plan["callgrind"]:
            child = analyzer.child_argv(record)
            self.assertEqual(child[:4], ["taskset", "-c", "0", "env"])
            self.assertIn("callgrind-one", child)
        self.assertEqual(plan["digests"], {
            "wall": "6501193e1c029ec3ea251d7a2816bc177e45a729f877a613199d03daeda4a3b5",
            "callgrind": "1e82cd86c79ea8b650afa182905c4a9ab9c30bb69fa5bba277d45c44a885e757",
            "perf_stat": "6130c98dd5c23ac84788937186198491de52fe17678259c68c8d9ba7991be395",
            "perf_record_fixed": "1089605b09cbde567fd05a6978e7fd0bf1e24ddc8f5c2534f59782cb92c76807",
            "perf_record_derived_candidates": "c66ef3dac8e17c5425e678a5c204a395849d8eed290dcb47f773763213528094",
            "plan_preimage": "598f62ef68a02777bdb2fb64367fcc6e83f3a0c0f01f9757bb96f84c495182f2",
        })

    def test_callgrind_inner_argv_matches_frozen_perfindex_semantics(self) -> None:
        kernel = runner.RUST_IDS[0]
        self.assertEqual(runner.callgrind_inner_argv(runner.RUST_BINARY, kernel), [
            "valgrind", "--tool=callgrind", "--callgrind-out-file=/dev/null",
            "--instr-atstart=no", str(runner.RUST_BINARY), "run", "--filter",
            kernel, "--exact", "--instr",
        ])

    def test_perf_record_ties_are_resolved_by_kernel_id(self) -> None:
        counts = {kernel: 7 for kernel in runner.C_IDS}
        selected = runner.select_perf_record_from_counts(counts)
        self.assertEqual(selected[:3], list(runner.FIXED_RECORD_IDS))
        self.assertEqual(selected[3:], sorted(runner.C_IDS)[:5])

    def test_callgrind_selection_requires_all_bound_receipts(self) -> None:
        original_root = runner.RUN_ROOT
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "baseline-aa-v5"
            runner.RUN_ROOT = root
            try:
                record = runner.callgrind_commands()[0]
                attempt = root / (
                    f"orchestration/attempts/callgrind-{record['ordinal']:03d}-{record['arm']}"
                )
                output = Path(record["output"])
                dump(attempt / "receipt.json", {"record": record, "returncode": 0})
                inner_argv = runner.callgrind_inner_argv(
                    runner.binary_for(record["kernel"]), record["kernel"],
                )
                dump(output / "command.json", {
                    "schema": "cpu-baseline-aa-v5-callgrind-command/v1",
                    "argv": inner_argv,
                })
                dump(output / "receipt.json", {
                    "schema": "cpu-baseline-aa-v5-callgrind-receipt/v1",
                    "child_returncode": 0, "effective_returncode": 0,
                    "parse_error": None,
                })
                (output / "status.txt").write_text("0\n", encoding="utf-8")
                dump(output / "result.json", {
                    "id": record["kernel"], "fingerprint": "exact-fingerprint", "ir": 42,
                })
                row, error = runner.validated_callgrind_result(
                    root, record, "exact-fingerprint",
                )
                self.assertIsNone(error)
                self.assertEqual(row["ir"], 42)
                dump(output / "result-tampered.json", {})
                (output / "result.json").write_text(json.dumps({
                    "id": "wrong/cell", "fingerprint": "exact-fingerprint", "ir": 42,
                }) + "\n", encoding="utf-8")
                row, error = runner.validated_callgrind_result(
                    root, record, "exact-fingerprint",
                )
                self.assertIsNone(row)
                self.assertIn("cell", error)
            finally:
                runner.RUN_ROOT = original_root

    def test_synthetic_complete_wall_gate_has_1056_rows(self) -> None:
        original_root = runner.RUN_ROOT
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "baseline-aa-v5"
            runner.RUN_ROOT = root
            try:
                plan = runner.build_plan()
                for index, spec in enumerate(analyzer.session_specs(root), 1):
                    record = plan["wall"][index - 1]
                    attempt = root / "orchestration/attempts" / f"wall-{index:02d}-{spec['id']}"
                    attempt.mkdir(parents=True)
                    stdout = attempt / "stdout.txt"
                    stderr = attempt / "stderr.txt"
                    stdout.write_text("", encoding="utf-8")
                    lines = []
                    for row in analyzer.expected_schedule(spec["ids"]):
                        values = " ".join(f"{arm}=0.001ms" for arm in row["arms"])
                        lines.append(f"round {row['round']}/6 {row['id']}: {values}")
                    stderr.write_text("\n".join(lines) + "\n", encoding="utf-8")
                    dump(attempt / "receipt.json", {
                        "schema": "cpu-baseline-aa-v5-attempt/v1",
                        "record": record,
                        "started_at": "2026-11-01T00:00:00+00:00",
                        "finished_at": "2026-11-01T00:00:01+00:00",
                        "returncode": 0,
                        "launch_error": None,
                        "stdout_sha256": digest(stdout),
                        "stderr_sha256": digest(stderr),
                    })
                    iso = analyzer.isolation_path(record)
                    dump(iso, {
                        "schema": "isolated-bench/1", "mode": "reserve",
                        "label": record["argv"][record["argv"].index("--label") + 1],
                        "reserved_cpus": [0, 1, 2, 3], "left_on_reserved": {},
                        "command": analyzer.child_argv(record), "exit_status": 0,
                        "contended_samples": 0, "samples": [],
                    })
                    raw = {}
                    kernels = []
                    for kernel in spec["ids"]:
                        fingerprint = f"fingerprint:{kernel}"
                        one = {
                            "id": kernel, "fingerprint": fingerprint,
                            "median_ns": 1000, "samples_ns": [900, 1000, 1100],
                        }
                        raw[kernel] = {
                            "A": [dict(one, round=round_index) for round_index in range(6)],
                            "B": [dict(one, round=round_index) for round_index in range(6)],
                            "A2": [],
                        }
                        kernels.append({"id": kernel, "verdict": "neutral"})
                    language = spec["language"]
                    binary = runner.RUST_BINARY if language == "rust" else runner.C_BINARY
                    compare = {
                        "valid": True, "rounds": 6, "mode": "wall", "unit": "ms",
                        "base": str(binary), "cand": str(binary),
                        "threads": 1 if spec["panel"] == "1t" else 4,
                        "samples_per_invocation": 5, "raw": raw, "kernels": kernels,
                        "host": {
                            "cpu": "synthetic", "logical_cores": 5,
                            "memory": "1024 kB", "os": "Synthetic",
                        },
                    }
                    dump(
                        root / f"wall-{spec['panel']}/{language}/compare/compare.json",
                        compare,
                    )
                gate, rows, _, fingerprints = analyzer.analyze_wall(root)
                self.assertEqual(gate["verdict"], "baseline_aa_complete_nonqualified")
                self.assertEqual(gate["observed_invocations"], 1056)
                self.assertEqual(gate["observed_cells"], 88)
                self.assertEqual(len(rows), 1056)
                self.assertEqual(len(fingerprints), 44)
                self.assertFalse(gate["provenance_findings"])
                self.assertFalse(gate["incomplete_findings"])
            finally:
                runner.RUN_ROOT = original_root

    def test_terminal_stop_expands_cancelled_export_rows(self) -> None:
        original_root = runner.RUN_ROOT
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "baseline-aa-v5"
            runner.RUN_ROOT = root
            try:
                rows = analyzer.complete_planned_rows(root, [])
                self.assertEqual(len(rows), 1056)
                self.assertEqual({row["status"] for row in rows}, {"cancelled"})
                self.assertEqual({row["attempts"] for row in rows}, {1})
                self.assertTrue(all(row["wall_seconds"] is None for row in rows))
            finally:
                runner.RUN_ROOT = original_root


if __name__ == "__main__":
    unittest.main()
