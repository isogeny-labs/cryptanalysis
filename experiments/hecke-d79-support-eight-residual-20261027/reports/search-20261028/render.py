#!/usr/bin/env python3
"""Render retrospective D79 evidence notes and vector figures using stdlib only."""
import hashlib
import json
import re
import textwrap
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
LIVE = ROOT / "hecke-d79-live-seven-20261027"
SUPPORT8 = ROOT / "hecke-d79-support-eight-residual-20261027"
LIVE_REPORT = LIVE / "reports/search-20261028"


def esc(text):
    return (str(text).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def svg_start(title, width=1000, height=600):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            '<rect width="100%" height="100%" fill="#ffffff"/>',
            '<style>text{font-family:Arial,sans-serif;fill:#182230}.title{font-size:26px;font-weight:bold}.label{font-size:17px}.small{font-size:14px}.axis{stroke:#526174;stroke-width:2}.fresh{fill:#2878b5}.control{fill:#d88b24}.good{fill:#31865b}.warn{fill:#bd5a45}.box{fill:#f3f6f9;stroke:#536579;stroke-width:2}</style>',
            f'<text x="40" y="42" class="title">{esc(title)}</text>']


def line(x1, y1, x2, y2, color="#526174", width=2):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}" marker-end="url(#arrow)"/>'


def svg_finish(lines, path):
    lines.append('</svg>')
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def live_figures():
    data = json.loads((LIVE / "index.json").read_text())
    cases = sorted(data["cases"], key=lambda c: c["p"])
    fresh = []
    for case in cases:
        if case["cohort"] != "fresh":
            continue
        summary = json.loads((LIVE / case["summary"]).read_text())
        fresh.append({**case, "source_count": summary["source_count"],
                      "final_rank": summary["final_rank_mod_q"]})
    rows = svg_start("Live support-seven source equations and rank", 1120, 610)
    rows += ['<text x="40" y="78" class="small">Each bar is the source count at stop; green reaches rank 39, red is rank 38 at the 40-source cap.</text>',
             '<line x1="120" y1="520" x2="1080" y2="520" class="axis"/>']
    for i, c in enumerate(fresh):
        x = 145 + i * 116
        h = c["source_count"] * 8
        cls = "good" if c["final_rank"] == 39 else "warn"
        rows += [f'<rect x="{x}" y="{520-h}" width="70" height="{h}" class="{cls}"/>',
                 f'<text x="{x+35}" y="{510-h}" text-anchor="middle" class="small">r{c["final_rank"]}</text>',
                 f'<text x="{x+35}" y="545" text-anchor="middle" class="small">{c["p"]}</text>',
                 f'<text x="{x+35}" y="570" text-anchor="middle" class="small">{c["source_count"]} src</text>']
    rows += ['<text x="40" y="592" class="small">Fresh panel only; known control p=103357, q=197 stopped at 14 sources and is reported separately in report.md.</text>']
    svg_finish(rows, LIVE_REPORT / "source-counts.svg")

    flow = svg_start("Audited live collector: saved-evidence flow", 1180, 380)
    flow += ['<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#526174"/></marker></defs>']
    boxes = [(45, "Frozen classes, q fields,\nsource order and cap"), (275, "Collect degree-13\nlifts; journal each"),
             (505, "Enumerate exact rows\nwith support <= 7"), (735, "Update F_q rank; stop\nat 39 or source cap"),
             (965, "Independent Sage audit;\nreplay anchored logs")]
    for x, label in boxes:
        flow.append(f'<rect x="{x}" y="140" width="185" height="96" rx="8" class="box"/>')
        for j, part in enumerate(label.split("\n")):
            flow.append(f'<text x="{x+92}" y="178" text-anchor="middle" class="small">{esc(part)}</text>' if j == 0 else f'<text x="{x+92}" y="202" text-anchor="middle" class="small">{esc(part)}</text>')
    for x in [230, 460, 690, 920]:
        flow.append(line(x, 188, x+38, 188))
    flow += ['<text x="45" y="300" class="label">Frozen panel: 7/8 fresh classes rank 39; p1825517 remains rank 38 at 40 sources.</text>',
             '<text x="45" y="330" class="small">Only saved records are summarized here; no new lift collection or relation search was run.</text>']
    svg_finish(flow, LIVE_REPORT / "collector-flow.svg")


def support_figures():
    initial = json.loads((SUPPORT8 / "result.json").read_text())
    full = json.loads((SUPPORT8 / "full/result.json").read_text())
    rows = svg_start("Separate support-eight executions: probe cap and rank", 1100, 560)
    rows += ['<text x="45" y="78" class="small">Probe counts are from separate runs against the same frozen 40-source set; they are not added.</text>',
             '<line x1="120" y1="450" x2="1020" y2="450" class="axis"/>']
    vals = [("Initial cap", initial, "warn"), ("Full follow-up", full, "good")]
    maxp = max(v[1]["quintuple_sign_probes"] for v in vals)
    for i, (label, d, cls) in enumerate(vals):
        x = 260 + i * 390
        h = 290 * d["quintuple_sign_probes"] / maxp
        rows += [f'<rect x="{x}" y="{450-h:.1f}" width="210" height="{h:.1f}" class="{cls}"/>',
                 f'<text x="{x+105}" y="{430-h:.1f}" text-anchor="middle" class="label">rank {d["rank_after"]}</text>',
                 f'<text x="{x+105}" y="482" text-anchor="middle" class="label">{esc(label)}</text>',
                 f'<text x="{x+105}" y="510" text-anchor="middle" class="small">{d["quintuple_sign_probes"]:,} probes</text>',
                 f'<text x="{x+105}" y="532" text-anchor="middle" class="small">{d["verified_rows"]} verified rows</text>']
    svg_finish(rows, HERE / "probe-rank.svg")

    flow = svg_start("Audited support-eight residual closure", 1160, 390)
    flow += ['<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#526174"/></marker></defs>']
    boxes = [(40, "40 sealed sources;\nbase rank 38"), (265, "39,520 signed\ntriples indexed"),
             (490, "Signed 3+5 search;\none support-8 row"), (715, "Insert verified row;\nrank rises to 39"),
             (940, "Anchored solve;\n40/40 replays pass")]
    for x, label in boxes:
        flow.append(f'<rect x="{x}" y="140" width="180" height="96" rx="8" class="box"/>')
        for j, part in enumerate(label.split("\n")):
            flow.append(f'<text x="{x+90}" y="178" text-anchor="middle" class="small">{esc(part)}</text>' if j == 0 else f'<text x="{x+90}" y="202" text-anchor="middle" class="small">{esc(part)}</text>')
    for x in [220, 445, 670, 895]:
        flow.append(line(x, 188, x+38, 188))
    flow += ['<text x="40" y="300" class="label">Selected sources: (0,3,4,6,8,9,30,31); signs (+,+,-,-,-,+,-,-).</text>',
             '<text x="40" y="330" class="small">The initial capped run and full-space follow-up are distinct executions, not a cumulative probe count.</text>']
    svg_finish(flow, HERE / "relation-flow.svg")


def source_inventory():
    evidence = []
    summary_files = [f"cases/p{p}-summary.json" for p in
                     (1590437, 1636157, 1692917, 1713797, 1771877, 1793237, 1825517, 1852637)]
    for base, files in ((LIVE, ["PROTOCOL.md", "inputs.json", "index.json", "audit.json", "post-audit.json"] + summary_files),
                        (SUPPORT8, ["PROTOCOL.md", "pre-run.json", "result.json", "audit.json", "post-audit.json",
                                    "full/PROTOCOL.md", "full/pre-run.json", "full/result.json", "full/run-stdout.jsonl"])):
        for rel in files:
            p = base / rel
            evidence.append({"path": p.relative_to(ROOT).as_posix(),
                             "sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "bytes": p.stat().st_size})
    live_index = json.loads((LIVE / "index.json").read_text())
    live_cases = []
    for case in live_index["cases"]:
        if case["cohort"] == "fresh":
            summary = json.loads((LIVE / case["summary"]).read_text())
            live_cases.append({"p": case["p"], "q": case["q"],
                               "sources": summary["source_count"], "rank": summary["final_rank_mod_q"]})
    initial = json.loads((SUPPORT8 / "result.json").read_text())
    full = json.loads((SUPPORT8 / "full/result.json").read_text())
    report = {"schema": "retrospective-evidence-source-index/v1", "generated_by": "render.py",
              "new_trials": False, "chart_data": {
                  "live_seven_fresh_cases": live_cases,
                  "support_eight_runs": [
                      {"label": "initial_cap", "probes": initial["quintuple_sign_probes"],
                       "rank": initial["rank_after"], "verified_rows": initial["verified_rows"]},
                      {"label": "full_follow_up", "probes": full["quintuple_sign_probes"],
                       "rank": full["rank_after"], "verified_rows": full["verified_rows"]}],
              }, "evidence": evidence}
    encoded = json.dumps(report, indent=2) + "\n"
    (HERE / "sources.json").write_text(encoded, encoding="utf-8")
    (LIVE_REPORT / "sources.json").write_text(encoded, encoding="utf-8")


def pdf_escape(s):
    s = s.encode("ascii", "replace").decode("ascii")
    return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def make_pdf(md_path, svg_chart, out_path):
    raw = md_path.read_text(encoding="utf-8")
    lines = []
    for original in raw.splitlines():
        line = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", original)
        line = re.sub(r"[`*_]", "", line)
        if not line.strip():
            lines.append("")
            continue
        lines.extend(textwrap.wrap(line, width=96, break_long_words=True, break_on_hyphens=False) or [""])
    chunks = [lines[i:i+52] for i in range(0, len(lines), 52)] or [[]]
    streams = []
    for page_no, chunk in enumerate(chunks, 1):
        out = ["BT", "/F1 9 Tf", "50 790 Td", "12 TL"]
        for idx, line in enumerate(chunk):
            if idx == 0 and line.startswith("# "):
                out += ["/F1 16 Tf", f"({pdf_escape(line[2:])}) Tj", "/F1 9 Tf", "0 -18 Td"]
                continue
            out += [f"({pdf_escape(line)}) Tj", "T*"]
        out += ["ET", f"BT /F1 8 Tf 50 24 Td (Retrospective saved-evidence report - page {page_no}) Tj ET"]
        streams.append("\n".join(out).encode("ascii"))
    # Add a vector chart page; bar geometry is intentionally simple for a reproducible PDF.
    source_data = json.loads((md_path.parent / "sources.json").read_text())
    if "support-eight" in str(md_path):
        runs = source_data["chart_data"]["support_eight_runs"]
        maximum = max(run["probes"] for run in runs)
        chart = ["BT /F1 16 Tf 50 790 Td (Two separate support-eight executions) Tj ET"]
        y_positions = [460, 380]
        colors = ["0.74 0.35 0.27 rg", "0.19 0.52 0.36 rg"]
        for run, y, color in zip(runs, y_positions, colors):
            width = int(370 * run["probes"] / maximum)
            chart += [color, f"100 {y} {width} 34 re f",
                      f"BT /F1 10 Tf 100 {y+45} Td ({run['label']}: {run['probes']:,} probes; rank {run['rank']}; {run['verified_rows']} verified rows) Tj ET"]
        chart += ["BT /F1 10 Tf 100 300 Td (Separate runs; probe counts are not added. 40/40 anchored replays pass.) Tj ET"]
    else:
        cases = source_data["chart_data"]["live_seven_fresh_cases"]
        rank39 = sum(case["rank"] == 39 for case in cases)
        rank38 = sum(case["rank"] == 38 for case in cases)
        chart = ["BT /F1 16 Tf 50 790 Td (Fresh live-seven panel: audited final ranks) Tj ET",
                 "0.19 0.52 0.36 rg", f"90 480 {rank39*35} 36 re f",
                 "BT /F1 11 Tf 90 530 Td (Rank 39 reached on 7 of 8 fresh classes) Tj ET",
                 "0.74 0.35 0.27 rg", f"90 390 {rank38*35} 36 re f",
                 "BT /F1 11 Tf 90 440 Td (Rank 38 at the 40-source cap on 1 fresh class) Tj ET",
                 "BT /F1 10 Tf 90 300 Td (Counts describe this frozen panel, not a population rate or speed claim.) Tj ET"]
    chart += ["BT /F1 8 Tf 50 24 Td (Source records and SHA-256 digests are listed in sources.json.) Tj ET"]
    streams.append("\n".join(chart).encode("ascii"))
    # Assemble a small PDF with built-in Helvetica and one uncompressed stream per page.
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>", None,
               b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    page_ids = []
    for stream in streams:
        page_id = len(objects) + 1
        contents_id = page_id + 1
        page_ids.append(page_id)
        objects.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 842] /Resources << /Font << /F1 3 0 R >> >> /Contents {contents_id} 0 R >>".encode())
        objects.append(b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream")
    kids = " ".join(f"{n} 0 R" for n in page_ids)
    objects[1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode()
    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for i, obj in enumerate(objects, 1):
        offsets.append(len(pdf))
        pdf.extend(f"{i} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref = len(pdf)
    pdf.extend(f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode())
    pdf.extend(f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    Path(out_path).write_bytes(pdf)


def main():
    source_inventory()
    live_figures()
    support_figures()
    make_pdf(LIVE_REPORT / "report.md", LIVE_REPORT / "source-counts.svg", LIVE_REPORT / "report.pdf")
    make_pdf(HERE / "report.md", HERE / "probe-rank.svg", HERE / "report.pdf")


if __name__ == "__main__":
    main()
