#!/usr/bin/env python3
"""Summarize a local smoke receipt (cloud-agent VM) into smoke/local_diagnostics.json.

LOCAL DIAGNOSTIC ONLY: a shared, loaded 4-vCPU VM, not timing evidence.
Usage: python3 smoke/summarize_local.py <receipt dir> [<receipt dir> ...]
Per row: arm, point, probes, root calls, relation checks, relation, scalar,
online ms and the online counters; per point: whether every IC arm agrees;
the online ratio cS / cF over the points where both ran.
"""
import base64
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def rows(receipt):
    for line in (receipt / "runs.jsonl").read_text().splitlines():
        row = json.loads(line)
        raw = None
        for text in (receipt / row["stdout_file"]).read_text().splitlines():
            if text.startswith("raw_b64="):
                raw = json.loads(base64.b64decode(text[len("raw_b64="):]))
        yield row, raw


def main():
    out = {"label": "LOCAL diagnostic on the cloud-agent VM (shared, loaded); not timing evidence",
           "receipts": [], "rows": [], "points": {}}
    for arg in sys.argv[1:]:
        receipt = Path(arg)
        out["receipts"].append(receipt.name)
        for row, raw in rows(receipt):
            f = raw["fields"]
            item = {"receipt": receipt.name, "serial": row["serial"], "arm": row["arm"], "point": row["point_id"],
                    "status": row["status"], "issues": row["issues"] + raw["issues"],
                    "scalar": f.get("recovered_scalar"), "online_ms": f.get("online_ms")}
            if raw["kind"] != "rho_tuned":
                item.update({k: f.get(k) for k in ("ops", "root_calls", "relation_checks", "relation",
                                                   "online_solve", "online_counters", "rank_stage_ms",
                                                   "logs_equal_archived", "rank_frame", "rank_padd")})
            out["rows"].append(item)
    ic = [r for r in out["rows"] if "ops" in r and r["status"] == "valid"]
    for point in sorted({r["point"] for r in ic}):
        mine = [r for r in ic if r["point"] == point]
        same = {k: len({json.dumps(r[k]) for r in mine}) == 1 for k in ("ops", "root_calls", "relation_checks",
                                                                        "relation", "scalar")}
        out["points"][point] = {"arms": sorted({r["arm"] for r in mine}), "identical": same,
                                "probes": mine[0]["ops"]}
    pairs = []
    for point in out["points"]:
        s = [r["online_ms"] for r in ic if r["point"] == point and r["arm"] == "cS" and r["receipt"] == out["receipts"][-1]]
        f = [r["online_ms"] for r in ic if r["point"] == point and r["arm"] == "cF" and r["receipt"] == out["receipts"][-1]]
        if s and f and point.startswith("s"):
            pairs.append((point, s[0], f[0]))
    if pairs:
        out["online_cS_over_cF_local"] = {"points": [p for p, _, _ in pairs],
                                          "ratio_of_means": sum(s for _, s, _ in pairs) / sum(f for _, _, f in pairs),
                                          "per_point": {p: s / f for p, s, f in pairs},
                                          "receipt": out["receipts"][-1]}
    (HERE / "local_diagnostics.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps({k: out[k] for k in ("points", "online_cS_over_cF_local") if k in out}, indent=1))


if __name__ == "__main__":
    main()
