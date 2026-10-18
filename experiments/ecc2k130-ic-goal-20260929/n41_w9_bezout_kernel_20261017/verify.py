"""Read-only audit of kernel panel, circuit, proof and ABBA probe receipts."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE/name).read_text())


for name in ("kernel_protocol.json","build_protocol.json","probe_protocol.json"):
    protocol=read(name)
    for path,digest in protocol["sources"].items():
        assert sha(path)==digest,(name,path)
panel=read("kernel_result.json")
build=read("build_result.json")
wires=read("input_wires.json")
probe=read("probe_result.json")
probe_protocol=read("probe_protocol.json")
assert panel["status"]=="PASS_NORMALIZED_BEZOUT_KERNEL_PANEL"
assert panel["positive_rank_three"]==1 and panel["control_rank_four"]==32
assert build["status"]=="PASS_N41_BEZOUT_KERNEL_CIRCUIT"
assert build["candidate_id"] is None and len(build["controls_checked"])==33
assert sum(row["kernel_zero"] for row in build["controls_checked"])==1
assert build["formula_sha256"]==sha(HERE/"formula.xcnf")
assert build["input_wires_sha256"]==sha(HERE/"input_wires.json")
assert build["formula_bytes"]==(HERE/"formula.xcnf").stat().st_size
assert len(wires["codes"])==5 and all(len(row)==8 for row in wires["codes"])
assert len(wires["left_reciprocal"])==41
assert len(wires["kernel_tail"])==3 and all(len(row)==41 for row in wires["kernel_tail"])
inputs={wire for row in wires["codes"] for wire in row}
inputs.update(wires["left_reciprocal"])
inputs.update(wire for row in wires["kernel_tail"] for wire in row)
assert len(inputs)==204
cnf=xors=pinned=0
with (HERE/"formula.xcnf").open("rb") as file:
    assert file.readline().strip()==f"p cnf {build['variables']} {build['clauses']+build['native_xor_rows']}".encode()
    for raw in file:
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
assert lean.count("depends on axioms")==4 and "sorryAx" not in lean
assert probe["status"]=="COMPLETED_FROZEN_ABBA_PROBE"
assert probe["protocol_sha256"]==sha(HERE/"probe_protocol.json")
assert len(probe["arm_results"])==4
assert [row["arm"] for row in probe["arm_results"]]==probe_protocol["arms"]
for index,row in enumerate(probe["arm_results"]):
    arm=row["arm"]
    assert row==read(f"probe_{index}_{arm}_result.json")
    assert row["status"]=="INDETERMINATE_CONFLICT_CAP"
    assert row["reported_conflicts"]==20001
    assert row["stop_reason"] is None and row["monitor_error"] is None
    assert row["sampled_peak_combined_rss_bytes"]<=probe_protocol["rss_cap_bytes"]
    assert row["solver_stdout_sha256"]==sha(HERE/f"probe_{index}_{arm}.stdout")
    assert row["solver_stderr_sha256"]==sha(HERE/f"probe_{index}_{arm}.stderr")
    assert row["command"][-1]==probe_protocol["formulas"][arm]
    assert row["command"][0]==probe_protocol["solver"]
first=probe["arm_results"][1]["wall_seconds"]/probe["arm_results"][0]["wall_seconds"]
second=probe["arm_results"][2]["wall_seconds"]/probe["arm_results"][3]["wall_seconds"]
promoted=first<=.8 and second<=.8
assert not promoted
print(json.dumps({"status":"PASS_KERNEL_STAGE_RECEIPTS",
                  "candidate_id":None,"control_rows":33,
                  "cnf_clauses":cnf,"native_xor_rows":xors,
                  "directly_pinned_inputs":pinned,
                  "fixed_conflict_pair_wall_ratios":[first,second],
                  "full_query_promotion_gate":promoted},sort_keys=True))
