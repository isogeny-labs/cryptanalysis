"""Check frozen input digests and the measured span-bound inequalities."""
import hashlib
import json
from pathlib import Path

here = Path(__file__).resolve().parent
root = here.parent.parent
plan = json.loads((here / "inputs.json").read_text())
for family in plan["families"]:
    base = root / family["dir"]
    for name, digest in ((family["selection"], family["selection_sha256"]),
                         (family["challenge"], family["challenge_sha256"]),
                         ("audit.json", family["audit_sha256"])):
        assert hashlib.sha256((base / name).read_bytes()).hexdigest() == digest
helper = plan["pair_index"]
assert hashlib.sha256((root / helper["path"]).read_bytes()).hexdigest() == helper["sha256"]
result = json.loads((here / "result.json").read_text())
assert result["status"] == "PASS" and len(result["cases"]) == 10
for cell in result["cases"]:
    assert cell["status"] == "PASS"
    assert cell["baseline_rank_mod_q"] <= cell["hecke_rank_mod_q"] <= cell["classpart_span_rank_mod_q"] <= 40
    assert cell["bound_gain"] == cell["classpart_span_rank_mod_q"] - cell["baseline_rank_mod_q"]
    assert cell["attained_gain"] == cell["hecke_rank_mod_q"] - cell["baseline_rank_mod_q"]
    assert cell["gap"] == cell["classpart_span_rank_mod_q"] - cell["hecke_rank_mod_q"]
    assert len(cell["prefix"]) == 41
    assert all(x["attained_rank_mod_q"] <= x["bound_rank_mod_q"] for x in cell["prefix"])
    assert cell["candidate_id"] is None and cell["target_online_ms"] is None
print("PASS: sealed inputs and ten class-part span bounds")
