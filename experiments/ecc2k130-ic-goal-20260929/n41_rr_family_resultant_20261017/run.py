"""Target-conditioned quartic family resultant on the archived N41 RR panel."""
import hashlib
import importlib.util
import json
import time
from pathlib import Path


D = Path(__file__).resolve().parent
ROOT = D.parent
PRIOR = ROOT / "n41_rr_two_slot_quotient_20261016"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def load_rr():
    path = PRIOR / "run.py"
    spec = importlib.util.spec_from_file_location("n41_rr_quotient", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def multiply_linear(coefficients, root, field):
    nxt = [0] * (len(coefficients) + 1)
    for i, value in enumerate(coefficients):
        nxt[i] ^= field.mul(root, value)
        nxt[i + 1] ^= value
    return nxt


def evaluate(coefficients, root, field):
    value = 0
    for coefficient in reversed(coefficients):
        value = field.mul(value, root) ^ coefficient
    return value


def main():
    p = read(D / "protocol.json")
    assert sha(D / "run.py") == p["runner_sha256"]
    for relative, digest in p["sources"].items():
        assert sha(ROOT / relative) == digest, relative
    rr = load_rr()
    g = read(rr.GEOMETRY)
    hit = read(rr.HIT)
    prior = read(PRIOR / "result.json")
    assert hit["raw_target"] == p["raw_target"]
    assert prior["fixed_state_ids"] == p["fixed_state_ids"]
    fixed = [g["blocks"][i]["states"][p["fixed_state_ids"][i - 2]]
             for i in range(2, 6)]
    target_x, target_y = p["raw_target"]
    rows = [rr.row(state["raw_sum"]) for state in fixed]
    rows.append(rr.row([target_x, target_y ^ target_x]))
    start = time.monotonic_ns()
    basis, pivots, free = rr.kernel(rows)
    assert basis == prior["basis"] and pivots == prior["pivots"] and free == prior["free"]
    fixed_columns = {column for state in fixed for column in state["columns"]}
    groups = []
    signatures = []
    for slot in (0, 1):
        by_code = {}
        sigs = {}
        for state_id, state in enumerate(g["blocks"][slot]["states"]):
            if fixed_columns.intersection(state["columns"]):
                continue
            code = state["a"]
            sig = rr.signature(state["raw_sum"], basis)
            key = rr.key(sig)
            assert isinstance(key, int), "zero or infinite signature requires separate chart"
            by_code.setdefault(code, []).append(state_id)
            sigs[state_id] = (sig, key)
        assert len(by_code) == 36 and all(len(ids) == 4 for ids in by_code.values())
        groups.append(by_code)
        signatures.append(sigs)
    polynomials = []
    for slot in (0, 1):
        polys = {}
        for code, ids in groups[slot].items():
            coefficients = [1]
            for state_id in ids:
                coefficients = multiply_linear(coefficients, signatures[slot][state_id][1], rr.F)
            assert len(coefficients) == 5 and coefficients[-1] == 1
            assert all(evaluate(coefficients, signatures[slot][i][1], rr.F) == 0 for i in ids)
            polys[code] = coefficients
        polynomials.append(polys)
    compatible = []
    state_pairs = []
    nonzero_checks = 0
    for left_code, left_poly in sorted(polynomials[0].items()):
        for right_code, right_poly in sorted(polynomials[1].items()):
            # Res(F_left,F_right) = product over right roots of F_left(root).
            resultant = 1
            for state_id in groups[1][right_code]:
                value = evaluate(left_poly, signatures[1][state_id][1], rr.F)
                resultant = rr.F.mul(resultant, value)
            if resultant:
                nonzero_checks += 1
                continue
            compatible.append([left_code, right_code])
            for i in groups[0][left_code]:
                left = g["blocks"][0]["states"][i]
                for j in groups[1][right_code]:
                    right = g["blocks"][1]["states"][j]
                    if signatures[0][i][1] == signatures[1][j][1] and not (
                        set(left["columns"]) & set(right["columns"])
                    ):
                        state_pairs.append([i, j])
    elapsed_ns = time.monotonic_ns() - start
    expected = prior["matches"]
    assert state_pairs == expected
    assert len(compatible) == 1 and len(state_pairs) == 1
    assert nonzero_checks == 1295
    result = {
        "status": "COMPLETE_N41_RR_FAMILY_RESULTANT",
        "candidate_id": None,
        "protocol_sha256": sha(D / "protocol.json"),
        "fixed_state_ids": p["fixed_state_ids"],
        "family_count": [len(x) for x in groups],
        "states_per_family": 4,
        "family_pairs": len(groups[0]) * len(groups[1]),
        "nonzero_resultant_pairs": nonzero_checks,
        "compatible_family_pairs": compatible,
        "linear_span_rank_two_families": [len(x) for x in groups],
        "linear_span_rejected_pairs": 0,
        "candidate_state_combinations_after_family_filter": 16 * len(compatible),
        "exact_state_pairs": state_pairs,
        "run_wall_ns": elapsed_ns,
        "family_polynomials": [{str(k): v for k, v in sorted(x.items())} for x in polynomials],
    }
    (D / "result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in (
        "status", "family_pairs", "nonzero_resultant_pairs",
        "compatible_family_pairs", "candidate_state_combinations_after_family_filter",
        "exact_state_pairs", "run_wall_ns")}, sort_keys=True))


if __name__ == "__main__":
    main()
