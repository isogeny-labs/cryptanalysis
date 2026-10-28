"""Admission/refusal controls; mocked Lean outputs are not native proof evidence."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tempfile
from types import SimpleNamespace
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


class KnownLabelRegistrationControls(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        self.project = self.root / PROJECT
        self.project.mkdir(parents=True)
        for name in gate.KNOWN_LABEL_PROJECT_INPUTS:
            shutil.copyfile(REPOSITORY / PROJECT / name, self.project / name)
        self.source = self.root / gate.KNOWN_LABEL_SOURCE
        self.source.parent.mkdir(parents=True)
        shutil.copyfile(REPOSITORY / gate.KNOWN_LABEL_SOURCE, self.source)
        for name, value in (("ROOT", self.root), ("HECKE_CI", self.project)):
            active = patch.object(gate, name, value)
            active.start()
            self.addCleanup(active.stop)
        self.names = sorted(gate.KNOWN_LABEL_THEOREMS)
        self.printed = "".join(f"'{n}' depends on axioms: [propext, Quot.sound]\n"
                               for n in self.names)
        self.audited = ("".join(f"ok    {n}  [propext, Quot.sound]\n" for n in self.names)
                        + "audited 4 theorems; 0 failing, 0 trusted\n")

    def check_with_outputs(self, printed=None, audited=None):
        with patch.object(gate, "run") as run, contextlib.redirect_stdout(io.StringIO()):
            run.side_effect = [
                SimpleNamespace(stdout=self.printed if printed is None else printed),
                SimpleNamespace(stdout=self.audited if audited is None else audited),
            ]
            value = gate.check_known_label_algebra("pinned-dependencies")
            calls = run.call_args_list
        return value, calls

    def test_native_commands_use_original_bytes_isolated_output_and_module_audit(self):
        before = self.source.read_bytes()
        value, calls = self.check_with_outputs()
        self.assertEqual(value, gate.KNOWN_LABEL_SHA256)
        self.assertEqual(self.source.read_bytes(), before)
        build, audit = calls
        self.assertEqual(build.args[0][:5], ["lake", "env", "lean", "-R", str(self.root)])
        self.assertEqual(build.args[0][-1], str(self.source))
        output = Path(build.args[0][build.args[0].index("-o") + 1])
        self.assertFalse(output.is_relative_to(self.root))
        self.assertEqual(build.kwargs["cwd"], self.project)
        self.assertEqual(audit.args[0][-1], gate.KNOWN_LABEL_SOURCE[:-5].replace("/", "."))
        self.assertIn("AuditHeckeAxioms.lean", audit.args[0][-2])
        self.assertTrue(audit.kwargs["env"]["LEAN_PATH"].endswith("pinned-dependencies"))

    def test_changed_source_refused_before_compilation(self):
        self.source.write_text(self.source.read_text() + "\n-- changed\n")
        with patch.object(gate, "run") as run:
            with self.assertRaisesRegex(ValueError, "known-label source changed"):
                gate.check_known_label_algebra("")
            run.assert_not_called()

    def test_each_workspace_input_is_bound(self):
        for name in gate.KNOWN_LABEL_PROJECT_INPUTS:
            with self.subTest(name=name):
                file = self.project / name
                original = file.read_bytes()
                file.write_bytes(original + b"\n")
                with patch.object(gate, "run") as run:
                    with self.assertRaisesRegex(ValueError, "known-label project input changed"):
                        gate.check_known_label_algebra("")
                    run.assert_not_called()
                file.write_bytes(original)

    def test_matching_source_through_symlink_refused(self):
        target = self.root / "original.lean"
        self.source.rename(target)
        self.source.symlink_to(target)
        with self.assertRaisesRegex(ValueError, "escapes repository"):
            gate.check_known_label_algebra("")

    def test_native_printout_cannot_substitute_same_short_names_in_other_namespace(self):
        with self.assertRaisesRegex(ValueError, "native theorem identities changed"):
            self.check_with_outputs(printed=self.printed.replace("KnownLabelLeads.", "Other."))

    def test_missing_printout_refused(self):
        with self.assertRaisesRegex(ValueError, "incomplete native declaration audit"):
            self.check_with_outputs(printed="\n".join(self.printed.splitlines()[:-1]))

    def test_nonstandard_axiom_refused(self):
        with self.assertRaisesRegex(ValueError, "unexpected foundation"):
            self.check_with_outputs(printed=self.printed.replace("Quot.sound", "sorryAx"))

    def test_zero_or_failed_module_audit_refused(self):
        for output in ("", "audited 0 theorems; 0 failing, 0 trusted\n",
                       self.audited.replace("0 failing", "1 failing")):
            with self.subTest(output=output), self.assertRaisesRegex(ValueError, "incomplete exhaustive"):
                self.check_with_outputs(audited=output)

    def test_plausible_audit_count_with_wrong_names_refused(self):
        with self.assertRaisesRegex(ValueError, "named theorems missing"):
            self.check_with_outputs(audited=self.audited.replace("KnownLabelLeads.", "Other."))

    def test_native_compile_failure_propagates(self):
        with patch.object(gate, "run", side_effect=ValueError("native compiler failed")) as run:
            with self.assertRaisesRegex(ValueError, "native compiler failed"):
                gate.check_known_label_algebra("")
            self.assertEqual(run.call_count, 1)

    def test_source_mutation_during_audit_refused(self):
        def runtime(args, **kwargs):
            if args[:2] == ["lean", "--run"]:
                self.source.write_bytes(self.source.read_bytes() + b"\n")
                return SimpleNamespace(stdout=self.audited)
            return SimpleNamespace(stdout=self.printed)
        with patch.object(gate, "run", side_effect=runtime), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(ValueError, "source changed during audit"):
                gate.check_known_label_algebra("")

    def test_only_exact_added_path_has_new_dispatch(self):
        with patch.object(gate, "reviewed_quartic_sources", return_value={}), \
             patch.object(gate, "run", return_value=SimpleNamespace(stdout="dependencies\n")), \
             patch.object(gate, "check_known_label_algebra", return_value=gate.KNOWN_LABEL_SHA256) as known:
            self.assertEqual(gate.check_new_hecke({gate.KNOWN_LABEL_SOURCE}),
                             {gate.KNOWN_LABEL_SOURCE: gate.KNOWN_LABEL_SHA256})
            known.assert_called_once_with("dependencies")
            with self.assertRaisesRegex(ValueError, "unreviewed Lean corpus addition"):
                gate.check_new_hecke({gate.KNOWN_LABEL_SOURCE.replace("Algebra", "Other")})
            self.assertEqual(known.call_count, 1)


if __name__ == "__main__":
    unittest.main()
