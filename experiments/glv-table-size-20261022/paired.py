"""Paired curve_solve ops ratio A/B on identical (curve, target), 95% bootstrap over curves."""
import gzip, json, random, sys
from collections import defaultdict
def load(b):
    d = {}
    for l in gzip.open(f"raw/trace_{b}.jsonl.gz", "rt"):
        r = json.loads(l); d[(r["family"], r["r_bits"], r["curve_index"], r["target"])] = r
    return d
B = 4000
res = {}
for A, Bn in [("escape", "legacy"), ("r32legacy", "legacy"), ("r32escape", "escape"), ("r32escape", "r32legacy")]:
    a, b = load(A), load(Bn)
    cells = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    for k, ra in a.items():
        rb = b.get(k)
        if rb is None: continue
        assert (ra["p"], ra["a"], ra["b"]) == (rb["p"], rb["a"], rb["b"])
        c = cells[(k[0], k[1])][k[2]]; c[0] += ra["total_ops"]; c[1] += rb["total_ops"]
    for (fam, bits), cur in sorted(cells.items()):
        v = list(cur.values()); rng = random.Random(f"{A}/{Bn}/{fam}/{bits}")
        st = lambda idx: sum(v[i][0] for i in idx) / sum(v[i][1] for i in idx)
        boots = sorted(st([rng.randrange(len(v)) for _ in v]) for _ in range(B))
        res[f"{A}/{Bn}:{fam}:{bits}"] = {"ratio": st(range(len(v))), "ci95": [boots[int(.025 * B)], boots[int(.975 * B) - 1]], "curves": len(v)}
json.dump(res, open("paired.json", "w"), indent=1)
for k, e in res.items(): print(f"{k:32s} {e['ratio']:.3f} [{e['ci95'][0]:.3f}, {e['ci95'][1]:.3f}] n={e['curves']}")
