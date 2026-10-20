#!/usr/bin/env python3
"""Inventory local repository dependencies without importing or running repo code."""
import argparse
import ast
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

try:
    import tomllib
except ImportError:
    tomllib = None

SKIP = {".git", "node_modules", "target", "build", "dist", ".venv", "venv",
        "third_party", "vendor", ".mypy_cache", ".pytest_cache", "__pycache__"}
IMPORT_PACKAGES = {
    "yaml": "PyYAML", "Crypto": "pycryptodome", "PIL": "Pillow",
    "sklearn": "scikit-learn", "cv2": "opencv-python", "z3": "z3-solver",
    "pysat": "python-sat", "flint": "python-flint", "sage": "SageMath",
    "numpy": "numpy", "scipy": "scipy", "sympy": "sympy", "matplotlib": "matplotlib",
    "pandas": "pandas", "networkx": "networkx", "cypari2": "cypari2", "fpylll": "fpylll",
    "gmpy2": "gmpy2", "pycryptosat": "pycryptosat", "requests": "requests",
    "tqdm": "tqdm", "boto3": "boto3", "botocore": "botocore", "modal": "modal",
    "runpod": "runpod", "huggingface_hub": "huggingface-hub", "pytest": "pytest",
    "jax": "jax", "jaxlib": "jaxlib", "torch": "torch", "qiskit": "qiskit",
    "langgraph": "langgraph", "langchain_core": "langchain-core",
}
TOOLS = ("nvcc", "nvidia-smi", "nsys", "ncu", "msolve", "Singular", "sage", "gp",
         "docker", "podman", "runsc", "kata-runtime", "bwrap", "cmake", "cargo",
         "rustc", "go", "redis-cli", "psql", "typst", "latexmk", "ffmpeg",
         "iverilog", "verilator", "yosys", "nextpnr", "magma", "fplll")
TOOL_RE = re.compile(r"(?<![\w./-])(" + "|".join(map(re.escape, TOOLS)) + r")(?![\w.-])")


def files(root):
    if shutil.which("rg"):
        args = ["rg", "--files", "--hidden"]
        for name in sorted(SKIP):
            args += ["-g", "!**/" + name + "/**"]
        result = subprocess.run(args + [str(root)], capture_output=True, text=True)
        if result.returncode in (0, 1):
            yield from map(Path, result.stdout.splitlines())
            return
    for base, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = [d for d in dirs if d not in SKIP and not Path(base, d).is_symlink()]
        for name in names:
            yield Path(base, name)


def inventory(root):
    root = root.resolve()
    evidence, errors, count = set(), [], 0
    local_modules = {p.stem for p in root.glob("*.py")}
    local_modules |= {p.name for p in root.iterdir() if p.is_dir()}
    stdlib = getattr(sys, "stdlib_module_names", set())

    def add(kind, name, path, line=1):
        evidence.add((kind, name, str(path.relative_to(root)), line))

    for path in files(root):
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 2_000_000:
            continue
        name = path.name
        relevant = path.suffix in {".py", ".sh", ".sage", ".yml", ".yaml"} or name in {
            "Cargo.toml", "go.mod", "pyproject.toml", "package.json", "CMakeLists.txt",
            "Makefile", "lean-toolchain"} or name.startswith(("requirements", "Dockerfile"))
        if not relevant:
            continue
        count += 1
        try:
            text = path.read_text(errors="replace")
            if name.startswith("requirements") and name.endswith(".txt"):
                for line, row in enumerate(text.splitlines(), 1):
                    match = re.match(r"\s*([A-Za-z0-9][A-Za-z0-9_.-]*)(?:\[.*?\])?\s*([<>=!~].*?)?(?:\s+#.*)?$", row)
                    if match and "://" not in row:
                        add("python-requirement", match[1] + (match[2] or ""), path, line)
            elif name in {"Cargo.toml", "pyproject.toml"}:
                if tomllib is None:
                    errors.append({"path": str(path.relative_to(root)), "reason": "TOML needs Python 3.11+; file was not parsed"})
                else:
                    doc = tomllib.loads(text)
                    if name == "Cargo.toml":
                        tables = [doc, doc.get("workspace", {})] + list(doc.get("target", {}).values())
                        for table in tables:
                            for section in ("dependencies", "dev-dependencies", "build-dependencies"):
                                for dep, value in table.get(section, {}).items():
                                    if not isinstance(value, dict) or "path" not in value:
                                        add("rust-crate", dep, path)
                    else:
                        for dep in doc.get("project", {}).get("dependencies", []):
                            if "://" not in dep: add("python-requirement", dep, path)
                        for deps in doc.get("project", {}).get("optional-dependencies", {}).values():
                            for dep in deps:
                                if "://" not in dep: add("python-optional", dep, path)
            elif name == "package.json":
                doc = json.loads(text)
                for section in ("dependencies", "devDependencies", "optionalDependencies"):
                    for dep in doc.get(section, {}): add("npm-package", dep, path)
            elif name == "go.mod":
                for line, row in enumerate(text.splitlines(), 1):
                    match = re.match(r"\s*(?:require\s+)?([\w.-]+/[^\s]+)\s+(v\S+)", row)
                    if match: add("go-module", match[1] + "@" + match[2], path, line)
            elif name == "lean-toolchain":
                add("lean-toolchain", text.strip(), path)
            if path.suffix == ".py":
                tree = ast.parse(text, filename=str(path))
                for node in ast.walk(tree):
                    modules = []
                    if isinstance(node, ast.Import): modules = [x.name.split(".")[0] for x in node.names]
                    elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                        modules = [node.module.split(".")[0]]
                    for module in modules:
                        if module in IMPORT_PACKAGES:
                            add("python-import", IMPORT_PACKAGES[module], path, node.lineno)
                        elif module not in stdlib and module not in local_modules:
                            add("unmapped-import", module, path, node.lineno)
            if path.suffix in {".sh", ".sage", ".yml", ".yaml"} or name in {"Makefile", "CMakeLists.txt"} or name.startswith("Dockerfile"):
                for line, row in enumerate(text.splitlines(), 1):
                    if row.lstrip().startswith("#"): continue
                    for match in TOOL_RE.finditer(row): add("tool-reference", match[1], path, line)
        except (ValueError, SyntaxError, OSError) as exc:
            errors.append({"path": str(path.relative_to(root)), "reason": type(exc).__name__})
    return {"root": str(root), "files_scanned": count,
            "evidence": [dict(zip(("kind", "dependency", "path", "line"), row)) for row in sorted(evidence)],
            "unparsed": errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repos", type=Path, nargs="+")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if any(not root.is_dir() for root in args.repos): parser.error("every repository path must exist")
    result = {"schema": 1, "note": "Evidence inventory; tool references and imports are not automatic install requests.",
              "repositories": [inventory(root) for root in args.repos]}
    output = json.dumps(result, indent=2) + "\n"
    if args.output: args.output.write_text(output)
    else: print(output, end="")


if __name__ == "__main__":
    main()
