"""Replay the Frobenius split gate and the sealed D=-1295 cycle evidence."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "hecke-two-sheet-small-order-20261023"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    seal = json.loads((PARENT / "SEAL.json").read_text())
    for rel, expected in seal["files"].items():
        assert digest(PARENT / rel) == expected, rel
    selection = json.loads((PARENT / "selection.json").read_text())
    audit = json.loads((PARENT / "audit.json").read_text())
    validation = json.loads((PARENT / "validation.json").read_text())
    d = selection["chosen"]
    p = d["p"]
    assert (d["d"], p, d["norm3_order_f2"]) == (1295, 11719, 18)
    assert (16 * 16 - 4 * p) % 11 == d["frobenius_discriminant_mod_11"] == 9
    roots = {}
    for t in (-d["u_abs"], d["u_abs"]):
        r = [x for x in range(11) if (x*x-t*x+p) % 11 == 0]
        assert len(r) == 2 and r[0] != r[1]
        roots[str(t)] = r
    assert roots == {"-16": [7, 10], "16": [1, 4]}
    assert audit["status"] == "PASS" or audit["verdict"] == "SEPARATE_SHEET_CYCLES"
    assert validation["status"] == "PASS_PROSPECTIVE_SEPARATE_SHEET_CYCLES"
    cycles = audit["cycles"]
    assert sorted(c["length"] for c in cycles) == [18] * 4
    assert all(c["distinct_j"] == 18 and set(c["j_multiplicities"].values()) == {1} for c in cycles)
    js = [frozenset(c["j_multiplicities"]) for c in cycles]
    pairs = [[i, j] for i in range(4) for j in range(i+1,4) if js[i] == js[j]]
    assert pairs == [[0, 3], [1, 2]]
    assert len(audit["c2_j_fibers"]) == 36
    assert set(audit["c2_j_fibers"].values()) == {2}
    assert validation["degree3_projected_kernel_dimension"] == 8
    out = {
        "status": "PASS_FROBENIUS_LABEL_GATE_AND_CYCLE_REPLAY",
        "previous_seal_sha256": digest(PARENT / "SEAL.json"),
        "selection_sha256": digest(PARENT / "selection.json"),
        "audit_sha256": digest(PARENT / "audit.json"),
        "validation_sha256": digest(PARENT / "validation.json"),
        "p": p, "trace_abs": d["u_abs"], "level": 11, "hecke_degree": 3,
        "frobenius_discriminant_mod_11": 9,
        "frobenius_eigenvalues_mod_11_by_trace": roots,
        "rational_fiber_size_c2": 2,
        "c2_base_j_count": 36,
        "c2_cycle_lengths": [c["length"] for c in cycles],
        "same_j_cycle_pairs": pairs,
        "candidate_id": None, "timing_claim": None,
    }
    (HERE / "replay.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps(out, sort_keys=True))


if __name__ == "__main__":
    main()
