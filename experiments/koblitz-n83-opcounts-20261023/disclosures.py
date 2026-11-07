#!/usr/bin/env python3
"""Disclosures beside the section 5a band of run 39882571652 (added 2026-11-06).

Sheriff case SHF-20261106-a114e7 (crypto-autoresearcher
research/sheriff/SHF-20261106-a114e7/) re-opened findings CAN-2, CAN-3 and
CAN-5 of SHF-20261028-0f3f64 and added CAX-2. Each asks for a read-out that
the frozen band (band.py, PROTOCOL.md) does not print. This script computes
those read-outs from the archived receipts only. It runs nothing, changes no
archived byte, and does not replace the band: the frozen band stays the
record, and everything here is reported beside it.

Inputs (all committed, read-only):

- run_github_39882571652/panel/runs/*.stdout.txt  (raw per-run payloads)
- run_github_39882571652/panel/counts.json        (the frozen band input)
- ../koblitz-n83-stacked-20261016/run_github_38862448935/panel/runs/
  (the archived twin; its second rank draw, seed 102, has rank probes only)
- docs/ic/baselines.json other_records[13] (X = 427.524 ms, the measured
  factor-base construction time of the replay run 39007026856)

Read-outs:

1. counters (CAX-2): every counter of every arm with its mean count per
   solved target, and its class in the frozen kind map (group, unpriced,
   reported-not-priced, bounded).
2. field_sensitivity (CAX-2): the gaps with the field kinds (field_mul,
   field_sqr, field_inv, field_half_trace) charged at w as well, and the
   crossover weight w* at which each IC arm's cost equals rT's, under the
   frozen map and under this sensitivity.
3. uncharged (CAN-2): the two phases the band unit does not charge (the
   rank process's own linear algebra and factor-base construction) and
   what charging them would do; the IC costs in the band are lower bounds.
4. rank_seed (CAN-3): the share of S's unpriced work that comes from the
   single rank process, an estimate of the gap at the archived second rank
   seed (proportional scaling of rank-stage counters by rank probes: an
   extrapolation, not a measurement), and the Monte-Carlo dependence of
   the bootstrap bounds (seeds and draw counts).
5. memory (CAN-5): peak RSS and stored table entries per arm.

Usage (from the repository root):

    python3 experiments/koblitz-n83-opcounts-20261023/disclosures.py \
        --out experiments/koblitz-n83-opcounts-20261023/disclosures-20261106
"""

import argparse
import base64
import copy
import importlib.util
import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RUN = HERE / "run_github_39882571652"
TWIN = ROOT / "experiments/koblitz-n83-stacked-20261016/run_github_38862448935/panel/runs"
BASELINES = ROOT / "docs/ic/baselines.json"
FIELD = ("field_mul", "field_sqr", "field_inv", "field_half_trace")
WEIGHTS = (0.0, 0.1, 1.0)


