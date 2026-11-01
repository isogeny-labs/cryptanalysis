#!/usr/bin/env python3
"""results.json from the Tier 1 workflow artifact (PROTOCOL.md claim rule).

    python3 analyze.py ARTIFACT_DIR OUT.json

ARTIFACT_DIR holds run-summary_<family>_<bits>.json and queue/results/<id>/{runs,pairs}.jsonl.
Per cell: median paired wall ratio ref/cand and the runner's 95% pair bootstrap, valid pairs,
CPU-time ratio, operation ratio, ns per operation per arm, and the ns-per-operation ratio
(wall ratio / ops ratio, interval scaled by the same constant)."""
import json
import re
import statistics
import sys
from pathlib import Path

art, out = Path(sys.argv[1]), sys.argv[2]
EXPECTED = {"j1728_38": "df0e321174cab70d", "j1728_40": "e17910cf4d6d0a22", "j1728_41": "08c446f53a24a1d1", "j1728_42": "71f73a5e27536b25", "j1728_44": "6f7d867cfd4fe4f8", "j1728_46": "85052ca772d3c208", "j1728_48": "6f24ba6e350b1abd", "j0_38": "9aedb9a35af40064", "j0_40": "bc1c64b3522430a2", "j0_41": "10c8b94b6652f498", "j0_42": "292a1304c2716d4a", "j0_44": "5ba26e797b37f1b2", "j0_46": "02f564dd7c4be57b", "j0_48": "c867c507fbe9bdda"}
res = {}
for cell, want in EXPECTED.items():
    s = json.load(open(art / f"run-summary_{cell}.json"))
    d = s["summary"]
    rdir = Path(s["output"].replace("/home/runner/work/_temp/glv-walltime", str(art)))
    runs = [json.loads(l) for l in open(rdir / "runs.jsonl")]
    pairs = [json.loads(l) for l in open(rdir / "pairs.jsonl")]
    arms = {"reference": [], "candidate": []}
    for r in runs:
        txt = (rdir / r["stdout_file"]).read_text()
        kv = dict(re.findall(r"(\w+)=(\S+)", txt))
        assert r["status"] == "valid" and kv["verified"] == "1" and kv["result"] == want, (cell, r["serial"])
        arms[r["variant"]].append((float(kv["online_ms"]), float(kv["cpu_ms"]), int(kv["ops"])))
    med = lambda v: statistics.median(v)
    ops = {k: {o for _, _, o in v} for k, v in arms.items()}
    assert all(len(v) == 1 for v in ops.values())
    ops = {k: next(iter(v)) for k, v in ops.items()}
    wall = {k: med([w for w, _, _ in v]) for k, v in arms.items()}
    cpu = {k: med([c for _, c, _ in v]) for k, v in arms.items()}
    ratio, ci = d["observed_ratio_median"], d["bootstrap95_by_pair"]
    opr = ops["reference"] / ops["candidate"]
    ns = {k: 1e6 * wall[k] / ops[k] for k in wall}
    res[cell] = {
        "valid_pairs": d["valid_pairs"], "paired_speedup": d["paired_speedup"],
        "wall_ratio_ref_over_cand": ratio, "wall_ci95": ci,
        "resolved": "faster" if ci[0] > 1 else ("slower" if ci[1] < 1 else "not resolved"),
        "cpu_ratio": cpu["reference"] / cpu["candidate"], "ops_ref": ops["reference"], "ops_cand": ops["candidate"],
        "ops_ratio_ref_over_cand": opr,
        "ns_per_op_ref": ns["reference"], "ns_per_op_cand": ns["candidate"],
        "nsop_ratio_ref_over_cand": ratio / opr, "nsop_ci95": [ci[0] / opr, ci[1] / opr],
        "median_wall_ms": wall, "pairs_valid": sum(p["status"] == "valid" for p in pairs),
        "gates": {k: d[k] for k in ("binaries_stable", "artifacts_stable", "runner_stable", "host_exclusivity_proved")},
    }
json.dump(res, open(out, "w"), indent=1)
for c, r in res.items():
    print(c, f"wall {r['wall_ratio_ref_over_cand']:.3f} {r['wall_ci95'][0]:.3f}-{r['wall_ci95'][1]:.3f} {r['resolved']}"
          f" ops {r['ops_ratio_ref_over_cand']:.3f} cpu {r['cpu_ratio']:.3f}"
          f" ns/op {r['ns_per_op_ref']:.1f}->{r['ns_per_op_cand']:.1f} nsop-ratio {r['nsop_ratio_ref_over_cand']:.3f}"
          f" [{r['nsop_ci95'][0]:.3f},{r['nsop_ci95'][1]:.3f}]")
