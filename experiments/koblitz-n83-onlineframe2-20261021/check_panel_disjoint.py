#!/usr/bin/env python3
"""Role-agnostic disjointness scan of the new panel (run once, before freezing).

`make_targets.py` regenerates every known n=83 panel role of B's law and
rejects any shared point. This scan also covers roles it does not know. It
looks for each panel coordinate (x and y, as decimal strings) in three
places:

* every file of `origin/main` under `experiments/` and `research/`;
* every file that any other `origin/*` branch changes against its merge base
  with `origin/main` (the whole branch content not already on main);
* every file in the scratch worktrees given with `--worktree` (committed or
  not; `.git` and `target` folders are skipped).

It writes `inputs/panel_disjointness.json` with the refs and their commits,
the counts and every hit (there must be none). It runs read-only git
commands in `--repo`, a worktree of this repository. The CI workflow does
not rerun it, because it needs the local refs and worktrees, so its record is
pinned in `protocol.json`.
"""

import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
TARGETS = HERE / "inputs" / "cold_targets.json"
OUT = HERE / "inputs" / "panel_disjointness.json"


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo)] + list(args), capture_output=True, text=True)


def grep(repo, ref, needles, paths):
    hits = []
    for start in range(0, len(paths), 500) if paths else [None]:
        chunk = paths[start:start + 500] if paths else ["experiments", "research"]
        argv = ["grep", "-F", "-l"] + [x for n in needles for x in ("-e", n)] + [ref, "--"] + chunk
        proc = git(repo, *argv)
        if proc.returncode not in (0, 1):
            raise SystemExit("git grep failed on %s: %s" % (ref, proc.stderr[:300]))
        hits += [line for line in proc.stdout.splitlines() if line]
    return hits


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--worktree", type=Path, action="append", default=[])
    args = parser.parse_args()
    panel = json.loads(TARGETS.read_text())
    needles = sorted({v for e in panel["points"] for v in e["point"]})
    main_sha = git(args.repo, "rev-parse", "origin/main").stdout.strip()
    result = {"schema": 1, "panel_role": panel["role"], "coordinates_searched": len(needles),
              "recorded_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
              "origin_main": main_sha, "hits": []}
    result["hits"] += [{"where": "origin/main", "file": h} for h in grep(args.repo, "origin/main", needles, None)]
    refs = [r for r in git(args.repo, "for-each-ref", "--format=%(refname:short)", "refs/remotes/origin").stdout.split()
            if r not in ("origin/main", "origin/HEAD", "origin")]
    scanned = {}
    files_total = 0
    for ref in refs:
        base = git(args.repo, "merge-base", "origin/main", ref).stdout.strip()
        if base:
            names = git(args.repo, "diff", "--name-only", "--diff-filter=AM", base, ref).stdout.split("\n")
        else:
            names = git(args.repo, "ls-tree", "-r", "--name-only", ref).stdout.split("\n")
        names = [n for n in names if n]
        files_total += len(names)
        scanned[ref] = git(args.repo, "rev-parse", ref).stdout.strip()
        if names:
            result["hits"] += [{"where": ref, "file": h} for h in grep(args.repo, ref, needles, names)]
    result["branches_scanned"] = len(scanned)
    result["branch_files_scanned"] = files_total
    result["branches"] = scanned
    worktrees = {}
    for tree in args.worktree:
        count = 0
        for root, dirs, files in os.walk(tree):
            dirs[:] = [d for d in dirs if d not in (".git", "target")]
            for name in files:
                path = Path(root) / name
                try:
                    data = path.read_bytes()
                except OSError:
                    continue
                count += 1
                if any(n.encode() in data for n in needles):
                    result["hits"].append({"where": str(tree), "file": str(path.relative_to(tree))})
        worktrees[tree.name] = count
    result["worktree_files_scanned"] = worktrees
    result["disjoint"] = not result["hits"]
    OUT.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    print(json.dumps({k: result[k] for k in ("disjoint", "branches_scanned", "branch_files_scanned",
                                             "worktree_files_scanned", "hits")}, sort_keys=True))


if __name__ == "__main__":
    main()
