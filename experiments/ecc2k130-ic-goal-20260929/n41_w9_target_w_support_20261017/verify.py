"""Read-only terminal audit of exact target-w/code support query."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


for name in ("build_protocol.json", "query_protocol.json"):
    p = read(HERE / name)
    assert p["status"].startswith("FROZEN_BEFORE_")
    for path, expected in p["sources"].items():
        assert sha(path) == expected, (name, path)

bp = read(HERE / "build_protocol.json")
qp = read(HERE / "query_protocol.json")
build = read(HERE / "build_result.json")
query = read(HERE / "query_result.json")
base = read(bp["base_build_result"])
table = read(HERE / "w_code_table.json")
audited_table = read(bp["audited_table"])
audit = read(bp["table_audit"])
assert build["status"] == "PASS_EXACT_TARGET_W_CODE_SUPPORT_BUILD"
assert build["protocol_sha256"] == sha(HERE / "build_protocol.json")
assert build["formula_sha256"] == sha(HERE / "formula.xcnf")
assert build["table_sha256"] == sha(HERE / "w_code_table.json")
assert table == audited_table
assert audit["status"] == "PASS_ALL_CODE_QUARTIC_ROOTS_EQUAL_TARGET_TABLE"
assert build["table_entries"] == build["distinct_w"] == len(table) == 284
assert len({row["code"] for row in table}) == build["distinct_codes"] == 71
assert build["selector_variables"] == 284
assert build["support_clauses"] == 1+284*(41+8)
assert build["variables"] == base["variables"]+build["selector_variables"]
assert build["constraints"] == base["clauses"]+base["native_xor_rows"]+build["support_clauses"]
assert abs(sum(build["phase_seconds"].values())-build["total_seconds"]) < 1e-8
assert build["total_seconds"] < bp["wall_cap_seconds"]
assert build["self_maxrss_bytes"] < bp["rss_cap_bytes"]

assert query["protocol_sha256"] == sha(HERE / "query_protocol.json")
assert query["candidate_id"] is None and query["curve_id"] == qp["curve_id"]
assert query["worker_count"] == 1
assert query["command"] == [qp["solver"], "--threads=1",
           f"--maxtime={qp['solver_cap_seconds']}", "--zero-exit-status",
           "--verb=1", "--printsol=1", str(HERE / "formula.xcnf")]
stdout = (HERE / "solver.stdout").read_bytes()
stderr = (HERE / "solver.stderr").read_bytes()
assert query["solver_stdout_sha256"] == hashlib.sha256(stdout).hexdigest()
assert query["solver_stderr_sha256"] == hashlib.sha256(stderr).hexdigest()
assert query["rss_samples"] > 0
assert query["sampled_peak_combined_rss_bytes"] < qp["rss_cap_bytes"]
assert query["query_parent_wall_seconds"] <= qp["parent_wall_cap_seconds"]+2
assert query["charged_stage_wall_seconds"] == (base["total_seconds"]+
              build["total_seconds"]+query["query_parent_wall_seconds"])
assert query["charged_stage_wall_seconds"] < 600
assert query["monitor_error"] is None
text = stdout.decode(errors="replace")
if query["status"] == "SAT_MODEL_UNVERIFIED":
    assert "s SATISFIABLE" in text and "\nv " in text
    model = read(HERE / "model_audit_result.json")
    assert model["status"] == "PASS_N41_UNPINNED_ORDINARY_RELATION"
elif query["status"] == "UNSAT_UNVERIFIED":
    assert "s UNSATISFIABLE" in text
elif query["status"] == "BOUNDED_UNKNOWN":
    assert query["stop_reason"] == "WALL_CAP" or "s INDETERMINATE" in text
else:
    raise AssertionError(query["status"])
assert not (HERE / "build.stderr").read_bytes()
assert not (HERE / "query.stderr").read_bytes()

print(json.dumps({"verification": "PASS_EXACT_TARGET_W_CODE_SUPPORT_RECEIPTS",
                  "status": query["status"],
                  "table_entries": len(table),
                  "selectors": build["selector_variables"],
                  "charged_stage_wall_seconds": query["charged_stage_wall_seconds"]},
                 sort_keys=True))
