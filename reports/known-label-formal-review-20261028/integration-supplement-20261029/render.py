from pathlib import Path
import hashlib
import html
import json
from reportlab import rl_config
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics import renderSVG
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

root = Path(__file__).resolve().parent
rl_config.invariant = True
styles = getSampleStyleSheet()
styles['BodyText'].fontSize = 9
styles['BodyText'].leading = 12
styles['Heading1'].fontSize = 16
styles['Heading1'].leading = 19
styles['Heading2'].fontSize = 11
styles['Heading2'].leading = 14
d = Drawing(475, 95)
for y, color, title, subtitle in [
    (64, '#dcefe3', 'Historical native proof: passed', '0b353c9bf; four unchanged ring identities'),
    (32, '#dcefe3', 'Integrated verifier software review: holds within limits', '5b20d2a; 26 existing tests and 46 independent mock cases'),
    (0, '#fff0cc', 'Final native CI and elaborated-type review: still open', 'No broad cryptanalysis, performance or full-task completion claim'),
]:
    d.add(Rect(0,y,475,30,fillColor=colors.HexColor(color),strokeColor=colors.HexColor('#666666')))
    d.add(String(8,y+18,title,fontName='Helvetica-Bold',fontSize=9))
    d.add(String(8,y+6,subtitle,fontName='Helvetica',fontSize=8))
flow=[]
for b in (root/'report.md').read_text().strip().split('\n\n'):
    style='BodyText'
    if b.startswith('# '): b=b[2:];style='Heading1'
    elif b.startswith('## '): b=b[3:];style='Heading2'
    flow.append(Paragraph(html.escape(b),styles[style]))
    flow.append(Spacer(1,5))
    if style=='Heading1': flow.extend([d,Spacer(1,8)])
doc=SimpleDocTemplate(str(root/'report.pdf'),pagesize=(595.28,841.89),leftMargin=60,rightMargin=60,topMargin=38,bottomMargin=35,title='Known-label integration supplement',author='Validation continuation')
doc.build(flow)
renderSVG.drawToFile(d,str(root/'proof-boundary.svg'))
names=['report.md','render.py','report.pdf','proof-boundary.svg','independence-integration.json']
(root/'render-receipt.json').write_text(json.dumps({'schema':'review-render/v1','dependencies':'reportlab4.4.10','files':{n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in names}},indent=2)+'\n')
