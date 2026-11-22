#!/usr/bin/env python3
"""Controls for the fail-closed PARI invariant adapter."""

from __future__ import annotations

from decimal import Decimal, localcontext
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import invariants_pari as adapter


ROW_37 = {
    "row_id": "control-37a1",
    "ainvs": [0, 0, 1, -1, 0],
    "selected_points": [[0, 0]],
}


def valid_transcript(overrides=None, omit=(), duplicate=None) -> str:
    height = "0.05111140823996884023588609975694202160953820228085296424924276152109705166560192612627628016614501315872683015691314"
    with localcontext() as context:
        context.prec = 150
        rho = format(Decimal(37).ln() / Decimal(height), "f")
    values = {
        "STATUS": "OK",
        "REALBITPRECISION": "384",
        "REALPRECISION": "115",
        "STABILITY_REALBITPRECISION": "256",
        "STABILITY_REALPRECISION": "77",
        "CONSTRUCTION_DISC": "37",
        "MINIMAL_DISC": "37",
        "MINIMAL_DISC_IDEAL": "37",
        "CONDUCTOR": "37",
        "MIN_A1": "0", "MIN_A2": "0", "MIN_A3": "1", "MIN_A4": "-1", "MIN_A6": "0",
        "TRANS_U_NUM": "1", "TRANS_U_DEN": "1",
        "TRANS_R_NUM": "0", "TRANS_R_DEN": "1",
        "TRANS_S_NUM": "0", "TRANS_S_DEN": "1",
        "TRANS_T_NUM": "0", "TRANS_T_DEN": "1",
        "CURVE_MAP_OK": "1",
        "MINIMAL_IDEMPOTENT_OK": "1",
        "MINIMAL_TRIVIAL_MAP_OK": "1",
        "DISC_RELATION_OK": "1",
        "MINIMAL_DISC_IDEAL_OK": "1",
        "POINT_COUNT": "1",
        "P1_X_NUM": "0", "P1_X_DEN": "1", "P1_Y_NUM": "0", "P1_Y_DEN": "1",
        "P1_ON_CONSTRUCTION": "1", "P1_ON_MINIMAL": "1", "P1_ROUNDTRIP": "1",
        "P1_HEIGHT": height,
        "P1_HEIGHT_TYPE": "t_REAL",
        "P1_HEIGHT_PRECISION": "134",
        "P1_CONSTRUCTION_HEIGHT": height,
        "P1_CONSTRUCTION_HEIGHT_TYPE": "t_REAL",
        "P1_CONSTRUCTION_HEIGHT_PRECISION": "134",
        "P1_HEIGHT_DELTA": "0.E-136",
        "P1_STABILITY_HEIGHT": height,
        "P1_STABILITY_CONSTRUCTION_HEIGHT": height,
        "MAX_HEIGHT": height,
        "MAX_HEIGHT_PRECISION": "134",
        "RHO": rho,
        "RHO_PRECISION": "115",
        "STABILITY_MAX_HEIGHT": height,
        "STABILITY_RHO": rho,
        "GRAM_1_1": height,
        "STABILITY_GRAM_1_1": height,
        "HEIGHT_GRAM_DETERMINANT": height,
        "HEIGHT_GRAM_DETERMINANT_PRECISION": "134",
        "STABILITY_HEIGHT_GRAM_DETERMINANT": height,
    }
    values.update(overrides or {})
    omitted = set(omit)
    body = [f"{key}={value}" for key, value in values.items() if key not in omitted]
    if duplicate is not None:
        body.append(f"{duplicate}={values[duplicate]}")
    return "\n".join((adapter.BEGIN, *body, adapter.END, ""))


