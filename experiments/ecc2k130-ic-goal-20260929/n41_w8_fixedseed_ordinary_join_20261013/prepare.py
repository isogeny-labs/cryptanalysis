"""Freeze the archived ordinary N41 point against the fixed-seed W8 states."""
import hashlib
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
GOAL = ROOT
sys.path.insert(0, str(GOAL))
import run_n41_disjoint_s5_sat as source

GEO = ROOT / "n41_w8_fixed_sum_table_20261009" / "geometry.json"
PUBLIC = ROOT / "n41_adjacent_pairpair" / "public_target.json"
R = 549756390943


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    g = json.loads(GEO.read_text())
    p = json.loads(PUBLIC.read_text())
    assert g["status"] == "EXACT_FIXED_SUM_GEOMETRY"
    assert g["curve_id"] == p["curve_id"] == "EC1N41Ckb1h7d5e80d3c4d0"
    assert g["pair_states_per_block"] == 160 and len(g["blocks"]) == 7
    field = source.Field(41, [0, 3])
    curve = source.Curve(field, 0)
    Q = tuple(p["target_q"])
    assert curve.mul(R, Q) is None
    raw = curve.mul(pow(4, -1, R), Q)
    assert raw is not None and curve.mul(4, raw) == Q
    lines = ["ECC2K41 7 160 1", f"T 0 {raw[0]} {raw[1]}"]
    for slot, block in enumerate(g["blocks"]):
        assert len(block["states"]) == 160
        for sid, state in enumerate(block["states"]):
            edge = sid // 4
            assert state["a"] == g["permitted_canonical_a"][edge]
            cols = state["columns"]
            x, y = state["raw_sum"]
            lines.append(f"S {slot} {sid} {edge} {cols[0]} {cols[1]} {x} {y}")
    rng = random.Random(202610132018)
    for _ in range(128):
        a = tuple(g["blocks"][rng.randrange(7)]["states"][rng.randrange(160)]["raw_sum"])
        b = tuple(g["blocks"][rng.randrange(7)]["states"][rng.randrange(160)]["raw_sum"])
        c = curve.add(a, b)
        lines.append(f"C {a[0]} {a[1]} {b[0]} {b[1]} {c[0] if c else -1} {c[1] if c else -1}")
    input_path = HERE / "input.tsv"
    input_path.write_text("\n".join(lines) + "\n")
    frozen = {"status": "FROZEN_BEFORE_ORDINARY_JOIN",
              "candidate_id": None, "curve_id": g["curve_id"],
              "public_target": list(Q), "raw_target": list(raw),
              "source_sha256": {str(x.relative_to(ROOT)): sha(x) for x in [GEO, PUBLIC]},
              "input_sha256": sha(input_path), "state_rows": 1120,
              "group_addition_checks": 128,
              "one_worker": True, "wall_cap_seconds": 180,
              "rss_cap_bytes": 4*1024**3,
              "query_scope": "one archived ordinary N41 public point, fixed W8 seed 56 and seven rotations"}
    (HERE / "protocol.json").write_text(json.dumps(frozen, indent=2, sort_keys=True)+"\n")
    print("FROZEN_N41_W8_ORDINARY_JOIN", sha(input_path))


if __name__ == "__main__":
    main()
