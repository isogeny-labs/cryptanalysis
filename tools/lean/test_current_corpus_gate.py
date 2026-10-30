"""Admission/refusal controls; mocked Lean outputs are not native proof evidence."""
import contextlib
import hashlib
import gzip
import importlib.util
import io
import json
import os
import sys
import subprocess
from contextlib import redirect_stdout
from io import StringIO
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


def fixture_object(args):
    if "-o" in args:
        Path(args[args.index("-o") + 1]).write_bytes(b"synthetic unit fixture, NOT Lean output")


class QuarticRegistrationControls(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        self.project = self.root / PROJECT
        self.project.mkdir(parents=True)
        auditor = self.root / "tools/lean/AuditHeckeAxioms.lean"
        auditor.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPOSITORY / "tools/lean/AuditHeckeAxioms.lean", auditor)
        for name in ("lean-toolchain", "lakefile.toml", "lake-manifest.json"):
            shutil.copyfile(REPOSITORY / PROJECT / name, self.project / name)
        self.manifest = self.root / "tools/ci/quartic_certificates.json"
        self.manifest.parent.mkdir(parents=True)
        shutil.copyfile(REPOSITORY / "tools/ci/quartic_certificates.json", self.manifest)
        known_label = self.root / gate.KNOWN_LABEL_SOURCE
        known_label.parent.mkdir(parents=True)
        shutil.copyfile(REPOSITORY / gate.KNOWN_LABEL_SOURCE, known_label)
        pair_index = self.root / gate.PAIR_INDEX_SOURCE
        pair_index.parent.mkdir(parents=True)
        shutil.copyfile(REPOSITORY / gate.PAIR_INDEX_SOURCE, pair_index)
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
                gate, "check_known_label_algebra", return_value=gate.KNOWN_LABEL_SHA256) as check:
            run.return_value.stdout = "dependency-path\n"
            result = gate.check_new_hecke({gate.KNOWN_LABEL_SOURCE})
            check.assert_called_once_with("dependency-path")
            self.assertEqual(result, {gate.KNOWN_LABEL_SOURCE: gate.KNOWN_LABEL_SHA256})

    def test_another_documentation_module_remains_unreviewed(self):
        with patch.object(gate, "run") as run:
            run.return_value.stdout = "dependency-path\n"
            with self.assertRaisesRegex(ValueError, "unreviewed Lean corpus addition"):
                gate.check_new_hecke({"docs/unreviewed/Other.lean"})
            self.assertEqual(run.call_count, 1)

    def test_pair_index_dispatch_requires_seven_native_audits(self):
        with patch.object(gate, "run") as run, patch.object(
                gate, "check_pair_index_algebra", return_value=gate.PAIR_INDEX_SHA256) as check:
            run.return_value.stdout = "dependency-path\n"
            result = gate.check_new_hecke({gate.PAIR_INDEX_SOURCE})
            check.assert_called_once_with("dependency-path")
            self.assertEqual(result, {gate.PAIR_INDEX_SOURCE: gate.PAIR_INDEX_SHA256})

    def test_pair_index_native_checker_requires_exact_names(self):
        with patch.object(gate, "check_pinned_mathlib_source",
                          return_value=gate.PAIR_INDEX_SHA256) as check:
            self.assertEqual(gate.check_pair_index_algebra("deps"), gate.PAIR_INDEX_SHA256)
            check.assert_called_once_with(
                gate.PAIR_INDEX_SOURCE, gate.PAIR_INDEX_SHA256, "deps",
                label="known-label-pair-index", exact_names=gate.PAIR_INDEX_THEOREMS,
                expected_theorems=7)

    def test_pair_index_changed_source_refused_before_native_compilation(self):
        file = self.root / gate.PAIR_INDEX_SOURCE
        file.write_bytes(file.read_bytes()+b"\n")
        with patch.object(gate, "run") as run:
            with self.assertRaisesRegex(ValueError, "source changed"):
                gate.check_pair_index_algebra("")
            run.assert_not_called()

    def test_pair_index_incomplete_native_module_audit_refused(self):
        source = (self.root / gate.PAIR_INDEX_SOURCE).read_text()
        names = gate.re.findall(r"^#print axioms\s+(\w+)", source, gate.re.MULTILINE)
        self.assertEqual(len(names), 7)
        printed = "".join(f"'KnownLabelPairIndex.{n}' depends on axioms: [propext]\n"
                          for n in names)
        audited = ("".join(f"ok    KnownLabelPairIndex.{n}  [propext]\n" for n in names[:6])
                   + "audited 6 theorems; 0 failing, 0 trusted\n")
        outputs = iter([SimpleNamespace(stdout=printed), SimpleNamespace(stdout=audited)])

        def native_metadata_stub(args, **_kwargs):
            fixture_object(args)
            return next(outputs)

        with patch.object(gate, "run") as run, redirect_stdout(StringIO()):
            run.side_effect = native_metadata_stub
            with self.assertRaisesRegex(ValueError, "reviewed theorem count changed"):
                gate.check_pair_index_algebra("")

    def test_known_label_changed_source_refused_before_compilation(self):
        file = self.root / gate.KNOWN_LABEL_SOURCE
        file.write_text(file.read_text() + "\n-- changed\n")
        with patch.object(gate, "run") as run:
            with self.assertRaisesRegex(ValueError, "known-label source changed"):
                gate.check_known_label_algebra("")
            run.assert_not_called()

    def test_known_label_compiler_failure_is_not_admission(self):
        with patch.object(gate, "run", side_effect=ValueError("native compiler failed")) as run:
            with self.assertRaisesRegex(ValueError, "native compiler failed"):
                gate.check_known_label_algebra("")
            self.assertEqual(run.call_count, 1)

    def test_known_label_three_audited_theorems_cannot_pass(self):
        names = ["triangle_identity", "signed_second_moment", "signed_third_moment",
                 "positive_pair_product"]
        printed = "\n".join(f"'KnownLabelLeads.{name}' depends on axioms: [propext]"
                            for name in names) + "\n"
        audit = "\n".join(f"ok    KnownLabelLeads.{name}  [propext]" for name in names[:3])
        audit += "\naudited 3 theorems; 0 failing, 0 trusted\n"
        with patch.object(gate, "run") as run, redirect_stdout(StringIO()):
            outputs = iter([printed, audit])
            def runtime(args, **kwargs):
                fixture_object(args)
                return SimpleNamespace(stdout=next(outputs))
            run.side_effect = runtime
            with self.assertRaisesRegex(ValueError, "reviewed theorem count changed"):
                gate.check_known_label_algebra("")
            self.assertEqual(run.call_count, 2)

    def test_known_label_nonstandard_axiom_refused(self):
        names = ["triangle_identity", "signed_second_moment", "signed_third_moment",
                 "positive_pair_product"]
        printed = "\n".join(f"'KnownLabelLeads.{name}' depends on axioms: [ClaimAsAxiom]"
                            for name in names) + "\n"
        with patch.object(gate, "run") as run:
            run.return_value.stdout = printed
            with self.assertRaisesRegex(ValueError, "unexpected foundation"):
                gate.check_known_label_algebra("")
            self.assertEqual(run.call_count, 1)


