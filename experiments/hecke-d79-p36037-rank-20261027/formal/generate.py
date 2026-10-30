"""Generate exact finite and rational kernel/minor certificates for p36037."""
import argparse
import hashlib
import json
import math
from fractions import Fraction
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
assert audit["source_projection_counts"] == {"2": 20, "3": 20}


def row(raw):
    return {int(i): int(v) for i, v in raw.items() if v}


base = [row(x["row"]) for x in data["base_rows"]]
direct_rows = base + [row(x["row"]) for x in analysis["direct"]["candidates"]]
hecke_rows = base + [row(x["row"]) for x in analysis["hecke"]["candidates"]]
both_rows = direct_rows + [row(x["row"]) for x in analysis["hecke"]["candidates"]]
assert len(base) == 20 and len(direct_rows) == 233 and len(hecke_rows) == 218
assert len(both_rows) == 431
assert data["class_size"] == 40 and data["largest_prime_factor"] == 1451


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


def modular_kernels(rows, modulus):
    chosen = independent(rows, modulus)
    pivots, _, _, reduced = minor_inverse(chosen, modulus)
    free = [i for i in range(40) if i not in pivots]
    vectors = []
    for column in free:
        v = [0]*40
        v[column] = 1
        for r, pivot in enumerate(pivots):
            v[pivot] = -reduced[r][column] % modulus
        vectors.append(v)
    assert all(sum(r.get(i, 0)*v[i] for i in range(40)) % modulus == 0
               for r in rows for v in vectors)
    return free, vectors


def rational_kernels(rows):
    M = [[Fraction(r.get(j, 0)) for j in range(40)] for r in rows]
    pivots = []
    rank = 0
    for col in range(40):
        pivot = next((i for i in range(rank, len(M)) if M[i][col]), None)
        if pivot is None:
            continue
        M[rank], M[pivot] = M[pivot], M[rank]
        z = M[rank][col]
        M[rank] = [x/z for x in M[rank]]
        for i in range(len(M)):
            if i != rank and M[i][col]:
                z = M[i][col]
                M[i] = [x-z*y for x, y in zip(M[i], M[rank])]
        pivots.append(col)
        rank += 1
    free = [i for i in range(40) if i not in pivots]
    vectors = []
    for column in free:
        v = [Fraction(0) for _ in range(40)]
        v[column] = 1
        for r, pivot in enumerate(pivots):
            v[pivot] = -M[r][column]
        den = math.lcm(*(x.denominator for x in v))
        vector = [int(den*x) for x in v]
        assert vector[column] == den and den > 0
        vectors.append(vector)
    assert all(sum(r.get(i, 0)*v[i] for i in range(40)) == 0
               for r in rows for v in vectors)
    return rank, free, vectors


def lit(xs):
    return "[" + ", ".join(map(str, xs)) + "]"


def mat(xs):
    return "[\n" + "\n".join("  " + lit(r) + ("," if i+1 < len(xs) else "")
                              for i, r in enumerate(xs)) + "\n]"


arms = [("direct", direct_rows, 37, 37),
        ("hecke", hecke_rows, 34, 34),
        ("both", both_rows, 39, 40)]
lines = ["module", "", "public import Init", "", "namespace RankP36037", "",
         "set_option maxRecDepth 65536", "set_option maxHeartbeats 0", "",
         "public def entry (M : List (List Nat)) (i j : Nat) : Nat :=",
         "  (M.getD i []).getD j 0",
         "public def entryZ (M : List (List Int)) (i j : Nat) : Int :=",
         "  (M.getD i []).getD j 0", ""]
