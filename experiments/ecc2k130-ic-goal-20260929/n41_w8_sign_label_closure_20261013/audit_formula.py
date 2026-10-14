"""Rebuild the frozen seven-pair formula and check every label conflict clause."""
import hashlib
import importlib.util
import json
import resource
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PRIOR = ROOT / "n41_w8_functional_root_table_v2_20261013"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / "formula_protocol.json").read_text())
    assert protocol["status"] == "FROZEN"
    for path, digest in protocol["sources"].items():
        assert sha(Path(path)) == digest, path
    spec = importlib.util.spec_from_file_location("frozen_sevenpair_circuit", PRIOR / "circuit.py")
    circuit = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(PRIOR))
    spec.loader.exec_module(circuit)
    geometry = circuit.geometry()
    target = circuit.F.inv(geometry["positive_control"]["raw_target"][0])
    start = time.monotonic_ns()
    formula, wires, selector = circuit.build(target)
    built = time.monotonic_ns()
    assert len(wires["codes"]) == 7 and all(len(row) == 7 for row in wires["codes"])
    seed = geometry["fixed_seed_sum_code"]
    bits = selector["bits"]
    code_masks = {sum(((mask >> bit) & 1) << j for j, bit in enumerate(bits)): mask
                  for mask in geometry["permitted_canonical_a"]}
    columns = {int(k): v for k, v in geometry["mask_columns"].items()}
    actual = set(formula.clauses)
    expected = set()
    for i in range(7):
        for j in range(i + 1, 7):
            for acode, a in code_masks.items():
                acol = {columns[a], columns[a ^ seed]}
                for bcode, b in code_masks.items():
                    if not (acol & {columns[b], columns[b ^ seed]}):
                        continue
                    lhs = [-wire if acode >> k & 1 else wire
                           for k, wire in enumerate(wires["codes"][i])]
                    rhs = [-wire if bcode >> k & 1 else wire
                           for k, wire in enumerate(wires["codes"][j])]
                    expected.add(" ".join(map(str, lhs + rhs)) + " 0")
    assert len(expected) == 966
    assert expected <= actual
    output = HERE / "rebuilt_public.xcnf"
    formula.write(output)
    assert sha(output) == sha(PRIOR / "public.xcnf")
    control = json.loads((PRIOR / "control_result.json").read_text())
    assert formula.next_var - 1 == control["variables"]
    assert len(formula.clauses) == control["clauses"]
    assert len(formula.xors) == control["xor_rows"]
    result = {
        "status": "PASS_FROZEN_SEVENPAIR_XCNF_LABEL_CLAUSES",
        "expected_conflict_clauses": len(expected),
        "present_conflict_clauses": len(expected & actual),
        "rebuilt_formula_sha256": sha(output),
        "variables": formula.next_var - 1,
        "clauses": len(formula.clauses),
        "native_xor_rows": len(formula.xors),
        "construction_ns": built - start,
        "total_ns": time.monotonic_ns() - start,
        "peak_process_rss_raw": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    with (HERE / "formula_result.json").open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(result["status"], flush=True)


if __name__ == "__main__":
    main()
