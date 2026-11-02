#!/usr/bin/env python3
"""Hermetic regression tests for remote CPU affinity selection and pinning."""

from __future__ import annotations

import copy
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
analyzer = load("go_remote_peer_key_analyzer", "analyze_remote_peer_key_ab.py")
exporter = load("go_remote_peer_key_exporter", "export_remote_peer_key_ab.py")


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
    value = {
        "affinity": cpus,
        "cpu_topology": rows,
        "topology_order": remote.ordered_cpus(cpus, rows),
        "logical_cpus": max(192, len(cpus)),
        "cpu_model": "Example Stable CPU Model",
        "cpuset_cpus": ",".join(str(cpu) for cpu in cpus),
        "memory_max": "64000000000",
        "nvidia_devices": [],
        "cpuinfo_sha256": "1" * 64,
        "loadavg": "0.10 0.20 0.30 1/100 1000",
        "pressure_cpu": "some avg10=0.1 avg60=0.2 avg300=0.3 total=1",
        "pressure_memory": "some avg10=0.0 avg60=0.0 avg300=0.0 total=0",
    }
    return remote.bind_stable_placement_identity(value)


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
        remote.bind_stable_placement_identity(state)
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

    def test_volatile_cpuinfo_load_and_pressure_are_diagnostic_only(self) -> None:
        initial = snapshot([2, 4, 6, 8])
        later = copy.deepcopy(initial)
        later.update({
            "cpuinfo_sha256": "f" * 64,
            "loadavg": "12.0 8.0 4.0 9/100 2000",
            "pressure_cpu": "some avg10=9.9 avg60=8.8 avg300=7.7 total=99",
            "pressure_memory": "some avg10=1.0 avg60=2.0 avg300=3.0 total=42",
            "meminfo": "MemAvailable: 123 kB",
            "cpu_stat": "usage_usec 999\nnr_throttled 7",
            "memory_events": "high 1\noom 0",
        })
        self.assertNotEqual(initial["cpuinfo_sha256"], later["cpuinfo_sha256"])
        self.assertTrue(remote.stable_placement_unchanged(initial, later))
        self.assertTrue(analyzer.stable_placement_unchanged(initial, later))
        self.assertEqual(
            remote.stable_placement_identity(initial),
            analyzer.stable_placement_identity(initial),
        )
        self.assertEqual(
            remote.stable_placement_sha256(initial["placement_identity"]),
            analyzer.stable_placement_sha256(initial["placement_identity"]),
        )
        self.assertEqual(
            exporter.stable_host_class_id(initial),
            exporter.stable_host_class_id(later),
        )

    def test_every_allowlisted_placement_mutation_is_rejected(self) -> None:
        initial = snapshot([2, 4, 6, 8])

        def changed(mutator) -> dict:
            value = copy.deepcopy(initial)
            mutator(value)
            return value

        mutations = [
            lambda value: value.__setitem__("cpu_model", "Different CPU Model"),
            lambda value: value.__setitem__("logical_cpus", 256),
            lambda value: value["affinity"].__setitem__(0, 10),
            lambda value: value["cpu_topology"][0].__setitem__("core", 99),
            lambda value: value["topology_order"].reverse(),
            lambda value: value.__setitem__("cpuset_cpus", "2,4,6"),
            lambda value: value.__setitem__("memory_max", "65000000000"),
            lambda value: value["nvidia_devices"].append("/dev/nvidia0"),
        ]
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                value = changed(mutate)
                self.assertFalse(remote.stable_placement_snapshot_valid(value))
                self.assertFalse(remote.stable_placement_unchanged(initial, value))
                self.assertFalse(analyzer.stable_placement_snapshot_valid(value))
                self.assertFalse(analyzer.stable_placement_unchanged(initial, value))

    def test_rebound_valid_stable_identity_change_does_not_match(self) -> None:
        initial = snapshot([2, 4, 6, 8])
        changed = copy.deepcopy(initial)
        changed["cpu_model"] = "Different CPU Model"
        remote.bind_stable_placement_identity(changed)
        self.assertTrue(remote.stable_placement_snapshot_valid(changed))
        self.assertTrue(analyzer.stable_placement_snapshot_valid(changed))
        self.assertFalse(remote.stable_placement_unchanged(initial, changed))
        self.assertFalse(analyzer.stable_placement_unchanged(initial, changed))
        self.assertNotEqual(
            exporter.stable_host_class_id(initial),
            exporter.stable_host_class_id(changed),
        )

    def test_equivalent_cpuset_text_has_one_canonical_identity(self) -> None:
        initial = snapshot([2, 3, 4, 5])
        later = copy.deepcopy(initial)
        later["cpuset_cpus"] = "2-5"
        self.assertTrue(remote.stable_placement_snapshot_valid(later))
        self.assertTrue(analyzer.stable_placement_snapshot_valid(later))
        self.assertTrue(remote.stable_placement_unchanged(initial, later))
        self.assertTrue(analyzer.stable_placement_unchanged(initial, later))

    def test_exporter_rejects_self_hashed_stale_identity(self) -> None:
        value = snapshot([2, 4, 6, 8])
        value["cpu_model"] = "Different raw model"
        with self.assertRaises(ValueError):
            exporter.stable_host_class_id(value)


if __name__ == "__main__":
    unittest.main()
