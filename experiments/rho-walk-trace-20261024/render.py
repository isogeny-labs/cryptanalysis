#!/usr/bin/env python3
"""Render REPORT.md to REPORT.pdf and breakdown.svg to breakdown.png with headless Chromium."""
import subprocess, sys, base64
from pathlib import Path
import markdown

here = Path(__file__).resolve().parent
chrome = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
flags = ["--headless", "--no-sandbox", "--disable-gpu", "--hide-scrollbars"]
svg = (here / "breakdown.svg").read_text()
m = __import__("re").search(r'width="(\d+)" height="(\d+)"', svg)
w, h = int(m.group(1)), int(m.group(2))
subprocess.run([chrome, *flags, f"--window-size={w},{h+120}", f"--screenshot={here/'breakdown.png'}", (here / "breakdown.svg").as_uri()], check=True, capture_output=True)
md = (here / "REPORT.md").read_text()
body = markdown.markdown(md, extensions=["tables", "fenced_code"])
body = body.replace("breakdown.svg", "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode())
css = "body{font:13px/1.45 sans-serif;max-width:980px;margin:20px auto}table{border-collapse:collapse;font-size:11px}td,th{border:1px solid #bbb;padding:2px 5px}code{background:#f2f2f2}img{max-width:100%}"
html = here / "_report.html"
html.write_text(f"<html><head><meta charset='utf-8'><style>{css}</style></head><body>{body}</body></html>")
subprocess.run([chrome, *flags, f"--print-to-pdf={here/'REPORT.pdf'}", "--no-pdf-header-footer", html.as_uri()], check=True, capture_output=True)
html.unlink()
print("wrote REPORT.pdf, breakdown.png")
