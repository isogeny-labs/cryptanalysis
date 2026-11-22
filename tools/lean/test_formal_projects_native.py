#!/usr/bin/env python3
"""Actual pinned-Lean cache regressions using disposable known-answer sources.

Run explicitly after the reviewed Mathlib runtime is available. This does not
admit the fixtures as mathematical evidence or replace the full corpus replay.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

if __package__:
    from . import test_formal_projects as fixture_module
else:
    import test_formal_projects as fixture_module

formal = fixture_module.formal


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_gate():
    source = Path(__file__).with_name("current-corpus-gate.py")
    spec = importlib.util.spec_from_file_location("native_control_gate", source)
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    assert digest(Path(formal.__file__)) == gate.FORMAL_CHECKER_SHA256
    gate.check_known_label_project_inputs()
    return gate


def native_case(gate, output, *, valid):
    """Use the unit fixture factory for inputs, and actual native gate functions."""
    fixture = fixture_module.FormalProjectControls()
    fixture.setUp()
    evidence = output / ("valid-change" if valid else "invalid-change")
    assert not evidence.exists(), "control evidence cannot be overwritten"
    try:
        auditor = fixture.root / "tools/lean/AuditHeckeAxioms.lean"
        auditor.write_bytes((gate.ROOT / "tools/lean/AuditHeckeAxioms.lean").read_bytes())
        for index, project in enumerate(fixture.projects):
            del fixture.record["files"][project + "/A.lean"]
            (fixture.root / project / "A.lean").unlink()
            value = 1 if valid or index == 0 else 2
            fixture.bind(project + "/B.lean", "namespace B\n"
                         f"def n : Nat := {value}\n"
                         f"theorem result : n = {value} := rfl\n"
                         "#print axioms B.result\nend B\n" +
                         ("-- distinct dependency source\n" if index else ""))
            fixture.bind(project + "/Z.lean", "import\n B\nnamespace Z\n"
                         "theorem result : B.n = 1 := rfl\n"
                         "#print axioms Z.result\nend Z\n")
        fixture.write_manifest()
        with patch.dict(os.environ, LEAN_CORPUS_EVIDENCE_DIR=str(evidence)):
            try:
                checked, probes = formal.check(fixture.root, SimpleNamespace(**vars(gate)))
            except ValueError:
                if valid:
                    raise
                failures = []
                for record in evidence.glob("command-*/record.json"):
                    metadata = json.loads(record.read_text())
                    if metadata["returncode"] != 1:
                        continue
                    assert "-o" in metadata["argv"] and metadata["argv"][-1].endswith("/Z.lean")
                    raw = (record.parent / "stdout.bin").read_bytes()
                    assert hashlib.sha256(raw).hexdigest() == metadata["files"]["stdout.bin"]
                    assert b"Type mismatch" in raw or b"Not a definitional equality" in raw
                    failures.append(str(record.relative_to(output)))
                assert len(failures) == 1, "refusal must be the actual invalid-proof compilation"
                assert not list(evidence.glob("formal-project-receipt-*"))
                result = {"case": "invalid dependency change", "refused": True,
                          "native_failure_records": failures}
            else:
                assert valid, "stale proof object was admitted after its dependency changed"
                receipts = list(evidence.glob("formal-project-receipt-*/record.json"))
                assert len(receipts) == 1 and len(checked) == 4 and not probes
                receipt = json.loads(receipts[0].read_text())
                assert receipt["fresh_native_module_contexts"] == 4
                assert not any(row["reused_exact_object_built_and_audited_in_this_invocation"]
                               for row in receipt["modules"])
                result = {"case": "valid dependency change", "checked_paths": 4,
                          "fresh_native_contexts": 4,
                          "receipt": str(receipts[0].relative_to(output))}
        assert not fixture.calls and not fixture.types, "mock native functions must never run"
        return result
    finally:
        fixture.doCleanups()


def main():
    if not __debug__:
        raise RuntimeError("Native regression controls require enabled assertions")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    args = parser.parse_args()
    output = args.evidence_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    assert not (output / "controls.json").exists(), "control report cannot be overwritten"
    gate = load_gate()
    with patch.dict(os.environ, LEAN_CORPUS_EVIDENCE_DIR=str(output / "runtime")):
        version = gate.run(["lean", "--version"], cwd=gate.HECKE_CI).stdout.strip()
    assert "version " + formal.TOOLCHAIN.split(":v", 1)[1] in version
    cases = [native_case(gate, output, valid=False), native_case(gate, output, valid=True)]
    report = {"schema": "cryptanalysis.native-import-cache-controls/v1",
              "scope": "Known-answer software controls; no fixture theorem standing",
              "lean_version": version, "checker_sha256": digest(Path(formal.__file__)),
              "driver_sha256": digest(Path(__file__)), "cases": cases}
    (output / "controls.json").write_text(json.dumps(report, indent=2) + "\n")
    print("NATIVE_IMPORT_CACHE_CONTROLS " + json.dumps(report), flush=True)


if __name__ == "__main__":
    main()
