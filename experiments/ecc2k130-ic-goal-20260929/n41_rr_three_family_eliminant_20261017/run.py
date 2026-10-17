"""Exact three-family determinant screen on the frozen N41 public point."""
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
    spec = importlib.util.spec_from_file_location("rr_three_field", PRIOR / "run.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def kernel_three(rows, rr):
    a = [r[:] for r in rows]
    pivots = []
    for col in range(7):
        k = len(pivots)
        first = next((i for i in range(k, len(a)) if a[i][col]), None)
        if first is None:
            continue
        a[k], a[first] = a[first], a[k]
        scale = rr.inv(a[k][col])
        a[k] = [rr.F.mul(v, scale) for v in a[k]]
        for i in range(len(a)):
            if i != k and a[i][col]:
                factor = a[i][col]
                a[i] = [v ^ rr.F.mul(factor, w) for v, w in zip(a[i], a[k])]
        pivots.append(col)
    free = [i for i in range(7) if i not in pivots]
    assert len(pivots) == 4 and len(free) == 3
    basis = []
    for j in free:
        v = [0] * 7
        v[j] = 1
        for k, pivot in enumerate(pivots):
            v[pivot] = a[k][j]
        assert all(rr.dot(row, v) == 0 for row in rows)
        basis.append(v)
    return basis, pivots, free


def cross(a, b, field):
    return (field.mul(a[1], b[2]) ^ field.mul(a[2], b[1]),
            field.mul(a[2], b[0]) ^ field.mul(a[0], b[2]),
            field.mul(a[0], b[1]) ^ field.mul(a[1], b[0]))


def dot(a, b, field):
    return field.mul(a[0], b[0]) ^ field.mul(a[1], b[1]) ^ field.mul(a[2], b[2])


def main():
    p = read(D / "protocol.json")
    assert sha(D / "run.py") == p["runner_sha256"]
    for relative, digest in p["sources"].items():
        assert sha(ROOT / relative) == digest, relative
    rr = load_rr()
    g = read(rr.GEOMETRY)
    hit = read(rr.HIT)
    assert p["raw_target"] == hit["raw_target"]
    fixed = [g["blocks"][slot]["states"][sid]
             for slot, sid in zip((3, 4, 5), p["fixed_state_ids"])]
    assert p["fixed_state_ids"] == [hit["pair_rows"][slot]["state_id"] for slot in (3, 4, 5)]
    qx, qy = p["raw_target"]
    rows = [rr.row(s["raw_sum"]) for s in fixed] + [rr.row([qx, qy ^ qx])]
    start = time.monotonic_ns()
    basis, pivots, free = kernel_three(rows, rr)
    fixed_columns = {c for s in fixed for c in s["columns"]}
    by_code = []
    signatures = []
    for slot in range(3):
        families = {}
        sigs = {}
        for sid, state in enumerate(g["blocks"][slot]["states"]):
            if fixed_columns.intersection(state["columns"]):
                continue
            families.setdefault(state["a"], []).append(sid)
            sigs[sid] = tuple(rr.signature(state["raw_sum"], basis))
        assert all(len(ids) == 4 for ids in families.values())
        by_code.append(families)
        signatures.append(sigs)
    family_triples = 0
    valid_family_triples = 0
    determinant_zero_family_triples = 0
    determinant_zero_states = 0
    valid_zero_states = []
    determinant_evaluations = 0
    # c0 x c1 cross vectors are reusable for every third-slot code family.
    for c0, ids0 in sorted(by_code[0].items()):
        for c1, ids1 in sorted(by_code[1].items()):
            pairs = []
            for i in ids0:
                for j in ids1:
                    si, sj = g["blocks"][0]["states"][i], g["blocks"][1]["states"][j]
                    pairs.append((i, j, cross(signatures[0][i], signatures[1][j], rr.F),
                                  set(si["columns"]) | set(sj["columns"]),
                                  set(si["columns"]).isdisjoint(sj["columns"])))
            for c2, ids2 in sorted(by_code[2].items()):
                family_triples += 1
                any_valid = False
                any_zero = False
                for i, j, cp, columns, pair_valid in pairs:
                    for k in ids2:
                        sk = g["blocks"][2]["states"][k]
                        valid = pair_valid and columns.isdisjoint(sk["columns"])
                        any_valid |= valid
                        determinant_evaluations += 1
                        if dot(cp, signatures[2][k], rr.F) == 0:
                            any_zero = True
                            determinant_zero_states += 1
                            if valid:
                                valid_zero_states.append([i, j, k])
                valid_family_triples += any_valid
                determinant_zero_family_triples += any_zero
    elapsed = time.monotonic_ns() - start
    expected = [hit["pair_rows"][slot]["state_id"] for slot in range(3)]
    assert expected in valid_zero_states
    result = {
        "status": "COMPLETE_N41_RR_THREE_FAMILY_DETERMINANT",
        "candidate_id": None,
        "protocol_sha256": sha(D / "protocol.json"),
        "fixed_state_ids": p["fixed_state_ids"],
        "kernel_pivots": pivots,
        "kernel_free": free,
        "kernel_basis": basis,
        "family_counts": [len(x) for x in by_code],
        "state_counts": [len(x) for x in signatures],
        "family_triples": family_triples,
        "valid_family_triples": valid_family_triples,
        "determinant_zero_family_triples": determinant_zero_family_triples,
        "determinant_nonzero_family_triples": family_triples - determinant_zero_family_triples,
        "determinant_evaluations": determinant_evaluations,
        "determinant_zero_state_triples": determinant_zero_states,
        "valid_determinant_zero_states": valid_zero_states,
        "expected_state_triple": expected,
        "run_wall_ns": elapsed,
    }
    (D / "result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({key: result[key] for key in (
        "status", "family_triples", "determinant_zero_family_triples",
        "determinant_evaluations", "valid_determinant_zero_states", "run_wall_ns")}, sort_keys=True))


if __name__ == "__main__":
    main()
