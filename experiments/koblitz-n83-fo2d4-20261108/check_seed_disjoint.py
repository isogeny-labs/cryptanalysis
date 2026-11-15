#!/usr/bin/env python3
"""Check that this design's rank seeds are new on n=83 (run once, before freezing).

The rank seeds are 2601..2636 (`make_protocol.py`: SEED0 + 3 i + j). Every
`schedule*.json` and `protocol.json` of an n=83 experiment is searched for a
seed in [2600, 2670) written as a JSON `"seed": <v>` value or inside a seed
list (`<v>, <v>`):

* on `origin/main` and every `origin/*` branch whose name contains `n83`
  (read-only `git grep` in `--repo`, a worktree of this repository);
* in the scratch worktrees given with `--worktree` (this experiment's own
  directory is skipped).

Positive control: the same search for the k4c400 experiment's seeds
[2500, 2570) (`koblitz-n83-k4c400-20261107`, 2501-2560) must find its schedule.
The record also lists the earlier ranges named in the task (2201-2236, 2301-2360,
2501-2560): they are other prefixes, so are outside the searched range by construction.
The record is `inputs/seed_disjointness.json`. This is the k4c400 `check_seed_disjoint.py`
with the ranges and the control moved.
"""

import argparse
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "inputs" / "seed_disjointness.json"
PATHS = ("experiments/*n83*/schedule*.json", "experiments/*n83*/protocol.json")


def pattern(prefix):
    return r'"seed": ?%s[0-6][0-9]\b|\b%s[0-6][0-9], %s[0-6][0-9]\b' % (prefix, prefix, prefix)


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo)] + list(args), capture_output=True, text=True)


def scan(repo, worktrees, prefix):
    hits = []
    refs = ["origin/main"] + [r for r in git(repo, "for-each-ref", "--format=%(refname:short)",
                                             "refs/remotes/origin").stdout.split() if "n83" in r]
    for ref in refs:
        proc = git(repo, "grep", "-l", "-E", pattern(prefix), ref, "--", *PATHS)
        if proc.returncode not in (0, 1):
            raise SystemExit("git grep failed on %s" % ref)
        hits += [{"where": ref, "file": line} for line in proc.stdout.splitlines() if line]
    regex = re.compile(pattern(prefix))
    for tree in worktrees:
        for path in list(tree.glob("experiments/*n83*/schedule*.json")) + list(tree.glob("experiments/*n83*/protocol.json")):
            if path.resolve().parent == HERE:
                continue
            if regex.search(path.read_text(errors="replace")):
                hits.append({"where": str(tree), "file": str(path.relative_to(tree))})
    return refs, hits


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--worktree", type=Path, action="append", default=[])
    args = parser.parse_args()
    refs, hits = scan(args.repo, args.worktree, "26")
    _, control = scan(args.repo, args.worktree, "25")
    record = {"schema": 1, "seeds": "2601..2636", "searched_range": [2600, 2670],
              "recorded_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
              "origin_main": git(args.repo, "rev-parse", "origin/main").stdout.strip(),
              "refs_searched": len(refs), "worktrees": [t.name for t in args.worktree], "hits": hits,
              "positive_control": {"range": [2500, 2570], "hits": len(control),
                                   "finds_parent_schedule": any(
                                       "koblitz-n83-k4c400-20261107/schedule.json" in h["file"]
                                       for h in control)},
              "new": not hits}
    OUT.write_text(json.dumps(record, indent=1, sort_keys=True) + "\n")
    print(json.dumps({k: record[k] for k in ("new", "refs_searched", "hits", "positive_control")}, sort_keys=True))


if __name__ == "__main__":
    main()
