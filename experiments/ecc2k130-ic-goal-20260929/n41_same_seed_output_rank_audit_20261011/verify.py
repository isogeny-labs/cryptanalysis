"""Bind the frozen rank, trace, and independent Sage evidence."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
STAGE = ROOT / "n41_same_seed_output_rank_20261011"
GEOMETRY = ROOT / "n41_two_free_pair_occupancy_20261009/geometry_snapshot.json"
ARITH = ROOT / "n41_two_free_pair_occupancy_20261009/arithmetic_snapshot.py"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    rank_p = json.loads((STAGE / "protocol.json").read_text())
    rank = json.loads((STAGE / "result.json").read_text())
    trace_p = json.loads((STAGE / "trace_protocol.json").read_text())
    trace = json.loads((STAGE / "trace_result.json").read_text())
    sage_p = json.loads((STAGE / "sage_protocol.json").read_text())
    sage = json.loads((STAGE / "sage_audit.json").read_text())
    assert rank_p["sha256"] == {"source": sha(STAGE / "rank.py"),
                                "prior": sha(ROOT / "n41_same_seed_derivative_collapse_20261011/result_v2.json"),
                                "geometry": sha(GEOMETRY), "arithmetic": sha(ARITH)}
    assert rank["status"] == "COMPLETE"
    assert rank["protocol_sha256"] == sha(STAGE / "protocol.json")
    assert rank["source_sha256"] == sha(STAGE / "rank.py")
    assert rank["elapsed_ns"] / 1e9 < rank_p["cap_seconds"]
    assert rank["peak_rss_bytes"] < rank_p["rss_cap_bytes"]
    assert rank["key_rank_histogram"] == {"1:7": 810, "2:15": 324, "3:23": 54}
    assert rank["seed_affine_rank_histogram"] == {"40": 63}
    assert rank["distinct_x_by_key_sum"] == 12960
    assert trace_p["sha256"] == {"source": sha(STAGE / "trace.py"),
                                 "rank": sha(STAGE / "result.json"),
                                 "geometry": sha(GEOMETRY),
                                 "arithmetic": sha(ARITH)}
    assert trace["status"] == "PASS_UNIVERSAL_TRACE_HYPERPLANE"
    assert trace["protocol_sha256"] == sha(STAGE / "trace_protocol.json")
    assert trace["source_sha256"] == sha(STAGE / "trace.py")
    assert trace["elapsed_ns"] / 1e9 < trace_p["cap_seconds"]
    assert trace["peak_rss_bytes"] < trace_p["rss_cap_bytes"]
    assert trace["trace_mask"] == 1 and trace["distinct_signed_x_checked"] == 12960
    assert trace["public_target_trace_bit"] == 0
    assert trace["extra_affine_equations_per_seed"] == 0
    assert sage_p["sha256"] == {"source": sha(STAGE / "sage_audit.py"),
                                "rank": sha(STAGE / "result.json"),
                                "trace": sha(STAGE / "trace_result.json"),
                                "geometry": sha(GEOMETRY),
                                "runtime": sha(STAGE / "sage_runtime_info.json")}
    assert json.loads((STAGE / "sage_runtime_info.json").read_text())["status"] == "verified"
    assert sage["status"] == "PASS_INDEPENDENT_SAGE_SHARED_SEED_RANK"
    assert sage["protocol_sha256"] == sha(STAGE / "sage_protocol.json")
    assert sage["key_rank_histogram"] == rank["key_rank_histogram"]
    assert sage["seed_affine_rank_histogram"] == rank["seed_affine_rank_histogram"]
    assert sage["trace_mask"] == 1 and sage["distinct_x_checked"] == 12960
    assert sage["elapsed_ns"] / 1e9 < sage_p["cap_seconds"]
    assert sage["peak_rss_bytes"] < sage_p["rss_cap_bytes"]
    out = {"status": "PASS_N41_SHARED_SEED_AFFINE_BOUNDARY",
           "key_rank_histogram": rank["key_rank_histogram"],
           "seed_affine_rank_histogram": rank["seed_affine_rank_histogram"],
           "trace_mask": trace["trace_mask"],
           "rank_result_sha256": sha(STAGE / "result.json"),
           "trace_result_sha256": sha(STAGE / "trace_result.json"),
           "sage_result_sha256": sha(STAGE / "sage_audit.json")}
    (HERE / "verification.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps(out, sort_keys=True))


if __name__ == "__main__":
    main()
