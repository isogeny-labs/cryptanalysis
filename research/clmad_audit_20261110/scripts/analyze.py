#!/usr/bin/env python3
"""Apply PROTOCOL.md's decision rules to the fetched results of every arm.

Reads research/clmad_audit_20261110/results/<arm>/results/ (unpacked
results.tar.xz) and writes results/summary.json, results/fig_timing.svg,
results/fig_repro.svg and REPORT.md.  Standard library only; every number in
the report comes from the raw files named here.
"""
import json
import math
import os
import re
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
RES = os.path.join(ROOT, "results")
T_THRESHOLD = 4.5
CLASSES = ["zero", "one", "ones", "topbit", "alt", "lowhw", "highhw", "random_a", "random_b",
           "fixed_a", "fixed_b"]
MODES = ["lo", "hi", "neg", "pos"]


def welch_t(x, y):
    if len(x) < 2 or len(y) < 2:
        return float("nan")
    mx, my = statistics.fmean(x), statistics.fmean(y)
    vx, vy = statistics.variance(x), statistics.variance(y)
    d = math.sqrt(vx / len(x) + vy / len(y))
    if d == 0:
        return 0.0 if mx == my else float("inf")
    return (mx - my) / d


def read_env(path):
    env = {"raw": ""}
    try:
        env["raw"] = open(path, errors="replace").read()
    except OSError:
        return env
    m = re.search(r"release ([0-9.]+), V([0-9.]+)", env["raw"])
    if m:
        env["nvcc"] = m.group(2)
    m = re.search(r"Driver Version: ([0-9.]+)", env["raw"])
    if m:
        env["driver"] = m.group(1)
    m = re.search(r"CUDA Version: ([0-9.]+)", env["raw"])
    if m:
        env["driver_cuda"] = m.group(1)
    m = re.search(r"^(NVIDIA [^,\n]+), ([0-9a-fA-F-]{20,}), ([0-9.]+), ([0-9.]+)", env["raw"], re.M)
    if m:
        env["gpu"] = m.group(1)
        env["compute_cap"] = m.group(4)
    return env


def read_repro(path):
    rows = []
    try:
        lines = open(path).read().splitlines()
    except OSError:
        return rows
    for ln in lines[1:]:
        f = ln.split("\t")
        if len(f) < 8:
            continue
        rows.append({"binary": f[0], "N": int(f[1]), "opt": int(f[2]), "codegen": f[3],
                     "variant": f[4], "exit": f[5], "clmad_sass": f[6], "first_line": f[7]})
    return rows


def q1_verdict(rows):
    kar = [r for r in rows if r["variant"] == "karatsuba" and r["codegen"] == "sass"]
    by = {(r["N"], r["opt"]): r["exit"] for r in kar}
    reproduced = []
    for n in sorted({r["N"] for r in kar}):
        hi_bad = any(by.get((n, o)) == "1" for o in (3, 2))
        lo_ok = all(by.get((n, o)) == "0" for o in (1, 0) if (n, o) in by)
        if hi_bad and lo_ok:
            reproduced.append(n)
    exits = {r["exit"] for r in kar}
    if reproduced:
        return "reproduced", reproduced
    if exits == {"0"}:
        return "not reproduced", []
    return "other pattern", sorted(exits)


def read_timing(path):
    meta, rows = None, []
    try:
        for ln in open(path):
            d = json.loads(ln)
            if "meta" in d:
                meta = d["meta"]
            else:
                rows.append(d)
    except OSError:
        pass
    return meta, rows


def timing_stats(meta, rows):
    """Per (mode, class): per-launch median cycles per op, Welch t vs fixed_a."""
    out = {}
    if not meta:
        return out
    chain = meta["chain"]
    for mode in MODES:
        per = {}
        for r in rows:
            if r["mode"] != mode:
                continue
            ops = r["ops"] if r["ops"] else chain  # pos: normalise by the nominal chain
            per.setdefault(r["class"], []).append(r["median"] / ops)
        if not per:
            continue
        ref = per.get("fixed_a", [])
        cls = {}
        for c in CLASSES:
            v = per.get(c, [])
            if not v:
                continue
            cls[c] = {"n": len(v), "median": statistics.median(v), "mean": statistics.fmean(v),
                      "min": min(v), "max": max(v),
                      "sd": statistics.pstdev(v) if len(v) > 1 else 0.0,
                      "t_vs_fixed_a": welch_t(v, ref) if c != "fixed_a" else 0.0}
        aa = welch_t(per.get("random_a", []), per.get("random_b", []))
        ff = welch_t(per.get("fixed_a", []), per.get("fixed_b", []))
        lh = welch_t(per.get("lowhw", []), per.get("highhw", []))
        out[mode] = {"classes": cls, "t_aa_random": aa, "t_fixed_pair": ff, "t_lowhw_highhw": lh}
    return out


