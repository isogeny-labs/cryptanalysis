"""Generate/check Lean integer and F_5 certificates from frozen receipts."""
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
degree13 = load(INPUTS["inputs"][4]["path"])
result = json.loads((HERE.parent / "result.json").read_text())
validation = json.loads((HERE.parent / "validation.json").read_text())
assert result["selected_candidate_indices"] == [11, 12]


def sparse(raw):
    return {int(i): int(value) for i, value in raw.items() if value}


rows = list(map(sparse, corrected["relation_rows"]))
rows += [sparse(item["row"]) for item in cancellation["closed_rows"] + cancellation["pair_rows"]]
rows += [sparse(item["row"]) for item in degree13["sources"] if item["status"] == "CLASS_CLOSED"]
rows += [sparse(result["candidates"][i]["row"]) for i in result["selected_candidate_indices"]]
assert len(rows) == 27
projection = list(map(int, validation["projection_coordinates_mod5"]))
assert len(projection) == 20 and any(projection)
assert all(sum(row.get(i, 0) * projection[i] for i in range(20)) % 5 == 0 for row in rows)


def dense(row):
    return [row.get(i, 0) % 5 for i in range(20)]


def rank_mod(rs):
    M = [dense(row) for row in rs]
    pivots = []
    rank = 0
    for column in range(20):
        pivot = next((i for i in range(rank, len(M)) if M[i][column]), None)
        if pivot is None:
            continue
        M[rank], M[pivot] = M[pivot], M[rank]
        inverse = pow(M[rank][column], -1, 5)
        M[rank] = [value * inverse % 5 for value in M[rank]]
        for i in range(len(M)):
            if i != rank and M[i][column]:
                scale = M[i][column]
                M[i] = [(a - scale * b) % 5 for a, b in zip(M[i], M[rank])]
        pivots.append(column)
        rank += 1
    return rank, pivots


independent_indices = []
independent_rows = []
for index, row in enumerate(rows):
    if rank_mod(independent_rows + [row])[0] > len(independent_rows):
        independent_indices.append(index)
        independent_rows.append(row)
assert len(independent_rows) == 19
rank19, columns = rank_mod(independent_rows)
assert rank19 == len(columns) == 19
minor = [[row.get(column, 0) % 5 for column in columns] for row in independent_rows]


def inverse_mod5(A):
    n = len(A)
    M = [row[:] + [int(i == j) for j in range(n)] for i, row in enumerate(A)]
    for column in range(n):
        pivot = next(i for i in range(column, n) if M[i][column])
        M[column], M[pivot] = M[pivot], M[column]
        scale = pow(M[column][column], -1, 5)
        M[column] = [value * scale % 5 for value in M[column]]
        for i in range(n):
            if i != column and M[i][column]:
                scale = M[i][column]
                M[i] = [(a - scale * b) % 5 for a, b in zip(M[i], M[column])]
    return [row[n:] for row in M]


minor_inverse = inverse_mod5(minor)
assert all(sum(minor[i][k] * minor_inverse[k][j] for k in range(19)) % 5 == int(i == j)
           for i in range(19) for j in range(19))


def literal(values):
    return "[" + ", ".join(map(str, values)) + "]"


def matrix_literal(M):
    return "[\n" + "\n".join("  " + literal(row) + ("," if i + 1 < len(M) else "")
                            for i, row in enumerate(M)) + "\n]"


lines = [
    "module", "", "public import Init", "", "namespace ShortTrace", "",
    "set_option maxRecDepth 8192", "set_option maxHeartbeats 0", "",
    "public def dot5 (a b : List Nat) : Nat :=",
    "  ((a.zip b).foldl (fun total pair => total + pair.1 * pair.2) 0) % 5", "",
    "public def allRows : List (List Nat) := " + matrix_literal(list(map(dense, rows))),
    "public def projection : List Nat := " + literal(projection), "",
    "public theorem rows_annihilate_projection :",
    "    allRows.all (fun row => dot5 row projection == 0) = true := by",
    "  decide", "",
    "public theorem projection_nonzero : projection ≠ List.replicate 20 0 := by",
    "  decide", "",
    "public def independentRowIndices : List Nat := " + literal(independent_indices),
    "public def pivotColumns : List Nat := " + literal(columns),
    "public def minorA : List (List Nat) := " + matrix_literal(minor),
    "public def minorInverse : List (List Nat) := " + matrix_literal(minor_inverse), "",
    "public def entry (M : List (List Nat)) (i j : Nat) : Nat :=",
    "  (M.getD i []).getD j 0", "",
    "public def productEntry (i j : Fin 19) : Nat :=",
    "  ((List.range 19).foldl (fun total k =>",
    "    total + entry minorA i.val k * entry minorInverse k j.val) 0) % 5", "",
    "public theorem minor_matches_rows : ∀ i j : Fin 19,",
    "    entry minorA i.val j.val =",
    "      entry allRows (independentRowIndices.getD i.val 0) (pivotColumns.getD j.val 0) := by",
    "  decide", "",
    "public theorem minor_inverse_certificate : ∀ i j : Fin 19,",
    "    productEntry i j = if i.val == j.val then 1 else 0 := by",
    "  decide", "",
]
for candidate_index in result["selected_candidate_indices"]:
    candidate = result["candidates"][candidate_index]
    support = candidate["support"]
    assert len(support) == 2 and [item["coefficient"] for item in support] == [1, -1]
    assert all(item["degree"] == 13 for item in support)
    names = [f'{item["degree"]}_{item["source"]}' for item in support]
    expanded = []
    for item in support:
        source = next(row for row in result["expanded_rows"]
                      if row["degree"] == item["degree"] and row["source"] == item["source"])
        values = sparse(source["class_part"])
        values[20] = 1
        expanded.append([values.get(i, 0) for i in range(21)])
    target = sparse(candidate["row"])
    target_values = [target.get(i, 0) for i in range(21)]
    assert [expanded[0][i] - expanded[1][i] for i in range(21)] == target_values
    label = names[0] + "_minus_" + names[1]
    lines += [
        f"public def first_{label} : List Int := " + literal(expanded[0]),
        f"public def second_{label} : List Int := " + literal(expanded[1]),
        f"public def result_{label} : List Int := " + literal(target_values),
        f"public theorem cancel_{label} : ∀ i : Fin 21,",
        f"    first_{label}.getD i.val 0 - second_{label}.getD i.val 0 =",
        f"      result_{label}.getD i.val 0 := by",
        "  decide", "",
    ]
lines += [
    "#print axioms rows_annihilate_projection",
    "#print axioms projection_nonzero",
    "#print axioms minor_matches_rows",
    "#print axioms minor_inverse_certificate",
]
for candidate_index in result["selected_candidate_indices"]:
    support = result["candidates"][candidate_index]["support"]
    label = f'{support[0]["degree"]}_{support[0]["source"]}_minus_{support[1]["degree"]}_{support[1]["source"]}'
    lines.append(f"#print axioms cancel_{label}")
lines += ["", "end ShortTrace", ""]
content = "\n".join(lines)
target = HERE / "ShortTrace.lean"
parser = argparse.ArgumentParser()
parser.add_argument("--write", action="store_true")
args = parser.parse_args()
if args.write:
    target.write_text(content)
else:
    assert target.read_text() == content
print("SHORT_TRACE_FORMAL_SOURCE_PASS", "rows", len(rows),
      "independent_rows", len(independent_rows), "columns", len(columns))
