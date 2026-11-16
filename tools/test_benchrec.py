#!/usr/bin/env python3
"""Tests for tools/benchrec.py: run in a throwaway git repository."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().with_name("benchrec.py")


def sh(*args, cwd, check=True, env=None):
    p = subprocess.run(list(args), cwd=cwd, capture_output=True, text=True, env=env)
    if check and p.returncode != 0:
        raise AssertionError(f"{' '.join(map(str, args))}\n{p.stdout}\n{p.stderr}")
    return p


class BenchrecTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        sh("git", "init", "-q", "-b", "main", cwd=self.root)
        sh("git", "config", "user.email", "t@example.invalid", cwd=self.root)
        sh("git", "config", "user.name", "t", cwd=self.root)
        (self.root / "README.md").write_text("x\n")
        (self.root / ".gitignore").write_text(".benchrec/\n")
        sh("git", "add", "-A", cwd=self.root)
        sh("git", "commit", "-qm", "init", cwd=self.root)
        self.env = dict(os.environ, BENCHREC_ISOLATION="L0")

    def tearDown(self):
        self.tmp.cleanup()

    def br(self, *args, check=True):
        return sh(sys.executable, str(TOOL), *args, cwd=self.root, check=check, env=self.env)

    def commit_all(self, msg="c"):
        sh("git", "add", "-A", cwd=self.root)
        sh("git", "commit", "-qm", msg, cwd=self.root)

    def test_finite_signed_extremes_have_finite_relative_changes(self):
        first = self.make_record(slug="aa-large-first", value=1e308)
        last = self.make_record(slug="zz-large-last", value=1e308)
        for magnitude in (1e308, 10 ** 308):
            with self.subTest(number_type=type(magnitude).__name__):
                for name, value in ((first, magnitude), (last, -magnitude)):
                    path = self.root / name
                    record = json.loads(path.read_text())
                    record["metrics"][0]["value"] = value
                    path.write_text(json.dumps(record))
                self.br("report")
                progress = json.loads((self.root / "benchmarks/progress/progress.json").read_text())
                series = next(s for s in progress["series"] if s["metric"] == "ir_per_op")
                self.assertEqual(series["latest_derived"]["improvement_vs_first_percent"], 200.0)
                self.assertEqual(series["latest_derived"]["improvement_vs_previous_percent"], 200.0)
                self.assertEqual(series["points"][-1]["value"], -magnitude)

    def test_extreme_finite_comparisons_have_finite_chart_coordinates(self):
        import re
        import zlib
        names = [self.make_record(slug=slug, value=100.0)
                 for slug in ("aa-anchor", "bb-positive", "zz-negative")]
        for name, value in zip(names, (100.0, 1e308, -1e308)):
            path = self.root / name
            record = json.loads(path.read_text())
            record["metrics"][0]["value"] = value
            path.write_text(json.dumps(record))
        self.br("report")
        svg = (self.root / "benchmarks/progress/progress.svg").read_text()
        self.assertNotRegex(svg, r"\b(?:nan|inf)\b")
        pdf = (self.root / "benchmarks/progress/progress.pdf").read_bytes()
        streams = re.findall(rb"stream\n(.*?)\nendstream", pdf, re.S)
        self.assertTrue(streams)
        for stream in streams:
            self.assertNotRegex(zlib.decompress(stream), rb"\b(?:nan|inf)\b")

    def test_extreme_finite_reference_axis_has_nonzero_finite_labels(self):
        names = [self.make_record(slug=slug, value=100.0, reference=100.0)
                 for slug in ("aa-reference", "zz-reference")]
        for name, reference in zip(names, (1e308, 1.0)):
            path = self.root / name
            record = json.loads(path.read_text())
            record["metrics"][0]["value"] = 1e308
            record["metrics"][0]["reference"] = reference
            path.write_text(json.dumps(record))
        self.br("report")
        svg = (self.root / "benchmarks/progress/progress.svg").read_text()
        self.assertNotRegex(svg, r"\b(?:nan|inf)\b")
        self.assertIn("10^", svg)

    def test_truly_unrepresentable_relative_change_still_fails(self):
        first = self.make_record(slug="aa-small-first", value=1e308)
        self.make_record(slug="zz-large-last", value=1e308)
        path = self.root / first
        record = json.loads(path.read_text())
        record["metrics"][0]["value"] = 1e-308
        path.write_text(json.dumps(record))
        result = self.br("report", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("derived comparison overflow", result.stdout + result.stderr)

    def make_record(self, slug="rho-step", value=100.0, reference=None, status="measured"):
        rec = self.br("init", "--slug", slug, "--problem", "kernel:rho_step").stdout.strip()
        self.assertTrue((self.root / rec).is_file())
        self.assertEqual(self.br("open", check=False).returncode, 1)
        out = self.root / "out"
        out.mkdir(exist_ok=True)
        data = out / f"{slug}-{value}.json"
        data.write_text(json.dumps({"value": value}))
        r = self.br("run", rec, "--", sys.executable, "-c", "print('ran')")
        self.assertIn("ran", r.stdout)
        self.br("add-raw", rec, str(data))
        args = ["metric", rec, "--name", "ir_per_op", "--value", str(value), "--unit", "ir_per_op", "--n", "3"]
        if reference is not None:
            args += ["--reference", str(reference), "--reference-kind", "matched_rho"]
        self.br(*args)
        self.br("metric", rec, "--name", "cost", "--value", str(value / 10), "--unit", "S")
        pdf = self.root / "report.pdf"
        pdf.write_bytes(b"%PDF-1.4\n")
        close = ["close", rec, "--status", status, "--summary", "a run"]
        if status == "measured":
            close += ["--report", str(pdf)]
        self.br(*close)
        return rec

    def test_one_record_has_no_self_comparison(self):
        self.make_record(value=100.0)
        progress = json.loads((self.root / "benchmarks/progress/progress.json").read_text())
        for series in progress["series"]:
            self.assertEqual(len(series["points"]), 1)
            self.assertNotIn("improvement_vs_first_percent", series["points"][0]["derived"])
        graphic = (self.root / "benchmarks/progress/progress.svg").read_text()
        self.assertIn("No comparable observations within a metric yet", graphic)

    def test_single_record_retains_real_reference(self):
        self.make_record(value=100.0, reference=50.0)
        progress = json.loads((self.root / "benchmarks/progress/progress.json").read_text())
        series = next(s for s in progress["series"] if s["metric"] == "ir_per_op")
        self.assertNotIn("improvement_vs_first_percent", series["points"][0]["derived"])
        self.assertEqual(series["points"][0]["derived"]["value_over_reference"], 2.0)
        graphic = (self.root / "benchmarks/progress/progress.svg").read_text()
        self.assertIn("Distance remaining: value / reference", graphic)

    def test_full_lifecycle_and_progress(self):
        rec1 = self.make_record(value=100.0, reference=50.0)
        rec2 = self.make_record(slug="rho-step-2", value=80.0, reference=50.0)
        prog = json.loads((self.root / "benchmarks/progress/progress.json").read_text())
        self.assertEqual(prog["schema"], "bench.progress/v1")
        s = next(x for x in prog["series"] if x["metric"] == "ir_per_op")
        self.assertEqual(len(s["points"]), 2)
        self.assertAlmostEqual(s["points"][1]["derived"]["improvement_vs_first_percent"], 20.0)
        self.assertAlmostEqual(s["points"][1]["derived"]["value_over_reference"], 1.6)
        for f in ("PROGRESS.md", "progress.svg", "progress.pdf"):
            self.assertTrue((self.root / "benchmarks/progress" / f).stat().st_size > 100)
        self.assertTrue((self.root / "benchmarks/progress/progress.pdf").read_bytes().startswith(b"%PDF"))
        self.assertEqual(self.br("open", check=False).returncode, 0)
        self.assertEqual(self.br("gate").returncode, 0)
        self.assertEqual(self.br("report", "--check").returncode, 0)
        # Records are immutable once closed.
        r = self.br("metric", rec1, "--name", "x", "--value", "1", "--unit", "S", check=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn(rec2, (self.root / rec2).as_posix())

    def test_metric_rejects_invalid_numeric_metadata_without_writing(self):
        rec = self.br("init", "--slug", "numeric", "--problem", "p:q").stdout.strip()
        path = self.root / rec
        before = path.read_bytes()
        for args in (["--value", "nan"], ["--value", "inf"],
                     ["--reference", "nan"], ["--baseline", "inf"],
                     ["--n", "0"], ["--n", "-1"],
                     ["--spread-low", "1"], ["--spread-high", "2"],
                     ["--spread-low", "3", "--spread-high", "2"],
                     ["--spread-low", "nan", "--spread-high", "2"]):
            with self.subTest(args=args):
                r = self.br("metric", rec, "--name", "m", "--unit", "S",
                            "--value", "1", *args, check=False)
                self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
                self.assertEqual(path.read_bytes(), before)

    def test_report_rejects_tampered_measurement_and_preserves_outputs(self):
        rec = self.make_record()
        path = self.root / rec
        original = json.loads(path.read_text())
        progress = self.root / "benchmarks/progress/progress.json"
        before = progress.read_bytes()
        for field, value in (("value", float("nan")), ("reference", True),
                             ("reference", "50"), ("baseline", float("inf")),
                             ("n", True), ("spread", [3, 2])):
            with self.subTest(field=field, value=value):
                body = json.loads(json.dumps(original))
                body["metrics"][0][field] = value
                path.write_text(json.dumps(body))
                r = self.br("report", check=False)
                self.assertNotEqual(r.returncode, 0)
                self.assertNotIn("Traceback", r.stderr)
                self.assertEqual(progress.read_bytes(), before)

    def test_failed_command_cannot_close_as_measured(self):
        rec = self.make_record()
        path = self.root / rec
        body = json.loads(path.read_text())
        body["status"] = "open"
        body["commands"][0]["exit"] = 1
        path.write_text(json.dumps(body))
        r = self.br("close", rec, "--status", "measured", check=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(json.loads(path.read_text())["status"], "open")
        self.br("close", rec, "--status", "invalid", "--summary", "failed command")
        prog = json.loads((self.root / "benchmarks/progress/progress.json").read_text())
        self.assertEqual(prog["series"], [])

    def test_direction_drift_rejected_before_progress_write(self):
        self.make_record()
        rec = self.make_record(slug="second", value=80)
        path = self.root / rec
        body = json.loads(path.read_text())
        body["metrics"][0]["better"] = "neutral"
        path.write_text(json.dumps(body))
        progress = self.root / "benchmarks/progress/progress.json"
        before = progress.read_bytes()
        r = self.br("report", check=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("direction", r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        self.assertEqual(progress.read_bytes(), before)

    def test_pinned_exclusion_is_visible_and_does_not_waive_raw_integrity(self):
        import hashlib
        rec = self.make_record()
        path = self.root / rec
        body = json.loads(path.read_text())
        body["commands"][0]["exit"] = None
        path.write_text(json.dumps(body))
        exclusions = {"schema": "bench.integrity-exclusions/v1", "records": {
            rec: {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                  "reason": "Documentary command; execution exit not captured."}}}
        exclusion_path = self.root / "benchmarks/integrity-exclusions.json"
        exclusion_path.write_text(json.dumps(exclusions))
        self.br("report")
        prog = json.loads((self.root / "benchmarks/progress/progress.json").read_text())
        self.assertEqual(prog["series"], [])
        self.assertEqual(prog["records"]["measured"], 1)
        self.assertEqual(prog["integrity_exclusions"][0]["record"], rec)
        self.assertIn(rec, (self.root / "benchmarks/progress/PROGRESS.md").read_text())
        self.br("check")
        raw = self.root / body["raw"][0]["path"]
        raw.write_text("corrupt")
        self.assertNotEqual(self.br("check", check=False).returncode, 0)
        body["summary"] = "changed after exclusion"
        path.write_text(json.dumps(body))
        r = self.br("report", check=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("exclusion", r.stderr)

    def test_raw_byte_count_must_match_even_when_hash_matches(self):
        rec = self.make_record()
        path = self.root / rec
        original = json.loads(path.read_text())
        for size in (True, -1, original["raw"][0]["bytes"] + 1):
            with self.subTest(size=size):
                body = json.loads(json.dumps(original))
                body["raw"][0]["bytes"] = size
                path.write_text(json.dumps(body))
                r = self.br("check", check=False)
                self.assertNotEqual(r.returncode, 0)
                self.assertIn("bytes", r.stdout + r.stderr)

    def test_exclusions_fail_closed_on_bad_pin_reason_or_record_status(self):
        import hashlib
        rec = self.make_record()
        path = self.root / rec
        original = path.read_bytes()
        manifest = self.root / "benchmarks/integrity-exclusions.json"
        for status, digest, reason in (("measured", "0" * 64, "bad pin"),
                                       ("measured", None, ""),
                                       ("open", None, "cannot hide open run"),
                                       ("censored", None, "cannot relabel status")):
            with self.subTest(status=status, digest=digest, reason=reason):
                body = json.loads(original)
                body["status"] = status
                path.write_text(json.dumps(body))
                manifest.write_text(json.dumps({"schema": "bench.integrity-exclusions/v1", "records": {
                    rec: {"sha256": digest or hashlib.sha256(path.read_bytes()).hexdigest(), "reason": reason}}}))
                result = self.br("report", check=False)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("exclusion", result.stderr)

    def test_missing_or_boolean_command_exit_rejected(self):
        rec = self.make_record()
        path = self.root / rec
        original = json.loads(path.read_text())
        for exit_code in (None, False, "0", 1):
            with self.subTest(exit_code=exit_code):
                body = json.loads(json.dumps(original))
                body["commands"][0]["exit"] = exit_code
                path.write_text(json.dumps(body))
                self.assertNotEqual(self.br("report", check=False).returncode, 0)

    def test_derived_overflow_cannot_publish_nonfinite_json(self):
        rec = self.make_record(value=1e308, reference=1e308)
        path = self.root / rec
        body = json.loads(path.read_text())
        body["metrics"][0]["reference"] = 1e-308
        path.write_text(json.dumps(body))
        progress = self.root / "benchmarks/progress/progress.json"
        before = progress.read_bytes()
        r = self.br("report", check=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("overflow", r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        self.assertEqual(progress.read_bytes(), before)

    def test_previous_gain_survives_zero_first_observation(self):
        self.make_record(slug="zero", value=0)
        self.make_record(slug="positive", value=100)
        rec = self.make_record(slug="later", value=80)
        # Avoid timestamp ties: record order is intentionally pinned here.
        for i, path in enumerate(sorted((self.root / "benchmarks/records").glob("*.json"),
                                        key=lambda p: {"zero": 0, "positive": 1, "later": 2}[json.loads(p.read_text())["slug"]])):
            body = json.loads(path.read_text())
            body["closed_utc"] = f"2026-11-07T00:00:0{i}+00:00"
            path.write_text(json.dumps(body))
        self.br("report")
        prog = json.loads((self.root / "benchmarks/progress/progress.json").read_text())
        point = next(s for s in prog["series"] if s["metric"] == "ir_per_op")["points"][-1]
        self.assertEqual(point["record"], Path(rec).stem)
        self.assertEqual(point["derived"]["improvement_vs_previous_percent"], 20)
        self.assertNotIn("improvement_vs_first_percent", point["derived"])

    def test_incompatible_close_leaves_record_open(self):
        self.make_record()
        rec = self.make_record(slug="second", value=80)
        path = self.root / rec
        body = json.loads(path.read_text())
        body["status"] = "open"
        body["metrics"][0]["better"] = "neutral"
        path.write_text(json.dumps(body))
        before = path.read_bytes()
        r = self.br("close", rec, "--status", "measured", check=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(path.read_bytes(), before)

    def test_store_backed_report_accepted_via_manifest(self):
        """A report kept in the artifact store (listed in a .artifacts.json, absent from the
        checkout) passes check; one that is neither on disk nor in a manifest fails."""
        import hashlib
        rec = self.make_record(value=100.0, reference=50.0)
        self.commit_all()
        body = json.loads((self.root / rec).read_text())
        pdf_rel = body["reports"]["pdf"]
        pdf = self.root / pdf_rel
        digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
        size = pdf.stat().st_size
        pdf.unlink()
        r = self.br("check", check=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("is not in the checkout or a .artifacts.json manifest", r.stdout + r.stderr)
        (pdf.parent / ".artifacts.json").write_text(json.dumps(
            {"schema": "artifacts.manifest/v1", "files": {pdf.name: {"sha256": digest, "bytes": size}}}))
        r = self.br("check", check=False)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_unknown_unit_and_bad_close_rejected(self):
        rec = self.br("init", "--slug", "unit-test", "--problem", "p:q").stdout.strip()
        r = self.br("metric", rec, "--name", "m", "--value", "1", "--unit", "furlongs", check=False)
        self.assertEqual(r.returncode, 1)
        self.assertIn("unknown unit", r.stderr)
        r = self.br("close", rec, "--status", "measured", check=False)
        self.assertEqual(r.returncode, 1)
        self.assertIn("no command recorded", r.stderr)
        self.assertEqual(json.loads((self.root / rec).read_text())["status"], "open")

    def test_gate_fails_on_open_record(self):
        self.br("init", "--slug", "left-open", "--problem", "p:q")
        r = self.br("gate", check=False)
        self.assertEqual(r.returncode, 1)
        self.assertIn("not closed", r.stdout)

    def test_check_base_requires_record_for_new_entry(self):
        self.make_record()
        self.commit_all("record")
        sh("git", "checkout", "-qb", "feature", cwd=self.root)
        d = self.root / "benchmarks/20261104-new-thing"
        d.mkdir(parents=True)
        (d / "README.md").write_text("entry\n")
        self.commit_all("entry without record")
        r = self.br("check", "--base", "main", check=False)
        self.assertEqual(r.returncode, 1)
        self.assertIn("benchmarks/20261104-new-thing: benchmark entry added without", r.stdout)
        rec = self.br("init", "--slug", "new-thing", "--problem", "p:q", "--entry", "benchmarks/20261104-new-thing").stdout.strip()
        self.br("run", rec, "--", "true")
        self.br("add-raw", rec, str(d / "README.md"))
        self.br("metric", rec, "--name", "m", "--value", "2", "--unit", "wall_s")
        pdf = self.root / "r.pdf"
        pdf.write_bytes(b"%PDF-1.4\n")
        self.br("close", rec, "--status", "measured", "--report", str(pdf), "--summary", "ok")
        self.commit_all("record")
        self.assertEqual(self.br("check", "--base", "main").returncode, 0)

    def test_closed_record_edit_rejected_against_base(self):
        rec = self.make_record()
        self.commit_all("record")
        sh("git", "checkout", "-qb", "feature", cwd=self.root)
        p = self.root / rec
        d = json.loads(p.read_text())
        d["summary"] = "rewritten"
        p.write_text(json.dumps(d, indent=2, sort_keys=True) + "\n")
        self.br("report")
        self.commit_all("tamper")
        r = self.br("check", "--base", "main", check=False)
        self.assertEqual(r.returncode, 1)
        self.assertIn("closed record is immutable", r.stdout)

    def test_invalid_base_does_not_become_an_empty_change_set(self):
        self.make_record()
        self.commit_all("record")
        for base in ("missing-base-branch", ""):
            with self.subTest(base=base):
                result = self.br("check", "--base", base, check=False)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("base", result.stderr)

    def test_unrelated_base_history_is_a_failure(self):
        self.make_record()
        self.commit_all("record")
        sh("git", "checkout", "--orphan", "unrelated", cwd=self.root)
        sh("git", "rm", "-rf", ".", cwd=self.root)
        (self.root / "anchor").write_text("independent history\n")
        self.commit_all("unrelated root")
        sh("git", "checkout", "main", cwd=self.root)
        result = self.br("check", "--base", "unrelated", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("merge-base", result.stderr)

    def test_closed_record_deletion_rename_and_type_change_are_rejected(self):
        rec = self.make_record()
        self.commit_all("closed record")
        base = sh("git", "rev-parse", "HEAD", cwd=self.root).stdout.strip()
        sh("git", "checkout", "-qb", "feature", cwd=self.root)
        path = self.root / rec
        for action in ("delete", "rename", "symlink"):
            with self.subTest(action=action):
                sh("git", "reset", "--hard", base, cwd=self.root)
                if action == "rename":
                    renamed = path.with_name(path.stem + "-renamed.json")
                    doc = json.loads(path.read_text())
                    doc["id"] = renamed.stem
                    renamed.write_text(json.dumps(doc))
                elif action == "symlink":
                    saved = self.root / "saved" / path.name
                    saved.parent.mkdir(exist_ok=True)
                    saved.write_bytes(path.read_bytes())
                path.unlink()
                if action == "symlink":
                    path.symlink_to(saved)
                self.br("report")
                self.commit_all("changed closed record representation")
                result = self.br("check", "--base", "main", check=False)
                self.assertEqual(result.returncode, 1)
                self.assertIn("closed record is immutable", result.stdout)

    def test_closed_record_base_uses_required_git_filter(self):
        import shlex
        filter_script = self.root / 'record_filter.py'
        filter_script.write_text(
            'import os,sys\n'
            'data=sys.stdin.buffer.read()\n'
            'if sys.argv[1]=="smudge" and os.environ.get("BENCHREC_FILTER_REJECT"): sys.exit(1)\n'
            'sys.stdout.buffer.write(b"VLT1"+data if sys.argv[1]=="clean" else data[4:] if data.startswith(b"VLT1") else data)\n')
        command = f'{shlex.quote(sys.executable)} {shlex.quote(str(filter_script))}'
        sh('git', 'config', 'filter.control.clean', command+' clean', cwd=self.root)
        sh('git', 'config', 'filter.control.smudge', command+' smudge', cwd=self.root)
        sh('git', 'config', 'filter.control.required', 'true', cwd=self.root)
        (self.root / '.gitattributes').write_text('*.json filter=control\n')
        rec = self.make_record()
        self.commit_all('filtered closed record')
        sh('git', 'checkout', '-qb', 'feature', cwd=self.root)
        path = self.root / rec
        value = json.loads(path.read_text())
        value['summary'] = 'changed in feature'
        path.write_text(json.dumps(value))
        self.br('report')
        self.commit_all('changed record')
        result = self.br('check', '--base', 'main', check=False)
        self.assertEqual(result.returncode, 1)
        self.assertIn('closed record is immutable', result.stdout)
        self.env['BENCHREC_FILTER_REJECT'] = '1'
        result = self.br('check', '--base', 'main', check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('cannot read committed base record', result.stderr)

    def test_stale_progress_detected(self):
        self.make_record()
        (self.root / "benchmarks/progress/PROGRESS.md").write_text("edited by hand\n")
        r = self.br("check", check=False)
        self.assertEqual(r.returncode, 1)
        self.assertIn("progress report is stale", r.stdout)

    def test_raw_missing_locally_and_not_uploaded_fails(self):
        rec = self.make_record()
        os.remove(self.root / "out" / "rho-step-100.0.json")
        r = self.br("check", check=False)
        self.assertEqual(r.returncode, 1)
        self.assertIn("neither in Git", r.stdout)

    def test_edited_raw_fails(self):
        self.make_record()
        (self.root / "out" / "rho-step-100.0.json").write_text("edited\n")
        r = self.br("check", check=False)
        self.assertEqual(r.returncode, 1)
        self.assertIn("differs from its recorded sha256", r.stdout)

    def test_living_path_is_not_checked_against_the_checkout(self):
        (self.root / ".benchrec.json").write_text(json.dumps({"living_paths": ["out/rho-step-100.0.json"]}))
        rec = self.make_record()
        old_record = (self.root / rec).read_bytes()
        raw = json.loads(old_record)["raw"][0]
        data = self.root / raw["path"]
        original = data.read_bytes()
        data.write_text("the catalog moved on\n")
        newer = data.read_bytes()
        missing = self.br("check", check=False)
        self.assertEqual(missing.returncode, 1, missing.stdout + missing.stderr)
        self.assertIn("differs from its recorded sha256", missing.stdout)
        cache = self.root / ".benchrec/raw-archive-cache" / raw["sha256"]
        cache.parent.mkdir(parents=True)
        cache.write_bytes(original)
        r = self.br("check", check=False)
        self.assertNotIn("differs from its recorded sha256", r.stdout)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("original raw bytes verified", r.stdout)
        self.assertIn("differing checkout bytes are not validated", r.stdout)
        self.assertEqual((self.root / rec).read_bytes(), old_record)
        self.assertEqual(data.read_bytes(), newer)

    def test_living_path_requires_fresh_online_archive_even_with_exact_cache(self):
        (self.root / ".benchrec.json").write_text(json.dumps({"living_paths": ["out/rho-step-100.0.json"]}))
        rec, old_record, raw, data, archive = self.archived_fixture()
        newer = data.read_bytes()
        cache = self.root / ".benchrec/raw-archive-cache" / raw["sha256"]
        cache.parent.mkdir(parents=True)
        cache.write_bytes(archive.read_bytes())
        for mode in ("get-denied", "corrupt", "truncated", "oversized", "wrong-size", "no-head"):
            with self.subTest(mode=mode):
                self.env["FAKE_ARCHIVE_MODE"] = mode
                r = self.br("check", "--verify-s3", check=False)
                self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
                self.assertIn("differs from its recorded sha256", r.stdout)
                self.assertEqual((self.root / rec).read_bytes(), old_record)
                self.assertEqual(data.read_bytes(), newer)
        self.env["FAKE_ARCHIVE_MODE"] = "good"
        r = self.br("check", "--verify-s3", check=False)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(any(a[:2] == ["s3api", "get-object"] for a in self.archive_calls()))
        self.assertFalse(any(a[:2] == ["s3", "cp"] for a in self.archive_calls()))

    def test_living_path_cannot_substitute_archive_for_open_record(self):
        (self.root / ".benchrec.json").write_text(json.dumps({"living_paths": ["out/rho-step-100.0.json"]}))
        self.test_open_record_cannot_substitute_an_old_archive()

    def test_living_path_cannot_download_noncanonical_archive(self):
        (self.root / ".benchrec.json").write_text(json.dumps({"living_paths": ["out/rho-step-100.0.json"]}))
        self.test_noncanonical_archive_uri_is_never_downloaded_for_fallback()

    def test_config_override(self):
        (self.root / ".benchrec.json").write_text(json.dumps({
            "records_dir": "docs/benchmarks/records", "progress_dir": "docs/benchmarks/progress",
            "entry_dirs": ["docs/benchmarks"], "entry_re": "^[a-z0-9-]+-\\d{8}$"}))
        rec = self.br("init", "--slug", "cfg", "--problem", "p:q").stdout.strip()
        self.assertTrue(rec.startswith("docs/benchmarks/records/"))

    def archived_fixture(self):
        """A real closed record plus a fake S3 CLI; no cloud access occurs."""
        rec = self.make_record()
        original_record = (self.root / rec).read_bytes()
        body = json.loads(original_record)
        raw = body["raw"][0]
        data = self.root / raw["path"]
        archive = self.root / "original-archive.bin"
        archive.write_bytes(data.read_bytes())
        data.write_bytes(b"newer generated checkout version\n")
        fake = self.root / "fake-bin"
        fake.mkdir()
        aws = fake / "aws"
        aws.write_text('''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
a = sys.argv[1:]
with Path(os.environ["FAKE_AWS_LOG"]).open("a") as f:
    f.write(json.dumps(a) + "\\n")
mode = os.environ.get("FAKE_ARCHIVE_MODE", "good")
data = Path(os.environ["FAKE_ARCHIVE"]).read_bytes()
if a[:2] == ["sts", "get-caller-identity"]:
    raise SystemExit(0)
if a[:2] == ["s3api", "head-object"]:
    if mode == "no-head": raise SystemExit(1)
    size = len(data) + (1 if mode == "wrong-size" else 0)
    print(size if "--query" in a else json.dumps({"ContentLength": size}))
    raise SystemExit(0)
if a[:2] == ["s3api", "get-object"]:
    if mode == "get-denied": raise SystemExit(1)
    if mode == "corrupt": data = bytes([data[0] ^ 1]) + data[1:]
    if mode == "truncated": data = data[:-1]
    if mode == "oversized": data += b"x"
    Path(a[-1]).write_bytes(data)
    print("{}")
    raise SystemExit(0)
# Any attempted PUT is a test failure.
raise SystemExit(99)
''')
        aws.chmod(0o755)
        self.env.update(PATH=str(fake) + os.pathsep + self.env["PATH"],
                        FAKE_ARCHIVE=str(archive),
                        FAKE_AWS_LOG=str(self.root / "aws-calls.jsonl"))
        return rec, original_record, raw, data, archive

    def archive_calls(self):
        p = self.root / "aws-calls.jsonl"
        return [json.loads(x) for x in p.read_text().splitlines()] if p.exists() else []

    def canonical_module(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("benchrec_archive_test", TOOL)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_closed_raw_verifies_exact_archive_without_changing_checkout(self):
        rec, old_record, raw, data, archive = self.archived_fixture()
        newer = data.read_bytes()
        p = self.br("check", "--verify-s3", check=False)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("original raw bytes verified", p.stdout)
        self.assertEqual(data.read_bytes(), newer)
        self.assertEqual((self.root / rec).read_bytes(), old_record)
        gets = [a for a in self.archive_calls() if a[:2] == ["s3api", "get-object"]]
        self.assertEqual(len(gets), 1)
        self.assertEqual(gets[0][gets[0].index("--range") + 1], f"bytes=0-{raw['bytes']}")
        self.assertFalse(Path(gets[0][-1]).exists())  # temporary download cleaned
        self.assertFalse(any(a[:2] == ["s3", "cp"] for a in self.archive_calls()))

    def test_changed_closed_raw_still_fails_offline_without_original_bytes(self):
        self.archived_fixture()
        p = self.br("gate", check=False)
        self.assertEqual(p.returncode, 1)
        self.assertIn("differs from its recorded sha256", p.stdout)
        self.assertEqual(self.archive_calls(), [])

    def test_offline_archive_cache_checks_both_digest_and_size(self):
        rec, old_record, raw, data, archive = self.archived_fixture()
        cache = self.root / ".benchrec/raw-archive-cache" / raw["sha256"]
        cache.parent.mkdir(parents=True)
        old = archive.read_bytes()
        cache.write_bytes(old)
        self.assertEqual(self.br("gate").returncode, 0)
        for bad in (bytes([old[0] ^ 1]) + old[1:], old + b"x", old[:-1]):
            with self.subTest(bytes=len(bad)):
                cache.write_bytes(bad)
                self.assertEqual(self.br("gate", check=False).returncode, 1)
        self.assertEqual((self.root / rec).read_bytes(), old_record)
        self.assertEqual(self.archive_calls(), [])

    def test_bad_archives_fail_closed_and_never_upload_newer_data(self):
        rec, old_record, raw, data, archive = self.archived_fixture()
        newer = data.read_bytes()
        for mode in ("get-denied", "corrupt", "truncated", "oversized", "wrong-size", "no-head"):
            with self.subTest(mode=mode):
                self.env["FAKE_ARCHIVE_MODE"] = mode
                p = self.br("check", "--verify-s3", check=False)
                self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
                self.assertIn("differs from its recorded sha256", p.stdout)
                p = self.br("upload", rec, check=False)
                self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
                self.assertEqual(data.read_bytes(), newer)
                self.assertEqual((self.root / rec).read_bytes(), old_record)
        self.assertFalse(any(a[:2] == ["s3", "cp"] for a in self.archive_calls()))

    def test_upload_accepts_only_existing_verified_archive_without_record_edit(self):
        rec, old_record, raw, data, archive = self.archived_fixture()
        newer = data.read_bytes()
        p = self.br("upload", rec, check=False)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("no upload performed", p.stdout)
        self.assertEqual((self.root / rec).read_bytes(), old_record)
        self.assertEqual(data.read_bytes(), newer)
        self.assertFalse(any(a[:2] == ["s3", "cp"] for a in self.archive_calls()))

    def test_upload_requires_store_availability_even_with_exact_local_cache(self):
        rec, old_record, raw, data, archive = self.archived_fixture()
        cache = self.root / ".benchrec/raw-archive-cache" / raw["sha256"]
        cache.parent.mkdir(parents=True)
        cache.write_bytes(archive.read_bytes())
        self.env["FAKE_ARCHIVE_MODE"] = "no-head"
        self.assertEqual(self.br("upload", rec, check=False).returncode, 1)
        self.assertEqual((self.root / rec).read_bytes(), old_record)

    def test_online_verification_replays_archive_even_with_exact_cache(self):
        rec, old_record, raw, data, archive = self.archived_fixture()
        cache = self.root / ".benchrec/raw-archive-cache" / raw["sha256"]
        cache.parent.mkdir(parents=True)
        cache.write_bytes(archive.read_bytes())
        self.env["FAKE_ARCHIVE_MODE"] = "get-denied"
        p = self.br("check", "--verify-s3", check=False)
        self.assertEqual(p.returncode, 1)
        self.assertIn("differs from its recorded sha256", p.stdout)
        self.assertTrue(any(a[:2] == ["s3api", "get-object"] for a in self.archive_calls()))
        self.assertEqual((self.root / rec).read_bytes(), old_record)

    def test_empty_archived_object_requires_exact_empty_digest_and_get(self):
        import hashlib
        from unittest.mock import patch
        rec, old_record, raw, data, archive = self.archived_fixture()
        archive.write_bytes(b"")
        module = self.canonical_module()
        cfg = module.load_config(self.root)
        digest = hashlib.sha256(b"").hexdigest()
        empty = dict(raw, sha256=digest, bytes=0, s3_uri=module.store_uri(cfg, digest))
        with patch.dict(os.environ, self.env):
            self.assertTrue(module.archived_raw_matches(self.root, cfg, empty, remote=True))
        gets = [a for a in self.archive_calls() if a[:2] == ["s3api", "get-object"]]
        self.assertEqual(len(gets), 1)
        self.assertFalse(Path(gets[0][-1]).exists())

    def test_closing_open_record_cannot_use_archive_fallback(self):
        (self.root / ".benchrec.json").write_text(json.dumps({"living_paths": ["raw.txt"]}))
        rec = self.br("init", "--slug", "open-close", "--problem", "fixture:archive-close").stdout.strip()
        self.br("run", rec, "--", "true")
        data = self.root / "raw.txt"
        original = b"original raw fixture\n"
        data.write_bytes(original)
        self.br("add-raw", rec, str(data))
        self.br("metric", rec, "--name", "control", "--value", "1", "--unit", "count")
        report = self.root / "report.pdf"
        report.write_bytes(b"%PDF-1.4\n")
        before = (self.root / rec).read_bytes()
        raw = json.loads(before)["raw"][0]
        cache = self.root / ".benchrec/raw-archive-cache" / raw["sha256"]
        cache.parent.mkdir(parents=True)
        cache.write_bytes(original)
        data.write_bytes(b"different current fixture\n")
        changed = data.read_bytes()
        for status in ("measured", "invalid", "censored"):
            with self.subTest(status=status):
                r = self.br("close", rec, "--status", status, "--summary", "synthetic control",
                            "--report", str(report), check=False)
                self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
                self.assertIn("differs from its recorded sha256", r.stderr)
                self.assertEqual((self.root / rec).read_bytes(), before)
                self.assertEqual(json.loads((self.root / rec).read_text())["status"], "open")
                self.assertEqual(data.read_bytes(), changed)
        # An open record can close normally after its actual recorded bytes
        # are restored; the cache does not replace this requirement.
        data.write_bytes(original)
        self.br("close", rec, "--status", "measured", "--summary", "synthetic control",
                "--report", str(report))
        self.assertEqual(json.loads((self.root / rec).read_text())["status"], "measured")

    def test_open_record_cannot_substitute_an_old_archive(self):
        rec, old_record, raw, data, archive = self.archived_fixture()
        body = json.loads(old_record)
        body["status"] = "open"
        body["closed_utc"] = None
        (self.root / rec).write_text(json.dumps(body, indent=2, sort_keys=True) + "\n")
        self.assertEqual(self.br("upload", rec, check=False).returncode, 1)
        self.assertEqual(self.br("check", "--verify-s3", check=False).returncode, 1)
        self.assertFalse(any(a[:2] == ["s3api", "get-object"] for a in self.archive_calls()))

    def test_noncanonical_archive_uri_is_never_downloaded_for_fallback(self):
        rec, old_record, raw, data, archive = self.archived_fixture()
        body = json.loads(old_record)
        body["raw"][0]["s3_uri"] = "s3://another-bucket/not-content-addressed"
        (self.root / rec).write_text(json.dumps(body, indent=2, sort_keys=True) + "\n")
        p = self.br("check", "--verify-s3", check=False)
        self.assertEqual(p.returncode, 1)
        self.assertIn("differs from its recorded sha256", p.stdout)
        self.assertFalse(any(a[:2] == ["s3api", "get-object"] for a in self.archive_calls()))

    def test_archive_verification_does_not_bypass_closed_record_immutability(self):
        rec, old_record, raw, data, archive = self.archived_fixture()
        self.commit_all("original closed record")
        sh("git", "checkout", "-qb", "feature", cwd=self.root)
        body = json.loads(old_record)
        body["summary"] = "tampered after closing"
        (self.root / rec).write_text(json.dumps(body, indent=2, sort_keys=True) + "\n")
        self.br("report")
        self.commit_all("tamper")
        p = self.br("check", "--base", "main", "--verify-s3", check=False)
        self.assertEqual(p.returncode, 1)
        self.assertIn("original raw bytes verified", p.stdout)
        self.assertIn("closed record is immutable", p.stdout)

    def test_archive_cache_symlink_is_rejected(self):
        rec, old_record, raw, data, archive = self.archived_fixture()
        cache = self.root / ".benchrec/raw-archive-cache" / raw["sha256"]
        cache.parent.mkdir(parents=True)
        cache.symlink_to(archive)
        self.assertEqual(self.br("gate", check=False).returncode, 1)
        self.assertEqual(self.archive_calls(), [])

    def test_archive_cache_parent_escape_is_rejected_without_reading_it(self):
        rec, old_record, raw, data, archive = self.archived_fixture()
        with tempfile.TemporaryDirectory() as outside:
            target = Path(outside) / raw["sha256"]
            target.write_bytes(archive.read_bytes())
            parent = self.root / ".benchrec/raw-archive-cache"
            parent.parent.mkdir(parents=True, exist_ok=True)
            parent.symlink_to(outside, target_is_directory=True)
            self.assertEqual(self.br("gate", check=False).returncode, 1)
            self.assertEqual(self.archive_calls(), [])

    def test_archive_timeout_and_malformed_size_fail_closed(self):
        from unittest.mock import patch
        rec, old_record, raw, data, archive = self.archived_fixture()
        module = self.canonical_module()
        cfg = module.load_config(self.root)
        # A timeout is not "absent": it raises S3Error so the check fails
        # closed with the command and the limit named, never silently.
        with patch.object(module.subprocess, "run", side_effect=subprocess.TimeoutExpired("aws", 180)):
            with self.assertRaisesRegex(module.S3Error, "head-object .* did not finish within"):
                module.archived_raw_matches(self.root, cfg, raw, remote=True)
        for size in (-1, True, 3.5, "12"):
            with self.subTest(size=size):
                malformed = dict(raw, bytes=size)
                self.assertFalse(module.archived_raw_matches(self.root, cfg, malformed, remote=True))


FAKE_STORE_AWS = r'''#!/usr/bin/env python3
import json, os, sys, time
from pathlib import Path
a = sys.argv[1:]
with Path(os.environ["FAKE_AWS_LOG"]).open("a") as f:
    f.write(json.dumps(a) + "\n")
store = json.loads(Path(os.environ["FAKE_STORE"]).read_text())
def opt(name):
    return a[a.index(name) + 1] if name in a else None
if a[:2] == ["sts", "get-caller-identity"]:
    raise SystemExit(0)
if a[:2] == ["s3api", "list-objects-v2"]:
    mode = os.environ.get("FAKE_LIST_MODE", "ok")
    if mode == "hang":
        time.sleep(60)
    if mode == "denied":
        print("An error occurred (AccessDenied) when calling the ListObjectsV2 operation", file=sys.stderr)
        raise SystemExit(254)
    rows = [[k, n] for k, n in sorted(store.items()) if k.startswith(opt("--prefix"))]
    print(json.dumps(rows or None))
    raise SystemExit(0)
if a[:2] == ["s3api", "head-object"]:
    if os.environ.get("FAKE_HEAD_MODE") == "hang":
        time.sleep(60)
    key = opt("--key")
    if key not in store:
        raise SystemExit(254)
    print(store[key])
    raise SystemExit(0)
raise SystemExit(99)
'''


class VerifyS3InventoryTest(unittest.TestCase):
    """--verify-s3 over many raw objects: one listing, bounded calls, same coverage."""

    # The same throwaway repository and helpers, without re-running those tests.
    setUp = BenchrecTest.setUp
    tearDown = BenchrecTest.tearDown
    br = BenchrecTest.br
    commit_all = BenchrecTest.commit_all
    make_record = BenchrecTest.make_record
    canonical_module = BenchrecTest.canonical_module

    N_RAW = 20

    def many_raw_fixture(self):
        rec = self.br("init", "--slug", "many", "--problem", "kernel:many").stdout.strip()
        self.br("run", rec, "--", sys.executable, "-c", "print('ran')")
        out = self.root / "out"
        out.mkdir(exist_ok=True)
        for i in range(self.N_RAW):
            f = out / f"part-{i:02d}.json"
            f.write_text(json.dumps({"i": i}))
            self.br("add-raw", rec, str(f))
        self.br("metric", rec, "--name", "cost", "--value", "1.5", "--unit", "S")
        pdf = self.root / "report.pdf"
        pdf.write_bytes(b"%PDF-1.4\n")
        self.br("close", rec, "--status", "measured", "--summary", "many raws", "--report", str(pdf))
        body = json.loads((self.root / rec).read_text())
        store = {r["s3_uri"].split("/", 3)[3]: r["bytes"] for r in body["raw"]}
        # Unrelated objects under the same store prefix are listed and ignored.
        store["store/sha256/ff/" + "f" * 64] = 7
        fake = self.root / "fake-bin"
        fake.mkdir()
        (fake / "aws").write_text(FAKE_STORE_AWS)
        (fake / "aws").chmod(0o755)
        self.store_file = self.root / "fake-store.json"
        self.store_file.write_text(json.dumps(store))
        self.env.update(PATH=str(fake) + os.pathsep + self.env["PATH"],
                        FAKE_STORE=str(self.store_file),
                        FAKE_AWS_LOG=str(self.root / "aws-calls.jsonl"),
                        # The CI job exports the wrong region for this bucket.
                        AWS_REGION="us-west-2", AWS_DEFAULT_REGION="us-west-2")
        self.env.pop("BENCHREC_S3_REGION", None)
        self.commit_all()
        return rec, body, store

    def calls(self, op=None):
        p = self.root / "aws-calls.jsonl"
        rows = [json.loads(x) for x in p.read_text().splitlines()] if p.exists() else []
        return [r for r in rows if op is None or r[:2] == ["s3api", op]]

    def test_one_listing_replaces_per_object_heads(self):
        self.many_raw_fixture()
        p = self.br("check", "--verify-s3", check=False)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(len(self.calls("list-objects-v2")), 1)
        self.assertEqual(self.calls("head-object"), [])
        self.assertIn("1 prefix listing(s)", p.stdout)
        self.assertEqual(self.calls("list-objects-v2")[0][self.calls("list-objects-v2")[0].index("--prefix") + 1],
                         "store/sha256/")

    def test_every_call_is_bounded_and_names_the_bucket_region(self):
        self.many_raw_fixture()
        self.store_file.write_text("{}")
        self.env["FAKE_LIST_MODE"] = "denied"
        self.br("check", "--verify-s3", check=False)
        calls = self.calls()
        self.assertTrue(calls)
        for c in calls:
            with self.subTest(call=c[:2]):
                self.assertEqual(c[c.index("--region") + 1], "us-east-2")
                self.assertIn("--cli-connect-timeout", c)
                self.assertIn("--cli-read-timeout", c)

    def test_missing_object_fails_with_listing(self):
        rec, body, store = self.many_raw_fixture()
        gone = body["raw"][3]
        del store[gone["s3_uri"].split("/", 3)[3]]
        self.store_file.write_text(json.dumps(store))
        p = self.br("check", "--verify-s3", check=False)
        self.assertEqual(p.returncode, 1)
        self.assertIn(f"raw {gone['path']} is not at {gone['s3_uri']}", p.stdout)
        self.assertEqual(p.stdout.count(" is not at "), 1)

    def test_wrong_size_object_fails(self):
        rec, body, store = self.many_raw_fixture()
        k = body["raw"][5]["s3_uri"].split("/", 3)[3]
        store[k] += 1
        self.store_file.write_text(json.dumps(store))
        p = self.br("check", "--verify-s3", check=False)
        self.assertEqual(p.returncode, 1)
        self.assertIn("the record says", p.stdout)

    def test_listing_denied_falls_back_to_heads_with_same_coverage(self):
        rec, body, store = self.many_raw_fixture()
        self.env["FAKE_LIST_MODE"] = "denied"
        p = self.br("check", "--verify-s3", check=False)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(len(self.calls("head-object")), self.N_RAW)
        self.assertIn("falling back", p.stderr)
        del store[body["raw"][0]["s3_uri"].split("/", 3)[3]]
        self.store_file.write_text(json.dumps(store))
        p = self.br("check", "--verify-s3", check=False)
        self.assertEqual(p.returncode, 1)
        self.assertIn(" is not at ", p.stdout)

    def test_few_objects_use_heads_not_a_store_listing(self):
        rec = self.make_record()
        body = json.loads((self.root / rec).read_text())
        fake = self.root / "fake-bin"
        fake.mkdir()
        (fake / "aws").write_text(FAKE_STORE_AWS)
        (fake / "aws").chmod(0o755)
        store = self.root / "fake-store.json"
        store.write_text(json.dumps({r["s3_uri"].split("/", 3)[3]: r["bytes"] for r in body["raw"]}))
        self.env.update(PATH=str(fake) + os.pathsep + self.env["PATH"], FAKE_STORE=str(store),
                        FAKE_AWS_LOG=str(self.root / "aws-calls.jsonl"))
        self.commit_all()
        p = self.br("check", "--verify-s3", check=False)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(self.calls("list-objects-v2"), [])
        self.assertEqual(len(self.calls("head-object")), 1)

    def run_in_process(self, **limits):
        import contextlib, io, time
        from unittest.mock import patch
        module = self.canonical_module()
        old = dict(os.environ)
        os.environ.update(self.env)
        out = io.StringIO()
        try:
            with contextlib.ExitStack() as stack:
                for k, v in limits.items():
                    stack.enter_context(patch.object(module, k, v))
                stack.enter_context(contextlib.redirect_stdout(out))
                stack.enter_context(contextlib.redirect_stderr(io.StringIO()))
                t = time.monotonic()
                rc = module.main(["--root", str(self.root), "check", "--verify-s3"])
                return rc, out.getvalue(), time.monotonic() - t
        finally:
            os.environ.clear()
            os.environ.update(old)

    def test_hung_listing_fails_fast_with_a_clear_error(self):
        self.many_raw_fixture()
        self.env["FAKE_LIST_MODE"] = "hang"
        rc, out, elapsed = self.run_in_process(AWS_LIST_TIMEOUT_S=1)
        self.assertEqual(rc, 1)
        self.assertIn("FAIL: S3 could not be verified", out)
        self.assertIn("list-objects-v2", out)
        self.assertIn("did not finish within 1s", out)
        self.assertLess(elapsed, 20)

    def test_hung_head_fails_fast_with_a_clear_error(self):
        self.many_raw_fixture()
        self.env.update(FAKE_LIST_MODE="denied", FAKE_HEAD_MODE="hang")
        rc, out, elapsed = self.run_in_process(AWS_CALL_TIMEOUT_S=1)
        self.assertEqual(rc, 1)
        self.assertIn("head-object", out)
        self.assertIn("did not finish within 1s", out)
        self.assertLess(elapsed, 30)


if __name__ == "__main__":
    unittest.main()
