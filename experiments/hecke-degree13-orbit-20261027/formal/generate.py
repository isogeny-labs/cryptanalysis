"""Regenerate/check the explicit Lean F_5 rank-separator receipt."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent
INPUTS = json.loads((HERE.parent / "inputs.json").read_text())
HASHES = {entry["path"]: entry["sha256"] for entry in INPUTS["inputs"]}


def load(path):
    data = (ROOT / path).read_bytes()
    assert hashlib.sha256(data).hexdigest() == HASHES[path]
    return json.loads(data)


corrected = load(INPUTS["inputs"][1]["path"])
cancellation = load(INPUTS["inputs"][2]["path"])
current = json.loads((HERE.parent / "result.json").read_text())
width = 20
baseline = corrected["relation_rows"] + [entry["row"] for entry in
    cancellation["closed_rows"] + cancellation["pair_rows"]]
new = next(entry["row"] for entry in current["sources"] if entry["source"] == 3)


def dense(raw):
    return [int(raw.get(str(i), 0)) % 5 for i in range(width)]


base_rows = list(map(dense, baseline))
new_row = dense(new)
M = [row[:] for row in base_rows]
pivots = []
rank = 0
for column in range(width):
    pivot = next((i for i in range(rank, len(M)) if M[i][column]), None)
    if pivot is None:
        continue
    M[rank], M[pivot] = M[pivot], M[rank]
    inv = pow(M[rank][column], -1, 5)
    M[rank] = [value * inv % 5 for value in M[rank]]
    for i in range(len(M)):
        if i != rank and M[i][column]:
            scale = M[i][column]
            M[i] = [(a - scale * b) % 5 for a, b in zip(M[i], M[rank])]
    pivots.append(column)
    rank += 1
assert rank == 16
witness = None
for free in range(width):
    if free in pivots:
        continue
    candidate = [0] * width
    candidate[free] = 1
    for i, pivot in enumerate(pivots):
        candidate[pivot] = -M[i][free] % 5
    if sum(a * b for a, b in zip(new_row, candidate)) % 5:
        witness = candidate
        break
assert witness is not None
assert all(sum(a * b for a, b in zip(row, witness)) % 5 == 0 for row in base_rows)
new_dot = sum(a * b for a, b in zip(new_row, witness)) % 5
assert new_dot == 3


def list_literal(values):
    return "[" + ", ".join(map(str, values)) + "]"


lines = [
    "module", "", "public import Init", "",
    "/-! Exact F_5 separator for the degree-13 source-3 row. -/",
    "namespace RankWitness", "",
    "public def dot5 (a b : List Nat) : Nat :=",
    "  ((a.zip b).foldl (fun total pair => total + pair.1 * pair.2) 0) % 5", "",
    "public def baselineRows : List (List Nat) := [",
]
lines += ["  " + list_literal(row) + ("," if i + 1 < len(base_rows) else "")
          for i, row in enumerate(base_rows)]
lines += ["]", "", "public def newRow : List Nat := " + list_literal(new_row),
          "public def witness : List Nat := " + list_literal(witness), "",
          "public theorem baseline_annihilated :",
          "    baselineRows.all (fun row => dot5 row witness == 0) = true := by",
          "  decide", "",
          "public theorem new_row_separated : dot5 newRow witness = 3 := by",
          "  decide", "",
          "#print axioms baseline_annihilated",
          "#print axioms new_row_separated", "", "end RankWitness", ""]
content = "\n".join(lines)
target = HERE / "RankWitness.lean"
parser = argparse.ArgumentParser()
parser.add_argument("--write", action="store_true")
args = parser.parse_args()
if args.write:
    target.write_text(content)
else:
    assert target.read_text() == content
print("RANK_WITNESS_SOURCE_PASS", "baseline", len(base_rows), "rank", rank,
      "new_dot", new_dot, "free_coordinate", free)
