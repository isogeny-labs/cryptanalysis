"""Validate saved source bindings, independent audits and file seal."""
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    selection = json.loads((HERE / "selection.json").read_text())
    screen = json.loads((HERE / "result.json").read_text())
    generators = json.loads((HERE / "generators.json").read_text())
    relation = json.loads((HERE / "relation-result.json").read_text())
    scalar = json.loads((HERE / "relation-scalar-result.json").read_text())
    audit = json.loads((HERE / "audit.json").read_text())
    sage = json.loads((HERE / "sage-audit.json").read_text())
    assert selection["selected"] == protocol["expected_fields"]
    for data, key, file in ((selection,"protocol_sha256","protocol.json"),
                            (selection,"source_sha256","select_fields.py"),
                            (screen,"protocol_sha256","protocol.json"),
                            (screen,"source_sha256","screen.py"),
                            (screen,"worker_sha256","worker.py"),
                            (screen,"input_sha256","selection.json"),
                            (generators,"screen_sha256","result.json"),
                            (generators,"source_sha256","generator_screen.py"),
                            (generators,"worker_sha256","generator.py"),
                            (relation,"protocol_sha256","relation-protocol.json"),
                            (relation,"source_sha256","relation.py"),
                            (relation,"selection_sha256","selection.json"),
                            (relation,"screen_sha256","result.json"),
                            (relation,"generators_sha256","generators.json")):
        assert data[key] == sha(HERE / file), (key, file)
    for row in screen["rows"] + generators["rows"]:
        assert sha(HERE / row["stdout_path"]) == row["stdout_sha256"]
        assert sha(HERE / row["stderr_path"]) == row["stderr_sha256"]
    assert screen["status_counts"] == {"completed":30,"rank_unknown":3,"timeout":7}
    assert len(screen["rows"]) == 40 and len(generators["rows"]) == 3
    assert all(r["generator"]["point_is_signed_generator"] for r in generators["rows"])
    assert relation["status"] == audit["status"] == sage["status"] == "PASS"
    assert relation["fields"] == scalar["fields"] and relation["totals"] == scalar["totals"]
    assert relation["source_sha256"] != scalar["source_sha256"]
    assert scalar["source_sha256"] == sha(HERE / "relation_scalar_index.py")
    assert relation["totals"]["queries"] == audit["queries"] == 9875576
    assert relation["totals"]["rational_relations"] == audit["rational_relations"] == sage["rational_relations"] == 44
    assert relation["totals"]["unique_relation_queries"] == audit["unique_relation_queries"] == 40
    for field in relation["fields"]:
        assert sha(HERE / field["raw_path"]) == field["raw_sha256"]
        assert field["first_direct"]["query_index_one_based"] < field["first_rational"]["query_index_one_based"]
    for file in ("screen.stderr","generator-screen.stderr","relation.stderr","audit.stderr","sage-audit.stderr"):
        assert (HERE / file).read_bytes() == b""
    build = (HERE / "formal" / "build-output.txt").read_text()
    assert "Build completed successfully (3138 jobs)." in build
    for name in ("pair_union_card_751","pair_union_card_883","pair_union_card_983"):
        assert f"{name}' depends on axioms: [propext, Classical.choice, Quot.sound]" in build
    source = (HERE / "formal" / "HoldoutUnion.lean").read_text()
    for forbidden in (r"\bsorry\b",r"\badmit\b",r"\bsorryAx\b",r"\bnative_decide\b",r"\baxiom\s+"):
        assert re.search(forbidden, source) is None
    for line in (HERE / "SEAL.sha256").read_text().splitlines():
        digest, rel = line.split("  ", 1)
        assert sha(HERE / rel) == digest, rel
    print(json.dumps({"schema":"xedni-nonisomorphic-holdout-verify-v1","status":"PASS",
                      "fields":8,"screen_cells":40,"queries":9875576,"relations":44},sort_keys=True))

if __name__ == "__main__":
    main()
