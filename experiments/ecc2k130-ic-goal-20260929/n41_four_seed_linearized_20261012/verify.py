"""Audit the frozen compact four-seed circuit panel and prior group labels."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
PRIOR = GOAL / "n41_four_family_joint_20261012"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


def audit():
    protocol = read("protocol.json")
    assert protocol["status"] == "FROZEN_BEFORE_COMPACT_FOUR_SEED_PANEL"
    assert all(sha(path) == value for path, value in protocol["sources"].items())
    prior = json.loads((PRIOR / "protocol.json").read_text())
    assert protocol["seed_tuples"] == [prior["positive_seed_tuple"], *prior["negative_seed_tuples"]]
    rows = []
    for index, seeds in enumerate(protocol["seed_tuples"]):
        built, result = read(f"case_{index}_build.json"), read(f"case_{index}_result.json")
        assert built["status"] == "PASS_EXACT_SEED_SUM_FORMULA"
        assert built["seed_tuple"] == seeds and built["seed_xor_rows"] == 32
        assert built["protocol_sha256"] == sha(HERE / "protocol.json")
        assert result["protocol_sha256"] == sha(HERE / "protocol.json")
        assert result["build_sha256"] == sha(HERE / f"case_{index}_build.json")
        assert sha(HERE / f"case_{index}.xcnf") == built["formula_sha256"]
        assert sha(HERE / f"case_{index}.stdout") == result["stdout_sha256"]
        assert sha(HERE / f"case_{index}.stderr") == result["stderr_sha256"]
        lines = (HERE / f"case_{index}.xcnf").read_text().splitlines()
        assert lines[0] == f"p cnf {built['variables']} {built['cnf_clauses'] + built['xor_rows']}"
        assert len(lines) - 1 == built["cnf_clauses"] + built["xor_rows"]
        assert sum(line.startswith("x ") for line in lines[1:]) == built["xor_rows"]
        expected = []
        for slot, seed in enumerate(seeds):
            left, right = built["mask_wires"][2*slot:2*slot+2]
            for bit, (a, b) in enumerate(zip(left, right)):
                expected.append(f"x {a if seed >> bit & 1 else -a} {b} 0")
        assert lines[-32:] == expected
        stdout = (HERE / f"case_{index}.stdout").read_text(errors="replace").splitlines()
        terminals = [line for line in stdout if line.startswith("s ")]
        assert result["terminal"] == (terminals[-1] if terminals else None)
        assert result["status"] == "BOUNDED_UNKNOWN" and result["stop_reason"] == "WALL_CAP"
        restarts = sum(line.startswith("c rst") for line in stdout)
        assert restarts > 0
        prior_join = (PRIOR / f"join_{index}.stdout").read_text().splitlines()
        hits = [line for line in prior_join if line.startswith("HIT ")]
        assert len(hits) == (1 if index == 0 else 0)
        if index == 0:
            assert built["positive_assignment_check"] == {
                "status": "PASS_COMPLETE_CONSTRUCTED_ASSIGNMENT",
                "variables": built["variables"], "clauses": built["cnf_clauses"],
                "xor_rows": built["xor_rows"]}
        else:
            assert built["positive_assignment_check"] is None
        rows.append({"case": index, "seed_tuple": seeds, "prior_group_hits": len(hits),
                     "status": result["status"], "parent_wall_seconds": result["wall_ns"]/1e9,
                     "restart_rows": restarts, "peak_solver_rss_bytes": result["peak_solver_rss_bytes"]})
    return {"status": "PASS_COMPACT_FOUR_SEED_PANEL_AUDIT", "rows": rows}


if __name__ == "__main__":
    print(json.dumps(audit(), sort_keys=True))
