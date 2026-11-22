"""Target-conditioned two-code affine screen with frozen five-pair suffixes."""
import hashlib
import json
import random
import sys
import time
from pathlib import Path
import psutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0,str(ROOT))
import run_n41_disjoint_s5_sat as source

GEO = ROOT/"n41_w8_fixed_sum_table_20261009"/"geometry.json"
ORD = ROOT/"n41_w8_fixedseed_ordinary_join_20261013"/"audit_result.json"
INPUT = ROOT/"n41_w8_fixedseed_ordinary_join_20261013"/"protocol.json"


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def basis_for(values):
    anchor = min(values)
    pivots = {}
    for v in values:
        v ^= anchor
        while v:
            bit = v.bit_length()-1
            if bit not in pivots:
                pivots[bit] = v
                break
            v ^= pivots[bit]
    return anchor,pivots


def contains(basis,target):
    anchor,pivots = basis
    value = target ^ anchor
    while value:
        bit = value.bit_length()-1
        if bit not in pivots:return False
        value ^= pivots[bit]
    return True


def affine_rank(values): return len(basis_for(values)[1])


def main():
    protocol = json.loads((HERE/"target_protocol_v2.json").read_text())
    for path,digest in protocol["sources"].items():
        assert sha(path) == digest, path
    started = time.monotonic_ns()
    process = psutil.Process()
    peak = 0
    g = json.loads(GEO.read_text())
    ordinary = json.loads(ORD.read_text())
    inp = json.loads(INPUT.read_text())
    field = source.Field(41,[0,3])
    curve = source.Curve(field,0)
    raw_target = tuple(inp["raw_target"])
    families = []
    for line in (HERE/"cases.jsonl").read_text().splitlines():
        row = json.loads(line)
        family = (row["left_code"],row["right_code"])
        outputs = set(row["reciprocal_coordinates"])
        basis = basis_for(outputs)
        assert len(outputs) == 8 and len(basis[1]) == 7
        families.append((family,outputs,basis))
    rng = random.Random(protocol["suffix_seed"])
    suffixes = [("witness",[row["state_id"] for row in ordinary["states"][2:]])]
    while len(suffixes) <= protocol["random_suffix_count"]:
        ids = [rng.randrange(160) for _ in range(5)]
        cols = [col for k,sid in enumerate(ids,2)
                for col in g["blocks"][k]["states"][sid]["columns"]]
        if len(set(cols)) == 10:
            suffixes.append(("random",ids))
    results = []
    residual_z = []
    for kind,ids in suffixes:
        peak = max(peak,process.memory_info().rss)
        assert peak < protocol["rss_cap_bytes"]
        assert time.monotonic_ns()-started < protocol["wall_cap_seconds"]*10**9
        suffix = None
        for k,sid in enumerate(ids,2):
            suffix = curve.add(suffix,tuple(g["blocks"][k]["states"][sid]["raw_sum"]))
        neg_suffix = None if suffix is None else (suffix[0],suffix[0]^suffix[1])
        residual = curve.add(raw_target,neg_suffix)
        assert residual is not None and residual[0] != 0
        z = field.inv(residual[0])
        residual_z.append(z)
        exact = []
        relaxed = []
        for code_pair,outputs,basis in families:
            if z in outputs: exact.append(code_pair)
            if contains(basis,z): relaxed.append(code_pair)
        assert set(map(tuple,exact)) <= set(map(tuple,relaxed))
        results.append({"kind":kind,"suffix_state_ids":ids,
                        "residual_raw_point":list(residual),
                        "residual_reciprocal":z,
                        "exact_code_pairs":exact,"affine_code_pairs":relaxed})
    witness = results[0]
    assert (24,37) in witness["exact_code_pairs"]
    assert (24,37) in witness["affine_code_pairs"]
    result = {"status":"PASS_N41_TARGET_CONDITIONED_TWO_CODE_SPAN_SCREEN",
              "candidate_id":None,"panel_size":len(results),
              "random_suffix_count":protocol["random_suffix_count"],
              "suffix_residual_affine_rank":affine_rank(residual_z[1:]),
              "total_exact_family_hits":sum(len(x["exact_code_pairs"]) for x in results),
              "total_affine_family_hits":sum(len(x["affine_code_pairs"]) for x in results),
              "witness_exact_hits":len(witness["exact_code_pairs"]),
              "witness_affine_hits":len(witness["affine_code_pairs"]),
              "panels":results,"peak_process_rss_sample_bytes":peak,
              "wall_ns":time.monotonic_ns()-started,
              "target_protocol_sha256":sha(HERE/"target_protocol_v2.json")}
    (HERE/"target_result_v2.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(result["status"],result["total_exact_family_hits"],
          result["total_affine_family_hits"],result["suffix_residual_affine_rank"],flush=True)


if __name__ == "__main__":main()
