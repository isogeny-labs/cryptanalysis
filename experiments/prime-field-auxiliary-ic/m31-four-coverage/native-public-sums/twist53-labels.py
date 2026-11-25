"""Exact same-abscissa twist tags for finite signed-pair sums on M31."""
from collections import Counter
from pathlib import Path
import runpy
import subprocess

HERE = Path(__file__).resolve().parent
control = runpy.run_path(str(HERE / "equal-size-control.py"))
P = control["P"]
SNAPSHOT = "9c702d0:experiments/prime-field-auxiliary-ic/snapshot/algebraic/end_to_end/field31_s5_base0/"


def archived(name):
    text = subprocess.check_output(["git", "-C", str(HERE), "show", SNAPSHOT + name + ".txt"], text=True)
    return [tuple(map(int, row.split())) for row in text.splitlines()[3:]]


def abscissae(points):
    keys = set()
    for i, (x, y) in enumerate(points):
        assert (y*y-x**3-2*x-14) % P == 0
        double_slope = (3*x*x+2)*pow(2*y, -1, P) % P
        keys.add((double_slope**2-2*x) % P)
        for u, v in points[:i]:
            inverse = pow(u-x, -1, P)
            for signed_v in (v, -v):
                slope = (signed_v-y)*inverse % P
                keys.add((slope*slope-x-u) % P)
    assert len(keys) == len(points)**2
    return keys


def main():
    a, b = archived("same_base"), archived("random")
    left, right = abscissae(a), abscissae(b)
    mixed = abscissae(a+b)
    cases = {"aux": left, "random": right, "cross": mixed-left-right, "mixed": mixed,
             "control34": abscissae(control["public_basis"](0))}
    keys = sorted(set.union(*cases.values()))
    gp = """
p=2^31-1; E=ellinit([2,-14],p); n=ellcard(E);
if(n!=53*40518151,error("twist order"));
tag(x)={my(v=ellordinate(E,Mod(x,p)),T);if(#v==0,return(-2));T=ellmul(E,[Mod(x,p),v[1]],40518151);if(T==[0],return(-1));if(ellmul(E,T,53)!=[0],error("subgroup"));lift(T[1])};
"""
    gp += "v=" + str(keys) + ";for(i=1,#v,print(tag(v[i])))\n"
    proc = subprocess.run(["gp", "-fq"], input=gp, capture_output=True, text=True, check=True)
    if proc.stderr:
        raise RuntimeError(proc.stderr)
    tags = dict(zip(keys, map(int, proc.stdout.splitlines()), strict=True))
    for case, xs in cases.items():
        counts = Counter(tags[x] for x in xs)
        print(case, len(xs), "tags", len(counts), "no lift", counts[-2],
              "identity", counts[-1], "finite range",
              min(c for t,c in counts.items() if t >= 0), max(c for t,c in counts.items() if t >= 0))


if __name__ == "__main__":
    main()
