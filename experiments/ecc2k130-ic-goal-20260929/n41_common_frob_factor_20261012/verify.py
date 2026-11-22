"""Read-only receipt and exact-count audit for common-Frobenius five-pair gate."""

import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
SOURCE = GOAL / "n131_w18_allseed_fourpair_20261012/n41_diagonal/pairs.tsv"
PARENT_CPP = GOAL / "n41_w8_ninepair_join_control_20261012/join9.cpp"
SUPPORT = GOAL / "n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv"
PUBLIC_PREIMAGES = GOAL / "n131_fixed_seed_eight_pair_circuit_20261010/target_preimages.json"
BASE = GOAL / "n41_w7_entropy_cubic_20261011/w8"
R41 = 549756390943
R131 = 680564733841876926932320129493409985129


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = read(HERE / "prepare_protocol.json")
    target = read(HERE / "target.json")
    assert p["sha256"] == {
        "source": sha(HERE / "prepare_sage.py"), "pairs": sha(SOURCE),
        "fixture": sha(BASE / "fixture.json"),
        "sage_runtime": sha(HERE / "sage_runtime_info.json")}
    assert target["status"] == "PASS_CHECKED_SAGE_TARGET_FACTOR"
    assert target["protocol_sha256"] == sha(HERE / "prepare_protocol.json")
    assert target["factor_mod_r"]*target["inverse_mod_r"] % R41 == 1
    assert target["public_point"] == [920359962848, 755404565011]
    q = read(HERE / "protocol.json")
    receipt = read(HERE / "result.json")
    assert q["sha256"] == {
        "runner": sha(HERE / "run.py"), "source": sha(HERE / "join5.cpp"),
        "binary": sha(HERE / "join5"), "pairs": sha(SOURCE),
        "parent_cpp": sha(PARENT_CPP), "target": sha(HERE / "target.json")}
    assert q["left_kept_cap"] == 2000000 and q["right_kept_cap"] == 5000000
    assert q["parent_time_cap_s"] == 180 and q["combined_rss_cap_bytes"] == 4*1024**3
    assert receipt["status"] == "HIT_PENDING_INDEPENDENT_REPLAY"
    assert receipt["stop_reason"] is None and receipt["exit_code"] == 0
    assert receipt["protocol_sha256"] == sha(HERE / "protocol.json")
    stdout = (HERE / "stdout.log").read_text()
    assert receipt["stdout_sha256"] == sha(HERE / "stdout.log")
    assert receipt["stderr_sha256"] == sha(HERE / "stderr.log")
    assert (HERE / "stderr.log").read_text() == ""
    assert [line for line in stdout.splitlines() if line.startswith("SOURCE_PASS ")] == [receipt["source_line"]]
    assert [line for line in stdout.splitlines() if line.startswith("LEFT_DONE ")] == [receipt["left_line"]]
    assert [line for line in stdout.splitlines() if line.startswith("HIT ")] == [receipt["hit_line"]]
    assert receipt["left_line"].split()[1] == "2000000"
    assert int(receipt["hit_line"].split()[8]) <= 5000000
    assert receipt["peak_combined_rss_bytes_sampled"] < 4*1024**3
    assert receipt["parent_wall_ns"] < 180*10**9
    ap = read(HERE / "audit_protocol.json")
    audit = read(HERE / "audit_result.json")
    assert ap["sha256"] == {
        "source": sha(HERE / "audit_sage.py"), "pairs": sha(SOURCE),
        "geometry": sha(BASE / "geometry.json"),
        "fixture": sha(BASE / "fixture.json"),
        "target": sha(HERE / "target.json"),
        "join_receipt": sha(HERE / "result.json"),
        "stdout": sha(HERE / "stdout.log"),
        "sage_runtime": sha(HERE / "sage_runtime_info.json")}
    assert audit["protocol_sha256"] == sha(HERE / "audit_protocol.json")
    assert audit["status"] == "PASS_INDEPENDENT_N41_COMMON_FROBENIUS_PUBLIC_RELATION"
    assert audit["public_point"] == target["public_point"]
    assert audit["transformed_target"] == target["transformed_target"]
    assert audit["rank_before"] == 6 and audit["rank_after"] == 7
    assert len(audit["source_pair_states"]) == 5 and audit["distinct_folded_columns"] == 10
    assert [z["state_id"] for z in audit["source_pair_states"]] == list(map(int, receipt["hit_line"].split()[1:6]))
    prior_columns = set()
    for name in ("n41_w8_sixpair_mitm_20261011", "n41_w8_ninepair_join_control_20261012",
                 "n41_w8_tenpair_xquotient_20261012"):
        data = read(GOAL / name / "audit_result.json")["relation_row"]
        prior_columns.update(int(z["column"]) for z in data) if isinstance(data, list) else prior_columns.update(map(int, data))
    for path in (GOAL / "n131_w18_allseed_fourpair_20261012/n41_diagonal/audit_result.json",
                 GOAL / "n131_w18_bucketed_public_20261012/bucket_audit_result.json"):
        data = read(path)["relation_row"]
        prior_columns.update(int(z["column"]) for z in data) if isinstance(data, list) else prior_columns.update(map(int, data))
    prefix = read(GOAL / "n41_source_prefix_joint_20261012/sage_audit_result.json")
    d3 = next(z for z in prefix["relations"] if z["label"] == "d3_random3")["relation_row"]
    prior_columns.update(int(z["column"]) for z in d3) if isinstance(d3, list) else prior_columns.update(map(int, d3))
    assert set(map(int, audit["relation_row"]))-prior_columns == {23, 37, 57, 85}
    np = read(HERE / "n131_projection_protocol.json")
    nt = read(HERE / "n131_projection_result.json")
    assert np["sha256"] == {"source": sha(HERE / "project_n131_sage.py"),
                            "public_preimages": sha(PUBLIC_PREIMAGES),
                            "sage_runtime": sha(HERE / "n131_sage_runtime_info.json")}
    assert nt["status"] == "PASS_CHECKED_SAGE_N131_COMMON_FACTOR_TARGET"
    assert nt["protocol_sha256"] == sha(HERE / "n131_projection_protocol.json")
    assert nt["factor_mod_r"]*nt["inverse_mod_r"] % R131 == 1
    assert nt["frobenius_shift"] == 16 and len(nt["raw_preimages"]) == 4
    assert nt["public_point"] == read(PUBLIC_PREIMAGES)["public_target"]
    sp = read(HERE / "source_projection_protocol.json")
    sr = read(HERE / "source_projection_result.json")
    assert sp["sha256"] == {"runner": sha(HERE / "project_source.py"),
                            "support": sha(SUPPORT),
                            "n41_audit": sha(HERE / "audit_result.json"),
                            "n131_target": sha(HERE / "n131_projection_result.json")}
    assert sr["status"] == "PASS_N131_FIVEPAIR_SOURCE_LOWER_BOUND"
    assert sr["protocol_sha256"] == sha(HERE / "source_projection_protocol.json")
    counts = Counter(int(line.split()[1]) for line in SUPPORT.read_text().splitlines())
    masks = sum(counts.values())
    states = 4*(masks*(masks-1)//2-sum(v*(v-1)//2 for v in counts.values()))
    incident = max(4*v*(masks-v) for v in counts.values())
    lower = 1
    for j in range(5):
        lower *= states-2*j*incident
    assert (masks, len(counts), states, incident) == (131307, 131068, 34482792912, 2100848)
    assert int(sr["ordered_fivepair_distinct_column_lower_bound"]) == lower
    assert int(sr["uniform_target_mean_lower_bound_denominator"]) == R131
    assert int(sr["fixed_list_2m_by_5m_uniform_hit_numerator"]) == 10**13
    assert "does not depend on any axioms" in (HERE / "lean_check.txt").read_text()
    assert "does not depend on any axioms" in (HERE / "five_pair_lean_check.txt").read_text()
    print("PASS_COMMON_FROBENIUS_N41_RELATION_AND_N131_PROJECTION", audit["rank_after"])


if __name__ == "__main__":
    main()
