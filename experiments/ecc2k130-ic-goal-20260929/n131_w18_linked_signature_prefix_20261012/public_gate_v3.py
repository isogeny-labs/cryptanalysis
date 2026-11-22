"""Run the ordinary public query only after exact all-root audit promotion."""

import hashlib
import json
from pathlib import Path

import gate_v2

HERE = Path(__file__).resolve().parent
SAT = HERE / "sat"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def query():
    frozen = json.loads((HERE / "public_gate_protocol.json").read_text())
    for name, path in {
        "runner": Path(__file__),
        "sat_protocol": SAT / "protocol.json",
        "constructed_control": SAT / "control_result.json",
        "control_archive": HERE / "archive_receipt.json",
        "table_audit": HERE / "table_audit_result.json",
        "hash_manifest": HERE / "hash_manifest.json",
        "fast_audit": HERE / "fast_audit_result.json",
        "fast_audit_protocol": HERE / "fast_audit_protocol.json",
        "source_table": HERE / "rows.tsv.gz",
    }.items():
        assert sha(path) == frozen["sha256"][name], name
    fast = json.loads((HERE / "fast_audit_result.json").read_text())
    assert fast["status"] == "PASS_INDEPENDENT_SAGE_ALL_W18_LINKED_ADDITION_FORMULAS"
    assert fast["source_codes"] == 33191
    assert fast["pair_output_roots"] == 66382
    assert fast["signed_additions_replayed"] == 4 * 66382
    assert fast["zero_signature_differences"] == 0
    assert fast["audit_protocol_sha256"] == sha(HERE / "fast_audit_protocol.json")
    control = json.loads((SAT / "control_result.json").read_text())
    assert control["status"] == "PASS_FULL_N131_LINKED_TENPAIR_CONSTRUCTED_WITNESS"
    assert control["formula"]["xcnf_sha256"] == json.loads(
        (HERE / "archive_receipt.json").read_text())["raw_sha256"]
    gate_v2.prior.protocol()
    return gate_v2.prior.query()


if __name__ == "__main__":
    query()
