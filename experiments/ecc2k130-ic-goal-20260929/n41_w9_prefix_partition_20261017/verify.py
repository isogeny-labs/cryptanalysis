"""Replay the frozen N41 prefix panel's source, formulas, and receipts."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text())


protocol = read_json(HERE / "protocol.json")
assert protocol["status"] == "FROZEN_BEFORE_N41_PREFIX_PANEL"
assert protocol["candidate_id"] is None
for path, expected in protocol["sources"].items():
    assert digest(Path(path).read_bytes()) == expected, path
assert protocol["prefix_order"] == list(range(8))
assert protocol["prefix_wires"] == [6, 7, 8]

wires = read_json(protocol["wires"])
allowed = wires["allowed_code_words"]
assert len(allowed) == len(set(allowed)) == 71
assert all(0 <= code < 256 for code in allowed)
assert wires["codes"][0][5:8] == protocol["prefix_wires"]
counts = {str(k): sum(code // 32 == k for code in allowed)
          for k in protocol["prefix_order"]}
assert counts == protocol["source_counts"]
assert sum(counts.values()) == 71

base = Path(protocol["base_formula"]).read_bytes()
old_header = b"p cnf 123218 339484\n"
assert base.startswith(old_header)
build = read_json(protocol["base_build_result"])
assert build["variables"] == 123218
assert build["clauses"] + build["native_xor_rows"] == 339484
assert build["formula_sha256"] == digest(base)
positive = build["witness_control"]
assert positive["all_clauses_and_xors_satisfied"]
assert positive["codes"][0] == 93 and 93 // 32 == 2

result = read_json(HERE / "result.json")
assert result["protocol_sha256"] == digest((HERE / "protocol.json").read_bytes())
assert result["curve_id"] == protocol["curve_id"]
assert result["candidate_id"] is None
assert result["worker_count"] == 1
assert result["prefix_order"] == protocol["prefix_order"]
assert result["source_counts"] == counts
assert result["target_dependent_base_build_seconds"] == build["total_seconds"]
accounting_gap = result["charged_stage_wall_seconds"] - (
    build["total_seconds"] + result["panel_parent_wall_seconds"])
# The producer reads its monotonic clock twice when filling these two fields.
assert 0 <= accounting_gap < 0.01
assert result["panel_parent_wall_seconds"] <= protocol["total_wall_cap_seconds"] + 2
assert result["charged_stage_wall_seconds"] < 600
assert not (HERE / "prefix_work.xcnf").exists()

rows = result["rows"]
assert 1 <= len(rows) <= 8
assert [row["prefix"] for row in rows] == protocol["prefix_order"][:len(rows)]
partial = read_json(HERE / "partial.json")
assert partial["status"] == "PARTIAL" and partial["rows"] == rows
assert partial["protocol_sha256"] == result["protocol_sha256"]
for row in rows:
    block = row["prefix"]
    assert row["source_code_count"] == counts[str(block)]
    clauses = b"".join(
        f"{wire if (block >> bit) & 1 else -wire} 0\n".encode()
        for bit, wire in enumerate(protocol["prefix_wires"]))
    formula = b"p cnf 123218 339487\n" + base[len(old_header):] + clauses
    assert digest(formula) == row["formula_sha256"]
    assert row["command"] == [protocol["solver"], "--threads=1",
               f"--maxtime={protocol['solver_cap_seconds']}",
               "--zero-exit-status", "--verb=1", "--printsol=1",
               str(HERE / "prefix_work.xcnf")]
    output = (HERE / f"prefix_{block}.stdout").read_bytes()
    errors = (HERE / f"prefix_{block}.stderr").read_bytes()
    assert digest(output) == row["stdout_sha256"]
    assert digest(errors) == row["stderr_sha256"]
    assert 0 < row["parent_wall_seconds"] <= protocol["per_prefix_wall_cap_seconds"] + 2
    assert 0 < row["sampled_peak_combined_rss_bytes"] <= protocol["rss_cap_bytes"]
    text = output.decode(errors="replace")
    if row["status"] == "UNSAT_UNVERIFIED":
        assert "s UNSATISFIABLE" in text
    elif row["status"] == "SAT_MODEL_UNVERIFIED":
        assert "s SATISFIABLE" in text and "\nv " in text
    elif row["status"] == "INDETERMINATE_SOLVER_CAP":
        assert "s INDETERMINATE" in text
    elif row["status"] in {"PREFIX_WALL_CAP", "TOTAL_WALL_CAP", "RSS_CAP"}:
        assert row["stop_reason"] == row["status"]
    elif row["status"] not in {"MONITOR_FAILURE", "PRODUCER_FAILURE_NO_TERMINAL_STATUS"}:
        raise AssertionError(row["status"])

if len(rows) == 8:
    assert result["status"] == ("UNSAT_UNVERIFIED" if all(
        row["status"] == "UNSAT_UNVERIFIED" for row in rows)
        else "BOUNDED_UNKNOWN")
else:
    assert result["status"] in {
        "BOUNDED_UNKNOWN_TOTAL_CAP", "SAT_MODEL_UNVERIFIED", "RSS_CAP",
        "MONITOR_FAILURE", "TOTAL_WALL_CAP", "PRODUCER_FAILURE_NO_TERMINAL_STATUS"}

print(json.dumps({"verification": "PASS_EXACT_PREFIX_PANEL_RECEIPTS",
                  "status": result["status"], "rows": len(rows),
                  "represented_first_codes": sum(row["source_code_count"] for row in rows),
                  "positive_control_prefix": 2,
                  "accounting_gap_seconds": accounting_gap,
                  "charged_stage_wall_seconds": result["charged_stage_wall_seconds"]},
                 sort_keys=True))