def q3_verdict(ts):
    if "pos" not in ts or "neg" not in ts:
        return "no data", {}
    pos_ok = abs(ts["pos"]["t_lowhw_highhw"]) > T_THRESHOLD
    neg_max = max([abs(c["t_vs_fixed_a"]) for c in ts["neg"]["classes"].values()] +
                  [abs(ts["neg"]["t_aa_random"]), abs(ts["neg"]["t_fixed_pair"])])
    neg_ok = neg_max <= T_THRESHOLD
    detail = {"positive_control_t": ts["pos"]["t_lowhw_highhw"], "negative_control_max_abs_t": neg_max}
    if not (pos_ok and neg_ok):
        return "instrument invalid", detail
    flagged = {}
    for mode in ("lo", "hi"):
        if mode not in ts:
            continue
        f = [c for c, s in ts[mode]["classes"].items() if abs(s["t_vs_fixed_a"]) > T_THRESHOLD]
        if abs(ts[mode]["t_aa_random"]) > T_THRESHOLD:
            f.append("random_a~random_b(A/A)")
        if abs(ts[mode]["t_fixed_pair"]) > T_THRESHOLD:
            f.append("fixed_a~fixed_b")
        flagged[mode] = f
    verdict = "no class distinguishable" if not any(flagged.values()) else "distinguishable"
    detail["flagged"] = flagged
    return verdict, detail


def make_exit(path, key):
    try:
        txt = open(path, errors="replace").read()
    except OSError:
        return None
    m = re.search(key + r"=(\d+)", txt)
    return int(m.group(1)) if m else None


def svg_timing(arms, path):
    """Strip chart: per-launch median cycles/op by class, one panel per arm x mode (lo, hi)."""
    panels = [(arm, mode) for arm in arms for mode in ("lo", "hi", "neg", "pos") if mode in arms[arm]["timing"]["latency"]]
    W, PH, L, R = 1100, 150, 90, 20
    H = 40 + PH * max(1, len(panels))
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="Helvetica,Arial" font-size="11">',
         f'<rect width="{W}" height="{H}" fill="white"/>',
         f'<text x="{L}" y="18" font-size="14">clmad dependent-chain latency on sm_120: per-launch median cycles per operation by operand class (latency geometry, 1 block x 32 threads)</text>']
    y0 = 30
    for arm, mode in panels:
        st = arms[arm]["timing"]["latency"][mode]["classes"]
        vals = [v for c in CLASSES if c in st for v in arms[arm]["timing"]["latency_raw"][mode].get(c, [])]
        if not vals:
            continue
        lo, hi = min(vals), max(vals)
        if hi == lo:
            hi = lo + 1
        pad = (hi - lo) * 0.08
        lo, hi = lo - pad, hi + pad
        px = W - L - R
        cw = px / len(CLASSES)

        def X(v):
            return L + (v - lo) / (hi - lo) * px
        s.append(f'<text x="4" y="{y0 + 14}" font-size="12">{arm} / {mode}</text>')
        s.append(f'<line x1="{L}" y1="{y0 + PH - 25}" x2="{W - R}" y2="{y0 + PH - 25}" stroke="#999"/>')
        for i in range(6):
            v = lo + (hi - lo) * i / 5
            s.append(f'<text x="{X(v):.1f}" y="{y0 + PH - 10}" text-anchor="middle" fill="#555">{v:.2f}</text>')
        for ci, c in enumerate(CLASSES):
            raw = arms[arm]["timing"]["latency_raw"][mode].get(c, [])
            if not raw:
                continue
            yy = y0 + 22 + ci * ((PH - 50) / len(CLASSES))
            s.append(f'<text x="{L - 6}" y="{yy + 4:.1f}" text-anchor="end" fill="#333">{c}</text>')
            for v in raw:
                s.append(f'<circle cx="{X(v):.1f}" cy="{yy:.1f}" r="2" fill="#1f77b4" fill-opacity="0.35"/>')
            med = st[c]["median"]
            t = st[c]["t_vs_fixed_a"]
            col = "#d62728" if abs(t) > T_THRESHOLD and c != "fixed_a" else "#222"
            s.append(f'<line x1="{X(med):.1f}" y1="{yy - 6:.1f}" x2="{X(med):.1f}" y2="{yy + 6:.1f}" stroke="{col}" stroke-width="2"/>')
            s.append(f'<text x="{W - R - 2}" y="{yy + 4:.1f}" text-anchor="end" fill="{col}">t={t:+.1f}</text>')
        y0 += PH
    s.append("</svg>")
    open(path, "w").write("\n".join(s))


