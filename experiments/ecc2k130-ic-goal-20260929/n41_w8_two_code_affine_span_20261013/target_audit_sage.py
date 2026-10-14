"""Independent Sage replay of target residuals and full affine screen panel."""
import hashlib
import importlib.util
import json
import time
from pathlib import Path
from sage.all import GF, matrix
import psutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OLD = ROOT/"n41_w8_fixed_sum_table_20261009"/"audit.py"
GEO = ROOT/"n41_w8_fixed_sum_table_20261009"/"geometry.json"
ORD = ROOT/"n41_w8_fixedseed_ordinary_join_20261013"/"protocol.json"


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def lowbit_span_contains(values,target):
    values = sorted(set(values))
    anchor = values[0]
    pivots = {}
    for value in values[1:]:
        value ^= anchor
        while value:
            bit = (value & -value).bit_length()-1
            if bit not in pivots:
                pivots[bit] = value
                break
            value ^= pivots[bit]
    target ^= anchor
    while target:
        bit = (target & -target).bit_length()-1
        if bit not in pivots:return False
        target ^= pivots[bit]
    return True


def main():
    frozen = json.loads((HERE/"target_audit_protocol.json").read_text())
    for path,digest in frozen["sources"].items():
        assert sha(path) == digest, path
    spec = importlib.util.spec_from_file_location("prior_curve_audit",OLD)
    old = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old)
    curve,elem,integer = old.sage_curve()
    g = json.loads(GEO.read_text())
    raw = json.loads(ORD.read_text())["raw_target"]
    T = curve(elem(raw[0]),elem(raw[1]))
    panels = json.loads((HERE/"target_result_v2.json").read_text())["panels"]
    families = {}
    for line in (HERE/"cases.jsonl").read_text().splitlines():
        row = json.loads(line)
        families[(row["left_code"],row["right_code"])] = set(row["reciprocal_coordinates"])
    assert len(families) == 1554 and len(panels) == 65
    started = time.monotonic_ns()
    process = psutil.Process()
    peak = 0
    residuals = []
    for panel in panels:
        peak = max(peak,process.memory_info().rss)
        assert peak < frozen["rss_cap_bytes"]
        assert time.monotonic_ns()-started < frozen["wall_cap_seconds"]*10**9
        ids = panel["suffix_state_ids"]
        assert len(ids) == 5
        cols = [col for k,sid in enumerate(ids,2)
                for col in g["blocks"][k]["states"][sid]["columns"]]
        assert len(set(cols)) == 10
        suffix = curve(0)
        for k,sid in enumerate(ids,2):
            point = g["blocks"][k]["states"][sid]["raw_sum"]
            suffix += curve(elem(point[0]),elem(point[1]))
        residual = T-suffix
        assert residual != curve(0) and residual[0] != 0
        coords = [integer(residual[0]),integer(residual[1])]
        assert coords == panel["residual_raw_point"]
        z = integer(1/residual[0])
        assert z == panel["residual_reciprocal"]
        residuals.append(z)
        exact = []
        relaxed = []
        for pair,values in families.items():
            if z in values:exact.append(pair)
            if lowbit_span_contains(values,z):relaxed.append(pair)
        assert sorted(map(list,exact)) == sorted(panel["exact_code_pairs"])
        assert sorted(map(list,relaxed)) == sorted(panel["affine_code_pairs"])
    anchor = residuals[1]
    rows = [[(value^anchor)>>i&1 for i in range(41)] for value in residuals[2:]]
    rank = int(matrix(GF(2),rows).rank())
    assert rank == 41
    assert panels[0]["exact_code_pairs"] == [[24,37]]
    assert panels[0]["affine_code_pairs"] == [[24,37]]
    result = {"status":"PASS_INDEPENDENT_SAGE_TARGET_SPAN_SCREEN",
              "candidate_id":None,"panels_checked":len(panels),
              "family_membership_checks":len(panels)*len(families),
              "random_suffix_affine_rank":rank,
              "total_exact_hits":sum(len(x["exact_code_pairs"]) for x in panels),
              "total_affine_hits":sum(len(x["affine_code_pairs"]) for x in panels),
              "target_audit_protocol_sha256":sha(HERE/"target_audit_protocol.json"),
              "peak_process_rss_sample_bytes":peak,
              "wall_ns":time.monotonic_ns()-started}
    with (HERE/"target_audit_result.json").open("x") as out:
        json.dump(result,out,indent=2,sort_keys=True);out.write("\n")
    print(result["status"],len(panels),rank,flush=True)


if __name__ == "__main__":main()
