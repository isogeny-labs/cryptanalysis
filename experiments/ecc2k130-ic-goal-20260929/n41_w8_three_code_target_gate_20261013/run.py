"""Target-conditioned third-code prefilter against exact two-code coordinate spans."""
import hashlib
import json
import random
import sys
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
import run_n41_disjoint_s5_sat as source

GEO = ROOT / "n41_w8_fixed_sum_table_20261009" / "geometry.json"
ORD = ROOT / "n41_w8_fixedseed_ordinary_join_20261013" / "audit_result.json"
INPUT = ROOT / "n41_w8_fixedseed_ordinary_join_20261013" / "protocol.json"
CASES = ROOT / "n41_w8_two_code_affine_span_20261013" / "cases.jsonl"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def neg(point):
    return None if point is None else (point[0], point[0] ^ point[1])


def basis_for(values):
    anchor = min(values)
    pivots = {}
    for value in values:
        value ^= anchor
        while value:
            bit = value.bit_length() - 1
            if bit not in pivots:
                pivots[bit] = value
                break
            value ^= pivots[bit]
    return anchor, pivots


def contains(basis, value):
    anchor, pivots = basis
    value ^= anchor
    while value:
        bit = value.bit_length() - 1
        if bit not in pivots:
            return False
        value ^= pivots[bit]
    return True


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    for path, digest in protocol["sources"].items():
        assert sha(path) == digest, path
    assert json.loads((HERE / "sage_runtime_info.json").read_text())["status"] == "verified"
    start = time.monotonic_ns()
    process = psutil.Process()
    peak = 0
    phase = {"basis_build_ns": 0, "target_residual_ns": 0,
             "membership_ns": 0, "point_check_ns": 0}
    geo = json.loads(GEO.read_text())
    ordinary = json.loads(ORD.read_text())
    inp = json.loads(INPUT.read_text())
    field = source.Field(41, [0, 3])
    curve = source.Curve(field, 0)
    raw_target = tuple(inp["raw_target"])
    suffix_witness = [state["state_id"] for state in ordinary["states"][3:]]
    assert len(suffix_witness) == 4
    begin = time.monotonic_ns()
    families = []
    for line in CASES.read_text().splitlines():
        row = json.loads(line)
        i, j = row["left_code"], row["right_code"]
        cols = set(geo["blocks"][0]["states"][4 * i]["columns"])
        cols.update(geo["blocks"][1]["states"][4 * j]["columns"])
        values = set(row["reciprocal_coordinates"])
        assert len(cols) == 4 and len(values) == 8
        basis = basis_for(values)
        assert len(basis[1]) == 7
        families.append((i, j, cols, values, basis))
    phase["basis_build_ns"] = time.monotonic_ns() - begin

    rng = random.Random(protocol["suffix_seed"])
    suffixes = [("witness", suffix_witness)]
    while len(suffixes) <= protocol["random_suffix_count"]:
        ids = [rng.randrange(160) for _ in range(4)]
        cols = [col for k, sid in enumerate(ids, 3)
                for col in geo["blocks"][k]["states"][sid]["columns"]]
        if len(set(cols)) == 8:
            suffixes.append(("random", ids))

    panels = []
    for kind, ids in suffixes:
        peak = max(peak, process.memory_info().rss)
        assert peak < protocol["rss_cap_bytes"]
        assert time.monotonic_ns() - start < protocol["wall_cap_seconds"] * 10**9
        begin = time.monotonic_ns()
        suffix = None
        suffix_cols = set()
        for k, sid in enumerate(ids, 3):
            state = geo["blocks"][k]["states"][sid]
            suffix_cols.update(state["columns"])
            suffix = curve.add(suffix, tuple(state["raw_sum"]))
        target_after_suffix = curve.add(raw_target, neg(suffix))
        eligible = [family for family in families if not (family[2] & suffix_cols)]
        third = []
        for c in range(40):
            states = geo["blocks"][2]["states"][4*c:4*c+4]
            cols = set(states[0]["columns"])
            if cols & suffix_cols:
                continue
            residuals = []
            for state in states:
                residual = curve.add(target_after_suffix, neg(tuple(state["raw_sum"])))
                residuals.append(None if residual is None or residual[0] == 0
                                 else field.inv(residual[0]))
            third.append((c, cols, residuals))
        phase["target_residual_ns"] += time.monotonic_ns() - begin
        begin = time.monotonic_ns()
        admissible = 0
        affine = []
        exact = []
        for c, cols3, residuals in third:
            for i, j, cols2, values, basis in eligible:
                if cols2 & cols3:
                    continue
                admissible += 1
                state_offsets = [k for k, value in enumerate(residuals)
                                 if value is not None and contains(basis, value)]
                if state_offsets:
                    affine.append([i, j, c, state_offsets])
                    exact_offsets = [k for k in state_offsets if residuals[k] in values]
                    if exact_offsets:
                        exact.append([i, j, c, exact_offsets])
        phase["membership_ns"] += time.monotonic_ns() - begin
        begin = time.monotonic_ns()
        full = []
        for i, j, c, offsets in exact:
            for k in offsets:
                point3 = tuple(geo["blocks"][2]["states"][4*c+k]["raw_sum"])
                for u in range(4):
                    point1 = tuple(geo["blocks"][0]["states"][4*i+u]["raw_sum"])
                    for v in range(4):
                        point2 = tuple(geo["blocks"][1]["states"][4*j+v]["raw_sum"])
                        if curve.add(curve.add(curve.add(point1, point2), point3), suffix) == raw_target:
                            full.append([4*i+u, 4*j+v, 4*c+k])
        phase["point_check_ns"] += time.monotonic_ns() - begin
        panels.append({"kind": kind, "suffix_state_ids": ids,
                       "admissible_code_triples": admissible,
                       "affine_candidates": affine, "exact_coordinate_candidates": exact,
                       "full_point_matches": full})

    witness = panels[0]
    expected = [state["state_id"] for state in ordinary["states"][:3]]
    assert expected in witness["full_point_matches"]
    assert witness["affine_candidates"] == [[24, 37, 10, [2]]]
    assert witness["exact_coordinate_candidates"] == [[24, 37, 10, [2]]]
    result = {"status": "PASS_N41_THREE_CODE_TARGET_GATE",
              "candidate_id": None, "curve_id": geo["curve_id"],
              "panel_count": len(panels), "random_suffix_count": protocol["random_suffix_count"],
              "families": len(families), "panels": panels,
              "total_admissible_code_triples": sum(x["admissible_code_triples"] for x in panels),
              "total_affine_candidates": sum(len(x["affine_candidates"]) for x in panels),
              "total_exact_coordinate_candidates": sum(len(x["exact_coordinate_candidates"]) for x in panels),
              "total_full_point_matches": sum(len(x["full_point_matches"]) for x in panels),
              "phase_ns": phase, "wall_ns": time.monotonic_ns() - start,
              "peak_process_rss_sample_bytes": peak,
              "protocol_sha256": sha(HERE / "protocol.json")}
    with (HERE / "result.json").open("x") as out:
        json.dump(result, out, indent=2, sort_keys=True)
        out.write("\n")
    print(result["status"], result["total_admissible_code_triples"],
          result["total_affine_candidates"], result["total_full_point_matches"], flush=True)


if __name__ == "__main__":
    main()
