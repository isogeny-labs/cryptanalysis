"""Render only the archived review text and its evidence-boundary diagram.

Dependencies: reportlab 4.4.10. This performs no trials or Lean builds.
"""
import hashlib
import html
import json
from pathlib import Path
import re

from reportlab import rl_config
from reportlab.graphics import renderSVG
from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

ROOT = Path(__file__).resolve().parent
rl_config.invariant = True


def diagram():
    d = Drawing(475, 166)
    rows = [
        (118, '#dcefe3', 'NATIVE MACHINE CHECK: PASSED',
         '4 identities; 4 theorem audits; standard Lean foundations'),
        (62, '#fff0cc', 'INDEPENDENT SOURCE REVIEW: SUPPORTS IDENTITIES',
         'Elaborated-type comparison still missing; review gate open'),
        (6, '#f7e1df', 'BROADER CRYPTANALYSIS CLAIMS: OPEN',
         'Graph/group bridge, recovery conditions, probability and cost'),
    ]
    for y, fill, title, subtitle in rows:
        d.add(Rect(1, y, 473, 45, rx=5, ry=5,
                   fillColor=colors.HexColor(fill), strokeColor=colors.HexColor('#555555')))
        d.add(String(12, y+29, title, fontName='Helvetica-Bold', fontSize=9))
        d.add(String(12, y+12, subtitle, fontName='Helvetica', fontSize=9))
    for y in (107, 51):
        d.add(Line(237, y, 237, y+10, strokeColor=colors.HexColor('#555555')))
    return d


def inline(text):
    text = re.sub(r'\[([^]]+)\]\(([^)]+)\)', r'\1 (\2)', text)
    text = text.replace('`', '')
    return html.escape(text)


def main():
    styles = getSampleStyleSheet()
    body = styles['BodyText']; body.fontSize = 9; body.leading = 13
    body.spaceAfter = 7; body.alignment = TA_LEFT; body.splitLongWords = True
    styles['Heading1'].fontSize = 17; styles['Heading1'].leading = 21
    styles['Heading2'].fontSize = 12; styles['Heading2'].leading = 16
    doc = SimpleDocTemplate(str(ROOT/'report.pdf'), pagesize=(595.28, 841.89),
                           leftMargin=60, rightMargin=60, topMargin=48, bottomMargin=46,
                           title='Known-label algebra technical evidence review',
                           author='TASK-20261028-871ca0')
    blocks = (ROOT/'report.md').read_text().strip().split('\n\n')
    flow = []
    for block in blocks:
        if block.startswith('# '):
            flow.append(Paragraph(inline(block[2:]), styles['Heading1']))
            flow.append(diagram()); flow.append(Spacer(1, 10))
        elif block.startswith('## '):
            flow.append(Paragraph(inline(block[3:]), styles['Heading2']))
        elif block.startswith('| '):
            lines = block.splitlines(); headings = [c.strip() for c in lines[0].strip('|').split('|')]
            for line in lines[2:]:
                cells = [c.strip() for c in line.strip('|').split('|')]
                flow.append(Paragraph('<br/>'.join('<b>'+inline(k)+':</b> '+inline(v)
                                                  for k,v in zip(headings,cells)),body))
        elif block.startswith('- '):
            for line in block.splitlines():
                flow.append(Paragraph(inline(line),body))
        else:
            flow.append(Paragraph(inline(block.replace('\n',' ')),body))
    def footer(canvas, doc):
        canvas.saveState(); canvas.setFont('Helvetica',8)
        canvas.drawString(60,28,'Known-label review | producer 0b353c9 | native job 123003327508')
        canvas.drawRightString(535,28,str(doc.page)); canvas.restoreState()
    doc.build(flow,onFirstPage=footer,onLaterPages=footer)
    renderSVG.drawToFile(diagram(),str(ROOT/'proof-boundary.svg'))
    names=['report.md','render_report.py','proof-boundary.svg','report.pdf','native-ci/receipt.json','independence-round2.json']
    receipt={'schema':'review-render/v1','producer':'0b353c9bf78e9340c3c100b71175127bb7d91d44',
             'command':'uv run --no-project --python 3.11 --with reportlab==4.4.10 python render_report.py',
             'inputs_and_outputs':{n:{'sha256':hashlib.sha256((ROOT/n).read_bytes()).hexdigest(),
                                      'bytes':(ROOT/n).stat().st_size} for n in names},
             'scope':'Derived review diagram and PDF; no measurements or new proof execution.'}
    (ROOT/'render-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')


if __name__ == '__main__':
    main()
