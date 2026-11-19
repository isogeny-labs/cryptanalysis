#!/usr/bin/env python3
"""Synthetic and real-tool controls for the heuristic PARI relation proposer."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import lift_builder
import relation_pari as proposer
from test_relation_certificate import synthetic_source


INDEPENDENT_ROW = {
    "row_id": "control-independent-389a1",
    "r": 2,
    "ainvs": [0, 1, 1, -2, 0],
    "selected_points": [[0, 0], [1, 0]],
}


def fake_transcript(overrides=None, omit=(), duplicate=None) -> str:
    values = {
        "STATUS": "OK",
        "R": "2",
        "PARISIZEMAX": str(proposer.PARISIZEMAX),
        "CONSTRUCTION_DISC": "389",
        "MINIMAL_DISC": "389",
        "CURVE_MAP_OK": "1",
        "POINTS_ON_CONSTRUCTION_OK": "1",
        "POINTS_ON_MINIMAL_OK": "1",
        "POINT_ROUNDTRIP_OK": "1",
        "SCHEDULE_COUNT": str(len(proposer.SCHEDULE)),
        "MIN_A1": "0", "MIN_A2": "1", "MIN_A3": "1", "MIN_A4": "-2", "MIN_A6": "0",
        "TRANS_U_NUM": "1", "TRANS_U_DEN": "1",
        "TRANS_R_NUM": "0", "TRANS_R_DEN": "1",
        "TRANS_S_NUM": "0", "TRANS_S_DEN": "1",
        "TRANS_T_NUM": "0", "TRANS_T_DEN": "1",
    }
    for index, (precision, scale) in enumerate(proposer.SCHEDULE, 1):
        values[f"S{index}_PRECISION_BITS"] = str(precision)
        values[f"S{index}_REALPRECISION"] = str(max(30, int(precision * 0.301)))
        values[f"S{index}_SCALE_BITS"] = str(scale)
        for i in range(1, 3):
            for j in range(1, 3):
                values[f"S{index}_H_{i}_{j}"] = "1.0" if i == j else "0.E-100"
                values[f"S{index}_G_{i}_{j}"] = str((1 << scale) + 3) if i == j else "0"
                values[f"S{index}_T_{i}_{j}"] = "1" if i == j else "0"
    values.update(overrides or {})
    omitted = set(omit)
    body = [f"{key}={value}" for key, value in values.items() if key not in omitted]
    if duplicate is not None:
        body.append(f"{duplicate}={values[duplicate]}")
    return "\n".join((proposer.BEGIN, *body, proposer.END, ""))


def install_fake(
    directory: Path,
    stdout: str,
    *,
    returncode=0,
    sleep_seconds=0,
    version="2.17.2-fake",
) -> Path:
    path = directory / f"fake-gp-{len(list(directory.iterdir()))}"
    source = f'''#!/usr/bin/env python3
import sys
import time
if "--version" in sys.argv:
    print("GP/PARI CALCULATOR Version {version}")
    raise SystemExit(0)
sys.stdin.read()
time.sleep({sleep_seconds!r})
sys.stdout.write({stdout!r})
raise SystemExit({returncode!r})
'''
    path.write_text(source, encoding="utf-8")
    path.chmod(0o755)
    return path


class ProtocolTests(unittest.TestCase):
    def test_strict_projection_prohibits_source_scalars(self):
        proposer.validate_row(INDEPENDENT_ROW)
        for leaked_key in (
            "selected_source_scalars_for_replay_only",
            "ordered_scalars",
            "target_scalar",
            "source",
        ):
            changed = {**INDEPENDENT_ROW, leaked_key: [1, 2]}
            with self.subTest(leaked_key=leaked_key), self.assertRaisesRegex(
                ValueError, "source scalars and metadata are prohibited"
            ):
                proposer.validate_row(changed)

    def test_script_freezes_schedule_stack_and_column_lll(self):
        _, _, ainvs, points = proposer.validate_row(INDEPENDENT_ROW)
        script = proposer.make_script(ainvs, points)
        self.assertIn("default(parisizemax,2147483648)", script)
        self.assertIn("qflllgram(G1,1)", script)
        self.assertIn("H1=(H1+H1~)/2", script)
        for precision, scale in proposer.SCHEDULE:
            self.assertIn(f"default(realbitprecision,{precision})", script)
            self.assertIn(f"round(2^{scale}*", script)
        for forbidden in ("selected_source_scalars", "ordered_scalars", "target_scalar"):
            self.assertNotIn(forbidden, script)

    def test_candidate_enumeration_is_bounded_and_column_oriented(self):
        schedule = {
            "schedule_index": 1,
            "precision_bits": 256,
            "scale_bits": 64,
            "integer_gram": [[10, 0], [0, 20]],
            "lll_transform": [[2, 1], [3, 1]],
        }
        candidates, counts = proposer._enumerate_candidates(schedule, 2)
        vectors = [candidate["vector"] for candidate in candidates]
        self.assertIn([2, 3], vectors)
        self.assertLessEqual(len(candidates), proposer.PER_SCHEDULE_CANDIDATE_CAP)
        self.assertEqual(counts["sign_canonical_alpha_generated"], 4)


class FakeToolTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="xedni-relation-pari-")
        self.directory = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def run_fake(self, transcript, *, timeout=2.0, returncode=0, sleep_seconds=0, version="2.17.2-fake"):
        executable = install_fake(
            self.directory,
            transcript,
            returncode=returncode,
            sleep_seconds=sleep_seconds,
            version=version,
        )
        tool = proposer.invariants.probe_tool(str(executable))
        return proposer.process_row(INDEPENDENT_ROW, tool, timeout)

    def test_independent_fake_completes_but_counts_nothing(self):
        result = self.run_fake(fake_transcript())
        self.assertEqual((result["status"], result["reason"]), ("OK", "heuristic_search_complete"))
        self.assertEqual(result["exact_rational_relations"], [])
        self.assertEqual(result["counted_relation_count"], 0)
        self.assertTrue(result["heuristic_only"])
        self.assertFalse(result["uses_source_scalars"])
        self.assertEqual(result["proposal_accounting"]["qflll_calls"], 3)
        self.assertEqual(result["execution"]["returncode"], 0)
        self.assertEqual(
            result["execution"]["script_sha256"],
            hashlib.sha256(result["execution"]["script"].encode()).hexdigest(),
        )

    def test_parser_and_semantic_mutations_fail_closed(self):
        cases = [
            (fake_transcript(omit=("S1_H_1_1",)), "marker keys differ"),
            (fake_transcript(duplicate="S1_G_1_1"), "duplicate"),
            (fake_transcript({"S1_G_1_1": "7"}), "integer Gram mismatch"),
            (fake_transcript({"S1_T_2_2": "0"}), "not unimodular"),
            (
                fake_transcript(
                    {
                        "S1_H_1_1": "2.0",
                        "S1_G_1_1": str(2 * (1 << 64) + 3),
                    }
                ),
                "height_precision_instability",
            ),
            (fake_transcript({"POINT_ROUNDTRIP_OK": "0"}), "point-map flag failed"),
        ]
        for transcript, error_fragment in cases:
            with self.subTest(error_fragment=error_fragment):
                result = self.run_fake(transcript)
                self.assertEqual(result["status"], "UNKNOWN")
                self.assertEqual(result["reason"], "parser_or_semantic_error")
                self.assertIn(error_fragment, result["error"])

    def test_tool_timeout_nonzero_version_and_missing_fail_closed(self):
        timed = self.run_fake(fake_transcript(), timeout=0.03, sleep_seconds=1)
        self.assertEqual(timed["reason"], "timeout")
        self.assertTrue(timed["execution"]["timed_out"])
        self.assertEqual(self.run_fake(fake_transcript(), returncode=9)["reason"], "tool_nonzero_exit")
        self.assertEqual(
            self.run_fake(fake_transcript(), version="9.9.9-fake")["reason"],
            "unsupported_pari_version",
        )
        tool = proposer.invariants.probe_tool(str(self.directory / "missing-gp"))
        self.assertEqual(proposer.process_row(INDEPENDENT_ROW, tool, 2.0)["reason"], "missing_tool")

    def test_cli_jsonl_is_canonical_and_preserves_order(self):
        executable = install_fake(self.directory, fake_transcript())
        raw = json.dumps(INDEPENDENT_ROW, separators=(",", ":")) + "\n{bad-json\n"
        completed = subprocess.run(
            [sys.executable, str(Path(proposer.__file__)), "--gp", str(executable)],
            input=raw,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        lines = completed.stdout.splitlines()
        parsed = [json.loads(line) for line in lines]
        self.assertEqual([item["row_id"] for item in parsed], [INDEPENDENT_ROW["row_id"], "invalid-json-line-2"])
        self.assertEqual([item["reason"] for item in parsed], ["heuristic_search_complete", "invalid_json"])
        for line, value in zip(lines, parsed):
            self.assertEqual(line, json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True))


@unittest.skipUnless(shutil.which("gp"), "real PARI/GP controls require gp")
class RealPariControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = proposer.invariants.probe_tool("gp")

    def test_planted_relations_r2_through_r6_are_proposed_and_exactly_replayed(self):
        for r in range(2, 7):
            source, planted = synthetic_source(r)
            lift = lift_builder.build_lift(source, r, "balanced")
            row = {
                "row_id": lift["row_id"],
                "r": r,
                "ainvs": lift["ainvs"],
                "selected_points": lift["points"],
            }
            with self.subTest(r=r):
                report = proposer.process_row(row, self.tool, 120.0)
                self.assertEqual((report["status"], report["reason"]), ("OK", "heuristic_search_complete"), report)
                canonical = proposer._primitive(planted)
                self.assertIn(canonical, report["exact_rational_relations"])
                self.assertEqual(report["counted_relation_count"], 0)
                self.assertGreaterEqual(report["proposal_accounting"]["exact_rational_relation_count"], 1)

    def test_independent_rank_three_control_has_no_exact_relation_in_budget(self):
        row = {
            "row_id": "control-independent-rank3",
            "r": 3,
            "ainvs": [0, 0, 1, -7, 6],
            "selected_points": [[-1, 3], [-3, 0], [11, 35]],
        }
        report = proposer.process_row(row, self.tool, 120.0)
        self.assertEqual((report["status"], report["reason"]), ("OK", "heuristic_search_complete"), report)
        self.assertEqual(report["exact_rational_relations"], [])
        self.assertEqual(report["finder_outcome"], "NO_EXACT_Q_RELATION_WITHIN_FROZEN_BUDGET")

    def test_relation_certificate_composition_is_required_for_counting(self):
        source, _ = synthetic_source(2)
        lift = lift_builder.build_lift(source, 2, "balanced")
        row = {
            "row_id": lift["row_id"],
            "r": 2,
            "ainvs": lift["ainvs"],
            "selected_points": lift["points"],
        }
        report = proposer.process_row(row, self.tool, 120.0)
        self.assertEqual(report["counted_relation_count"], 0)
        composed = proposer.compose_with_relation_certificate(report, lift, source)
        self.assertGreaterEqual(composed["counted_relation_count"], 1)
        self.assertFalse(composed["phase_separation"]["proposer_used_source_scalars"])
        self.assertFalse(composed["phase_separation"]["heuristic_proposer_is_certificate"])
        mutated = copy.deepcopy(report)
        mutated["input_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "not bound"):
            proposer.compose_with_relation_certificate(mutated, lift, source)


if __name__ == "__main__":
    unittest.main()
