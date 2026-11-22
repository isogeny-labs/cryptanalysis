"""Replay the two 578-point coverage certificates with Lean's kernel.

Run with Python 3 and the repository Lean toolchain on PATH. Python supplies
slope witnesses. Lean enumerates the pairs and checks each witness and sum.
"""
import itertools
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
FIXTURE = ROOT / "snapshot/algebraic/optimized/results/field31_s5_base0/public.json"
CHECKER = """import Std
namespace M31Coverage
abbrev p : Nat := 2147483647
abbrev Pt := Nat × Nat
def signed (base : List Pt) := base.flatMap fun (x,y) => [(x,y),(x,p-y)]
def pairs : List Pt → List (Pt × Pt)
  | [] => []
  | a::as => ((a::as).map fun b => (a,b)) ++ pairs as
def nonzero (a b : Pt) := !(a.1 == b.1 && (a.2+b.2)%p == 0)
def onCurve (a : Pt) := a.1 < p && a.2 < p && a.2*a.2%p == (a.1^3+2*a.1+14)%p
def check (row : (Pt × Pt) × Nat) : Bool :=
  let ((a,b),m) := row
  let (d,n) := if a == b then ((2*a.2)%p,(3*a.1^2+2)%p)
               else ((b.1+p-a.1)%p,(b.2+p-a.2)%p)
  d != 0 && m < p && m*d%p == n
def coord (row : (Pt × Pt) × Nat) : Pt :=
  let ((a,b),m) := row
  let x := (m*m + 2*p-a.1-b.1)%p
  (x,(m*((a.1+p-x)%p)+p-a.2)%p)
def distinct : List Nat → Bool
  | [] => true
  | x::xs => !(xs.contains x) && distinct xs

def cert (base : List Pt) (slopes : List Nat) :=
  let pts := signed base
  let allPairs := pairs pts
  let nz := allPairs.filter fun (a,b) => nonzero a b
  let rows := nz.zip slopes
  let out := rows.map coord
  let keys := out.map fun (x,y) => x*p+y
  pts.all onCurve && allPairs.length == 595 && nz.length == 578 &&
    slopes.length == nz.length && rows.all check && out.all onCurve &&
    distinct keys
"""


def emit_certificate(points, name, p, curve_a):
    signed = [(x, v) for x, y in points for v in (y, (-y) % p)]
    slopes = []
    for (x, y), (u, v) in itertools.combinations_with_replacement(signed, 2):
        if x == u and (y + v) % p == 0:
            continue
        if (x, y) == (u, v):
            numerator, denominator = 3 * x * x + curve_a, 2 * y
        else:
            numerator, denominator = v - y, u - x
        slopes.append(numerator * pow(denominator, -1, p) % p)
    coordinates = ", ".join(f"({x},{y})" for x, y in points)
    return f"""
def {name} : List Pt := [{coordinates}]
def {name}Slopes : List Nat := [{", ".join(map(str, slopes))}]
set_option maxRecDepth 20000 in
set_option maxHeartbeats 4000000 in
theorem {name}Coverage : cert {name} {name}Slopes = true := by decide +kernel
#print axioms {name}Coverage
"""


def main():
    fixture = json.loads(FIXTURE.read_bytes())
    curve = fixture["public"]
    if (curve["p"], curve["a"], curve["b"]) != (2147483647, 2, 14):
        raise ValueError("fixture curve differs from the Lean model")
    source = CHECKER
    for field, name in (("factor_base", "aux"), ("random_factor_base", "control")):
        source += emit_certificate(fixture[field], name, curve["p"], curve["a"])
    subprocess.run(
        ["lean", "--stdin"], input=source + "end M31Coverage\n",
        cwd=ROOT, text=True, check=True,
    )


if __name__ == "__main__":
    main()
