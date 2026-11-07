"""Render the source-linked conditional proof report; no experiment executes."""
from pathlib import Path
from html import escape
import subprocess
import reportlab
import fitz
import tempfile
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,PageBreak,Table,TableStyle,Flowable
HERE=Path(__file__).resolve().parent
subprocess.run(['dot','-Tsvg',str(HERE/'implication.dot'),'-o',str(HERE/'implication.svg')],check=True)
figure_bytes=subprocess.check_output(['dot','-Tpdf',str(HERE/'implication.dot')])
figure_document=fitz.open(stream=figure_bytes,filetype='pdf')
figure_rect=figure_document[0].rect
figure_positions=[]
class VectorFigure(Flowable):
    def __init__(self):
        super().__init__()
        scale=min(6.5*inch/figure_rect.width,5.2*inch/figure_rect.height)
        self.width=figure_rect.width*scale;self.height=figure_rect.height*scale
    def draw(self):
        x,y=self.canv.absolutePosition(0,0)
        figure_positions.append((self.canv.getPageNumber()-1,x,y,self.width,self.height))
fonts=Path(reportlab.__file__).resolve().parent/'fonts'
pdfmetrics.registerFont(TTFont('ReportSans',str(fonts/'Vera.ttf')))
pdfmetrics.registerFont(TTFont('ReportSansBold',str(fonts/'VeraBd.ttf')))
styles=getSampleStyleSheet()
for style in styles.byName.values():
    if hasattr(style,'fontName'):style.fontName='ReportSansBold' if 'Bold' in style.fontName else 'ReportSans'
styles.add(ParagraphStyle(name='SmallNote',fontName='ReportSans',fontSize=8,leading=11,textColor=colors.HexColor('#475569')))
def p(text,style='BodyText'):return Paragraph(escape(text),styles[style])
story=[p('Corrected bounded-witness implication','Title'),p('Xedni proof correction | 30 October 2026','SmallNote'),Spacer(1,12)]
story += [p('Exact issue and correction','Heading2'),p('The historical statement bounds every nontrivial relation by a fixed B. Scaling any nonzero relation violates that bound, so the hypothesis already implies independence. The corrected hypothesis says that if a relation exists, some nontrivial bounded witness exists. The witness can differ from the original relation.'),Spacer(1,8),p('Conditional implication and open bridge','Heading2')]
story += [VectorFigure(),Spacer(1,8),p('Orange identifies an explicit mathematical hypothesis, not a proved height bridge. Native verification of the new five-theorem source is pending. The sealed original build is not validation of this successor.','SmallNote'),PageBreak()]
story += [p('Written argument and proof map','Title'),p('Let rho: H -> G be an additive homomorphism and let a lifted tuple reduce to the fixed tuple downstairs. Suppose a nontrivial lifted relation exists. The bounded-witness hypothesis supplies another nontrivial lifted relation with every coefficient at most B in absolute value. Reduction preserves its coefficients, giving a forbidden bounded relation downstairs. This proves the conditional exclusion. For all compatible lifts, the hypothesis is supplied for each tuple using the same B; the chosen witness may vary.'),Spacer(1,10),p('Controls against the original circular hypothesis','Heading2'),p('The dependent zero tuple has a nontrivial witness bounded by one. The same tuple has nontrivial relations beyond every fixed bound. These two controls distinguish existence of a bounded witness from a universal bound on all relations.'),Spacer(1,10)]
rows=[['Declaration','Current status']]+[[name,'Implemented; native check pending'] for name in ['relation_reduces','no_dependent_lift','all_compatible_lifts_blocked','zero_tuple_has_bounded_witness','zero_tuple_has_unbounded_relations']]
table=Table([[p(x,'SmallNote') for x in row] for row in rows],colWidths=[3.3*inch,3.1*inch]);table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e2e8f0')),('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#cbd5e1')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]));story += [table,Spacer(1,12),p('Evidence and remaining obligations','Heading2'),p('Source: formal/WitnessObstruction.lean. Toolchain: leanprover/lean4:v4.35.0-rc4. Mathlib: 021c46bdd042f67b538b9f9871d556a93713a9a9. All five declarations request a foundation audit. Dependency hashes bind inputs and do not attest a completed build. The original sealed bundle remains byte-exact.'),p('Primary source: Jacobson et al., Analysis of the Xedni Calculus Attack, sections 3-4, Lemma 4.1; https://pages.cpsc.ucalgary.ca/~jacobs/PDF/xedni.pdf. The lemma supplies a witness under height/discriminant and Lang assumptions; that height bridge and the actual curve-selection distribution remain open. No new experiment, general impossibility or performance claim is made.'),p('Canonical graph review: this proof correction changes no curve, measured row, atlas status or performance edge. Editable diagram: implication.dot; full written report: RESULT.md.','SmallNote')]
temporary=tempfile.TemporaryDirectory()
draft=Path(temporary.name)/'draft.pdf'
SimpleDocTemplate(str(draft),pagesize=(612,792),leftMargin=50,rightMargin=50,topMargin=42,bottomMargin=42,title='Corrected bounded-witness implication').build(story)

with fitz.open(draft) as document:
    for page,x,y,width,height in figure_positions:
        sheet=document[page]
        sheet.show_pdf_page(fitz.Rect(x,sheet.rect.height-y-height,x+width,sheet.rect.height-y),figure_document,0)
    document.save(HERE/'report.pdf',deflate=True,garbage=4)
figure_document.close()
temporary.cleanup()
