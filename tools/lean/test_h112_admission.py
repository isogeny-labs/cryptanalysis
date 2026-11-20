"""Admission refusal controls. Synthetic runtime output is not native proof evidence."""
import contextlib
import importlib.util
import io
from pathlib import Path
import shutil
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("h112_gate", Path(__file__).with_name("current-corpus-gate.py"))
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
REPO = gate.ROOT
PROJECT = gate.HECKE_CI.relative_to(REPO)


class H112AdmissionTests(unittest.TestCase):
    def setUp(self):
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.root = Path(scratch.name)
        self.project = self.root / PROJECT
        for name in [gate.H112_SOURCE, "tools/lean/AuditHeckeAxioms.lean", *[str(PROJECT / n) for n in gate.KNOWN_LABEL_PROJECT_INPUTS]]:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO / name, target)
        for name, value in [("ROOT", self.root), ("HECKE_CI", self.project)]:
            active = patch.object(gate, name, value)
            active.start()
            self.addCleanup(active.stop)

    def test_dispatch_is_one_exact_original_path(self):
        with patch.object(gate, "run", return_value=SimpleNamespace(stdout="deps\n")), patch.object(gate, "check_h112_interface", return_value=gate.H112_SHA256) as check:
            self.assertEqual(gate.check_new_hecke({gate.H112_SOURCE}), {gate.H112_SOURCE: gate.H112_SHA256})
            check.assert_called_once_with("deps")
            with self.assertRaisesRegex(ValueError, "unreviewed Lean corpus addition"):
                gate.check_new_hecke({gate.H112_SOURCE.replace("H112P3SecondDigitCarry", "Unreviewed")})

    def test_changed_source_refused_before_runtime(self):
        source = self.root / gate.H112_SOURCE
        source.write_bytes(source.read_bytes() + b"\n")
        with patch.object(gate, "run") as run:
            with self.assertRaisesRegex(ValueError, "source changed"):
                gate.check_h112_interface("")
            run.assert_not_called()

    def test_each_changed_project_input_refused(self):
        for name in gate.KNOWN_LABEL_PROJECT_INPUTS:
            with self.subTest(name=name):
                path = self.project / name
                original = path.read_bytes()
                path.write_bytes(original + b"\n")
                with patch.object(gate, "run") as run:
                    with self.assertRaisesRegex(ValueError, "H112 maintained project input changed"):
                        gate.check_h112_interface("")
                    run.assert_not_called()
                path.write_bytes(original)

    def runtime_outputs(self, audited_names=None, printed_names=None):
        names = sorted(gate.H112_THEOREMS if printed_names is None else printed_names)
        audited = sorted(gate.H112_MODULE_THEOREMS if audited_names is None else audited_names)
        printed = "".join(f"'{name}' depends on axioms: [propext]\n" for name in names)
        report = "".join(f"ok    {name}  [propext]\n" for name in audited) + f"audited {len(audited)} theorems; 0 failing, 0 trusted\n"
        types = "".join(f"{name} : True\n" for name in sorted(gate.H112_MODULE_THEOREMS))
        output = iter([printed, report, types])
        def run(args, **_kwargs):
            if "-o" in args:
                Path(args[args.index("-o") + 1]).write_bytes(b"synthetic unit fixture; not a Lean object")
            return SimpleNamespace(stdout=next(output))
        return run

    def test_eight_named_and_twelve_exhaustive_results_required(self):
        with patch.object(gate, "run", side_effect=self.runtime_outputs()), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(gate.check_h112_interface("deps"), gate.H112_SHA256)

    def test_missing_or_extra_generated_theorem_refused(self):
        for names in [gate.H112_THEOREMS, gate.H112_MODULE_THEOREMS | {"Unexpected.result"}]:
            with self.subTest(names=names), patch.object(gate, "run", side_effect=self.runtime_outputs(names)), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(ValueError, "reviewed theorem count changed"):
                    gate.check_h112_interface("")

    def test_same_count_renamed_generated_theorem_refused(self):
        names = (gate.H112_MODULE_THEOREMS - {"H112P3SecondDigitCarry.carry.eq_1"}) | {"Other.carry.eq_1"}
        with patch.object(gate, "run", side_effect=self.runtime_outputs(names)), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(ValueError, "native module theorem identities changed"):
                gate.check_h112_interface("")

    def test_same_basename_wrong_namespace_refused(self):
        names = {n.replace("H112P3SecondDigitCarry.", "Other.") for n in gate.H112_THEOREMS}
        with patch.object(gate, "run", side_effect=self.runtime_outputs(printed_names=names)):
            with self.assertRaisesRegex(ValueError, "native theorem identities changed"):
                gate.check_h112_interface("")

    def test_compiler_failure_never_admits_source(self):
        with patch.object(gate, "run", side_effect=ValueError("native compiler failed")):
            with self.assertRaisesRegex(ValueError, "native compiler failed"):
                gate.check_h112_interface("")

    def test_nested_comment_words_are_not_proof_tokens(self):
        source = '/- axiom /- sorry -/ admit -/\n-- native_decide\ntheorem result : True := by trivial\n'
        code = gate.code_without_comments(source)
        self.assertNotRegex(code, r'\b(?:axiom|sorry|admit|native_decide)\b')
        self.assertIn('theorem result : True := by trivial', code)

    def test_live_escape_tokens_after_comments_remain_visible(self):
        for token in ['axiom', 'sorry', 'admit', 'sorryAx', 'native_decide']:
            with self.subTest(token=token):
                code = gate.code_without_comments('/- harmless /- nested -/ -/\n' + token + '\n')
                self.assertRegex(code, r'\b' + token + r'\b')
