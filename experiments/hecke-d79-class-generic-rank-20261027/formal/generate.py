"""Generate finite-field rank and annihilation certificates for direct rows."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
REPO = ROOT.parent.parent
inputs = json.loads((ROOT / "inputs.json").read_text())


def load(entry):
    raw = (REPO / entry["path"]).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == entry["sha256"]
    return json.loads(raw)


data = load(inputs["class_receipt"])
search = load(inputs["search_receipt"])
assert all(load(e)["status"] == "PASS" for e in inputs["validation_receipts"])
result = json.loads((ROOT / "result.json").read_text())
validation = json.loads((ROOT / "validation.json").read_text())
assert validation["status"] == "PASS" and validation["ranks"] == result["ranks"]
assert result["class_size"] == inputs["class_size"] == 39


def row(raw):
    return {int(i): int(v) for i, v in raw.items() if v}


base = [row(x["row"]) for x in data["base_rows"]]
direct = [row(x["row"]) for x in result["candidates"]]
selected61 = base + [direct[i] for i in result["selected_candidate_indices"]]
projection = search["projection_coordinates_mod61"]
assert len(selected61) == 38 and len(projection) == 39 and any(projection)
assert all(sum(r.get(i, 0)*projection[i] for i in range(39)) % 61 == 0 for r in base+direct)


def independent_rows(rows, p):
    pivots, selected = {}, []
    for r in rows:
        v = {i: x % p for i, x in r.items() if x % p}
        while v:
            i = min(v)
            if i not in pivots:
                z = v[i]
                pivots[i] = {j: x*pow(z, -1, p) % p for j, x in v.items()}
                selected.append(r)
                break
            z = v[i]
            for j, x in pivots[i].items():
                y = (v.get(j, 0)-z*x) % p
                if y:
                    v[j] = y
                else:
                    v.pop(j, None)
    return selected


def minor_inverse(rows, p):
    size = len(rows)
    M = [[r.get(j, 0) % p for j in range(39)] for r in rows]
    pivots = []
    rank = 0
    for col in range(39):
        pivot = next((i for i in range(rank, size) if M[i][col]), None)
        if pivot is None:
            continue
        M[rank], M[pivot] = M[pivot], M[rank]
        inv = pow(M[rank][col], -1, p)
        M[rank] = [x*inv % p for x in M[rank]]
        for i in range(size):
            if i != rank and M[i][col]:
                z = M[i][col]
                M[i] = [(a-z*b) % p for a, b in zip(M[i], M[rank])]
        pivots.append(col)
        rank += 1
    assert rank == size
    minor = [[r.get(col, 0) % p for col in pivots] for r in rows]
    A = [r[:] + [int(i == j) for j in range(size)] for i, r in enumerate(minor)]
    for col in range(size):
        pivot = next(i for i in range(col, size) if A[i][col])
        A[col], A[pivot] = A[pivot], A[col]
        inv = pow(A[col][col], -1, p)
        A[col] = [v*inv % p for v in A[col]]
        for i in range(size):
            if i != col and A[i][col]:
                z = A[i][col]
                A[i] = [(a-z*b) % p for a, b in zip(A[i], A[col])]
    inverse = [r[size:] for r in A]
    assert all(sum(minor[i][k]*inverse[k][j] for k in range(size)) % p == int(i == j)
               for i in range(size) for j in range(size))
    return pivots, minor, inverse


selected2 = independent_rows(direct, 2)
assert len(selected2) == 39
certs = [(61, selected61), (2, selected2)]


def lit(xs):
    return "[" + ", ".join(map(str, xs)) + "]"


def mat(xs):
    return "[\n" + "\n".join("  " + lit(r) + ("," if i+1 < len(xs) else "")
                              for i, r in enumerate(xs)) + "\n]"


lines = ["module", "", "public import Init", "", "namespace DirectRankP317", "",
         "set_option maxRecDepth 16384", "set_option maxHeartbeats 0", "",
         "public def projection : List Nat := " + lit(projection),
         "public def allRows61 : List (List Nat) := " +
         mat([[r.get(i, 0) % 61 for i in range(39)] for r in base+direct]),
         "public def dot61 (a b : List Nat) : Nat :=",
         "  ((a.zip b).foldl (fun total pair => total + pair.1 * pair.2) 0) % 61", "",
         "public theorem all_rows_annihilate_projection :",
         "    allRows61.all (fun r => dot61 r projection == 0) = true := by decide", "",
         "public theorem projection_nonzero : projection ≠ List.replicate 39 0 := by decide", ""]
for p, rows in certs:
    n = len(rows)
    pivots, minor, inverse = minor_inverse(rows, p)
    prefix = f"mod{p}"
    lines += [f"public def {prefix}Rows : List (List Nat) := " +
              mat([[r.get(i, 0) % p for i in range(39)] for r in rows]),
              f"public def {prefix}Pivots : List Nat := " + lit(pivots),
              f"public def {prefix}Minor : List (List Nat) := " + mat(minor),
              f"public def {prefix}Inverse : List (List Nat) := " + mat(inverse), ""]
    if p == 61:
        lines += ["public def entry (M : List (List Nat)) (i j : Nat) : Nat :=",
                  "  (M.getD i []).getD j 0", ""]
    lines += [f"public theorem {prefix}_minor_matches : ∀ i j : Fin {n},",
              f"    entry {prefix}Minor i.val j.val =",
              f"      entry {prefix}Rows i.val ({prefix}Pivots.getD j.val 0) := by decide", "",
              f"public theorem {prefix}_inverse_certificate : ∀ i j : Fin {n},",
              f"    ((List.range {n}).foldl (fun total k =>",
              f"      total + entry {prefix}Minor i.val k * entry {prefix}Inverse k j.val) 0) % {p} =",
              "      if i.val == j.val then 1 else 0 := by decide", ""]
lines += ["#print axioms all_rows_annihilate_projection",
          "#print axioms projection_nonzero",
          "#print axioms mod61_minor_matches",
          "#print axioms mod61_inverse_certificate",
          "#print axioms mod2_minor_matches",
          "#print axioms mod2_inverse_certificate", "", "end DirectRankP317", ""]
content = "\n".join(lines)
parser = argparse.ArgumentParser()
parser.add_argument("--write", action="store_true")
args = parser.parse_args()
target = HERE / "DirectRankP317.lean"
if args.write:
    target.write_text(content)
else:
    assert target.read_text() == content
print("DIRECT_RANK_FORMAL_PASS", len(base)+len(direct), len(selected61), len(selected2))
