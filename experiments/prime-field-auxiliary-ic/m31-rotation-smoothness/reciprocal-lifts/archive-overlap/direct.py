"""Independent histogram using explicit coordinates and ordinary field scalings."""
import json
from pathlib import Path
import subprocess
import sys

import numpy as np

here = Path(__file__).resolve().parent
receipt = json.loads((here / "result.json").read_text())
path = "experiments/prime-field-auxiliary-ic/snapshot/algebraic/optimized/results/field31_s5_base0/public.json"
fixture = json.loads(subprocess.check_output(["git", "show", f"{receipt['archive']}:{path}"], cwd=here))
p = 2**31 - 1
pairs = subprocess.check_output([str(Path(sys.argv[1]).resolve())]).splitlines()
coordinates = set()
for line in pairs:
    x = int(line)
    for seed in (x, pow(x, -1, p)):
        for _ in range(31):
            coordinates.add(seed)
            seed = (2*seed) % p
assert len(coordinates) == 204724
support = np.array(list(coordinates), dtype=np.uint64)
for name, xs in [
    ("roots", fixture["structured_roots"]),
    ("columns", [x for x, _ in fixture["factor_base"]]),
    ("random_columns", [x for x, _ in fixture["random_factor_base"]]),
]:
    # For each coordinate x, enumerate every individual nonzero s with sx in support.
    # Products of two field residues fit in uint64, and outputs fit in uint32.
    scales = np.concatenate([((support * pow(x, -1, p)) % p).astype(np.uint32) for x in xs])
    distinct, multiplicities = np.unique(scales, return_counts=True)
    histogram = np.bincount(multiplicities)
    histogram[0] = p-1-len(distinct)
    expected = {int(k): v for k,v in receipt[name]["field_scales_by_hits"].items()}
    if dict(enumerate(histogram.tolist())) != expected:
        raise ValueError(f"{name} histogram mismatch")
    print(f"{name}: {len(scales)} incidences, complete histogram matches")
