"""Check sealed custody and paired probe accounting without Sage imports."""
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
    index = json.loads((HERE / "index.json").read_text())
    audit = json.loads((HERE / "audit.json").read_text())
    assert index["status"] == "COMPLETE" and audit["status"] == "PASS"
    assert len(index["cases"]) == len(audit["cases"]) == 9
    fresh = []
    for case, checked in zip(index["cases"], audit["cases"]):
        assert (case["p"], case["q"], case["cohort"]) == (checked["p"], checked["q"], checked["cohort"])
        assert checked["status"] == "PASS"
        assert sha(HERE / case["journal"]) == case["journal_sha256"]
        assert sha(HERE / case["summary"]) == case["summary_sha256"]
        summary = json.loads((HERE / case["summary"]).read_text())
        assert summary["actual_eight_probes"] == case["actual_eight_probes"] == checked["probes"]
        assert summary["first_eight_source_count"] == case["first_eight_source_count"]
        assert summary["final_rank_eight_mod_q"] == {"lex": 39, "reverse_lex": 39}
        assert all(x["anchored_log_replay"] == "PASS" for x in summary["eight_replay"].values())
        if case["cohort"] == "fresh":
            fresh.append(case)
    assert len(fresh) == 8
    lex = sum(x["actual_eight_probes"]["lex"] for x in fresh)
    reverse = sum(x["actual_eight_probes"]["reverse_lex"] for x in fresh)
    assert (lex, reverse) == (53958650, 47016625)
    assert all(x["actual_eight_probes"]["reverse_lex"] < x["actual_eight_probes"]["lex"] for x in fresh)
    output = {"status": "PASS", "fresh_cases": 8, "lex_probes": lex,
              "reverse_lex_probes": reverse, "probe_difference": lex - reverse,
              "lex_over_reverse": lex / reverse,
              "reverse_reduction_fraction": (lex-reverse)/lex}
    print(json.dumps(output, sort_keys=True))

if __name__ == "__main__":
    main()
