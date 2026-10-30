"""Receipt and cross-file checks for the direct-degree order panel."""
import hashlib
import json
from pathlib import Path

here = Path(__file__).resolve().parent
root = here.parent.parent
plan = json.loads((here / "inputs.json").read_text())
post_selection = json.loads((here / "post-selection.json").read_text())
post_challenge = json.loads((here / "post-challenge.json").read_text())


def sealed(path, digest):
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == digest, path
    return json.loads(raw)


selection = sealed(here / "selection.json", post_selection["selection_sha256"])
challenge = sealed(here / "challenge.json", post_challenge["challenge_sha256"])
assert selection["status"] == "ORDERS_FROZEN" and challenge["status"] == "COMPLETE"
assert len(selection["selected"]) == len(challenge["cases"]) == plan["target_ready_classes"]
audit = json.loads((here / "audit.json").read_text())
assert audit["status"] == "PASS" and len(audit["cases"]) == plan["target_ready_classes"]
for frozen, produced, audited in zip(selection["selected"], challenge["cases"], audit["cases"]):
    assert frozen["p"] == produced["p"] == audited["p"]
    assert produced["status"] == "COMPLETE" and audited["status"] == "PASS"
    assert produced["full_pool_rank_mod_q"] == audited["full_pool_rank_mod_q"]
    assert len(produced["source_entries"]) == audited["source_equations_verified"] == 40
    assert produced["hecke_candidate_count"] == audited["hecke_rows_verified"]
    assert len(frozen["direct_degree"]) == 40
    assert set(frozen["source_orders"]) == {"ascending", "low_degree", "high_degree", "sha"}
    for name, order in frozen["source_orders"].items():
        assert sorted(order) == list(range(40))
        prefixes = produced["order_results"][name]["prefixes"]
        assert [x["source_count"] for x in prefixes] == list(range(41))
        assert prefixes[-1]["rank_mod_q"] == produced["full_pool_rank_mod_q"]
        assert all(a["rank_mod_q"] <= b["rank_mod_q"] for a, b in zip(prefixes, prefixes[1:]))
    assert produced["candidate_id"] is None and produced["target_online_ms"] is None
print("PASS: frozen selection, challenge, and audit receipts")
