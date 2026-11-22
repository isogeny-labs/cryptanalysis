"""Check an identity submatrix in the archived depth-five zero predicate."""
from pathlib import Path
import json
import subprocess

ROOT = Path(__file__).resolve().parent
FIXTURE = ROOT / "snapshot/algebraic/optimized/results/field31_s5_base0/public.json"

LEAN = """import Std
namespace ZeroGrid
abbrev p := 2147483647
abbrev Pt := Nat × Nat
def onCurve (q : Pt) := q.1 < p && q.2 < p &&
  q.2*q.2%p == (q.1^3+2*q.1+14)%p
def hit (roots : List Nat) (x y : Nat) :=
  let xy := x*y%p
  let d := ((x+p-y)%p)^2%p
  let c := 2*((x+y)*(xy+2)+28)%p
  let h := (((xy+p-2)%p)^2+p-(56*(x+y))%p)%p
  roots.any fun z => (d*z*z%p+p-c*z%p+h)%p == 0
"""


def main():
    data = json.loads(FIXTURE.read_bytes())
    p = 2147483647
    assert (data["public"]["p"], data["public"]["a"], data["public"]["b"]) == (p, 2, 14)
    base = list(map(tuple, data["factor_base"]))
    roots = data["structured_roots"]
    assert len(base) == 17 and len(roots) == 32
    # For the full-field counting argument, z=3 supplies a rational fiber point
    # and every factor remains a nonzero polynomial even when a leading term vanishes.
    assert (3, 417540811) in base and 3 in roots
    assert all((z**3 + 2*z + 14) % p != 0 for z in roots)
    doubled = []
    for x, y in base:
        slope = (3*x*x+2) * pow(2*y, -1, p) % p
        t = (slope*slope-2*x) % p
        doubled.append((t, (slope*(x-t)-y) % p))
    code = [LEAN, f"def roots : List Nat := {roots}",
            f"def rows : List Pt := {base}", f"def cols : List Pt := {doubled}",
            "example : rows.all onCurve && cols.all onCurve := by decide +kernel"]
    for i, (x, _) in enumerate(base):
        values = ", ".join("true" if i == j else "false" for j in range(len(base)))
        code.append(f"example : cols.map (fun q => hit roots {x} q.1) = [{values}] := by decide +kernel")
    subprocess.run(["lean", "--stdin"], input="\n".join(code + ["end ZeroGrid"]), text=True, check=True)
    print("Verified identity of size", len(base))


if __name__ == "__main__":
    main()
