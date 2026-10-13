"""Read-only replay of frozen N41 residual and N131 projection evidence."""
import hashlib
import json
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
PAIRS = GOAL / "n131_w18_allseed_fourpair_20261012/n41_diagonal/pairs.tsv"
SUPPORT = GOAL / "n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv"
PREVIOUS = GOAL / "n41_common_frob_factor_20261012"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = json.loads((HERE / "protocol.json").read_text())
    files = {"source": HERE / "residual.cpp", "binary": HERE / "residual",
             "runner": HERE / "run.py", "pairs": PAIRS,
             "parent_cpp": GOAL / "n41_w8_ninepair_join_control_20261012/join9.cpp"}
    assert p["status"] == "FROZEN_BEFORE_PUBLIC_N41_QUERY"
    assert p["sha256"] == {key: sha(path) for key, path in files.items()}
    q = json.loads((HERE / "result.json").read_text())
    assert q["protocol_sha256"] == sha(HERE / "protocol.json")
    assert q["stdout_sha256"] == sha(HERE / "stdout.log")
    assert q["stderr_sha256"] == sha(HERE / "stderr.log")
    assert q["status"] == "HIT_PENDING_INDEPENDENT_REPLAY"
    assert q["stop_reason"] is None and q["exit_code"] == 0
    assert q["parent_wall_ns"] < p["parent_time_cap_s"] * 10**9
    assert q["peak_combined_rss_bytes_sampled"] < p["combined_rss_cap_bytes"]
    lines = (HERE / "stdout.log").read_text().splitlines()
    assert q["source_line"] in lines and q["double_line"] in lines and q["hit_line"] in lines
    assert len([s for s in lines if s.startswith("HIT ")]) == 1
    assert len([s for s in lines if s.startswith("EXHAUSTED ")]) == 0
    ap = json.loads((HERE / "audit_protocol.json").read_text())
    audit_files = {"source": HERE / "audit_sage.py", "pairs": PAIRS,
                   "geometry": GOAL / "n41_w7_entropy_cubic_20261011/w8/geometry.json",
                   "fixture": GOAL / "n41_w7_entropy_cubic_20261011/w8/fixture.json",
                   "target": PREVIOUS / "target.json", "join_receipt": HERE / "result.json",
                   "stdout": HERE / "stdout.log", "sage_runtime": HERE / "sage_runtime_info.json"}
    assert ap["status"] == "FROZEN_BEFORE_INDEPENDENT_REPLAY"
    assert ap["sha256"] == {key: sha(path) for key, path in audit_files.items()}
    a = json.loads((HERE / "audit_result.json").read_text())
    assert a["protocol_sha256"] == sha(HERE / "audit_protocol.json")
    assert a["status"] == "PASS_INDEPENDENT_N41_OUTPUT_RESIDUAL_PUBLIC_RELATION"
    assert (a["rank_before"], a["rank_after"], a["distinct_folded_columns"]) == (7, 8, 10)
    assert [item["state_id"] for item in a["source_pair_states"]] == list(map(int, q["hit_line"].split()[1:6]))
    assert len(a["relation_row"]) == 10
    for path, digest in a["prior_row_sha256"].items():
        assert sha(Path(path)) == digest
    proj = json.loads((HERE / "projection.json").read_text())
    assert proj["status"] == "PASS_EXACT_SOURCE_UNIFORM_RESIDUAL_PROJECTION"
    assert proj["protocol_sha256"] == sha(HERE / "protocol.json")
    assert proj["query_result_sha256"] == sha(HERE / "result.json")
    assert proj["n131_support_sha256"] == sha(SUPPORT)
    S = proj["n131_signed_pair_states"]
    r = 680564733841876926932320129493409985129
    assert S == 34482792912
    assert Fraction(proj["n131_uniform_single_probe_upper_bound"]) == Fraction(S, r)
    assert Fraction(proj["n131_uniform_expected_hits_at_frozen_kept_limit"]) == Fraction(p["kept_limit"] * S, r)
    assert Fraction(proj["n131_uniform_probes_for_expected_one_hit_lower_bound"]) == Fraction(r, S)
    print("PASS_N41_RESIDUAL_RELATION_AND_N131_PROJECTION", a["rank_after"])


if __name__ == "__main__":
    main()
