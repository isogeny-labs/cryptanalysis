#!/usr/bin/env python3
"""Write the frozen run order (`schedule.json`) from `protocol.json`.

Segments, in order:

This is the parent's `make_schedule.py` (`koblitz-n83-indexbuild2-20261020`,
itself the Tier 1 template's, `koblitz-n83-closure-indexlift-rep-20261020`)
with this experiment's arms and one more sub-block. Side A = kM38IC then
cM38IC (the row's producer, round-2 index build), side B = kM38OF then
cM38OF (the online-frame producer, `KIC_ONLINE_SOLVE=frame`), Baa = kM38OFaa
then cM38OFaa; a planted pair of COLD processes cM38OF and cM38OFX
(`frame_s3plant`); and, new, a layout pair of COLD processes cM38OS and
cM38OF (the online-frame BINARY with `KIC_ONLINE_SOLVE=s3`, the parent's
online loop, against `frame`: the online ratio within one binary).

* `O1`: Q0 (B's validation point), one cold process each of `q0_arms`
  (both producers on all three bases, plus cM38OFX), shuffled by
  `random.Random(order_seed0 + 99)`. This is an exactness check against the
  archived and frozen identities, never timing evidence.
* `P<i>` (i = 1..points): point s<i-1> of `inputs/cold_targets.json`. The
  point's generator is `random.Random(order_seed0 + i - 1)`, and it draws, in
  this order:
  1. the start of the primary block (A or B);
  2. the start of the A/A block (B or Baa);
  3. the start of the planted block (cM38OF or cM38OFX);
  4. the start of the layout block (cM38OS or cM38OF);
  5. the order of the five sub-blocks (primary, aa, planted, layout, rho),
     by shuffle.

  The primary block is 2K sides in strict alternation (ABAB... or BABA...).
  Pair j (sides 2j-1 and 2j) uses rank seed rank_seeds[point][j-1] in both
  rank processes. The A/A block is 2 K_AA sides alternating B and Baa, and
  pair j uses the rank seed of primary pair j. The planted and layout blocks
  are one alternating pair of cold processes each (seed 7). The rho block
  is one rT process with seed rho_seed_base + point seed. Cold processes use
  seed 7, the parent's.

Every run carries `role` (q0, primary, aa, planted, rho), `pair`, `side` and
`position` (its side's index in its block), and the verifier reads them from
here. `--check` regenerates the schedule and requires byte identity with
the committed file.
"""

import argparse
import hashlib
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
TARGETS = HERE / "inputs" / "cold_targets.json"
B_TARGETS = HERE.parent / "koblitz-single-target-n83-tier1-20261014" / "inputs" / "targets.json"
COLD_SEED = 7


def alternate(first, second, start, pairs):
    """2 * pairs side labels in strict alternation from `start`."""
    other = second if start == first else first
    return [start if n % 2 == 0 else other for n in range(2 * pairs)]


def build(protocol):
    design = protocol["design"]
    if hashlib.sha256(TARGETS.read_bytes()).hexdigest() != protocol["sources"]["local_sha256"]["cold_targets"]:
        raise ValueError("cold_targets.json differs from the protocol's digest")
    points = sorted(json.loads(TARGETS.read_text())["points"], key=lambda e: e["seed"])
    if len(points) != design["points"]:
        raise ValueError("panel size differs from the protocol")
    q0 = json.loads(B_TARGETS.read_text())["q0"]["point"]
    if [str(v) for v in q0] != design["q0_point"]:
        raise ValueError("Q0 differs from the protocol")
    sides = design["sides"]
    k, k_aa = design["primary_pairs_per_point"], design["aa_pairs_per_point"]
    if design["planted_pairs_per_point"] != 1:
        raise ValueError("this schedule builder writes one planted pair per point")
    segments = []
    runs = [{"arm": arm, "point_id": "q0", "point": design["q0_point"], "seed": COLD_SEED, "role": "q0",
             "pair": None, "side": None, "position": None} for arm in design["q0_arms"]]
    random.Random(design["order_seed0"] + 99).shuffle(runs)
    segments.append({"id": "O1", "panel": "O", "block": 1, "runs": runs})
    for i, entry in enumerate(points):
        unit = "s%03d" % entry["seed"]
        seeds = design["rank_seeds"][unit]
        rng = random.Random(design["order_seed0"] + i)
        start_primary = rng.choice(["A", "B"])
        start_aa = rng.choice(["B", "Baa"])
        planted_arms = design["planted_arms"]
        start_planted = rng.choice(planted_arms)
        layout_arms = design["layout_arms"]
        start_layout = rng.choice(layout_arms)
        order = ["primary", "aa", "planted", "layout", "rho"]
        rng.shuffle(order)

        def run(arm, seed, role, pair, side, position):
            return {"arm": arm, "point_id": unit, "point": entry["point"], "seed": seed, "role": role,
                    "pair": pair, "side": side, "position": position}

        def side_runs(label, pair, role, position):
            rank_arm, cold_arm = sides[label]
            return [run(rank_arm, seeds[pair - 1], role, pair, label, position),
                    run(cold_arm, COLD_SEED, role, pair, label, position)]

        blocks = {"primary": [], "aa": [], "planted": [], "layout": [], "rho": []}
        for position, label in enumerate(alternate("A", "B", start_primary, k)):
            blocks["primary"] += side_runs(label, position // 2 + 1, "primary", position)
        for position, label in enumerate(alternate("B", "Baa", start_aa, k_aa)):
            blocks["aa"] += side_runs(label, position // 2 + 1, "aa", position)
        for position, arm in enumerate(alternate(planted_arms[0], planted_arms[1], start_planted, 1)):
            blocks["planted"].append(run(arm, COLD_SEED, "planted", 1, arm, position))
        for position, arm in enumerate(alternate(layout_arms[0], layout_arms[1], start_layout, 1)):
            blocks["layout"].append(run(arm, COLD_SEED, "layout", 1, arm, position))
        blocks["rho"].append(run("rT", design["rho_seed_base"] + entry["seed"], "rho", None, None, None))
        segment_runs = [r for name in order for r in blocks[name]]
        segments.append({"id": "P%d" % (i + 1), "panel": "P", "block": i + 1, "runs": segment_runs,
                         "sub_block_order": order,
                         "starts": {"primary": start_primary, "aa": start_aa, "planted": start_planted,
                                    "layout": start_layout}})
    serial = 0
    for segment in segments:
        for r in segment["runs"]:
            serial += 1
            r["serial"] = serial
    return {"schema": 1, "protocol_kind": protocol["kind"], "segments": segments, "runs": serial}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    protocol = json.loads((HERE / "protocol.json").read_text())
    text = json.dumps(build(protocol), indent=1, sort_keys=True) + "\n"
    path = HERE / "schedule.json"
    if args.check:
        if path.read_text() != text:
            raise SystemExit("schedule.json differs from the schedule the protocol defines")
        print("schedule_verified=" + str(path))
        return
    path.write_text(text)
    print(str(path))


if __name__ == "__main__":
    main()