class KnownLabelRegistrationControls(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        self.project = self.root / PROJECT
        self.project.mkdir(parents=True)
        auditor = self.root / "tools/lean/AuditHeckeAxioms.lean"
        auditor.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPOSITORY / "tools/lean/AuditHeckeAxioms.lean", auditor)
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
        # Synthetic headers test orchestration only; no proposition is verified.
        self.types = "".join(f"@{n}.{{u_1}} : Type u_1\n" for n in self.names)

    def check_with_outputs(self, printed=None, audited=None):
        with patch.object(gate, "run") as run, contextlib.redirect_stdout(io.StringIO()):
            outputs = iter([self.printed if printed is None else printed,
                            self.audited if audited is None else audited, self.types])
            def runtime(args, **kwargs):
                fixture_object(args)
                return SimpleNamespace(stdout=next(outputs))
            run.side_effect = runtime
            value = gate.check_known_label_algebra("pinned-dependencies")
            calls = run.call_args_list
        return value, calls

    def test_native_commands_use_original_bytes_isolated_output_and_module_audit(self):
        before = self.source.read_bytes()
        value, calls = self.check_with_outputs()
        self.assertEqual(value, gate.KNOWN_LABEL_SHA256)
        self.assertEqual(self.source.read_bytes(), before)
        build, audit, types = calls
        self.assertEqual(build.args[0][:5], ["lake", "env", "lean", "-R", str(self.root)])
        self.assertEqual(build.args[0][-1], str(self.source))
        output = Path(build.args[0][build.args[0].index("-o") + 1])
        self.assertFalse(output.is_relative_to(self.root))
        self.assertEqual(build.kwargs["cwd"], self.project)
        self.assertEqual(audit.args[0][-1], gate.KNOWN_LABEL_SOURCE[:-5].replace("/", "."))
        self.assertIn("AuditHeckeAxioms.lean", audit.args[0][-2])
        self.assertTrue(audit.kwargs["env"]["LEAN_PATH"].endswith("pinned-dependencies"))
        self.assertEqual(types.args[0][0], "lean")
        self.assertEqual(Path(types.args[0][1]).name, "CollectedTypes.lean")
        self.assertEqual(types.kwargs["env"]["LEAN_PATH"], audit.kwargs["env"]["LEAN_PATH"])

    def test_extra_audited_theorem_refused(self):
        audited = self.audited.replace("audited 4 theorems", "ok    Unexpected.extra  []\naudited 5 theorems")
        with self.assertRaisesRegex(ValueError, "reviewed theorem count changed"):
            self.check_with_outputs(audited=audited)

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
            fixture_object(args)
            if args[:2] == ["lean", "--run"]:
                self.source.write_bytes(self.source.read_bytes() + b"\n")
                return SimpleNamespace(stdout=self.audited)
            return SimpleNamespace(stdout=self.printed)
        with patch.object(gate, "run", side_effect=runtime), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(ValueError, "source changed during audit"):
                gate.check_known_label_algebra("")

    def test_missing_compiled_object_cannot_reuse_plausible_stdout(self):
        with patch.object(gate, "run", return_value=SimpleNamespace(stdout=self.printed)):
            with self.assertRaisesRegex(ValueError, "compiled object missing"):
                gate.check_known_label_algebra("")

    def test_auditor_change_refused_before_native(self):
        auditor = self.root / "tools/lean/AuditHeckeAxioms.lean"
        auditor.write_bytes(auditor.read_bytes() + b"\n")
        with patch.object(gate, "run") as native:
            with self.assertRaisesRegex(ValueError, "runtime auditor changed"):
                gate.check_known_label_algebra("")
            native.assert_not_called()

    def test_compiled_object_and_auditor_mutations_refused_at_phase_boundaries(self):
        for phase in ("audit", "types"):
            for target in ("object", "remove", "sidecar", "auditor", "snapshot"):
                with self.subTest(phase=phase, target=target):
                    auditor = self.root / "tools/lean/AuditHeckeAxioms.lean"
                    original = auditor.read_bytes()
                    compiled = None
                    audit_snapshot = None
                    def runtime(args, **kwargs):
                        nonlocal compiled, audit_snapshot
                        if "-o" in args:
                            fixture_object(args)
                            compiled = Path(args[args.index("-o") + 1])
                            return SimpleNamespace(stdout=self.printed)
                        auditing = args[:2] == ["lean", "--run"]
                        if auditing:
                            audit_snapshot = Path(args[2])
                        if ("audit" if auditing else "types") == phase:
                            if target == "object":
                                compiled.write_bytes(b"replaced")
                            elif target == "remove":
                                compiled.unlink()
                            elif target == "sidecar":
                                compiled.with_name(compiled.name + ".private").write_bytes(b"added")
                            elif target == "auditor":
                                auditor.write_bytes(original + b"\n")
                            else:
                                audit_snapshot.write_bytes(original + b"\n")
                        return SimpleNamespace(stdout=self.audited if auditing else self.types)
                    try:
                        with patch.object(gate, "run", side_effect=runtime), redirect_stdout(StringIO()):
                            with self.assertRaisesRegex(ValueError, "compiled object|runtime auditor"):
                                gate.check_known_label_algebra("")
                    finally:
                        auditor.write_bytes(original)

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

    def test_workspace_mutation_during_each_native_command_refused(self):
        for name in gate.KNOWN_LABEL_PROJECT_INPUTS:
            for phase in ("compile", "audit", "types"):
                with self.subTest(name=name, phase=phase):
                    file = self.project / name
                    original = file.read_bytes()
                    def runtime(args, **kwargs):
                        fixture_object(args)
                        auditing = args[:2] == ["lean", "--run"]
                        typing = args[0] == "lean" and not auditing
                        current_phase = "audit" if auditing else "types" if typing else "compile"
                        if current_phase == phase:
                            file.write_bytes(original + b"\n")
                        return SimpleNamespace(stdout=self.audited if auditing else
                                               self.types if typing else self.printed)
                    try:
                        with patch.object(gate, "run", side_effect=runtime), \
                             contextlib.redirect_stdout(io.StringIO()):
                            with self.assertRaisesRegex(ValueError, "known-label project input changed"):
                                gate.check_known_label_algebra("")
                    finally:
                        file.write_bytes(original)


