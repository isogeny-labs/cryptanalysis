"""Refusal and cache controls. Synthetic objects here are not Lean proof evidence."""
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout

SPEC = importlib.util.spec_from_file_location("formal_projects", Path(__file__).with_name("check_formal_projects.py"))
formal = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(formal)


def digest(data):
    return hashlib.sha256(data).hexdigest()


class FormalProjectControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.projects = ["experiments/xedni-one/formal", "experiments/xedni-two/formal"]
        self.record = {"schema": "cryptanalysis.formal-projects/v1", "source_commit": "a" * 40,
                       "toolchain": formal.TOOLCHAIN, "mathlib_revision": formal.MATHLIB,
                       "projects": {}, "files": {}, "probes": {}}
        for project in self.projects:
            directory = self.root / project
            directory.mkdir(parents=True)
            inputs = {
                "lean-toolchain": formal.TOOLCHAIN + "\n",
                "lakefile.toml": 'name="fixture"\nversion="0.1.0"\n[[require]]\nname="mathlib"\ngit="https://github.com/leanprover-community/mathlib4"\nrev="' + formal.MATHLIB + '"\n[[lean_lib]]\nname="A"\n',
                "lake-manifest.json": json.dumps({"packages": [{"name": "mathlib", "rev": formal.MATHLIB}]})}
            self.record["projects"][project] = {"inputs": {}}
            for name, text in inputs.items():
                file = directory / name
                file.write_text(text)
                self.record["projects"][project]["inputs"][str(file.relative_to(self.root))] = digest(file.read_bytes())
            self.bind(project + "/A.lean", "import B\nnamespace A\ntheorem result : True := True.intro\n#print axioms A.result\nend A\n")
            self.bind(project + "/B.lean", "import Mathlib\nnamespace B\ntheorem result : True := True.intro\n#print axioms B.result\nend B\n")
        self.write_manifest()
        self.calls = []
        self.types = []
        self.axioms = "propext"
        self.tamper = False
        self.shared = self.root / "shared"
        self.shared.mkdir()
        (self.shared / "lake-manifest.json").write_text(json.dumps({"packages": [{"name": "mathlib", "rev": formal.MATHLIB}]}))
        auditor = self.root / "tools/lean/AuditHeckeAxioms.lean"
        auditor.parent.mkdir(parents=True, exist_ok=True)
        auditor.write_bytes(b"synthetic unit auditor, never used as proof")
        self.gate = SimpleNamespace(
            check_known_label_project_inputs=lambda: None, HECKE_CI=self.shared,
            AUDITOR_SHA256=digest(auditor.read_bytes()), run=self.fake_run,
            evidence_directory=self.evidence_dir, retain_evidence=self.retain,
            compiled_identity=self.identity, check_compiled_identity=self.check_identity,
            collect_elaborated_types=self.collect_types)

    def bind(self, path, text):
        file = self.root / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(text)
        h = digest(file.read_bytes())
        self.record["files"][path] = {"mode": "100644", "sha256": h, "body_sha256": h}

    def write_manifest(self):
        file = self.root / formal.MANIFEST
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(json.dumps(self.record))

    def evidence_dir(self):
        directory = self.root / "evidence"
        directory.mkdir(exist_ok=True)
        return directory

    def retain(self, kind, files, metadata):
        directory = Path(tempfile.mkdtemp(prefix=kind, dir=self.evidence_dir()))
        for name, data in files.items():
            (directory / name).write_bytes(data)
        (directory / "record.json").write_text(json.dumps(metadata))
        return directory

    def identity(self, output):
        return {output.name: digest(output.read_bytes())}

    def check_identity(self, output, expected):
        if self.identity(output) != expected:
            raise ValueError("compiled object changed between phases")

    def collect_types(self, path, names, scratch, lean_path):
        self.types.append((path, names))

    def fake_run(self, args, **kwargs):
        if args[0] == "lake":
            return SimpleNamespace(stdout="reviewed Mathlib fixture path")
        if "--run" in args:
            name = args[-1]
            if self.tamper:
                output = Path(kwargs["env"]["LEAN_PATH"].split(os.pathsep)[0]) / (name + ".olean")
                output.write_bytes(b"changed after compilation")
            return SimpleNamespace(stdout=f"ok    {name}.result  []\naudited 1 theorems; 0 failing, 0 trusted\n")
        output = Path(args[args.index("-o") + 1])
        source = Path(args[-1])
        dependency = source.parent / "B.olean"
        inherited = dependency.read_bytes() if source.stem == "A" and dependency.exists() else b""
        output.write_bytes(b"synthetic unit object, not Lean: " + source.read_bytes() + inherited)
        self.calls.append((source.stem, source.read_bytes()))
        return SimpleNamespace(stdout=f"'{source.stem}.result' depends on axioms: [{self.axioms}]\n")

    def checked(self):
        with redirect_stdout(io.StringIO()):
            return formal.check(self.root, self.gate)

    def test_identical_source_and_dependency_context_reuses_only_this_invocations_object(self):
        checked, probes = self.checked()
        self.assertEqual(len(checked), 4)
        self.assertFalse(probes)
        self.assertEqual([name for name, _ in self.calls], ["B", "A"])
        self.assertEqual(len(self.types), 2)

    def test_same_module_name_with_a_different_dependency_never_shares_object(self):
        self.bind(self.projects[1] + "/B.lean", (self.root / self.projects[1] / "B.lean").read_text() + "-- different source version\n")
        self.write_manifest()
        self.checked()
        self.assertEqual([name for name, _ in self.calls], ["B", "A", "B", "A"])

    def test_original_internal_symlink_is_bound_and_its_change_is_refused(self):
        path = self.projects[1] + "/B.lean"
        file = self.root / path
        file.unlink()
        target = os.path.relpath(self.root / self.projects[0] / "B.lean", file.parent)
        file.symlink_to(target)
        self.record["files"][path] = {"mode": "120000", "target": target,
            "sha256": digest(target.encode()), "body_sha256": digest(file.read_bytes())}
        self.write_manifest()
        self.checked()
        file.unlink()
        file.symlink_to(self.root / self.projects[0] / "A.lean")
        with self.assertRaisesRegex(ValueError, "alias target"):
            formal.validate(self.root, self.record)

    def test_primary_proof_cannot_be_reclassified_as_an_original_censored_probe(self):
        self.record["probes"][self.projects[0] + "/A.lean"] = {}
        with self.assertRaisesRegex(ValueError, "primary proof"):
            formal.validate(self.root, self.record)

    def test_source_build_input_unknown_import_and_cycle_fail_closed(self):
        file = self.root / self.projects[0] / "A.lean"
        original = file.read_text()
        file.write_text(original + "\n")
        with self.assertRaisesRegex(ValueError, "bytes changed"):
            formal.validate(self.root, self.record)
        self.bind(self.projects[0] + "/A.lean", original.replace("import B", "import Missing"))
        with self.assertRaisesRegex(ValueError, "unbound formal module"):
            formal.validate(self.root, self.record)
        self.bind(self.projects[0] + "/A.lean", original)
        self.bind(self.projects[0] + "/B.lean", "import A\n" + (self.root / self.projects[0] / "B.lean").read_text())
        with self.assertRaisesRegex(ValueError, "cyclic"):
            formal.validate(self.root, self.record)

    def test_query_coverage_preserves_relative_and_root_name_resolution(self):
        self.assertTrue(formal.query_coverage(["A.result"], ["Outer.A.result"]))
        self.assertTrue(formal.query_coverage(["result"], ["Outer.A.result"]))
        self.assertTrue(formal.query_coverage(["_root_.A.result"], ["A.result"]))
        self.assertFalse(formal.query_coverage(["_root_.A.result"], ["Outer.A.result"]))
        self.assertFalse(formal.query_coverage(["A.result"], ["Other.result"]))
        self.assertFalse(formal.query_coverage(["A.result", "B.result"],
                                             ["Other.result", "Another.result"]))
        self.assertFalse(formal.query_coverage(["result", "A.result"],
                                             ["A.result", "A.result"]))
        self.assertTrue(formal.query_coverage(["result", "A.result"],
                                            ["A.result", "B.result"]))
        self.assertFalse(formal.query_coverage(["A.result", "B.A.result", "other"],
                                             ["B.A.result", "C.other", "D.other"]))

    def test_qualified_query_does_not_accept_another_namespace(self):
        original_run = self.gate.run

        def mismatched_query(args, **kwargs):
            result = original_run(args, **kwargs)
            if "-o" in args:
                module = Path(args[-1]).stem
                result.stdout = result.stdout.replace(f"'{module}.result'", "'Other.result'")
            return result

        self.gate.run = mismatched_query
        with self.assertRaisesRegex(ValueError, "query coverage changed"):
            self.checked()

    def test_native_foundation_and_compiled_object_changes_are_refused(self):
        self.axioms = "sorryAx"
        with self.assertRaisesRegex(ValueError, "unexpected foundation"):
            self.checked()
        self.axioms = "propext"
        self.tamper = True
        with self.assertRaisesRegex(ValueError, "compiled object changed"):
            self.checked()

    def test_nested_comments_are_not_proof_escape_tokens_but_real_tokens_are(self):
        text = "/- axiom /- sorry -/ admit -/\ntheorem t : True := True.intro\n"
        self.assertNotIn("axiom", formal.code_without_comments(text))
        self.assertIn("theorem", formal.code_without_comments(text))
        self.assertIn('axiom', formal.code_without_comments('"--" axiom X : True'))
        self.bind(self.projects[0] + "/A.lean", text + "#print axioms t\n")
        formal.validate(self.root, self.record)
        self.bind(self.projects[0] + "/A.lean", "axiom t : True\n#print axioms t\n")
        with self.assertRaisesRegex(ValueError, "proof escape"):
            formal.validate(self.root, self.record)

    def test_unreviewed_compiler_options_and_dynamic_elaboration_are_refused(self):
        path = self.projects[0] + "/lakefile.toml"
        file = self.root / path
        file.write_text(file.read_text().replace('version="0.1.0"', 'version="0.1.0"\nmoreLeanArgs=["-T0"]'))
        self.record["projects"][self.projects[0]]["inputs"][path] = digest(file.read_bytes())
        with self.assertRaisesRegex(ValueError, "compiler options"):
            formal.validate(self.root, self.record)

    def test_real_inventory_includes_both_original_censored_statuses(self):
        root = Path(__file__).resolve().parents[2]
        record = json.loads((root / formal.MANIFEST).read_text())
        graphs, order = formal.validate(root, record)
        self.assertEqual(len(graphs), 63)
        self.assertEqual(sum(map(len, order.values())), 242)
        self.assertEqual(set(record["probes"]), set(formal.KNOWN_PROBES))



