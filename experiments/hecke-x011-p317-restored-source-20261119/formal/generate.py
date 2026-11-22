"""Generate finite-field rank certificates for archived plus restored Hecke rows."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
pre = json.loads((ROOT / "pre-run.json").read_text())
protocol = json.loads((ROOT / "protocol.json").read_text())
raw_inputs = (ROOT.parent / "hecke-x011-p317-complete-fiber-rank-20261119/archived-inputs.json").read_bytes()
assert hashlib.sha256(raw_inputs).hexdigest() == protocol["archived_inputs_sha256"]
data = json.loads(raw_inputs)
result = json.loads((ROOT / "result.json").read_text())
validation = json.loads((ROOT / "audit.json").read_text())
assert validation["status"] == "PASS"
assert result["ranks"]["baseline_plus_new"] == {"QQ": 40, "F61": 39}


def row(raw):
    return {int(i): int(v) for i, v in raw.items() if v}


rows = [row(x) for key in ("base_rows","closed_rows","short_cancellation_rows") for x in data[key]]
rows += [row(x["row"]) for x in result["new_rows"]]
assert len(rows) == 104
all_rows_count = len(rows)
projection = data["projection_coordinates_mod61"] + [0]
assert len(projection) == 40 and any(projection)
assert all(sum(r.get(i, 0)*projection[i] for i in range(40)) % 61 == 0 for r in rows)


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
    M = [[r.get(j, 0) % p for j in range(40)] for r in rows]
    pivots = []
    rank = 0
    for col in range(40):
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


selected61 = independent_rows(rows,61)
selected3 = independent_rows(rows,3)
assert len(selected61) == 39 and len(selected3) == 40
certs = [(61, selected61), (3, selected3)]


def lit(xs):
    return "[" + ", ".join(map(str, xs)) + "]"


def mat(xs):
    return "[\n" + "\n".join("  " + lit(r) + ("," if i+1 < len(xs) else "")
                              for i, r in enumerate(xs)) + "\n]"


lines = ["module", "", "public import Init", "", "namespace RestoredHeckeRankP317", "",
         "set_option maxRecDepth 16384", "set_option maxHeartbeats 0", "",
         "public def projection : List Nat := " + lit(projection),
         "public def allRows61 : List (List Nat) := " +
         mat([[r.get(i, 0) % 61 for i in range(40)] for r in rows]),
         "public def dot61 (a b : List Nat) : Nat :=",
         "  ((a.zip b).foldl (fun total pair => total + pair.1 * pair.2) 0) % 61", "",
         "public theorem all_rows_annihilate_projection :",
         "    allRows61.all (fun r => dot61 r projection == 0) = true := by decide", "",
         "public theorem projection_nonzero : projection ≠ List.replicate 40 0 := by decide", ""]
for p, rows in certs:
    n = len(rows)
    pivots, minor, inverse = minor_inverse(rows, p)
    prefix = f"mod{p}"
    lines += [f"public def {prefix}Rows : List (List Nat) := " +
              mat([[r.get(i, 0) % p for i in range(40)] for r in rows]),
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
          "#print axioms mod3_minor_matches",
          "#print axioms mod3_inverse_certificate", "", "end RestoredHeckeRankP317", ""]
content = "\n".join(lines)
parser = argparse.ArgumentParser()
parser.add_argument("--write", action="store_true")
args = parser.parse_args()
target = HERE / "RestoredHeckeRankP317.lean"
if args.write:
    target.write_text(content)
else:
    assert target.read_text() == content
print("RESTORED_HECKE_RANK_FORMAL_PASS", all_rows_count, len(selected61), len(selected3))
