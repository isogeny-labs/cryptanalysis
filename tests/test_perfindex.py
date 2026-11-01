import importlib.util
import sys
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "cryptanalysis_perfindex", ROOT / "scripts" / "perf" / "perfindex.py"
)
assert SPEC is not None and SPEC.loader is not None
PERFINDEX = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PERFINDEX
SPEC.loader.exec_module(PERFINDEX)


class ExactFilterTests(unittest.TestCase):
    KERNELS = [
        {"id": "gf2_la/rref_random_4940x8357", "area": "gf2_la"},
        {"id": "gf2_la/rref_random_4940x8357_w17", "area": "gf2_la"},
        {"id": "gf2_la/rref_macaulay_k5m3d5", "area": "gf2_la"},
    ]

    @mock.patch.object(PERFINDEX, "run_json", return_value=KERNELS)
    def test_substring_filter_keeps_legacy_prefix_matches(self, _run_json):
        selected = PERFINDEX.list_kernels(
            "perfbench", False, ["gf2_la/rref_random_4940x8357"]
        )
        self.assertEqual(
            [row["id"] for row in selected],
            [
                "gf2_la/rref_random_4940x8357",
                "gf2_la/rref_random_4940x8357_w17",
            ],
        )

    @mock.patch.object(PERFINDEX, "run_json", return_value=KERNELS)
    def test_exact_filter_excludes_suffix_variant(self, _run_json):
        selected = PERFINDEX.list_kernels(
            "perfbench", False, [], ["gf2_la/rref_random_4940x8357"]
        )
        self.assertEqual(
            [row["id"] for row in selected],
            ["gf2_la/rref_random_4940x8357"],
        )

    @mock.patch.object(PERFINDEX, "run_json", return_value=KERNELS)
    def test_exact_filter_requires_every_requested_id(self, _run_json):
        with self.assertRaisesRegex(SystemExit, "not present in registry: missing"):
            PERFINDEX.list_kernels("perfbench", False, [], ["missing"])

    @mock.patch.object(PERFINDEX, "run_json", return_value=KERNELS)
    def test_exact_filter_rejects_duplicate_requests(self, _run_json):
        with self.assertRaisesRegex(SystemExit, "duplicate kernel IDs"):
            PERFINDEX.list_kernels("perfbench", False, [], ["same", "same"])


if __name__ == "__main__":
    unittest.main()
