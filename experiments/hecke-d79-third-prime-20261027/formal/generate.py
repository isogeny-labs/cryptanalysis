"""Generate/check finite F41 rank and signed-row certificates in Lean."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent
INPUTS = json.loads((HERE.parent / "search_inputs.json").read_text())


def load(entry):
    data = (ROOT / entry["path"]).read_bytes()
    assert hashlib.sha256(data).hexdigest() == entry["sha256"]
    return json.loads(data)


data, prior_validation, prior_sage_validation = [load(x) for x in INPUTS["inputs"]]
result = json.loads((HERE.parent / "search-result.json").read_text())
validation = json.loads((HERE.parent / "search-validation.json").read_text())
assert prior_validation["status"] == prior_sage_validation["status"] == validation["status"] == "PASS"
assert result["selected_candidate_indices"] == [0, 1, 2, 3, 4, 6, 8, 9, 10]


def row(raw):
    return {int(i): int(v) for i, v in raw.items() if v}


base = [row(x["row"]) for x in data["base_rows"]]
base += [row(x["class_part"]) for x in data["degree13_sources"]
         if x["status"] == "CLASS_CLOSED"]
all_rows = base + [row(x["row"]) for x in result["candidates"]]
selected_rows = base + [row(result["candidates"][i]["row"])
                        for i in result["selected_candidate_indices"]]
assert len(base) == 10 and len(selected_rows) == 19
projection = result["projection_coordinates_mod41"]
assert len(projection) == 20 and any(projection)
assert all(sum(r.get(i, 0)*projection[i] for i in range(20)) % 41 == 0 for r in all_rows)


def dense(r):
    return [r.get(i, 0) % 41 for i in range(20)]


M = [dense(r) for r in selected_rows]
pivots = []
rank = 0
for col in range(20):
    pivot = next((i for i in range(rank, len(M)) if M[i][col]), None)
    if pivot is None:
        continue
    M[rank], M[pivot] = M[pivot], M[rank]
    inv = pow(M[rank][col], -1, 41)
    M[rank] = [x*inv % 41 for x in M[rank]]
    for i in range(len(M)):
        if i != rank and M[i][col]:
            factor = M[i][col]
            M[i] = [(a-factor*b) % 41 for a, b in zip(M[i], M[rank])]
    pivots.append(col)
    rank += 1
assert rank == len(pivots) == 19
minor = [[r.get(col, 0) % 41 for col in pivots] for r in selected_rows]
A = [r[:] + [int(i == j) for j in range(19)] for i, r in enumerate(minor)]
for col in range(19):
    pivot = next(i for i in range(col, 19) if A[i][col])
    A[col], A[pivot] = A[pivot], A[col]
    inv = pow(A[col][col], -1, 41)
    A[col] = [v*inv % 41 for v in A[col]]
    for i in range(19):
        if i != col and A[i][col]:
            factor = A[i][col]
            A[i] = [(a-factor*b) % 41 for a, b in zip(A[i], A[col])]
inverse = [r[19:] for r in A]
assert all(sum(minor[i][k]*inverse[k][j] for k in range(19)) % 41 == int(i == j)
           for i in range(19) for j in range(19))


def literal(values):
    return "[" + ", ".join(map(str, values)) + "]"


def matrix_literal(M):
    return "[\n" + "\n".join("  " + literal(r) + ("," if i+1 < len(M) else "")
                            for i, r in enumerate(M)) + "\n]"


lines = ["module", "", "public import Init", "", "namespace ShortP223", "",
         "set_option maxRecDepth 8192", "set_option maxHeartbeats 0", "",
         "public theorem characteristic_roots :",
         "    (4 * 4 + 223) % 13 = (24 * 4) % 13 ∧",
         "    (7 * 7 + 223) % 13 = (24 * 7) % 13 ∧",
         "    4 % 13 ≠ 7 % 13 := by decide", "",
         "public theorem eigenvalue_ratio :",
         "    (4 * 10) % 13 = 1 ∧ (7 * 10) % 13 = 5 := by decide", "",
         "public theorem ratio_order_four :",
         "    5 ^ 4 % 13 = 1 ∧",
         "    (∀ k : Fin 3, 5 ^ (k.val + 1) % 13 ≠ 1) := by decide", "",
         "public def dot41 (a b : List Nat) : Nat :=",
         "  ((a.zip b).foldl (fun total pair => total + pair.1 * pair.2) 0) % 41", "",
         "public def allRows : List (List Nat) := " + matrix_literal(list(map(dense, all_rows))),
         "public def selectedRows : List (List Nat) := " + matrix_literal(list(map(dense, selected_rows))),
         "public def projection : List Nat := " + literal(projection), "",
         "public theorem rows_annihilate_projection :",
         "    allRows.all (fun r => dot41 r projection == 0) = true := by decide", "",
         "public theorem projection_nonzero : projection ≠ List.replicate 20 0 := by decide", "",
         "public def pivotColumns : List Nat := " + literal(pivots),
         "public def minorA : List (List Nat) := " + matrix_literal(minor),
         "public def minorInverse : List (List Nat) := " + matrix_literal(inverse), "",
         "public def entry (M : List (List Nat)) (i j : Nat) : Nat :=",
         "  (M.getD i []).getD j 0", "",
         "public def productEntry (i j : Fin 19) : Nat :=",
         "  ((List.range 19).foldl (fun total k =>",
         "    total + entry minorA i.val k * entry minorInverse k j.val) 0) % 41", "",
         "public theorem minor_matches_rows : ∀ i j : Fin 19,",
         "    entry minorA i.val j.val =",
         "      entry selectedRows i.val (pivotColumns.getD j.val 0) := by decide", "",
         "public theorem minor_inverse_certificate : ∀ i j : Fin 19,",
         "    productEntry i j = if i.val == j.val then 1 else 0 := by decide", ""]
by_source = {x["source"]: row(x["class_part"]) for x in data["degree13_sources"]}
for candidate_index in result["selected_candidate_indices"]:
    candidate = result["candidates"][candidate_index]
    sources = candidate["sources"]
    coeffs = candidate["coefficients"]
    target = row(candidate["row"])
    assert len(sources) == len(coeffs)
    assert all(sum(c*by_source[s].get(i, 0) for s, c in zip(sources, coeffs)) == target.get(i, 0)
               for i in range(20))
    names = []
    for j, s in enumerate(sources):
        name = f"source_{candidate_index}_{j}"
        names.append(name)
        lines.append(f"public def {name} : List Int := " + literal([by_source[s].get(i, 0) for i in range(20)]))
    lines.append(f"public def result_{candidate_index} : List Int := " +
                 literal([target.get(i, 0) for i in range(20)]))
    terms = [f"({name}.getD i.val 0)" if c == 1 else f"(-{name}.getD i.val 0)"
             for name, c in zip(names, coeffs)]
    expr = " + ".join(terms)
    lines += [f"public theorem signed_row_{candidate_index} : ∀ i : Fin 20,",
              f"    {expr} = result_{candidate_index}.getD i.val 0 := by decide", ""]
lines += ["#print axioms characteristic_roots",
          "#print axioms eigenvalue_ratio",
          "#print axioms ratio_order_four",
          "#print axioms rows_annihilate_projection",
          "#print axioms projection_nonzero",
          "#print axioms minor_matches_rows",
          "#print axioms minor_inverse_certificate"]
for i in result["selected_candidate_indices"]:
    lines.append(f"#print axioms signed_row_{i}")
lines += ["", "end ShortP223", ""]
content = "\n".join(lines)
target = HERE / "ShortP223.lean"
parser = argparse.ArgumentParser()
parser.add_argument("--write", action="store_true")
args = parser.parse_args()
if args.write:
    target.write_text(content)
else:
    assert target.read_text() == content
print("SHORT_P223_FORMAL_SOURCE_PASS", "all_rows", len(all_rows), "selected_rows", len(selected_rows))
