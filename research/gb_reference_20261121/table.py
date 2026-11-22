#!/usr/bin/env python3
"""Join f4_fp and msolve rows on the exported system and tabulate.

Inputs: f4_fp rows (pilot `--out` files, joined by `export_id`, or
`gb_ms_f4fp` rows, joined by `id`) and msolve rows (`run_msolve.py`, by
`id`).  A pair is joined only when both rows name the same system and the
msolve row's `ms_sha256` equals the pilot's `export_sha256` where both exist.

Checks per pair: planted_ok on both (planted targets), and agreement on
consistency (random targets: f4_fp `inconsistent` vs msolve basis [1]).  An
f4_fp row that timed out or stopped at its degree bound with pairs dropped is
`censored`: its max_cols is a lower bound and its consistency is not compared.

Output: one markdown table per set, grouped by (kind, m, control, t), with
medians over targets of max_cols and wall for each engine and their ratio
f4_fp / msolve, plus a JSON summary of every check.

Usage: table.py --f4 A.jsonl [B.jsonl ...] --msolve M.jsonl [...] [--md OUT.md]
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
from collections import defaultdict
from pathlib import Path

ID = re.compile(r"^(?P<kind>[a-z]+)-m(?P<m>\d+)-(?P<control>[a-z]+)-t(?P<t>\d+)-g\d+-"
                r"(?P<target>planted|random)\d+-p\d+(?P<direct>-direct)?$")


def rows(paths):
    for p in paths:
        for line in Path(p).read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                if "summary" not in r:
                    yield r


def med(xs):
    xs = [x for x in xs if x is not None]
    return statistics.median(xs) if xs else None


def fmt(x, nd=0):
    if x is None:
        return "—"
    return f"{x:,.{nd}f}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--f4", nargs="+", required=True)
    ap.add_argument("--msolve", nargs="+", required=True)
    ap.add_argument("--md")
    a = ap.parse_args()
    f4 = {}
    for r in rows(a.f4):
        k = r.get("export_id") or r.get("id")
        if k:
            f4[k] = r
    ms = {r["id"]: r for r in rows(a.msolve)}
    checks = defaultdict(int)
    groups = defaultdict(list)
    problems = []
    for sid, m in ms.items():
        g = ID.match(sid)
        f = f4.get(sid)
        if not g:
            continue
        if f is None:
            checks["msolve_only"] += 1
            continue
        if f.get("export_sha256") and f["export_sha256"] != m["ms_sha256"]:
            problems.append({"id": sid, "problem": "sha256 mismatch"})
            continue
        censored = bool(f.get("timed_out")) or (f.get("pairs_above_bound") or 0) > 0
        m_ok = m["status"] == "ok"
        if g["target"] == "planted":
            for eng, r in (("f4_fp", f), ("msolve", m)):
                if r.get("planted_ok") is False:
                    problems.append({"id": sid, "problem": f"{eng} planted violation"})
        elif m_ok and not censored:
            agree = bool(f.get("inconsistent")) == bool(m.get("inconsistent"))
            checks["consistency_agree" if agree else "consistency_disagree"] += 1
            if not agree:
                problems.append({"id": sid, "problem": "consistency disagreement",
                                 "f4_fp": f.get("inconsistent"), "msolve": m.get("inconsistent")})
        checks["joined"] += 1
        checks["f4_censored"] += censored
        checks["msolve_" + m["status"]] += 1
        f_wall = f.get("wall_s") if f.get("wall_s") is not None else (f.get("ms") or 0) / 1000
        key = ("direct" if g["direct"] else "chain", g["kind"], int(g["m"]), g["control"], int(g["t"]), g["target"])
        groups[key].append({"f_cols": f.get("max_cols"), "m_cols": m.get("max_cols") if m_ok else None,
                            "f_wall": f_wall, "m_wall": m.get("wall_s") if m_ok else None,
                            "censored": censored, "m_status": m["status"]})
    lines = []
    for pres in ("chain", "direct"):
        keys = sorted(k for k in groups if k[0] == pres)
        if not keys:
            continue
        title = "Set A: PKM tower, chain presentation" if pres == "chain" else \
            "Set B: direct Semaev S_{m+1}"
        lines += [f"### {title}", "",
                  "| kind | m | control | t | target | systems | f4_fp max_cols | msolve max_cols | cols ratio | "
                  "f4_fp wall s | msolve wall s | wall ratio | f4_fp censored | msolve not ok |",
                  "|:--|--:|:--|--:|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|"]
        for k in keys:
            g = groups[k]
            fc, mc = med([x["f_cols"] for x in g]), med([x["m_cols"] for x in g])
            fw, mw = med([x["f_wall"] for x in g]), med([x["m_wall"] for x in g])
            cr = fc / mc if fc and mc else None
            wr = fw / mw if fw and mw else None
            lines.append(f"| {k[1]} | {k[2]} | {k[3]} | {k[4]} | {k[5]} | {len(g)} | {fmt(fc)} | {fmt(mc)} | "
                         f"{fmt(cr, 1)} | {fmt(fw, 3)} | {fmt(mw, 3)} | {fmt(wr, 1)} | "
                         f"{sum(x['censored'] for x in g)} | {sum(x['m_status'] != 'ok' for x in g)} |")
        lines.append("")
    summary = {"checks": dict(checks), "problems": problems}
    lines += ["```json", json.dumps(summary, indent=1), "```", ""]
    text = "\n".join(lines)
    if a.md:
        Path(a.md).write_text(text)
    print(text)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
