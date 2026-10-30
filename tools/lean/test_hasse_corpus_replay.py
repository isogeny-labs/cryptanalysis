"""Admission controls only; mocked commands do not supply native proof evidence."""
import hashlib
import importlib.util
from pathlib import Path
import shutil
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "corpus_gate", Path(__file__).with_name("current-corpus-gate.py"))
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)
REPOSITORY = gate.ROOT
PRIOR = REPOSITORY / "reports/hasse-interval-bridge-20261027"


class HasseIntervalReplayControls(unittest.TestCase):
    def setUp(self):
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.root = Path(scratch.name)
        self.formal = self.root / "bindings/rust/curve-audit/formal"
        self.formal.mkdir(parents=True)
        for name in ("HasseUnique.lean", "lean-toolchain"):
            shutil.copyfile(gate.HASSE_FORMAL / name, self.formal / name)
        auditor = self.root / "tools/lean/AuditAxioms.lean"
        auditor.parent.mkdir(parents=True)
        shutil.copyfile(REPOSITORY / "tools/lean/AuditAxioms.lean", auditor)
        self.build = (PRIOR / "source-build.stdout").read_text()
        self.audit = (PRIOR / "source-audit.stdout").read_text()
        for attribute, value in (("ROOT", self.root), ("HASSE_FORMAL", self.formal)):
            context = patch.object(gate, attribute, value)
            context.start()
            self.addCleanup(context.stop)

    def check(self):
        outputs = [SimpleNamespace(stdout=self.build, stderr=""),
                   SimpleNamespace(stdout=self.audit, stderr="")]
        with patch.object(gate, "run", side_effect=outputs) as commands:
            result = gate.check_changed_hasse_unique()
            self.assertEqual(commands.call_count, 2)
            compile_call, audit_call = commands.call_args_list
            self.assertIn("-o", compile_call.args[0])
            self.assertIn("--run", audit_call.args[0])
            self.assertEqual(compile_call.kwargs["cwd"], self.formal)
            self.assertEqual(compile_call.kwargs["env"]["ELAN_TOOLCHAIN"],
                             "leanprover/lean4:v4.34.1")
            self.assertEqual(compile_call.kwargs["env"]["LEAN_PATH"],
                             audit_call.kwargs["env"]["LEAN_PATH"])
            return result

    def refuses_without_native_command(self, message):
        with patch.object(gate, "run") as commands:
            with self.assertRaisesRegex(ValueError, message):
                gate.check_changed_hasse_unique()
            commands.assert_not_called()

    def test_complete_metadata_control_uses_both_native_commands(self):
        evidence = self.check()
        self.assertEqual(evidence["hasse_unique_axiom_stdout_sha256"],
                         hashlib.sha256(self.build.encode()).hexdigest())

    def test_changed_source_refused_before_compilation(self):
        with (self.formal / "HasseUnique.lean").open("a") as file:
            file.write("\n")
        self.refuses_without_native_command("source changed")

    def test_changed_own_toolchain_refused_before_compilation(self):
        (self.formal / "lean-toolchain").write_text("leanprover/lean4:v4.35.0-rc4\n")
        self.refuses_without_native_command("toolchain changed")

    def test_changed_auditor_refused_before_compilation(self):
        (self.root / "tools/lean/AuditAxioms.lean").write_text("changed\n")
        self.refuses_without_native_command("auditor changed")

    def test_proof_escape_refused_even_under_synthetic_refreshed_pin(self):
        source = self.formal / "HasseUnique.lean"
        source.write_text(source.read_text() + "\ntheorem bad : False := by sorry\n")
        with patch.object(gate, "HASSE_UNIQUE_SHA256", gate.digest(source)):
            self.refuses_without_native_command("forbidden proof escape")

    def test_missing_printout_refused_even_under_synthetic_refreshed_pin(self):
        source = self.formal / "HasseUnique.lean"
        source.write_text(source.read_text().replace(
            "#print axioms unique_multiple_from_center_bounds", ""))
        with patch.object(gate, "HASSE_UNIQUE_SHA256", gate.digest(source)):
            self.refuses_without_native_command("coverage changed")

    def test_native_build_failure_propagates(self):
        with patch.object(gate, "run", side_effect=ValueError("lean exited 1")):
            with self.assertRaisesRegex(ValueError, "lean exited 1"):
                gate.check_changed_hasse_unique()

    def test_incomplete_native_printout_refused(self):
        self.build = self.build.splitlines()[0] + "\n"
        with self.assertRaisesRegex(ValueError, "printout or foundations"):
            self.check()

    def test_unknown_native_axiom_refused(self):
        self.build = self.build.replace("propext", "Unreviewed.falseAxiom")
        with self.assertRaisesRegex(ValueError, "printout or foundations"):
            self.check()

    def test_incomplete_transitive_audit_refused(self):
        self.audit = self.audit.replace(
            "ok    CurveAudit.unique_multiple_from_center_bounds  [propext, Quot.sound]\n", "")
        with self.assertRaisesRegex(ValueError, "transitive audit changed"):
            self.check()

    def test_wrong_transitive_name_refused_despite_same_count(self):
        self.audit = self.audit.replace("unique_multiple_from_center_bounds", "unrelated")
        with self.assertRaisesRegex(ValueError, "transitive audit changed"):
            self.check()

    def test_trusted_exception_refused(self):
        self.audit = self.audit.replace("0 trusted", "1 trusted")
        with self.assertRaisesRegex(ValueError, "transitive audit changed"):
            self.check()

    def test_native_audit_failure_propagates(self):
        with patch.object(gate, "run", side_effect=[
                SimpleNamespace(stdout=self.build, stderr=""), ValueError("audit exited 1")]):
            with self.assertRaisesRegex(ValueError, "audit exited 1"):
                gate.check_changed_hasse_unique()


if __name__ == "__main__":
    unittest.main()
