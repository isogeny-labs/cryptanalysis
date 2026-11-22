"""Audit frozen global source XOR rows and all terminal solver receipts."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
FIXTURE = GOAL / "n131_w18_allseed_fourpair_20261012/n41_diagonal/control_fixture.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


def parity(value):
    return bin(value).count("1") & 1


def main():
    panel, protocol = read("panel.json"), read("protocol.json")
    assert panel["status"] == "FROZEN_GLOBAL_XOR_ROWS"
    assert protocol["status"] == "FROZEN_BEFORE_GLOBAL_XOR_SLICE_PANEL"
    assert all(sha(path) == value for path, value in protocol["sources"].items())
    rows = panel["rows"]
    assert len(rows) == 11 and panel["rank"] == 11
    basis = {}
    for row in rows:
        assert all((row >> (8*slot)) & 255 for slot in range(4))
        value = row
        while value:
            pivot = value.bit_length()-1
            if pivot not in basis:
                basis[pivot] = value
                break
            value ^= basis[pivot]
        else:
            raise AssertionError("dependent slice row")
    fixture = json.loads(FIXTURE.read_text())
    witness = sum(mask << (8*i) for i, mask in enumerate(
        mask for pair in fixture["masks"] for mask in pair))
    assert [parity(row & witness) for row in rows] == panel["witness_parities"]
    assert panel["ordinary_parities"] == [
        hashlib.sha256(f"ordinary|{panel['target_reciprocal']}|{sha(GOAL / 'n131_w18_allseed_fourpair_20261012/fourpair_v2.py')}|{i}".encode()).digest()[0] & 1
        for i in range(11)]
    outcomes = []
    for case in panel["cases"]:
        name = case["name"]
        built, result = read(f"{name}_build.json"), read(f"{name}_result.json")
        assert built["status"] == "PASS_EXACT_GLOBAL_XOR_FORMULA"
        assert built["protocol_sha256"] == result["protocol_sha256"] == sha(HERE / "protocol.json")
        assert result["build_sha256"] == sha(HERE / f"{name}_build.json")
        assert built["source_xor_rows"] == len(case["bits"])
        formula = HERE / f"{name}.xcnf"
        assert sha(formula) == built["formula_sha256"]
        text = formula.read_text().splitlines()
        assert text[0] == f"p cnf {built['variables']} {built['cnf_clauses']+built['xor_rows']}"
        assert len(text)-1 == built["cnf_clauses"]+built["xor_rows"]
        mask_wires = [wire for bits in built["mask_wires"] for wire in bits]
        expected = []
        for row, bit in zip(rows, case["bits"]):
            literals = [mask_wires[i] for i in range(64) if row >> i & 1]
            if bit == 0:
                literals[0] = -literals[0]
            expected.append("x " + " ".join(map(str, literals)) + " 0")
        assert text[-len(expected):] == expected
        stdout, stderr = HERE / f"{name}.stdout", HERE / f"{name}.stderr"
        assert sha(stdout) == result["stdout_sha256"] and sha(stderr) == result["stderr_sha256"]
        lines = stdout.read_text(errors="replace").splitlines()
        terminals = [line for line in lines if line.startswith("s ")]
        assert result["terminal"] == (terminals[-1] if terminals else None)
        assert result["restart_rows"] == sum(line.startswith("c rst") for line in lines) > 0
        assert result["status"] == "BOUNDED_UNKNOWN" and result["stop_reason"] == "WALL_CAP"
        if name == "control8":
            assert built["positive_assignment_check"] == {
                "status": "PASS_COMPLETE_CONSTRUCTED_ASSIGNMENT",
                "variables": built["variables"], "clauses": built["cnf_clauses"],
                "xor_rows": built["xor_rows"]}
        else:
            assert built["positive_assignment_check"] is None
        outcomes.append({"name": name, "status": result["status"],
                         "wall_seconds": result["wall_ns"]/1e9,
                         "restart_rows": result["restart_rows"],
                         "peak_solver_rss_bytes": result["peak_solver_rss_bytes"]})
    print(json.dumps({"status": "PASS_GLOBAL_XOR_SLICE_PANEL_AUDIT",
                      "outcomes": outcomes}, sort_keys=True))


if __name__ == "__main__":
    main()
