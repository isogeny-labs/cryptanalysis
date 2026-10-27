#!/usr/bin/env python3
"""Bind the frozen Lean corpus and natively check admitted theorem modules.

The October 21 corpus audit compiled 93 files. Its 96-file bridge remains
byte-for-byte source-bound to the committed receipt; six explicitly rebuilt
files and the PQC assay are separately pinned. New Hecke modules use the
pinned Mathlib toolchain; the reviewed Hasse-square module uses its own pinned
toolchain. Other source or pin changes still fail until native evidence is
added here.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / "reports/lean-evidence-audit-20261021/evidence/corpus"
INDEX = ARCHIVE / "cryptanalysis-corpus-index-20261021.json"
GLV = ROOT / "experiments/glv-table-rule-confirm-20261022"
ORBIT = ROOT / "experiments/orbit-quotient-summation/lean"
CUBIC = ROOT / "experiments/ghs-sweeper/formal"
CM = ROOT / "experiments/ghs-sweeper/cm-formal"
HECKE_CI = ROOT / "experiments/hecke-432-formal-ci-20261025"
HASSE_FORMAL = ROOT / "bindings/rust/curve-audit/formal"
HASSE_SOURCE = "bindings/rust/curve-audit/formal/HasseSquareBounds.lean"
HASSE_SHA256 = "26e3e7bbf28aad0f60f72137fca027427b435f05bcef9f5de5881d7979307c42"
PQC = ROOT / "verification/pqc-assay/lean"
PQC_SOURCE = "verification/pqc-assay/lean/Modarith.lean"
HISTORICAL_GLV_COMMIT = "d488af97a0cae6d7e96686da17aeff2f0db5f29f"
HISTORICAL_GLV_SHA256 = "4ab176d18c6b8b562fb48aba23e67127a61d59e4450a93d781902c47579fac20"
HISTORICAL_GLV_RECEIPT = ROOT / "reports/ghs-pr-1104-main-integration-20261025/prior-live-source-binding.json"
HISTORICAL_GLV_RECEIPT_SHA256 = "bb0abf96c3f9d0d655b88cafafe0c5f50d90a86c9948278381e727ed193ab534"
LIVE_GLV_COMMIT = "8bf648dcbefe7b8131e5fb26909c77e68778332a"
LIVE_GLV_SHA256 = "60796724ef7d7c5b3b7dfd89c29db85d5e188deb247b5d9d0bd69b84551afe20"
DELTA = {
    "experiments/ghs-sweeper/cm-formal/CubicCM53.lean": "472ed227d624bdeaf14504da82751843dc941e71e74aa4b6fffdddf17562387f",
    "experiments/ghs-sweeper/formal/CubicGluing.lean": "5c62ca3cd27f891ef5930f2fbf0488a23e9e9217ea5a32771744be2ca2f62557",
    "experiments/orbit-quotient-summation/lean/AxiomAudit.lean": "a9dd5996abaa753224d6855d5490a58679c5eb90aa1d9661fdab2dbacbad1374",
    "experiments/orbit-quotient-summation/lean/OrbitPairIndex.lean": "32807cd33bdbed15ac178d40eb18b9d268b11d7db514b196ae515d4caba7acd7",
    "experiments/glv-table-rule-confirm-20261022/TableBudget.lean": "823903d27e906feccfe40f29df7feb7a23669b0c96d0bdc1f79ff0e3bddf93b4",
    PQC_SOURCE: "83c8a9ec8cd48f0c49d686ad551977d170130b06b726cf0bd002227a89036170",
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
    require(len(added) == 4 and len(current) == 97 and
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


def check_pqc() -> dict:
    pin = PQC / "lean-toolchain"
    require(effective_pin(PQC_SOURCE) == str(pin.relative_to(ROOT)) and
            pin.read_text().strip() == "leanprover/lean4:v4.34.1",
            "PQC assay Lean toolchain changed")
    with tempfile.TemporaryDirectory(prefix="pqc-lean-gate-") as scratch:
        out = Path(scratch) / "receipt"
        gate = run([str(ROOT / "tools/lean/proof-gate.sh"), "--out", str(out),
                    PQC_SOURCE], timeout=900)
        require(gate.stdout.startswith("PASS "), "PQC standalone gate did not pass")
        slug = "verification_pqc-assay_lean_Modarith_lean"
        receipt = out / slug
        require((receipt / "status").read_text() == "PASS\n", "PQC gate status changed")
        audit = (receipt / "audit.log").read_text()
        checked = [line for line in audit.splitlines()
                   if line.startswith("ok    ") or line.startswith("audited ")]
        expected = [
            "ok    PqcAssay.cAdd64_correct  [propext, Quot.sound]",
            "ok    PqcAssay.cSub64_correct  [propext, Quot.sound]",
            "audited 2 theorems in [Modarith]; 0 failing, 0 trusted (native_decide)",
        ]
        require(checked == expected, "PQC theorem coverage or axiom set changed")
    return {"pqc_axiom_stdout_sha256": hashlib.sha256(
                ("\n".join(expected) + "\n").encode()).hexdigest(),
            "pqc_toolchain_sha256": digest(pin)}


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
    # `check.sh` also prints Lake's build progress, which differs between a
    # cached local build and a fresh CI runner. The three checked axiom lines
    # are the source-bound proof evidence; bind only those stable lines.
    orbit_axioms = "\n".join(expected_orbit) + "\n"
    check = run(["python3", "check_lean_source_binding.py"], cwd=GLV)
    require(check.stdout.encode() == (GLV / "lean-source-binding.json").read_bytes(),
            "GLV historical source binding changed")
    # Main changed unrelated C code after the old live receipt. Preserve that
    # receipt, replay its exact selector/guards and both negative controls on
    # its pinned source, then bind today's live file separately. No historical
    # source, receipt, or mathematical selector assertion is overwritten.
    spec = importlib.util.spec_from_file_location("glv_binding", GLV / "check_lean_source_binding.py")
    require(spec is not None and spec.loader is not None, "GLV validator unavailable")
    binding = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(binding)

    def selector_negatives(data: bytes, expected_hash: str) -> None:
        binding.require_selector(data, expected_hash, 12)
        for changed in (
            data.replace(b"(12u * (uint64_t)lg)", b"(48u * (uint64_t)lg)"),
            data.replace(b"rr * 2 <= 32", b"rr * 2 <= 64"),
        ):
            try:
                binding.require_selector(changed, hashlib.sha256(changed).hexdigest(), 12)
            except ValueError:
                continue
            raise ValueError("GLV selector negative control admitted")

    require(digest(HISTORICAL_GLV_RECEIPT) == HISTORICAL_GLV_RECEIPT_SHA256,
            "archived GLV live receipt bytes changed")
    historical_live = json.loads(HISTORICAL_GLV_RECEIPT.read_text())
    expected_historical = {
        "schema": "glv-table-live-source-binding-v1",
        "source_commit": HISTORICAL_GLV_COMMIT,
        "source_sha256": HISTORICAL_GLV_SHA256,
        "historical_source_commit": binding.CURRENT_SOURCE_COMMIT,
        "historical_source_sha256": binding.CURRENT_SHA256,
        "divisor": 12, "loop_start": 8, "loop_cap": 32,
        "negative_controls_rejected": 2, "result": "pass",
    }
    require(historical_live == expected_historical, "historical GLV live receipt changed")
    historical_bytes = run(["git", "show", f"{HISTORICAL_GLV_COMMIT}:src/curve.c"]).stdout.encode()
    selector_negatives(historical_bytes, HISTORICAL_GLV_SHA256)
    current_live = run(["python3", "check_lean_source_binding.py", "--live"], cwd=GLV)
    require(current_live.stdout.encode() == (GLV / "live-source-binding.json").read_bytes(),
            "current main GLV live receipt changed")
    live_bytes = (ROOT / "src/curve.c").read_bytes()
    pinned_live = run(["git", "show", f"{LIVE_GLV_COMMIT}:src/curve.c"]).stdout.encode()
    require(live_bytes == pinned_live, "live GLV source differs from the new pin")
    selector_negatives(live_bytes, LIVE_GLV_SHA256)
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
    require((CUBIC / "lean-toolchain").read_text().strip() == "leanprover/lean4:v4.34.1",
            "Cubic gluing Lean toolchain changed")
    require(json.loads((CUBIC / "lake-manifest.json").read_text())["packages"] == [],
            "Cubic gluing dependency set changed")
    run(["lake", "build"], cwd=CUBIC)
    cubic = run(["lake", "env", "lean", "CubicGluing.lean"], cwd=CUBIC)
    names = {"coefficient_injectivity", "frobenius_stability", "basis_isotropy",
             "coordinate_transversality", "determinant_binding"}
    expected_cubic = {
        f"'CubicGluing.{name}' depends on axioms: [propext]" for name in names}
    require(set(cubic.stdout.splitlines()) == expected_cubic and not cubic.stderr,
            "Cubic gluing theorem printout or foundations changed")
    declared_cubic = set(re.findall(r"^theorem\s+(\w+)",
                                   (CUBIC / "CubicGluing.lean").read_text(), re.MULTILINE))
    require(declared_cubic == names, "Cubic gluing declaration coverage changed")
    audit = run(["lake", "env", "lean", "--run",
                 str(ROOT / "tools/lean/AuditAxioms.lean"), "CubicGluing"], cwd=CUBIC)
    audited = [line for line in audit.stdout.splitlines()
               if line.startswith("ok    ") or line.startswith("audited ")]
    require(len(audited) == 9 and
            audited[-1] == "audited 8 theorems in [CubicGluing]; 0 failing, 0 trusted (native_decide)",
            "Cubic gluing transitive theorem audit changed")
    require((CM / "lean-toolchain").read_text().strip() == "leanprover/lean4:v4.34.1",
            "CM arithmetic Lean toolchain changed")
    require(json.loads((CM / "lake-manifest.json").read_text())["packages"] == [],
            "CM arithmetic dependency set changed")
    run(["lake", "build"], cwd=CM)
    cm = run(["lake", "env", "lean", "CubicCM53.lean"], cwd=CM)
    cm_names = {"sorted_bounds", "finite_exclusion", "no_admissible_partition", "no_cube_trace"}
    cm_expected = {
        "'CubicCM53.sorted_bounds' depends on axioms: [propext, Classical.choice, Quot.sound]",
        "'CubicCM53.no_admissible_partition' depends on axioms: [propext, Classical.choice, Quot.sound]",
        "'CubicCM53.finite_exclusion' does not depend on any axioms",
        "'CubicCM53.no_cube_trace' does not depend on any axioms",
    }
    require(set(cm.stdout.splitlines()) == cm_expected and not cm.stderr,
            "CM arithmetic theorem printout or foundations changed")
    require(set(re.findall(r"^theorem\s+(\w+)", (CM / "CubicCM53.lean").read_text(), re.MULTILINE)) == cm_names,
            "CM arithmetic theorem coverage changed")
    cm_audit = run(["lake", "env", "lean", "--run",
                    str(ROOT / "tools/lean/AuditAxioms.lean"), "CubicCM53"], cwd=CM)
    cm_audited = [line for line in cm_audit.stdout.splitlines()
                  if line.startswith("ok    ") or line.startswith("audited ")]
    require(len(cm_audited) == 6 and
            cm_audited[-1] == "audited 5 theorems in [CubicCM53]; 0 failing, 0 trusted (native_decide)",
            "CM arithmetic transitive audit changed")
    pqc = check_pqc()
    return {"orbit_axiom_stdout_sha256": hashlib.sha256(orbit_axioms.encode()).hexdigest(),
            "glv_axiom_stdout_sha256": hashlib.sha256(glv.stdout.encode()).hexdigest(),
            "glv_receipt_sha256": digest(GLV / "lean-receipt.json"),
            "glv_historical_live_source_sha256": HISTORICAL_GLV_SHA256,
            "glv_historical_live_receipt_sha256": digest(HISTORICAL_GLV_RECEIPT),
            "glv_live_binding_receipt_sha256": digest(GLV / "live-source-binding.json"),
            "glv_live_source_commit": LIVE_GLV_COMMIT,
            "glv_live_source_sha256": LIVE_GLV_SHA256,
            "cubic_axiom_stdout_sha256": hashlib.sha256(cubic.stdout.encode()).hexdigest(),
            "cubic_transitive_audit_sha256": hashlib.sha256(("\n".join(audited)+"\n").encode()).hexdigest(),
            "cm_axiom_stdout_sha256": hashlib.sha256(cm.stdout.encode()).hexdigest(),
            "cm_transitive_audit_sha256": hashlib.sha256(("\n".join(cm_audited)+"\n").encode()).hexdigest(),
            **pqc}


def check_new_hecke(paths: set[str]) -> dict[str, str]:
    """Build every added Hecke source; never admit an unbuilt corpus addition."""
    if not paths:
        return {}
    require(HECKE_CI.joinpath("lean-toolchain").read_text().strip() ==
            "leanprover/lean4:v4.35.0-rc4", "Hecke Lean toolchain changed")
    manifest = json.loads(HECKE_CI.joinpath("lake-manifest.json").read_text())
    mathlib = [p for p in manifest["packages"] if p["name"] == "mathlib"]
    require(len(mathlib) == 1 and
            mathlib[0]["rev"] == "021c46bdd042f67b538b9f9871d556a93713a9a9",
            "Hecke Mathlib revision changed")
    checked = {}
    for path in sorted(paths):
        require(path.startswith("experiments/hecke-") and "/formal/" in path and
                path.endswith(".lean"), f"unreviewed Lean corpus addition: {path}")
        pin = ROOT / effective_pin(path)
        require(pin.read_text().strip() == "leanprover/lean4:v4.35.0-rc4",
                f"Hecke theorem toolchain changed: {path}")
        source = (ROOT / path).read_text()
        require(not re.search(r"\b(?:sorry|admit|sorryAx|native_decide|axiom)\b", source),
                f"forbidden proof escape in {path}")
        declared = re.findall(r"^(?:theorem|lemma)\s+(\w+)", source, re.MULTILINE)
        requested = re.findall(r"^#print axioms\s+(\w+)", source, re.MULTILINE)
        require(declared and len(declared) == len(set(declared)) and
                set(declared) == set(requested) and len(declared) == len(requested),
                f"incomplete declaration audit in {path}")
        result = run(["lake", "env", "lean", "-R", str(ROOT), str(ROOT / path)],
                     cwd=HECKE_CI, timeout=900)
        printed = re.findall(r"^'([^']+)' depends on axioms: \[([^]]*)\]$",
                             result.stdout, re.MULTILINE)
        require(len(printed) == len(declared) and
                {name.rsplit(".", 1)[-1] for name, _ in printed} == set(declared),
                f"incomplete native axiom output for {path}")
        require(all({axiom.strip() for axiom in names.split(",") if axiom.strip()}
                    <= {"propext", "Classical.choice", "Quot.sound"}
                    for _, names in printed),
                f"unexpected foundation in {path}")
        checked[path] = digest(ROOT / path)
    return checked


def check_new_hasse() -> str:
    """Rebuild the source-bound Nat bridge and audit its transitive axioms."""
    require((HASSE_FORMAL / "lean-toolchain").read_text().strip() ==
            "leanprover/lean4:v4.34.1", "Hasse theorem toolchain changed")
    source = (ROOT / HASSE_SOURCE).read_text()
    require(digest(ROOT / HASSE_SOURCE) == HASSE_SHA256,
            "Hasse theorem source changed without review")
    require(not re.search(r"\b(?:sorry|admit|sorryAx|native_decide|axiom)\b", source),
            "forbidden proof escape in Hasse theorem source")
    declared = set(re.findall(r"^theorem\s+(\w+)", source, re.MULTILINE))
    requested = re.findall(r"^#print axioms\s+(\w+)", source, re.MULTILINE)
    require(declared == {
        "squared_deviations_have_short_sum",
        "unique_multiple_from_squared_center_bounds",
        "unsignedDelta_center_bounds",
        "unique_multiple_from_hasse_squared_checks",
    } and len(requested) == len(declared) and set(requested) == declared,
            "Hasse theorem declaration or axiom printout coverage changed")
    with tempfile.TemporaryDirectory(prefix="hasse-corpus-") as temporary:
        env = {**os.environ, "LEAN_PATH": temporary}
        run(["lean", "-o", str(Path(temporary) / "HasseUnique.olean"),
             "HasseUnique.lean"], cwd=HASSE_FORMAL, env=env)
        built = run(["lean", "-o", str(Path(temporary) / "HasseSquareBounds.olean"),
                     "HasseSquareBounds.lean"], cwd=HASSE_FORMAL, env=env)
        printed = re.findall(r"^'CurveAudit\.([^']+)' depends on axioms: \[([^]]*)\]$",
                             built.stdout, re.MULTILINE)
        require(len(printed) == len(declared) and
                {name for name, _ in printed} == declared and
                all({axiom.strip() for axiom in names.split(",") if axiom.strip()}
                    <= {"propext", "Classical.choice", "Quot.sound"}
                    for _, names in printed),
                "Hasse native axiom printout changed")
        audit = run(["lean", "--run", str(ROOT / "tools/lean/AuditAxioms.lean"),
                     "HasseSquareBounds"], cwd=HASSE_FORMAL, env=env)
        audited = [line for line in audit.stdout.splitlines()
                   if line.startswith("ok    ") or line.startswith("audited ")]
        require(len(audited) == 6 and
                audited[-1] ==
                "audited 5 theorems in [HasseSquareBounds]; 0 failing, 0 trusted (native_decide)",
                "Hasse transitive theorem audit changed")
    return HASSE_SHA256


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-receipt", type=Path)
    args = parser.parse_args()
    index = json.loads(INDEX.read_text())
    paths = [path for path in run(["git", "ls-files", "--", "*.lean"]).stdout.splitlines()
             if not path.startswith("tools/lean/")]
    current = {path: digest(ROOT / path) for path in paths}
    require(len(current) == len(paths), "duplicate tracked Lean path")
    frozen_paths = {row["source"] for row in index["files"]} | set(DELTA)
    require(frozen_paths <= set(current), "frozen Lean source missing")
    additions = set(current) - frozen_paths
    frozen = {path: current[path] for path in frozen_paths}
    reused, archive = check_archive(index, frozen)
    delta = check_delta()
    output = {"schema": "cryptanalysis.current_lean_corpus_bridge.v1",
              "archive_source_commit": index["source_commit"],
              "current_lean_files": len(frozen), "archived_byte_identical_files": len(reused),
              "fresh_native_files": sorted(DELTA), "archive_evidence": archive,
              "fresh_native_source_sha256": {path: current[path] for path in sorted(DELTA)},
              "fresh_native_evidence": delta,
              "scope": "source-bound historical and fresh Lean builds with recorded allowed axiom outputs; exhaustive theorem audit, semantic fidelity and historical execution remain open"}
    encoded = (json.dumps(output, indent=2, sort_keys=True) + "\n").encode()
    if args.check_receipt:
        require(args.check_receipt.read_bytes() == encoded, "committed corpus receipt differs")
    else:
        print(encoded.decode(), end="")
    hasse_addition = HASSE_SOURCE in additions
    checked = check_new_hecke(additions - {HASSE_SOURCE})
    if hasse_addition:
        checked[HASSE_SOURCE] = check_new_hasse()
    print(f"native added theorem modules checked: {len(checked)}")


if __name__ == "__main__":
    main()
