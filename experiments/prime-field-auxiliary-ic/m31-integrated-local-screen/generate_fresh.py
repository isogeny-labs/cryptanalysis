"""Generate frozen coordinate-only M31 targets and a separate evaluator file."""
import json
import random
import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
helpers = runpy.run_path(str(HERE.parent / "m31-full-rust-comparison/replay.py"))
fixture = json.loads(helpers["frozen"]("comparison/field31/auxiliary/public.json"))
curve = helpers["Curve"](fixture["p"], a4=fixture["a"], a6=fixture["b"])
generator = tuple(fixture["P"])
n = fixture["n"]
rng = random.Random(2026112743)
scalars = []
while len(scalars) < 5:
    candidate = rng.randrange(1, n)
    if candidate not in scalars:
        scalars.append(candidate)
targets = [list(curve.mul(scalar, generator)) for scalar in scalars]
public = {"schema": "m31-inline-fresh-public/v1", "p": fixture["p"],
          "n": n, "a": fixture["a"], "b": fixture["b"], "G": list(generator),
          "targets": [{"index": i, "Q": point} for i, point in enumerate(targets)]}
evaluator = {"schema": "m31-inline-evaluator/v1", "scalars": scalars,
             "targets": targets}
with (HERE / "fresh-public.json").open("x") as out:
    json.dump(public, out, indent=2)
    out.write("\n")
with Path("/Volumes/SSD990/m31-inline-evaluator-20261127.json").open("x") as out:
    json.dump(evaluator, out, indent=2)
    out.write("\n")