class ElaboratedTypeControls(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.names = gate.KNOWN_LABEL_THEOREMS
        self.types = "".join(f"@{n}.{{u_1}} : Type u_1\n" for n in sorted(self.names))

    def collect(self, output, source=gate.KNOWN_LABEL_SOURCE):
        with patch.object(gate, "run", return_value=SimpleNamespace(stdout=output)), \
             contextlib.redirect_stdout(io.StringIO()):
            return gate.collect_elaborated_types(
                source, self.names, self.scratch.name, "dependencies")

    def test_real_native_pair_index_wrapped_universe_headers(self):
        fixtures = REPOSITORY / "tools/lean/fixtures"
        meta = json.loads((fixtures / "pair-index-native-wrapped-types.json").read_text())
        raw = gzip.decompress((fixtures / "pair-index-native-wrapped-types.txt.gz").read_bytes())
        self.assertEqual(hashlib.sha256(raw).hexdigest(), meta["native_stdout_sha256"])
        self.assertEqual(set(meta["names"]), gate.PAIR_INDEX_THEOREMS)
        self.names = gate.PAIR_INDEX_THEOREMS
        self.assertEqual(self.collect(raw.decode(), gate.PAIR_INDEX_SOURCE), raw.decode())

    def test_wrapped_headers_still_reject_missing_duplicate_and_unclosed_lists(self):
        wrapped = self.types.replace("{u_1}", "{u_1,\n    u_2}")
        first = sorted(self.names)[0]
        header = f"@{first}.{{u_1,\n    u_2}} : Type u_1\n"
        for output in (wrapped.replace(header, ""), wrapped + header,
                       wrapped.replace("u_2}", "u_2", 1)):
            with self.subTest(output=output), self.assertRaisesRegex(ValueError, "incomplete native"):
                self.collect(output)

    def test_wrapper_imports_compiled_original_and_prints_exact_names(self):
        self.assertEqual(self.collect(self.types), self.types)
        wrapper = (Path(self.scratch.name) / "CollectedTypes.lean").read_text()
        self.assertTrue(wrapper.startswith(
            "import «docs».«known-label-next-leads-20261028».«Algebra»\n"))
        self.assertIn("set_option pp.fullNames true", wrapper)
        self.assertEqual([line for line in wrapper.splitlines() if line.startswith("#check")],
                         [f"#check @{n}" for n in sorted(self.names)])

    def test_empty_missing_duplicate_and_wrong_namespace_outputs_refused(self):
        lines = self.types.splitlines(keepends=True)
        for output in ("", "".join(lines[:-1]), "".join(lines[:-1] + [lines[0]]),
                       self.types.replace("KnownLabelLeads", "Other")):
            with self.subTest(output=output), self.assertRaisesRegex(ValueError, "incomplete native"):
                self.collect(output)

    def test_empty_type_body_refused(self):
        with self.assertRaisesRegex(ValueError, "incomplete native"):
            self.collect("\n".join(f"@{n} :" for n in self.names))

    def test_native_type_command_failure_propagates(self):
        with patch.object(gate, "run", side_effect=ValueError("native type command failed")):
            with self.assertRaisesRegex(ValueError, "native type command failed"):
                gate.collect_elaborated_types(gate.KNOWN_LABEL_SOURCE, self.names,
                                             self.scratch.name, "dependencies")

    def test_changed_wrapper_refused(self):
        def native(args, **kwargs):
            Path(args[-1]).write_text("#check True\n")
            return SimpleNamespace(stdout=self.types)
        with patch.object(gate, "run", side_effect=native):
            with self.assertRaisesRegex(ValueError, "wrapper changed"):
                gate.collect_elaborated_types(gate.KNOWN_LABEL_SOURCE, self.names,
                                             self.scratch.name, "dependencies")

    def test_unsafe_module_or_empty_names_refused_before_native(self):
        for path, names in (("../escape.lean", self.names), (gate.KNOWN_LABEL_SOURCE, frozenset()),
                            (gate.KNOWN_LABEL_SOURCE, frozenset({"x\n#check True"}))):
            with self.subTest(path=path, names=names), patch.object(gate, "run") as native:
                with self.assertRaisesRegex(ValueError, "invalid"):
                    gate.collect_elaborated_types(path, names, self.scratch.name, "dependencies")
                native.assert_not_called()


class DurableDiagnosticsControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        active = patch.dict(os.environ, {"LEAN_CORPUS_EVIDENCE_DIR": str(self.root)})
        active.start()
        self.addCleanup(active.stop)

    def test_real_nonzero_child_retains_complete_bytes_and_exit(self):
        args = [sys.executable, "-c", "import os; os.write(1,b'out\\xff'); os.write(2,b'E'*4000); raise SystemExit(7)"]
        with self.assertRaisesRegex(ValueError, "exited 7"):
            gate.run(args, timeout=5)
        directory, = self.root.glob("command-*")
        self.assertEqual((directory / "stdout.bin").read_bytes(), b"out\xff")
        self.assertEqual((directory / "stderr.bin").read_bytes(), b"E" * 4000)
        record = json.loads((directory / "record.json").read_text())
        self.assertEqual(record["returncode"], 7)
        self.assertEqual(record["argv"], args)
        self.assertFalse(record["timed_out"])

    def test_timeout_retains_partial_output_and_unknown_exit(self):
        failure = subprocess.TimeoutExpired(["lean"], 5, output=b"partial", stderr=b"error")
        with patch.object(gate.subprocess, "run", side_effect=failure):
            with self.assertRaises(subprocess.TimeoutExpired):
                gate.run(["lean"], timeout=5)
        directory, = self.root.glob("command-*")
        record = json.loads((directory / "record.json").read_text())
        self.assertIsNone(record["returncode"])
        self.assertTrue(record["timed_out"])
        self.assertEqual((directory / "stdout.bin").read_bytes(), b"partial")
        self.assertEqual((directory / "stderr.bin").read_bytes(), b"error")

    def test_opted_in_real_failure_prints_bounded_tail_and_retains_all_bytes(self):
        args = [sys.executable, "-c", "import os; os.write(1,b'out\\xff'); os.write(2,b'E'*10000+b'END'); raise SystemExit(7)"]
        console = io.StringIO()
        with contextlib.redirect_stdout(console):
            with self.assertRaisesRegex(ValueError, "exited 7"):
                gate.run(args, timeout=5, failure_diagnostics=True)
        directory, = self.root.glob("command-*")
        self.assertEqual((directory / "stdout.bin").read_bytes(), b"out\xff")
        self.assertEqual((directory / "stderr.bin").read_bytes(), b"E" * 10000 + b"END")
        rendered = console.getvalue()
        self.assertIn("out\\xff", rendered)
        self.assertIn("last 8192 of 10003 raw bytes", rendered)
        self.assertNotIn("E" * 10000, rendered)
        self.assertTrue(rendered.rstrip().endswith("END"))
        self.assertEqual(json.loads((directory / "record.json").read_text())["returncode"], 7)

    def test_success_does_not_print_failure_payload(self):
        args = [sys.executable, "-c", "print('successful child output')"]
        console = io.StringIO()
        with contextlib.redirect_stdout(console):
            result = gate.run(args, timeout=5, failure_diagnostics=True)
        self.assertEqual(result.stdout, "successful child output\n")
        self.assertNotIn("failure stdout", console.getvalue())
        self.assertNotIn("successful child output", console.getvalue())

    def test_malformed_zero_exit_types_and_wrapper_survive_cleanup(self):
        with tempfile.TemporaryDirectory() as scratch:
            with patch.object(gate, "run", return_value=SimpleNamespace(stdout="wrong output\n")):
                with self.assertRaisesRegex(ValueError, "incomplete native"):
                    gate.collect_elaborated_types(gate.KNOWN_LABEL_SOURCE,
                                                 gate.KNOWN_LABEL_THEOREMS, scratch, "deps")
        wrapper, = self.root.glob("type-wrapper-*/CollectedTypes.lean")
        self.assertEqual(wrapper.read_text().count("#check @KnownLabelLeads."), 4)
        output, = self.root.glob("type-output-*/stdout.txt")
        self.assertEqual(output.read_text(), "wrong output\n")


class EngineeringSourceAdmissionControls(unittest.TestCase):
    """Synthetic compiler responses check refusal behavior, never prove lemmas."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.project = self.root / PROJECT
        self.project.mkdir(parents=True)
        for name in ("lean-toolchain", "lakefile.toml", "lake-manifest.json"):
            shutil.copyfile(REPOSITORY / PROJECT / name, self.project / name)
        context = Path(gate.CORE_COMPATIBILITY_CONTEXT).parent
        (self.root / context).mkdir(parents=True)
        for name in ("lean-toolchain", "DEPENDENCIES.json"):
            shutil.copyfile(REPOSITORY / context / name, self.root / context / name)
        self.source = self.root / gate.CORE_COMPATIBILITY_SOURCE
        self.source.parent.mkdir(parents=True)
        shutil.copyfile(REPOSITORY / gate.CORE_COMPATIBILITY_SOURCE, self.source)
        for name, value in (("ROOT", self.root), ("HECKE_CI", self.project)):
            active = patch.object(gate, name, value)
            active.start()
            self.addCleanup(active.stop)
        active = patch.object(gate, "reviewed_quartic_sources", return_value={})
        active.start()
        self.addCleanup(active.stop)
        self.lines = [
            "'XedniCoreCompatibility.constant_bound' does not depend on any axioms\n",
            "'XedniCoreCompatibility.successor_nonzero' depends on axioms: [propext]\n",
            "'XedniCoreCompatibility.bound_contradiction' depends on axioms: [propext]\n",
        ]

    def native(self, output):
        def response(args, **kwargs):
            return SimpleNamespace(stdout="dependencies" if "printenv" in args else output)
        return response

    def test_discovery_retains_ci_reports_and_separates_only_existing_selftests(self):
        unknown = "reports/ci-new/Unreviewed.lean"
        paths = [gate.CORE_COMPATIBILITY_SOURCE, unknown,
                 gate.CORE_COMPATIBILITY_CONTEXT, "tools/lean/selftest/Positive.lean"]
        with patch.object(gate, "run", return_value=SimpleNamespace(stdout="\n".join(paths))):
            self.assertEqual(gate.tracked_corpus_sources(), paths[:-1])

    def test_unregistered_ci_report_is_rejected_before_any_compilation(self):
        with patch.object(gate, "run", side_effect=self.native("")) as native:
            with self.assertRaisesRegex(ValueError, "unreviewed Lean corpus addition"):
                gate.check_new_hecke({"reports/ci-new/Unreviewed.lean"})
            self.assertEqual(native.call_count, 1)
            self.assertIn("printenv", native.call_args.args[0])

    def test_exact_indented_regression_source_requires_all_three_native_audits(self):
        with patch.object(gate, "run", side_effect=self.native("".join(self.lines))) as native:
            console = StringIO()
            with redirect_stdout(console):
                checked = gate.check_new_hecke({gate.CORE_COMPATIBILITY_SOURCE})
            self.assertEqual(checked, {gate.CORE_COMPATIBILITY_SOURCE:
                                       gate.CORE_COMPATIBILITY_SHA256})
            self.assertEqual(native.call_count, 2)
            self.assertEqual(native.call_args.kwargs["cwd"], self.project)
            self.assertEqual(native.call_args.kwargs["timeout"], 900)
            self.assertTrue(native.call_args.kwargs["failure_diagnostics"])
            self.assertIn("verified native axiom outputs:", console.getvalue())
            for line in self.lines:
                self.assertIn(line, console.getvalue())

    def test_changed_regression_source_is_rejected_before_compilation(self):
        self.source.write_text(self.source.read_text() + "\n-- changed\n")
        with patch.object(gate, "run", side_effect=self.native("")) as native:
            with self.assertRaisesRegex(ValueError, "core compatibility source changed"):
                gate.check_new_hecke({gate.CORE_COMPATIBILITY_SOURCE})
            self.assertEqual(native.call_count, 1)

    def test_missing_extra_and_duplicate_native_audits_are_rejected(self):
        for lines in (self.lines[:-1], self.lines + [self.lines[0]],
                      [self.lines[0], self.lines[1], self.lines[1]]):
            with self.subTest(lines=lines), patch.object(
                    gate, "run", side_effect=self.native("".join(lines))):
                with redirect_stdout(StringIO()), self.assertRaisesRegex(
                        ValueError, "incomplete native axiom output"):
                    gate.check_new_hecke({gate.CORE_COMPATIBILITY_SOURCE})

    def test_nonstandard_foundation_is_rejected(self):
        output = "".join(self.lines).replace("[propext]", "[ClaimAsAxiom]", 1)
        with patch.object(gate, "run", side_effect=self.native(output)):
            with redirect_stdout(StringIO()), self.assertRaisesRegex(
                    ValueError, "unexpected foundation"):
                gate.check_new_hecke({gate.CORE_COMPATIBILITY_SOURCE})

    def test_changed_recorded_build_context_is_rejected(self):
        dependencies = (self.root / gate.CORE_COMPATIBILITY_CONTEXT).parent / "DEPENDENCIES.json"
        record = json.loads(dependencies.read_text())
        record["mathlib_revision"] = "0" * 40
        dependencies.write_text(json.dumps(record))
        with patch.object(gate, "run", side_effect=self.native("")) as native:
            with self.assertRaisesRegex(ValueError, "recorded build dependencies changed"):
                gate.check_new_hecke({gate.CORE_COMPATIBILITY_SOURCE})
            self.assertEqual(native.call_count, 1)


if __name__ == "__main__":
    unittest.main()

