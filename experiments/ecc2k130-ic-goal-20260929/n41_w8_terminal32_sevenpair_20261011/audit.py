"""Audit terminal-32 source count, native cap, Sage rank, and target recovery."""

import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BASE = ROOT / "n41_w8_sixpair_mitm_20261011"
GEOMETRY = ROOT / "n41_w7_entropy_cubic_20261011/w8/geometry.json"
R = 549756390943


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    query = json.loads((HERE / "query_result.json").read_text())
    sage = json.loads((HERE / "sage_audit_result.json").read_text())
    recovery = json.loads((HERE / "recovery_result.json").read_text())
    geometry = json.loads(GEOMETRY.read_text())
    assert protocol["status"] == "FROZEN_N41_SEVEN_PAIR_TERMINAL32"
    assert protocol["source_sha256"]["native_source"] == sha(HERE / "join7.cpp")
    assert protocol["source_sha256"]["native_binary"] == sha(HERE / "join7")
    assert protocol["source_sha256"]["input"] == sha(BASE / "join_input.tsv")
    assert protocol["source_sha256"]["geometry"] == sha(GEOMETRY)
    assert query["protocol_sha256"] == sha(HERE / "protocol.json")
    assert query["stdout_sha256"] == sha(HERE / "join.stdout.txt")
    assert query["stderr_sha256"] == sha(HERE / "join.stderr.txt")
    assert not (HERE / "join.stderr.txt").read_bytes()
    assert query["preflight_group_checks_passed"]
    assert query["status"] == "CENSORED_TIME" and query["stop_reason"] == "WALL_CAP"
    assert query["worker_count"] == 1 and query["raw_preimage_index"] == 0
    assert query["peak_combined_rss_bytes_sampled"] < protocol["combined_rss_cap_bytes"]
    assert query["wall_ns_exploratory"] >= protocol["parent_wall_cap_seconds"] * 10**9
    assert sage["status"] == "PASS_INDEPENDENT_N41_TERMINAL32_RELATIONS"
    assert sage["source_sha256"]["query"] == sha(HERE / "query_result.json")
    assert recovery["status"] == "PASS_TERMINAL32_N41_TARGET_SCALAR_RECOVERY"
    assert recovery["source_sha256"]["relations"] == sha(HERE / "sage_audit_result.json")
    assert recovery["verified_relation_count"] == sage["verified_hits"] == len(query["hit_lines"]) == 2
    assert sage["rank_from_empty_matrix"] == recovery["rank_from_empty_matrix"] == 2
    assert [row["novel_rank"] for row in sage["replayed"]] == [1, 1]
    assert recovery["recovered_scalar_mod_r"] == "445577591162"
    assert recovery["independent_scalar_replay"]
    rows = {int(row["mask"]): row for row in geometry["rows"]}
    edges = [(a, a ^ 184) for a in sorted(rows)
             if a < (a ^ 184) and a ^ 184 in rows
             and rows[a]["column"] != rows[a ^ 184]["column"]]
    columns = [int(rows[mask]["column"]) for edge in edges for mask in edge]
    assert len(edges) == 35 and len(columns) == len(set(columns)) == 70
    exact_source = 32 * math.perm(34, 6) * 4**6
    assert str(exact_source) == protocol["source_count_distinct_column_ordered_tuples"]
    assert all(row["state_ids"][-1] < 32 for row in sage["replayed"])
    lines = (HERE / "join.stdout.txt").read_text().splitlines()
    assert lines[0].startswith("CHECK_PASS 128 ")
    assert any(line.startswith("LEFT_DONE 2513280 ") for line in lines)
    assert [line for line in lines if line.startswith("HIT ")] == query["hit_lines"]
    assert not any(line.startswith(("COMPLETE_HITS ", "MISS_COMPLETE ")) for line in lines)
    left_seconds = float(next(line.split()[-1] for line in lines if line.startswith("LEFT_DONE ")))
    hit_seconds = [float(line.split()[-1]) for line in query["hit_lines"]]
    assert hit_seconds[0] > left_seconds and hit_seconds == sorted(hit_seconds)
    result = {"status": "PASS_N41_TERMINAL32_CENSORED_RANK_AND_RECOVERY_AUDIT",
              "candidate_id": None,
              "curve_id": protocol["curve_id"],
              "public_target_transported": protocol["public_target_transported"],
              "uniform_raw_point_mean_upper": protocol["uniform_raw_point_mean_upper_decimal"],
              "verified_relations": sage["verified_hits"],
              "novel_rank": sage["rank_from_empty_matrix"],
              "recovered_scalar_mod_r": recovery["recovered_scalar_mod_r"],
              "precompute_left_table_seconds_exploratory": left_seconds,
              "first_hit_after_table_seconds_exploratory": hit_seconds[0]-left_seconds,
              "second_hit_after_table_seconds_exploratory": hit_seconds[1]-left_seconds,
              "query_status": query["status"],
              "source_sha256": {"script": sha(Path(__file__)),
                                "protocol": sha(HERE / "protocol.json"),
                                "query": sha(HERE / "query_result.json"),
                                "sage": sha(HERE / "sage_audit_result.json"),
                                "recovery": sha(HERE / "recovery_result.json")}}
    with (HERE / "audit_result.json").open("x") as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write("\n")
    print(result["status"], result["verified_relations"], result["novel_rank"])


if __name__ == "__main__":
    main()
