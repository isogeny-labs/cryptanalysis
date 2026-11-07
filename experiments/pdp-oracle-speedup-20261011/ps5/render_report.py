"""Render report/ps5_report.pdf from raw/ and figures/ (Typst source kept beside it).
Rendering only: every number in a table is read from raw/; the prose is fixed text.

    python3 render_report.py     (needs the `typst` and `pikepdf` Python packages)
"""
import glob
import json
import os
import re

import typst

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
OUT = os.path.join(HERE, "report")
os.makedirs(OUT, exist_ok=True)


def last_json(path):
    rows = [json.loads(x) for x in open(path).read().splitlines() if x.startswith("{")]
    return rows[-1] if rows else None


def fmt(n):
    return f"{n:,}"


ls = [8, 9, 10, 11, 12]
emit = {l: json.load(open(f"{RAW}/emit/emit_l{l}.json")) for l in ls}
par = {l: last_json(f"{RAW}/parity_l{l}.jsonl") for l in ls}
self_ = {l: last_json(f"{RAW}/selftest_l{l}.jsonl") for l in ls}
model = {l: last_json(f"{RAW}/parity_l{l}_model.jsonl") for l in ls if os.path.exists(f"{RAW}/parity_l{l}_model.jsonl")}
p13 = last_json(f"{RAW}/parity_l13.jsonl") if os.path.exists(f"{RAW}/parity_l13.jsonl") else None
s13 = last_json(f"{RAW}/selftest_l13.jsonl") if os.path.exists(f"{RAW}/selftest_l13.jsonl") else None
manifest = json.load(open(f"{RAW}/manifest.json"))


def cell(x):
    return "[" + str(x).replace("[", "\\[").replace("]", "\\]").replace("#", "\\#").replace("*", "\\*") + "]"


def table(cols, header, rows, widths=None):
    w = widths or ", ".join(["auto"] * cols)
    lines = [f"#table(columns: ({w}), inset: 4pt, stroke: 0.4pt + luma(160), align: (left,) + (right,) * {cols - 1},"]
    lines.append("  " + ", ".join(cell(h) for h in header) + ",")
    for r in rows:
        lines.append("  " + ", ".join(cell(c) for c in r) + ",")
    lines.append(")")
    return "\n".join(lines)


# parity table
par_rows = []
tot_pairs = 0
tot_hits = 0
for l in ls:
    p = par[l]
    tot_pairs += p["pairs_replayed"]
    tot_hits += p["hit_lanes_confirmed"]
    par_rows.append([
        l, p["n"], fmt(p["base_points"]), fmt(p["valid_pairs_per_target"]), fmt(p["pairs_replayed"]),
        f"{p['hit_lanes_confirmed']} / {p['hit_lanes_unconfirmed']}", p["exceptional_lanes"],
        f"{p['roots_found']} ({p['targets_with_roots']})", f"{p['root_set_mismatches']} / {p['verdict_mismatches']}",
        "yes" if p["digest_verdicts_equal_corpus"] and p["digest_verdicts_equal_expected"] == 1 else "NO",
        "yes" if p["digest_roots_equal_corpus"] and p["digest_roots_equal_expected"] == 1 else "NO",
    ])
par_rows.append(["all", "", "", "", fmt(tot_pairs), f"{tot_hits} / 0", 0, "", "0 / 0", "5 of 5", "5 of 5"])

# bit-operation table
bo_rows = []
for l in ls:
    e, p = emit[l], par[l]
    bo_rows.append([
        l, fmt(e["lop3_per_run"]), fmt(e["xand"]), f"{p['bitops_fused_per_lane_slot']:,.2f}",
        f"{p['bitops_unfused_per_lane_slot']:,.2f}", f"{p['lane_utilisation']:.4f}",
        f"{p['bitops_fused_per_valid_pair']:,.1f}", f"{p['bitops_unfused_per_valid_pair']:,.1f}",
        f"{p['lop3_thread_instructions_per_valid_pair']:,.2f}",
    ])

# self-test table
st_rows = []
for l in ls:
    s = self_[l]
    st_rows.append([l, "pass" if s["lut_tables_ok"] else "FAIL", f"{fmt(s['wires_compared'])} / {s['wire_mismatches']}",
                    f"{fmt(s['lanes_compared'])} / {s['lane_mismatches']}", fmt(s["reference_hit_lanes"]),
                    fmt(s["reference_exceptional_lanes"])])

# compile evidence
ptxas = open(f"{RAW}/ptxas_l8_sm_80.txt").read()
m = re.search(r"(\d+) bytes stack frame, (\d+) bytes spill stores, (\d+) bytes spill loads", ptxas)
regs = re.search(r"Used (\d+) registers", ptxas).group(1)
sass = open(f"{RAW}/sass_hist_l8_sm_80.txt").read()
n_sass = re.search(r"sass instructions: (\d+)", sass).group(1)
hist = {}
for line in sass.splitlines():
    mm = re.match(r"\s*(\d+) ([A-Z0-9]+)$", line)
    if mm:
        hist[mm.group(2)] = int(mm.group(1))