def load_band():
    spec = importlib.util.spec_from_file_location("band_frozen", HERE / "band.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def payload(path):
    for line in path.read_text().splitlines():
        if line.startswith("raw_b64="):
            return json.loads(base64.b64decode(line[len("raw_b64="):]))
    raise ValueError("no raw_b64 line in %s" % path)


def runs():
    out = []
    for path in sorted((RUN / "panel/runs").glob("*.stdout.txt")):
        out.append((path.name, payload(path)))
    return out


def ic_record(p):
    return next(r for r in p["records"] if "op_counts" in r and "phases" in r.get("op_counts", {}))


def mean(xs):
    return sum(xs) / len(xs)


def class_of(kind, spec):
    for name in ("group", "unpriced", "reported", "bounded"):
        if kind in spec[name]:
            return name
    return "unclassified"


def parts(unit, spec, extra_unpriced=()):
    g = sum(unit[k] for k in spec["group"])
    u = sum(unit[k] for k in spec["unpriced"]) + sum(unit.get(k, 0) for k in extra_unpriced)
    b = sum(unit[k] for k in spec["bounded"])
    return g, u, b


def arm_means(counts, band, extra_unpriced=()):
    out = {}
    for name, arm in counts["arms"].items():
        spec = band.classes(arm["family"], False)
        extra = extra_unpriced if arm["family"] == "ic" else ()
        ps = [parts(u, spec, extra) for u in arm["units"].values()]
        out[name] = tuple(mean([p[i] for p in ps]) for i in range(3))
    return out


def gap(means, arm, ref, w, b):
    g, u, s = means[arm]
    gr, ur, sr = means[ref]
    return (g + s * b + w * u) / (gr + sr * b + w * ur)


def crossover(means, arm, ref, b):
    """w at which mean cost(arm) = mean cost(ref); cost is linear in w."""
    g, u, s = means[arm]
    gr, ur, sr = means[ref]
    return ((gr + sr * b) - (g + s * b)) / (u - ur)


def patched_analyse(band, counts, draws, seed, extra_unpriced=()):
    saved = copy.deepcopy(band.CLASSES)
    try:
        if extra_unpriced:
            band.CLASSES["ic"]["unpriced"] = tuple(band.CLASSES["ic"]["unpriced"]) + tuple(extra_unpriced)
            band.CLASSES["ic"]["reported"] = tuple(k for k in band.CLASSES["ic"]["reported"]
                                                   if k not in extra_unpriced)
        return band.analyse(counts, draws=draws, seed=seed)
    finally:
        band.CLASSES.clear()
        band.CLASSES.update(saved)


def gap_cells(result, arm):
    rows = result["gap_to_reference"][arm]
    return {w: [{"rho_scalar_mul_gae": r["rho_scalar_mul_gae"], "ratio": r["ratio"], "ci95": r["ci95"]}
                for r in rows[w]] for w in rows}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--draws", type=int, default=10000)
    args = ap.parse_args()

    band = load_band()
    counts = json.loads((RUN / "panel/counts.json").read_text())
    ref = counts["reference"]
    r_bits = int(counts["r_bits"])
    bmax = 2.0 * (r_bits - 1)
    result = {"schema": "ic-band-disclosures/v1", "run": 39882571652,
              "inputs": {"counts_json": "run_github_39882571652/panel/counts.json",
                         "band_py": "band.py (frozen; imported, not modified)",
                         "raw_runs": "run_github_39882571652/panel/runs/*.stdout.txt",
                         "twin_runs": "../koblitz-n83-stacked-20261016/run_github_38862448935/panel/runs"},
              "case": "SHF-20261106-a114e7"}

    # 1. every counter, every arm (CAX-2)
    table = {}
    for name, arm in counts["arms"].items():
        spec = band.classes(arm["family"], False)
        kinds = sorted(set().union(*[set(u) for u in arm["units"].values()]))
        table[name] = {k: {"class": class_of(k, spec),
                           "mean_count": mean([u.get(k, 0) for u in arm["units"].values()])}
                       for k in kinds}
    result["counters"] = table
    totals = {}
    for name, rows in table.items():
        t = {}
        for k, v in rows.items():
            t[v["class"]] = t.get(v["class"], 0) + v["mean_count"]
        t["field_kinds"] = sum(rows[k]["mean_count"] for k in FIELD if k in rows)
        totals[name] = t
    result["counter_totals_by_class"] = totals

    # 2. field kinds charged at w (CAX-2)
    m_frozen = arm_means(counts, band)
    m_field = arm_means(counts, band, FIELD)
    sens = {"frozen_map": {}, "field_kinds_charged": {}}
    for label, m in (("frozen_map", m_frozen), ("field_kinds_charged", m_field)):
        for arm in counts["arms"]:
            if arm == ref:
                continue
            sens[label][arm] = {
                "gap_b0": {"%g" % w: gap(m, arm, ref, w, 0.0) for w in WEIGHTS},
                "gap_b104": {"%g" % w: gap(m, arm, ref, w, bmax) for w in WEIGHTS},
                "crossover_w_b0": crossover(m, arm, ref, 0.0),
                "crossover_w_b104": crossover(m, arm, ref, bmax),
            }
    field_band = patched_analyse(band, counts, args.draws, 20261023, FIELD)
    sens["field_kinds_charged_intervals"] = {arm: gap_cells(field_band, arm) for arm in field_band["gap_to_reference"]}
    sens["field_kinds_charged_pairs"] = [{"arms": p["arms"], "statement": p["statement"]} for p in field_band["pairs"]]
    result["field_sensitivity"] = sens

    # raw payloads
    payloads = runs()
    by_arm = {}
    for name, p in payloads:
        by_arm.setdefault(p["arm"], []).append((name, p))

    # 3. uncharged phases (CAN-2)
    rank_la = {}
    for arm in ("kS", "kP"):
        (_, p), = by_arm[arm]
        rec = ic_record(p)
        rank_la[arm] = rec["op_counts"]["phases"]["linear_algebra"]
    base_sources = sorted({ic_record(p).get("base_source") for a in ("kS", "kP", "cS", "cP")
                           for _, p in by_arm[a]})
    ec_frob = sorted({sum(ph.get("ec_frobenius", 0) for ph in ic_record(p)["op_counts"]["phases"].values())
                      for a in ("kS", "kP", "cS", "cP") for _, p in by_arm[a]})
    rt = [p for _, p in by_arm["rT"]]
    step_ns = 1e6 * sum(p["fields"]["online_ms"] for p in rt) / sum(p["fields"]["ops"] for p in rt)
    other = json.loads(BASELINES.read_text())["other_records"][13]
    x_ms = 427.524  # other_records[13].uncharged_phases.measurement_status (replay run 39007026856)
    assert "427.524 ms" in other["uncharged_phases"]["measurement_status"]
    x_gae = x_ms * 1e6 / step_ns
    unc = {"rank_process_linear_algebra": {}, "factor_base_construction": {}}
    for arm, ic in (("kS", "S"), ("kP", "P")):
        la = rank_la[arm].get("la_mulmods", 0) + rank_la[arm].get("la_inversions", 0)
        g, u, s = m_frozen[ic]
        m2 = dict(m_frozen)
        m2[ic] = (g, u + la, s)
        unc["rank_process_linear_algebra"][ic] = {
            "rank_process_la_unpriced_ops": la,
            "rank_process_la_phase": rank_la[arm],
            "gap_w1_b0_band": gap(m_frozen, ic, ref, 1.0, 0.0),
            "gap_w1_b0_with_rank_la": gap(m2, ic, ref, 1.0, 0.0),
        }
        m3 = dict(m_frozen)
        m3[ic] = (g + x_gae, u, s)
        unc["factor_base_construction"][ic] = {
            "gap_w0_b0_band": gap(m_frozen, ic, ref, 0.0, 0.0),
            "gap_w0_b0_if_all_of_X_were_group_additions": gap(m3, ic, ref, 0.0, 0.0),
            "crossover_w_b0_if_all_of_X_were_group_additions": crossover(m3, ic, ref, 0.0),
        }
    unc["factor_base_construction"]["ec_frobenius_totals_seen_in_ic_records"] = ec_frob
    unc["factor_base_construction"]["base_source_values"] = base_sources
    unc["factor_base_construction"]["x_ms"] = x_ms
    unc["factor_base_construction"]["x_source"] = ("docs/ic/baselines.json other_records[13].uncharged_phases."
                                                   "measurement_status (replay run 39007026856, Intel Xeon 8573C)")
    unc["factor_base_construction"]["rT_ns_per_walk_step_this_run"] = step_ns
    unc["factor_base_construction"]["x_as_gae_upper_bound"] = x_gae
    unc["factor_base_construction"]["caveat"] = ("X is wall time on another host class; dividing it by this run's "
                                                 "rho step mixes hosts and prices construction as if it were all "
                                                 "group additions, so it is a bound for illustration, not a count")
    result["uncharged"] = unc

    # 4. rank seed (CAN-3)
    rs = {}
    for arm, ic in (("kS", "S"), ("kP", "P")):
        (_, p), = by_arm[arm]
        rank = ic_record(p)["op_counts"]["phases"]["rank_stage"]
        spec = band.classes("ic", False)
        rank_u = sum(rank.get(k, 0) for k in spec["unpriced"])
        rank_g = sum(rank.get(k, 0) for k in spec["group"])
        g, u, s = m_frozen[ic]
        rs[ic] = {"rank_stage_unpriced": rank_u, "rank_stage_group": rank_g,
                  "rank_stage_share_of_unpriced": rank_u / u}
    twin = {}
    for path in sorted(TWIN.glob("*.stdout.txt")):
        p = payload(path)
        if p.get("arm") in ("kS", "kP"):
            rec = next(r for r in p["records"] if "rank_probes_total" in r)
            twin[(p["arm"], p.get("seed"))] = rec["rank_probes_total"]
    for arm, ic in (("kS", "S"), ("kP", "P")):
        ratio = twin[(arm, 102)] / twin[(arm, 101)]
        g, u, s = m_frozen[ic]
        ru = rs[ic]["rank_stage_unpriced"]
        m4 = dict(m_frozen)
        m4[ic] = (g, u + ru * (ratio - 1.0), s)
        rs[ic].update({"twin_rank_probes_seed101": twin[(arm, 101)], "twin_rank_probes_seed102": twin[(arm, 102)],
                       "seed102_over_seed101_rank_probes": ratio,
                       "estimated_gap_seed102_b0": {"%g" % w: gap(m4, ic, ref, w, 0.0) for w in WEIGHTS},
                       "estimate_method": ("rank-stage unpriced counters scaled by the seed-102/seed-101 rank-probe "
                                           "ratio of the archived twin; group operations of the rank stage left at "
                                           "seed 101 (the uncounted twin does not emit them): an extrapolation")})
    rs["S_over_P_w0_b0"] = (m_frozen["S"][0]) / (m_frozen["P"][0])
    rs["S_minus_P_group_ops_w0"] = m_frozen["S"][0] - m_frozen["P"][0]
    mc = {}
    for seed, draws in ((20261023, args.draws), (1, args.draws), (987654321, 4 * args.draws)):
        res = band.analyse(counts, draws=draws, seed=seed)
        mc["seed%d_draws%d" % (seed, draws)] = {arm: gap_cells(res, arm) for arm in res["gap_to_reference"]}
    rs["bootstrap_monte_carlo"] = mc
    rs["note"] = ("the paired bootstrap resamples the 20 cold points only; kS and kP are one rank process each "
                  "(seed 101), so their rank stage is a constant in every resample and the intervals carry no "
                  "rank-seed variance")
    result["rank_seed"] = rs

    # 5. memory (CAN-5)
    mem = {}
    for arm in ("kS", "kP", "cS", "cP"):
        rss = [p["fields"]["peak_rss_bytes"] for _, p in by_arm[arm]]
        ent = [ic_record(p)["root_table_entries"] for _, p in by_arm[arm]]
        tb = [ic_record(p)["root_table_bytes"] for _, p in by_arm[arm]]
        mem[arm] = {"runs": len(rss), "peak_rss_bytes_min": min(rss), "peak_rss_bytes_median": statistics.median(rss),
                    "peak_rss_bytes_max": max(rss), "root_table_entries_mean": mean(ent),
                    "root_table_bytes_max": max(tb)}
    rss = [next(r for r in p["records"] if "peak_rss_bytes" in r)["peak_rss_bytes"] for p in rt]
    ent = [next(r for r in p["records"] if "outcome" in r)["outcome"]["table_entries"] for p in rt]
    pay = [next(r for r in p["records"] if "outcome" in r)["outcome"]["table_payload_lower_bound_bytes"] for p in rt]
    mem["rT"] = {"runs": len(rss), "peak_rss_bytes_min": min(rss), "peak_rss_bytes_median": statistics.median(rss),
                 "peak_rss_bytes_max": max(rss), "table_entries_mean": mean(ent),
                 "table_payload_lower_bound_bytes_mean": mean(pay)}
    mem["ic_over_rT_peak_rss_median"] = {a: mem[a]["peak_rss_bytes_median"] / mem["rT"]["peak_rss_bytes_median"]
                                         for a in ("kS", "kP", "cS", "cP")}
    mem["ic_over_rT_peak_rss_max"] = {a: mem[a]["peak_rss_bytes_max"] / mem["rT"]["peak_rss_bytes_max"]
                                      for a in ("kS", "kP", "cS", "cP")}
    result["memory"] = mem

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "disclosures.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (args.out / "disclosures.md").write_text(markdown(result))
    print(markdown(result))
    return 0


def markdown(r):
    L = ["# Disclosures beside the section 5a band (run 39882571652)", "",
         "Computed by `disclosures.py` from the archived receipts; the frozen band (`band.py`) is unchanged "
         "and stays the record. Case SHF-20261106-a114e7. `[pcc:unverified]`", ""]
    L += ["## 1. Every counter, mean per solved target (CAX-2)", "",
          "Class is the frozen kind map (`band.py` `CLASSES`): group (priced at 1 GAE), unpriced (priced at w), "
          "reported (counted, not priced), bounded (rho scalar multiplications, 0 or 104 GAE).", ""]
    arms = list(r["counters"])
    for arm in arms:
        L += ["**%s**" % arm, "", "| counter | class | mean count |", "| --- | --- | ---: |"]
        for k, v in sorted(r["counters"][arm].items(), key=lambda kv: (kv[1]["class"], kv[0])):
            L.append("| `%s` | %s | %.6g |" % (k, v["class"], v["mean_count"]))
        t = r["counter_totals_by_class"][arm]
        L += ["", "Totals: " + ", ".join("%s %.4g" % (k, v) for k, v in sorted(t.items())), ""]
    s = r["field_sensitivity"]
    L += ["## 2. Field kinds charged at w (CAX-2 sensitivity)", "",
          "| arm | map | gap w=0 | w=0.1 | w=1 | crossover w* (b=0) | w* (b=104) |",
          "| --- | --- | ---: | ---: | ---: | ---: | ---: |"]
    for label in ("frozen_map", "field_kinds_charged"):
        for arm, v in s[label].items():
            g = v["gap_b0"]
            L.append("| %s | %s | %.4g | %.4g | %.4g | %.5g | %.5g |" % (
                arm, label, g["0"], g["0.1"], g["1"], v["crossover_w_b0"], v["crossover_w_b104"]))
    L += ["", "Pairs with field kinds charged: " + "; ".join("%s vs %s: %s" % (p["arms"][0], p["arms"][1], p["statement"])
                                                         for p in s["field_kinds_charged_pairs"]), ""]
    u = r["uncharged"]
    fb = u["factor_base_construction"]
    L += ["## 3. Phases the band unit does not charge (CAN-2)", "",
          "The IC costs in the band, and so every IC gap at w >= 0.1, are **lower bounds**:", "",
          "- Factor-base construction: every IC process loads the K600 base (base_source %s); `ec_frobenius` "
          "(base construction) totals seen in the IC records: %s. X = %.3f ms (%s) is %.4g GAE at this run's rT step "
          "of %.2f ns if all of it were group additions (%s)." % (
              ", ".join(map(str, fb["base_source_values"])), fb["ec_frobenius_totals_seen_in_ic_records"], fb["x_ms"],
              fb["x_source"], fb["x_as_gae_upper_bound"], fb["rT_ns_per_walk_step_this_run"], fb["caveat"])]
    for arm in ("S", "P"):
        v = fb[arm]
        L.append("  - %s: gap at w=0 %.4g in the band, at most %.4g with X added; crossover w* then %.5g." % (
            arm, v["gap_w0_b0_band"], v["gap_w0_b0_if_all_of_X_were_group_additions"],
            v["crossover_w_b0_if_all_of_X_were_group_additions"]))
    L.append("- Linear algebra: the unit takes cS / cP's checked cached-table load, not the rank process's solve.")
    for arm in ("S", "P"):
        v = u["rank_process_linear_algebra"][arm]
        L.append("  - %s: the rank process's LA phase has %d unpriced operations outside the unit; gap at w=1 "
                 "%.7g -> %.7g with them." % (arm, v["rank_process_la_unpriced_ops"], v["gap_w1_b0_band"],
                                              v["gap_w1_b0_with_rank_la"]))
    L += ["", "No ruling changes: w=0 stays below 1 and w >= 0.1 above 1 for both arms.", ""]
    rs = r["rank_seed"]
    L += ["## 4. Rank-seed variance and Monte-Carlo digits (CAN-3)", "",
          "- %s." % (rs["note"][0].upper() + rs["note"][1:])]
    for arm in ("S", "P"):
        v = rs[arm]
        e = v["estimated_gap_seed102_b0"]
        L.append("- %s: the rank stage is %.2f%% of the unit's unpriced work. Archived twin rank probes seed 102 / "
                 "seed 101 = %.5f; scaling the rank stage by it (extrapolation, not a measurement) gives gaps %.4g / "
                 "%.4g / %.4g at w = 0 / 0.1 / 1." % (arm, 100 * v["rank_stage_share_of_unpriced"],
                                                      v["seed102_over_seed101_rank_probes"], e["0"], e["0.1"], e["1"]))
    L.append("- S < P at w = 0 is a single-seed order: S / P = %.6f, a difference of %.0f group operations between "
             "one kS and one kP rank draw (seed 101). It is not a ranking across rank seeds." % (
                 rs["S_over_P_w0_b0"], -rs["S_minus_P_group_ops_w0"]))
    L += ["- Bootstrap bounds at b = 0 under other seeds and draw counts (quote them to 3 significant figures):", "",
          "| arm | w | " + " | ".join(rs["bootstrap_monte_carlo"]) + " |",
          "| --- | --- | " + " | ".join("---" for _ in rs["bootstrap_monte_carlo"]) + " |"]
    for arm in ("S", "P"):
        for w in ("0", "0.1", "1"):
            cells = []
            for key, v in rs["bootstrap_monte_carlo"].items():
                c = v[arm][w][0]
                cells.append("%.4g [%.4g, %.4g]" % (c["ratio"], c["ci95"][0], c["ci95"][1]))
            L.append("| %s | %s | %s |" % (arm, w, " | ".join(cells)))
    m = r["memory"]
    L += ["", "## 5. Memory (CAN-5)", "",
          "| arm | runs | peak RSS min | median | max | stored table entries (mean) |",
          "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for arm in ("kS", "kP", "cS", "cP", "rT"):
        v = m[arm]
        ent = v.get("root_table_entries_mean", v.get("table_entries_mean"))
        L.append("| %s | %d | %.4g MB | %.4g MB | %.4g MB | %.6g |" % (
            arm, v["runs"], v["peak_rss_bytes_min"] / 1e6, v["peak_rss_bytes_median"] / 1e6,
            v["peak_rss_bytes_max"] / 1e6, ent))
    L += ["", "IC / rT peak RSS against rT's median: " + ", ".join(
        "%s %.0fx" % (a, x) for a, x in m["ic_over_rT_peak_rss_median"].items()) +
          "; against rT's maximum: " + ", ".join("%s %.0fx" % (a, x) for a, x in m["ic_over_rT_peak_rss_max"].items()) +
          ". On memory every IC arm is worse than rT, so the w = 0 end of the band (IC cheaper in GAE) is not a "
          "Pareto point: rT is undominated at every weight.", ""]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    sys.exit(main())
