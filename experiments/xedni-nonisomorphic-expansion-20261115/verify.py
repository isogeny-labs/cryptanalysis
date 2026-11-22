"""Check frozen receipts, proof status and the experiment file seal."""
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    screen = json.loads((HERE / "result.json").read_text())
    relation = json.loads((HERE / "relation-result.json").read_text())
    audit = json.loads((HERE / "audit.json").read_text())
    generator = json.loads((HERE / "generator.json").read_text())
    assert screen["status_counts"] == {"completed": 14, "rank_unknown": 1, "timeout": 1}
    assert len(screen["rows"]) == 16
    assert screen["protocol_sha256"] == sha(HERE / "protocol.json")
    assert screen["source_sha256"] == sha(HERE / "screen.py")
    assert screen["worker_sha256"] == sha(HERE / "worker.py")
    for row in screen["rows"]:
        assert sha(HERE / row["stdout_path"]) == row["stdout_sha256"]
        assert sha(HERE / row["stderr_path"]) == row["stderr_sha256"]
    assert generator["generator_status"] == "proved" and generator["point_is_signed_generator"]
    assert relation["status"] == audit["status"] == "PASS"
    assert relation["raw_sha256"] == sha(HERE / "relation-rows.jsonl.gz")
    assert relation["source_sha256"] == sha(HERE / "relation.py")
    assert relation["screen_sha256"] == sha(HERE / "result.json")
    assert relation["generator_sha256"] == sha(HERE / "generator.json")
    assert relation["queries"] == audit["queries"] == 109561
    assert relation["membership_tests"] == audit["membership_tests"] == 219122
    assert sum(len(m["hits"]) for m in relation["models"]) == audit["relations"] == 8
    for name in ("screen.stderr", "generator.stderr", "relation.stderr", "audit.stderr"):
        assert (HERE / name).read_bytes() == b""
    build = (HERE / "formal" / "build-output.txt").read_text()
    assert "Build completed successfully (3138 jobs)." in build
    assert "pair_union_card_331' depends on axioms: [propext, Classical.choice, Quot.sound]" in build
    source = (HERE / "formal" / "ExpansionUnion.lean").read_text()
    for forbidden in (r"\bsorry\b", r"\badmit\b", r"\bsorryAx\b", r"\bnative_decide\b", r"\baxiom\s+"):
        assert re.search(forbidden, source) is None
    for line in (HERE / "SEAL.sha256").read_text().splitlines():
        digest, rel = line.split("  ", 1)
        assert sha(HERE / rel) == digest, rel
    print(json.dumps({"schema": "xedni-nonisomorphic-expansion-verify-v1", "status": "PASS",
                      "screen_cells": 16, "queries": 109561, "relations": 8}, sort_keys=True))

if __name__ == "__main__":
    main()