luts = {}
tail = sass.split("LOP3 tables:")[1]
for line in tail.splitlines():
    mm = re.match(r"\s*(\d+) (0x[0-9a-f]+)$", line)
    if mm:
        luts[mm.group(2)] = int(mm.group(1))

extra = ""
l11p = os.path.join(RAW, "ptxas_l11_sm_80.txt")
if os.path.exists(l11p):
    t11 = open(l11p).read()
    m11 = re.search(r"(\d+) bytes stack frame, (\d+) bytes spill stores, (\d+) bytes spill loads", t11)
    r11 = re.search(r"Used (\d+) registers", t11).group(1)
    extra = (f"\n== Compile evidence, l = 11 (sm_80)\nptxas: {r11} registers, {m11.group(1)} bytes stack, {m11.group(2)} bytes spill stores, "
             f"{m11.group(3)} bytes spill loads.\n")
    s11p = os.path.join(RAW, "sass_hist_l11_sm_80.txt")
    if os.path.exists(s11p):
        s11 = open(s11p).read()
        extra += f"SASS (static): {re.search(r'sass instructions: (\\d+)', s11).group(1)} instructions; see raw/sass_hist_l11_sm_80.txt.\n"

model_txt = "Not run in this report."
if model:
    model_txt = ("lop3-model build: " + "; ".join(
        f"l = {l}: {r['hit_lanes_confirmed']} hit lanes confirmed, {r['mismatches']} mismatches, digests equal "
        f"{'yes' if r['digest_verdicts_equal_corpus'] and r['digest_roots_equal_corpus'] else 'NO'}" for l, r in sorted(model.items())) + ".")
l13_txt = "Not run."
if p13:
    l13_txt = (f"l = 13 (PS-3's 3-target sample, program hash first recorded by PS-5): {p13['pairs_replayed']:,} pairs, "
               f"{p13['mismatches']} mismatches, verdict and root digests equal the sample's: "
               f"{'yes' if p13['digest_verdicts_equal_corpus'] and p13['digest_roots_equal_corpus'] else 'NO'}; "
               f"emulation wall {p13['emulation_secs']} s.")

# One font family everywhere keeps the PDF small (the data-file rule of AGENTS.md puts PDFs over 64 KiB in the artifact store):
# the figures are copied with their font names replaced, for rendering only.
import shutil
svgdir = os.path.join(OUT, "_svg")
os.makedirs(svgdir, exist_ok=True)
for name in ("ps5_pipeline.svg", "ps5_ops_and_coverage.svg"):
    t = open(os.path.join(HERE, "figures", name)).read()
    t = t.replace("Helvetica, Arial, sans-serif", "Libertinus Serif").replace("'DejaVu Sans'", "'Libertinus Serif'").replace("'Inter'", "'Libertinus Serif'")
    open(os.path.join(svgdir, name), "w").write(t)

