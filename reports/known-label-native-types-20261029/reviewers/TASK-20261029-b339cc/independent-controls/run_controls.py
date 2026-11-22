"""Bounded Python controls only. Never executes Lean, Lake, network or builds."""
import contextlib
import hashlib
import importlib.util
import io
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = pathlib.Path(__file__).resolve().parent
SNAPSHOT = HERE / "snapshot"
TEMP = HERE / "temporary"
TEMP.mkdir(exist_ok=True)
tempfile.tempdir = str(TEMP)
sys.dont_write_bytecode = True


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate = load("independent_gate", SNAPSHOT / "tools/lean/current-corpus-gate.py")
NAMES = sorted(gate.KNOWN_LABEL_THEOREMS)
PRINTED = "".join(f"'{n}' depends on axioms: [propext, Quot.sound]\n" for n in NAMES)
AUDITED = "".join(f"ok    {n}  [propext, Quot.sound]\n" for n in NAMES)
AUDITED += "audited 4 theorems; 0 failing, 0 trusted\n"
TYPES = "".join(f"@{n}.{{u_1}} : Type u_1\n" for n in NAMES)
results = []


def control(case, target_phase=None, action=None, fail=False, output=None):
    with tempfile.TemporaryDirectory(prefix="fixture-") as name:
        root = pathlib.Path(name)
        project = root / gate.HECKE_CI.relative_to(gate.ROOT)
        project.mkdir(parents=True)
        for filename in gate.KNOWN_LABEL_PROJECT_INPUTS:
            shutil.copyfile(gate.HECKE_CI / filename, project / filename)
        source = root / gate.KNOWN_LABEL_SOURCE
        source.parent.mkdir(parents=True)
        shutil.copyfile(gate.ROOT / gate.KNOWN_LABEL_SOURCE, source)
        audit_source = root / "tools/lean/AuditHeckeAxioms.lean"
        audit_source.parent.mkdir(parents=True)
        shutil.copyfile(gate.ROOT / "tools/lean/AuditHeckeAxioms.lean", audit_source)
        state = {"calls": [], "events": []}

        def synthetic_command(args, **kwargs):
            # Mock below gate.run so the real return-code check is exercised.
            phase = "compile" if args[0] == "lake" else "audit" if args[1] == "--run" else "types"
            state["calls"].append({"phase": phase, "args": args,
                                   "cwd": str(kwargs.get("cwd")),
                                   "lean_path": (kwargs.get("env") or {}).get("LEAN_PATH")})
            if phase == "compile":
                state["object"] = pathlib.Path(args[args.index("-o") + 1])
                state["object"].write_bytes(b"SYNTHETIC-OBJECT-NOT-LEAN")
            if phase == target_phase and action:
                action(root, source, project, audit_source, state, args)
            stdout = PRINTED if phase == "compile" else AUDITED if phase == "audit" else TYPES
            if phase == target_phase and output is not None:
                stdout = output
            stderr = ""
            rc = 0
            if phase == target_phase and fail:
                rc = 7
                stdout += "UNIQUE-NATIVE-STDOUT-DIAGNOSTIC\n"
                stderr = "UNIQUE-STDERR-PREFIX\n" + "z" * 1200 + "\nSTDERR-SUFFIX\n"
            return subprocess.CompletedProcess(args, rc, stdout, stderr)

        captured = io.StringIO()
        with patch.object(gate, "ROOT", root), patch.object(gate, "HECKE_CI", project), \
             patch.object(gate.subprocess, "run", side_effect=synthetic_command), \
             contextlib.redirect_stdout(captured):
            try:
                value = gate.check_known_label_algebra("synthetic-dependency-path")
                accepted, error = True, None
            except Exception as exc:
                value, accepted, error = None, False, f"{type(exc).__name__}: {exc}"
        row = {"case": case, "accepted": accepted, "returned": value, "error": error,
               "stdout": captured.getvalue(), "calls": state["calls"], "events": state["events"],
               "source_sha256_after": hashlib.sha256(source.read_bytes()).hexdigest(),
               "audit_source_sha256_after": hashlib.sha256(audit_source.read_bytes()).hexdigest(),
               "synthetic_only": True}
        results.append(row)
        return row


positive = control("positive_synthetic_full_pipeline")
assert positive["accepted"] and len(positive["calls"]) == 3
assert "import «docs».«known-label-next-leads-20261028».«Algebra»\n" in positive["stdout"]
assert positive["calls"][1]["lean_path"] == positive["calls"][2]["lean_path"]

