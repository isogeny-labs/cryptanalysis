"""Read-only audit of the direct-root N41 circuit, probe and query."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "n41_w9_bezout_kernel_20261017"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


build_protocol = read(HERE / "build_protocol.json")
probe_protocol = read(HERE / "probe_protocol.json")
query_protocol = read(HERE / "query_protocol.json")
for protocol in (build_protocol, probe_protocol, query_protocol):
    for path, digest in protocol["sources"].items():
        assert sha(path) == digest, path

panel = read(BASE / "kernel_result.json")
assert panel["status"] == "PASS_NORMALIZED_BEZOUT_KERNEL_PANEL"
assert panel["positive_rank_three"] == 1 and panel["control_rank_four"] == 32
lean = (BASE / "lean_check.log").read_text()
assert lean.count("depends on axioms") == 4 and "sorryAx" not in lean
direct_lean = (HERE / "lean_check.log").read_text()
assert direct_lean.count("depends on axioms") == 2 and "sorryAx" not in direct_lean
assert "sorry" not in (HERE / "DirectRoot.lean").read_text()

build = read(HERE / "build_result.json")
wires = read(HERE / "input_wires.json")
assert build["status"] == "PASS_N41_DIRECT_ROOT_CIRCUIT"
assert build["candidate_id"] is None and len(build["controls_checked"]) == 33
assert sum(row["kernel_zero"] for row in build["controls_checked"]) == 1
assert build["formula_sha256"] == sha(HERE / "formula.xcnf")
assert build["input_wires_sha256"] == sha(HERE / "input_wires.json")
assert build["formula_bytes"] == (HERE / "formula.xcnf").stat().st_size
assert len(wires["codes"]) == 5 and all(len(row) == 8 for row in wires["codes"])
assert len(wires["left_reciprocal"]) == 41 and len(wires["root_witness"]) == 41
inputs = {bit for row in wires["codes"] for bit in row}
inputs.update(wires["left_reciprocal"])
inputs.update(wires["root_witness"])
assert len(inputs) == 122
cnf = xors = pinned = 0
with (HERE / "formula.xcnf").open("rb") as stream:
    assert stream.readline().strip() == (
        f"p cnf {build['variables']} {build['clauses'] + build['native_xor_rows']}".encode()
    )
    for raw in stream:
        parts = raw.split()
        assert parts and parts[-1] == b"0"
        if parts[0] == b"x":
            xors += 1
        else:
            cnf += 1
            if len(parts) == 2 and abs(int(parts[0])) in inputs:
                pinned += 1
assert (cnf, xors, pinned) == (build["clauses"], build["native_xor_rows"], 0)

probe = read(HERE / "probe_result.json")
assert probe["status"] == "COMPLETED_FROZEN_ABBA_PROBE"
assert probe["protocol_sha256"] == sha(HERE / "probe_protocol.json")
rows = probe["arm_results"]
assert len(rows) == 4 and [row["arm"] for row in rows] == ["root", "direct", "direct", "root"]
for index, row in enumerate(rows):
    arm = row["arm"]
    assert row == read(HERE / f"probe_{index}_{arm}_result.json")
    assert row["status"] == "INDETERMINATE_CONFLICT_CAP"
    assert row["reported_conflicts"] in (20001, 20002)
    assert row["stop_reason"] is None and row["monitor_error"] is None
    assert row["sampled_peak_combined_rss_bytes"] <= probe_protocol["rss_cap_bytes"]
    assert row["solver_stdout_sha256"] == sha(HERE / f"probe_{index}_{arm}.stdout")
    assert row["solver_stderr_sha256"] == sha(HERE / f"probe_{index}_{arm}.stderr")
    assert row["command"][0] == probe_protocol["solver"]
    assert row["command"][-1] == probe_protocol["formulas"][arm]

decision_ratios = [rows[1]["reported_decisions"] / rows[0]["reported_decisions"],
                   rows[2]["reported_decisions"] / rows[3]["reported_decisions"]]
wall_ratios = [rows[1]["wall_seconds"] / rows[0]["wall_seconds"],
               rows[2]["wall_seconds"] / rows[3]["wall_seconds"]]
promoted = all(row["reported_conflicts"] >= 20000 for row in rows) and \
    all(ratio <= .8 for ratio in decision_ratios) and \
    all(ratio <= 1.25 for ratio in wall_ratios)
assert promoted

query_status = "RUNNING_OR_NOT_STARTED"
relation_replay = None
if (HERE / "query_result.json").exists():
    query = read(HERE / "query_result.json")
    assert query["candidate_id"] is None and query["worker_count"] == 1
    assert query["protocol_sha256"] == sha(HERE / "query_protocol.json")
    assert query["command"][0] == query_protocol["solver"]
    assert query["command"][-1] == str(HERE / "formula.xcnf")
    assert query["solver_stdout_sha256"] == sha(HERE / "solver.stdout")
    assert query["solver_stderr_sha256"] == sha(HERE / "solver.stderr")
    assert query["sampled_peak_combined_rss_bytes"] <= query_protocol["rss_cap_bytes"]
    assert query["charged_stage_wall_seconds"] == build["wall_seconds"] + query["query_parent_wall_seconds"]
    query_status = query["status"]
    if query_status == "BOUNDED_UNKNOWN":
        assert query["stop_reason"] == "WALL_CAP"
        assert query["monitor_error"] is None
        assert query["query_parent_wall_seconds"] >= query_protocol["parent_wall_cap_seconds"]
        assert not any(query[f"solver_terminal_{name}"] for name in ("sat", "unsat", "indeterminate"))
    if (HERE / "replay_result.json").exists():
        replay_protocol = read(HERE / "replay_protocol.json")
        for path, digest in replay_protocol["sources"].items():
            assert sha(path) == digest, path
        replay = read(HERE / "replay_result.json")
        assert replay["protocol_sha256"] == sha(HERE / "replay_protocol.json")
        assert query_status == "SAT_MODEL_UNVERIFIED"
        relation_replay = replay["status"]

print(json.dumps({"status": "PASS_DIRECT_ROOT_RECEIPTS", "candidate_id": None,
                  "control_rows": 33, "unpinned_inputs": len(inputs),
                  "cnf_clauses": cnf, "native_xor_rows": xors,
                  "decision_ratios": decision_ratios, "wall_ratios": wall_ratios,
                  "full_query_promotion_gate": promoted,
                  "query_status": query_status, "relation_replay": relation_replay}, sort_keys=True))
