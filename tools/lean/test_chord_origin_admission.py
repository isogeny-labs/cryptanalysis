"""Chord-origin admission controls; synthetic outputs are not native evidence."""
import contextlib
import importlib.util
import io
from pathlib import Path
import shutil
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("chord_gate", Path(__file__).with_name("current-corpus-gate.py"))
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
REPO = gate.ROOT
PROJECT = gate.HECKE_CI.relative_to(REPO)


class ChordOriginAdmissionTests(unittest.TestCase):
    def setUp(self):
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.root = Path(scratch.name)
        self.project = self.root / PROJECT
        original = Path(gate.CHORD_ORIGIN_SOURCE).parent
        files = [gate.CHORD_ORIGIN_SOURCE, "tools/lean/AuditHeckeAxioms.lean"]
        files += [str(PROJECT / n) for n in gate.KNOWN_LABEL_PROJECT_INPUTS]
        files += [str(original / n) for n in gate.CHORD_ORIGIN_PROJECT_INPUTS]
        for name in files:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO / name, target)
        for name, value in [("ROOT", self.root), ("HECKE_CI", self.project)]:
            active = patch.object(gate, name, value)
            active.start()
            self.addCleanup(active.stop)

    def test_only_exact_research_source_is_dispatched(self):
        with patch.object(gate, "run", return_value=SimpleNamespace(stdout="deps\n")), patch.object(gate, "check_chord_origin", return_value=gate.CHORD_ORIGIN_SHA256) as check:
            self.assertEqual(gate.check_new_hecke({gate.CHORD_ORIGIN_SOURCE}), {gate.CHORD_ORIGIN_SOURCE: gate.CHORD_ORIGIN_SHA256})
            check.assert_called_once_with("deps")
            with self.assertRaisesRegex(ValueError, "unreviewed Lean corpus addition"):
                gate.check_new_hecke({gate.CHORD_ORIGIN_SOURCE.replace("ChordOrigin", "Other")})

    def test_original_source_change_is_refused(self):
        file = self.root / gate.CHORD_ORIGIN_SOURCE
        file.write_bytes(file.read_bytes() + b"\n")
        with patch.object(gate, "run") as run:
            with self.assertRaisesRegex(ValueError, "source changed"):
                gate.check_chord_origin("")
            run.assert_not_called()

    def test_original_and_maintained_build_inputs_are_pinned(self):
        for folder, names in [(self.project, gate.KNOWN_LABEL_PROJECT_INPUTS), ((self.root / gate.CHORD_ORIGIN_SOURCE).parent, gate.CHORD_ORIGIN_PROJECT_INPUTS)]:
            for name in names:
                with self.subTest(folder=folder, name=name):
                    file = folder / name
                    original = file.read_bytes()
                    file.write_bytes(original + b"\n")
                    with patch.object(gate, "run") as run:
                        with self.assertRaisesRegex(ValueError, "project input changed"):
                            gate.check_chord_origin("")
                        run.assert_not_called()
                    file.write_bytes(original)

    def runtime(self, names=None, axiom="propext"):
        names = sorted(gate.CHORD_ORIGIN_THEOREMS if names is None else names)
        printed = "".join(f"'{n}' depends on axioms: [{axiom}]\n" for n in sorted(gate.CHORD_ORIGIN_THEOREMS))
        audit = "".join(f"ok    {n}  [propext]\n" for n in names) + f"audited {len(names)} theorems; 0 failing, 0 trusted\n"
        types = "".join(f"{n} : True\n" for n in sorted(gate.CHORD_ORIGIN_THEOREMS))
        outputs = iter([printed, audit, types])
        def run(args, **_kwargs):
            if "-o" in args:
                Path(args[args.index("-o") + 1]).write_bytes(b"synthetic fixture; not a Lean object")
            return SimpleNamespace(stdout=next(outputs))
        return run

    def test_complete_four_theorem_metadata_path(self):
        with patch.object(gate, "run", side_effect=self.runtime()), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(gate.check_chord_origin("deps"), gate.CHORD_ORIGIN_SHA256)

    def test_three_theorems_cannot_pass(self):
        names = sorted(gate.CHORD_ORIGIN_THEOREMS)[:3]
        with patch.object(gate, "run", side_effect=self.runtime(names)), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(ValueError, "reviewed theorem count changed"):
                gate.check_chord_origin("")

    def test_same_count_wrong_identity_cannot_pass(self):
        names = (gate.CHORD_ORIGIN_THEOREMS - {"XedniChordOrigin.shifted_target_recovers"}) | {"Other.shifted_target_recovers"}
        with patch.object(gate, "run", side_effect=self.runtime(names)), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(ValueError, "native module theorem identities changed"):
                gate.check_chord_origin("")

    def test_nonstandard_axiom_is_refused(self):
        with patch.object(gate, "run", side_effect=self.runtime(axiom="InventedPremise")):
            with self.assertRaisesRegex(ValueError, "unexpected foundation"):
                gate.check_chord_origin("")

    def test_native_compiler_failure_is_not_admission(self):
        with patch.object(gate, "run", side_effect=ValueError("native compile failed")):
            with self.assertRaisesRegex(ValueError, "native compile failed"):
                gate.check_chord_origin("")
