#!/usr/bin/env python3
"""Closed Python router for CPU baseline A/A v5.

The external ``python_preflight_v5.sh`` hashes the interpreter, this file,
every importable source/extension, and each allowed target before Python
starts.  This router then proves that startup disabled site processing and
bytecode caches, validates the inherited-nothing environment, adds only the
frozen import roots, and executes one allow-listed target.
"""

from __future__ import annotations

import os
import sys


HERE = "/workspace/cryptanalysis/experiments/performance-saturation-20261101/cpu"
SITE_PACKAGES = (
    "/opt/codex/runtimes/codex-primary-runtime/dependencies/python/"
    "lib/python3.12/site-packages"
)
STDLIB_ROOT = "/opt/codex/runtimes/codex-primary-runtime/dependencies/python/lib/python3.12"
IMPORT_INVENTORY = f"{HERE}/python-import-inventory-v5.txt"
SITE_PACKAGES_ALLOWED = (
    "attr", "attrs", "idna", "jsonschema", "jsonschema_specifications",
    "referencing", "rpds", "webcolors",
)
SITE_FILES_ALLOWED = ("typing_extensions.py",)
STDLIB_PATH = [
    "/opt/codex/runtimes/codex-primary-runtime/dependencies/python/lib/python312.zip",
    "/opt/codex/runtimes/codex-primary-runtime/dependencies/python/lib/python3.12",
    "/opt/codex/runtimes/codex-primary-runtime/dependencies/python/lib/python3.12/lib-dynload",
]
BASE_PATH = "/workspace/.tools/rustup/toolchains/stable-x86_64-unknown-linux-gnu/bin:/usr/bin:/bin"
PREFLIGHT_ENV = "CPU_V5_PREFLIGHT_VERIFIED"
PREFLIGHT_VALUE = "cpu-baseline-aa-v5/preflight-v1"
BASE_ENVIRONMENT = {
    PREFLIGHT_ENV: PREFLIGHT_VALUE,
    "LANG": "C",
    "LC_ALL": "C",
    "PATH": BASE_PATH,
    "PYTHONCOERCECLOCALE": "0",
    "PYTHONHASHSEED": "0",
    "PYTHONUTF8": "1",
    "TZ": "UTC",
}
PROFILES = {
    "base": BASE_ENVIRONMENT,
    "wall-1": {
        **BASE_ENVIRONMENT,
        "OMP_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "RAYON_NUM_THREADS": "1",
    },
    "wall-4": {
        **BASE_ENVIRONMENT,
        "OMP_NUM_THREADS": "4",
        "OPENBLAS_NUM_THREADS": "1",
        "RAYON_NUM_THREADS": "4",
    },
    "callgrind-1": {
        **BASE_ENVIRONMENT,
        "PATH": "/workspace/.tools/valgrind/bin:/usr/bin:/bin",
        "OMP_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "RAYON_NUM_THREADS": "1",
    },
}
ALLOWED_TARGETS = {
    f"{HERE}/run_cpu_baseline_aa_v5.py": "application",
    f"{HERE}/analyze_cpu_baseline_aa_v5.py": "application",
    "/workspace/crypto-autoresearcher/tools/experiment_protocol.py": "protocol",
}


