#!/usr/bin/env python3
"""Progress-metrics exporter for the `cryptanalysis` repo (C/C++/CUDA kernels, ECC2K-130, ic-bench).

Sources (committed, read at --ref):
  experiments/ic-bench/history.csv                      append-only IC benchmark history (recorded_at, suite, ...)
  ecc2k130/runner/research/production/**/result.json    GPU paired A/B runs (return_rate_billion_per_second)
  ecc2k130/README.md                                    headline B/s (prose; parsed as a fallback only)
  experiments/ghs-sweeper/quartic-cubic-checks/         exact local spectral census (no attack/novelty claim)
Run: python3 tools/progress_metrics.py [--ref origin/main] [--since YYYY-MM-DD]
"""
# ---- progress-metrics exporter boilerplate (copied verbatim into each repo's tools/progress_metrics.py) ----
# Contract: print one JSON object per line to stdout. Fields: metric, value, date (YYYY-MM-DD),
# problem, unit, better (higher|lower|neutral), kind (gauge|event), label, source.
# Reads committed state at --ref via `git show`; never the working tree. stdlib only.
import argparse
import datetime as dt
import hashlib
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
P_HECKE = "hecke-relation-collection"

D79_INDEXES = (
    "experiments/hecke-d79-live-seven-20261027/index.json",
    "experiments/hecke-d79-live-eight-20261027/index.json",
    "experiments/hecke-d79-live-eight-stop-20261027/index.json",
    "experiments/hecke-d79-live-eight-row-stop-20261027/index.json",
    "experiments/hecke-d79-query-order-20261027/index.json",
)
D79_SUPPORT_EIGHT = "experiments/hecke-d79-support-eight-residual-20261027"


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


def ghs_quartic_evidence(ref, since):
    """Exact committed census counts; spectral matches do not certify transfers."""
    prefix = "experiments/ghs-sweeper/quartic-cubic-checks/"
    for day, _, txt in file_history(ref, prefix + "census-attempt-1.json", since):
        data = json.loads(txt)
        targets = data["target_representatives"]
        for trace in (-35, 35):
            emit(f"ghs.o3.spectral_targets.trace_{'minus' if trace < 0 else 'plus'}35",
                 sum(row["source_trace"] == trace for row in targets), date=day,
                 problem="binary-cubic-gluing-target-and-novelty", unit="count",
                 label=f"Published O3 spectral targets at trace {trace}; map unverified",
                 source=prefix + "census-attempt-1.json")
    for day, _, txt in file_history(ref, prefix + "local-missing-trace-audit.json", since):
        data = json.loads(txt)
        emit("ghs.o3.new_local_source_trace_classes", len(data["new_local_trace_classes_only"]),
             date=day, problem="binary-cubic-gluing-target-and-novelty", unit="count",
             label="Trace classes absent from the prior local journal; global novelty unproved",
             source=prefix + "local-missing-trace-audit.json")


def _arm_values(case, field):
    value = case.get(field)
    if isinstance(value, dict):
        return {str(arm): number for arm, number in value.items() if _f(number) is not None}
    return {"all": value} if _f(value) is not None else {}


