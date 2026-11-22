"""Freeze W8 quadratic ideal census and prior censored attempts."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
table = PARENT / "n131_w18_allseed_fourpair_20261012/n41_diagonal/pairs.tsv"
sources = [HERE / name for name in ("census.cpp", "joint_core.hpp", "census", "run.py")]
sources += [table,
            PARENT / "n131_w18_allseed_fourpair_20261012/n41_diagonal/receipt.json",
            PARENT / "n131_w18_allseed_fourpair_20261012/n41_diagonal/audit_result.json",
            PARENT / "n41_product_region_span_gate_20261013/terminal.json",
            PARENT / "n41_w8_joint_partial_gate_v2_20261013/terminal.json",
            PARENT / "n41_w8_quadratic_partial_ideal_20261013/run_result.json",
            PARENT / "n41_w8_quadratic_partial_ideal_v2_20261013/run_result.json"]
protocol = {"status": "FROZEN", "kind": "n41_w8_quadratic_two_pair_family_ideal_v3",
            "curve_id": "EC1N41Ckb1h7d5e80d3c4d0",
            "source_table": str(table),
            "witness_state_ids": [17678, 155, 6169, 16990],
            "raw_target_index": 1,
            "free_state_bit_levels": [2, 3, 4, 5],
            "sampled_region_quadruples_per_tested_level": 64,
            "sampling_seed_base": 202610140300,
            "worker_count": 1, "wall_cap_seconds": 120,
            "rss_cap_bytes": 4294967296,
            "sources": {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                        for path in sources}}
with (HERE / "protocol.json").open("x") as stream:
    json.dump(protocol, stream, indent=2, sort_keys=True)
    stream.write("\n")
