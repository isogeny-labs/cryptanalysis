"""Exact two-code output spans for adjacent fixed-seed W8 pair slots."""
import hashlib
import json
import sys
import time
from collections import Counter
from pathlib import Path
import psutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
import run_n41_disjoint_s5_sat as source

GEO = ROOT / "n41_w8_fixed_sum_table_20261009" / "geometry.json"
ORDINARY = ROOT / "n41_w8_fixedseed_ordinary_join_20261013" / "audit_result.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def affine_rank(values):
    values = sorted(set(values))
    if not values: return None
    anchor = values[0]
    pivots = {}
    for value in values[1:]:
        value ^= anchor
        while value:
            bit = value.bit_length()-1
            if bit not in pivots:
                pivots[bit] = value
                break
            value ^= pivots[bit]
    return len(pivots)


def main():
    frozen = json.loads((HERE / "protocol.json").read_text())
    for name,digest in frozen["sources"].items():
        assert sha(Path(name)) == digest, name
    started = time.monotonic_ns()
    process = psutil.Process()
    peak_rss = 0
    g = json.loads(GEO.read_text())
    field = source.Field(41,[0,3])
    curve = source.Curve(field,0)
    hit = json.loads(ORDINARY.read_text())["states"]
    hit_pair = [hit[0]["state_id"]//4,hit[1]["state_id"]//4]
    counts = Counter()
    rows = 0
    exceptions = 0
    hit_row = None
    output = HERE / "cases.jsonl"
    with output.open("x") as out:
        for i in range(40):
            left = g["blocks"][0]["states"][4*i:4*i+4]
            for j in range(40):
                peak_rss = max(peak_rss,process.memory_info().rss)
                if peak_rss > frozen["rss_cap_bytes"]:
                    raise MemoryError("frozen RSS cap")
                if time.monotonic_ns()-started > frozen["wall_cap_seconds"]*10**9:
                    raise TimeoutError("frozen wall cap")
                right = g["blocks"][1]["states"][4*j:4*j+4]
                if set(left[0]["columns"]) & set(right[0]["columns"]):
                    counts["column_conflict"] += 1
                    continue
                xvalues = set()
                zvalues = set()
                for a in left:
                    for b in right:
                        P = curve.add(tuple(a["raw_sum"]),tuple(b["raw_sum"]))
                        if P is None or P[0] == 0:
                            exceptions += 1
                            continue
                        xvalues.add(P[0])
                        zvalues.add(field.inv(P[0]))
                xr = affine_rank(xvalues)
                zr = affine_rank(zvalues)
                record = {"left_code":i,"right_code":j,
                          "x_coordinates":sorted(xvalues),
                          "reciprocal_coordinates":sorted(zvalues),
                          "x_affine_rank":xr,"reciprocal_affine_rank":zr,
                          "raw_state_combinations":16}
                if [i,j] == hit_pair: hit_row = record
                out.write(json.dumps(record,sort_keys=True,separators=(",",":"))+"\n")
                counts[f"x_count_{len(xvalues)}"] += 1
                counts[f"x_rank_{xr}"] += 1
                counts[f"z_rank_{zr}"] += 1
                counts[f"z_count_{len(zvalues)}"] += 1
                rows += 1
    assert hit_row is not None and rows+counts["column_conflict"] == 1600
    result = {"status":"PASS_EXACT_N41_TWO_CODE_AFFINE_SPAN_CENSUS",
              "candidate_id":None,"curve_id":g["curve_id"],
              "family_pairs_checked":rows,"column_conflict_pairs":counts["column_conflict"],
              "exceptional_raw_combinations":exceptions,
              "histogram":dict(sorted(counts.items())),
              "ordinary_relation_first_two_codes":hit_pair,
              "ordinary_relation_family":hit_row,
              "cases_sha256":sha(output),"protocol_sha256":sha(HERE/"protocol.json"),
              "peak_process_rss_sample_bytes":peak_rss,
              "wall_ns":time.monotonic_ns()-started}
    (HERE/"result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(result["status"],rows,dict(sorted(counts.items())),flush=True)


if __name__ == "__main__": main()
