"""Independent Sage replay of all two-code output sets and affine ranks."""
import hashlib
import importlib.util
import json
import time
from pathlib import Path
from sage.all import GF, matrix
import psutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OLD = ROOT / "n41_w8_fixed_sum_table_20261009" / "audit.py"
GEO = ROOT / "n41_w8_fixed_sum_table_20261009" / "geometry.json"
PRIOR_SAGE = ROOT / "n41_w8_sign_label_closure_20261013" / "sage_result.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rank_affine(values):
    values = sorted(set(values))
    anchor = values[0]
    rows = [[(value ^ anchor) >> i & 1 for i in range(41)]
            for value in values[1:]]
    return int(matrix(GF(2),rows).rank())


def main():
    frozen = json.loads((HERE/"audit_protocol.json").read_text())
    for path,digest in frozen["sources"].items():
        assert sha(path) == digest, path
    prior = json.loads(PRIOR_SAGE.read_text())
    assert prior["status"] == "PASS_INDEPENDENT_SAGE_N41_SEVENPAIR_ALL_STATES"
    assert prior["states_checked"] == 1120
    spec = importlib.util.spec_from_file_location("prior_curve_audit",OLD)
    old = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old)
    curve,elem,integer = old.sage_curve()
    g = json.loads(GEO.read_text())
    slots = [[curve(elem(s["raw_sum"][0]),elem(s["raw_sum"][1]))
              for s in g["blocks"][k]["states"]] for k in (0,1)]
    started = time.monotonic_ns()
    process = psutil.Process()
    peak = 0
    checked = 0
    with (HERE/"cases.jsonl").open() as lines:
        for line in lines:
            peak = max(peak,process.memory_info().rss)
            assert peak < frozen["rss_cap_bytes"]
            assert time.monotonic_ns()-started < frozen["wall_cap_seconds"]*10**9
            row = json.loads(line)
            i,j = row["left_code"],row["right_code"]
            assert set(g["blocks"][0]["states"][4*i]["columns"]).isdisjoint(
                g["blocks"][1]["states"][4*j]["columns"])
            xs,zs = set(),set()
            for a in slots[0][4*i:4*i+4]:
                for b in slots[1][4*j:4*j+4]:
                    point = a+b
                    assert point != curve(0) and point[0] != 0
                    xs.add(integer(point[0]))
                    zs.add(integer(1/point[0]))
            assert sorted(xs) == row["x_coordinates"]
            assert sorted(zs) == row["reciprocal_coordinates"]
            assert rank_affine(xs) == row["x_affine_rank"] == 7
            assert rank_affine(zs) == row["reciprocal_affine_rank"] == 7
            checked += 1
    assert checked == 1554
    result = {"status":"PASS_INDEPENDENT_SAGE_TWO_CODE_AFFINE_SPANS",
              "candidate_id":None,"families_checked":checked,
              "raw_group_sums_checked":checked*16,
              "ordinary_witness_family":[24,37],
              "cases_sha256":sha(HERE/"cases.jsonl"),
              "audit_protocol_sha256":sha(HERE/"audit_protocol.json"),
              "peak_process_rss_sample_bytes":peak,
              "wall_ns":time.monotonic_ns()-started}
    with (HERE/"audit_result.json").open("x") as out:
        json.dump(result,out,indent=2,sort_keys=True);out.write("\n")
    print(result["status"],checked,flush=True)


if __name__ == "__main__": main()