type_lines = TYPES.splitlines(keepends=True)
for case, output in [
    ("missing_type", "".join(type_lines[:-1])),
    ("duplicate_type", "".join(type_lines[:-1] + [type_lines[0]])),
    ("wrong_namespace_type", TYPES.replace("KnownLabelLeads.", "Other.")),
    ("empty_types", ""),
    ("extra_type", TYPES + "@Other.extra : True\n"),
]:
    row = control(case, "types", output=output)
    assert not row["accepted"]
    assert "BEGIN NATIVE ELABORATED TYPES" not in row["stdout"]

for phase in ["compile", "audit", "types"]:
    row = control(f"nonzero_{phase}", phase, fail=True)
    assert not row["accepted"] and len(row["calls"]) == ["compile", "audit", "types"].index(phase) + 1
    visible = row["stdout"] + row["error"]
    assert "UNIQUE-NATIVE-STDOUT-DIAGNOSTIC" not in visible
    assert "UNIQUE-STDERR-PREFIX" not in visible
    assert "STDERR-SUFFIX" in visible


def change_source(root, source, project, audit_source, state, args):
    source.write_bytes(source.read_bytes() + b"\n-- PERSISTENT SYNTHETIC MUTATION\n")


def change_project(root, source, project, audit_source, state, args):
    file = project / "lakefile.toml"
    file.write_bytes(file.read_bytes() + b"\n# PERSISTENT SYNTHETIC MUTATION\n")


def change_wrapper(root, source, project, audit_source, state, args):
    pathlib.Path(args[-1]).write_text("#check True\n")


for phase in ["compile", "audit", "types"]:
    assert not control(f"persistent_source_mutation_{phase}", phase, change_source)["accepted"]
    assert not control(f"persistent_project_mutation_{phase}", phase, change_project)["accepted"]
assert not control("persistent_type_wrapper_mutation", "types", change_wrapper)["accepted"]


def change_auditor(root, source, project, audit_source, state, args):
    audit_source.write_text("-- altered verifier source in an isolated test fixture\n")
    state["events"].append("auditor source was persistently replaced after compile")


def change_object(root, source, project, audit_source, state, args):
    state["object"].write_bytes(b"REPLACED-SYNTHETIC-OBJECT-NOT-LEAN")
    state["events"].append("compiled placeholder object was persistently replaced before type collection")


def remove_object(root, source, project, audit_source, state, args):
    state["object"].unlink()
    state["events"].append("compiled placeholder object was removed before type collection")


def transient_mutations(root, source, project, audit_source, state, args):
    for file in [source, project / "lakefile.toml", pathlib.Path(args[-1])]:
        original = file.read_bytes()
        file.write_bytes(original + b"\n-- transient synthetic mutation\n")
        file.write_bytes(original)
    state["events"].append("source, project and wrapper were changed then restored during synthetic command")


assert control("persistent_auditor_mutation_unchecked", "compile", change_auditor)["accepted"]
assert control("persistent_object_mutation_unchecked", "audit", change_object)["accepted"]
assert control("missing_object_unchecked", "audit", remove_object)["accepted"]
assert control("transient_mutations_undetected", "types", transient_mutations)["accepted"]

# Real bounded Python child process verifies generic runner retention independently
# of all synthetic Lean outputs. No native Lean executable is used.
captured = io.StringIO()
try:
    with contextlib.redirect_stdout(captured):
        gate.run([sys.executable, "-c", "import sys; print('REAL-CHILD-STDOUT'); sys.stderr.write('REAL-PREFIX'+('x'*1200)+'REAL-SUFFIX'); sys.exit(7)"], cwd=HERE, timeout=5)
except ValueError as exc:
    error = str(exc)
else:
    raise AssertionError("failed child was admitted")
assert "REAL-CHILD-STDOUT" not in error + captured.getvalue()
assert "REAL-PREFIX" not in error + captured.getvalue()
assert "REAL-SUFFIX" in error
results.append({"case": "real_python_child_failure_diagnostics", "accepted": False,
                "error": error, "stdout": captured.getvalue(), "native_lean": False})

producer = load("producer_controls", SNAPSHOT / "tools/lean/test_current_corpus_gate.py")
suite = unittest.TestSuite()
for cls in [producer.KnownLabelRegistrationControls, producer.ElaboratedTypeControls]:
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(cls))
with (HERE / "producer-selected-tests.txt").open("w") as stream:
    test_result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
assert test_result.wasSuccessful()

result = {"classification": "Python/mock software controls; no native proof evidence",
          "independent_cases": len(results), "producer_selected_tests": test_result.testsRun,
          "producer_skipped_class": "QuarticRegistrationControls requires an input outside permitted review scope",
          "python": sys.version, "results": results}
(HERE / "results.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({"independent_cases": len(results), "producer_selected_tests": test_result.testsRun,
                  "checks": "passed", "native_lean_executed": False}, indent=2))
