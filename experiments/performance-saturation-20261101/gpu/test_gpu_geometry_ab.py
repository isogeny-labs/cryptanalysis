#!/usr/bin/env python3
"""Focused standard-library tests for the frozen GPU geometry analyzer."""

from __future__ import annotations

import importlib.util
import sqlite3
import sys
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "analyze_gpu_geometry_ab", HERE / "analyze_gpu_geometry_ab.py"
)
assert SPEC is not None and SPEC.loader is not None
MOD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MOD
SPEC.loader.exec_module(MOD)


def make_trace(path: Path, blocks_per_sm: int) -> None:
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE StringIds (id INTEGER PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE CUPTI_ACTIVITY_KIND_KERNEL (
            start INTEGER NOT NULL,
            shortName INTEGER NOT NULL,
            gridX INTEGER NOT NULL, gridY INTEGER NOT NULL, gridZ INTEGER NOT NULL,
            blockX INTEGER NOT NULL, blockY INTEGER NOT NULL, blockZ INTEGER NOT NULL,
            registersPerThread INTEGER NOT NULL,
            staticSharedMemory INTEGER NOT NULL,
            dynamicSharedMemory INTEGER NOT NULL,
            localMemoryPerThread INTEGER NOT NULL
        );
        """
    )
    names = {
        "f4e_gather": 1,
        "f4e_panel_block": 2,
        "f4e_materialise": 3,
        "f4e_update": 4,
        "f4e_low": 5,
    }
    connection.executemany(
        "INSERT INTO StringIds(id, value) VALUES (?, ?)",
        [(identifier, name) for name, identifier in names.items()],
    )
    rows = []
    start = 0
    for launch in range(MOD.EXPECTED_UPDATE_LAUNCHES):
        remaining_words = MOD.EXPECTED_UPDATE_LAUNCHES - launch
        materialise_grid = (remaining_words + 127) // 128
        tiles = (remaining_words + 31) // 32
        update_grid = tiles * MOD.parts_for(170, tiles, blocks_per_sm)
        rows.extend([
            (start, names["f4e_gather"], 658, 1, 1, 256, 1, 1, 39, 0, 0, 0),
            (start + 1, names["f4e_panel_block"], 1, 1, 1, 1024, 1, 1, 47, 47392, 0, 0),
            (start + 2, names["f4e_materialise"], materialise_grid, 1, 1, 128, 1, 1, 40, 0, 0, 0),
            (start + 3, names["f4e_update"], update_grid, 1, 1, 256, 1, 1, 31, 16384, 0, 0),
        ])
        start += 4
    rows.append((start, names["f4e_low"], 658, 1, 1, 256, 1, 1, 30, 0, 0, 0))
    connection.executemany(
        """
        INSERT INTO CUPTI_ACTIVITY_KIND_KERNEL
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    connection.commit()
    connection.close()


class GeometryAnalyzerTests(unittest.TestCase):
    def test_registered_grid_math(self) -> None:
        self.assertEqual(MOD.parts_for(170, 92, 4), 8)
        self.assertEqual(MOD.parts_for(170, 92, 6), 12)
        self.assertEqual(MOD.infer_tiles(23, 736, 170), 92)

    def test_exact_bootstrap_identity(self) -> None:
        values = [Fraction(index, 10) for index in range(10, 16)]
        self.assertEqual(
            MOD.bootstrap_interval(values, values),
            (Fraction(1, 1), Fraction(1, 1)),
        )

    def test_primary_must_strictly_clear_same_session_aa_floor(self) -> None:
        effect = Fraction(103, 100)
        noise = Fraction(101, 100)
        self.assertFalse(MOD.primary_geometry_pass(effect, noise, noise))
        self.assertTrue(MOD.primary_geometry_pass(effect, Fraction(102, 100), noise))

    def test_aa_interval_must_contain_identity(self) -> None:
        self.assertTrue(MOD.aa_interval_admissible(Fraction(99, 100), Fraction(101, 100)))
        self.assertFalse(MOD.aa_interval_admissible(Fraction(1001, 1000), Fraction(101, 100)))

    def test_wide_aa_interval_containing_identity_is_inadmissible(self) -> None:
        self.assertFalse(MOD.aa_interval_admissible(Fraction(9, 10), Fraction(11, 10)))
        self.assertFalse(MOD.aa_interval_admissible(Fraction(49, 50), Fraction(51, 50)))

    def test_mechanism_gate_accepts_only_registered_change(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline = root / "baseline.sqlite"
            candidate = root / "candidate.sqlite"
            make_trace(baseline, 4)
            make_trace(candidate, 6)
            result = MOD.mechanism_gate(baseline, candidate, 170)
            self.assertEqual(result["update_launches_per_arm"], 2941)
            self.assertGreater(result["changed_update_launches"], 0)
            self.assertEqual(result["transitions"]["92:736->1104"], 29)

    def test_mechanism_gate_rejects_baseline_grid_in_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline = root / "baseline.sqlite"
            candidate = root / "candidate.sqlite"
            make_trace(baseline, 4)
            make_trace(candidate, 4)
            with self.assertRaises(MOD.GateError):
                MOD.mechanism_gate(baseline, candidate, 170)


if __name__ == "__main__":
    unittest.main()
