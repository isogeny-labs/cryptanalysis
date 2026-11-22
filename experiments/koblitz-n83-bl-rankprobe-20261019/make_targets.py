#!/usr/bin/env python3
"""Derive the new held-out cold panel before any timing.

`inputs/cold_targets.json`: COUNT public points from B's public hash-to-curve
law (beat `koblitz.compact_orbit.n83_single_target`, domain
`kic-n83-single-target-public-point-v1`) through the pinned harness
`single_target_panel.public_point` (crypto 770f6a69, restored into
`../koblitz-n83-rankprobe-20261019/snapshots/r770` by that experiment's
`restore.py`), with the new role ROLE and seeds 0..COUNT-1. No earlier run
has used this role, and no scalar is known for any of the points.

Every point must be in the prime-order subgroup, distinct, and different from
every n=83 panel of this law registered on origin or in a scratch worktree on
2026-10-19, all regenerated here from the same law:

* on origin/main: Q0 and B's fresh points (role `eval`,
  `../koblitz-single-target-n83-tier1-20261014/inputs/targets.json`),
  `scanorder-heldout` (384), `combined-primary-v1` (576),
  `probepipe-primary-v1` (384), `statefold-cold-v1` (16),
  `tablefilter-primary-v1` (384), `stacked-cold-v1` (20), `rankcut-cold-v1`
  (20), `rankprobe-cold-v1` (20) and the 64 `eval` points of
  `n131-ref-walk-20261015` (a superset of B's panel);
* in the scratch worktrees n83-indexlift, n83-rotkey, n83-k899,
  n83-onlineframe and n83-closure: `indexlift-cold-v1` (20 or 64 there),
  `rotkey-cold-v1` (20 or 128), `k899-cold-v1` (20 or 128),
  `onlineframe-v1` (64) and `closure-cold-v1` (20), each checked here to 256
  seeds so that a later enlargement of those panels stays disjoint;
* n83-knownlog had no panel when this file was written; the names it would
  most likely take (`knownlog-cold-v1`, `known-log-cold-v1`,
  `knownlog-v1`) are excluded to 256 seeds as well.

COUNT = 64 (`power_check.py`, `analysis/power.json`: the smallest panel in the
frozen grid whose median 95% interval of the online gap spans at most a
factor of 2). `--check` regenerates and compares byte for byte.
"""

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SNAPSHOT = HERE.parent / "koblitz-n83-rankprobe-20261019" / "snapshots" / "r770"
PRIMARY = HERE / "inputs" / "cold_targets.json"
B_TARGETS = HERE.parent / "koblitz-single-target-n83-tier1-20261014" / "inputs" / "targets.json"
BEAT = "koblitz.compact_orbit.n83_single_target"
ROLE = "blrankprobe-cold-v1"
COUNT = 64
EARLIER_ROLES = (("scanorder-heldout", 384), ("combined-primary-v1", 576), ("probepipe-primary-v1", 384),
                 ("statefold-cold-v1", 16), ("tablefilter-primary-v1", 384), ("stacked-cold-v1", 20),
                 ("rankcut-cold-v1", 20), ("rankprobe-cold-v1", 20), ("eval", 64))
SCRATCH_ROLES = (("indexlift-cold-v1", 256), ("rotkey-cold-v1", 256), ("k899-cold-v1", 256),
                 ("onlineframe-v1", 256), ("closure-cold-v1", 256), ("knownlog-cold-v1", 256),
                 ("known-log-cold-v1", 256), ("knownlog-v1", 256))


def harness():
    sys.path.insert(0, str(SNAPSHOT / "research/sat_factor_base_review_20260908/autolab"))
    import single_target_panel as panel  # noqa: E402  (pinned harness)

    beat = json.loads((SNAPSHOT / "research/sat_factor_base_review_20260908/autolab/protocol.json")
                      .read_text())["beats"][BEAT]
    return panel, beat, panel.cached_curve(dict(beat["curve_fixture"]))


def points_of(panel, beat, curve, role, count):
    domain = beat["target_law"]["domain"]
    points = []
    for seed in range(count):
        x, y = panel.public_point(curve, domain, role, seed)
        q = curve.decode([x, y])
        if q is None or curve.mul(q, curve.r) is not None:
            raise ValueError("%s point %d is not in the prime-order subgroup" % (role, seed))
        points.append({"seed": seed, "point": [str(x), str(y)]})
    if len({tuple(e["point"]) for e in points}) != count:
        raise ValueError("%s points repeat" % role)
    return points


def derive():
    panel, beat, curve = harness()
    primary = points_of(panel, beat, curve, ROLE, COUNT)
    used = json.loads(B_TARGETS.read_text())
    earlier = {tuple(used["q0"]["point"])} | {tuple(e["point"]) for e in used["panel_b"]["points"]}
    for role, count in EARLIER_ROLES + SCRATCH_ROLES:
        earlier |= {tuple(e["point"]) for e in points_of(panel, beat, curve, role, count)}
    if any(tuple(e["point"]) in earlier for e in primary):
        raise ValueError("a primary point equals a point of an earlier n=83 panel")
    return {"schema": 1, "beat_id": BEAT, "domain": beat["target_law"]["domain"], "role": ROLE,
            "input_law": panel.input_law(beat).replace("<role>", ROLE), "points": primary,
            "scalar_known_to_anyone": False,
            "disjoint_from": ["q0", "eval (B's panel_b, %d points)" % len(used["panel_b"]["points"])] +
                             ["%s (%d points, origin/main)" % rc for rc in EARLIER_ROLES] +
                             ["%s (%d points, scratch worktrees or reserved)" % rc for rc in SCRATCH_ROLES],
            "sized_by": "power_check.py (analysis/power.json)"}


def text(record):
    return json.dumps(record, indent=2, sort_keys=True) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    record = derive()
    if args.check:
        if PRIMARY.read_text() != text(record):
            raise SystemExit("inputs/cold_targets.json differs from the regenerated points")
        print("targets_verified=" + str(PRIMARY))
        return
    PRIMARY.write_text(text(record))
    print(str(PRIMARY))


if __name__ == "__main__":
    main()
