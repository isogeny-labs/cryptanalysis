"""Refusal controls for original-path quartic corpus registration."""
import hashlib
import importlib.util
import json
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


if __name__ == "__main__":
    unittest.main()
