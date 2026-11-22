"""Independent byte replay and phase/status audit of the charged public run."""
import hashlib
import json
import tempfile
import time
from pathlib import Path

import circuit

HERE=Path(__file__).resolve().parent
GOAL=HERE.parent
ORIGINAL=GOAL/"n131_common_frob_inverse_trace_20261012"
PRIOR_TARGET=GOAL/"n41_common_frob_factor_20261012/n131_projection_result.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def main():
    frozen=read(HERE/"audit_protocol.json")
    files={"script":HERE/"audit.py","circuit":HERE/"circuit.py",
           "query_protocol":HERE/"query_protocol.json",
           "query_result":HERE/"query_result.json",
           "target":HERE/"target_result.json",
           "target_stdout":HERE/"target_project.stdout",
           "target_stderr":HERE/"target_project.stderr",
           "public_build":HERE/"public_build_result.json",
           "build_stdout":HERE/"build.stdout","build_stderr":HERE/"build.stderr",
           "solver_stdout":HERE/"solver.stdout","solver_stderr":HERE/"solver.stderr",
           "public_xcnf":HERE/"public.xcnf",
           "control_xcnf":ORIGINAL/"control.xcnf",
           "control_result":ORIGINAL/"control_result.json",
           "fixture":HERE/"fixture.json","prior_target":PRIOR_TARGET,
           "failed_attempt":ORIGINAL/"query_result.json"}
    assert frozen["status"]=="FROZEN_BEFORE_N131_INVERSE_TRACE_TERMINAL_AUDIT"
    assert frozen["sha256"]=={name:sha(path) for name,path in files.items()}
    protocol=read(HERE/"query_protocol.json")
    query=read(HERE/"query_result.json")
    target=read(HERE/"target_result.json")
    prior=read(PRIOR_TARGET)
    control=read(ORIGINAL/"control_result.json")
    public=read(HERE/"public_build_result.json")
    fixture=read(HERE/"fixture.json")
    assert query["protocol_sha256"]==sha(HERE/"query_protocol.json")
    assert target["protocol_sha256"]==sha(HERE/"query_protocol.json")
    assert target["status"]==prior["status"]=="PASS_CHECKED_SAGE_N131_COMMON_FACTOR_TARGET"
    for key in ("curve_id","public_point","transformed_target","raw_preimages",
                "raw_preimage_reciprocals","factor_mod_r","inverse_mod_r"):
        assert target[key]==prior[key]
    assert target["public_point"]==protocol["public_point"]
    assert target["transformed_target"]==protocol["transformed_target"]
    assert target["raw_preimage_reciprocals"]==protocol["raw_preimage_reciprocals"]
    assert query["target_projection"]["exit_code"]==0
    assert query["build"]["exit_code"]==0
    for stage,label in ((query["target_projection"],"target_project"),
                        (query["build"],"build"),(query["solver"],"solver")):
        assert stage["stdout_sha256"]==sha(HERE/f"{label}.stdout")
        assert stage["stderr_sha256"]==sha(HERE/f"{label}.stderr")
    assert (HERE/"target_project.stderr").read_text()==""
    assert (HERE/"build.stderr").read_text()==""
    assert query["peak_combined_rss_bytes_sampled"]<protocol["combined_rss_cap_bytes"]
    phases={"target_projection_parent":query["target_projection"]["wall_ns"],
            "build_parent":query["build"]["wall_ns"],
            "solver_parent":query["solver"]["wall_ns"],
            "bookkeeping":query["bookkeeping_ns"]}
    assert all(value>=0 for value in phases.values())
    assert sum(phases.values())==query["target_dependent_attempt_ns"]
    assert query["target_dependent_attempt_ns"]>=600*10**9
    assert query["target_dependent_attempt_ns"]<601*10**9
    stdout=(HERE/"solver.stdout").read_text(errors="replace")
    terminals=[line for line in stdout.splitlines() if line.startswith("s ")]
    assert terminals==query["solver_terminal_lines"]
    assert sum(line.startswith("c rst") for line in stdout.splitlines())==query["solver_restart_rows"]
    if query["status"]=="PARENT_TIME_CAP":
        assert query["solver"]["stop_reason"]=="PARENT_TIME_CAP"
        assert query["solver"]["exit_code"]==-9 and not terminals
        outcome="BOUNDED_UNKNOWN"
    elif query["status"]=="SAT_PENDING_INDEPENDENT_REPLAY":
        assert "s SATISFIABLE" in terminals
        outcome="SAT_PENDING_INDEPENDENT_REPLAY"
    else:
        raise AssertionError(f"unexpected solver status: {query['status']}")
    assert control["status"]=="PASS_COMPLETE_N131_FIVEPAIR_ASSIGNMENT"
    assert control["xcnf_sha256"]==sha(ORIGINAL/"control.xcnf")
    assert public["status"]=="PUBLIC_FORMULA_BUILT"
    assert public["xcnf_sha256"]==sha(HERE/"public.xcnf")
    start=time.monotonic_ns()
    profiles={}
    for label,zlist in (("control",[fixture["raw_target_reciprocal"]]),
                        ("public",target["raw_preimage_reciprocals"])):
        formula,wires,metadata=circuit.build(zlist)
        receipt=control if label=="control" else public
        assert formula.next_var-1==receipt["variables"]
        assert formula.and_count==receipt["and_gates"]
        assert len(formula.clauses)==receipt["cnf_clauses"]
        assert len(formula.xors)==receipt["native_xor_rows"]
        assert metadata==receipt["metadata"]
        if label=="control":
            assert circuit.check_assignment(formula,wires,fixture)==receipt["assignment_check"]
        else:
            assert wires["target_flags"]==public["target_flags"]
            assert wires["masks"]==public["mask_wires"]
            assert wires["inverse_witnesses"]==public["inverse_witness_wires"]
            assert wires["pair_outputs"]==public["pair_output_wires"]
            assert wires["middle"]==public["middle_wires"]
        with tempfile.TemporaryDirectory() as temporary:
            regenerated=Path(temporary)/f"{label}.xcnf"
            formula.write(regenerated)
            original=(ORIGINAL/"control.xcnf" if label=="control" else HERE/"public.xcnf")
            assert regenerated.read_bytes()==original.read_bytes()
        profiles[label]={"variables":receipt["variables"],
                         "cnf_clauses":receipt["cnf_clauses"],
                         "native_xor_rows":receipt["native_xor_rows"],
                         "xcnf_bytes":receipt["xcnf_bytes"],
                         "xcnf_sha256":receipt["xcnf_sha256"]}
    ended=time.monotonic_ns()
    audited={"status":"PASS_N131_INVERSE_TRACE_FROZEN_EVIDENCE_AUDIT",
             "candidate_id":None,"public_process_status":query["status"],
             "mathematical_outcome":outcome,"profiles":profiles,
             "solver_restart_rows":query["solver_restart_rows"],
             "phase_ns":{**phases,"total":query["target_dependent_attempt_ns"]},
             "peak_combined_rss_bytes_sampled":query["peak_combined_rss_bytes_sampled"],
             "audit_wall_ns":ended-start,
             "protocol_sha256":sha(HERE/"audit_protocol.json")}
    with (HERE/"audit_result.json").open("x") as out:
        json.dump(audited,out,sort_keys=True,indent=2)
        out.write("\n")
    print(audited["status"],outcome,flush=True)


if __name__=="__main__":
    main()
