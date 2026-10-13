"""Freeze and control the signature gate; require all-source replay for query."""

import argparse
import hashlib
import json
from pathlib import Path

import gate

HERE = Path(__file__).resolve().parent
SAT = HERE / "sat"
prior = gate.prior


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sources():
    result = gate.sources()
    # The independent audit protocol is frozen before the constructed
    # control. The public query additionally requires its terminal PASS.
    result["linked_signature_sage_audit"] = HERE / "audit_protocol.json"
    result["linked_signature_table_audit"] = HERE / "table_audit_result.json"
    result["signature_gate_runner"] = Path(__file__)
    result["balanced_runner"] = Path(__file__)
    return result


def query():
    audit = json.loads((HERE / "audit_result.json").read_text())
    frozen = json.loads((HERE / "audit_protocol.json").read_text())
    assert audit["status"] == "PASS_INDEPENDENT_SAGE_ALL_W18_LINKED_SIGNATURES"
    assert audit["audit_protocol_sha256"] == sha(HERE / "audit_protocol.json")
    assert frozen["sha256"]["rows"] == sha(HERE / "rows.tsv.gz")
    assert frozen["sha256"]["audit_source"] == sha(HERE / "audit_sage.py")
    return prior.query()


prior.HERE = SAT
prior.orbit9.HERE = SAT
prior.sources = sources
prior.orbit9.sources = sources


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("freeze", "control", "query"))
    choice = parser.parse_args().mode
    {"freeze": prior.freeze, "control": prior.control,
     "query": query}[choice]()
