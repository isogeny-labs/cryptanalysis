#!/usr/bin/env python3
"""Compile the submitted proof modules with their recorded toolchains and locks."""
import json
from pathlib import Path
import re
import subprocess
import tomllib

root = Path.cwd()
manifest = json.loads((root / "tools/ci/hecke_required_inputs.json").read_text())
projects = [root / path for path in manifest["formal"]]
shared = root / "experiments/hecke-d2631-fricke-eigenspaces-20261026/formal"
toolchain = (shared / "lean-toolchain").read_bytes()
shared_require = tomllib.loads((shared / "lakefile.toml").read_text())["require"]


def run(arguments, directory):
    result = subprocess.run(arguments, cwd=directory, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(result.stdout, end="", flush=True)
    result.check_returncode()
    return result.stdout


# All five mathlib projects declare the same exact revision and toolchain.
# Share that immutable package/cache checkout; each project's proof is checked afresh.
run(["lake", "exe", "cache", "get", "Mathlib.Tactic.Abel", "Mathlib.Tactic.Ring",
     "Mathlib.Tactic.Linarith", "Mathlib.Tactic.FinCases",
     "Mathlib.Algebra.Module.LinearMap.Basic", "Mathlib.Algebra.Field.Basic",
     "Mathlib.Data.Fintype.Fin"], shared)
for project in projects:
    assert (project / "lean-toolchain").read_bytes() == toolchain, project
    config = tomllib.loads((project / "lakefile.toml").read_text())
    if config.get("require"):
        assert config["require"] == shared_require, project
        if project != shared:
            packages = project / ".lake/packages"
            packages.parent.mkdir(exist_ok=True)
            if packages.is_symlink():
                assert packages.resolve() == (shared / ".lake/packages").resolve(), packages
            elif not packages.exists():
                packages.symlink_to(shared / ".lake/packages", target_is_directory=True)
            else:
                raise ValueError(f"existing package directory is not the verified shared checkout: {packages}")
    for library in config.get("lean_lib", []):
        source = project / (library["name"] + ".lean")
        text = source.read_text()
        assert not re.search(r"\b(sorry|admit|native_decide|axiom)\b", text), source
        requested = len(re.findall(r"^#print axioms ", text, flags=re.MULTILINE))
        assert requested > 0, source
        output = run(["lake", "env", "lean", source.name], project)
        assert "sorryAx" not in output and "declaration uses" not in output, source
        audited = len(re.findall(r"does not depend on any axioms", output))
        dependencies = re.findall(r"depends on axioms:\s*\[([^]]*)\]", output)
        for dependency in dependencies:
            assert set(x.strip() for x in dependency.split(",")) <= {"propext", "Classical.choice", "Quot.sound"}, output
        assert audited + len(dependencies) == requested, source
        print("PROOF_PASS", source.relative_to(root), "audited", requested, flush=True)
