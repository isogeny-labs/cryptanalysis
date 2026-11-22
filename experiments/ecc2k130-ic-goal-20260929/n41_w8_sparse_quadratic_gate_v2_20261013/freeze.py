"""Freeze the exact sparse-quadratic N41 W8 census."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
TABLE = ROOT / "n131_w18_allseed_fourpair_20261012/n41_diagonal/pairs.tsv"
SOURCES = [HERE / "sparse.cpp", HERE / "sparse", HERE / "run.py", TABLE,
           ROOT / "n41_w8_quadratic_partial_ideal_v3_20261013/joint_core.hpp",
           ROOT / "n41_w8_ninepair_join_control_20261012/join9.cpp",
           ROOT / "n41_w8_quadratic_partial_ideal_v3_20261013/audit_result.json",
           ROOT / "n41_w8_sparse_quadratic_gate_20261013/run_result.json"]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


assert not (HERE / "protocol.json").exists()
record = {
    "status": "FROZEN",
    "kind": "n41_w8_two_pair_trace_reduced_sparse_quadratic_annihilator_census",
    "curve_id": "EC1N41Ckb1h7d5e80d3c4d0",
    "candidate_id": None,
    "source_table": str(TABLE),
    "public_raw_preimage_index": 1,
    "public_target_reciprocal": 344545435656,
    "witness_state_ids": [17678, 155, 6169, 16990],
    "region_width_per_slot": 16,
    "sample_count": 8,
    "sample_seed": 202610140304,
    "monomial_order": "constant; 40 coordinates i=1..40; i<j squarefree products; bit 0 checked trace-zero",
    "max_annihilator_support": 4,
    "worker_count": 1,
    "wall_cap_seconds": 120,
    "rss_cap_bytes": 4 * 1024**3,
    "compiler_command": ["c++", "-std=c++17", "-O3", "-DNDEBUG", "sparse.cpp", "-o", "sparse"],
    "sources": {str(path): sha(path) for path in SOURCES},
}
with (HERE / "protocol.json").open("x") as stream:
    json.dump(record, stream, indent=2, sort_keys=True)
    stream.write("\n")
print("FROZEN_N41_SPARSE_QUADRATIC")
