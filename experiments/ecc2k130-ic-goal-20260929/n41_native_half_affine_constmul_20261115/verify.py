"""Read-only custody and full-census check for the constant-multiply arm."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
BASE = EXP / "n41_cubic_product_inverse_20261024"
PREV = EXP / "n41_native_half_affine_20261114"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    receipt = json.loads((HERE / "abba_result.json").read_text())
    assert receipt["status"] == "PASS_FROZEN_N41_CONSTMUL_ABBA"
    assert receipt["protocol_sha256"] == sha(HERE / "protocol.json")
    paths = {
        "input": BASE / "n41_quotient_native_input_20261025.tsv",
        "constmul": HERE / "native_constmul.cpp",
        "prior_affine": PREV / "native_half_affine.cpp",
        "direct_rank": BASE / "n41_quotient_native_20261025.cpp",
        "sage_audit": BASE / "affine_gate_result.json",
        "runner": HERE / "run_abba.py",
    }
    for key, path in paths.items():
        assert sha(path) == protocol["sha256"][key], key
    assert [row["name"] for row in receipt["rows"]] == protocol["order"]
    sage = json.loads(paths["sage_audit"].read_text())
    for row in receipt["rows"]:
        name, result = row["name"], row["result"]
        assert row["binary_sha256"] == sha(HERE / ("native_" + name))
        assert result["families"] == protocol["expected"]["families"]
        assert result["gate_hits"] == 1
        assert result["hit"] == protocol["expected"]["hit"]
        assert result["query_s"] > 0 and result["setup_s"] > 0
        if name == "direct_rank":
            assert result["queries"] == 1989120
            continue
        assert result["half_survivors"] == protocol["expected"]["half_survivors"]
        assert result["retained"] == protocol["expected"]["retained"]
        assert result["source_checks"] == 3960
        assert result["half_survivors"] == sage["half_survivors"]
        assert result["retained"] == sage["families_retained"]
        for half in range(2):
            for rank, count in enumerate(result["rank_hist"][half]):
                assert count == int(sage["half_rank_histograms"][half].get(str(rank), 0))
    print("PASS_FROZEN_N41_CONSTMUL_RECEIPT")


if __name__ == "__main__":
    main()
