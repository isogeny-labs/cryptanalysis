#!/usr/bin/env python3
"""Address public proof targets by numeric index across GitHub Actions jobs.

GitHub can mistake a public target path for a secret and suppress the entire
job output. Only indexes cross the job boundary; each worker discovers the
same tracked targets at the same commit before selecting its target.
"""

import argparse
import json
from pathlib import Path
import subprocess


BATCH_SIZE = 4  # 4 * 256 targets fit in the hosted Actions matrix limit.


def discover():
    root = Path(__file__).resolve().parents[2]
    output = subprocess.check_output(
        [str(root / "tools/lean/proof-gate.sh"), "--list"], cwd=root, text=True
    )
    return [line for line in output.splitlines() if line]


def address(targets, index=None):
    if len(set(targets)) != len(targets):
        raise ValueError("proof discovery returned duplicate targets")
    if index is None:
        return json.dumps(list(range(len(targets))), separators=(",", ":"))
    if index < 0 or index >= len(targets):
        raise ValueError(f"target index {index} is outside {len(targets)} discovered targets")
    return targets[index]


def batches(targets, start=None):
    if len(set(targets)) != len(targets):
        raise ValueError("proof discovery returned duplicate targets")
    if start is None:
        count = (len(targets) + BATCH_SIZE - 1) // BATCH_SIZE
        if count > 256:
            raise ValueError(f"{len(targets)} proof targets exceed the 256-job matrix limit")
        return json.dumps([i * BATCH_SIZE for i in range(count)], separators=(",", ":"))
    if start < 0 or start >= len(targets) or start % BATCH_SIZE:
        raise ValueError(f"batch start {start} is invalid for {len(targets)} targets")
    return "\n".join(targets[start : start + BATCH_SIZE])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("matrix", "select", "batch"))
    parser.add_argument("index", type=int, nargs="?")
    args = parser.parse_args()
    if (args.mode == "matrix") != (args.index is None):
        parser.error("select and batch require an index; matrix takes no index")
    try:
        targets = discover()
        print(address(targets, args.index) if args.mode == "select" else batches(targets, args.index))
    except (ValueError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"proof target discovery failed: {exc}\n")


if __name__ == "__main__":
    main()
