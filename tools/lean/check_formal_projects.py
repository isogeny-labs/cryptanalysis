"""Fresh native audit of exact standalone Mathlib projects and internal aliases."""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import tomllib
from pathlib import Path

MANIFEST = Path("tools/lean/formal-projects-20261117.json")
TOOLCHAIN = "leanprover/lean4:v4.35.0-rc4"
MATHLIB = "021c46bdd042f67b538b9f9871d556a93713a9a9"
ALLOWED_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def contained(root, path):
    relative = Path(path)
    require(not relative.is_absolute() and ".." not in relative.parts,
            "formal project path escapes repository")
    file = root / relative
    require(file.resolve().is_relative_to(root.resolve()),
            "formal project target escapes repository")
    return file


def code_without_comments(source):
    """Ignore nested Lean comments while preserving strings and line positions."""
    result, index, depth = [], 0, 0
    while index < len(source):
        if depth:
            if source.startswith("/-", index):
                depth += 1
                index += 2
            elif source.startswith("-/", index):
                depth -= 1
                index += 2
            else:
                result.append("\n" if source[index] == "\n" else " ")
                index += 1
        elif source.startswith("/-", index):
            result.append(" ")
            depth = 1
            index += 2
        elif source.startswith("--", index):
            end = source.find("\n", index)
            index = len(source) if end < 0 else end
        elif source[index] == '"':
            result.append(source[index])
            index += 1
            while index < len(source):
                char = source[index]
                result.append(char)
                index += 1
                if char == "\\" and index < len(source):
                    result.append(source[index])
                    index += 1
                elif char == '"':
                    break
        else:
            result.append(source[index])
            index += 1
    require(depth == 0, "unterminated Lean comment")
    return "".join(result)


KNOWN_PROBES = {
    "experiments/xedni-public-first-large-holdout-20261115/formal/probes/OrderProbe.lean":
        ("probe-status.json", "xedni-lean-order-probe-v1", "lean_order_proved", 60),
    "experiments/xedni-public-first-large-holdout-20261115/formal/probes/PointFormulaProbe.lean":
        ("point-formula-probe-status.json", "xedni-point-formula-probe-v1", "lean_point_equality_proved", 75),
}