class FormalGateBindingControls(unittest.TestCase):
    def test_gate_pins_checker_and_manifest_before_loading_code(self):
        spec = importlib.util.spec_from_file_location(
            "formal_gate_binding_control", Path(__file__).with_name("current-corpus-gate.py"))
        gate = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gate)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            files = ["tools/lean/check_formal_projects.py", str(formal.MANIFEST)]
            for name in files:
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((gate.ROOT / name).read_bytes())
            with patch.object(gate, "ROOT", root), patch.object(
                    gate.importlib.util, "spec_from_file_location",
                    side_effect=AssertionError("changed code must never be loaded")):
                for name, diagnostic in zip(files, ["checker changed", "bindings changed"]):
                    file = root / name
                    original = file.read_bytes()
                    file.write_bytes(original + b"\n")
                    with self.assertRaisesRegex(ValueError, diagnostic):
                        gate.check_formal_projects()
                    file.write_bytes(original)

    def test_induced_replay_sparse_inputs_cover_every_original_formal_input(self):
        root = Path(__file__).resolve().parents[2]
        record = json.loads((root / formal.MANIFEST).read_text())
        workflow = (root / ".github/workflows/chained-transfer-induced-proof.yml").read_text()
        selected = workflow.split("sparse-checkout: |", 1)[1].split("- id: producer_pin", 1)[0]
        paths = set(line.strip() for line in selected.splitlines())
        self.assertTrue(set(record["projects"]) <= paths)



    def test_induced_replay_sparse_inputs_cover_all_registered_proofs_and_build_inputs(self):
        root = Path(__file__).resolve().parents[2]
        record = json.loads((root / "tools/lean/registered-mathlib-sources-20261117.json").read_text())
        workflow = (root / ".github/workflows/chained-transfer-induced-proof.yml").read_text()
        selected = workflow.split("sparse-checkout: |", 1)[1].split("- id: producer_pin", 1)[0]
        paths = {line.strip() for line in selected.splitlines() if line.strip()}
        required = set(record["sources"])
        required.update(path for row in record["sources"].values() for path in row["project_inputs"])
        missing = {path for path in required
                   if not any(path == prefix or path.startswith(prefix + "/") for prefix in paths)}
        self.assertEqual(missing, set(), "registered controls need their exact original sparse inputs")


if __name__ == "__main__":
    unittest.main()