def svg_repro(arms, path):
    Ns = [14, 15, 16, 18, 19]
    opts = [3, 2, 1, 0]
    cell, L, T = 44, 160, 50
    W = L + len(Ns) * cell + 40
    H = T + len(arms) * (len(opts) * cell + 30) + 20
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="Helvetica,Arial" font-size="11">',
         f'<rect width="{W}" height="{H}" fill="white"/>',
         '<text x="10" y="20" font-size="14">repro.cu exit code by chain length N and ptxas -O level (0 = all steps match, 1 = mismatch, 2 = CUDA error)</text>']
    y = T
    for arm, d in arms.items():
        s.append(f'<text x="10" y="{y - 8}" font-size="12">{arm}  (nvcc {d["env"].get("nvcc", "?")})</text>')
        by = {(r["N"], r["opt"]): r["exit"] for r in d["repro"] if r["variant"] == "karatsuba" and r["codegen"] == "sass"}
        for j, n in enumerate(Ns):
            s.append(f'<text x="{L + j * cell + cell / 2}" y="{y + len(opts) * cell + 14}" text-anchor="middle">N={n}</text>')
        for i, o in enumerate(opts):
            s.append(f'<text x="{L - 8}" y="{y + i * cell + cell / 2 + 4}" text-anchor="end">-Xptxas -O{o}</text>')
            for j, n in enumerate(Ns):
                e = by.get((n, o), "?")
                col = {"0": "#2ca02c", "1": "#d62728", "2": "#ff7f0e"}.get(e, "#bbb")
                s.append(f'<rect x="{L + j * cell}" y="{y + i * cell}" width="{cell - 2}" height="{cell - 2}" fill="{col}"/>')
                s.append(f'<text x="{L + j * cell + cell / 2 - 1}" y="{y + i * cell + cell / 2 + 4}" text-anchor="middle" fill="white" font-weight="bold">{e}</text>')
        y += len(opts) * cell + 30
    s.append("</svg>")
    open(path, "w").write("\n".join(s))


