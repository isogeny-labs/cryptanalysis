#!/usr/bin/env python3
"""Hermetic regression tests for remote CPU affinity selection and pinning."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


HERE = Path(__file__).resolve().parent


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


remote = load("go_remote_ab", "run_remote_ab.py")
campaign = load("go_remote_campaign", "run_remote_campaign.py")


V3_OBSERVED_AFFINITY = [
    0, 2, 31, 35, 39, 45, 53, 60, 61, 70, 78, 79, 86, 87, 89, 90,
    96, 98, 127, 131, 135, 141, 149, 156, 157, 166, 174, 175, 182, 183,
    185, 186,
]


def topology(cpus: list[int]) -> list[dict[str, int | str | None]]:
    return [
        {
            "cpu": cpu,
            "package": 0,
            "die": 0,
            "numa": 0,
            "core": index,
            "thread_siblings": str(cpu),
        }
        for index, cpu in enumerate(cpus)
    ]


def snapshot(cpus: list[int]) -> dict:
    rows = topology(cpus)
    return {
        "affinity": cpus,
        "cpu_topology": rows,
        "topology_order": remote.ordered_cpus(cpus, rows),
        "memory_max": "64000000000",
        "nvidia_devices": [],
    }


class RemoteAffinityTests(unittest.TestCase):
    def test_accepts_exact_noncontiguous_runpod_affinity(self) -> None:
        placement = remote.validate_host(
            snapshot(V3_OBSERVED_AFFINITY), 32, 64_000_000_000
        )
        self.assertEqual(placement["allowed_cpus"], V3_OBSERVED_AFFINITY)
        self.assertEqual(placement["benchmark_cpus"], [0])
        self.assertEqual(placement["memory_limit_bytes"], 64_000_000_000)

    def test_selection_does_not_assume_cpu_zero_or_contiguity(self) -> None:
        cpus = [7, 41, 103]
        rows = [
            {"cpu": 7, "package": 1, "die": 0, "numa": 1, "core": 0},
            {"cpu": 41, "package": 0, "die": 1, "numa": 0, "core": 0},
            {"cpu": 103, "package": 0, "die": 0, "numa": 0, "core": 9},
        ]
        state = snapshot(cpus)
        state["cpu_topology"] = rows
        state["topology_order"] = [103, 41, 7]
        placement = remote.validate_host(state, 3, 64_000_000_000)
        self.assertEqual(placement["topology_order"], [103, 41, 7])
        self.assertEqual(placement["benchmark_cpus"], [103])

    def test_rejects_count_duplicate_topology_and_affinity_changes(self) -> None:
        with self.assertRaises(RuntimeError):
            remote.validate_host(snapshot([2, 4]), 3, 64_000_000_000)
        with self.assertRaises(RuntimeError):
            remote.ordered_cpus([2, 2], topology([2, 2]))
        bad = snapshot([2, 4, 6])
        bad["cpu_topology"] = bad["cpu_topology"][:-1]
        with self.assertRaises(RuntimeError):
            remote.validate_host(bad, 3, 64_000_000_000)
        with self.assertRaises(RuntimeError):
            remote.assert_affinity([2, 4, 6], [2, 4, 8])

    def test_campaign_parses_and_pins_observed_cpu(self) -> None:
        cpus = campaign.parse_affinity("7,41,103")
        self.assertEqual(cpus, [7, 41, 103])
        command = campaign.benchmark_command(
            103, Path("/tmp/coord.test"), "BenchmarkStateVersionVector/log_1024"
        )
        self.assertEqual(command[:4], ["taskset", "-c", "103", "/tmp/coord.test"])
        campaign.require_affinity(cpus, [103, 7, 41])
        with self.assertRaises(RuntimeError):
            campaign.require_affinity(cpus, [7, 41])
        for invalid in ("", "41,7", "7,7", "-1,7", "seven"):
            with self.assertRaises(ValueError):
                campaign.parse_affinity(invalid)

    def test_requires_exact_decimal_runpod_memory_limit(self) -> None:
        state = snapshot(V3_OBSERVED_AFFINITY)
        remote.validate_host(state, 32, 64_000_000_000)
        for invalid in (str(64 << 30), "max", "", "64000000000\n", None):
            changed = dict(state)
            changed["memory_max"] = invalid
            with self.assertRaises(RuntimeError):
                remote.validate_host(changed, 32, 64_000_000_000)
        with self.assertRaises(RuntimeError):
            remote.validate_host(state, 32, 0)


if __name__ == "__main__":
    unittest.main()
