#!/usr/bin/env python3
"""Render REPORT.pdf from results/summary.json with reportlab (no LaTeX here).
Every number is read from summary.json; the figures are redrawn natively."""
import json
import os
import sys

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.graphics.shapes import Drawing, Line, Rect, String, Circle

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
S = json.load(open(os.path.join(ROOT, "results", "summary.json")))
CLASSES = ["zero", "one", "ones", "topbit", "alt", "lowhw", "highhw", "random_a", "random_b", "fixed_a", "fixed_b"]


def repro_drawing(arm, d):
    Ns, opts, cell = [14, 15, 16, 18, 19], [3, 2, 1, 0], 11 * mm
    W, H = 150 * mm, 4 * cell + 14 * mm
    g = Drawing(W, H)
    by = {(r["N"], r["opt"]): r["exit"] for r in d["repro_rows"] if r["variant"] == "karatsuba" and r["codegen"] == "sass"}
    L = 32 * mm
    for i, o in enumerate(opts):
        y = H - 10 * mm - (i + 1) * cell
        g.add(String(L - 2 * mm, y + cell / 2 - 1.5 * mm, f"-Xptxas -O{o}", fontSize=8, textAnchor="end"))
        for j, n in enumerate(Ns):
            e = by.get((n, o), "?")
            col = {"0": colors.HexColor("#2ca02c"), "1": colors.HexColor("#d62728"), "2": colors.HexColor("#ff7f0e")}.get(e, colors.grey)
            g.add(Rect(L + j * cell, y, cell - 1, cell - 1, fillColor=col, strokeColor=None))
            g.add(String(L + j * cell + cell / 2 - 1.5 * mm, y + cell / 2 - 1.5 * mm, e, fontSize=9, fillColor=colors.white))
            if i == len(opts) - 1:
                g.add(String(L + j * cell + 2 * mm, y - 4 * mm, f"N={n}", fontSize=8))
    g.add(String(0, H - 5 * mm, f"{arm}: repro.cu exit by N and ptxas level (0 match, 1 mismatch, 2 CUDA error)", fontSize=9))
    return g


def timing_drawing(arm, d, mode):
    st = d["timing"]["latency"].get(mode, {}).get("classes", {})
    if not st:
        return Spacer(1, 1)
    W, H = 160 * mm, 48 * mm
    g = Drawing(W, H)
    vals = [v for c in CLASSES if c in st for v in (st[c]["min"], st[c]["max"])]
    lo, hi = min(vals), max(vals)
    if hi == lo:
        hi = lo + 0.01
    pad = (hi - lo) * 0.1
    lo, hi = lo - pad, hi + pad
    L, R = 20 * mm, 5 * mm

    def X(v):
        return L + (v - lo) / (hi - lo) * (W - L - R)
    g.add(Line(L, 6 * mm, W - R, 6 * mm, strokeColor=colors.grey))
    for i in range(5):
        v = lo + (hi - lo) * i / 4
        g.add(String(X(v) - 4 * mm, 2 * mm, f"{v:.3f}", fontSize=6))
    for ci, c in enumerate(CLASSES):
        if c not in st:
            continue
        y = 9 * mm + ci * 3.4 * mm
        g.add(String(0, y - 1 * mm, c, fontSize=6))
        g.add(Line(X(st[c]["min"]), y, X(st[c]["max"]), y, strokeColor=colors.HexColor("#1f77b4")))
        g.add(Circle(X(st[c]["median"]), y, 1.1 * mm, fillColor=colors.HexColor("#1f77b4"), strokeColor=None))
        t = st[c]["t_vs_fixed_a"]
        g.add(String(W - R - 10 * mm, y - 1 * mm, f"t={t:+.1f}", fontSize=6,
                     fillColor=colors.red if abs(t) > S["t_threshold"] and c != "fixed_a" else colors.black))
    g.add(String(0, H - 4 * mm, f"{arm} / {mode}: cycles per operation, min to max over launches, dot = median (latency geometry)", fontSize=7))
    return g


