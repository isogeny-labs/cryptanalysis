"""Independent integer/modular replay of the projected ranks."""
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "hecke-new-quotient-holdout-20261026"
ATKIN = HERE.parent / "hecke-d2631-atkin-commutation-20261026"


def rank_mod(rows, prime):
    pivots = {}
    for source in rows:
        row = {j: int(v) % prime for j, v in enumerate(source) if v % prime}
        while row:
            col = min(row)
            pivot = pivots.get(col)
            if pivot is None:
                inv = pow(row[col], -1, prime)
                pivots[col] = {j: v * inv % prime for j, v in row.items()}
                break
            scale = row[col]
            for j, v in pivot.items():
                value = (row.get(j, 0) - scale * v) % prime
                if value:
                    row[j] = value
                else:
                    row.pop(j, None)
    return len(pivots)


def main():
    data = json.loads((BASE / "data" / "exp11_class_walk_D2631_f6.json").read_text())
    floor = json.loads((BASE / "floor_audit.json").read_text())
    scan = json.loads((ATKIN / "scan.json").read_text())
    measured = json.loads((HERE / "ranks.json").read_text())
    perm = scan["class_permutation"]
    pairs = [(i, perm[i]) for i in range(len(perm)) if i < perm[i]]
    rows = [{int(k): int(v) for k, v in row.items()} for row in data["relation_rows"]]
    witnesses = [{int(k): int(v) for k, v in x["signed_floor_columns"].items()}
                 for x in floor["cycles"] + floor["pairs"]]
    results = {}
    for label, source in (("relation", rows), ("floor_witness", witnesses)):
        results[label] = {}
        for sign, sign_label in ((1, "plus"), (-1, "minus")):
            projected = [[row.get(i, 0) + sign * row.get(j, 0) for i, j in pairs]
                         for row in source]
            results[label][sign_label] = {}
            for prime in (23, 1000000007):
                got = rank_mod(projected, prime)
                key = f"mod_{prime}"
                assert got == measured[f"{label}_ranks"][sign_label][key]
                results[label][sign_label][key] = got
    output = {"status": "INDEPENDENT_MODULAR_REPLAY_PASS", "ranks": results}
    (HERE / "validation.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps(output, sort_keys=True))


if __name__ == "__main__":
    main()
