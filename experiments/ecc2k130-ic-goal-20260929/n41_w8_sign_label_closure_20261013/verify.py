"""Read-only verifier for sign, source-label, Sage, XCNF, and Lean receipts."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PRIOR = ROOT / "n41_w8_functional_root_table_v2_20261013"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


def sources(record):
    assert record["status"] == "FROZEN"
    for name, digest in record["sources"].items():
        assert sha(Path(name)) == digest, name


p = read("protocol.json")
sources(p)
assert p["candidate_id"] is None
r = read("result.json")
assert r["status"] == "PASS_N41_W8_SIGN_AND_LABEL_CLOSURE"
assert r["curve_id"] == p["curve_id"]
assert r["public_point"] == p["public_point"]
assert r["raw_target"] == p["raw_target"]
assert len(r["slots"]) == 7
assert all(s["codes"] == 40 and s["coordinate_roots"] == 80
           and s["signed_raw_points"] == 160 and s["sign_fibers_checked"] == 80
           for s in r["slots"])
assert (r["ordered_conflicting_code_pairs_per_slot_pair"], r["slot_pairs"],
        r["total_cross_slot_conflict_clauses"]) == (46, 21, 966)

sage_protocol = read("sage_protocol.json")
sources(sage_protocol)
sage_run = read("sage_run_result.json")
assert sage_run["status"] == "EXIT_0" and sage_run["exit_code"] == 0
assert sage_run["stop_reason"] is None
assert sage_run["wall_ns"] < 600 * 10**9
assert sage_run["protocol_sha256"] == sha(HERE / "sage_protocol.json")
for name, digest in sage_run["sha256"].items():
    assert sha(HERE / name) == digest, name
sage = read("sage_result.json")
assert sage["status"] == "PASS_INDEPENDENT_SAGE_N41_SEVENPAIR_ALL_STATES"
assert sage["states_checked"] == 1120
assert sage["distinct_unrotated_raw_leaves"] == 160
assert [s["source_states_checked"] for s in sage["slots"]] == [160] * 7
assert read("sage_runtime_info.json")["status"] == "verified"

formula_protocol = read("formula_protocol.json")
sources(formula_protocol)
f = read("formula_result.json")
assert f["status"] == "PASS_FROZEN_SEVENPAIR_XCNF_LABEL_CLAUSES"
assert f["expected_conflict_clauses"] == f["present_conflict_clauses"] == 966
assert f["rebuilt_formula_sha256"] == sha(HERE / "rebuilt_public.xcnf")
assert f["rebuilt_formula_sha256"] == sha(PRIOR / "public.xcnf")
assert (f["variables"], f["clauses"], f["native_xor_rows"]) == (30536, 67329, 8439)
assert "ModuleNotFoundError: No module named 'psutil'" in (HERE / "first_formula_launch_failure.txt").read_text()
lean = (HERE / "lean_check.log").read_text()
assert "'SignLift.target_reachable' does not depend on any axioms" in lean
assert all(word not in (HERE / "SignLift.lean").read_text()
           for word in ("sorry", "admit", "sorryAx"))
print("PASS_FROZEN_N41_SEVENPAIR_SIGN_LABEL_CLOSURE")
