"""Replay the deletion table using the earlier exhaustive four-step prefix counter."""
import csv
import io
import subprocess
import sys
from pathlib import Path
from matched_bases import sample_basis, smooth_basis

here = Path(__file__).resolve().parent
control = sys.argv[2:] == ["seed3"]
assert control or len(sys.argv) == 2
xs = sample_basis(3) if control else smooth_basis()
suffix = "-seed3" if control else ""

# A signed three-step return would give a two-step endpoint in the basis.
# Use ordinary affine arithmetic with Python modular inversion for this check.
p = 2**31-1
labels = set(xs)
points = [(x,pow((x**3+2*x+14)%p,(p+1)//4,p)) for x in xs]
for i,(x,y) in enumerate(points):
    for u,v in points[i:]:
        for w in (v,-v % p):
            if x == u and (y+w)%p == 0:
                continue
            slope = ((3*x*x+2)*pow(2*y,-1,p) if x == u else (y-w)*pow(x-u,-1,p))
            assert (slope*slope-x-u)%p not in labels

def count(removed):
    raw = subprocess.check_output([sys.argv[1], "five-prefixes"],
        input="".join(f"{x}\n" for i,x in enumerate(xs) if i not in removed), text=True)
    bins = {int(row["prefix_permutations"]): int(row["completable_prefixes_up_to_sign"])
            for row in csv.DictReader(io.StringIO(raw))}
    assert set(bins) == {1,4,6,12,24}
    assert all(bins[k] == 0 for k in (1,4,6,12))
    # The frozen basis has no three-step return. Each five-label class
    # supplies five distinct four-label prefixes, one per removed label.
    assert bins[24] % 5 == 0
    return bins[24] // 5

initial = count(set())
assert initial == (21 if control else 20)
selected = set()
with (here / f"private-pivots{suffix}.csv").open() as stream:
    for row in csv.DictReader(stream):
        i = int(row["removed_label"])
        assert 0 <= i < len(xs) and i not in selected
        assert count({i}) == int(row["classes_without_this_label"]) == initial - 1
        selected.add(i)
        assert count(selected) == int(row["classes_without_all_selected"]) == initial - len(selected)
assert len(selected) == (21 if control else 19)
print(f"{initial} classes; {len(selected)} private coordinates; {initial-len(selected)} residual")
