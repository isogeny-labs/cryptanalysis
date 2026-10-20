import math
import hashlib
import json
import pathlib
import subprocess
import sys
import tarfile
import tempfile
import unittest

from audit_panels_v2 import audit_archive, interval_qualifies, recompute_pair_ratio


def make_panel_archive(directory, *, forged_ratio=False, repetitions=1, bool_serial=False):
    directory = pathlib.Path(directory)
    rules_path = directory / "sample-rules.json"
    rules = {"aa_acceptance": [0.9, 1.11], "repetitions": repetitions}
    rules_bytes = json.dumps(rules, sort_keys=True).encode()
    rules_path.write_bytes(rules_bytes)
    cases = [
        {"id": name, "reference": ["ref"], "candidate": ["ref"]}
        for name in ("cal_before", "cal_after")
    ] + [{"id": "compare", "reference": ["ref"], "candidate": ["cand"]}]
    manifest_bytes = json.dumps({"cases": cases}, sort_keys=True).encode()
    runs, pairs = [], []
    serial = 1
    for repeat in range(repetitions if isinstance(repetitions, int) and not isinstance(repetitions, bool) and repetitions > 0 else 1):
        for case in cases:
            arm_serials = {}
            for variant in ("reference", "candidate"):
                row_serial = True if bool_serial and serial == 1 else serial
                ms = 100.0
                runs.append({
                    "serial": row_serial, "repeat": repeat, "case": case["id"],
                    "variant": variant, "command": case[variant],
                    "status": "valid", "issues": [], "timed_out": False,
                    "returncode": 0, "online_ms": ms,
                    "fields": {"online_ms": str(ms)},
                })
                arm_serials[variant] = row_serial
                serial += 1
            pairs.append({
                "repeat": repeat, "case": case["id"], "status": "valid", "issues": [],
                "run_serials": arm_serials,
                "speedup": 9.0 if forged_ratio and case["id"] == "compare" else 1.0,
            })
    summary = {
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "artifact_sha256": {"/workspace/isolated-bench/panels/sample-rules.json":
                            hashlib.sha256(rules_bytes).hexdigest()},
        "valid_pairs": len(pairs), "expected_pairs": len(pairs),
    }
    root = "synthetic-panel"
    members = {
        "manifest.json": manifest_bytes,
        "summary.json": json.dumps(summary, sort_keys=True).encode(),
        "runs.jsonl": b"\n".join(json.dumps(row, sort_keys=True).encode() for row in runs) + b"\n",
        "pairs.jsonl": b"\n".join(json.dumps(row, sort_keys=True).encode() for row in pairs) + b"\n",
    }
    archive = directory / ("synthetic-panel.tar.gz")
    with tarfile.open(archive, "w:gz") as tf:
        for name, data in members.items():
            info = tarfile.TarInfo(f"{root}/{name}")
            info.size = len(data)
            tf.addfile(info, __import__("io").BytesIO(data))
    return archive


class PairRatioTests(unittest.TestCase):
    def test_recomputes_reference_over_candidate(self):
        self.assertEqual(recompute_pair_ratio(120.0, 100.0, 1.2), 1.2)

    def test_rejects_forged_pair_speedup(self):
        with self.assertRaisesRegex(ValueError, "does not match"):
            recompute_pair_ratio(120.0, 100.0, 0.8)

    def test_rejects_nonpositive_raw_times_even_when_ratio_is_positive(self):
        with self.assertRaisesRegex(ValueError, "positive"):
            recompute_pair_ratio(-120.0, -100.0, 1.2)

    def test_rejects_nonfinite_values(self):
        with self.assertRaisesRegex(ValueError, "finite"):
            recompute_pair_ratio(math.inf, 100.0, math.inf)


class DirectionalGateTests(unittest.TestCase):
    def test_a_a_failure_blocks_interval_above_one(self):
        self.assertFalse(interval_qualifies([1.01, 1.20], aa_passed=False))

    def test_a_a_failure_blocks_interval_below_one(self):
        self.assertFalse(interval_qualifies([0.80, 0.99], aa_passed=False))

    def test_both_directions_remain_available_after_a_a_pass(self):
        self.assertTrue(interval_qualifies([1.01, 1.20], aa_passed=True))
        self.assertTrue(interval_qualifies([0.80, 0.99], aa_passed=True))

    def test_malformed_interval_fails_closed(self):
        self.assertFalse(interval_qualifies([0.99, 1.01], aa_passed=True))
        self.assertFalse(interval_qualifies([1.2, 1.1], aa_passed=True))
        self.assertFalse(interval_qualifies([0.8, math.nan], aa_passed=True))


class ArchiveCliTests(unittest.TestCase):
    def test_malformed_supported_ledger_exits_nonzero_but_unsupported_is_inventory_only(self):
        script = pathlib.Path(__file__).with_name("audit_panels_v2.py")
        with tempfile.TemporaryDirectory() as temp:
            directory = pathlib.Path(temp)
            make_panel_archive(directory, forged_ratio=True)
            unsupported = directory / "unrelated.tar.gz"
            with tarfile.open(unsupported, "w:gz") as tf:
                payload = b"provenance only"
                info = tarfile.TarInfo("source.txt")
                info.size = len(payload)
                tf.addfile(info, __import__("io").BytesIO(payload))
            result = subprocess.run(
                [sys.executable, str(script), str(directory)],
                text=True, capture_output=True, check=False,
            )
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("invalid=1", result.stdout)
            self.assertIn("unsupported=1", result.stdout)
            self.assertIn("INVALID\tsynthetic-panel.tar.gz", result.stdout)
            self.assertIn("UNSUPPORTED\tunrelated.tar.gz", result.stdout)

        with tempfile.TemporaryDirectory() as temp:
            directory = pathlib.Path(temp)
            with tarfile.open(directory / "unsupported.tar.gz", "w:gz") as tf:
                payload = b"provenance only"
                info = tarfile.TarInfo("source.txt")
                info.size = len(payload)
                tf.addfile(info, __import__("io").BytesIO(payload))
            result = subprocess.run(
                [sys.executable, str(script), str(directory)],
                text=True, capture_output=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("archives=1 supported=0 unsupported=1 invalid=0", result.stdout)

    def test_bool_run_serial_is_invalid(self):
        with tempfile.TemporaryDirectory() as temp:
            archive = make_panel_archive(temp, bool_serial=True)
            with self.assertRaisesRegex(ValueError, "serials.*noninteger"):
                audit_archive(archive, pathlib.Path(temp))

    def test_repetitions_must_be_positive_non_bool_integer(self):
        for repetitions in (0, -1, 1.5, True):
            with self.subTest(repetitions=repetitions), tempfile.TemporaryDirectory() as temp:
                archive = make_panel_archive(temp, repetitions=repetitions)
                with self.assertRaisesRegex(ValueError, "positive integer"):
                    audit_archive(archive, pathlib.Path(temp))


if __name__ == "__main__":
    unittest.main()
