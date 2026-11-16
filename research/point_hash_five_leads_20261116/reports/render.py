#!/usr/bin/env python3
"""Lay out the recorded Markdown and SVG; performs no research computation.

Install typst and mistune in a scratch venv, then invoke this file there.
The generated report.typ remains editable and can be compiled separately.
"""
import json
from pathlib import Path

import mistune
import typst

ROOT = Path(__file__).resolve().parent


def quoted(value):
    return json.dumps(value, ensure_ascii=False)


def inline(nodes):
    out = []
    for node in nodes:
        kind = node["type"]
        if kind == "text":
            out.append("#text(" + quoted(node["raw"]) + ")")
        elif kind == "codespan":
            out.append("#raw(" + quoted(node["raw"]) + ")")
        elif kind == "softbreak":
            out.append(" ")
        elif kind == "linebreak":
            out.append("#linebreak()")
        elif kind == "image":
            out.append('#image(' + quoted(node["attrs"]["url"]) + ', width: 65%)')
        elif kind == "link":
            out.append("#link(" + quoted(node["attrs"]["url"]) + ")[" + inline(node["children"]) + "]")
        elif kind in ("strong", "emphasis"):
            fn = "strong" if kind == "strong" else "emph"
            out.append("#" + fn + "[" + inline(node["children"]) + "]")
        else:
            raise ValueError("unsupported inline node: " + kind)
    return "".join(out)


def blocks(nodes):
    out = []
    for node in nodes:
        kind = node["type"]
        if kind == "blank_line":
            continue
        if kind == "heading":
            level = node["attrs"]["level"]
            out.append("#heading(level: " + str(level) + ")[" + inline(node["children"]) + "]")
            if node["children"] == [{"type": "text", "raw": "References"}]:
                out.append("#set text(size: 8pt)")
        elif kind in ("paragraph", "block_text"):
            out.append(inline(node["children"]))
        elif kind == "list":
            fn = "enum" if node["attrs"]["ordered"] else "list"
            items = ["[" + blocks(item["children"]) + "]" for item in node["children"]]
            out.append("#" + fn + "(tight: false, " + ", ".join(items) + ")")
        else:
            raise ValueError("unsupported block node: " + kind)
    return "\n\n".join(out)


def main():
    ast = mistune.create_markdown(renderer="ast")((ROOT / "REPORT.md").read_text())
    preamble = '''// Generated layout only. Source: REPORT.md and pipeline.svg.
#set document(title: "Point hashing: five integrated paths", author: "Isogeny Labs — development implementation")
#set page(paper: "a4", margin: (x: 17mm, y: 17mm), numbering: "1",
  header: context text(size: 8pt, fill: rgb("52677d"))[Point hashing · implementation controls · 2026-11-16])
#set text(font: "DejaVu Sans", size: 9pt)
#set par(justify: false, leading: 0.65em)
#set heading(numbering: none)
#show heading.where(level: 1): set text(size: 20pt, fill: rgb("16395b"))
#show heading.where(level: 2): set text(size: 13pt, fill: rgb("16395b"))
#show raw: set text(size: 7.6pt)
#show link: set text(fill: rgb("176293"), size: 8pt)
#show image: it => block(breakable: false, inset: 2pt, it)
'''
    (ROOT / "report.typ").write_text(preamble + blocks(ast) + "\n")
    typst.compile(str(ROOT / "report.typ"), output=str(ROOT / "report.pdf"), root=str(ROOT))


if __name__ == "__main__":
    main()
