"""Generate exact F53 and F3 matrix certificates for the p1277 holdout."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
REPO = ROOT.parent.parent
post = json.loads((ROOT / "post_inputs.json").read_text())
raw = (REPO / post["class_receipt"]).read_bytes()
assert hashlib.sha256(raw).hexdigest() == post["class_receipt_sha256"]
data = json.loads(raw)
analysis = json.loads((ROOT / "analysis.json").read_text())
audit = json.loads((ROOT / "audit.json").read_text())
assert audit["status"] == "PASS" and audit["ranks"] == analysis["ranks"]
assert audit["class_projection_counts"] == {"1": 20, "4": 20}
assert audit["source_projection_counts"] == {"1": 4, "2": 16, "3": 16, "4": 4}
assert audit["q53_projection_nonzero_points"] == 40


def row(raw):
    return {int(i): int(v) for i, v in raw.items() if v}


base = [row(x["row"]) for x in data["base_rows"]]
direct_rows = base + [row(x["row"]) for x in analysis["direct"]["candidates"]]
hecke_rows = base + [row(x["row"]) for x in analysis["hecke"]["candidates"]]
assert len(base) == 20 and len(direct_rows) == 22 and len(hecke_rows) == 49
assert data["class_size"] == 40 and data["largest_prime_factor"] == 53


def independent(rows, p):
    pivots, choice = {}, []
    for r in rows:
        v = {i: x % p for i, x in r.items() if x % p}
        while v:
            i = min(v)
            if i not in pivots:
                z = v[i]
                pivots[i] = {j: x*pow(z, -1, p) % p for j, x in v.items()}
                choice.append(r)
                break
            z = v[i]
            for j, x in pivots[i].items():
                y = (v.get(j, 0)-z*x) % p
                if y:
                    v[j] = y
                else:
                    v.pop(j, None)
    return choice


def minor_inverse(rows, p):
    n = len(rows)
    M = [[r.get(j, 0) % p for j in range(40)] for r in rows]
    pivots = []
    rank = 0
    for col in range(40):
        pivot = next((i for i in range(rank, n) if M[i][col]), None)
        if pivot is None:
            continue
        M[rank], M[pivot] = M[pivot], M[rank]
        inv = pow(M[rank][col], -1, p)
        M[rank] = [x*inv % p for x in M[rank]]
        for i in range(n):
            if i != rank and M[i][col]:
                z = M[i][col]
                M[i] = [(a-z*b) % p for a, b in zip(M[i], M[rank])]
        pivots.append(col)
        rank += 1
    assert rank == n
    minor = [[r.get(col, 0) % p for col in pivots] for r in rows]
    A = [r[:] + [int(i == j) for j in range(n)] for i, r in enumerate(minor)]
    for col in range(n):
        pivot = next(i for i in range(col, n) if A[i][col])
        A[col], A[pivot] = A[pivot], A[col]
        inv = pow(A[col][col], -1, p)
        A[col] = [x*inv % p for x in A[col]]
        for i in range(n):
            if i != col and A[i][col]:
                z = A[i][col]
                A[i] = [(a-z*b) % p for a, b in zip(A[i], A[col])]
    inverse = [r[n:] for r in A]
    assert all(sum(minor[i][k]*inverse[k][j] for k in range(n)) % p == int(i == j)
               for i in range(n) for j in range(n))
    return pivots, minor, inverse, M


direct53 = independent(direct_rows, 53)
hecke53 = independent(hecke_rows, 53)
hecke3 = independent(hecke_rows, 3)
assert (len(direct53), len(hecke53), len(hecke3)) == (22, 39, 40)
piv53, _, _, reduced53 = minor_inverse(hecke53, 53)
free = [i for i in range(40) if i not in piv53]
assert len(free) == 1
kernel = [0]*40
kernel[free[0]] = 1
for r, col in enumerate(piv53):
    kernel[col] = -reduced53[r][free[0]] % 53
assert any(kernel)
assert all(sum(r.get(i, 0)*kernel[i] for i in range(40)) % 53 == 0
           for r in hecke_rows)


def lit(xs):
    return "[" + ", ".join(map(str, xs)) + "]"


def mat(xs):
    return "[\n" + "\n".join("  " + lit(r) + ("," if i+1 < len(xs) else "")
                              for i, r in enumerate(xs)) + "\n]"


lines = ["module", "", "public import Init", "", "namespace RankP1277", "",
         "set_option maxRecDepth 16384", "set_option maxHeartbeats 0", "",
         "public def allHeckeRows53 : List (List Nat) := " +
         mat([[r.get(i, 0) % 53 for i in range(40)] for r in hecke_rows]),
         "public def kernel : List Nat := " + lit(kernel),
         "public def dot53 (a b : List Nat) : Nat :=",
         "  ((a.zip b).foldl (fun s x => s + x.1 * x.2) 0) % 53", "",
         "public theorem all_hecke_rows_annihilate_kernel :",
         "    allHeckeRows53.all (fun r => dot53 r kernel == 0) = true := by decide",
         "public theorem kernel_nonzero : kernel ≠ List.replicate 40 0 := by decide", "",
         "public def entry (M : List (List Nat)) (i j : Nat) : Nat :=",
         "  (M.getD i []).getD j 0", ""]
for p, choice, prefix in [(53, direct53, "direct53"),
                          (53, hecke53, "hecke53"),
                          (3, hecke3, "hecke3")]:
    n = len(choice)
    piv, minor, inverse, _ = minor_inverse(choice, p)
    lines += [f"public def {prefix}Rows : List (List Nat) := " +
              mat([[r.get(i, 0) % p for i in range(40)] for r in choice]),
              f"public def {prefix}Pivots : List Nat := " + lit(piv),
              f"public def {prefix}Minor : List (List Nat) := " + mat(minor),
              f"public def {prefix}Inverse : List (List Nat) := " + mat(inverse), "",
              f"public theorem {prefix}_minor_matches : ∀ i j : Fin {n},",
              f"    entry {prefix}Minor i.val j.val =",
              f"      entry {prefix}Rows i.val ({prefix}Pivots.getD j.val 0) := by decide", "",
              f"public theorem {prefix}_inverse_certificate : ∀ i j : Fin {n},",
              f"    ((List.range {n}).foldl (fun total k =>",
              f"      total + entry {prefix}Minor i.val k * entry {prefix}Inverse k j.val) 0) % {p} =",
              "      if i.val == j.val then 1 else 0 := by decide", ""]
lines += ["#print axioms all_hecke_rows_annihilate_kernel",
          "#print axioms kernel_nonzero",
          "#print axioms direct53_minor_matches",
          "#print axioms direct53_inverse_certificate",
          "#print axioms hecke53_minor_matches",
          "#print axioms hecke53_inverse_certificate",
          "#print axioms hecke3_minor_matches",
          "#print axioms hecke3_inverse_certificate", "", "end RankP1277", ""]
content = "\n".join(lines)
target = HERE / "RankP1277.lean"
parser = argparse.ArgumentParser()
parser.add_argument("--write", action="store_true")
args = parser.parse_args()
if args.write:
    target.write_text(content)
else:
    assert target.read_text() == content
print("RANK_P1277_FORMAL_PASS", len(direct_rows), len(hecke_rows), len(hecke53), len(hecke3))
