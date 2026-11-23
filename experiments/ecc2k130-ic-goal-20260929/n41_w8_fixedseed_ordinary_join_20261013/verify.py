"""Read-only audit of frozen ordinary relation, Sage row, and SAT comparator."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_sources(record, key, relative_root=HERE):
    for name, digest in record[key].items():
        path = Path(name)
        if not path.is_absolute(): path = relative_root / path
        assert sha(path) == digest, name


def main():
    source = json.loads((HERE/"protocol.json").read_text())
    check_sources(source,"source_sha256",HERE.parent)
    assert source["input_sha256"] == sha(HERE/"input.tsv")
    assert source["public_target"] == [1458168294740,1672312028033]
    query_p = json.loads((HERE/"query_protocol.json").read_text())
    check_sources(query_p,"source_sha256")
    query = json.loads((HERE/"query_result.json").read_text())
    assert query["protocol_sha256"] == sha(HERE/"query_protocol.json")
    assert query["stdout_sha256"] == sha(HERE/"join.stdout")
    assert query["stderr_sha256"] == sha(HERE/"join.stderr")
    assert query["status"] == "PASS_ORDINARY_RAW_RELATION"
    assert query["returncode"] == 0 and query["wall_ns"] < 180*10**9
    assert query["peak_combined_rss_sample_bytes"] < 4*1024**3
    assert query["terminal_lines"][0].startswith("CHECK_PASS 128 ")
    assert query["terminal_lines"][1].startswith("LEFT_DONE 3750144 ")
    assert query["terminal_lines"][2].startswith("HIT 0 97 151 42 0 14 109 51 231031 ")
    assert query["terminal_lines"][3].startswith("COMPLETE_HITS 1 231031 ")
    audit_p = json.loads((HERE/"audit_protocol.json").read_text())
    check_sources(audit_p,"source_sha256")
    audit = json.loads((HERE/"audit_result.json").read_text())
    assert audit["audit_protocol_sha256"] == sha(HERE/"audit_protocol.json")
    assert audit["group_replay_pass"] and audit["raw_sum_pass"]
    assert audit["public_target"] == source["public_target"]
    assert audit["raw_target"] == source["raw_target"]
    assert audit["distinct_folded_columns"] == 14
    row_p = json.loads((HERE/"row_protocol.json").read_text())
    check_sources(row_p,"sources")
    row = json.loads((HERE/"row_result.json").read_text())
    assert row["row_protocol_sha256"] == sha(HERE/"row_protocol.json")
    assert row["rank_from_empty"] == 1 and row["nonzero_row_entries"] == 14
    assert len({x["column"] for x in row["terms"]}) == 14 and row["public_group_replay"]
    build_p = json.loads((HERE/"build_protocol.json").read_text())
    check_sources(build_p,"sources")
    build = json.loads((HERE/"build_result.json").read_text())
    assert build["status"] == "PASS_ORDINARY_POINT_CONSTRUCTED_ASSIGNMENT"
    assert build["build_protocol_sha256"] == sha(HERE/"build_protocol.json")
    assert build["formula_sha256"] == sha(HERE/"ordinary.xcnf")
    assert build["assignment_check"] == {"clauses":build["clauses"],"native_xor_rows":build["xor_rows"]}
    sat_p = json.loads((HERE/"sat_protocol.json").read_text())
    check_sources(sat_p,"sources")
    assert sat_p["solver_sha256"] == sha(sat_p["solver_path"])
    sat = json.loads((HERE/"sat_result.json").read_text())
    assert sat["protocol_sha256"] == sha(HERE/"sat_protocol.json")
    assert sat["status"] == "BOUNDED_UNKNOWN" and sat["stop_reason"] == "PARENT_WALL_CAP"
    assert sat["terminal_lines"] == [] and sat["exit_code"] == -15
    assert sat["sampled_peak_combined_rss_bytes"] < 4*1024**3
    assert sat["sha256"] == {"sat.stdout":sha(HERE/"sat.stdout"),"sat.stderr":sha(HERE/"sat.stderr")}
    projection = json.loads((HERE/"projection_result.json").read_text())
    source_count = HERE.parent/"n131_w20_sevenpair_gate_20261010"/"count_result_v2.json"
    assert projection["source_sha256"] == sha(source_count)
    S = json.loads(source_count.read_text())["signed_pair_states_per_slot"]
    assert int(projection["left_triples_upper"]) == S**3
    assert int(projection["right_quadruples_upper"]) == S**4
    assert json.loads((HERE/"sage_runtime_info.json").read_text())["status"] == "verified"
    print("PASS_N41_W8_FIXEDSEED_ORDINARY_RELATION_AND_SAT_AUDIT")


if __name__ == "__main__":
    main()
