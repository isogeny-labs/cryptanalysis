"""Read-only audit of frozen inputs, exact circuit, and optional query receipt."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE/name).read_text())


for name in ("bezout_protocol.json","build_protocol.json","query_protocol.json",
             "affine_protocol.json","affine_audit_protocol.json"):
    p=read(name)
    for path,digest in p["sources"].items():
        assert sha(path)==digest,(name,path)

audit=read("bezout_result.json")
build=read("build_result.json")
wire=read("input_wires.json")
query_protocol=read("query_protocol.json")
assert audit["status"]=="PASS_CHAR2_BEZOUT_RESULTANT_PANEL"
assert audit["panel_rows"]==33 and audit["positive_zero"]==1 and audit["control_zero"]==0
assert build["status"]=="PASS_N41_TWO_QUARTIC_BEZOUT_CIRCUIT"
assert build["candidate_id"] is None
assert len(build["controls_checked"])==33
assert sum(row["det_zero"] for row in build["controls_checked"])==1
assert build["formula_sha256"]==sha(HERE/"formula.xcnf")
assert build["input_wires_sha256"]==sha(HERE/"input_wires.json")
assert build["formula_bytes"]==(HERE/"formula.xcnf").stat().st_size
assert len(wire["codes"])==5 and all(len(row)==8 for row in wire["codes"])
assert len(wire["left_reciprocal"])==41
assert len(wire["allowed_code_words"])==71
inputs={x for row in wire["codes"] for x in row}|set(wire["left_reciprocal"])
assert len(inputs)==81
cnf=xors=units_on_inputs=0
with (HERE/"formula.xcnf").open("rb") as file:
    header=file.readline().strip()
    assert header==f"p cnf {build['variables']} {build['clauses']+build['native_xor_rows']}".encode()
    for raw in file:
        parts=raw.split()
        assert parts and parts[-1]==b"0"
        if parts[0]==b"x":
            xors+=1
        else:
            cnf+=1
            if len(parts)==2 and abs(int(parts[0])) in inputs:
                units_on_inputs+=1
assert (cnf,xors,units_on_inputs)==(build["clauses"],build["native_xor_rows"],0)
lean=(HERE/"lean_check.log").read_text()
assert lean.count("depends on axioms")==2 and "sorryAx" not in lean
affine=read("affine_result.json")
affine_audit=read("affine_audit_result.json")
assert affine["status"]=="PASS_FIXED_CODE_AFFINE_RANK_CENSUS"
assert affine_audit["status"]=="PASS_SAGE_ALL_FIXED_CODE_AFFINE_RANKS"
assert affine["usable_code_pairs"]==affine_audit["code_pairs_checked"]==4964
assert affine["usable_rows"]==affine_audit["rows_checked"]==79424
assert affine["size_dimension_histogram"]==affine_audit["size_dimension_histogram"]=={"16,15":4964}
assert affine["excluded_code_pairs"]==77 and not affine["affine_dependency_pairs"]
attempt=read("affine_attempt1.json")
frozen=read(attempt["protocol_snapshot"])
assert attempt["status"]=="PRODUCER_FAILURE"
assert sha(HERE/attempt["source_snapshot"])==frozen["sources"][str(HERE/"affine_census.py")]

query_status="PENDING"
verification_status="PASS_BEZOUT_CIRCUIT_RECEIPTS"
if (HERE/"query_result.json").exists():
    result=read("query_result.json")
    assert result["protocol_sha256"]==sha(HERE/"query_protocol.json")
    assert result["worker_count"]==query_protocol["worker_count"]==1
    assert result["curve_id"]==build["curve_id"]
    assert result["solver_stdout_sha256"]==sha(HERE/"solver.stdout")
    assert result["solver_stderr_sha256"]==sha(HERE/"solver.stderr")
    assert result["sampled_peak_combined_rss_bytes"]<=query_protocol["rss_cap_bytes"]
    assert abs(result["charged_stage_wall_seconds"]-
               (build["wall_seconds"]+result["query_parent_wall_seconds"]))<1e-6
    assert result["command"][:4]==[query_protocol["solver"],"--threads=1",
                                    f"--maxtime={query_protocol['solver_cap_seconds']}",
                                    "--zero-exit-status"]
    assert result["command"][-1]==str(HERE/"formula.xcnf")
    query_status=result["status"]
    if query_status=="BOUNDED_UNKNOWN":
        assert result["stop_reason"]=="WALL_CAP" or result["solver_terminal_indeterminate"]
    elif query_status=="SAT_MODEL_UNVERIFIED":
        assert result["solver_terminal_sat"]
        verification_status="PENDING_INDEPENDENT_MODEL_REPLAY"
        if (HERE/"replay_result.json").exists():
            replay_protocol=read("replay_protocol.json")
            for path,digest in replay_protocol["sources"].items():
                assert sha(path)==digest,path
            replay=read("replay_result.json")
            assert replay["protocol_sha256"]==sha(HERE/"replay_protocol.json")
            assert replay["status"]=="PASS_INDEPENDENT_SAGE_MODEL_GROUP_REPLAY"
            assert replay["independent_group_matches"]>=1
            verification_status="PASS_INDEPENDENT_SAGE_RELATION_REPLAY"
    elif query_status=="UNSAT_UNVERIFIED":
        assert result["solver_terminal_unsat"]

print(json.dumps({"status":verification_status,
                  "candidate_id":None,"control_rows":33,
                  "usable_code_pairs_affine_rank_15":4964,
                  "cnf_clauses":cnf,"native_xor_rows":xors,
                  "directly_pinned_input_wires":units_on_inputs,
                  "query_status":query_status},sort_keys=True))
