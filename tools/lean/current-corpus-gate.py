#!/usr/bin/env python3
"""Bind the current Lean corpus to archived native builds and fresh delta builds.

The October 21 corpus audit compiled 93 files. This gate accepts only unchanged
source and toolchain pins from that audit, plus three explicitly rebuilt files.
Any other source or pin change fails until native evidence is added here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / "reports/lean-evidence-audit-20261021/evidence/corpus"
INDEX = ARCHIVE / "cryptanalysis-corpus-index-20261021.json"
GLV = ROOT / "experiments/glv-table-rule-confirm-20261022"
ORBIT = ROOT / "experiments/orbit-quotient-summation/lean"
DELTA = {
    "experiments/orbit-quotient-summation/lean/AxiomAudit.lean": "a9dd5996abaa753224d6855d5490a58679c5eb90aa1d9661fdab2dbacbad1374",
    "experiments/orbit-quotient-summation/lean/OrbitPairIndex.lean": "32807cd33bdbed15ac178d40eb18b9d268b11d7db514b196ae515d4caba7acd7",
    "experiments/glv-table-rule-confirm-20261022/TableBudget.lean": "823903d27e906feccfe40f29df7feb7a23669b0c96d0bdc1f79ff0e3bddf93b4",
}
DIRECT_LOGS = {
    "orbit-audit.log": "cryptanalysis-orbit-audit-20261021.log",
    "orbit-build.log": "cryptanalysis-orbit-build-20261021.log",
    "binary-build.log": "cryptanalysis-binary-genus2-build-20261021.log",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def run(args: list[str], *, cwd: Path = ROOT, env: dict | None = None,
        timeout: int = 900) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(args, cwd=cwd, env=env, text=True,
                            capture_output=True, timeout=timeout, check=False)
    require(result.returncode == 0, f"{args[0]} failed: {result.stderr[-1000:]}")
    return result


def effective_pin(path: str) -> str:
    directory = (ROOT / path).parent
    while directory != ROOT and not (directory / "lean-toolchain").is_file():
        directory = directory.parent
    pin = directory / "lean-toolchain"
    require(pin.is_file(), f"missing toolchain for {path}")
    return str(pin.relative_to(ROOT))


def check_archive(index: dict, current: dict[str, str]) -> tuple[list[str], dict]:
    require(index["schema"] == "cryptanalysis.lean_corpus_replay.v1", "archive schema changed")
    require(index["tracked_lean_files"] == index["compiled_lean_files"] == 93, "archived corpus not complete")
    require(index["uncompiled_lean_files"] == 0, "archived corpus incomplete")
    require(index["coverage_by_method"] == {
        "pinned experiment check.py": 28,
        "mixed640 Lean build and axiom printout": 17,
        "core Lean build and axiom printout": 24,
        "dependent Lean build and axiom printout": 19,
        "pinned direct or Lake build": 5,
    }, "archived proof method partition changed")
    archived = {row["source"]: row for row in index["files"]}
    require(len(archived) == 93, "duplicate archived source")
    added = set(DELTA) - set(archived)
    require(len(added) == 1 and len(current) == 94 and
            set(current) == set(archived) | added, "current Lean corpus changed")
    reused = sorted(set(archived) - set(DELTA))
    require(len(reused) == 91, "unexpected archive reuse count")
    for path in reused:
        row = archived[path]
        require(current[path] == row["sha256"], f"Lean source changed without native replay: {path}")
        pin = effective_pin(path)
        historical = run(["git", "show", f"{index['source_commit']}:{pin}"]).stdout.encode()
        require((ROOT / pin).read_bytes() == historical, f"effective toolchain changed: {path}")
    for path, expected in DELTA.items():
        require(current.get(path) == expected, f"delta Lean source changed: {path}")

    summaries = {}
    for name, expected in (("mixed640", 17), ("core", 24), ("dependent", 19)):
        file = ARCHIVE / name / "summary.json"
        rows = json.loads(file.read_text())
        require(len(rows) == expected, f"{name} archive row count changed")
        require(all(r["status"] == "PASS" and not r["bad_axioms"] and
                    r["expected_prints"] == r["actual_prints"] for r in rows),
                f"{name} archive has failed or incomplete row")
        for row in rows:
            require(row["sha256"] == archived[row["source"]]["sha256"],
                    f"{name} archive source mismatch")
        summaries[name] = {"rows": expected, "sha256": digest(file)}
    checks_file = ARCHIVE / "experiment-checks.json"
    checks = json.loads(checks_file.read_text())
    require(checks["checks_passed"] == 13 and checks["checks_failed"] == 0 and
            len(checks["checks"]) == 13 and all(c["exit"] == 0 for c in checks["checks"]) and
            checks["unique_lean_sources_covered"] == 28,
            "archived experiment proof checks changed")
    for row in index["files"]:
        if row["method"] == "pinned direct or Lake build":
            for name in row["evidence"].split(" and "):
                path = ARCHIVE / DIRECT_LOGS.get(name, name)
                require(path.is_file() and path.stat().st_size > 0,
                        f"missing direct proof log: {name}")
    return reused, {"index_sha256": digest(INDEX), "group_summaries": summaries,
                    "experiment_checks_sha256": digest(checks_file)}


def check_delta() -> dict:
    require((ROOT / "lean-toolchain").read_text().strip() == "leanprover/lean4:v4.34.1",
            "root Lean toolchain changed")
    require((ORBIT / "lean-toolchain").read_text().strip() == "leanprover/lean4:v4.34.1",
            "Orbit Lean toolchain changed")
    orbit = run([str(ORBIT / "check.sh")], timeout=900)
    expected_orbit = [
        "'OrbitQuotient.mem_pairTotals_iff' depends on axioms: [propext, Quot.sound]",
        "'OrbitQuotient.triple_matches_iff_pair_lookup' depends on axioms: [propext, Quot.sound]",
        "'OrbitQuotient.quadruple_matches_iff_two_pair_lookup' depends on axioms: [propext, Quot.sound]",
    ]
    require(orbit.stdout.splitlines()[-3:] == expected_orbit, "Orbit axiom output changed")
    require(not orbit.stderr.strip(), "Orbit build wrote stderr")
    for mode, archived in (([], "lean-source-binding.json"),
                           (["--live"], "live-source-binding.json")):
        check = run(["python3", "check_lean_source_binding.py", *mode], cwd=GLV)
        require(check.stdout.encode() == (GLV / archived).read_bytes(),
                f"GLV source binding changed: {archived}")
    lean_receipt = json.loads((GLV / "lean-receipt.json").read_text())
    require(digest(GLV / "TableBudget.lean") == lean_receipt["source_sha256"],
            "GLV theorem source differs from native receipt")
    env = dict(os.environ, ELAN_TOOLCHAIN="leanprover/lean4:v4.34.1")
    glv = run(["lean", "TableBudget.lean"], cwd=GLV, env=env, timeout=900)
    require(glv.stdout == lean_receipt["stdout"] and
            glv.stderr == lean_receipt["stderr"] and lean_receipt["exit_code"] == 0,
            "GLV native output differs from receipt")
    printed = re.findall(r"^'([^']+)' depends on axioms: \[([^]]*)\]$",
                         glv.stdout, re.MULTILINE)
    declared = {"GlvTableBudget." + name for name in
                re.findall(r"^theorem\s+(\w+)", (GLV / "TableBudget.lean").read_text(), re.MULTILINE)}
    require(len(printed) == len(declared) == 8 and
            {name for name, _ in printed} == declared and
            all({axiom.strip() for axiom in names.split(",") if axiom.strip()}
                <= {"propext", "Quot.sound"} for _, names in printed),
            "GLV theorem coverage or axiom set changed")
    return {"orbit_axiom_stdout_sha256": hashlib.sha256(orbit.stdout.encode()).hexdigest(),
            "glv_axiom_stdout_sha256": hashlib.sha256(glv.stdout.encode()).hexdigest(),
            "glv_receipt_sha256": digest(GLV / "lean-receipt.json")}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-receipt", type=Path)
    args = parser.parse_args()
    index = json.loads(INDEX.read_text())
    paths = [path for path in run(["git", "ls-files", "--", "*.lean"]).stdout.splitlines()
             if not path.startswith("tools/lean/")]
    current = {path: digest(ROOT / path) for path in paths}
    require(len(current) == len(paths), "duplicate tracked Lean path")
    reused, archive = check_archive(index, current)
    delta = check_delta()
    output = {"schema": "cryptanalysis.current_lean_corpus_bridge.v1",
              "archive_source_commit": index["source_commit"],
              "current_lean_files": len(current), "archived_byte_identical_files": len(reused),
              "fresh_native_files": sorted(DELTA), "archive_evidence": archive,
              "fresh_native_source_sha256": {path: current[path] for path in sorted(DELTA)},
              "fresh_native_evidence": delta,
              "scope": "source-bound historical and fresh Lean builds with recorded allowed axiom outputs; exhaustive theorem audit, semantic fidelity and historical execution remain open"}
    encoded = (json.dumps(output, indent=2, sort_keys=True) + "\n").encode()
    if args.check_receipt:
        require(args.check_receipt.read_bytes() == encoded, "committed corpus receipt differs")
    else:
        print(encoded.decode(), end="")


if __name__ == "__main__":
    main()
