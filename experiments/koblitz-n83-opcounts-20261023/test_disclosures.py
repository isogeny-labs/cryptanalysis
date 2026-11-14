"""Checks for disclosures.py (2026-11-06): it must agree with the frozen band and be reproducible."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
COMMITTED = HERE / "disclosures-20261106" / "disclosures.json"


class DisclosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        out = Path(cls.tmp.name)
        subprocess.run([sys.executable, str(HERE / "disclosures.py"), "--out", str(out)], check=True,
                       stdout=subprocess.DEVNULL)
        cls.fresh = json.loads((out / "disclosures.json").read_text())
        cls.fresh_md = (out / "disclosures.md").read_text()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_committed_output_is_reproduced(self):
        self.assertEqual(self.fresh, json.loads(COMMITTED.read_text()))
        self.assertEqual(self.fresh_md, (COMMITTED.parent / "disclosures.md").read_text())

    def test_frozen_map_equals_frozen_band(self):
        """The frozen-map gaps and the seed-20261023 intervals equal band-v2.md's analysis."""
        mc = self.fresh["rank_seed"]["bootstrap_monte_carlo"]["seed20261023_draws10000"]
        frozen = self.fresh["field_sensitivity"]["frozen_map"]
        for arm in ("S", "P"):
            for w in ("0", "0.1", "1"):
                self.assertAlmostEqual(frozen[arm]["gap_b0"][w], mc[arm][w][0]["ratio"], places=12)
                self.assertAlmostEqual(frozen[arm]["gap_b104"][w], mc[arm][w][1]["ratio"], places=12)
        band_md = (HERE / "run_github_39882571652/analysis_v2/band-v2.md").read_text()
        for arm in ("S", "P"):
            cell = mc[arm]["0.1"][0]
            self.assertIn("%.4g [%.4g, %.4g]" % (cell["ratio"], cell["ci95"][0], cell["ci95"][1]), band_md)

    def test_counter_table_sums_to_band_parts(self):
        totals = self.fresh["counter_totals_by_class"]
        counts = json.loads((HERE / "run_github_39882571652/panel/counts.json").read_text())
        for arm in ("S", "P"):
            units = counts["arms"][arm]["units"].values()
            group = sum(u["ec_add"] + u["ec_double"] for u in units) / len(units)
            self.assertAlmostEqual(totals[arm]["group"], group, places=6)

    def test_rulings_unchanged_under_field_sensitivity(self):
        frozen = self.fresh["field_sensitivity"]["frozen_map"]
        field = self.fresh["field_sensitivity"]["field_kinds_charged"]
        for table in (frozen, field):
            for arm in ("S", "P"):
                self.assertLess(table[arm]["gap_b0"]["0"], 1.0)
                self.assertGreater(table[arm]["gap_b0"]["0.1"], 1.0)
                self.assertGreater(table[arm]["gap_b104"]["1"], 1.0)
                self.assertLess(table[arm]["crossover_w_b0"], 0.1)
        for arm in ("S", "P"):
            self.assertLess(field[arm]["crossover_w_b0"], frozen[arm]["crossover_w_b0"])


if __name__ == "__main__":
    unittest.main()
