#!/usr/bin/env python3
"""Mutation controls for the finite guard; no sealed archive file is edited."""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

import verify


ARCHIVE = Path(__file__).resolve().parents[2] / "experiments/hecke-432-prime997-20261025"


class FiniteGuardControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.census = json.loads((ARCHIVE / "census.json").read_text())
        cls.image = json.loads((ARCHIVE / "image.json").read_text())

    def test_unmodified_archive(self) -> None:
        result = verify.verify_records(self.census, self.image)
        self.assertEqual(result["source_pairs"], 1800)
        self.assertEqual(result["histogram"], {"12": 6, "24": 60, "48": 6})

    def test_invalid_division_polynomial_root_rejected(self) -> None:
        census = copy.deepcopy(self.census)
        edge = census["rows"][0]["two_paths"][0][0]
        self.assertEqual(edge["kernel_x"], 605)
        edge["kernel_x"] = 606
        with self.assertRaisesRegex(verify.VerificationError, "invalid kernel root"):
            verify.verify_records(census, self.image)

    def test_wrong_source_j_rejected(self) -> None:
        image = copy.deepcopy(self.image)
        self.assertEqual(image["rows"][0]["source_j"], 17)
        image["rows"][0]["source_j"] = 0
        with self.assertRaisesRegex(verify.VerificationError, "source j metadata mismatch"):
            verify.verify_records(self.census, image)

    def test_projection_swap_remains_out_of_scope(self) -> None:
        image = copy.deepcopy(self.image)
        image["rows"][0]["projections"], image["rows"][1]["projections"] = (
            image["rows"][1]["projections"], image["rows"][0]["projections"])
        result = verify.verify_records(self.census, image)
        self.assertEqual(result["histogram"], {"12": 6, "24": 60, "48": 6})


if __name__ == "__main__":
    unittest.main()
