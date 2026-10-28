"""Refusal controls for source-bound Mathlib corpus registration.

Compiler/auditor mocks below test fail-closed orchestration, not native proofs.
The corpus CI job must execute the real compiler and exhaustive axiom auditor.
"""
import hashlib
import importlib.util
import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "corpus_gate", Path(__file__).with_name("current-corpus-gate.py"))
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)
REPOSITORY = gate.ROOT
PROJECT = gate.HECKE_CI.relative_to(REPOSITORY)


class QuarticRegistrationControls(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        self.project = self.root / PROJECT
        self.project.mkdir(parents=True)
        for name in ("lean-toolchain", "lakefile.toml", "lake-manifest.json"):
            shutil.copyfile(REPOSITORY / PROJECT / name, self.project / name)
        self.manifest = self.root / "tools/ci/quartic_certificates.json"
        self.manifest.parent.mkdir(parents=True)
        shutil.copyfile(REPOSITORY / "tools/ci/quartic_certificates.json", self.manifest)
        known_label = self.root / gate.KNOWN_LABEL_SOURCE
        known_label.parent.mkdir(parents=True)
        shutil.copyfile(REPOSITORY / gate.KNOWN_LABEL_SOURCE, known_label)
        self.root_patch = patch.object(gate, "ROOT", self.root)
        self.project_patch = patch.object(gate, "HECKE_CI", self.project)
        self.root_patch.start()
        self.project_patch.start()
        self.addCleanup(self.root_patch.stop)
        self.addCleanup(self.project_patch.stop)

    def test_original_bare_paths_are_explicitly_bound(self):
        sources = gate.reviewed_quartic_sources()
        self.assertEqual(len(sources), 37)
        self.assertEqual(sum("/formal/" not in p for p in sources), 3)

    def test_unknown_bare_source_still_refused_without_compilation(self):
        with patch.object(gate, "run") as run:
            run.return_value.stdout = "dependency-path\n"
            with self.assertRaisesRegex(ValueError, "unreviewed Lean corpus addition"):
                gate.check_new_hecke({"experiments/hecke-432-unreviewed/New.lean"})
            self.assertEqual(run.call_count, 1)  # environment lookup only

    def test_changed_registered_source_refused_before_compilation(self):
        path, expected = next(iter(gate.reviewed_quartic_sources().items()))
        file = self.root / path
        file.parent.mkdir(parents=True)
        file.write_text("theorem different : True := True.intro\n")
        with patch.object(gate, "run") as run:
            with self.assertRaisesRegex(ValueError, "reviewed quartic source changed"):
                gate.check_reviewed_quartic(path, expected, "")
            run.assert_not_called()

    def test_changed_build_pin_refused(self):
        data = json.loads(self.manifest.read_text())
        data["mathlib"] = "0" * 40
        self.manifest.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "build pins changed"):
            gate.reviewed_quartic_sources()

    def test_changed_project_bytes_refused(self):
        with (self.project / "lakefile.toml").open("a") as file:
            file.write("\n# changed dependency declaration\n")
        with self.assertRaisesRegex(ValueError, "project input changed"):
            gate.reviewed_quartic_sources()

    def test_symlink_source_refused_even_with_matching_bytes(self):
        path, _ = next(iter(gate.reviewed_quartic_sources().items()))
        target = self.root / "outside-source"
        target.write_text("theorem different : True := True.intro\n")
        file = self.root / path
        file.parent.mkdir(parents=True)
        file.symlink_to(target)
        with self.assertRaisesRegex(ValueError, "escapes repository"):
            gate.check_reviewed_quartic(path, hashlib.sha256(target.read_bytes()).hexdigest(), "")

    def test_known_label_dispatch_requires_native_checker(self):
        with patch.object(gate, "run") as run, patch.object(
                gate, "check_reviewed_quartic", return_value=gate.KNOWN_LABEL_SHA256) as check:
            run.return_value.stdout = "dependency-path\n"
            result = gate.check_new_hecke({gate.KNOWN_LABEL_SOURCE})
            check.assert_called_once_with(gate.KNOWN_LABEL_SOURCE,
                                          gate.KNOWN_LABEL_SHA256, "dependency-path",
                                          kind="known-label", expected_theorems=4)
            self.assertEqual(result, {gate.KNOWN_LABEL_SOURCE: gate.KNOWN_LABEL_SHA256})

    def test_another_documentation_module_remains_unreviewed(self):
        with patch.object(gate, "run") as run:
            run.return_value.stdout = "dependency-path\n"
            with self.assertRaisesRegex(ValueError, "unreviewed Lean corpus addition"):
                gate.check_new_hecke({"docs/unreviewed/Other.lean"})
            self.assertEqual(run.call_count, 1)

    def test_known_label_changed_source_refused_before_compilation(self):
        file = self.root / gate.KNOWN_LABEL_SOURCE
        file.write_text(file.read_text() + "\n-- changed\n")
        with patch.object(gate, "run") as run:
            with self.assertRaisesRegex(ValueError, "reviewed known-label source changed"):
                gate.check_reviewed_quartic(gate.KNOWN_LABEL_SOURCE, gate.KNOWN_LABEL_SHA256,
                                           "", kind="known-label", expected_theorems=4)
            run.assert_not_called()

    def test_known_label_compiler_failure_is_not_admission(self):
        with patch.object(gate, "run", side_effect=ValueError("native compiler failed")) as run:
            with self.assertRaisesRegex(ValueError, "native compiler failed"):
                gate.check_reviewed_quartic(gate.KNOWN_LABEL_SOURCE, gate.KNOWN_LABEL_SHA256,
                                           "", kind="known-label", expected_theorems=4)
            self.assertEqual(run.call_count, 1)

    def test_known_label_three_audited_theorems_cannot_pass(self):
        names = ["triangle_identity", "signed_second_moment", "signed_third_moment",
                 "positive_pair_product"]
        printed = "\n".join(f"'KnownLabelLeads.{name}' depends on axioms: [propext]"
                            for name in names) + "\n"
        audit = "\n".join(f"ok    KnownLabelLeads.{name}  [propext]" for name in names[:3])
        audit += "\naudited 3 theorems; 0 failing, 0 trusted\n"
        with patch.object(gate, "run") as run, redirect_stdout(StringIO()):
            run.side_effect = [type("Output", (), {"stdout": printed})(),
                               type("Output", (), {"stdout": audit})()]
            with self.assertRaisesRegex(ValueError, "reviewed theorem count changed"):
                gate.check_reviewed_quartic(gate.KNOWN_LABEL_SOURCE, gate.KNOWN_LABEL_SHA256,
                                           "", kind="known-label", expected_theorems=4)
            self.assertEqual(run.call_count, 2)

    def test_known_label_nonstandard_axiom_refused(self):
        names = ["triangle_identity", "signed_second_moment", "signed_third_moment",
                 "positive_pair_product"]
        printed = "\n".join(f"'KnownLabelLeads.{name}' depends on axioms: [ClaimAsAxiom]"
                            for name in names) + "\n"
        with patch.object(gate, "run") as run:
            run.return_value.stdout = printed
            with self.assertRaisesRegex(ValueError, "unexpected foundation"):
                gate.check_reviewed_quartic(gate.KNOWN_LABEL_SOURCE, gate.KNOWN_LABEL_SHA256,
                                           "", kind="known-label", expected_theorems=4)
            self.assertEqual(run.call_count, 1)


if __name__ == "__main__":
    unittest.main()
