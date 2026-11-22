"""Read-only validation of frozen symbolic-label and exact-join records."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(name):
    return json.loads((HERE / name).read_text())


for name in ("protocol.json", "exact_protocol.json", "audit_protocol.json"):
    record = load(name)
    assert record["status"] == "FROZEN"
    for path, expected in record["sources"].items():
        assert digest(path) == expected, (name, path)

build, sat, exact, exact_run, audit, audit_run = (
    load(name) for name in ("build_result.json", "run_result.json", "exact_result.json",
                           "exact_run_result.json", "audit_result.json", "audit_run_result.json"))
assert build["status"] == "FORMULAS_BUILT"
assert sat["status"] == "COMPLETE_MONITORED_PAIR"
assert exact["status"] == "COMPLETE_EXACT_REGION_JOIN"
assert audit["status"] == "PASS_INDEPENDENT_EIGHT_FAMILY_SAGE_REPLAY"
assert sat["protocol_sha256"] == digest(HERE / "protocol.json")
assert exact["protocol_sha256"] == exact_run["protocol_sha256"] == digest(HERE / "exact_protocol.json")
assert audit_run["protocol_sha256"] == digest(HERE / "audit_protocol.json")

for case, row in zip(build["cases"], sat["cases"]):
    name = case["name"]
    assert row["name"] == name
    assert digest(HERE / f"{name}.xcnf") == case["formula_sha256"]
    assert digest(HERE / f"{name}.stdout") == row["stdout_sha256"]
    assert digest(HERE / f"{name}.stderr") == row["stderr_sha256"]
    assert row["stop_reason"] == "PARENT_WALL_CAP" and row["exit_code"] == -15
    assert not row["raw_solver_status_lines"] and not row["monitor_degraded"]
    assert row["sampled_peak_combined_rss_bytes"] < load("protocol.json")["rss_cap_bytes"]
    assert "c rst" in (HERE / f"{name}.stdout").read_text()
assert build["cases"][0]["constructed_assignment_checked"]
assert all(case["primary_variables"] == 18 and case["symbolic_label_bits"] == 4
           for case in build["cases"])

for name, run, protocol in (("exact", exact_run, "exact_protocol.json"),
                            ("audit", audit_run, "audit_protocol.json")):
    assert run["status"] == "EXIT_0" and run["exit_code"] == 0
    assert run["stop_reason"] is None
    assert run["wall_ns"] < load(protocol)["wall_cap_seconds"] * 10**9
    assert run["sampled_peak_combined_rss_bytes"] < load(protocol)["rss_cap_bytes"]
    for path, expected in run["sha256"].items():
        assert digest(HERE / path) == expected, (name, path)
assert not audit_run["monitor_degraded"]
# The exact native runner had a process-exit sampling race. Its wall/status
# and output are retained, but its sampled peak is not promoted as a complete
# memory certificate.
assert exact_run["monitor_degraded"]

assert [row["exact_coordinate_hits"] for row in exact["cases"]] == [1, 0]
assert [[x["c"], x["d"]] for x in exact["cases"][0]["hits"]] == [
    [940337512568, 1570560155378]]
assert all(row["left_unique_outputs"] == 316 and row["right_unique_outputs"] == 252
           and row["root_proposals"] == 334 for row in exact["cases"])
for row, independent in zip(exact["cases"], audit["cases"]):
    assert row["name"] == independent["name"]
    assert [[x["c"], x["d"]] for x in row["hits"]] == independent["coordinate_hits"]
    assert row["left_unique_outputs"] == independent["left_outputs"]
    assert row["right_unique_outputs"] == independent["right_outputs"]

terminal = {"status": "PASS_FROZEN_LABEL_REGION_DIAGNOSTIC",
            "constructed_exact_hits": 1, "public_exact_hits": 0,
            "sat_case_statuses": ["BOUNDED_UNKNOWN_PARENT_CAP"] * 2,
            "independent_sage_replay": "PASS",
            "exact_memory_monitor_degraded": True,
            "evidence_sha256": {name: digest(HERE / name) for name in
                                ("build_result.json", "run_result.json", "exact_result.json",
                                 "audit_result.json")}}
print(json.dumps(terminal, indent=2, sort_keys=True))
