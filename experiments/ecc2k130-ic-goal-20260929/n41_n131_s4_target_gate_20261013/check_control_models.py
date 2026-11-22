"""Independently check complete CryptoMiniSat assignments against XCNF."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(variant):
    formula = HERE / f"control_{variant}.xcnf"
    output = HERE / f"control_{variant}.solver.stdout"
    lines = output.read_text().splitlines()
    assert "s SATISFIABLE" in lines
    values = {}
    for line in lines:
        if not line.startswith("v "):
            continue
        for token in line.split()[1:]:
            literal = int(token)
            if literal == 0:
                continue
            index = abs(literal)
            assert index not in values
            values[index] = literal > 0
    with formula.open() as handle:
        header = handle.readline().split()
        assert header[:2] == ["p", "cnf"]
        variables, rows = map(int, header[2:4])
        assert set(values) == set(range(1, variables+1))
        clause_count = xor_count = 0
        for line in handle:
            bits = line.split()
            if not bits:
                continue
            xor = bits[0] == "x"
            literals = [int(value) for value in bits[1 if xor else 0:]]
            assert literals[-1] == 0
            literals.pop()
            evals = [values[abs(value)] if value > 0 else not values[-value]
                     for value in literals]
            if xor:
                assert sum(evals) % 2 == 1
                xor_count += 1
            else:
                assert any(evals)
                clause_count += 1
    assert clause_count + xor_count == rows
    return {"variant": variant, "status": "PASS_COMPLETE_XCNF_MODEL",
            "variables": variables, "clauses": clause_count, "xor_rows": xor_count,
            "formula_sha256": sha(formula), "solver_stdout_sha256": sha(output)}


def main():
    protocol = json.loads((HERE / "control_model_protocol.json").read_text())
    paths = {"checker": HERE / "check_control_models.py",
             "control": HERE / "source_control.json",
             "run": HERE / "control_run_result.json",
             "two_s3_formula": HERE / "control_two_s3_links.xcnf",
             "s4_formula": HERE / "control_direct_s4.xcnf",
             "two_s3_stdout": HERE / "control_two_s3_links.solver.stdout",
             "s4_stdout": HERE / "control_direct_s4.solver.stdout"}
    assert protocol["status"] == "FROZEN"
    assert protocol["sha256"] == {key: sha(path) for key, path in paths.items()}
    rows = [check(variant) for variant in ("two_s3_links", "direct_s4")]
    result = {"status": "PASS_BOTH_COMPLETE_MODELS_AND_GROUP_CONTROL",
              "protocol_sha256": sha(HERE / "control_model_protocol.json"),
              "control_sha256": sha(HERE / "source_control.json"),
              "rows": rows}
    (HERE / "control_model_result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