for label, rows, qrank, qrank3 in arms:
    qchoice = independent(rows, 1451)
    choice3 = independent(rows, 3)
    assert (len(qchoice), len(choice3)) == (qrank, qrank3)
    freeq, kernelsq = modular_kernels(rows, 1451)
    rankz, freez, kernelsz = rational_kernels(rows)
    assert rankz == qrank3
    lines += [f"public def {label}AllRows1451 : List (List Nat) := " +
              mat([[r.get(i, 0) % 1451 for i in range(40)] for r in rows]),
              f"public def {label}AllRows3 : List (List Nat) := " +
              mat([[r.get(i, 0) % 3 for i in range(40)] for r in rows]),
              f"public def {label}Kernels1451 : List (List Nat) := " + mat(kernelsq),
              f"public def {label}Free1451 : List Nat := " + lit(freeq),
              f"public def {label}Dot1451 (a b : List Nat) : Nat :=",
              "  ((a.zip b).foldl (fun s x => s + x.1 * x.2) 0) % 1451", "",
              f"public theorem {label}_all_rows_annihilate_q_kernels :",
              f"    {label}Kernels1451.all (fun k =>",
              f"      {label}AllRows1451.all (fun r => {label}Dot1451 r k == 0)) = true := by decide",
              f"public theorem {label}_q_kernels_free_identity : ∀ i j : Fin {len(freeq)},",
              f"    entry {label}Kernels1451 i.val ({label}Free1451.getD j.val 0) =",
              "      if i.val == j.val then 1 else 0 := by decide", ""]
    if kernelsz:
        lines += [f"public def {label}AllRowsZ : List (List Int) := " +
                  mat([[r.get(i, 0) for i in range(40)] for r in rows]),
                  f"public def {label}KernelsZ : List (List Int) := " + mat(kernelsz),
                  f"public def {label}FreeZ : List Nat := " + lit(freez),
                  f"public def {label}DotZ (a b : List Int) : Int :=",
                  "  (a.zip b).foldl (fun s x => s + x.1 * x.2) 0", "",
                  f"public theorem {label}_all_rows_annihilate_z_kernels :",
                  f"    {label}KernelsZ.all (fun k =>",
                  f"      {label}AllRowsZ.all (fun r => {label}DotZ r k == 0)) = true := by decide",
                  f"public theorem {label}_z_kernels_free_diagonal : ∀ i j : Fin {len(freez)},",
                  f"    entryZ {label}KernelsZ i.val ({label}FreeZ.getD j.val 0) =",
                  f"      if i.val == j.val then entryZ {label}KernelsZ i.val",
                  f"        ({label}FreeZ.getD i.val 0) else 0 := by decide",
                  f"public theorem {label}_z_kernels_diagonal_nonzero : ∀ i : Fin {len(freez)},",
                  f"    entryZ {label}KernelsZ i.val ({label}FreeZ.getD i.val 0) ≠ 0 := by decide", ""]
    for modulus, choice in [(1451, qchoice), (3, choice3)]:
        n = len(choice)
        prefix = f"{label}{modulus}"
        pivots, minor, inverse, _ = minor_inverse(choice, modulus)
        lines += [f"public def {prefix}Rows : List (List Nat) := " +
                  mat([[r.get(i, 0) % modulus for i in range(40)] for r in choice]),
                  f"public theorem {prefix}_rows_in_all :",
                  f"    {prefix}Rows.all (fun r => {label}AllRows{modulus}.contains r) = true := by decide", "",
                  f"public def {prefix}Pivots : List Nat := " + lit(pivots),
                  f"public def {prefix}Minor : List (List Nat) := " + mat(minor),
                  f"public def {prefix}Inverse : List (List Nat) := " + mat(inverse), "",
                  f"public theorem {prefix}_minor_matches : ∀ i j : Fin {n},",
                  f"    entry {prefix}Minor i.val j.val =",
                  f"      entry {prefix}Rows i.val ({prefix}Pivots.getD j.val 0) := by decide", "",
                  f"public theorem {prefix}_inverse_certificate : ∀ i j : Fin {n},",
                  f"    ((List.range {n}).foldl (fun total k =>",
                  f"      total + entry {prefix}Minor i.val k * entry {prefix}Inverse k j.val) 0) % {modulus} =",
                  "      if i.val == j.val then 1 else 0 := by decide", ""]
    lines += [f"#print axioms {label}_all_rows_annihilate_q_kernels",
              f"#print axioms {label}_q_kernels_free_identity"]
    if kernelsz:
        lines += [f"#print axioms {label}_all_rows_annihilate_z_kernels",
                  f"#print axioms {label}_z_kernels_free_diagonal",
                  f"#print axioms {label}_z_kernels_diagonal_nonzero"]
    for modulus in (1451, 3):
        lines += [f"#print axioms {label}{modulus}_rows_in_all",
                  f"#print axioms {label}{modulus}_minor_matches",
                  f"#print axioms {label}{modulus}_inverse_certificate"]
lines += ["", "end RankP36037", ""]
content = "\n".join(lines)
target = HERE / "RankP36037.lean"
parser = argparse.ArgumentParser()
parser.add_argument("--write", action="store_true")
args = parser.parse_args()
if args.write:
    target.write_text(content)
else:
    assert target.read_text() == content
print("RANK_P36037_FORMAL_PASS", len(direct_rows), len(hecke_rows), len(both_rows))
