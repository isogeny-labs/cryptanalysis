#!/usr/bin/env python3
"""Bind the frozen Lean corpus and natively check admitted theorem modules.

The October 21 corpus audit compiled 93 files. Its 97-file bridge remains
byte-for-byte source-bound to the committed receipt; six explicitly rebuilt
files and the PQC assay are separately pinned. New Hecke modules use the
pinned Mathlib workspace, including modules whose recorded build dependencies
override the repository's inherited root pin. The reviewed Hasse-square module
uses its own pinned toolchain. Other source or pin changes still fail until
native evidence is added here.
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

LOADED_GATE_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
AUDITOR_SHA256 = "c2ba62cad8b2678cd3058489c146ed78b2fe2c4ef5b8c059ae6426e25864c241"
ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / "reports/lean-evidence-audit-20261021/evidence/corpus"
INDEX = ARCHIVE / "cryptanalysis-corpus-index-20261021.json"
GLV = ROOT / "experiments/glv-table-rule-confirm-20261022"
ORBIT = ROOT / "experiments/orbit-quotient-summation/lean"
CUBIC = ROOT / "experiments/ghs-sweeper/formal"
CM = ROOT / "experiments/ghs-sweeper/cm-formal"
HECKE_CI = ROOT / "experiments/hecke-432-formal-ci-20261025"
HECKE_TOOLCHAIN = "leanprover/lean4:v4.35.0-rc4"
HECKE_MATHLIB_REV = "021c46bdd042f67b538b9f9871d556a93713a9a9"
KNOWN_LABEL_SOURCE = "docs/known-label-next-leads-20261028/Algebra.lean"
KNOWN_LABEL_SHA256 = "d0e0fa1892bc800999e3b5330f543bf2e99811f607606901f363fce27bcb428d"
KNOWN_LABEL_THEOREMS = frozenset({
    "KnownLabelLeads.triangle_identity",
    "KnownLabelLeads.signed_second_moment",
    "KnownLabelLeads.signed_third_moment",
    "KnownLabelLeads.positive_pair_product",
})
# These are the new check's inputs, not a claim about the producer's environment.
# The original CHECKS.json explicitly says the proposed Lean source was unbuilt.
KNOWN_LABEL_PROJECT_INPUTS = {
    "lean-toolchain": "8f89aa44fccdb1a0b6cc768c7c9f54b94cd40e47a08d582f82d1235f13075cf7",
    "lakefile.toml": "efb8f87487140c5a80d7931e29aff9eda54b008323153887b10a13f2beca3e00",
    "lake-manifest.json": "47af1da86329fd961aed48007fe7e29b9aad28ecbb6f2835938656ecfdb30756",
}
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


def evidence_directory() -> Path:
    """Durable diagnostics, separate from disposable module build directories."""
    root = Path(os.environ.get("LEAN_CORPUS_EVIDENCE_DIR", ROOT / ".lean-corpus-evidence"))
    root.mkdir(parents=True, exist_ok=True)
    return root


def retain_evidence(kind: str, files: dict[str, bytes], metadata: dict) -> Path:
    directory = Path(tempfile.mkdtemp(prefix=kind + "-", dir=evidence_directory()))
    for name, data in files.items():
        (directory / name).write_bytes(data)
    metadata = {**metadata, "files": {
        name: hashlib.sha256(data).hexdigest() for name, data in files.items()}}
    (directory / "record.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(f"retained {kind} evidence: {directory}", flush=True)
    return directory


def run(args: list[str], *, cwd: Path = ROOT, env: dict | None = None,
        timeout: int = 900) -> subprocess.CompletedProcess[str]:
    metadata = {"argv": args, "cwd": str(cwd), "timeout_seconds": timeout,
                "gate_sha256": LOADED_GATE_SHA256,
                "LEAN_PATH": (env or os.environ).get("LEAN_PATH"),
                "github_sha": os.environ.get("GITHUB_SHA")}
    try:
        # Keep original bytes, including invalid UTF-8, before decoding for parsers.
        result = subprocess.run(args, cwd=cwd, env=env, capture_output=True,
                                timeout=timeout, check=False)
    except (subprocess.TimeoutExpired, OSError) as error:
        files = {"stdout.bin": getattr(error, "stdout", None) or b"",
                 "stderr.bin": getattr(error, "stderr", None) or b""}
        retain_evidence("command", files, {**metadata, "returncode": None,
                        "timed_out": isinstance(error, subprocess.TimeoutExpired),
                        "exception": repr(error)})
        raise
    record = retain_evidence("command", {"stdout.bin": result.stdout,
                             "stderr.bin": result.stderr},
                             {**metadata, "returncode": result.returncode,
                              "timed_out": False})
    require(result.returncode == 0,
            f"{args[0]} exited {result.returncode}; complete diagnostics: {record}")
    return subprocess.CompletedProcess(args, result.returncode,
                                       result.stdout.decode("utf-8"),
                                       result.stderr.decode("utf-8"))


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


def reviewed_quartic_sources() -> dict[str, str]:
    """Bind the original locations and build pins of the reviewed certificates."""
    file = ROOT / "tools/ci/quartic_certificates.json"
    if not file.is_file():
        return {}
    manifest = json.loads(file.read_text())
    require(manifest["schema"] == "quartic-certificate-replay/v1" and
            manifest["toolchain"] == HECKE_TOOLCHAIN and
            manifest["mathlib"] == HECKE_MATHLIB_REV and
            manifest["project"] == str(HECKE_CI.relative_to(ROOT)),
            "reviewed quartic build pins changed")
    rows = manifest["formal"]
    sources = {row["path"]: row["sha256"] for row in rows}
    require(len(sources) == len(rows) == 37,
            "reviewed quartic source inventory changed")
    for path, expected in sources.items():
        relative = Path(path)
        require(not relative.is_absolute() and ".." not in relative.parts and
                path.startswith("experiments/hecke-432-") and
                path.endswith(".lean") and
                manifest["inputs"].get(path) == expected,
                f"invalid reviewed quartic source binding: {path}")
    for name in ("lean-toolchain", "lake-manifest.json", "lakefile.toml"):
        path = HECKE_CI / name
        require(digest(path) == manifest["inputs"].get(str(path.relative_to(ROOT))),
                f"reviewed quartic project input changed: {name}")
    return sources


def check_reviewed_quartic(path: str, expected: str, lean_path: str) -> str:
    return check_pinned_mathlib_source(path, expected, lean_path,
                                      label="reviewed quartic")


def check_known_label_algebra(lean_path: str) -> str:
    """Check the fixed proposed ring lemmas; no elliptic-group bridge is asserted."""
    check_known_label_project_inputs()
    checked = check_pinned_mathlib_source(
        KNOWN_LABEL_SOURCE, KNOWN_LABEL_SHA256, lean_path,
        label="known-label", exact_names=KNOWN_LABEL_THEOREMS,
        expected_theorems=4)
    check_known_label_project_inputs()
    return checked


def check_known_label_project_inputs() -> None:
    """Bind workspace input bytes before and after the native commands."""
    for name, expected in KNOWN_LABEL_PROJECT_INPUTS.items():
        file = HECKE_CI / name
        require(not file.is_symlink() and digest(file) == expected,
                f"known-label project input changed: {name}")


def collect_elaborated_types(path: str, names: frozenset[str],
                             scratch: str, lean_path: str) -> str:
    """Import the freshly built module and retain actual native type output.

    Header checks establish output completeness, not semantic fidelity. The
    frozen producer source is never edited to add printing commands.
    """
    parts = Path(path).with_suffix("").parts
    require(parts and all(re.fullmatch(r"[A-Za-z0-9_-]+", p) for p in parts),
            "invalid module path for type collection")
    require(names and all(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.]*", n) for n in names),
            "invalid theorem names for type collection")
    module = ".".join(f"«{part}»" for part in parts)
    wrapper = (f"import {module}\n"
               "set_option pp.universes true\n"
               "set_option pp.explicit true\n"
               "set_option pp.fullNames true\n" +
               "".join(f"#check @{name}\n" for name in sorted(names)))
    file = Path(scratch) / "CollectedTypes.lean"
    file.write_text(wrapper)
    retain_evidence("type-wrapper", {"CollectedTypes.lean": wrapper.encode()},
                    {"module": path, "names": sorted(names)})
    env = {**os.environ, "LEAN_PATH": scratch + os.pathsep + lean_path}
    result = run(["lean", str(file)], cwd=HECKE_CI, env=env)
    retain_evidence("type-output", {"stdout.txt": result.stdout.encode()},
                    {"module": path, "names": sorted(names)})
    found = re.findall(
        r"^@?([A-Za-z_][A-Za-z0-9_.]*?)(?:\.\{[^}\n]+\})?\s*:\s*\S",
        result.stdout, re.MULTILINE)
    require(len(found) == len(names) and set(found) == names,
            f"incomplete native elaborated types in {path}")
    require(file.read_text() == wrapper, "type wrapper changed during collection")
    print("BEGIN NATIVE ELABORATED TYPES", flush=True)
    print(json.dumps({"module": path, "names": sorted(names),
                      "wrapper_sha256": hashlib.sha256(wrapper.encode()).hexdigest(),
                      "stdout_sha256": hashlib.sha256(result.stdout.encode()).hexdigest()}),
          flush=True)
    print(wrapper, end="", flush=True)
    print(result.stdout, end="", flush=True)
    print("END NATIVE ELABORATED TYPES", flush=True)
    return result.stdout


def compiled_identity(output: Path) -> dict[str, str]:
    """Bind the primary object and any Lean sidecars; this is a boundary check."""
    require(output.is_file() and not output.is_symlink(),
            "compiled object missing or symlinked")
    files = [output, *sorted(output.parent.glob(output.name + ".*"))]
    require(all(p.is_file() and not p.is_symlink() for p in files),
            "compiled sidecar missing or symlinked")
    return {p.name: digest(p) for p in files}


def check_compiled_identity(output: Path, expected: dict[str, str]) -> None:
    require(compiled_identity(output) == expected, "compiled object changed between phases")


def check_pinned_mathlib_source(path: str, expected: str, lean_path: str, *,
                               label: str, exact_names: frozenset[str] | None = None,
                               expected_theorems: int | None = None) -> str:
    """Compile original bytes; audit requested declarations and non-internal theorems."""
    file = ROOT / path
    require(file.resolve().is_relative_to(ROOT.resolve()) and not file.is_symlink(),
            f"{label} source escapes repository: {path}")
    require(digest(file) == expected, f"{label} source changed: {path}")
    source = file.read_text()
    require(not re.search(r"\b(?:sorry|admit|sorryAx|native_decide|axiom)\b", source),
            f"forbidden proof escape in {path}")
    requested = re.findall(r"^#print axioms\s+([\w.]+)\s*$", source, re.MULTILINE)
    require(requested and len(requested) == len(set(requested)),
            f"missing or duplicate declaration audit in {path}")
    auditor = ROOT / "tools/lean/AuditHeckeAxioms.lean"
    if exact_names is not None:
        require(auditor.is_file() and not auditor.is_symlink() and
                digest(auditor) == AUDITOR_SHA256, "runtime auditor changed")
        binding = retain_evidence("module-inputs", {
            "Source.lean": file.read_bytes(),
            "AuditHeckeAxioms.lean": auditor.read_bytes(),
            **{name: (HECKE_CI / name).read_bytes() for name in KNOWN_LABEL_PROJECT_INPUTS},
        }, {"source": path, "source_sha256": expected,
            "gate_sha256": LOADED_GATE_SHA256, "auditor_sha256": AUDITOR_SHA256,
            "trust_boundary": "Point-in-time hashes, not protection against transient edits; "
                              "trust Lean executable, dependencies/cache and runner integrity"})
        audit_input = binding / "AuditHeckeAxioms.lean"
    else:
        audit_input = auditor
    with tempfile.TemporaryDirectory(prefix="mathlib-corpus-") as scratch:
        output = Path(scratch) / Path(path).with_suffix(".olean")
        output.parent.mkdir(parents=True)
        result = run(["lake", "env", "lean", "-R", str(ROOT), "-o", str(output),
                      str(file)], cwd=HECKE_CI, timeout=900)
        printed = re.findall(r"^'([^']+)' depends on axioms: \[([^]]*)\]$",
                             result.stdout, re.MULTILINE)
        free = re.findall(r"^'([^']+)' does not depend on any axioms$",
                          result.stdout, re.MULTILINE)
        names = [name for name, _ in printed] + free
        require(len(names) == len(requested) and
                {name.rsplit(".", 1)[-1] for name in names} ==
                {name.rsplit(".", 1)[-1] for name in requested},
                f"incomplete native declaration audit in {path}")
        if exact_names is not None:
            require(len(names) == len(exact_names) and set(names) == exact_names,
                    f"native theorem identities changed in {path}")
        require(all({a.strip() for a in axs.split(",") if a.strip()} <=
                    {"propext", "Classical.choice", "Quot.sound"}
                    for _, axs in printed), f"unexpected foundation in {path}")
        object_identity = None
        if exact_names is not None:
            object_identity = compiled_identity(output)
            retain_evidence("compiled-object", {}, {"module": path,
                            "sha256": object_identity, "source_sha256": expected,
                            "gate_sha256": LOADED_GATE_SHA256,
                            "auditor_sha256": AUDITOR_SHA256})
            require(digest(auditor) == digest(audit_input) == AUDITOR_SHA256,
                    "runtime auditor changed")
        env = {**os.environ, "LEAN_PATH": scratch + os.pathsep + lean_path}
        audit = run(["lean", "--run", str(audit_input),
                     path[:-5].replace("/", ".")], cwd=HECKE_CI, env=env)
        if object_identity is not None:
            check_compiled_identity(output, object_identity)
            require(digest(auditor) == digest(audit_input) == AUDITOR_SHA256,
                    "runtime auditor changed")
        print(result.stdout, end="", flush=True)
        print(audit.stdout, end="", flush=True)
        summary = re.findall(r"^audited ([1-9][0-9]*) theorems; 0 failing, 0 trusted$",
                             audit.stdout, re.MULTILINE)
        require(len(summary) == 1 and
                len(re.findall(r"^ok    ", audit.stdout, re.MULTILINE)) == int(summary[0]),
                f"incomplete exhaustive theorem audit in {path}")
        if expected_theorems is not None:
            require(len(requested) == expected_theorems and
                    int(summary[0]) == expected_theorems,
                    f"reviewed theorem count changed in {path}")
        if exact_names is not None:
            audited_names = set(re.findall(r"^ok    (\S+)  \[", audit.stdout, re.MULTILINE))
            require(exact_names <= audited_names,
                    f"named theorems missing from module audit in {path}")
        print(f"{label} native audit: {path}: {len(requested)} declarations, "
              f"{summary[0]} theorems", flush=True)
        require(digest(file) == expected, f"{label} source changed during audit: {path}")
        if exact_names is not None:
            check_compiled_identity(output, object_identity)
            collect_elaborated_types(path, exact_names, scratch, lean_path)
            check_compiled_identity(output, object_identity)
            require(digest(auditor) == digest(audit_input) == AUDITOR_SHA256,
                    "runtime auditor changed")
    require(digest(file) == expected, f"{label} source changed during audit: {path}")
    return expected


def check_new_hecke(paths: set[str]) -> dict[str, str]:
    """Build every added Hecke source; never admit an unbuilt corpus addition."""
    if not paths:
        return {}
    require(HECKE_CI.joinpath("lean-toolchain").read_text().strip() ==
            HECKE_TOOLCHAIN, "Hecke Lean toolchain changed")
    manifest = json.loads(HECKE_CI.joinpath("lake-manifest.json").read_text())
    mathlib = [p for p in manifest["packages"] if p["name"] == "mathlib"]
    require(len(mathlib) == 1 and
            mathlib[0]["rev"] == HECKE_MATHLIB_REV,
            "Hecke Mathlib revision changed")
    reviewed = reviewed_quartic_sources()
    lean_path = run(["lake", "env", "printenv", "LEAN_PATH"], cwd=HECKE_CI).stdout.strip()
    checked = {}
    for path in sorted(paths):
        if path == KNOWN_LABEL_SOURCE:
            checked[path] = check_known_label_algebra(lean_path)
            continue
        if path in reviewed:
            checked[path] = check_reviewed_quartic(path, reviewed[path], lean_path)
            continue
        require(path.startswith("experiments/hecke-") and "/formal/" in path and
                path.endswith(".lean"), f"unreviewed Lean corpus addition: {path}")
        pin = ROOT / effective_pin(path)
        if pin.read_text().strip() != HECKE_TOOLCHAIN:
            # Some archived Hecke sources have no local lean-toolchain file.
            # Their build records explicitly name the shared Mathlib workspace;
            # do not treat the inherited root pin as their build environment.
            require(pin == ROOT / "lean-toolchain",
                    f"Hecke theorem toolchain changed: {path}")
            dependencies = (ROOT / path).parent / "DEPENDENCIES.json"
            require(dependencies.is_file(),
                    f"Hecke build dependencies missing: {path}")
            recorded = json.loads(dependencies.read_text())
            require(recorded.get("lean_toolchain") == HECKE_TOOLCHAIN and
                    (recorded.get("mathlib_revision") or
                     recorded.get("mathlib_git_rev")) == HECKE_MATHLIB_REV,
                    f"Hecke recorded build dependencies changed: {path}")
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
        axiom_free = re.findall(r"^'([^']+)' does not depend on any axioms$",
                                result.stdout, re.MULTILINE)
        printed_names = [name for name, _ in printed] + axiom_free
        require(len(printed_names) == len(declared) and
                {name.rsplit(".", 1)[-1] for name in printed_names} == set(declared),
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