typ = f"""
#set page(paper: "a4", margin: (x: 1.5cm, y: 1.6cm), numbering: "1")
#set text(size: 9pt, font: "Libertinus Serif")
#show raw: set text(font: "Libertinus Serif", size: 8.5pt)
#set par(justify: false)
#show heading: set block(above: 1em, below: 0.5em)
#show table: set text(size: 7.8pt)

= PS-5: GPU kernel, CPU emulation and digest parity

*Date* 2026-10-18. *Status:* #text(fill: rgb("#a33"))[*the device run did not happen and is BLOCKED (no GPU, no owner-approved allocation or cap).*]
No GPU figure, speedup or ratio appears anywhere in this report. Every executed number is a *CPU emulation* number or a *compile-time* number of the pinned `nvcc` 13.3.73.
Protocol: `crypto` `research/pdp_oracle_speedup_20261011/protocols/PS-5.md`; this repository's `experiments/pdp-oracle-speedup-20261011/ps5/README.md` is the full record.

== What was built
PS-3's straight-line program (hash-frozen, `pdp-slp/1`) is turned by `pdp_ps5_emit` into one statement per gate; every gate is one `lop3` (the fused xor-and is one ternary operation). The same generated
statements are compiled by `nvcc` as the CUDA kernel (never run) and by a C compiler as the CPU emulation, which a parity driver runs over the PS-0 corpus.

#figure(image("/report/_svg/ps5_pipeline.svg", width: 100%), caption: [Pipeline and what was run. Source: `figures/ps5_pipeline.svg`.])

== Requirement status (summary; the full table is in the README)
#table(columns: (1.2fr, 2.2fr), inset: 4pt, stroke: 0.4pt + luma(160),
  [*Requirement*], [*Status*],
  [Frozen program by hash, l = 8..12], [verified complete: the five hashes equal PS-2's; fresh export byte-identical],
  [CUDA kernel, `lop3`, one pair per lane, generated], [implemented; compile-checked for sm_80 (l = 8: PTX has exactly 63,630 `lop3.b32` = the program's gates); *never run on a device*],
  [CPU emulation of the kernel's arithmetic], [implemented and verified on the CPU (same generated code; storage binding and operator form named in the README)],
  [Replay PS-0 corpus, identical digests and root sets, l = 8..12], [verified complete on the CPU: {tot_pairs:,} pairs, 400 targets, 0 mismatches],
  [Same gate on the device], [*BLOCKED*: no GPU, no allocation],
  [Counted bit operations per pair], [verified complete (derived, cross-checked against the PTX); table below],
  [Pairs per second on a device; A/A; ABAB vs PS-3], [*BLOCKED*],
  [>= 50x PS-3 (success) / < 20x (stop)], [*not evaluated* (no device); requirement open],
  [Expected ratio from a datasheet and microbenchmark], [*not filled: no device, no datasheet-sourced figure*],
  [l = 13..16], [l = 13 optional sample only; 14..16 not attempted],
  [`fes_gpu.rs` bridge (paired PR)], [not attempted; `fes_gpu.rs` untouched],
)

== Parity with PS-0 (CPU emulation, 80 targets per rung)
{table(11, ["l", "n", "base pts", "pairs/target", "pairs replayed", "hit lanes conf./unconf.", "exc. lanes", "roots (targets)", "root-set / verdict mismatches", "verdict digest = PS-0", "root digest = PS-0"], par_rows)}

{model_txt}

{l13_txt}

== Self-test (CPU emulation, 50 repetitions per rung)
{table(6, ["l", "lop3 tables", "wires compared / mismatches", "lanes compared / mismatches", "reference hit lanes", "reference exceptional lanes"], st_rows)}

== Counted bit operations per pair
Per lane slot: bit operations = G x 32 / (8 tasks x 32 lanes) = G / 8 (fused: xand = 1; two-input: xand = 2). Per valid pair: divide by the lane utilisation u = valid pairs / lane slots of this job layout.
{table(9, ["l", "G (lop3/run)", "xand", "fused / lane slot", "two-input / lane slot", "u", "fused / valid pair", "two-input / valid pair", "lop3 / valid pair"], bo_rows)}

#figure(image("/report/_svg/ps5_ops_and_coverage.svg", width: 100%), caption: [Left: counted gates per lane slot by kind (n = 8 tasks per program). Right: pairs replayed through the CPU emulation per rung (80 targets). Source: `raw/emit`, `raw/parity_l*.jsonl`; `figures/ps5_ops_and_coverage.svg`.])

== Compile evidence, l = 8 (sm_80, nvcc 13.3.73 -O3; nothing run)
ptxas: {regs} registers, {m.group(1)} bytes stack, {m.group(2)} bytes spill stores, {m.group(3)} bytes spill loads. SASS (static): {n_sass} instructions, of which LOP3 {hist.get("LOP3")}
(tables 0x78: {luts.get("0x78")}, 0x3c: {luts.get("0x3c")}, 0xc0: {luts.get("0xc0")}, 0xfc: {luts.get("0xfc")}); LDL {hist.get("LDL")}, STL {hist.get("STL")}, LDG {hist.get("LDG")}, STG {hist.get("STG")}, ATOMG {hist.get("ATOMG")}.
The program has 46,360 xand, 12,334 xor, 4,008 and, 880 or, 48 not gates. These are static compiler outputs, not performance.
{extra}
== Gaps and open requirements
The device run and everything that needs it (pairs per second, A/A, ABAB against PS-3, the 50x and 20x thresholds, the expected ratio) stay open. Also: the Gray-position mapping is moot and was not built; the emulation keeps wires in an array and
runs operators proved equal to the `lop3` tables (hardware `lop3` semantics not verified here); the job layout wastes lanes (u = 0.25 to 0.87); the l = 8 kernel needs 255 registers and spills; the PS-0 corpus has no exceptional
lanes; no Rust bridge, NVRTC path or CI job; l = 14..16 not attempted. Host: {manifest["cpu"]["model_name"]}, {manifest["cpu"]["cpus"]} vCPU, kernel {manifest["os"]["kernel"]}, shared host, evidence tier: none (exploratory); GPU devices: none.
"""
open(os.path.join(OUT, "ps5_report.typ"), "w").write(typ)
typst.compile(os.path.join(OUT, "ps5_report.typ"), output=os.path.join(OUT, "ps5_report.pdf"), root=HERE)
shutil.rmtree(svgdir)
# Typst writes no object streams; rewriting them takes the PDF from about 100 KB to about 62 KB (under the 64 KiB store threshold).
import pikepdf

pdf_path = os.path.join(OUT, "ps5_report.pdf")
with pikepdf.open(pdf_path, allow_overwriting_input=True) as pdf:
    pdf.save(pdf_path, object_stream_mode=pikepdf.ObjectStreamMode.generate, compress_streams=True,
             recompress_flate=True, stream_decode_level=pikepdf.StreamDecodeLevel.generalized)
print("wrote", os.path.join(OUT, "ps5_report.pdf"))
