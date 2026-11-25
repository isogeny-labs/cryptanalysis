#!/usr/bin/env python3
"""Run the autoresearcher independence checker on this repository's review records.

The precommitted plan calls the worked attack ``worked_attack`` and identifies
joints by ``id``; the shared checker calls those fields ``attack_plan`` and
``joint``. The blind attestation's ``blind_derivation_compliance`` maps to
``blind_from_respected``. Adapt only those fields in memory; never rewrite the
signed review inputs.
"""

from __future__ import annotations

import argparse
import pathlib
import sys

import yaml

HERE = pathlib.Path(__file__).resolve().parent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checker", type=pathlib.Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.checker.resolve().parent.parent))
    from tools import check_review_independence as shared

    plan = yaml.safe_load((HERE / "review-plan.yaml").read_text())["review_plan"]
    for joint in plan["joints"]:
        joint["attack_plan"] = joint["worked_attack"]
        joint["joint_description"] = joint["joint"]
        joint["joint"] = joint["id"]
    reports = []
    for task in ("TASK-20261102-1a2b3c", "TASK-20261102-4d5e6f"):
        path = HERE / task / "review-attestation.yaml"
        attestation = yaml.safe_load(path.read_text())
        if "blind_derivation_compliance" in attestation:
            attestation["blind_from_respected"] = attestation["blind_derivation_compliance"]
        reports.append((str(path), attestation))
    problems = shared.check(plan, reports)
    for problem in problems:
        print(problem)
    print(f"independence checker: {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