def main():
    arms = {}
    for arm in sorted(os.listdir(RES)):
        d = os.path.join(RES, arm, "results")
        if not os.path.isdir(d):
            continue
        env = read_env(os.path.join(d, "env.txt"))
        repro = read_repro(os.path.join(d, "repro_summary.tsv"))
        verdict, detail = q1_verdict(repro)
        extra = {r["variant"] + ("_ptxjit" if r["codegen"] == "ptx" else ""): r["exit"]
                 for r in repro if r["variant"] != "karatsuba" or r["codegen"] == "ptx"}
        timing = {}
        for geom in ("latency", "occupancy"):
            meta, rows = read_timing(os.path.join(d, f"timing_{geom}.jsonl"))
            timing[geom] = timing_stats(meta, rows)
            timing[geom + "_meta"] = meta
            raw = {}
            for r in rows:
                ops = r["ops"] if r["ops"] else (meta["chain"] if meta else 1)
                raw.setdefault(r["mode"], {}).setdefault(r["class"], []).append(r["median"] / ops)
            timing[geom + "_raw"] = raw
        q3 = {geom: q3_verdict(timing[geom]) for geom in ("latency", "occupancy")}
        alloc = {}
        try:
            alloc = json.load(open(os.path.join(RES, arm, "allocation.json")))
        except OSError:
            pass
        arms[arm] = {
            "env": {k: v for k, v in env.items() if k != "raw"},
            "pod": {"id": alloc.get("pod_id"), "gpu": (alloc.get("last_pod") or {}).get("gpu"),
                    "cost_per_hr": (alloc.get("created") or {}).get("costPerHr"), "wall_s": alloc.get("wall_s"),
                    "run_exit": alloc.get("run_exit")},
            "repro": repro,
            "q1": {"verdict": verdict, "detail": detail, "controls": extra},
            "q2": {"host_tests_exit": make_exit(os.path.join(d, "ecc2k130_host_tests.log"), "host_tests_exit"),
                   "test_packed_cuda_exit": make_exit(os.path.join(d, "ecc2k130_test_packed_cuda.log"), "test_packed_cuda_exit")},
            "timing": timing,
            "q3": {g: {"verdict": v, "detail": dd} for g, (v, dd) in q3.items()},
        }
    summary = {"schema": "clmad-audit-summary/v1", "t_threshold": T_THRESHOLD, "arms": {}}
    for arm, d in arms.items():
        s = {k: v for k, v in d.items() if k not in ("timing", "repro")}
        s["timing"] = {g: d["timing"][g] for g in ("latency", "occupancy")}
        s["timing_meta"] = {g: d["timing"][g + "_meta"] for g in ("latency", "occupancy")}
        s["repro_rows"] = d["repro"]
        summary["arms"][arm] = s
    json.dump(summary, open(os.path.join(RES, "summary.json"), "w"), indent=1, sort_keys=True)
    if arms:
        svg_timing(arms, os.path.join(RES, "fig_timing.svg"))
        svg_repro(arms, os.path.join(RES, "fig_repro.svg"))
    # REPORT.md
    L = ["# clmad audit on sm_120: results", "",
         "Decision rules: `PROTOCOL.md`. Numbers: `results/summary.json`. Raw: `results/<arm>/results/`.", ""]
    L += ["## Arms", "", "| arm | GPU | driver | nvcc | pod | run exit |", "|---|---|---|---|---|---|"]
    for arm, d in arms.items():
        e = d["env"]
        L.append(f"| {arm} | {e.get('gpu', '?')} (cc {e.get('compute_cap', '?')}) | {e.get('driver', '?')} (CUDA {e.get('driver_cuda', '?')}) | {e.get('nvcc', '?')} | {d['pod']['id']} | {d['pod']['run_exit']} |")
    L += ["", "## Q1: reproduction of the ptxas clmad folding defect", ""]
    for arm, d in arms.items():
        L.append(f"- **{arm}**: {d['q1']['verdict']} ({d['q1']['detail']}); controls: {d['q1']['controls']}")
    L += ["", "![repro](results/fig_repro.svg)", "", "| arm | binary | N | -O | codegen | variant | exit | CLMAD in SASS | first output line |", "|---|---|---|---|---|---|---|---|---|"]
    for arm, d in arms.items():
        for r in d["repro"]:
            L.append(f"| {arm} | {r['binary']} | {r['N']} | {r['opt']} | {r['codegen']} | {r['variant']} | {r['exit']} | {r['clmad_sass']} | {r['first_line'][:70]} |")
    L += ["", "## Q2: ecc2k130 tests", ""]
    for arm, d in arms.items():
        L.append(f"- **{arm}**: host clmad tests exit {d['q2']['host_tests_exit']}; test-packed-cuda exit {d['q2']['test_packed_cuda_exit']}")
    L += ["", "## Q3: two-class timing", ""]
    for arm, d in arms.items():
        for g in ("latency", "occupancy"):
            L.append(f"- **{arm} / {g}**: {d['q3'][g]['verdict']}; {d['q3'][g]['detail']}")
    L += ["", "![timing](results/fig_timing.svg)", ""]
    for arm, d in arms.items():
        for g in ("latency", "occupancy"):
            ts = d["timing"][g]
            if not ts:
                continue
            L += [f"### {arm} / {g}: cycles per operation (per-launch median over threads)", "",
                  "| mode | class | n | median | min | max | sd | t vs fixed_a |", "|---|---|---|---|---|---|---|---|"]
            for mode in MODES:
                if mode not in ts:
                    continue
                for c in CLASSES:
                    if c in ts[mode]["classes"]:
                        s = ts[mode]["classes"][c]
                        L.append(f"| {mode} | {c} | {s['n']} | {s['median']:.3f} | {s['min']:.3f} | {s['max']:.3f} | {s['sd']:.4f} | {s['t_vs_fixed_a']:+.2f} |")
                L.append(f"| {mode} | A/A random_a~random_b t | | {ts[mode]['t_aa_random']:+.2f} | | | | fixed_a~fixed_b t {ts[mode]['t_fixed_pair']:+.2f}; lowhw~highhw t {ts[mode]['t_lowhw_highhw']:+.2f} |")
            L.append("")
    open(os.path.join(ROOT, "REPORT.md"), "w").write("\n".join(L) + "\n")
    print(json.dumps({a: {"q1": d["q1"]["verdict"], "q2": d["q2"], "q3": {g: d["q3"][g]["verdict"] for g in d["q3"]}} for a, d in arms.items()}, indent=1))


if __name__ == "__main__":
    sys.exit(main())
