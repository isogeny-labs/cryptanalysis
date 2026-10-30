#!/usr/bin/env python3
"""Render documentation and exact-bound illustrations; no cryptanalysis run."""
import html
import json
import math
from pathlib import Path
import subprocess

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams["pdf.use14corefonts"] = True
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, PageBreak, Table, TableStyle
from pypdf import PdfReader, PdfWriter
import tempfile

ROOT = Path(__file__).resolve().parent
FIG = ROOT / 'figures'
subprocess.run(['dot', '-Tsvg', str(FIG/'classification.dot'), '-o', str(FIG/'classification.svg')], check=True)
subprocess.run(['dot', '-Tpdf', str(FIG/'classification.dot'), '-o', str(FIG/'classification.pdf')], check=True)
subprocess.run(['dot', '-Tpng', '-Gdpi=70', str(FIG/'classification.dot'), '-o', str(FIG/'classification.png')], check=True)
r = int(json.loads((ROOT/'fixtures/b163.json').read_text())['subgroup_order'])
a,b=1,0
rows=[]
for g in range(65):
    bound=a+math.isqrt(2*b*b)
    rows.append({'genus':g,'exact_integer_upper_bound':str(bound),'excludes_r':bound<r})
    a,b=3*a+4*b,2*a+3*b
(FIG/'calculated-bound.json').write_text(json.dumps({'q':2,'r':str(r),'scope':'exact calculated bounds, not attack costs or measurements','rows':rows},indent=2)+'\n')
fig,ax=plt.subplots(figsize=(7,3.5))
ax.plot([x['genus'] for x in rows],[math.log2(int(x['exact_integer_upper_bound'])) for x in rows],label='log2(exact integer Weil upper bound)',color='#28648c')
ax.axhline(math.log2(r),label='log2(B-163 subgroup order)',color='#a03b2e',linestyle='--')
ax.axvline(63,color='#777777',linestyle=':',label='last excluded genus: 63')
ax.set(xlabel='Target genus over F2',ylabel='log2(group size)',title='Calculated obstruction; no solver-cost claim')
ax.legend(fontsize=8,loc='upper left');ax.grid(alpha=.2);fig.tight_layout()
for ext in ['svg','png','pdf']:fig.savefig(FIG/f'weil-bound.{ext}',dpi=85)
plt.close(fig)
pdfmetrics.registerFont(TTFont('AuditSans',str(Path(matplotlib.get_data_path())/'fonts/ttf/DejaVuSans.ttf')))
styles=getSampleStyleSheet()
for style in styles.byName.values():style.fontName='AuditSans'
styles['BodyText'].fontSize=9;styles['BodyText'].leading=12
story=[]
for source in ['REPORT.md','THEOREMS.md']:
    if story:story.append(PageBreak())
    paragraph=[]
    table=[]
    def flush():
        if paragraph:
            story.append(Paragraph(html.escape(' '.join(paragraph)),styles['BodyText']))
            story.append(Spacer(1,5));paragraph.clear()
        if table:
            rows=[[Paragraph(html.escape(c.strip()),styles['BodyText']) for c in row.strip('|').split('|')] for row in table if not row.startswith('|---')]
            widths=[6.8*inch/len(rows[0])]*len(rows[0])
            item=Table(rows,colWidths=widths,repeatRows=1)
            item.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#edf2f7')),('GRID',(0,0),(-1,-1),.3,colors.lightgrey),('VALIGN',(0,0),(-1,-1),'TOP')]))
            story.append(item);story.append(Spacer(1,8));table.clear()
    for line in (ROOT/source).read_text().splitlines():
        if not line.strip():flush();continue
        if line.startswith('|'):
            if paragraph:flush()
            table.append(line);continue
        if table:flush()
        if line.startswith('#'):
            flush();level=len(line)-len(line.lstrip('#'));story.append(Paragraph(html.escape(line.lstrip('# ').strip()),styles['Title' if level==1 else 'Heading2']));continue
        if line.startswith('!['):
            flush();story.append(Paragraph('Vector figures follow the theorem text; editable SVG and DOT are retained.',styles['BodyText']));continue
        paragraph.append(line)
    flush()
with tempfile.TemporaryDirectory() as temp:
    body=Path(temp)/'body.pdf'
    SimpleDocTemplate(str(body),pagesize=(8.5*inch,11*inch),leftMargin=.7*inch,rightMargin=.7*inch,topMargin=.6*inch,bottomMargin=.6*inch,title='Binary transfer classification and obstruction audit').build(story)
    writer=PdfWriter()
    for file in [body,FIG/'classification.pdf',FIG/'weil-bound.pdf']:writer.append(PdfReader(file))
    writer.add_metadata({'/Title':'Binary transfer classification and obstruction audit'})
    with (ROOT/'REPORT.pdf').open('wb') as output:writer.write(output)
assert (ROOT/'REPORT.pdf').stat().st_size<=65536,'report exceeds artifact data threshold'
for svg in FIG.glob('*.svg'):svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
print('rendered vector report/PDF and editable/vector figures')
