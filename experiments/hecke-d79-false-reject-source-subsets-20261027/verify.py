"""Lightweight receipt checks; run_sage.py performs the group and rank replay."""
import hashlib
import json
from pathlib import Path

here = Path(__file__).resolve().parent
root = here.parent.parent
plan = json.loads((here / "inputs.json").read_text())
source = root / plan["source_dir"]
for name, key in (("gate-result.json", "gate_sha256"),
                  ("challenge-result.json", "challenge_sha256"),
                  ("audit.json", "audit_sha256")):
    assert hashlib.sha256((source / name).read_bytes()).hexdigest() == plan[key]
result = json.loads((here / "result.json").read_text())
assert result["status"] == "PASS"
assert result["p"] == plan["target_p"] and result["q"] == 197
assert result["baseline_rank_mod_q"] == 35
assert result["full_rank_mod_q"] == result["inclusion_minimal_rank_mod_q"] == 39
assert len(result["ascending_prefix"]) == 41
assert [p["source_count"] for p in result["ascending_prefix"]] == list(range(41))
assert all(a["rank_mod_q"] <= b["rank_mod_q"] for a, b in zip(result["ascending_prefix"], result["ascending_prefix"][1:]))
assert min(p["source_count"] for p in result["ascending_prefix"] if p["rank_mod_q"] == 39) == result["first_rank39_prefix_count"]
assert result["inclusion_minimal_source_count"] == len(result["inclusion_minimal_source_ids"])
assert result["inclusion_minimal_hecke_row_count"] == len(result["inclusion_minimal_hecke_rows"])
assert set().union(*(set(x["source_ids"]) for x in result["inclusion_minimal_hecke_rows"])) == set(result["inclusion_minimal_source_ids"])
assert result["candidate_id"] is None and result["target_online_ms"] is None
print("PASS: frozen receipts and subset summary")
