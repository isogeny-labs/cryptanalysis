"""Check sealed custody and both exact-row audits."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    seal = json.loads((HERE / "post-audit.json").read_text())
    for name, digest in seal["sha256"].items():
        assert sha(HERE / name) == digest, name
    first = json.loads((HERE / "audit.json").read_text())
    second = json.loads((HERE / "micro-audit.json").read_text())
    for audit, index_name in ((first, "index.json"), (second, "micro-index.json")):
        index = json.loads((HERE / index_name).read_text())
        assert audit["status"] == "PASS" and index["status"] == "COMPLETE"
        assert len(audit["cases"]) == len(index["cases"]) == 9
        assert all(case["status"] == "PASS" for case in audit["cases"])
        assert audit["candidate_id"] is None and audit["target_online_ms"] is None
    assert (first["fresh_triple_sum_add_calls"], first["fresh_symmetric_add_calls"],
            first["fresh_add_reduction"]) == (49121207, 48976287, 144920)
    assert second["fresh_symmetric_add_calls"] == second["fresh_micro_add_calls"] == 48976287
    print(json.dumps({"status": "PASS", "cases": 9, "fresh_cases": 8,
                      "full_add_calls": first["fresh_triple_sum_add_calls"],
                      "symmetric_add_calls": first["fresh_symmetric_add_calls"],
                      "micro_add_calls": second["fresh_micro_add_calls"]}, sort_keys=True))


if __name__ == "__main__":
    main()
