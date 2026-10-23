#!/usr/bin/env python3
"""Progress-metrics exporter for the `cryptanalysis` repo (C/C++/CUDA kernels, ECC2K-130, ic-bench).

Sources (committed, read at --ref):
  experiments/ic-bench/history.csv                      append-only IC benchmark history (recorded_at, suite, ...)
  ecc2k130/runner/research/production/**/result.json    GPU paired A/B runs (return_rate_billion_per_second)
  ecc2k130/README.md                                    headline B/s (prose; parsed as a fallback only)
Run: python3 tools/progress_metrics.py [--ref origin/main] [--since YYYY-MM-DD]
"""
# ---- progress-metrics exporter boilerplate (copied verbatim into each repo's tools/progress_metrics.py) ----
# Contract: print one JSON object per line to stdout. Fields: metric, value, date (YYYY-MM-DD),
# problem, unit, better (higher|lower|neutral), kind (gauge|event), label, source.
# Reads committed state at --ref via `git show`; never the working tree. stdlib only.
import argparse
import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(os.environ.get("PM_REPO_PATH") or Path(__file__).resolve().parents[1])
TODAY = dt.date.today().isoformat()


def _git(*args, check=True):
    p = subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True)
    if check and p.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {p.stderr.strip()[:200]}")
    return p.stdout


def show(ref, path):
    p = subprocess.run(["git", "-C", str(REPO), "show", f"{ref}:{path}"], capture_output=True, text=True)
    return p.stdout if p.returncode == 0 else None


def ls(ref, path=""):
    return [l for l in _git("ls-tree", "-r", "--name-only", ref, "--", path, check=False).splitlines() if l]


def file_history(ref, path, since):
    """Yield (date, commit, text) for the newest commit per day touching `path`, newest first."""
    out = _git("log", "--first-parent", ref, f"--since={since}", "--format=%H %cs", "--", path, check=False)
    seen = set()
    for line in out.splitlines():
        h, d = line.split()
        if d in seen:
            continue
        seen.add(d)
        txt = show(h, path)
        if txt is not None:
            yield d, h[:12], txt


def emit(metric, value, *, date=None, problem="misc", unit="", better="neutral", kind="gauge", label="", source=""):
    if value is None:
        return
    try:
        v = float(value)
    except (TypeError, ValueError):
        return
    if v != v:
        return
    print(json.dumps({"metric": metric, "value": v, "date": date or TODAY, "problem": problem, "unit": unit,
                      "better": better, "kind": kind, "label": label or metric, "source": source}))


def args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", default=os.environ.get("PM_REF", "origin/main"))
    ap.add_argument("--since", default=os.environ.get("PM_SINCE") or (dt.date.today() - dt.timedelta(days=90)).isoformat())
    return ap.parse_args()
# ---- end boilerplate ----

import csv
import io
import re
import statistics

P_IC = "ecdlp-index-calculus"
P_RHO = "ecc2k130-rho-throughput"


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def ic_bench(ref, since):
    txt = show(ref, "experiments/ic-bench/history.csv")
    if not txt:
        return
    rows = list(csv.DictReader(io.StringIO(txt)))
    by = {}
    for r in rows:
        day = (r.get("recorded_at") or "")[:10]
        if not day or day < since:
            continue
        by.setdefault((r.get("suite") or "unknown", day), []).append(r)
    for (suite, day), rs in by.items():
        src = f"experiments/ic-bench/history.csv suite={suite}"
        ok = [r for r in rs if (r.get("status") == "complete") and str(r.get("verified")).lower() == "true"]
        emit(f"icbench.{suite}.rows", len(rs), date=day, problem=P_IC, unit="count", better="neutral", kind="event",
             label=f"ic-bench {suite}: rows recorded", source=src)
        sp = [v for v in (_f(r.get("online_speedup")) for r in ok) if v is not None and v > 0]
        if sp:
            emit(f"icbench.{suite}.online_speedup_median", statistics.median(sp), date=day, problem=P_IC, unit="x",
                 better="higher", label=f"ic-bench {suite}: median online speedup (rho/IC online wall)", source=src)
            emit(f"icbench.{suite}.online_speedup_best", max(sp), date=day, problem=P_IC, unit="x",
                 better="higher", label=f"ic-bench {suite}: best online speedup", source=src)
        rr = [v for v in (_f(r.get("ratio_to_rho")) for r in ok) if v is not None and v > 0]
        if rr:
            emit(f"icbench.{suite}.ratio_to_rho_best", min(rr), date=day, problem=P_IC, unit="IC/rho",
                 better="lower", label=f"ic-bench {suite}: best whole-pipeline cost ratio to rho", source=src)
    emit("icbench.history_rows_total", len(rows), problem=P_IC, unit="count", better="higher",
         label="ic-bench history rows (all suites)", source="experiments/ic-bench/history.csv")


def ecc2k130_runs(ref, since):
    paths = [p for p in ls(ref, "ecc2k130/runner/research/production") if p.endswith("/result.json")]
    by_day = {}
    for p in paths:
        txt = show(ref, p)
        if not txt:
            continue
        try:
            d = json.loads(txt)
        except json.JSONDecodeError:
            continue
        day = (d.get("started_at_utc") or d.get("completed_at_utc") or "")[:10]
        if not day or day < since:
            continue
        # Failed paired runs may contain partial population measurements.
        valid = d.get("valid") is True
        rates, ratios = [], []
        if valid:
            for pr in d.get("population_results") or []:
                r = _f(pr.get("return_rate_billion_per_second"))
                if r:
                    rates.append(r)
                m = _f(pr.get("median_ratio"))
                if m:
                    ratios.append(m)
        e = by_day.setdefault(day, {"runs": 0, "valid": 0, "rates": [], "ratios": []})
        e["runs"] += 1
        e["valid"] += valid
        e["rates"] += rates
        e["ratios"] += ratios
    for day, e in by_day.items():
        src = "ecc2k130/runner/research/production/*/runs/*/result.json"
        emit("ecc2k130.gpu.paired_runs", e["runs"], date=day, problem=P_RHO, unit="count", kind="event",
             label="ECC2K-130 GPU paired A/B runs recorded", source=src)
        emit("ecc2k130.gpu.paired_runs_valid", e["valid"], date=day, problem=P_RHO, unit="count", kind="event",
             better="higher", label="ECC2K-130 GPU paired runs marked valid", source=src)
        if e["rates"]:
            emit("ecc2k130.gpu.return_rate_gps_max", max(e["rates"]), date=day, problem=P_RHO, unit="G it/s",
                 better="higher", label="ECC2K-130 GPU: best candidate walk rate in valid paired runs", source=src)
        if e["ratios"]:
            emit("ecc2k130.gpu.paired_median_ratio", statistics.median(e["ratios"]), date=day, problem=P_RHO,
                 unit="cand/ref", better="higher", label="ECC2K-130 GPU: median candidate/reference ratio in valid paired runs", source=src)


def readme_headline(ref):
    txt = show(ref, "ecc2k130/README.md") or ""
    m = re.search(r"\*\*([\d.]+)\s+billion iterations per second", txt)
    if m:
        emit("ecc2k130.readme.headline_gps", float(m.group(1)), problem=P_RHO, unit="G it/s", better="higher",
             label="ECC2K-130 README headline (one RTX PRO 6000)", source="ecc2k130/README.md")


def main():
    a = args()
    ic_bench(a.ref, a.since)
    ecc2k130_runs(a.ref, a.since)
    readme_headline(a.ref)


if __name__ == "__main__":
    main()
