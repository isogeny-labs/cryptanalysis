"""Bind the exact N41 finite-family join and its independent Sage replay."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
GEOMETRY = ROOT / "n41_two_free_pair_occupancy_20261009/geometry_snapshot.json"
ARITHMETIC = ROOT / "n41_two_free_pair_occupancy_20261009/arithmetic_snapshot.py"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


def main():
    p, result = read("protocol.json"), read("result.json")
    sp, sage = read("sage_protocol.json"), read("sage_audit.json")
    assert p["status"] == "FROZEN_N41_FINITE_FAMILY_TARGET_JOIN"
    assert p["sha256"] == {"source": sha(HERE / "run.py"),
                           "geometry": sha(GEOMETRY),
                           "arithmetic": sha(ARITHMETIC)}
    assert sp["status"] == "FROZEN_N41_FINITE_JOIN_SAGE_AUDIT"
    assert sp["sha256"] == {"source": sha(HERE / "sage_audit.py"),
                            "result": sha(HERE / "result.json"),
                            "geometry": sha(GEOMETRY),
                            "runtime": sha(HERE / "sage_runtime_info.json")}
    assert result["status"] == "COMPLETE"
    assert sage["status"] == "PASS_INDEPENDENT_SAGE_FINITE_JOIN"
    assert result["curve_id"] == p["curve_id"] == sp["curve_id"]
    assert result["protocol_sha256"] == sha(HERE / "protocol.json")
    assert result["source_sha256"] == sha(HERE / "run.py")
    assert sage["protocol_sha256"] == sha(HERE / "sage_protocol.json")
    assert result["families"] == sage["families"] == 1620
    assert result["family_x_roots"] == 12960
    assert result["full_ordered_family_pairs"] == 2624400
    assert result["targets"]["constructed_positive"]["ordered_disjoint_family_hits"] == 54
    assert result["targets"]["frozen_public"]["ordered_disjoint_family_hits"] == 0
    for name in ("constructed_positive", "frozen_public"):
        actual, replay = result["targets"][name], sage["targets"][name]
        assert actual["root_probes"] == 25920
        assert all(actual[k] == replay[k] for k in replay)
    assert result["elapsed_ns"] < p["cap_seconds"] * 10**9
    assert result["peak_rss_bytes"] < p["rss_cap_bytes"]
    assert sage["elapsed_ns"] < sp["cap_seconds"] * 10**9
    assert sage["peak_rss_bytes"] < sp["rss_cap_bytes"]
    output = {"status": "PASS_N41_FINITE_FAMILY_TARGET_JOIN",
              "producer_sha256": sha(HERE / "result.json"),
              "sage_sha256": sha(HERE / "sage_audit.json"),
              "positive_ordered_disjoint_family_hits": 54,
              "public_ordered_disjoint_family_hits": 0,
              "root_probes_per_target": 25920,
              "ordered_family_pairs": 2624400}
    (HERE / "verification.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps(output, sort_keys=True))


if __name__ == "__main__":
    main()
