"""Check final custody and aggregate triple-sum result."""
import hashlib
import json
from pathlib import Path
HERE = Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    post = json.loads((HERE / "post-audit.json").read_text())
    for name, digest in post["sha256"].items():
        assert sha(HERE / name) == digest, name
    audit = json.loads((HERE / "audit.json").read_text())
    index = json.loads((HERE / "index.json").read_text())
    assert audit["status"] == "PASS" and index["status"] == "COMPLETE"
    assert len(audit["cases"]) == len(index["cases"]) == 9
    assert (audit["fresh_pair_sum_add_calls"], audit["fresh_triple_sum_add_calls"],
            audit["fresh_add_reduction"]) == (95847008, 49121207, 46725801)
    assert all(c["status"] == "PASS" for c in audit["cases"])
    print(json.dumps({"status": "PASS", "fresh_cases": 8,
        "pair_sum_add_calls": audit["fresh_pair_sum_add_calls"],
        "triple_sum_add_calls": audit["fresh_triple_sum_add_calls"],
        "add_reduction": audit["fresh_add_reduction"],
        "add_reduction_fraction": audit["fresh_add_reduction_fraction"]}, sort_keys=True))

if __name__ == "__main__":
    main()
