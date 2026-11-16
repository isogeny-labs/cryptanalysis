"""Render the additive proof-admission note without rewriting earlier reports."""
import html,re
from pathlib import Path
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer
from svglib.svglib import svg2rlg
folder=Path(__file__).resolve().parent
pdfmetrics.registerFont(TTFont('DejaVu','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
styles=getSampleStyleSheet()
for name in ['Normal','Title']:
    styles[name].fontName='DejaVu'
styles['Normal'].fontSize=10;styles['Normal'].leading=14
story=[]
for block in (folder/'FORMAL_ADMISSION.md').read_text().split('\n\n'):
    if block.startswith('|'):
        block='\n'.join(line.replace('|',' · ') for line in block.splitlines() if '---' not in line)
    text=html.escape(' '.join(block.splitlines()).replace('`',''))
    text=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',lambda m:'<link href="'+m[2]+'" color="#246b82">'+m[1]+'</link>',text)
    story.extend([Paragraph(text.lstrip('# '),styles['Title' if block.startswith('#') else 'Normal']),Spacer(1,10)])
d=svg2rlg(str(folder/'pipeline.svg'));r=min(490/d.width,290/d.height);d.scale(r,r);d.width*=r;d.height*=r
story.extend([Paragraph('Implementation wiring is unchanged; no target-DLP transport edge is added.',styles['Normal']),d])
SimpleDocTemplate(str(folder/'FORMAL_ADMISSION.pdf'),leftMargin=44,rightMargin=44,topMargin=40,bottomMargin=40,title='Native field-fiber identity admission').build(story)
