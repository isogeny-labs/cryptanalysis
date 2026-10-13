"""Read-only status correction and complete frozen-evidence integrity check."""
import hashlib
import json
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
PAIRS = GOAL / "n131_w18_allseed_fourpair_20261012/n41_diagonal/pairs.tsv"
SUPPORT = GOAL / "n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    frozen = json.loads((HERE / "terminal_protocol.json").read_text())
    files = {"script": HERE / "terminal_audit.py", "query_protocol": HERE / "protocol.json",
             "query_result": HERE / "result.json", "query_stdout": HERE / "stdout.log",
             "query_stderr": HERE / "stderr.log", "source": HERE / "triple.cpp",
             "binary": HERE / "triple", "pairs": PAIRS,
             "fixture_protocol": HERE / "fixture_protocol.json", "fixture": HERE / "fixture.json",
             "control_protocol": HERE / "control_protocol.json", "control_result": HERE / "control_result.json",
             "control_stdout": HERE / "control.stdout", "control_stderr": HERE / "control.stderr",
             "control_audit_protocol": HERE / "control_audit_protocol.json",
             "control_audit_result": HERE / "control_audit_result.json",
             "projection": HERE / "projection.json", "support": SUPPORT}
    assert frozen["status"] == "FROZEN_BEFORE_TERMINAL_AUDIT"
    assert frozen["sha256"] == {key: sha(path) for key,path in files.items()}
    p = json.loads((HERE / "protocol.json").read_text())
    q = json.loads((HERE / "result.json").read_text())
    assert q["protocol_sha256"] == sha(HERE / "protocol.json")
    assert q["stdout_sha256"] == sha(HERE / "stdout.log")
    assert q["stderr_sha256"] == sha(HERE / "stderr.log")
    assert q["status"] == "EXHAUSTED" and q["exit_code"] == 0 and q["stop_reason"] is None
    assert q["hit_line"] is None
    assert q["source_line"] == "SOURCE_PASS 1956 4"
    parts = q["index_line"].split()
    assert parts[:3] == ["INDEX_READY", "1583568", "1583568"]
    fields = q["exhausted_line"].split()
    assert fields[0] == "EXHAUSTED" and len(fields) == 7
    families, inner, point_matches, column_rejects = map(int, fields[1:5])
    setup_s, query_s = map(float, fields[5:7])
    assert (families,inner,point_matches,column_rejects) == (22304,29568392,12,12)
    assert families < int(parts[1]) and families < p["outer_family_cap"]
    assert p["worker_query_cap_s"] <= query_s < p["worker_query_cap_s"] + 1
    assert q["parent_wall_ns"] < p["parent_time_cap_s"] * 10**9
    assert q["peak_combined_rss_bytes_sampled"] < p["combined_rss_cap_bytes"]
    assert len([line for line in (HERE / "stdout.log").read_text().splitlines()
                if line.startswith("HIT ")]) == 0
    control = json.loads((HERE / "control_result.json").read_text())
    fixture = json.loads((HERE / "fixture.json").read_text())
    checked = json.loads((HERE / "control_audit_result.json").read_text())
    assert control["status"] == "HIT_PENDING_INDEPENDENT_REPLAY"
    assert control["hit_line"].split()[1:6] == list(map(str, fixture["selected_subset_ids"]))
    assert checked["status"] == "PASS_INDEPENDENT_CONSTRUCTED_THREEPAIR_CONTROL"
    assert checked["distinct_folded_columns"] == 10
    assert checked["projected_target"] == fixture["projected_target"]
    assert control["protocol_sha256"] == sha(HERE / "control_protocol.json")
    assert checked["protocol_sha256"] == sha(HERE / "control_audit_protocol.json")
    proj = json.loads((HERE / "projection.json").read_text())
    S=34482792912
    r=680564733841876926932320129493409985129
    assert proj["status"] == "PASS_EXACT_N131_TRIPLE_SOURCE_PROJECTION"
    assert proj["n131_support_sha256"] == sha(SUPPORT)
    assert Fraction(proj["n131_uniform_triple_completion_probability_upper_bound"]) == Fraction(S**3,r)
    assert Fraction(proj["n131_uniform_outer_families_for_expected_one_hit_lower_bound"]) == Fraction(r,S**3)
    assert int(proj["n131_literal_unordered_two_pair_index_entries"]) == S*(S-1)//2
    audited={"status":"PASS_THREEPAIR_FROZEN_EVIDENCE_AUDIT",
             "producer_status":"EXHAUSTED",
             "corrected_stop_reason":"WORKER_QUERY_CAP",
             "mathematical_outcome":"BOUNDED_UNKNOWN",
             "public_outer_families_fully_tested":families,
             "public_inner_candidates_tested":inner,
             "point_matches":point_matches,
             "column_rejects":column_rejects,
             "public_valid_rows":0,
             "source_and_index_setup_s":setup_s,
             "worker_target_query_s":query_s,
             "parent_wall_ns":q["parent_wall_ns"],
             "sampled_peak_combined_rss_bytes":q["peak_combined_rss_bytes_sampled"],
             "constructed_control":"PASS_INDEPENDENT_CONSTRUCTED_THREEPAIR_CONTROL",
             "protocol_sha256":sha(HERE / "terminal_protocol.json")}
    with (HERE / "terminal_audit.json").open("x") as out:
        json.dump(audited,out,sort_keys=True,indent=2)
        out.write("\n")
    print(audited["status"],audited["mathematical_outcome"],flush=True)


if __name__ == "__main__":
    main()
