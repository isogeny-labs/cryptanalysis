"""Check exact two-variable separation ranks on the archived M31 fixture."""
from pathlib import Path
import json
import subprocess

from sympy import GF
from sympy.polys.matrices import DomainMatrix

P = 2147483647
ROOT = Path(__file__).resolve().parent
FIXTURE = ROOT / "snapshot/algebraic/optimized/results/field31_s5_base0/public.json"


def evaluate(x, y, roots, maps, terminal):
    # Coefficients of Dz²-Cz+H in the fiber coordinate z.
    xy = x*y % P
    d = (x-y)**2 % P
    c = 2*((x+y)*(xy+2)+28) % P
    h = ((xy-2)**2-56*(x+y)) % P
    value = 1
    for z in roots:
        value = value * ((d*z-c)*z+h) % P

    # Independent evaluation of the centered producer recurrence.
    assert maps[0]["r"] == 0
    for i, stage in enumerate(maps):
        b = stage["B"]
        delta = stage["A"] - (maps[i+1]["r"] if i+1 < len(maps) else terminal)
        new_d = h*d % P
        norm = ((h-b*d)**2+b*c*c) % P
        cd = c*(h+b*d) % P
        if i+1 == len(maps):
            if value != (norm + delta*cd + delta**2*new_d) % P:
                raise ValueError("product and centered circuit disagree")
        else:
            c = (cd + 2*delta*new_d) % P
            h = (norm + delta*c - delta**2*new_d) % P
            d = new_d
    return value


LEAN = """import Std
namespace RankWitness
abbrev p := 2147483647
def entry (x y : Nat) (roots : List Nat) : Nat :=
  let xy := x*y%p
  let d := ((x+p-y)%p)^2%p
  let c := (2*((x+y)*(xy+2)+28))%p
  let h := (((xy+p-2)%p)^2+p-(56*(x+y))%p)%p
  roots.foldl (fun v z => v * ((d*z*z%p + p - c*z%p + h)%p)%p) 1
def dot (a b : List Nat) := (List.zipWith (·*·) a b).sum % p
"""


def main():
    data = json.loads(FIXTURE.read_bytes())
    assert tuple(data["public"][key] for key in ("p","a","b")) == (P,2,14)
    roots = data["structured_roots"]
    aux = data["auxiliary"]
    assert len(roots) == 32 and len(aux["maps"]) == 5
    code = [LEAN, f"def roots : List Nat := {roots}"]
    field = GF(P)
    # Use liftable coordinates in both directions, so the lower bound also
    # applies when every input must come from an actual curve point.
    grid = []
    x = 0
    while len(grid) < 65:
        rhs = (x**3 + 2*x + 14) % P
        y = pow(rhs, (P+1)//4, P)
        if y*y % P == rhs:
            grid.append((x,y))
        x += 1
    for name, xs in (("grid", [x for x,_ in grid]),
                     ("aux", [x for x,_ in data["factor_base"]]),
                     ("control", [x for x,_ in data["random_factor_base"]])):
        n = len(xs)
        rows = [[evaluate(x,y,roots,aux["maps"],aux["terminal_c"]) for y in xs] for x in xs]
        matrix = DomainMatrix.from_list(rows,field)
        determinant = int(matrix.det()) % P
        if determinant == 0:
            raise ValueError(f"singular {name} minor")
        print(name,n,determinant,flush=True)
        code.append(f"namespace {name}Witness")
        points = grid if name == "grid" else data["factor_base" if name == "aux" else "random_factor_base"]
        code.append(f"def points : List (Nat × Nat) := {[tuple(point) for point in points]}")
        code.append("example : points.all (fun (x,y) => y*y%p == (x^3+2*x+14)%p) = true := by decide +kernel")
        code.append("def coordinates := points.map Prod.fst")
        columns = [[int(v)%P for v in col] for col in matrix.inv().transpose().to_list()]
        for col_index, column in enumerate(columns):
            code.append(f"def col{col_index} : List Nat := {column}")
        names = ", ".join(f"col{i}" for i in range(n))
        code.append(f"def columns : List (List Nat) := [{names}]")
        for i,(x,row) in enumerate(zip(xs,rows)):
            code.append(f"def row{i} : List Nat := {row}")
            code.append(f"example : coordinates.map (fun y => entry {x} y roots) = row{i} := by decide +kernel")
            code.append(f"example : columns.map (dot row{i}) = {[int(i==j) for j in range(n)]} := by decide +kernel")
        code.append(f"end {name}Witness")
    subprocess.run(["lean","--stdin"],input="\n".join(code+["end RankWitness"]),text=True,check=True)


if __name__ == "__main__":
    main()
