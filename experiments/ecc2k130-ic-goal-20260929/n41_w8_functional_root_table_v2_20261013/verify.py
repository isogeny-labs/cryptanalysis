"""Read-only verification of the frozen N41 functional root-table experiment."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


def checked_sources(record):
    for name, digest in record.items():
        assert sha(Path(name)) == digest, name


protocol = read("protocol.json")
assert protocol["status"] == "FROZEN_BEFORE_N41_W8_SELECTOR_CONTROL_AND_PUBLIC"
assert protocol["candidate_id"] is None
checked_sources(protocol["source_sha256"])
assert sha(HERE / "preflight.json") == protocol["preflight_sha256"]
preflight = read("preflight.json")
assert preflight["status"] == "PASS_N41_W8_FUNCTIONAL_ROOT_PREFLIGHT"
assert (preflight["exact_pair_codes"], preflight["root_entries"],
        preflight["support_masks"]) == (40, 80, 125)

control_protocol = read("control_run_protocol.json")
checked_sources(control_protocol["sources"])
control_run = read("control_run_result.json")
assert control_run["status"] == "EXIT_0"
assert control_run["protocol_sha256"] == sha(HERE / "control_run_protocol.json")
for name, digest in control_run["sha256"].items():
    assert sha(HERE / name) == digest, name
control = read("control_result.json")
assert control["status"] == "PASS_N41_SELECTOR_CONSTRUCTED_ASSIGNMENT"
assert control["assignment_check"] == {"clauses": 67329, "native_xor_rows": 8439}
assert control["formula_sha256"] == sha(HERE / "public.xcnf")

public_protocol = read("public_protocol.json")
checked_sources(public_protocol["sources"])
public = read("public_result.json")
assert public["status"] == "BOUNDED_UNKNOWN"
assert public["stop_reason"] == "PARENT_WALL_CAP"
assert public["protocol_sha256"] == sha(HERE / "public_protocol.json")
assert public["terminal_lines"] == []
assert public["wall_ns"] <= 186_000_000_000
for name, digest in public["sha256"].items():
    assert sha(HERE / name) == digest, name
assert "Executed with command line:" in (HERE / "solver.stdout").read_text()

bdd_protocol = read("bdd_protocol.json")
checked_sources(bdd_protocol["sources"])
bdd = read("bdd_result.json")
assert bdd["status"] == "PASS_EXHAUSTIVE_N41_FUNCTIONAL_ROOT_BDD"
assert (bdd["valid_pair_codes"], bdd["root_branches_checked"]) == (40, 80)
assert bdd["formula_sha256"] == control["formula_sha256"]
print(json.dumps({"status": "PASS_FROZEN_N41_FUNCTIONAL_ROOT_V2",
                  "public_status": public["status"],
                  "control_status": control["status"],
                  "root_branches_checked": 80}, sort_keys=True))
