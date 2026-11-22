"""Check frozen inputs and both archived propagation outcomes."""

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "n41_sixpair_shared_target_20261017"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    result = json.loads((HERE / "result.json").read_text())
    audit = json.loads((HERE / "audit_result.json").read_text())
    assert protocol["source_sha256"] == {
        "script": sha(HERE / "screen.py"),
        "public_xcnf": sha(SOURCE / "public.xcnf"),
        "independent_join_witness": sha(SOURCE / "join_audit_result.json"),
    }
    assert result["protocol_sha256"] == sha(HERE / "protocol.json")
    assert result["public_xcnf_sha256"] == protocol["source_sha256"]["public_xcnf"]
    assert audit["input_sha256"] == {
        "auditor": sha(HERE / "audit.py"),
        "public_xcnf": protocol["source_sha256"]["public_xcnf"],
        "protocol": sha(HERE / "protocol.json"),
        "result": sha(HERE / "result.json"),
    }
    assert result["status"] == "PASS_BOUNDED_CODE_PROPAGATION_SCREEN"
    assert audit["status"] == "PASS_INDEPENDENT_FULL_SCAN_PROPAGATION_REPLAY"
    assert result["code_count"] == audit["code_count"] == 40
    assert result["conflicts"] == audit["conflicts"] == 0
    assert result["open_families"] == 40
    assert len(result["rows"]) == len(audit["rows"]) == 40
    assert [(r["code"], r["status"], r["assigned_variables"])
            for r in result["rows"]] == [
            (r["code"], r["status"], r["assigned_variables"])
            for r in audit["rows"]]
    assert result["witness_code"] == 6
    assert all(r["status"] == "OPEN" for r in result["rows"])
    assert (HERE / "run.stderr").read_text() == ""
    assert (HERE / "audit.stderr").read_text() == ""
    print("PASS_N41_CODE_PROPAGATION_ARCHIVE 40 0")


if __name__ == "__main__":
    main()
