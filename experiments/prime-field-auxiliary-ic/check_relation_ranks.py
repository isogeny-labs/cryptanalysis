"""Replay the archived M31 signed-row rank certificates. Requires SymPy and Lean 4."""
import json
from pathlib import Path
import subprocess

import sympy

ROOT = Path(__file__).resolve().parent
TRACES = ROOT / "snapshot/algebraic/optimized/results/field31_s5_base0"
ORDER = 2147505293
ARMS = ("v2_batch", "v2_chain")

CHECKER = """import Std

namespace ArchivedRank
abbrev order : Int := 2147505293
abbrev Matrix := List (List Int)
def entry (m : Matrix) (i j : Nat) := (m[i]?.getD [])[j]?.getD 0

/-- The right inverse of the prefix minor and a left null vector of the full
matrix certify that the final row produces the first dependency. -/
def valid (rows : Matrix) (cols : List Nat) (inv : Matrix) (w : List Int) : Bool := Id.run do
  let k := rows.length - 1
  let r := List.range k
  let all := List.range rows.length
  return k > 0 && rows.all (fun row => row.length == 17) &&
    cols.length == k && cols.all (fun c => c < 17) &&
    inv.length == k && inv.all (fun row => row.length == k) &&
    r.all (fun i => r.all (fun j =>
      ((r.map (fun t => entry rows i (cols[t]?.getD 17) * entry inv t j)).sum % order)
      == (if i == j then 1 else 0))) &&
    w.length == rows.length && (w[k]?.getD 0) % order != 0 &&
    (List.range 17).all (fun j =>
      (all.map (fun i => (w[i]?.getD 0) * entry rows i j)).sum % order == 0)
"""


def encode(row):
    coefficients = [0] * 17
    for column, sign in ((row["i"], row["si"]), (row["j"], row["sj"])):
        if not 0 <= column < 17 or sign not in (-1, 1):
            raise ValueError("invalid signed incidence")
        coefficients[column] += sign
    return coefficients


def cycle_rows(rows):
    groups = [{column} for column in range(17)]
    cycles = []
    for index, row in enumerate(rows, 1):
        left = next(group for group in groups if row["i"] in group)
        right = next(group for group in groups if row["j"] in group)
        if left is right:
            cycles.append(index)
        else:
            left.update(right)
            groups.remove(right)
    return cycles


def main():
    source = [CHECKER]
    report = []
    for arm in ARMS:
        for seed in range(3):
            name = f"{arm}_seed{seed}"
            rows = [json.loads(line) for line in (TRACES / f"{name}.relations.jsonl").read_text().splitlines()]
            receipt = json.loads((TRACES / f"{name}.audited.json").read_bytes())
            matrix = [encode(row) for row in rows]
            prefix = sympy.Matrix(matrix[:-1])
            columns = list(prefix.rref()[1])
            if len(columns) != len(rows) - 1:
                raise ValueError(f"{name} prefix lacks full rank")
            minor = prefix[:, columns]
            inv = minor.inv_mod(ORDER).applyfunc(int).tolist()
            weights = receipt["weights"]
            # The receipt moves the weighted query coefficients to the opposite side.
            residuals = [(-sum(w * row[key] for w, row in zip(weights, rows))) % ORDER
                         for key in ("a", "b")]
            if residuals != [receipt["A"], receipt["B"]] or residuals[1] == 0:
                raise ValueError(f"{name} residual disagrees with receipt or vanishes")
            support = sum(w % ORDER != 0 for w in weights)
            if (receipt["rank"], receipt["audit"]["dependency_relations"]) != (len(columns), support):
                raise ValueError(f"{name} receipt disagrees with certificate sizes")
            source.append(f"theorem {name} : valid {matrix} {columns} {inv} {weights} = true := by decide")
            source.append(f"#print axioms {name}")
            report.append((name, len(rows), support, cycle_rows(rows)))
    subprocess.run(["lean", "--stdin"], input="\n".join(source + ["end ArchivedRank"]), text=True, check=True)
    for name, count, support, cycles in report:
        print(name, "first dependent row", count, "support", support, "unsigned cycle rows", cycles)


if __name__ == "__main__":
    main()
