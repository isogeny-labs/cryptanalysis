"""Verify input/code seals and all paired exact-output receipts."""
import hashlib
import json
from pathlib import Path

here = Path(__file__).resolve().parent
root = here.parent.parent
plan = json.loads((here / "inputs.json").read_text())
post = json.loads((here / "post-run.json").read_text())
seal = json.loads((here / post["implementation_seal"]).read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


assert sha(here / "result.json") == post["result_sha256"]
assert sha(here / "pair_index.py") == seal["pair_index_sha256"]
assert sha(here / "benchmark_sage.py") == seal["benchmark_sage_sha256"]
helper = plan["exhaustive_helper"]
assert sha(root / helper["path"]) == helper["sha256"]
for family in plan["families"]:
    base = root / family["dir"]
    assert sha(base / family["selection"]) == family["selection_sha256"]
    assert sha(base / family["challenge"]) == family["challenge_sha256"]
    assert sha(base / "audit.json") == family["audit_sha256"]
result = json.loads((here / "result.json").read_text())
assert result["status"] == "COMPLETE" and len(result["cases"]) == 10
assert result["repetitions"] == 3 and result["pair_index_sha256"] == seal["pair_index_sha256"]
for cell in result["cases"]:
    assert cell["status"] == "COMPLETE" and len(cell["pairs"]) == 3
    for record in cell["pairs"]:
        assert record["status"] == "EXACT_ROWS_MATCH"
        assert set(record["methods"]) == {"exhaustive", "pair_index"}
        exhaustive = record["methods"]["exhaustive"]
        indexed = record["methods"]["pair_index"]
        assert exhaustive["row_digest"] == indexed["row_digest"]
        assert exhaustive["row_count"] == indexed["row_count"] == cell["expected_candidate_count"]
        assert exhaustive["signed_support_trials"] == 772240
        assert indexed["signed_singleton_insertions"] == 80
        assert indexed["signed_pair_insertions"] == indexed["complement_bucket_probes"] == 3120
        assert indexed["group_add_calls"] < exhaustive["group_add_calls"]
        assert indexed["group_neg_calls"] < exhaustive["group_neg_calls"]
        assert exhaustive["wall_ns"] > 0 and indexed["wall_ns"] > 0
    assert cell["candidate_id"] is None and cell["target_online_ms"] is None
print("PASS: ten sealed classes, 30 exact paired matches, and Lean source receipts")
