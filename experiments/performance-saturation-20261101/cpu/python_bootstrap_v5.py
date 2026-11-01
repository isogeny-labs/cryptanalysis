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
import runpy
import sys


HERE = "/workspace/cryptanalysis/experiments/performance-saturation-20261101/cpu"
SITE_PACKAGES = (
    "/opt/codex/runtimes/codex-primary-runtime/dependencies/python/"
    "lib/python3.12/site-packages"
)
STDLIB_PATH = [
    "/opt/codex/runtimes/codex-primary-runtime/dependencies/python/lib/python312.zip",
    "/opt/codex/runtimes/codex-primary-runtime/dependencies/python/lib/python3.12",
    "/opt/codex/runtimes/codex-primary-runtime/dependencies/python/lib/python3.12/lib-dynload",
]
BASE_PATH = "/workspace/.tools/rustup/toolchains/stable-x86_64-unknown-linux-gnu/bin:/usr/bin:/bin"
BASE_ENVIRONMENT = {
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
    f"{HERE}/run_cpu_baseline_aa_v5.py": "local",
    f"{HERE}/analyze_cpu_baseline_aa_v5.py": "local",
    "/workspace/crypto-autoresearcher/tools/experiment_protocol.py": "protocol",
}


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
    target_kind = ALLOWED_TARGETS.get(target)
    if target_kind is None:
        raise SystemExit(f"CPU v5 Python target is not allow-listed: {target}")
    if target_kind == "local":
        sys.path.insert(0, HERE)
    elif target_kind == "protocol":
        sys.path.append(SITE_PACKAGES)
    # The analyzer imports both the local runner and the canonical tool.  The
    # latter imports jsonschema from this one exact, pre-hashed site root.
    if target.endswith("/analyze_cpu_baseline_aa_v5.py"):
        sys.path.append(SITE_PACKAGES)
    sys.argv = [target, *sys.argv[3:]]
    runpy.run_path(target, run_name="__main__")


if __name__ == "__main__":
    main()
