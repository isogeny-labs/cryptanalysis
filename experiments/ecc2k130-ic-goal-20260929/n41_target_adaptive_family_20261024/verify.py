"""Replay the frozen Fermat-vs-trace component comparison receipts."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


cfg = load(HERE / "protocol.json")
result = load(HERE / "result.json")
audit = load(HERE / "audit_result.json")
prior_cfg = load(cfg["sources"]["prior_protocol"]["path"])
prior = load(cfg["sources"]["prior_result"]["path"])
assert all(sha(source["path"]) == source["sha256"] for source in cfg["sources"].values())
assert cfg["status"] == "FROZEN_N41_FOUR_CODE_FERMAT_ZERO"
assert cfg["boxes"] == prior_cfg["boxes"]
assert cfg["suffix_state_ids"] == prior_cfg["suffix_state_ids"]
assert cfg["exponent"] == result["exponent"] == 2**41-1
assert cfg["addition_chain_lengths"] == [1, 2, 4, 5, 10, 20, 40, 41]
assert result["status"] == "PASS_N41_FOUR_CODE_FERMAT_ZERO"
assert audit["status"] == "PASS_INDEPENDENT_SAGE_FOUR_CODE_FERMAT_AUDIT"
assert result["protocol_sha256"] == audit["protocol_sha256"] == sha(HERE / "protocol.json")
assert audit["result_sha256"] == sha(HERE / "result.json")
assert result["candidate_id"] is None and audit["candidate_id"] is None
assert result["boxes"] == prior["boxes"] == 2
assert result["families_covered"] == prior["families_covered"] == 32
assert [row["target_rejected"] for row in result["rows"]] == [row["target_rejected"] for row in prior["rows"]] == [True, False]
assert all(row["fermat_squarings"] == 82 and row["fermat_multiplications"] == 7
           for row in result["rows"])
assert audit["families_checked"] == 32 and audit["roots_checked"] == 256
assert audit["norm_zeros"] == 1 and audit["target_charts_checked"] == 160
assert audit["zero_locations"][0]["code_quad"] == [24, 37, 10, 0]
assert result["wall_seconds"] < cfg["wall_cap_seconds"]
assert audit["wall_seconds"] < cfg["wall_cap_seconds"]
assert max(result["self_maxrss_raw"], audit["self_maxrss_raw"]) < cfg["rss_cap_bytes"]
lean = (HERE / "lean_check.log").read_text()
assert "indicator_eq_one_iff_zero' depends on axioms: [propext]" in lean
assert "addition_chain_exponents' does not depend on any axioms" in lean
print(json.dumps({"status": "PASS_N41_FERMAT_ZERO_RECEIPTS",
                  "fermat_wall_seconds": result["wall_seconds"],
                  "trace_wall_seconds": prior["wall_seconds"],
                  "roots_checked": audit["roots_checked"]}, sort_keys=True))
