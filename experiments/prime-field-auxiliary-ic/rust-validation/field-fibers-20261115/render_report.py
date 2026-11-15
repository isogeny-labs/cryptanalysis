"""Render the source-count figure and this report; no benchmark is executed."""
import html,json,re,subprocess
from pathlib import Path
from reportlab.graphics import renderSVG
from reportlab.graphics.shapes import Drawing,Rect,String
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from svglib.svglib import svg2rlg
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,Preformatted,Table,TableStyle,KeepTogether

folder=Path(__file__).resolve().parent
pdfmetrics.registerFont(TTFont('DejaVu','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
subprocess.run(['dot','-Tsvg',str(folder/'pipeline.dot'),'-o',str(folder/'pipeline.svg')],check=True)
svg_path=folder/'pipeline.svg'
svg_path.write_text(svg_path.read_text().replace('font-family="DejaVu Sans"','font-family="DejaVu"'))
subprocess.run(['dot','-Tpng','-Gdpi=72',str(folder/'pipeline.dot'),'-o',str(folder/'pipeline.png')],check=True)
x=json.loads((folder/'source-operations.json').read_text())['terminal']
d=Drawing(500,165)
d.add(String(0,150,'Terminal evaluation: source multiplication calls',fontName='DejaVu',fontSize=11))
for i,(label,key) in enumerate([('Old general','old_general'),('Split general','new_general'),('Split opposite','new_opposite'),('Split unit opposite','new_unit_opposite')]):
 y=120-i*28;v=x[key]
 d.add(String(0,y,label,fontName='DejaVu',fontSize=10))
 d.add(Rect(145,y-2,29*v,15,fillColor=colors.HexColor('#357b8e'),strokeColor=None))
 d.add(String(153+29*v,y,str(v),fontName='DejaVu',fontSize=10))
d.add(String(0,0,'Derived counts; excludes setup and initialization. No timings.',fontName='DejaVu',fontSize=9))
renderSVG.drawToFile(d,str(folder/'operations.svg'))
styles=getSampleStyleSheet()
for key in ['Normal','BodyText','Title','Heading1','Heading2','Heading3']:
 styles[key].fontName='DejaVu' if key.startswith('Heading') or key=='Title' else 'DejaVu'
 styles[key].fontSize=10 if key in ['Normal','BodyText'] else styles[key].fontSize
 styles[key].leading=14 if key in ['Normal','BodyText'] else styles[key].leading
 styles[key].spaceAfter=7
styles['Code'].fontSize=7;styles['Code'].leading=10

def prose(s):
 s=html.escape(s)
 s=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',lambda m:'<link color="#246b82" href="'+m[2]+'">'+m[1]+'</link>',s)
 return s.replace('`','')
lines=(folder/'REPORT.md').read_text().splitlines();story=[];i=0
while i<len(lines):
 line=lines[i]
 if not line.strip():i+=1;continue
 if line.startswith('```'):
  code=[];i+=1
  while i<len(lines) and not lines[i].startswith('```'):code.append(lines[i]);i+=1
  story.append(Preformatted('\n'.join(code),styles['Code']));i+=1;continue
 if line.startswith('!['):
  diagram=svg2rlg(str(folder/'pipeline.svg'));ratio=min(500/diagram.width,320/diagram.height)
  diagram.scale(ratio,ratio);diagram.width*=ratio;diagram.height*=ratio;story.append(diagram)
  i+=1;continue
 if line.startswith('|'):
  rows=[]
  while i<len(lines) and lines[i].startswith('|'):
   cells=lines[i].strip('|').split('|')
   if not all(re.fullmatch(r'[:\-\s]+',c) for c in cells):rows.append([Paragraph(prose(c.strip()),styles['BodyText']) for c in cells])
   i+=1
  t=Table(rows,colWidths=[160,340] if len(rows[0])==2 else None,repeatRows=1,hAlign='LEFT')
  t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e6f0f4')),('GRID',(0,0),(-1,-1),0.3,colors.lightgrey),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5)]))
  story.extend([t,Spacer(1,10)]);continue
 if line.startswith('#'):
  level=len(line)-len(line.lstrip('#'));story.append(Paragraph(prose(line.lstrip('# ')),styles['Title' if level==1 else 'Heading2']))
  if line=='## Source-operation audit':story.extend([d,Spacer(1,12)])
  i+=1;continue
 paragraph=[line];i+=1
 while i<len(lines) and lines[i].strip() and not lines[i].startswith(('#','|','```','![')):
  paragraph.append(lines[i]);i+=1
 story.append(Paragraph(prose(' '.join(paragraph)),styles['BodyText']))
def footer(canvas,doc):
 canvas.setFont('DejaVu',8);canvas.drawString(44,23,'Auxiliary IC field fibers · unsigned producer report · timing unestablished')
 canvas.drawRightString(550,23,str(doc.page))
SimpleDocTemplate(str(folder/'REPORT.pdf'),pagesize=(595,842),leftMargin=44,rightMargin=44,topMargin=40,bottomMargin=42,title='Compiled field fibers and terminal factors').build(story,onFirstPage=footer,onLaterPages=footer)
