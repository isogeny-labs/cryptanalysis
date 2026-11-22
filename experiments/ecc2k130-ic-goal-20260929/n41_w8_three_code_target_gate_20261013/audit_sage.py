"""Independent Sage replay of the full three-code affine gate panel."""
import hashlib
import importlib.util
import json
import time
from pathlib import Path

import psutil
from sage.all import GF, matrix

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
GEO = ROOT / "n41_w8_fixed_sum_table_20261009" / "geometry.json"
CASES = ROOT / "n41_w8_two_code_affine_span_20261013" / "cases.jsonl"
OLD = ROOT / "n41_w8_fixed_sum_table_20261009" / "audit.py"
INPUT = ROOT / "n41_w8_fixedseed_ordinary_join_20261013" / "protocol.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def low_basis(values):
    anchor = min(values)
    pivots = {}
    for v in values:
        v ^= anchor
        while v:
            bit = (v & -v).bit_length() - 1
            if bit not in pivots:
                pivots[bit] = v
                break
            v ^= pivots[bit]
    return anchor, pivots


def in_span(basis, value):
    anchor, pivots = basis
    value ^= anchor
    while value:
        bit = (value & -value).bit_length() - 1
        if bit not in pivots:
            return False
        value ^= pivots[bit]
    return True


def main():
    protocol = json.loads((HERE / "audit_protocol.json").read_text())
    for path, digest in protocol["sources"].items():
        assert sha(path) == digest, path
    result = json.loads((HERE / "result.json").read_text())
    geo = json.loads(GEO.read_text())
    inp = json.loads(INPUT.read_text())
    spec = importlib.util.spec_from_file_location("old_w8_sage_audit", OLD)
    old = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old)
    curve, elem, integer = old.sage_curve()
    points = [[curve(elem(s["raw_sum"][0]), elem(s["raw_sum"][1]))
               for s in block["states"]] for block in geo["blocks"]]
    raw_target = curve(elem(inp["raw_target"][0]), elem(inp["raw_target"][1]))
    families = []
    for line in CASES.read_text().splitlines():
        row = json.loads(line)
        i, j = row["left_code"], row["right_code"]
        cols = set(geo["blocks"][0]["states"][4*i]["columns"])
        cols.update(geo["blocks"][1]["states"][4*j]["columns"])
        values = set(row["reciprocal_coordinates"])
        assert matrix(GF(2), [[(v ^ min(values)) >> b & 1 for b in range(41)]
                              for v in values]).rank() == 7
        families.append((i, j, cols, values, low_basis(values)))
    start = time.monotonic_ns()
    process = psutil.Process()
    peak = 0
    total_checks = total_affine = total_exact = total_full = 0
    for panel in result["panels"]:
        peak = max(peak, process.memory_info().rss)
        assert peak < protocol["rss_cap_bytes"]
        assert time.monotonic_ns() - start < protocol["wall_cap_seconds"] * 10**9
        ids = panel["suffix_state_ids"]
        suffix = curve(0)
        suffix_cols = set()
        for k, sid in enumerate(ids, 3):
            suffix += points[k][sid]
            suffix_cols.update(geo["blocks"][k]["states"][sid]["columns"])
        target_after_suffix = raw_target - suffix
        eligible = [x for x in families if not (x[2] & suffix_cols)]
        affine, exact, full = [], [], []
        admissible = 0
        for c in range(40):
            cols3 = set(geo["blocks"][2]["states"][4*c]["columns"])
            if cols3 & suffix_cols:
                continue
            residuals = [target_after_suffix - points[2][4*c+k] for k in range(4)]
            zvalues = [None if p == curve(0) or p[0] == 0 else integer(1/p[0])
                       for p in residuals]
            for i, j, cols2, outputs, basis in eligible:
                if cols2 & cols3:
                    continue
                admissible += 1
                hit_offsets = [k for k, z in enumerate(zvalues)
                               if z is not None and in_span(basis, z)]
                if hit_offsets:
                    affine.append([i, j, c, hit_offsets])
                    exact_offsets = [k for k in hit_offsets if zvalues[k] in outputs]
                    if exact_offsets:
                        exact.append([i, j, c, exact_offsets])
                        for k in exact_offsets:
                            for u in range(4):
                                for v in range(4):
                                    if (points[0][4*i+u] + points[1][4*j+v]
                                            + points[2][4*c+k] + suffix) == raw_target:
                                        full.append([4*i+u, 4*j+v, 4*c+k])
        assert admissible == panel["admissible_code_triples"]
        assert affine == panel["affine_candidates"]
        assert exact == panel["exact_coordinate_candidates"]
        assert full == panel["full_point_matches"]
        total_checks += admissible * 4
        total_affine += len(affine)
        total_exact += len(exact)
        total_full += len(full)
    audit = {"status": "PASS_INDEPENDENT_SAGE_THREE_CODE_TARGET_GATE",
             "candidate_id": None, "panels_checked": len(result["panels"]),
             "admissible_code_triples_checked": result["total_admissible_code_triples"],
             "coordinate_membership_slots_checked": total_checks,
             "affine_candidates": total_affine, "exact_coordinate_candidates": total_exact,
             "full_point_matches": total_full,
             "peak_process_rss_sample_bytes": peak,
             "wall_ns": time.monotonic_ns() - start,
             "protocol_sha256": sha(HERE / "audit_protocol.json")}
    with (HERE / "audit_result.json").open("x") as out:
        json.dump(audit, out, indent=2, sort_keys=True)
        out.write("\n")
    print(audit["status"], total_checks, total_full, flush=True)


if __name__ == "__main__":
    main()
