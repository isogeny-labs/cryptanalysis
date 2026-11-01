import argparse
import importlib.util
from fractions import Fraction
from pathlib import Path
import shutil
import tarfile
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
ANALYZER_PATH = (
    REPO
    / "experiments"
    / "performance-saturation-20261101"
    / "go"
    / "analyze_remote_ab.py"
)
SPEC = importlib.util.spec_from_file_location("go_remote_ab_analyzer", ANALYZER_PATH)
assert SPEC is not None and SPEC.loader is not None
ANALYZER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ANALYZER)


class ExactBootstrapTests(unittest.TestCase):
    def test_constant_distribution_is_exact(self) -> None:
        distribution = ANALYZER.exact_bootstrap_median_distribution(
            [Fraction(7, 3)] * 20
        )
        self.assertEqual(distribution, {Fraction(7, 3): 20**20})
        self.assertEqual(
            ANALYZER.exact_quantile(distribution, Fraction(1, 480)),
            Fraction(7, 3),
        )

    def test_order_statistic_distribution_matches_fixed_quantiles(self) -> None:
        distribution = ANALYZER.exact_bootstrap_median_distribution(
            [Fraction(value) for value in range(1, 21)]
        )
        self.assertEqual(sum(distribution.values()), 20**20)
        self.assertEqual(len(distribution), 39)
        self.assertEqual(
            ANALYZER.exact_quantile(distribution, Fraction(1, 480)), Fraction(5)
        )
        self.assertEqual(
            ANALYZER.exact_quantile(distribution, Fraction(1, 2)), Fraction(21, 2)
        )

    def test_hash_manifest_rejects_parent_traversal(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsafe archive member"):
            ANALYZER.parse_hash_manifest(("0" * 64 + "  ../escape\n").encode())


class RetainedEvidenceTests(unittest.TestCase):
    def test_v7_archive_reproduces_frozen_unsupported_verdict(self) -> None:
        root = (
            REPO
            / "experiments"
            / "performance-saturation-20261101"
            / "go"
        )
        evidence = root / "evidence" / "remote-run-v7"
        archive = evidence / "result.tar.gz"
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            with tarfile.open(archive, "r:gz") as bundle:
                for member in bundle.getmembers():
                    ANALYZER.safe_member_name(member.name)
                    self.assertTrue(member.isfile())
                    source = bundle.extractfile(member)
                    self.assertIsNotNone(source)
                    target = temp_path / member.name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with target.open("xb") as destination:
                        shutil.copyfileobj(source, destination)
            analysis = ANALYZER.analyze(
                argparse.Namespace(
                    run=temp_path / "go-ab-v6-run",
                    protocol=root / "protocol.v7.json",
                    receipt=evidence / "http-receipt.json",
                    archive=archive,
                    output=None,
                )
            )

        self.assertEqual(analysis["flow"]["completed"], 276)
        self.assertEqual(analysis["exact"]["matching_fingerprint_pairs"], 120)
        self.assertEqual(analysis["claims"]["C-ab-correct"], "supported")
        self.assertEqual(analysis["claims"]["C-ab-allocation"], "unsupported")
        self.assertEqual(analysis["verdict"]["overall"], "unsupported")
        first = analysis["cases"][0]["metrics"]
        self.assertEqual(
            first["ns/op"]["bonferroni_lower"]["numerator"], "16022082"
        )
        self.assertEqual(
            first["ns/op"]["bonferroni_lower"]["denominator"], "1098811"
        )


if __name__ == "__main__":
    unittest.main()
