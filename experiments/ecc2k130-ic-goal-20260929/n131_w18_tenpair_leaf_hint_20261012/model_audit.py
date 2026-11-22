"""Independent literal-level check of the SAT model against archived XCNF."""

import gzip
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "n131_w18_tenpair_binary_frob_20261012"
ARM = "selector10_output10_intermediate8"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, obj):
    with path.open("x") as stream:
        json.dump(obj, stream, sort_keys=True, indent=2)
        stream.write("\n")


def freeze():
    result = json.loads((HERE / "result.json").read_text())
    assert result["arms"][-1]["arm"] == ARM
    assert result["arms"][-1]["status"] == "SAT"
    paths = [HERE / "leaf.py", HERE / "result.json", HERE / f"{ARM}.stdout",
             HERE / f"{ARM}.xcnf.gz", SOURCE / "sage_fixture_result.json",
             Path(__file__)]
    save(HERE / "model_audit_protocol.json", {
        "status": "FROZEN_BEFORE_MODEL_AUDIT",
        "inputs": {str(path): sha(path) for path in paths},
        "curve_id": "EC1N131Ckb1heb5f1998f20b",
        "arm": ARM,
        "check": "all literal assignments, CNF rows, native XOR rows, unit hints, archived point-chain receipt",
    })


def run():
    protocol = json.loads((HERE / "model_audit_protocol.json").read_text())
    assert protocol["status"] == "FROZEN_BEFORE_MODEL_AUDIT"
    for path, digest in protocol["inputs"].items():
        assert sha(path) == digest, path
    sage = json.loads((SOURCE / "sage_fixture_result.json").read_text())
    assert "PASS" in sage["status"]
    log = (HERE / f"{ARM}.stdout").read_text(errors="replace").splitlines()
    assert [line for line in log if line.startswith("s ")] == ["s SATISFIABLE"]
    assigned = {}
    for line in log:
        if not line.startswith("v "):
            continue
        for item in line.split()[1:]:
            literal = int(item)
            if literal == 0:
                continue
            var = abs(literal)
            assert var not in assigned
            assigned[var] = literal > 0
    cnf = xor = units = 0
    with gzip.open(HERE / f"{ARM}.xcnf.gz", "rt") as stream:
        header = stream.readline().split()
        assert header[:2] == ["p", "cnf"]
        variable_count, row_count = map(int, header[2:])
        assert len(assigned) == variable_count
        assert set(assigned) == set(range(1, variable_count + 1))
        for line in stream:
            fields = line.split()
            is_xor = fields[0] == "x"
            literals = [int(value) for value in fields[1 if is_xor else 0:-1]]
            assert fields[-1] == "0" and literals
            assert all(0 < abs(lit) <= variable_count for lit in literals)
            values = [assigned[abs(lit)] == (lit > 0) for lit in literals]
            if is_xor:
                assert sum(values) & 1, xor
                xor += 1
            else:
                assert any(values), cnf
                cnf += 1
                units += len(literals) == 1
    assert cnf + xor == row_count
    assert cnf == 528850 + 2538 and xor == 81064
    assert units >= 2538
    out = {"status": "PASS_INDEPENDENT_FULL_XCNF_MODEL_CHECK",
           "curve_id": protocol["curve_id"], "arm": ARM,
           "variables": variable_count, "cnf_rows": cnf,
           "xor_rows": xor, "unit_rows": units,
           "model_true_bits": sum(assigned.values()),
           "protocol_sha256": sha(HERE / "model_audit_protocol.json"),
           "sage_fixture_receipt_sha256": sha(SOURCE / "sage_fixture_result.json")}
    save(HERE / "model_audit_result.json", out)
    print(out["status"], variable_count, cnf, xor)


if __name__ == "__main__":
    {"freeze": freeze, "run": run}[sys.argv[1]]()
