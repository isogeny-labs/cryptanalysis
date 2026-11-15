#!/usr/bin/env python3
"""Compile tracked report and graph Python sources without executing them."""

from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys


REPORT_GRAPH_NAME = re.compile(
    r"(?:render|dashboard|report|figure|visual|plot|chart|svg).*\.py$",
    re.IGNORECASE,
)


def tracked_sources() -> list[pathlib.Path]:
    names = subprocess.check_output(["git", "ls-files", "-z", "--cached"])
    paths = (pathlib.Path(name.decode("utf-8")) for name in names.split(b"\0") if name)
    return sorted(path for path in paths if REPORT_GRAPH_NAME.search(path.name))


def check(paths: list[pathlib.Path]) -> int:
    if not paths:
        print("report-graph-python: no sources selected", file=sys.stderr)
        return 1
    failures = 0
    for path in paths:
        try:
            compile(path.read_bytes(), str(path), "exec")
        except (OSError, SyntaxError, UnicodeError) as exc:
            print(f"{path}: {exc}", file=sys.stderr)
            failures += 1
    print(f"report-graph-python: {len(paths)} source(s), {failures} failure(s)")
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="*",
        type=pathlib.Path,
        help="explicit files for a focused check; default is tracked report/graph sources",
    )
    args = parser.parse_args()
    return check(args.paths or tracked_sources())


if __name__ == "__main__":
    raise SystemExit(main())
