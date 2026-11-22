#!/usr/bin/env python3
"""Render a small Markdown report (headings, paragraphs, bullets, pipe tables, one PNG) to PDF.

Usage: make_report_pdf.py REPORT.md OUT.pdf [--image PNG]

The report PDFs of the earlier n=83 rounds were built with pandoc and pdflatex.
That toolchain is not usable on every host (this one lacks the Latin Modern
and Type 1 metrics), so this is a dependency-light renderer (reportlab, standard PDF fonts) that keeps the PDF well under 64 KiB. It renders what the
report says and adds nothing: the Markdown is the report. Links are kept as
their text, code spans as monospace, and a YAML front matter gives the title.
"""

import argparse
import re
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import Image, ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

SERIF, BOLD, MONO = "Times-Roman", "Times-Bold", "Courier"
ASCII = {"\u2265": ">=", "\u2264": "<=", "\u2248": "~", "\u2192": "->", "\u2212": "-", "\u2013": "-",
         "\u2014": "--", "\u00b7": ".", "\u2019": "'", "\u2018": "'", "\u201c": '"', "\u201d": '"',
         "\u03bb": "lambda", "\u03c4": "tau", "\u03c6": "phi", "\u221a": "sqrt", "\u2026": "...",
         "\u2260": "!=", "\u00b2": "^2", "\u2208": "in", "\u2211": "sum"}


def inline(text):
    for old, new in ASCII.items():
        text = text.replace(old, new)
    text = text.encode("latin-1", "replace").decode("latin-1")
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"`([^`]+)`", lambda m: '<font name="Courier" size="7.5">%s</font>' % m.group(1), text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("markdown", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--image", type=Path)
    args = parser.parse_args()
    body = ParagraphStyle("b", fontName=SERIF, fontSize=8.6, leading=11.4, spaceAfter=5, wordWrap="CJK")
    h = {1: ParagraphStyle("h1", parent=body, fontName=BOLD, fontSize=14, leading=17, spaceAfter=7),
         2: ParagraphStyle("h2", parent=body, fontName=BOLD, fontSize=11, leading=14, spaceBefore=6),
         3: ParagraphStyle("h3", parent=body, fontName=BOLD, fontSize=9.5, leading=12, spaceBefore=4)}
    cell = ParagraphStyle("c", parent=body, fontSize=7.4, leading=9.2, spaceAfter=0)
    lines = args.markdown.read_text().splitlines()
    title = None
    if lines and lines[0] == "---":
        end = lines.index("---", 1)
        for line in lines[1:end]:
            if line.startswith("title:"):
                title = line.split(":", 1)[1].strip().strip('"')
        lines = lines[end + 1:]
    story, i = [], 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
        elif line.startswith("#"):
            level = min(len(line) - len(line.lstrip("#")), 3)
            story.append(Paragraph(inline(line.lstrip("#").strip()), h[level]))
            i += 1
        elif line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-+:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            width = max(len(r) for r in rows)
            data = [[Paragraph(inline(c), cell) for c in r + [""] * (width - len(r))] for r in rows]
            table = Table(data, hAlign="LEFT", colWidths=[(A4[0] - 3.2 * cm) / width] * width, repeatRows=1)
            table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
                                       ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.92, 0.92, 0.92)),
                                       ("VALIGN", (0, 0), (-1, -1), "TOP")]))
            story += [table, Spacer(1, 6)]
        elif re.match(r"\s*[-*] ", line):
            items = []
            while i < len(lines) and re.match(r"\s*[-*] ", lines[i]):
                text = re.sub(r"^\s*[-*] ", "", lines[i])
                i += 1
                while i < len(lines) and lines[i].startswith("  ") and not re.match(r"\s*[-*] ", lines[i]):
                    text += " " + lines[i].strip()
                    i += 1
                items.append(ListItem(Paragraph(inline(text), body), leftIndent=12))
            story.append(ListFlowable(items, bulletType="bullet", start="-", leftIndent=12))
        elif line.startswith("!["):
            i += 1
            if args.image:
                story += [Image(str(args.image), width=A4[0] - 3.2 * cm, height=(A4[0] - 3.2 * cm) * 0.46), Spacer(1, 6)]
        else:
            para = [line.strip()]
            i += 1
            while i < len(lines) and lines[i].strip() and not re.match(r"(#|\||\s*[-*] |!\[)", lines[i]):
                para.append(lines[i].strip())
                i += 1
            story.append(Paragraph(inline(" ".join(para)), body))
    doc = SimpleDocTemplate(str(args.out), pagesize=A4, leftMargin=1.6 * cm, rightMargin=1.6 * cm,
                            topMargin=1.5 * cm, bottomMargin=1.5 * cm, title=title or args.markdown.stem,
                            invariant=True)
    if title and not any(l.startswith("# ") for l in lines[:3]):
        story.insert(0, Paragraph(inline(title), h[1]))
    doc.build(story)
    print(args.out, args.out.stat().st_size)


if __name__ == "__main__":
    sys.exit(main())
