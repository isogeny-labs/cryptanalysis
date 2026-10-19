#!/usr/bin/env python3
"""Replay frozen radix15 arithmetic, group and paired-receipt audits."""
import json
import os
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DEPS = (
    "prime-j0-nearest-digit-12211-20261014",
    "prime-j0-nearest-orbit-12211-20261014",
    "prime-j0-mixed640-materialized-tree-20261013",
    "prime-j0-mixed-radix640-20261010",
    "prime-j0-tau-power16-20261010",
)
env = os.environ.copy()
env["PYTHONPATH"] = os.pathsep.join(
    str(ROOT / "experiments" / path) for path in DEPS
)


def replay(script, expected):
    completed = subprocess.run(
        [sys.executable, str(HERE / script)],
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    actual = json.loads(completed.stdout)
    frozen = json.loads((HERE / expected).read_text())
    if actual != frozen:
        raise SystemExit(f"{script}: output differs from {expected}")
    print(f"{script}: matches {expected}")


if __name__ == "__main__":
    replay("frontier15.py", "frontier15.json")
    replay("screen268.py", "screen268.json")
    replay("group_replay268.py", "group-replay268.json")
    replay("analyze_tier1.py", "tier1-analysis.json")