def install_fake(
    directory: Path, stdout: str, *, returncode=0, sleep_seconds=0, version="2.17.2-fake"
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


class ExactInputTests(unittest.TestCase):
    def test_rational_input_is_exact_and_canonical(self):
        row = {
            "row_id": "rational",
            "ainvs": [0, 0, 1, -1, 0],
            "selected_points": [["1/4", "-5/8"]],
        }
        _, _, points = adapter.validate_row(row)
        self.assertEqual(points, ((Fraction(1, 4), Fraction(-5, 8)),))
        for bad in ("2/4", "1/1", "+1", "01", "-0", 0.25, True):
            mutated = {**row, "selected_points": [[bad, "-5/8"]]}
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                adapter.validate_row(mutated)

    def test_exact_discriminants_and_map_formula(self):
        self.assertEqual(adapter.curve_discriminant((6, 6, 12, 55, 233)), -2031616)
        self.assertEqual(adapter.curve_discriminant((0, 0, 0, 1, 1)), -496)
        mapped = adapter.map_point_to_new(
            (Fraction(-4), Fraction(-3)),
            (Fraction(2), Fraction(-5), Fraction(-3), Fraction(9)),
        )
        self.assertEqual(mapped, (Fraction(1, 4), Fraction(-9, 8)))
        self.assertTrue(adapter.on_curve((0, 0, 0, 1, 1), mapped))

    def test_generated_script_uses_documented_exact_and_stability_checks(self):
        script = adapter.make_script((6, 6, 12, 55, 233), ((Fraction(-5), Fraction(17)),), 384, 256)
        for fragment in (
            "ellminimalmodel(E,&V)", "ellchangecurve(E,V)", "ellchangepoint(PTS[i],V)",
            "ellchangepointinv(MPTS[i],V)", "ellminimaldisc(E)", "ellheight(M,MPTS[i])",
            "ellheightmatrix(M,MPTS)", "ellglobalred(M)[1]",
            "E.disc==M.disc*V[1]^12", "default(realbitprecision,256)",
            "default(realbitprecision,384)",
        ):
            self.assertIn(fragment, script)
        self.assertNotIn("ellchangepoint(E,", script)

    def test_stable_decimal_key_and_tie_rule_are_deterministic(self):
        value = Decimal("3.258229096431299821788496303606563033108549")
        self.assertEqual(
            adapter.stable_decimal_key(value),
            "3.258229096431299821788496303606563033109E+0",
        )
        self.assertEqual(adapter.stable_decimal_key(value), adapter.stable_decimal_key(value))
        self.assertEqual(
            adapter.stable_selection_components(adapter.stable_decimal_key(value)),
            (0, "3258229096431299821788496303606563033109"),
        )


class ParserMutationTests(unittest.TestCase):
    def test_valid_parser_and_scientific_space(self):
        transcript = valid_transcript({"P1_HEIGHT_DELTA": "1.25 E-120"})
        parsed = adapter.parse_transcript(transcript, 1)
        value, normalized = adapter._parse_decimal(parsed, "P1_HEIGHT_DELTA")
        self.assertEqual(value, Decimal("1.25E-120"))
        self.assertEqual(normalized, "1.25E-120")

    def test_parser_rejects_missing_duplicate_and_markers(self):
        mutations = [
            valid_transcript(omit=("P1_HEIGHT",)),
            valid_transcript(duplicate="MINIMAL_DISC"),
            valid_transcript().replace(adapter.END, "MUTATED_END"),
            valid_transcript() + adapter.END + "\n",
        ]
        for transcript in mutations:
            with self.subTest(transcript=transcript[:80]), self.assertRaises(ValueError):
                adapter.parse_transcript(transcript, 1)


class FakeExecutionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="xedni-invariant-tests-")
        self.directory = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def run_fake(self, transcript: str, *, returncode=0, sleep_seconds=0, timeout=2.0):
        executable = install_fake(self.directory, transcript, returncode=returncode, sleep_seconds=sleep_seconds)
        return adapter.process_row(ROW_37, adapter.probe_tool(str(executable)), timeout, 384, 256)

    def test_success_retains_audit_and_numeric_semantics(self):
        result = self.run_fake(valid_transcript())
        self.assertEqual((result["status"], result["reason"]), ("OK", "computed"))
        self.assertEqual(result["minimal_model"]["ainvs"], ["0", "0", "1", "-1", "0"])
        self.assertEqual(result["mapped_points"][0]["minimal_point"], ["0", "0"])
        self.assertFalse(result["height_semantics"]["certified_real_interval"])
        self.assertEqual(result["conductor"], "37")
        self.assertEqual(
            result["height_gram_matrix"],
            [[result["mapped_points"][0]["canonical_height"]]],
        )
        self.assertFalse(result["selected_height_determinant"]["is_regulator"])
        self.assertFalse(result["selected_height_determinant"]["certified_real_interval"])
        self.assertEqual(
            result["selected_height_determinant"]["numerical_approximation"],
            result["height_gram_matrix"][0][0],
        )
        self.assertEqual(
            result["mordell_weil_regulator"]["status"],
            "UNAVAILABLE_BASIS_NOT_ESTABLISHED",
        )
        self.assertIsNone(result["mordell_weil_regulator"]["value"])
        self.assertEqual(
            result["minimum_height_lower_bound"]["status"],
            "UNAVAILABLE_NOT_CERTIFIED",
        )
        self.assertFalse(result["minimum_height_lower_bound"]["certified"])
        self.assertIsNone(result["minimum_height_lower_bound"]["value"])
        self.assertRegex(result["invariant_evidence_sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(result["selection_evidence_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(result["stable_selection_key"][2], result["candidate_sha256"])
        execution = result["execution"]
        self.assertEqual(execution["returncode"], 0)
        self.assertEqual(execution["script_sha256"], hashlib.sha256(execution["script"].encode()).hexdigest())
        self.assertIn(adapter.BEGIN, execution["stdout"])
        self.assertGreaterEqual(execution["wall_ns"], 0)
        self.assertEqual(result["tool"]["version_returncode"], 0)

    def test_bad_exact_maps_fail_closed(self):
        cases = [
            ({"CURVE_MAP_OK": "0"}, "bad_minimal_model_map"),
            ({"P1_ROUNDTRIP": "0"}, "bad_point_map"),
            ({"P1_X_NUM": "1"}, "bad_point_map"),
            ({"MINIMAL_DISC_IDEAL": "38"}, "bad_minimal_discriminant"),
        ]
        for mutation, reason in cases:
            with self.subTest(mutation=mutation):
                result = self.run_fake(valid_transcript(mutation))
                self.assertEqual((result["status"], result["reason"]), ("UNKNOWN", reason))

    def test_zero_nonfinite_missing_and_unstable_heights_fail_closed(self):
        zero = {
            "P1_HEIGHT": "0", "P1_HEIGHT_TYPE": "t_INT", "P1_HEIGHT_PRECISION": "0",
            "P1_CONSTRUCTION_HEIGHT": "0", "P1_CONSTRUCTION_HEIGHT_TYPE": "t_INT",
            "P1_CONSTRUCTION_HEIGHT_PRECISION": "0", "P1_HEIGHT_DELTA": "0",
            "P1_STABILITY_HEIGHT": "0", "P1_STABILITY_CONSTRUCTION_HEIGHT": "0",
            "MAX_HEIGHT": "0", "MAX_HEIGHT_PRECISION": "0", "RHO": "0", "RHO_PRECISION": "0",
            "STABILITY_MAX_HEIGHT": "0", "STABILITY_RHO": "0",
        }
        self.assertEqual(self.run_fake(valid_transcript(zero))["reason"], "zero_height")
        nonfinite = {
            "P1_HEIGHT": "NaN", "P1_CONSTRUCTION_HEIGHT": "NaN", "P1_HEIGHT_DELTA": "NaN",
            "P1_STABILITY_HEIGHT": "NaN", "P1_STABILITY_CONSTRUCTION_HEIGHT": "NaN",
            "MAX_HEIGHT": "NaN", "RHO": "NaN", "STABILITY_MAX_HEIGHT": "NaN",
            "STABILITY_RHO": "NaN",
        }
        self.assertEqual(self.run_fake(valid_transcript(nonfinite))["reason"], "nonfinite_height")
        self.assertEqual(self.run_fake(valid_transcript(omit=("P1_HEIGHT",)))["reason"], "parser_error")
        unstable = {"P1_STABILITY_HEIGHT": "0.06", "P1_STABILITY_CONSTRUCTION_HEIGHT": "0.06"}
        self.assertEqual(
            self.run_fake(valid_transcript(unstable))["reason"], "height_precision_instability"
        )
        gram_unstable = {"STABILITY_GRAM_1_1": "0.06"}
        self.assertEqual(
            self.run_fake(valid_transcript(gram_unstable))["reason"],
            "height_gram_precision_instability",
        )
        determinant_unstable = {"STABILITY_HEIGHT_GRAM_DETERMINANT": "0.06"}
        self.assertEqual(
            self.run_fake(valid_transcript(determinant_unstable))["reason"],
            "height_gram_determinant_precision_instability",
        )

    def test_timeout_nonzero_and_missing_tool_fail_closed(self):
        timed = self.run_fake(valid_transcript(), sleep_seconds=1, timeout=0.03)
        self.assertEqual((timed["status"], timed["reason"]), ("UNKNOWN", "timeout"))
        self.assertTrue(timed["execution"]["timed_out"])
        nonzero = self.run_fake(valid_transcript(), returncode=7)
        self.assertEqual((nonzero["status"], nonzero["reason"]), ("UNKNOWN", "tool_nonzero_exit"))
        missing_tool = adapter.probe_tool(str(self.directory / "missing-gp"))
        missing = adapter.process_row(ROW_37, missing_tool, 2.0, 384, 256)
        self.assertEqual((missing["status"], missing["reason"]), ("UNKNOWN", "missing_tool"))
        wrong = install_fake(self.directory, valid_transcript(), version="9.9.9-fake")
        wrong_version = adapter.process_row(
            ROW_37, adapter.probe_tool(str(wrong)), 2.0, 384, 256
        )
        self.assertEqual(wrong_version["reason"], "unsupported_pari_version")

    def test_preflight_rejects_singular_offcurve_and_malformed(self):
        missing = adapter.probe_tool(str(self.directory / "missing-gp"))
        singular = {"row_id": "singular", "ainvs": [0, 0, 0, 0, 0], "selected_points": [[0, 0]]}
        self.assertEqual(adapter.process_row(singular, missing, 2.0, 384, 256)["reason"], "singular_curve")
        offcurve = {**ROW_37, "selected_points": [[0, 1]]}
        self.assertEqual(
            adapter.process_row(offcurve, missing, 2.0, 384, 256)["reason"],
            "point_not_on_construction_curve",
        )
        malformed = {**ROW_37, "selected_points": []}
        self.assertEqual(adapter.process_row(malformed, missing, 2.0, 384, 256)["reason"], "invalid_input")

    def test_cli_jsonl_order_invalid_json_and_canonical_output(self):
        executable = install_fake(self.directory, valid_transcript())
        first = json.dumps(ROW_37, separators=(",", ":"))
        completed = subprocess.run(
            [sys.executable, str(Path(adapter.__file__)), "--gp", str(executable)],
            input=first + "\n{mutated-json\n",
            capture_output=True, text=True, timeout=10, check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        lines = completed.stdout.splitlines()
        parsed = [json.loads(line) for line in lines]
        self.assertEqual([item["row_id"] for item in parsed], ["control-37a1", "invalid-json-line-2"])
        self.assertEqual([item["reason"] for item in parsed], ["computed", "invalid_json"])
        for line, value in zip(lines, parsed):
            self.assertEqual(line, json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True))


@unittest.skipUnless(shutil.which("gp"), "real PARI/GP control requires gp")
class RealPariControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = adapter.probe_tool("gp")

    def test_documented_nonminimal_model_and_exact_maps(self):
        row = {
            "row_id": "control-pari-doc-nonminimal",
            "ainvs": [6, 6, 12, 55, 233],
            "selected_points": [[-5, 17], [-4, -3]],
        }
        result = adapter.process_row(row, self.tool, 60.0, 384, 256)
        self.assertEqual((result["status"], result["reason"]), ("OK", "computed"), result)
        self.assertEqual(result["construction_discriminant"], "-2031616")
        self.assertEqual(result["minimal_model"]["ainvs"], ["0", "0", "0", "1", "1"])
        self.assertEqual(result["minimal_model"]["discriminant"], "-496")
        self.assertEqual(result["minimal_model"]["transformation"]["u"], "2")
        self.assertEqual(
            [item["minimal_point"] for item in result["mapped_points"]],
            [["0", "1"], ["1/4", "-9/8"]],
        )

    def test_minimal_rational_point_and_384_768_stability(self):
        row = {
            "row_id": "control-37a1-rational",
            "ainvs": [0, 0, 1, -1, 0],
            "selected_points": [[0, 0], ["1/4", "-5/8"]],
        }
        medium = adapter.process_row(row, self.tool, 60.0, 384, 256)
        high = adapter.process_row(row, self.tool, 60.0, 768, 384)
        self.assertEqual((medium["status"], medium["reason"]), ("OK", "computed"), medium)
        self.assertEqual((high["status"], high["reason"]), ("OK", "computed"), high)
        self.assertEqual(medium["stable_selection_key"], high["stable_selection_key"])
        self.assertEqual(medium["selection_evidence_sha256"], high["selection_evidence_sha256"])
        self.assertEqual(medium["conductor"], "37")
        gram = [[Decimal(value) for value in row] for row in medium["height_gram_matrix"]]
        self.assertEqual([len(row) for row in gram], [2, 2])
        self.assertEqual(gram[0][1], gram[1][0])
        determinant = Decimal(medium["selected_height_determinant"]["numerical_approximation"])
        with localcontext() as context:
            context.prec = 100
            self.assertAlmostEqual(gram[0][0] * gram[1][1] - gram[0][1]**2, determinant, places=95)
        self.assertGreater(Decimal(medium["max_canonical_height"]), 0)
        self.assertGreater(Decimal(medium["rho"]), 0)

    def test_torsion_zero_height_is_rejected(self):
        row = {
            "row_id": "control-11a1-torsion",
            "ainvs": [0, -1, 1, -10, -20],
            "selected_points": [[5, 5]],
        }
        result = adapter.process_row(row, self.tool, 60.0, 384, 256)
        self.assertEqual((result["status"], result["reason"]), ("UNKNOWN", "zero_height"), result)


if __name__ == "__main__":
    unittest.main()