def validate(root, record):
    require(record.get("schema") == "cryptanalysis.formal-projects/v1"
            and record.get("toolchain") == TOOLCHAIN
            and record.get("mathlib_revision") == MATHLIB,
            "formal project dependency pins changed")
    require(re.fullmatch("[0-9a-f]{40}", record.get("source_commit", "")),
            "formal project source revision missing")
    graphs = {p: {} for p in record["projects"]}
    probes = record.get("probes", {})
    require(set(probes) <= set(KNOWN_PROBES), "a primary proof cannot become a censored probe")
    for path, row in record["files"].items():
        owners = [p for p in graphs if path.startswith(p + "/")]
        require(len(owners) == 1, "formal source has no unique build project")
        project = owners[0]
        file = contained(root, path)
        if row["mode"] == "120000":
            require(file.is_symlink() and os.readlink(file) == row["target"],
                    "formal alias target changed: " + path)
            raw = os.readlink(file).encode()
        else:
            require(row["mode"] == "100644" and file.is_file() and not file.is_symlink(),
                    "formal source mode changed: " + path)
            raw = file.read_bytes()
        source_bytes = file.read_bytes()
        require(sha(raw) == row["sha256"] and sha(source_bytes) == row["body_sha256"],
                "formal source or alias bytes changed: " + path)
        parts = Path(path).relative_to(project).with_suffix("").parts
        require(parts and all(re.fullmatch("[A-Za-z_][A-Za-z0-9_]*", p) for p in parts)
                and parts[0] not in {"CollectedTypes", "AuditHeckeAxioms"},
                "invalid formal module name")
        module = ".".join(parts)
        require(module not in graphs[project], "ambiguous formal module identity")
        source = code_without_comments(source_bytes.decode())
        require(not re.search(r"\b(?:sorry|admit|sorryAx|native_decide|axiom)\b", source),
                "formal source has a proof escape: " + path)
        require(not re.search(r"\b(?:IO|unsafe|elab|macro|run_tac|run_elab|run_cmd|initialize|builtin_initialize)\b|#eval", source),
                "formal source needs a separately reviewed elaboration input boundary: " + path)
        requests = re.findall(r"^[ \t]*#print axioms\s+([\w.]+)\s*$", source, re.M)
        if path in probes:
            status_row = probes[path]
            filename, schema, proved_field, seconds = KNOWN_PROBES[path]
            status_path = Path(path).parent / filename
            require(status_row["status_path"] == status_path.as_posix()
                    and status_row["timeout_seconds"] == seconds,
                    "original censored probe protocol changed")
            status_file = contained(root, str(status_path))
            require(status_file.is_file() and not status_file.is_symlink()
                    and sha(status_file.read_bytes()) == status_row["status_sha256"],
                    "original censored probe status changed")
            status = json.loads(status_file.read_text())
            require(status["schema"] == schema and status["status"] == "timeout"
                    and status["observed_exit_code"] == 124 and status[proved_field] is False
                    and status["source_sha256"] == row["body_sha256"],
                    "censored probe acquired unsupported proof standing")
        else:
            require(requests and len(requests) == len(set(requests)),
                    "formal source lacks distinct original axiom queries: " + path)
        graphs[project][module] = {"path": path, "source": source_bytes,
                                  "requests": requests, "probe": path in probes}
    for path, row in record["files"].items():
        if row["mode"] == "120000":
            target = contained(root, path).resolve().relative_to(root.resolve()).as_posix()
            require(target in record["files"] and record["files"][target]["mode"] == "100644"
                    and Path(path).stem == Path(target).stem,
                    "formal alias is not a bound same-name module")
    orders = {}
    for project, project_row in record["projects"].items():
        require(project.startswith("experiments/xedni-") and project.endswith("/formal"),
                "unrecognized standalone formal project")
        expected = {project + "/" + name for name in
                    ("lean-toolchain", "lakefile.toml", "lake-manifest.json")}
        require(set(project_row["inputs"]) == expected, "incomplete formal build inputs")
        for path, expected_hash in project_row["inputs"].items():
            file = contained(root, path)
            require(file.is_file() and not file.is_symlink() and sha(file.read_bytes()) == expected_hash,
                    "formal build input changed: " + path)
        require((root / project / "lean-toolchain").read_text().strip() == TOOLCHAIN,
                "formal toolchain changed")
        lake = tomllib.loads((root / project / "lakefile.toml").read_text())
        requires = lake.get("require", [])
        require(len(requires) == 1 and requires[0].get("name") == "mathlib"
                and requires[0].get("git") == "https://github.com/leanprover-community/mathlib4"
                and requires[0].get("rev") == MATHLIB,
                "formal direct dependency changed")
        require(set(lake) <= {"name", "version", "defaultTargets", "require", "lean_lib"}
                and all(set(lib) <= {"name"} for lib in lake.get("lean_lib", [])),
                "unsupported standalone project compiler options")
        packages = json.loads((root / project / "lake-manifest.json").read_text())["packages"]
        mathlib = [p for p in packages if p["name"] == "mathlib"]
        require(len(mathlib) == 1 and mathlib[0]["rev"] == MATHLIB,
                "formal manifest Mathlib revision changed")
        modules = graphs[project]
        require(modules, "formal build project has no bound source")
        for module, row in modules.items():
            imports = []
            for line in code_without_comments(row["source"].decode()).splitlines():
                match = re.match(r"^import\s+(.+)", line)
                if not match:
                    continue
                for name in match[1].split("--", 1)[0].split():
                    if name in modules:
                        require(not modules[name]["probe"], "proof imports a censored probe")
                        imports.append(name)
                    else:
                        require(name.split(".")[0] in {"Mathlib", "Lean", "Std", "Init", "Batteries", "Aesop", "Qq"},
                                "unbound formal module import: " + name)
            row["imports"] = imports
        order, visiting, done = [], set(), set()
        def visit(name):
            require(name not in visiting, "cyclic formal import graph")
            if name in done:
                return
            visiting.add(name)
            for dependency in modules[name]["imports"]:
                visit(dependency)
            visiting.remove(name)
            done.add(name)
            order.append(name)
        for name in sorted(modules):
            if not modules[name]["probe"]:
                visit(name)
        orders[project] = order
    return graphs, orders