def import_inventory(
    stdlib_root: str = STDLIB_ROOT,
    site_packages: str = SITE_PACKAGES,
    allowed_packages: tuple[str, ...] = SITE_PACKAGES_ALLOWED,
    allowed_files: tuple[str, ...] = SITE_FILES_ALLOWED,
) -> list[str]:
    """Inventory every executable file and directory-routing node PathFinder can use."""
    result: set[str] = set()

    def record_link(path: str) -> None:
        result.add(
            "L\t" + path + "\t" + os.readlink(path) + "\t" + os.path.realpath(path)
        )

    def scan(root: str) -> None:
        if os.path.islink(root):
            record_link(root)
            return
        if not os.path.isdir(root):
            result.add("X\t" + root)
            return
        result.add("D\t" + root)
        for directory, names, files in os.walk(root, followlinks=False):
            retained_names: list[str] = []
            for name in sorted(names):
                path = os.path.join(directory, name)
                if name == "__pycache__" or os.path.abspath(path) == os.path.abspath(site_packages):
                    continue
                if os.path.islink(path):
                    record_link(path)
                elif os.path.isdir(path):
                    result.add("D\t" + path)
                    retained_names.append(name)
                else:
                    result.add("X\t" + path)
            names[:] = retained_names
            for name in sorted(files):
                path = os.path.join(directory, name)
                if os.path.islink(path):
                    record_link(path)
                elif name.endswith((".py", ".pyc", ".so")):
                    result.add("P\t" + path)

    scan(stdlib_root)
    for package in allowed_packages:
        scan(os.path.join(site_packages, package))
    allowed_top = set(allowed_packages) | {
        name.removesuffix(".py") for name in allowed_files
    }
    for entry in os.scandir(site_packages):
        stem = entry.name.split(".", 1)[0]
        if stem not in allowed_top:
            continue
        if entry.name in allowed_packages:
            kind = "D" if entry.is_dir(follow_symlinks=False) else "X"
            result.add(f"{kind}\t{entry.path}")
        elif entry.name in allowed_files:
            kind = "F" if entry.is_file(follow_symlinks=False) else "X"
            result.add(f"{kind}\t{entry.path}")
        elif entry.name.endswith((".py", ".pyc", ".so")):
            result.add(f"A\t{entry.path}")
    return sorted(result)


class ClosedSiteFinder:
    """Resolve only the named, inventoried top-level third-party modules."""

    def __init__(self, path_finder: object) -> None:
        self.path_finder = path_finder

    def find_spec(self, fullname: str, path: object = None, target: object = None) -> object:
        if path is not None or fullname not in {
            *SITE_PACKAGES_ALLOWED, "typing_extensions",
        }:
            return None
        spec = self.path_finder.find_spec(fullname, [SITE_PACKAGES], target)
        expected = (
            os.path.join(SITE_PACKAGES, "typing_extensions.py")
            if fullname == "typing_extensions"
            else os.path.join(SITE_PACKAGES, fullname, "__init__.py")
        )
        if spec is None or os.path.realpath(spec.origin or "") != os.path.realpath(expected):
            raise ImportError(f"CPU v5 closed-site route differs for {fullname}")
        return spec


def main() -> None:
    if (
        not sys.flags.no_site
        or not sys.flags.safe_path
        or not sys.flags.dont_write_bytecode
        or sys.pycache_prefix != "/dev/null"
        or sys.path != STDLIB_PATH
    ):
        raise SystemExit("CPU v5 Python startup is not closed")
    if len(sys.argv) < 3:
        raise SystemExit("usage: python_bootstrap_v5.py PROFILE TARGET [ARGS...]")
    profile, target = sys.argv[1], os.path.realpath(sys.argv[2])
    expected_environment = PROFILES.get(profile)
    if expected_environment is None or dict(os.environ) != expected_environment:
        raise SystemExit("CPU v5 Python environment differs from the frozen profile")
    os.environ.pop(PREFLIGHT_ENV)
    target_kind = ALLOWED_TARGETS.get(target)
    if target_kind is None:
        raise SystemExit(f"CPU v5 Python target is not allow-listed: {target}")
    with open(IMPORT_INVENTORY, "r", encoding="utf-8") as stream:
        expected_inventory = stream.read().splitlines()
    if import_inventory() != expected_inventory:
        raise SystemExit("CPU v5 effective Python import inventory differs")
    from importlib.machinery import PathFinder
    import runpy

    if target_kind in {"application", "protocol"}:
        sys.meta_path.insert(0, ClosedSiteFinder(PathFinder))
    os.environ["CPU_V5_CLOSED_BOOTSTRAP"] = f"cpu-baseline-aa-v5/{profile}"
    sys.argv = [target, *sys.argv[3:]]
    runpy.run_path(target, run_name="__main__")


if __name__ == "__main__":
    main()
