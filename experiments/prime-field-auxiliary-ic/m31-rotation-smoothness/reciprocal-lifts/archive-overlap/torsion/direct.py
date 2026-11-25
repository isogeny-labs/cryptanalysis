"""Recheck sibling histograms with literal coordinates and individual scales."""
from collections import Counter, defaultdict
import json
from pathlib import Path
import subprocess
import sys

import numpy as np

here = Path(__file__).resolve().parent
sys.path.insert(0, str(here.parents[1]))
from census import P, pair_representatives, reciprocal

receipt = json.loads((here / "result.json").read_text())
path = "experiments/prime-field-auxiliary-ic/snapshot/algebraic/optimized/results/field31_s5_base0/public.json"
fixture = json.loads(subprocess.check_output(["git","show",f"{receipt['archive']}:{path}"],cwd=here))
support = sorted({(z << i) % P for x in pair_representatives(reciprocal)
                  for z in (x, reciprocal(x)) for i in range(31)})
coords = np.array(support, dtype=np.uint64)
xs = fixture["structured_roots"]
for step, result in zip(fixture["auxiliary"]["maps"], receipt["levels"], strict=True):
    grouped = defaultdict(list)
    for x in xs:
        u = (x-step["r"]) % P
        parent = (u+step["A"]+step["B"]*reciprocal(u)) % P
        grouped[parent].append(u)
    scale_counts = Counter()
    compatible_hits = 0
    for u,v in grouped.values():
        scales = coords * reciprocal(u) % P
        partners = scales * v % P
        hits = scales[np.isin(partners, coords, kind="sort")]
        scale_counts.update(map(int,hits))
        compatible_hits += sum(pow(s*s*step["B"] % P,31,P)==1 for s in map(int,hits))
    hist = Counter(scale_counts.values())
    hist[0] = P-1-len(scale_counts)
    assert hist == {int(k):v for k,v in result["scales_by_complete_pairs"].items()}
    assert compatible_hits == sum(int(k)*n for k,n in result["compatible_by_complete_pairs"].items())
    xs = list(grouped)
    print(f"{len(grouped)} pairs, {len(scale_counts)} hitting scales, {compatible_hits} compatible incidences")
assert xs == [fixture["auxiliary"]["terminal_c"]]
