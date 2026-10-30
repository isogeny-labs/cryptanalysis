#!/usr/bin/env python3
"""Render existing evidence and RESULT.md; never execute the Sage experiment.

Requires Graphviz dot, reportlab and PyMuPDF. The SVGs remain editable and
the PDF uses vectors. Run from any directory with python3 build_report.py.
"""
from pathlib import Path
import hashlib
import html
import json
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET

import fitz
import reportlab
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, PageBreak

HERE = Path(__file__).resolve().parent
FONT = Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
pdfmetrics.registerFont(TTFont('EvidenceSans', str(FONT)))
BASE_URL = 'https://github.com/isogeny-labs/cryptanalysis/blob/codex/hecke-x011-global-fricke-20261026/experiments/hecke-x011-global-fricke-20261026/'


def inline(text):
    text = re.sub(r'`([^`]+)`', r'\1', text)
    parts = []
    start = 0
    for match in re.finditer(r'\[([^]]+)\]\(([^)]+)\)', text):
        parts.append(html.escape(text[start:match.start()]))
        url = match[2] if '://' in match[2] else BASE_URL + match[2]
        parts.append(f'<link href="{html.escape(url, quote=True)}" color="#125b8b">{html.escape(match[1])}</link>')
        start = match.end()
    parts.append(html.escape(text[start:]))
    return ''.join(parts)


def main():
    evidence = json.loads((HERE / 'verification.json').read_text())
    rows = sorted(((int(p), item['checked_points']) for p, item in evidence['finite_field_checks'].items()))
    assert rows == [(7, 10), (13, 10), (23, 25), (23743, 3)]
    subprocess.run(['dot', '-Tsvg', 'evidence.dot', '-o', 'evidence.svg'], cwd=HERE, check=True)
    body = ParagraphStyle('body', fontName='EvidenceSans', fontSize=9, leading=13, spaceAfter=8)
    styles = {1: ParagraphStyle('title', parent=body, fontSize=15, leading=20, spaceAfter=16),
              2: ParagraphStyle('heading', parent=body, fontSize=12, leading=16, spaceBefore=10)}
    story = []
    for block in (HERE / 'RESULT.md').read_text().split('\n\n'):
        block = block.strip()
        if not block:
            continue
        if block.startswith('## Visual report and graph review'):
            story.append(PageBreak())
        level = len(block) - len(block.lstrip('#'))
        style = styles.get(level, body) if block.startswith('#') else body
        text = block[level:].strip() if block.startswith('#') else block
        story.append(Paragraph(inline(' '.join(text.splitlines())), style))
    story.extend([Spacer(1, 16), Paragraph('Saved finite-field coverage', styles[2]),
                  Paragraph('Source: verification.json. Counts are exact saved control coverage, not timing measurements or a proof of the global modular identity. The F23743 check uses three distinguished points; the other fields enumerate every curve point.', body)])
    drawing = Drawing(475, 220)
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="720" height="310" viewBox="0 0 720 310">',
           '<rect width="720" height="310" fill="white"/>',
           '<g font-family="sans-serif" font-size="16" fill="#172b4d">',
           '<text x="24" y="28">Saved point checks by finite field (exact counts)</text>']
    for i, (prime, count) in enumerate(rows):
        y = 170 - i * 40
        drawing.add(String(0, y+3, f'F{prime}', fontName='EvidenceSans', fontSize=10))
        drawing.add(Rect(78, y, count*12, 21, fillColor=colors.HexColor('#2f7498'), strokeColor=None))
        drawing.add(String(85+count*12, y+4, str(count), fontName='EvidenceSans', fontSize=10))
        sy = 55+i*52
        svg.extend([f'<text x="24" y="{sy+23}">F{prime}</text>',
                    f'<rect x="155" y="{sy}" width="{count*16}" height="32" fill="#2f7498"/>',
                    f'<text x="{165+count*16}" y="{sy+23}">{count}</text>'])
    drawing.add(String(78, 4, 'Points checked (count); uncertainty: not applicable', fontName='EvidenceSans', fontSize=9))
    svg.extend(['<text x="24" y="292">F23743: distinguished points only; other fields: all points.</text>', '</g></svg>'])
    (HERE / 'coverage.svg').write_text('\n'.join(svg)+'\n')
    ET.parse(HERE / 'evidence.svg')
    ET.parse(HERE / 'coverage.svg')
    story.extend([Spacer(1, 12), drawing])
    with tempfile.TemporaryDirectory() as tmp:
        text_pdf = Path(tmp) / 'report-text.pdf'
        diagram_pdf = Path(tmp) / 'diagram.pdf'
        SimpleDocTemplate(str(text_pdf), pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40).build(story)
        subprocess.run(['dot', '-Tpdf', str(HERE/'evidence.dot'), '-o', str(diagram_pdf)], check=True)
        with fitz.open(text_pdf) as pdf, fitz.open(diagram_pdf) as diagram:
            page = pdf.new_page(width=A4[1], height=A4[0])
            page.show_pdf_page(fitz.Rect(20, 20, A4[1]-20, A4[0]-20), diagram, 0)
            pdf.set_metadata({'title': 'Fricke involution on the 11a1 model', 'author': 'Cryptanalysis research record'})
            pdf.save(HERE/'report.pdf', garbage=4, deflate=True)
    with fitz.open(HERE/'report.pdf') as pdf:
        text = '\n'.join(page.get_text() for page in pdf)
        for required in ['formalization', 'FrickeAffine', 'Saved finite-field coverage', 'WRITTEN GLOBAL CONCLUSION', 'OPEN LEAN BRIDGE']:
            assert required in text, required
        pages = len(pdf)
    files = ['RESULT.md', 'PROTOCOL.md', 'verification.json', 'formal/FrickeAffine.lean',
             'formal/build-output.txt', 'evidence.dot', 'evidence.svg', 'coverage.svg', 'build_report.py', 'report.pdf']
    validation = {'scope': 'Documentation rendering only; no Sage, Lean, benchmark or new experiment executed',
                  'reportlab': reportlab.Version, 'pymupdf': fitz.VersionBind,
                  'graphviz': subprocess.run(['dot', '-V'], capture_output=True, text=True, check=True).stderr.strip(),
                  'pdf_pages': pages, 'coverage': rows,
                  'files': {f: {'sha256': hashlib.sha256((HERE/f).read_bytes()).hexdigest(), 'bytes': (HERE/f).stat().st_size} for f in files}}
    (HERE/'visuals-validation.json').write_text(json.dumps(validation, indent=2)+'\n')
    print(json.dumps({'pdf_pages': pages, 'pdf_bytes': (HERE/'report.pdf').stat().st_size, 'coverage': rows}))


if __name__ == '__main__':
    main()