def main():
    out = os.path.join(ROOT, "REPORT.pdf")
    doc = SimpleDocTemplate(out, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=16 * mm)
    ss = getSampleStyleSheet()
    body = ss["BodyText"]
    body.fontSize = 9
    body.leading = 12
    F = []
    F.append(Paragraph("clmad audit on sm_120: miscompile reproduction, ecc2k130 tests, two-class timing", ss["Title"]))
    F.append(Paragraph("research/clmad_audit_20261110 · protocol frozen before data · every number from results/summary.json · claims [pcc:unverified] until the benchmark record is closed and validated", body))
    F.append(Spacer(1, 4 * mm))
    rows = [["arm", "GPU", "driver", "nvcc", "pod", "run exit", "Q1", "Q2 host / device", "Q3 latency / occupancy"]]
    for arm, d in S["arms"].items():
        e = d["env"]
        rows.append([arm, f"{e.get('gpu', '?')}\ncc {e.get('compute_cap', '?')}", f"{e.get('driver', '?')}\nCUDA {e.get('driver_cuda', '?')}", e.get("nvcc", "?"),
                     d["pod"]["id"], str(d["pod"]["run_exit"]), d["q1"]["verdict"],
                     f"{d['q2']['host_tests_exit']} / {d['q2']['test_packed_cuda_exit']}",
                     f"{d['q3']['latency']['verdict']}\n{d['q3']['occupancy']['verdict']}"])
    t = Table(rows, repeatRows=1)
    t.setStyle(TableStyle([("FONTSIZE", (0, 0), (-1, -1), 6.5), ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                           ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeeee")), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    F.append(t)
    F.append(Spacer(1, 4 * mm))
    for arm, d in S["arms"].items():
        if d["repro_rows"]:
            F.append(repro_drawing(arm, d))
            F.append(Paragraph(f"{arm}: Q1 {d['q1']['verdict']} {d['q1']['detail']}; controls {d['q1']['controls']}. "
                               f"SASS CLMAD counts per binary: " + ", ".join(f"{r['binary']}={r['clmad_sass']}" for r in d["repro_rows"] if r["codegen"] == "sass"), body))
            F.append(Spacer(1, 3 * mm))
    F.append(PageBreak())
    for arm, d in S["arms"].items():
        if not d["timing"]["latency"]:
            continue
        F.append(Paragraph(f"{arm}: timing. Positive control t = {d['q3']['latency']['detail'].get('positive_control_t', float('nan')):.0f}; "
                           f"negative control max |t| = {d['q3']['latency']['detail'].get('negative_control_max_abs_t', float('nan')):.2f}; threshold {S['t_threshold']}.", body))
        for mode in ("lo", "hi", "neg", "pos"):
            F.append(timing_drawing(arm, d, mode))
        for geom in ("latency", "occupancy"):
            ts = d["timing"][geom]
            rows = [["mode", "class", "n", "median c/op", "min", "max", "sd", "t vs fixed_a"]]
            for mode in ("lo", "hi", "neg", "pos"):
                if mode not in ts:
                    continue
                for c in CLASSES:
                    if c in ts[mode]["classes"]:
                        s = ts[mode]["classes"][c]
                        rows.append([mode, c, s["n"], f"{s['median']:.3f}", f"{s['min']:.3f}", f"{s['max']:.3f}", f"{s['sd']:.4f}", f"{s['t_vs_fixed_a']:+.2f}"])
                rows.append([mode, "A/A random_a~random_b", "", f"t {ts[mode]['t_aa_random']:+.2f}", "", "fixed pair", f"t {ts[mode]['t_fixed_pair']:+.2f}", f"low~high t {ts[mode]['t_lowhw_highhw']:+.1f}"])
            tt = Table(rows, repeatRows=1)
            tt.setStyle(TableStyle([("FONTSIZE", (0, 0), (-1, -1), 6), ("GRID", (0, 0), (-1, -1), 0.2, colors.lightgrey),
                                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeeee"))]))
            F.append(Paragraph(f"{arm} / {geom} geometry ({d['timing_meta'][geom]})", body))
            F.append(tt)
            F.append(Spacer(1, 3 * mm))
        F.append(PageBreak())
    doc.build(F)
    print(out)


if __name__ == "__main__":
    sys.exit(main())
