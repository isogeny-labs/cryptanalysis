"""Replay distinct signed pair-sum coverage at threshold 20 using Python 3 and PARI/GP.

The holdout retains the original sampler's used-index map when changing seeds.
Each reported union spans accepted sets. Individual sums use two different points
from the same set. This experiment measures coverage and performs no timing.
"""

from pathlib import Path
import subprocess


AUDIT = """
emit(m,xs) = {
  my(v=materialize(xs), values=List());
  for(i=1,#v,for(j=i+1,#v,
    listput(values,lift(elladd(target,v[i],v[j])[1]));
    listput(values,lift(ellsub(target,v[i],v[j])[1]))));
  print(m," ",Vec(values))
};
{
  for(b=1,#batches,for(j=1,#batches[b],
    pair=batches[b][j]; xs=coordinates(pair[1]);
    if(score(xs)>=20,emit(1,xs),
      if(score(-xs)>=20,emit(2,-xs));
      ys=coordinates(pair[2]); if(score(ys)>=20,emit(3,ys)))));
}
"""
HOLDOUT = """
setrand(20261123);
batches=vector(36,b,vector(256,j,[nextIndex(),nextIndex()]));
"""


def coverage(program):
    run = subprocess.run(["gp", "-fq"], input=program, capture_output=True,
                         text=True, check=True)
    if run.stderr:
        raise RuntimeError(run.stderr)
    accepted = [0, 0, 0]
    distinct = [set(), set(), set()]
    for line in run.stdout.splitlines():
        arm, vector = line.split(" ", 1)
        index = int(arm) - 1
        if index not in range(3):
            raise ValueError(f"unexpected arm {arm}")
        accepted[index] += 1
        distinct[index].update(map(int, vector.strip("[]").split(",")))
    original, reflected, fresh = distinct
    return (*accepted, len(original | reflected), len(original | fresh))


def main():
    source = Path(__file__).with_name("panel.gp").read_text()
    prefix, boundary, _ = source.partition("\norders=")
    if not boundary:
        raise ValueError("cannot locate the end of the frozen sample definition")
    print("panel original reflected_fallback fresh_fallback reflected_union fresh_union")
    for name, extra, expected in [
        ("original", "", (980, 922, 877, 793622, 772816)),
        ("holdout", HOLDOUT, (963, 922, 863, 783391, 757856)),
    ]:
        observed = coverage(prefix + "\n" + extra + AUDIT)
        print(name, *observed, flush=True)
        if observed != expected:
            raise ValueError(f"{name} panel differs from its recorded counts {expected}")


if __name__ == "__main__":
    main()
