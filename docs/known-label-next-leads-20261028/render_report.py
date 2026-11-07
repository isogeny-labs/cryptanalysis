"""Render this proposal note and editable diagram; runs no experiment."""
from pathlib import Path
from hashlib import sha256
from xml.sax.saxutils import escape
import importlib.metadata
import json
import re

from reportlab.graphics import renderPDF, renderSVG
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted

ROOT = Path(__file__).resolve().parent


def diagram():
    d = Drawing(720, 345)

    def box(x, y, w, h, text):
        d.add(Rect(x, y, w, h, rx=6, ry=6,
                   fillColor=colors.HexColor('#e8f0ff'), strokeColor=colors.HexColor('#64748b')))
        for i, line in enumerate(text):
            d.add(String(x+w/2, y+h-19-16*i, line, textAnchor='middle',
                         fontName='Helvetica', fontSize=11))

    def arrow(x1, y1, x2, y2):
        d.add(Line(x1, y1, x2, y2, strokeColor=colors.HexColor('#64748b')))
        d.add(Polygon([x2, y2, x2-7, y2+3, x2-7, y2-3],
                      fillColor=colors.HexColor('#64748b'), strokeColor=None))

    d.add(String(5, 328, 'Lead 1: fixed domain, labels recovered from verified relations',
                 fontName='Helvetica-Bold', fontSize=13))
    box(5, 229, 155, 65, ['Actual points R_i in S', 'Labels initially unknown'])
    box(195, 229, 155, 65, ['Pair-sum witnesses', 'R_i + R_j = aP + bQ'])
    box(385, 229, 155, 65, ['Odd cycle or anchor', 'Propagate u_i, v_i'])
    box(575, 229, 140, 65, ['Verify every label', 'Keep original domain'])
    for a, b in [(160, 195), (350, 385), (540, 575)]:
        arrow(a, 261, b, 261)
    d.add(String(5, 205, 'Triangle identity: 2 R_1 = T_12 - T_23 + T_31. Cycle label defects can solve the DLP.',
                 fontName='Helvetica', fontSize=11))
    d.add(String(5, 181, 'Pair-table build, failed queries, graph work and group verification are charged.',
                 fontName='Helvetica', fontSize=11))
    d.add(String(5, 139, 'Lead 2: four-seed cubic generator with one-minus signed decoding',
                 fontName='Helvetica-Bold', fontSize=13))
    box(5, 44, 155, 65, ['Four labeled seeds', 'Cubic point polynomial F(i)'])
    box(195, 44, 155, 65, ['Shared index circuit', 'F(i) + F(j) - F(k) = O'])
    box(385, 44, 155, 65, ['Three signed moments', 'Recover k, then a quadratic'])
    box(575, 44, 140, 65, ['Decode and verify', 'Compare complete cost'])
    for a, b in [(160, 195), (350, 385), (540, 575)]:
        arrow(a, 76, b, 76)
    d.add(String(5, 12, 'Proposals, not measured speedups. Scalar field F_r and coordinate field F_p stay distinct.',
                 fontName='Helvetica', fontSize=11))
    return d


def rich(text):
    text = escape(text)
    text = re.sub(r'\[([^]]+)\]\(([^)]+)\)', r'<link href="\2" color="#1d4ed8">\1</link>', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'`([^`]+)`', r'<font face="Courier">\1</font>', text)
    return text


def main():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Note', parent=styles['BodyText'], fontSize=9.5,
                              leading=13, spaceAfter=8, splitLongWords=True))
    flow, pending, code = [], [], []

    def flush():
        if pending:
            flow.append(Paragraph(rich(' '.join(pending)), styles['Note']))
            pending.clear()
        if code:
            flow.append(Preformatted('\n'.join(code), styles['Code'], maxLineLength=100))
            flow.append(Spacer(1, 6))
            code.clear()

    for line in (ROOT/'README.md').read_text().splitlines():
        if line.startswith('#'):
            flush()
            level = len(line)-len(line.lstrip('#'))
            flow.append(Paragraph(rich(line[level:].strip()), styles['Title' if level==1 else 'Heading2' if level==2 else 'Heading3']))
            if level == 1:
                drawing = diagram()
                renderSVG.drawToFile(drawing, str(ROOT/'diagram.svg'))
                drawing.scale(0.70, 0.70)
                drawing.width *= 0.70
                drawing.height *= 0.70
                flow.extend([drawing, Spacer(1, 12)])
        elif not line.strip():
            flush()
        elif line.startswith('    '):
            if pending:
                flush()
            code.append(line[4:])
        else:
            if code:
                flush()
            pending.append(line)
    flush()

    def footer(canvas, doc):
        canvas.setFont('Helvetica', 8)
        canvas.drawString(40, 23, f'2026-10-28 | Proposals and algebra controls | page {doc.page}')

    SimpleDocTemplate(str(ROOT/'REPORT.pdf'), pagesize=(595.28, 841.89),
                      leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=42,
                      title='Known-label construction: graph bootstrap and cubic signatures').build(
                          flow, onFirstPage=footer, onLaterPages=footer)
    receipt = {'kind': 'document rendering only',
               'versions': {x: importlib.metadata.version(x) for x in ['reportlab', 'sympy', 'PyYAML']},
               'source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
               'inputs': {x: sha256((ROOT/x).read_bytes()).hexdigest() for x in ['README.md', 'CHECKS.json', 'atlas-matches.json']},
               'outputs': {x: {'sha256': sha256((ROOT/x).read_bytes()).hexdigest(), 'bytes': (ROOT/x).stat().st_size} for x in ['diagram.svg', 'REPORT.pdf']}}
    (ROOT/'RENDER_RECEIPT.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
