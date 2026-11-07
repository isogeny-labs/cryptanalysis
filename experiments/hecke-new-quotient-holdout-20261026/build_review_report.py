#!/usr/bin/env python3
"""Render the exploratory reviewed report and saved rank evidence only.

Requires Graphviz dot, reportlab and PyMuPDF. The SVGs remain editable and
the PDF uses vectors. Run from any directory with python3 build_review_report.py.
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
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, PageBreak, Table, TableStyle

HERE = Path(__file__).resolve().parent
FONT = Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
pdfmetrics.registerFont(TTFont('EvidenceSans', str(FONT)))
BASE_URL = 'https://github.com/isogeny-labs/cryptanalysis/blob/codex/hecke-d2631-six-mixed-components-20261026/experiments/hecke-new-quotient-holdout-20261026/'


def inline(text):
    text = re.sub(r'`([^`]+)`', r'\1', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
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
    evidence = json.loads((HERE / 'validation.json').read_text())
    assert evidence['cycles'] == 6 and evidence['pairs'] == 48
    for rank in evidence['ranks'].values():
        assert rank == {'full': 480, 'nonfloor': 426, 'witness': 54}
    rows = [('Full matrix', 480), ('Nonfloor projection', 426), ('Floor witnesses', 54)]
    subprocess.run(['dot', '-Tsvg', 'evidence.dot', '-o', 'evidence.svg'], cwd=HERE, check=True)
    body = ParagraphStyle('body', fontName='EvidenceSans', fontSize=9, leading=13, spaceAfter=8)
    styles = {1: ParagraphStyle('title', parent=body, fontSize=15, leading=20, spaceAfter=16),
              2: ParagraphStyle('heading', parent=body, fontSize=12, leading=16, spaceBefore=10)}
    story = []
    for block in (HERE / 'RESULT_REVIEWED.md').read_text().split('\n\n'):
        block = block.strip()
        if not block:
            continue
        if block.startswith('|'):
            lines = [line for line in block.splitlines() if not re.fullmatch(r'[| :\-]+', line)]
            data = [[Paragraph(inline(cell.strip()), body) for cell in line.strip('|').split('|')] for line in lines]
            table = Table(data, colWidths=[245, 125, 145], repeatRows=1)
            table.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.3,colors.HexColor('#aab7c2')),
                                      ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#eaf2fa')),
                                      ('VALIGN',(0,0),(-1,-1),'TOP')]))
            story.extend([table, Spacer(1, 10)])
            continue
        level = len(block) - len(block.lstrip('#'))
        style = styles.get(level, body) if block.startswith('#') else body
        text = block[level:].strip() if block.startswith('#') else block
        story.append(Paragraph(inline(' '.join(text.splitlines())), style))
    story.extend([Spacer(1, 16), Paragraph('Saved exact ranks', styles[2]),
                  Paragraph('Source: validation.json. The exact rational ranks also agree modulo 23 and 1000000007. These are finite relation-space dimensions, not timing or end-to-end ECDLP measurements. Statistical uncertainty does not apply to these exact saved ranks.', body)])
    drawing = Drawing(475, 220)
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="720" height="310" viewBox="0 0 720 310">',
           '<rect width="720" height="310" fill="white"/>',
           '<g font-family="sans-serif" font-size="16" fill="#172b4d">',
           '<text x="24" y="28">Saved exact ranks (QQ; also modulo 23 and 1000000007)</text>']
    for i, (label, count) in enumerate(rows):
        y = 170 - i * 40
        drawing.add(String(0, y+3, label, fontName='EvidenceSans', fontSize=9))
        drawing.add(Rect(145, y, count*0.6, 21, fillColor=colors.HexColor('#2f7498'), strokeColor=None))
        drawing.add(String(152+count*0.6, y+4, str(count), fontName='EvidenceSans', fontSize=10))
        sy = 55+i*52
        svg.extend([f'<text x="24" y="{sy+23}">{label}</text>',
                    f'<rect x="225" y="{sy}" width="{count*0.85}" height="32" fill="#2f7498"/>',
                    f'<text x="{235+count*0.85}" y="{sy+23}">{count}</text>'])
    drawing.add(String(145, 4, 'Rank (dimension); exact saved values', fontName='EvidenceSans', fontSize=9))
    svg.extend(['<text x="24" y="292">480 - 426 = 54; 6 cycle + 48 pair witnesses. Exploratory case.</text>', '</g></svg>'])
    (HERE / 'ranks.svg').write_text('\n'.join(svg)+'\n')
    ET.parse(HERE / 'evidence.svg')
    ET.parse(HERE / 'ranks.svg')
    story.extend([Spacer(1, 12), drawing])
    with tempfile.TemporaryDirectory() as tmp:
        text_pdf = Path(tmp) / 'report-text.pdf'
        diagram_pdf = Path(tmp) / 'diagram.pdf'
        SimpleDocTemplate(str(text_pdf), pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40).build(story)
        subprocess.run(['dot', '-Tpdf', str(HERE/'evidence.dot'), '-o', str(diagram_pdf)], check=True)
        with fitz.open(text_pdf) as pdf, fitz.open(diagram_pdf) as diagram:
            page = pdf.new_page(width=A4[1], height=A4[0])
            page.show_pdf_page(fitz.Rect(20, 20, A4[1]-20, A4[0]-20), diagram, 0)
            pdf.set_metadata({'title': 'Exploratory D2631 mixed floor-kernel record', 'author': 'Cryptanalysis research record'})
            pdf.save(HERE/'report.pdf', garbage=4, deflate=True)
    with fitz.open(HERE/'report.pdf') as pdf:
        text = '\n'.join(page.get_text() for page in pdf)
        for required in ['exploratory', 'MixedSix', 'Saved exact ranks', 'SAVED FINITE CONCLUSION', 'OPEN BRIDGES']:
            assert required in text, required
        pages = len(pdf)
    files = ['README.md', 'RESULT_REVIEWED.md', 'evidence.dot', 'evidence.svg', 'ranks.svg',
             'build_review_report.py', 'verify_review.py', 'report.pdf',
             'review-20261030/provenance.json', 'review-20261030/MixedSix.sealed.lean.txt']
    validation = {'scope': 'Documentation rendering only; no Sage, Lean, benchmark or new experiment executed',
                  'reportlab': reportlab.Version, 'pymupdf': fitz.VersionBind,
                  'graphviz': subprocess.run(['dot', '-V'], capture_output=True, text=True, check=True).stderr.strip(),
                  'pdf_pages': pages, 'saved_ranks': rows,
                  'files': {f: {'sha256': hashlib.sha256((HERE/f).read_bytes()).hexdigest(), 'bytes': (HERE/f).stat().st_size} for f in files}}
    (HERE/'review-20261030/visuals-manifest.json').write_text(json.dumps(validation, indent=2)+'\n')
    print(json.dumps({'pdf_pages': pages, 'pdf_bytes': (HERE/'report.pdf').stat().st_size, 'saved_ranks': rows}))


if __name__ == '__main__':
    main()