def query_coverage(requests, names):
    """Bind full query suffixes; Lean permits relative namespace resolution."""
    if len(requests) != len(names) or len(set(names)) != len(names):
        return False
    matched = {}

    def assign(index, seen):
        query = requests[index]
        root_qualified = query.startswith("_root_.")
        query = query.removeprefix("_root_.")
        for name in names:
            if name in seen or not (name == query or
                    (not root_qualified and name.endswith("." + query))):
                continue
            seen.add(name)
            if name not in matched or assign(matched[name], seen):
                matched[name] = index
                return True
        return False

    return all(assign(index, set()) for index in range(len(requests)))


def context_signature(module, source, dependency_signatures):
    return sha(json.dumps([module, sha(source), dependency_signatures, TOOLCHAIN, MATHLIB],
                          sort_keys=True).encode())


def check(root, gate):
    manifest_bytes = (root / MANIFEST).read_bytes()
    checker_bytes = Path(__file__).read_bytes()
    record = json.loads(manifest_bytes)
    graphs, orders = validate(root, record)
    gate.check_known_label_project_inputs()
    shared = json.loads((gate.HECKE_CI / "lake-manifest.json").read_text())
    shared_revisions = {p["name"]: p["rev"] for p in shared["packages"]}
    for project in graphs:
        packages = json.loads((root / project / "lake-manifest.json").read_text())["packages"]
        require(all(shared_revisions.get(p["name"]) == p["rev"] for p in packages),
                "formal transitive dependency differs from reviewed workspace")
    auditor = root / "tools/lean/AuditHeckeAxioms.lean"
    require(auditor.is_file() and not auditor.is_symlink()
            and sha(auditor.read_bytes()) == gate.AUDITOR_SHA256, "formal runtime auditor changed")
    lean_path = gate.run(["lake", "env", "printenv", "LEAN_PATH"], cwd=gate.HECKE_CI).stdout.strip()
    originals = {path: (root / path).read_bytes() for row in record["projects"].values()
                 for path in row["inputs"]}
    for path, row in record["files"].items():
        originals[path] = (row["target"].encode() if row["mode"] == "120000"
                           else (root / path).read_bytes())
    for row in record.get("probes", {}).values():
        originals[row["status_path"]] = (root / row["status_path"]).read_bytes()
    evidence_files = {"manifest.json": manifest_bytes, "checker.py": checker_bytes,
                      "AuditHeckeAxioms.lean": auditor.read_bytes()}
    original_paths = {}
    for index, (path, data) in enumerate(sorted(originals.items())):
        name = f"input-{index:04d}.bin"
        evidence_files[name] = data
        original_paths[name] = path
    binding = gate.retain_evidence("formal-project-inputs", evidence_files, {
        "manifest_sha256": sha(manifest_bytes), "source_commit": record["source_commit"],
        "original_paths": original_paths,
        "trust_boundary": "Point-in-time hashes; trust native compiler, reviewed dependencies and runner integrity."})
    checked, receipts, cache = {}, [], {}
    for project, modules in sorted(graphs.items()):
        with tempfile.TemporaryDirectory(prefix="formal-native-", dir=gate.evidence_directory()) as temporary:
            workspace = Path(temporary)
            for name, row in modules.items():
                file = workspace / Path(*name.split(".")).with_suffix(".lean")
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_bytes(row["source"])
            runtime_auditor = workspace / "AuditHeckeAxioms.lean"
            runtime_auditor.write_bytes(auditor.read_bytes())
            env = {**os.environ, "LEAN_PATH": str(workspace) + os.pathsep + lean_path}
            identities, signatures = {}, {}
            def output_file(name):
                return workspace / Path(*name.split(".")).with_suffix(".olean")
            def guard():
                require((root / MANIFEST).read_bytes() == manifest_bytes
                        and Path(__file__).read_bytes() == checker_bytes,
                        "formal verifier or binding manifest changed")
                validate(root, record)
                gate.check_known_label_project_inputs()
                require(auditor.read_bytes() == runtime_auditor.read_bytes()
                        and sha(runtime_auditor.read_bytes()) == gate.AUDITOR_SHA256,
                        "formal runtime auditor changed")
                require(all(sha((workspace / Path(*name.split(".")).with_suffix(".lean")).read_bytes())
                            == sha(row["source"]) for name, row in modules.items()),
                        "formal compilation copy changed")
                for name, identity in identities.items():
                    gate.check_compiled_identity(output_file(name), identity)
            for name in orders[project]:
                guard()
                row = modules[name]
                signature = context_signature(name, row["source"],
                    [(dependency, signatures[dependency]) for dependency in row["imports"]])
                output = output_file(name)
                output.parent.mkdir(parents=True, exist_ok=True)
                reused = signature in cache
                if reused:
                    cached = cache[signature]
                    require({p: sha(data) for p, data in cached["objects"].items()}
                            == cached["receipt"]["compiled_identity"], "fresh native cache object changed")
                    for filename, data in cached["objects"].items():
                        (output.parent / filename).write_bytes(data)
                    identities[name] = cached["receipt"]["compiled_identity"]
                    receipt = cached["receipt"]
                else:
                    result = gate.run(["lean", "-R", str(workspace), "-o", str(output),
                                       str(workspace / Path(*name.split(".")).with_suffix(".lean"))],
                                      cwd=gate.HECKE_CI, env=env, timeout=900, failure_diagnostics=True)
                    identities[name] = gate.compiled_identity(output)
                    printed = re.findall(r"^'([^']+)' depends on axioms: \[([^]]*)\]$", result.stdout, re.M)
                    free = re.findall(r"^'([^']+)' does not depend on any axioms$", result.stdout, re.M)
                    names = [n for n, _ in printed] + free
                    require(query_coverage(row["requests"], names),
                            "formal native query coverage changed: " + name)
                    require(all({a.strip() for a in axioms.split(",") if a.strip()} <= ALLOWED_AXIOMS
                                for _, axioms in printed), "formal query has an unexpected foundation")
                    audit = gate.run(["lean", "--run", str(runtime_auditor), name],
                                     cwd=gate.HECKE_CI, env=env, timeout=900, failure_diagnostics=True)
                    summary = re.findall(r"^audited ([1-9][0-9]*) theorems; 0 failing, 0 trusted$",
                                         audit.stdout, re.M)
                    require(len(summary) == 1
                            and len(re.findall(r"^ok    ", audit.stdout, re.M)) == int(summary[0]),
                            "formal module lacks a complete native theorem audit: " + name)
                    guard()
                    gate.collect_elaborated_types("/".join(name.split(".")) + ".lean",
                                                  frozenset(names), str(workspace), lean_path)
                    guard()
                    print(result.stdout, end="", flush=True)
                    print(audit.stdout, end="", flush=True)
                    receipt = {"module": name, "source": row["path"], "source_sha256": sha(row["source"]),
                               "queried_constants": names, "theorems": int(summary[0]),
                               "compiled_identity": identities[name]}
                    cache[signature] = {"receipt": receipt, "objects": {
                        filename: (output.parent / filename).read_bytes()
                        for filename in identities[name]}}
                signatures[name] = signature
                guard()
                receipts.append({**receipt, "context_source_path": row["path"],
                                 "project": project, "context_signature": signature,
                                 "reused_exact_object_built_and_audited_in_this_invocation": reused})
                checked[row["path"]] = record["files"][row["path"]]["body_sha256"]
            guard()
    probes = record.get("probes", {})
    gate.retain_evidence("formal-project-receipt", {}, {
        "projects": len(record["projects"]), "fresh_native_module_contexts": len(cache),
        "proof_source_and_alias_paths": len(checked), "modules": receipts,
        "historical_censored_probes": [
            {"source": path, **row, "theorem_standing": False, "native_replayed": False,
             "scope": "Exact original censored input and status, not an admitted theorem"}
            for path, row in sorted(probes.items())],
        "inputs_evidence": str(binding)})
    print(f"standalone formal module contexts freshly audited: {len(cache)}; "
          f"proof source/alias paths bound: {len(checked)}; "
          f"original censored inputs without theorem standing: {len(probes)}", flush=True)
    return checked, set(probes)