def _support_number(value):
    words = {"four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8}
    text = str(value).lower()
    if text in words:
        return words[text]
    match = re.fullmatch(r"(?:support[-_ ]?)?(\d+)", text)
    return int(match.group(1)) if match else None


def _emit_d79_index(ref, path, since):
    """Emit cohort-separated operation counts only from completed, audited indexes."""
    index_text = show(ref, path)
    if not index_text:
        return
    root = path.removesuffix("/index.json")
    audit_text = show(ref, root + "/audit.json")
    if not audit_text:
        return
    index, audit = json.loads(index_text), json.loads(audit_text)
    if index.get("status") != "COMPLETE" or audit.get("status") != "PASS":
        return
    m = re.search(r"(\d{8})$", root)
    if not m:
        return
    day = dt.datetime.strptime(m.group(1), "%Y%m%d").date().isoformat()
    if day < since:
        return
    slug = root.rsplit("/", 1)[-1].removeprefix("hecke-d79-").removesuffix("-20261027")
    source = f"{path}; {root}/audit.json (PASS)"
    rank_field = "final_rank_eight_mod_q" if any("final_rank_eight_mod_q" in c for c in index.get("cases", [])) else "final_rank_mod_q"
    first_field = "first_eight_source_count" if any("first_eight_source_count" in c for c in index.get("cases", [])) else "source_count"
    for cohort in sorted({c.get("cohort", "unspecified") for c in index.get("cases", [])}):
        cases = [c for c in index.get("cases", []) if c.get("cohort", "unspecified") == cohort]
        if not cases:
            continue
        audited_yields = []
        for case in cases:
            summary_name, expected = case.get("summary"), case.get("summary_sha256")
            summary_text = show(ref, root + "/" + summary_name) if summary_name else None
            if not summary_text or not expected or hashlib.sha256(summary_text.encode("utf-8")).hexdigest() != expected:
                continue
            summary = json.loads(summary_text)
            row_counts = summary.get("row_counts")
            if isinstance(row_counts, dict):
                audited_yields.append(row_counts)
        arms = sorted({arm for c in cases for arm in _arm_values(c, rank_field)})
        for arm in arms:
            suffix = "" if arm == "all" else f".{arm}"
            ranked, first_counts = [], []
            for case in cases:
                rank = _arm_values(case, rank_field).get(arm)
                if rank is None:
                    continue
                ranked.append(float(rank) >= 39)
                first = _arm_values(case, first_field).get(arm)
                if first is not None and float(rank) >= 39:
                    first_counts.append(float(first))
            prefix = f"hecke.d79.{slug}.{cohort}{suffix}"
            emit(prefix + ".cases", len(cases), date=day, problem=P_HECKE, unit="count", better="neutral",
                 label=f"D79 {slug}: audited cases in {cohort} cohort" + (f" ({arm})" if arm != "all" else ""),
                 source=source)
            if ranked:
                reached = sum(ranked)
                emit(prefix + ".rank39_cases", reached, date=day, problem=P_HECKE, unit="count",
                     better="higher", label=f"D79 {slug}: cases reaching F_q rank 39 in {cohort} cohort" +
                     (f" ({arm})" if arm != "all" else ""), source=source)
                emit(prefix + ".rank39_fraction", reached / len(ranked), date=day, problem=P_HECKE,
                     unit="fraction", better="higher", label=f"D79 {slug}: fraction reaching F_q rank 39 in {cohort} cohort" +
                     (f" ({arm})" if arm != "all" else ""), source=source)
            if first_counts:
                emit(prefix + ".first_rank39_source_count_median", statistics.median(first_counts), date=day,
                     problem=P_HECKE, unit="sources", better="lower",
                     label=f"D79 {slug}: median sources at rank 39 in {cohort} cohort" +
                     (f" ({arm})" if arm != "all" else ""), source=source)
            for field, metric, label in (
                ("saved_eight_probes", "saved_through_horizon_probes", "signed quintuple probes saved through horizon"),
                ("saved_within_prefix_probes", "saved_within_prefix_probes", "signed quintuple probes saved inside final source"),
            ):
                values = [float(v) for c in cases for v in [_arm_values(c, field).get(arm)] if v is not None]
                if values:
                    emit(prefix + "." + metric, sum(values), date=day, problem=P_HECKE, unit="probes",
                         better="higher", label=f"D79 {slug}: {label}, {cohort} cohort" +
                         (f" ({arm})" if arm != "all" else ""), source=source)
            ratios = [float(v) for c in cases for v in [_arm_values(c, "paired_probe_ratio").get(arm)] if v is not None]
            if ratios:
                emit(prefix + ".paired_probe_ratio_median", statistics.median(ratios), date=day,
                     problem=P_HECKE, unit="lex/reverse-lex probes", better="higher",
                     label=f"D79 {slug}: median paired lex/reverse-lex probe ratio, {cohort} cohort" +
                     (f" ({arm})" if arm != "all" else ""), source=source)
        if audited_yields:
            supports = sorted({support for row_counts in audited_yields for support in row_counts},
                              key=lambda support: (_support_number(support) is None,
                                                   _support_number(support) or 0, str(support)))
            for support in supports:
                values = [float(row_counts[support]) for row_counts in audited_yields
                          if _f(row_counts.get(support)) is not None]
                if not values:
                    continue
                support_number = _support_number(support)
                if support_number is not None:
                    support_id = f"support{support_number}"
                    row_label = f"support-{support_number} relation rows"
                elif str(support).lower() in {"lex_eight", "reverse_lex_eight"}:
                    support_id = "order_" + str(support).lower()
                    row_label = f"{str(support).lower().replace('_', '-')} order eight-support relation rows"
                else:
                    continue
                label = f"audited {row_label}, {cohort} cohort (n={len(values)} cases)"
                yield_prefix = f"hecke.d79.{slug}.{cohort}.relation_rows.{support_id}"
                yield_source = source + "; hash-checked per-case summaries"
                emit(yield_prefix + ".total", sum(values), date=day, problem=P_HECKE, unit="rows",
                     better="higher", label=label + ", total", source=yield_source)
                emit(yield_prefix + ".median_per_case", statistics.median(values), date=day,
                     problem=P_HECKE, unit="rows/case", better="higher", label=label + ", median per case",
                     source=yield_source)


def hecke_d79_metrics(ref, since):
    """Expose committed, independently audited D79 counts without promoting timings."""
    for path in D79_INDEXES:
        _emit_d79_index(ref, path, since)

    root = D79_SUPPORT_EIGHT
    audit_text = show(ref, root + "/audit.json")
    initial_text = show(ref, root + "/result.json")
    full_text = show(ref, root + "/full/result.json")
    day_match = re.search(r"(\d{8})$", root)
    if not (audit_text and initial_text and full_text and day_match):
        return
    audit, initial, full = json.loads(audit_text), json.loads(initial_text), json.loads(full_text)
    day = dt.datetime.strptime(day_match.group(1), "%Y%m%d").date().isoformat()
    if day < since or audit.get("status") != "PASS":
        return
    source = f"{root}/result.json; {root}/full/result.json; {root}/audit.json (PASS)"
    prefix = "hecke.d79.support_eight_residual.retained_p1825517"
    for label, suffix, record in (("initial capped run", "initial_cap", initial),
                                  ("full-space follow-up", "full_followup", full)):
        emit(f"{prefix}.{suffix}.signed_quintuple_probes", record.get("quintuple_sign_probes"),
             date=day, problem=P_HECKE, unit="probes", better="lower",
             label=f"D79 support-eight residual: {label} signed quintuple probes (retained class, not a fresh panel)",
             source=source)
        emit(f"{prefix}.{suffix}.rank_after", record.get("rank_after"), date=day,
             problem=P_HECKE, unit="F_6091 rank", better="higher",
             label=f"D79 support-eight residual: {label} final rank", source=source)
    if full.get("rank_before") is not None and full.get("rank_after") is not None:
        emit(prefix + ".full_followup.rank_gain", full["rank_after"] - full["rank_before"], date=day,
             problem=P_HECKE, unit="F_6091 rank", better="higher",
             label="D79 support-eight residual: rank gain in audited full-space follow-up (retained class, not a fresh panel)",
             source=source)
    emit(prefix + ".full_followup.verified_rows", full.get("verified_rows"), date=day,
         problem=P_HECKE, unit="rows", better="higher",
         label="D79 support-eight residual: verified matched rows in full-space follow-up (retained class, not a fresh panel)",
         source=source)


def main():
    a = args()
    ic_bench(a.ref, a.since)
    ecc2k130_runs(a.ref, a.since)
    readme_headline(a.ref)
    ghs_quartic_evidence(a.ref, a.since)
    hecke_d79_metrics(a.ref, a.since)


if __name__ == "__main__":
    main()
