"""Print exact full-field counts at each archived structured root used as a center."""
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURE = "experiments/prime-field-auxiliary-ic/snapshot/algebraic/optimized/results/field31_s5_base0/public.json"
fixture = json.loads(subprocess.check_output(["git", "show", f"efb9330c1:{FIXTURE}"], cwd=HERE))
p = 2**31 - 1
assert fixture["public"]["p"] == p and (fixture["public"]["a"], fixture["public"]["b"]) == (2, 14)
roots = fixture["structured_roots"]
assert len(set(roots)) == len(roots) == 32 and all(type(c) is int and 0 <= c < p for c in roots)
centers = sorted(set([0, *roots]))
source = (HERE / "shifted.gp").read_text()
source += f"p={p}; centers={centers};\n"
source += 'for(i=1,#centers,c=centers[i];s=shifted(p,c);print(c,",",s,",",(p-s)/4))\n'
run = subprocess.run(["gp", "-fq"], input=source, text=True, capture_output=True, check=True)
if run.stderr:
    raise RuntimeError(run.stderr)
records = [tuple(map(int, row.split(","))) for row in run.stdout.splitlines()]
assert [c for c, _, _ in records] == centers
assert records[0] == (0, 105943, 536844426)
assert all(p - s == 4*m and 536824571 <= m <= 536917252 for _, s, m in records)
print("center,correlation,mixed_pairs")
print(run.stdout, end="")
