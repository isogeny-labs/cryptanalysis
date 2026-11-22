"""Render the complete report and editable algorithm diagram; no experiment."""
from hashlib import sha256
from pathlib import Path
from xml.sax.saxutils import escape
import importlib.metadata
import json
import re
import reportlab

from reportlab.graphics import renderSVG
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = Path(__file__).resolve().parent
FONTS = Path(reportlab.__file__).resolve().parent/'fonts'
pdfmetrics.registerFont(TTFont('NoteSans', str(FONTS/'Vera.ttf')))
pdfmetrics.registerFont(TTFont('NoteSansBold', str(FONTS/'VeraBd.ttf')))
pdfmetrics.registerFontFamily('NoteSans', normal='NoteSans', bold='NoteSansBold',
                              italic='NoteSans', boldItalic='NoteSansBold')


def diagram():
    source = json.loads((ROOT/'diagram.json').read_text())
    drawing = Drawing(720, 290)
    drawing.add(String(5, 270, source['title'], fontName='NoteSansBold', fontSize=14))
    for row, boxes in enumerate(source['rows']):
        y = 176-94*row
        for col, lines in enumerate(boxes):
            x = 5+244*col
            drawing.add(Rect(x, y, 222, 62, rx=5, ry=5,
                             fillColor=colors.HexColor('#e8f0ff'),
                             strokeColor=colors.HexColor('#64748b')))
            for i, line in enumerate(lines):
                drawing.add(String(x+111, y+41-17*i, line, textAnchor='middle',
                                   fontName='NoteSans', fontSize=11))
            if col < 2:
                drawing.add(Line(x+222, y+31, x+240, y+31,
                                 strokeColor=colors.HexColor('#64748b')))
                drawing.add(Polygon([x+240,y+31,x+234,y+35,x+234,y+27],
                                    fillColor=colors.HexColor('#64748b'), strokeColor=None))
    for x1, y1, x2, y2 in ((604,176,604,160), (604,160,116,160), (116,160,116,144)):
        drawing.add(Line(x1, y1, x2, y2, strokeColor=colors.HexColor('#64748b')))
    drawing.add(Polygon([116,144,112,150,120,150],
                        fillColor=colors.HexColor('#64748b'), strokeColor=None))
    for i, text in enumerate(source['notes']):
        drawing.add(String(5, 55-17*i, text, fontName='NoteSans', fontSize=10.5))
    return drawing


def rich(text):
    text = escape(text)
    text = re.sub(r'\[([^]]+)\]\(([^)]+)\)',
                  r'<link href="\2" color="#1d4ed8">\1</link>', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)
    return re.sub(r'`([^`]+)`', r'<font face="NoteSans">\1</font>', text)


def main():
    styles = getSampleStyleSheet()
    styles['BodyText'].fontName = 'NoteSans'
    styles['Title'].fontName = styles['Heading2'].fontName = 'NoteSansBold'
    styles.add(ParagraphStyle(name='ReportBody', parent=styles['BodyText'],
                              fontSize=9.5, leading=13, spaceAfter=8))
    styles['Code'].fontSize, styles['Code'].leading = 7.5, 10
    styles['Code'].fontName = 'NoteSans'
    flow, pending, code = [], [], []

    def flush():
        if pending:
            flow.append(Paragraph(rich(' '.join(pending)), styles['ReportBody']))
            pending.clear()
        if code:
            flow.extend([Preformatted('\n'.join(code), styles['Code'], maxLineLength=110),
                         Spacer(1, 6)])
            code.clear()

    for line in (ROOT/'README.md').read_text().splitlines():
        if line.startswith('#'):
            flush()
            level = len(line)-len(line.lstrip('#'))
            flow.append(Paragraph(rich(line[level:].strip()),
                                  styles['Title' if level == 1 else 'Heading2']))
            if level == 1:
                drawing = diagram()
                renderSVG.drawToFile(drawing, str(ROOT/'diagram.svg'))
                drawing.scale(0.7, 0.7)
                drawing.width *= 0.7
                drawing.height *= 0.7
                flow.extend([drawing, Spacer(1, 10)])
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

    def footer(c, doc):
        c.setFont('NoteSans', 8)
        c.drawString(40, 23, f'2026-10-29 | Correctness prototype; complete cost unknown | {doc.page}')

    def deterministic_canvas(*args, **kwargs):
        kwargs['invariant'] = 1
        return canvas.Canvas(*args, **kwargs)

    SimpleDocTemplate(str(ROOT/'REPORT.pdf'), pagesize=(595.28, 841.89),
                      leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=42,
                      title='Coordinate pair index for known-label construction',
                      author='isogeny-labs research').build(
                          flow, onFirstPage=footer, onLaterPages=footer,
                          canvasmaker=deterministic_canvas)
    names = ['README.md', 'PROTOCOL.md', 'diagram.json', 'diagram.svg',
             'render_report.py', 'REPORT.pdf']
    receipt = {'renderer':'ReportLab', 'version':importlib.metadata.version('reportlab'),
               'command':'python render_report.py',
               'files':{name:{'bytes':(ROOT/name).stat().st_size,
                              'sha256':sha256((ROOT/name).read_bytes()).hexdigest()}
                        for name in names},
               'benchmark_run':False, 'native_lean_status':'pending real CI'}
    (ROOT/'RENDER_RECEIPT.json').write_text(json.dumps(receipt, indent=2)+'\n')


if __name__ == '__main__':
    main()
