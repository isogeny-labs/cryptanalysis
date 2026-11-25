"""Look for distinct private coordinates using only aggregate class counts."""
import csv
import subprocess
import sys
from matched_bases import sample_basis, smooth_basis

binary = sys.argv[1]
args = sys.argv[2:]
reverse = "reverse" in args
assert set(args) <= {"reverse","seed3"}
basis = sample_basis(3) if "seed3" in args else smooth_basis()

def count(excluded):
    xs = [x for i, x in enumerate(basis) if i not in excluded]
    if reverse:
        xs.reverse()
    return int(subprocess.check_output([binary, "simple-five"],
        input="".join(f"{x}\n" for x in xs), text=True))

writer = csv.writer(sys.stdout, lineterminator="\n")
writer.writerow(["removed_label", "classes_without_this_label", "classes_without_all_selected"])
initial = remaining = count(set())
selected = set()
for i in range(len(basis)):
    if not remaining:
        break
    single = count({i})
    if single != initial - 1:
        continue
    after = count(selected | {i})
    if after == remaining:
        continue
    assert after == remaining - 1
    selected.add(i)
    writer.writerow([i, single, after])
    remaining = after
# A single residual row already has nonzero coefficients on its five labels.
# All selected private coordinates vanish on it.
if remaining > 1:
    sys.exit(f"partial certificate: {remaining} classes still uncovered")
