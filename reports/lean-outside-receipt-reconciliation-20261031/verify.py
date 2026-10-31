#!/usr/bin/env python3
"""Recompute the frozen 87-path partition from a manifest and hosted job export.

This checks consistency and scope, not GitHub job authenticity or theorem meaning.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--job", type=Path, required=True)
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--gate", type=Path, required=True)
    parser.add_argument("--reconciliation", type=Path, default=Path(__file__).with_name("reconciliation.json"))
    args = parser.parse_args()
    report = json.loads(args.reconciliation.read_text())
    manifest = json.loads(args.manifest.read_text())
    job = json.loads(args.job.read_text())
    lines = args.log.read_text().splitlines()
    body = [line.split("Z ", 1)[-1] for line in lines]

    require(report["schema"] == "lean.outside-receipt-reconciliation/v2", "wrong report schema")
    source = report["source_inventory"]
    require(sha256(args.manifest) == source["manifest_sha256"], "manifest hash changed")
    expected = manifest["cryptanalysis_corpus_boundary"]["outside_this_receipt_paths"]
    require(len(expected) == len(set(expected)) == 87, "frozen path inventory changed")
    paths = [row["path"] for row in report["rows"]]
    require(len(paths) == len(set(paths)) == 87 and set(paths) == set(expected), "report path inventory differs")
    require(job["head_sha"] == source["cryptanalysis_commit"] and job["status"] == "completed"
            and job["conclusion"] == "success" and job["id"] == 124428817573,
            "job is not the successful frozen-commit job")
    evidence = report["evidence"]
    require(sha256(args.log) == evidence["job_log_sha256"], "job log hash changed")
    require(sha256(args.gate) == evidence["gate_sha256"], "gate hash changed")

    native = {}
    generic_build = {}
    generic_axioms = {}
    fixtures = {}
    for number, line in enumerate(body, 1):
        match = re.search(r"native audit: ([^:\n]+\.lean): (\d+) declarations, (\d+) theorems", line)
        if match:
            recent = "\n".join(body[max(0, number - 6):number - 1])
            audits = re.findall(r"audited (\d+) theorems; (\d+) failing, (\d+) trusted", recent)
            require(audits and audits[-1] == (match.group(3), "0", "0"),
                    f"native audit count/failures differ: {match.group(1)}")
            native[match.group(1)] = (number, int(match.group(2)), int(match.group(3)))
        match = re.search(r"compiling current proof source: ([^\s]+\.lean)", line)
        if match:
            generic_build[match.group(1)] = number
        match = re.search(r"verified native axiom outputs: ([^\s]+\.lean)", line)
        if match:
            generic_axioms[match.group(1)] = number
        match = re.search(r"ok\s+(pass|fail)\s+(PASS|FAIL_audit|FAIL_build)\s+"
                          r"(\d+) thm\s+(\d+) trusted\s+"
                          r"(tools/lean/selftest/(?:pass|fail)/[^\s]+\.lean)", line)
        if match:
            fixtures[match.group(5)] = (number, match.group(1), match.group(2),
                                        int(match.group(3)), int(match.group(4)))

    require(len(native) == 39, "dedicated audit count changed")
    require(len(generic_build) == 37 and generic_build.keys() == generic_axioms.keys(),
            "generic build/axiom-output pairing changed")
    require(len(fixtures) == 7, "fixture outcome count changed")
    require(any("native added theorem modules checked: 77" in line for line in body),
            "aggregate native module count changed")
    hasse = "bindings/rust/curve-audit/formal/HasseSquareBounds.lean"
    implementations = {"tools/lean/AuditAxioms.lean", "tools/lean/AuditHeckeAxioms.lean",
                       "tools/lean/transfer-audit/TransferAudit.lean"}
    require(set(expected) == set(native) | set(generic_build) | {hasse} | set(fixtures)
            | implementations, "job/source-role partition differs")
    for row in report["rows"]:
        path = row["path"]
        if path in native:
            require(row["machine_status"] == "passed_exhaustive_module_audit"
                    and row["machine_details"] == dict(zip(("line", "declarations", "theorems"), native[path])),
                    f"dedicated audit row differs: {path}")
        elif path in generic_build:
            require(row["machine_status"] == "passed_native_build_and_declared_axiom_outputs"
                    and row["machine_details"] == {"compile_log_line": generic_build[path],
                                                   "axiom_output_log_line": generic_axioms[path]},
                    f"generic row differs: {path}")
        elif path in fixtures:
            number, expected_class, outcome, theorems, trusted = fixtures[path]
            require(row["machine_status"] == "expected_fixture_outcome_observed"
                    and row["machine_details"] == {"line": number, "expected_class": expected_class,
                                                   "observed_outcome": outcome, "theorems": theorems,
                                                   "trusted": trusted},
                    f"fixture row differs: {path}")
        elif path == hasse:
            require(row["machine_status"] == "passed_separate_hasse_gate", "Hasse row differs")
        else:
            require(path in implementations and row["role"] == "verifier_implementation",
                    f"implementation row differs: {path}")
    require(report["counts"] == {"outside_receipt": 87,
                                 "exhaustive_native_module_audits": 39,
                                 "generic_native_builds_with_declared_axiom_outputs": 37,
                                 "separate_hasse_source": 1,
                                 "verifier_self_test_fixtures": 7,
                                 "verifier_implementations": 3}, "reported counts differ")
    print("PASS: 87 paths partitioned; 39 exhaustive audits, 37 generic builds, 1 Hasse, "
          "7 fixtures, 3 verifier implementations")


if __name__ == "__main__":
    main()
