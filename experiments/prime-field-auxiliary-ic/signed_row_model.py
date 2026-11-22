"""Exact first-dependency distribution for uniformly shuffled signed two-term keys.

Every pair of distinct columns has two keys up to overall sign. Each column
also has one doubling key. The signed-graph independence criterion in odd
characteristic is given in Zaslavsky, Signed Graphs and Geometry, sections 2–3
(https://people.math.binghamton.edu/zaslav/Tpapers/sggm.pdf).
The model concerns algebraic dependence. It does not model query generation
or whether a final dependency has a nonzero target coefficient.
"""
import subprocess
from collections import defaultdict
from fractions import Fraction
from math import comb, factorial
from functools import cache

def signed_components(n):
    # Pick the unique cycle, then attach a rooted labeled forest to it.
    trees = 1 if n == 1 else 2**(n-1)*n**(n-2)
    unicyclic = 0
    for length in range(1,n+1):
        cycle = 1 if length <= 2 else factorial(length-1)*2**(length-2)
        forest = 1 if length == n else length*n**(n-length-1)
        unicyclic += comb(n,length)*cycle*forest*2**(n-length)
    return trees, unicyclic

@cache
def independent(n,k):
    if k<0 or k>n: return 0
    if n==0: return int(k==0)
    total=0
    for size in range(1,n+1):
        trees,cycles=signed_components(size)
        total += comb(n-1,size-1)*(trees*independent(n-size,k-size+1)+cycles*independent(n-size,k-size))
    return total

def transitions(n):
    # State lists the sizes of balanced tree components. Remaining vertices
    # belong to components with one unbalanced cycle and full row rank.
    counts=[1]
    states={(1,)*n:1}
    for k in range(1,n+1):
        nxt=defaultdict(int)
        for parts,weight in states.items():
            saturated=n-sum(parts)
            for i,a in enumerate(parts):
                rest=parts[:i]+parts[i+1:]
                # Add an unbalancing internal edge or join a full-rank component.
                nxt[rest]+=weight*(a*(a+1)//2+2*a*saturated)
                for j in range(i+1,len(parts)):
                    b=parts[j]
                    merged=tuple(sorted(parts[:i]+parts[i+1:j]+parts[j+1:]+(a+b,)))
                    nxt[merged]+=weight*2*a*b
        states=nxt
        counts.append(sum(states.values())//factorial(k))
        assert sum(states.values())==counts[-1]*factorial(k)
    return counts

def model(n):
    counts=transitions(n)
    assert counts==[independent(n,k) for k in range(n+1)]
    return [Fraction(value,comb(n*n,k)) for k,value in enumerate(counts)]+[Fraction(0)]
def elimination_counts(n):
    """Exhaustively extend independent row subsets over the archived order."""
    order = 2147505293
    rows = []
    for i in range(n):
        loop = [0] * n
        loop[i] = 2
        rows.append(loop)
        for j in range(i):
            for sign in (-1, 1):
                row = [0] * n
                row[i], row[j] = 1, sign
                rows.append(row)
    counts = [0] * (n + 1)
    def visit(start, pivots):
        counts[len(pivots)] += 1
        if len(pivots) == n:
            return
        for idx in range(start, len(rows)):
            row = rows[idx].copy()
            for col, pivot in sorted(pivots.items()):
                if row[col]:
                    row = [(x-row[col]*y) % order for x,y in zip(row,pivot)]
            col = next((c for c,x in enumerate(row) if x % order), None)
            if col is not None:
                inv = pow(row[col], -1, order)
                visit(idx+1, pivots | {col: [x*inv % order for x in row]})
    visit(0, {})
    return counts

def verify_arithmetic(n):
    lean = """import Std
namespace SignedRows

def fact (k : Nat) := ((List.range k).map (·+1)).prod
def choose (n k : Nat) : Nat :=
  if k > n then 0 else ((List.range k).map (fun j => n-j)).prod / fact k
def tree (n : Nat) := if n == 1 then 1 else 2^(n-1)*n^(n-2)
def unicyclic (n : Nat) :=
  ((List.range n).map fun j =>
    let m := j+1
    let cycle := if m ≤ 2 then 1 else fact (m-1)*2^(m-2)
    let forest := if m == n then 1 else m*n^(n-m-1)
    choose n m * cycle * forest * 2^(n-m)).sum
def atCell (tab : List (List Nat)) (n k : Nat) := ((tab[n]?).getD [])[k]?.getD 0
def count (tab : List (List Nat)) (n k : Nat) :=
  ((List.range n).map fun j =>
    let m := j+1
    choose (n-1) (m-1) *
      ((if m-1 ≤ k then tree m * atCell tab (n-m) (k+1-m) else 0) +
       (if m ≤ k then unicyclic m * atCell tab (n-m) (k-m) else 0))).sum
"""
    table = [[independent(i,k) for k in range(i+1)] for i in range(n+1)]
    lines = [lean, f"def tab : List (List Nat) := {table}",
             "example : tab[0]? = some [1] := by decide"]
    for i in range(1,n+1):
        lines.append(f"example : ((List.range {i+1}).map (count tab {i})) = tab[{i}]! := by decide +kernel")
    lines.append("example : 2 * atCell tab 17 12 > choose 289 12 ∧ 2 * atCell tab 17 13 ≤ choose 289 13 := by decide +kernel")
    lines.append("end SignedRows")
    subprocess.run(["lean", "--stdin"], input="\n".join(lines), text=True, check=True)


def main():
    for n in range(1,6):
        assert elimination_counts(n) == transitions(n) == [independent(n,k) for k in range(n+1)]
    survival = model(17)
    verify_arithmetic(17)
    print("mean distinct rows", float(sum(survival)))
    uniform_query_mean = sum(prob * Fraction(2147505293, 2*(289-i))
                             for i,prob in enumerate(survival[:-1]))
    print("mean queries under independent uniform sampling", float(uniform_query_mean))
    for k in range(1,len(survival)):
        print(k, float(1-survival[k]))


if __name__ == "__main__":
    main()
