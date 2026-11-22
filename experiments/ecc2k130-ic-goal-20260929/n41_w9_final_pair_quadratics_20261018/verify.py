"""Read-only audit of the two-quadratic N41 circuit, proof and query."""
import hashlib
import json
from collections import defaultdict
from pathlib import Path

HERE=Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


for name in ("audit_protocol.json","build_protocol.json","probe_protocol.json",
             "query_protocol.json"):
    protocol=read(HERE/name)
    for path,digest in protocol["sources"].items():
        assert sha(path)==digest,(name,path)
audit_protocol=read(HERE/"audit_protocol.json")
audit=read(HERE/"audit_result.json")
assert audit["status"]=="PASS_ALL_N41_FINAL_ROOTS_FROM_TWO_QUADRATICS"
assert audit["protocol_sha256"]==sha(HERE/"audit_protocol.json")
assert (audit["codes_checked"],audit["signed_states_checked"])==(71,284)
assert (audit["pair_quadratic_roots"],audit["s3_quadratic_roots"])==(142,284)
assert audit["s3_zero_leading_cases"]==0
expected=defaultdict(set)
for row in read(audit_protocol["w_table"]):
    expected[str(row["code"])].add(row["w"])
assert len(expected)==71
for code,branches in audit["branches_by_code"].items():
    assert len(branches)==2 and all(len(row["final_roots"])==2 for row in branches)
    assert {w for branch in branches for w in branch["final_roots"]}==expected[code]

build=read(HERE/"build_result.json")
wires=read(HERE/"input_wires.json")
assert build["status"]=="PASS_N41_FINAL_PAIR_QUADRATICS_CIRCUIT"
assert build["candidate_id"] is None and build["protocol_sha256"]==sha(HERE/"build_protocol.json")
assert build["formula_sha256"]==sha(HERE/"formula.xcnf")
assert build["input_wires_sha256"]==sha(HERE/"input_wires.json")
assert len(build["controls_checked"])==33
assert sum(row["preceding_zero"] for row in build["controls_checked"])==1
assert all(row["pair_zero"] and row["s3_zero"] for row in build["controls_checked"])
assert len(wires["codes"])==5 and all(len(row)==8 for row in wires["codes"])
assert len(wires["left_reciprocal"])==len(wires["root_witness"])==len(wires["final_pair_reciprocal"])==41
inputs={bit for row in wires["codes"] for bit in row}
inputs.update(wires["left_reciprocal"])
inputs.update(wires["root_witness"])
inputs.update(wires["final_pair_reciprocal"])
assert len(inputs)==163
cnf=xors=pinned=0
with (HERE/"formula.xcnf").open("rb") as stream:
    assert stream.readline().strip()==f"p cnf {build['variables']} {build['clauses']+build['native_xor_rows']}".encode()
    for raw in stream:
        parts=raw.split()
        assert parts and parts[-1]==b"0"
        if parts[0]==b"x":
            xors+=1
        else:
            cnf+=1
            if len(parts)==2 and abs(int(parts[0])) in inputs:
                pinned+=1
assert (cnf,xors,pinned)==(build["clauses"],build["native_xor_rows"],0)
lean=(HERE/"lean_check.log").read_text()
assert lean.count("depends on axioms")==2 and "sorryAx" not in lean
assert "sorry" not in (HERE/"PairQuadratics.lean").read_text()

probe_protocol=read(HERE/"probe_protocol.json")
probe=read(HERE/"probe_result.json")
assert probe["status"]=="COMPLETED_FROZEN_ABBA_PROBE"
assert probe["protocol_sha256"]==sha(HERE/"probe_protocol.json")
rows=probe["arm_results"]
assert len(rows)==4 and [row["arm"] for row in rows]==probe_protocol["arms"]==["direct","quadratic","quadratic","direct"]
for index,row in enumerate(rows):
    arm=row["arm"]
    assert row==read(HERE/f"probe_{index}_{arm}_result.json")
    assert row["status"]=="INDETERMINATE_CONFLICT_CAP"
    assert row["reported_conflicts"]>=20000
    assert row["stop_reason"] is None and row["monitor_error"] is None
    assert row["sampled_peak_combined_rss_bytes"]<=probe_protocol["rss_cap_bytes"]
    assert row["solver_stdout_sha256"]==sha(HERE/f"probe_{index}_{arm}.stdout")
    assert row["solver_stderr_sha256"]==sha(HERE/f"probe_{index}_{arm}.stderr")
decisions=[rows[1]["reported_decisions"]/rows[0]["reported_decisions"],
           rows[2]["reported_decisions"]/rows[3]["reported_decisions"]]
walls=[rows[1]["wall_seconds"]/rows[0]["wall_seconds"],
       rows[2]["wall_seconds"]/rows[3]["wall_seconds"]]
promoted=all(x<=.8 for x in decisions) and all(x<=1.25 for x in walls)
assert promoted

query_status="RUNNING_OR_NOT_STARTED"
replay_status=None
if (HERE/"query_result.json").exists():
    query_protocol=read(HERE/"query_protocol.json")
    query=read(HERE/"query_result.json")
    assert query["candidate_id"] is None and query["worker_count"]==1
    assert query["protocol_sha256"]==sha(HERE/"query_protocol.json")
    assert query["command"][0]==query_protocol["solver"]
    assert query["command"][-1]==str(HERE/"formula.xcnf")
    assert query["solver_stdout_sha256"]==sha(HERE/"solver.stdout")
    assert query["solver_stderr_sha256"]==sha(HERE/"solver.stderr")
    assert query["sampled_peak_combined_rss_bytes"]<=query_protocol["rss_cap_bytes"]
    assert query["charged_stage_wall_seconds"]==build["wall_seconds"]+query["query_parent_wall_seconds"]
    query_status=query["status"]
    if query_status=="BOUNDED_UNKNOWN":
        assert query["monitor_error"] is None
        if query["stop_reason"]=="WALL_CAP":
            assert query["query_parent_wall_seconds"]>=query_protocol["parent_wall_cap_seconds"]
            assert not any(query[f"solver_terminal_{name}"] for name in ("sat","unsat","indeterminate"))
        else:
            assert query["stop_reason"] is None and query["solver_terminal_indeterminate"]
    if (HERE/"replay_result.json").exists():
        replay_protocol=read(HERE/"replay_protocol.json")
        for path,digest in replay_protocol["sources"].items():
            assert sha(path)==digest,path
        replay=read(HERE/"replay_result.json")
        assert replay["protocol_sha256"]==sha(HERE/"replay_protocol.json")
        assert query_status=="SAT_MODEL_UNVERIFIED"
        replay_status=replay["status"]

print(json.dumps({"status":"PASS_FINAL_PAIR_QUADRATIC_RECEIPTS",
                  "candidate_id":None,"codes_checked":71,"signed_states_checked":284,
                  "control_rows":33,"unpinned_inputs":len(inputs),
                  "cnf_clauses":cnf,"native_xor_rows":xors,
                  "decision_ratios":decisions,"wall_ratios":walls,
                  "full_query_promotion_gate":promoted,
                  "query_status":query_status,"replay_status":replay_status},sort_keys=True))
