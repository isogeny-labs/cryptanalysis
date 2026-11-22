"""Audit every selector clause, frozen source and first solver probe."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


for name in ("build_protocol.json","probe_protocol.json",
             "holdout_protocol.json","query_protocol.json"):
    protocol=read(HERE/name)
    for path,digest in protocol["sources"].items():
        assert sha(path)==digest,(name,path)
build_protocol=read(HERE/"build_protocol.json")
build=read(HERE/"build_result.json")
wires=read(HERE/"input_wires.json")
assert build["status"]=="PASS_N41_FINAL_ROOT_SELECTOR_CIRCUIT"
assert build["candidate_id"] is None
assert build["formula_sha256"]==sha(HERE/"formula.xcnf")
assert build["input_wires_sha256"]==sha(HERE/"input_wires.json")
assert len(build["controls_checked"])==33
assert sum(row["kernel_zero"] for row in build["controls_checked"])==1
audit=read(build_protocol["w_audit"])
assert audit["status"]=="PASS_ALL_CODE_QUARTIC_ROOTS_EQUAL_TARGET_TABLE"
assert (audit["codes_checked"],audit["distinct_target_w"])==(71,284)
lean=(HERE/"lean_check.log").read_text()
assert lean.count("FinalRootSelector.")==3
assert lean.count("depends on axioms") == 2
assert lean.count("does not depend on any axioms") == 1
assert "sorryAx" not in lean
assert "sorry" not in (HERE/"Selector.lean").read_text()
table=sorted(read(build_protocol["w_table"]),key=lambda row:(row["code"],row["w"]))
assert [(row["code"],row["w"]) for row in table]==[(row["code"],row["w"]) for row in wires["selector_rows"]]
assert len({row["w"] for row in table})==284
selector=wires["selector"]
assert len(selector)==9
assert len(wires["codes"])==5 and all(len(row)==8 for row in wires["codes"])
assert len(wires["root_witness_wires"])==41 and len(wires["left_reciprocal"])==41
free={bit for row in wires["codes"][:4] for bit in row}
free.update(wires["left_reciprocal"])
free.update(selector)
assert len(free)==82


def mismatch(bits,index):
    return tuple(-wire if index>>bit&1 else wire for bit,wire in enumerate(bits))


expected=set(mismatch(selector,index) for index in range(284,512))
for index,row in enumerate(table):
    guard=mismatch(selector,index)
    for value,bits in ((row["code"],wires["codes"][4]),
                       (row["w"],wires["root_witness_wires"])):
        for bit,wire in enumerate(bits):
            expected.add(guard+((wire if value>>bit&1 else -wire),))
assert len(expected)==14144==build["selector_clauses"]
selector_set=set(selector)
actual=[]
cnf=xors=pinned=0
with (HERE/"formula.xcnf").open("rb") as stream:
    assert stream.readline().strip()==f"p cnf {build['variables']} {build['clauses']+build['native_xor_rows']}".encode()
    for raw in stream:
        parts=raw.split()
        assert parts and parts[-1]==b"0"
        if parts[0]==b"x":
            xors+=1
            assert not selector_set.intersection(abs(int(x)) for x in parts[1:-1])
        else:
            cnf+=1
            clause=tuple(int(x) for x in parts[:-1])
            if len(clause)==1 and abs(clause[0]) in free:
                pinned+=1
            if selector_set.intersection(abs(x) for x in clause):
                actual.append(clause)
assert (cnf,xors,pinned)==(build["clauses"],build["native_xor_rows"],0)
assert len(actual)==len(expected) and set(actual)==expected

probe_protocol=read(HERE/"probe_protocol.json")
probe=read(HERE/"probe_result.json")
assert probe["status"]=="COMPLETED_FROZEN_ABBA_PROBE"
assert probe["protocol_sha256"]==sha(HERE/"probe_protocol.json")
rows=probe["arm_results"]
assert len(rows)==4 and [row["arm"] for row in rows]==probe_protocol["arms"]==["direct","selector","selector","direct"]
for index,row in enumerate(rows):
    arm=row["arm"]
    assert row==read(HERE/f"probe_{index}_{arm}_result.json")
    assert row["status"]=="INDETERMINATE_CONFLICT_CAP"
    assert row["reported_conflicts"]>=20000
    assert row["stop_reason"] is None and row["monitor_error"] is None
    assert row["sampled_peak_combined_rss_bytes"]<=probe_protocol["rss_cap_bytes"]
    assert row["solver_stdout_sha256"]==sha(HERE/f"probe_{index}_{arm}.stdout")
    assert row["solver_stderr_sha256"]==sha(HERE/f"probe_{index}_{arm}.stderr")
    assert row["command"][0]==probe_protocol["solver"]
    assert row["command"][-1]==probe_protocol["formulas"][arm]
decisions=[rows[1]["reported_decisions"]/rows[0]["reported_decisions"],
           rows[2]["reported_decisions"]/rows[3]["reported_decisions"]]
walls=[rows[1]["wall_seconds"]/rows[0]["wall_seconds"],
       rows[2]["wall_seconds"]/rows[3]["wall_seconds"]]
promoted=all(x<=.8 for x in decisions) and all(x<=1.25 for x in walls)
assert not promoted
failure=read(HERE/"holdout_attempt1.json")
assert failure["status"]=="PRODUCER_FAILURE_MISSING_PROTOCOL"
assert failure["solver_started"] is False
holdout_protocol=read(HERE/"holdout_protocol.json")
holdout=read(HERE/"holdout_result.json")
assert holdout["status"]=="COMPLETED_FROZEN_ABBA_PROBE"
assert holdout["protocol_sha256"]==sha(HERE/"holdout_protocol.json")
holdout_rows=holdout["arm_results"]
assert len(holdout_rows)==4
assert [row["arm"] for row in holdout_rows]==holdout_protocol["arms"]==["direct","selector","selector","direct"]
for index,row in enumerate(holdout_rows):
    arm=row["arm"]
    assert row==read(HERE/f"holdout_{index}_{arm}_result.json")
    assert row["status"]=="INDETERMINATE_CONFLICT_CAP"
    assert row["reported_conflicts"]>=50000
    assert row["stop_reason"] is None and row["monitor_error"] is None
    assert row["sampled_peak_combined_rss_bytes"]<=holdout_protocol["rss_cap_bytes"]
    assert row["solver_stdout_sha256"]==sha(HERE/f"holdout_{index}_{arm}.stdout")
    assert row["solver_stderr_sha256"]==sha(HERE/f"holdout_{index}_{arm}.stderr")
holdout_walls=[holdout_rows[1]["wall_seconds"]/holdout_rows[0]["wall_seconds"],
               holdout_rows[2]["wall_seconds"]/holdout_rows[3]["wall_seconds"]]
direct_aa=max(holdout_rows[0]["wall_seconds"],holdout_rows[3]["wall_seconds"])/min(holdout_rows[0]["wall_seconds"],holdout_rows[3]["wall_seconds"])
selector_aa=max(holdout_rows[1]["wall_seconds"],holdout_rows[2]["wall_seconds"])/min(holdout_rows[1]["wall_seconds"],holdout_rows[2]["wall_seconds"])
holdout_promoted=all(ratio<=.75 for ratio in holdout_walls) and max(direct_aa,selector_aa)<=1.25
assert not holdout_promoted and selector_aa>1.25

query_status="RUNNING_OR_NOT_STARTED"
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
        assert query["stop_reason"]=="WALL_CAP" and query["monitor_error"] is None
        assert query["query_parent_wall_seconds"]>=query_protocol["parent_wall_cap_seconds"]
        assert not any(query[f"solver_terminal_{name}"] for name in ("sat","unsat","indeterminate"))
    if (HERE/"replay_result.json").exists():
        replay_protocol=read(HERE/"replay_protocol.json")
        for path,digest in replay_protocol["sources"].items():
            assert sha(path)==digest,path
        replay=read(HERE/"replay_result.json")
        assert replay["protocol_sha256"]==sha(HERE/"replay_protocol.json")
        assert query_status=="SAT_MODEL_UNVERIFIED"
print(json.dumps({"status":"PASS_SELECTOR_STAGE_RECEIPTS","candidate_id":None,
                  "free_inputs":len(free),"selector_rows":len(table),
                  "selector_clauses":len(expected),"directly_pinned_inputs":pinned,
                  "cnf_clauses":cnf,"native_xor_rows":xors,
                  "fixed_conflict_decision_ratios":decisions,
                  "fixed_conflict_wall_ratios":walls,
                  "first_promotion_gate":promoted,
                  "holdout_wall_ratios":holdout_walls,
                  "holdout_same_formula_ratios":[direct_aa,selector_aa],
                  "holdout_promotion_gate":holdout_promoted,
                  "query_status":query_status},sort_keys=True))
