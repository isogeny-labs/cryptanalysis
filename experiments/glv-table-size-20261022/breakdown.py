"""Per family x size x build: where curve_solve's operations go (trace rows from trace_run.py)."""
import gzip
import json
import math
import sys
from collections import defaultdict

out = {}
for build in sys.argv[1:]:
    g = defaultdict(list)
    for line in gzip.open(f"raw/trace_{build}.jsonl.gz", "rt"):
        r = json.loads(line)
        g[(r["family"], r["r_bits"])].append(r)
    for (fam, bits), rows in sorted(g.items()):
        T = sum(r["total_ops"] for r in rows)
        rho = sum(r["rho_ops"] for r in rows)
        steps = sum(r["useful_steps"] for r in rows)
        e = {
            "n": len(rows),
            "cs_over_rho": T / rho,
            "dp_bits": sorted({r["dp_bits"] for r in rows}),
            "abandon_after": sorted({r["abandon_after"] for r in rows}),
            "W": round(sum(r["W"] for r in rows) / len(rows)),
            "mult_r": sorted({r["r"] for r in rows}),
            "share_setup": sum(r["table_ops"] + r["start_ops"] + r["restart_ops"] for r in rows) / T,
            "share_retry": sum(r["retry_steps"] for r in rows) / T,
            "share_cycle_waste": sum(r["abandon_wasted"] for r in rows) / T,
            "share_productive": (steps - sum(r["abandon_wasted"] for r in rows)) / T,
            "cycle_entries_per_1e4_steps": 1e4 * sum(r["abandons"] + r.get("escape2", 0) + r.get("escape4", 0) for r in rows) / steps,
            "abandons_per_1e4_steps": 1e4 * sum(r["abandons"] for r in rows) / steps,
            "escapes_per_1e4_steps": 1e4 * sum(r.get("escape2", 0) + r.get("escape4", 0) for r in rows) / steps,
            "mean_steps_per_walk_between_dps": steps / max(1, sum(r["dps"] for r in rows)),
        }
        out[f"{build}:{fam}:{bits}"] = e
json.dump(out, open("breakdown.json", "w"), indent=1)
hdr = "build   fam    bits cs/rho setup retry waste prod  entr/1e4 aband/1e4 esc/1e4 dp abandon W"
print(hdr)
for k, e in out.items():
    b, f, n = k.split(":")
    print(f"{b:7s} {f:6s} {n:>4s} {e['cs_over_rho']:.3f}  {e['share_setup']:.3f} {e['share_retry']:.3f} {e['share_cycle_waste']:.3f} {e['share_productive']:.3f}"
          f"  {e['cycle_entries_per_1e4_steps']:6.2f}  {e['abandons_per_1e4_steps']:6.2f}  {e['escapes_per_1e4_steps']:6.2f}  {e['dp_bits']} {e['abandon_after']} {e['W']}")
