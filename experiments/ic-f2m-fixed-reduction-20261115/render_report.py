#!/usr/bin/env python3
"""Render retained raw component evidence; ratios are never timing-qualified."""
from pathlib import Path
import json
import subprocess
import statistics
import textwrap
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from PIL import Image as PillowImage
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak

HERE = Path(__file__).resolve().parent
rows = json.loads((HERE/'run-001/pairs.json').read_text())
summary = json.loads((HERE/'run-001/summary.json').read_text())
subprocess.run(['dot','-Tsvg',str(HERE/'flow.dot'),'-o',str(HERE/'flow.svg')],check=True)
subprocess.run(['dot','-Tpng','-Gdpi=170',str(HERE/'flow.dot'),'-o',str(HERE/'flow.png')],check=True)
fig, axes = plt.subplots(1,2,figsize=(10.5,4),sharey=True)
degrees = [113,131,155,163,233]
for ax,key,title in zip(axes,['raw_wall_ratio','reduction_wall_ratio'],['Default / combined','Six-product only / combined']):
    for i,degree in enumerate(degrees):
        values=[r[key] for r in rows if r['degree']==degree]
        ax.scatter([i+(j-2.5)*.045 for j in range(len(values))],values,s=24,color='#25638c')
        ax.hlines(statistics.median(values),i-.28,i+.28,color='#111111',linewidth=2)
    ax.axhline(1,color='#a95437',linestyle='--',linewidth=1)
    ax.set_xticks(range(5),[str(x) for x in degrees]);ax.set_xlabel('Field degree (113/233 are controls)')
    ax.set_title(title);ax.grid(axis='y',alpha=.2)
axes[0].set_ylabel('Raw paired wall-time ratio (higher = less candidate time)')
fig.suptitle('Exploratory component diagnostic: six fresh inputs per field; qualified values null',fontsize=11)
fig.tight_layout()
fig.savefig(HERE/'ratios.svg');fig.savefig(HERE/'ratios.png',dpi=200);plt.close(fig)
styles=getSampleStyleSheet();styles.add(ParagraphStyle(name='Small',fontName='Helvetica',fontSize=8,leading=11))
pdf=SimpleDocTemplate(str(HERE/'REPORT.pdf'),pagesize=(11.7*inch,8.3*inch),rightMargin=36,leftMargin=36,topMargin=30,bottomMargin=30)
story=[Paragraph('Bounded-product fixed two-fold reduction',styles['Title']),Paragraph('2026-11-15 - producer component evidence; performance goal remains open',styles['Small']),Spacer(1,10)]
body=[
'Question: does eliminating the generic high-word reduction walk lower complete field-multiplication cost on the same inputs? The three arms are current default, six-product multiplication, and six-product multiplication plus fixed reduction. This is arithmetic supporting ECC/IC, without a full attack comparison.',
'The reducer handles canonical degree 131, 155 and 163 polynomials. A masked product has degree at most 2m-2. With a one-word tail and m greater than 128, two folds finish reduction. Unsupported fields, polynomial representations and CPUs retain the generic reducer. The implementation remains opt-in.',
'Protocol: 30 triples, six fresh fixtures per field, all six backend orders, one million dependent public field multiplies per arm. Initial construction/check and checksum encoding are outside the interval; dispatch, scratch clearing, reduction and result handling are included. Before/after default calibrations use the frozen 0.85..1.15 bound.',
'Every qualified timing value remains null on the unprepared gVisor allocation. The benchmark record is invalid for promotion. Matching checksums and producer tests are consistency evidence, not signed execution standing. Retain all control shifts, failed calibrations and regressions.'
]
for t in body:story += [Paragraph(t,styles['BodyText']),Spacer(1,6)]
flow_size=PillowImage.open(HERE/'flow.png').size
story += [Paragraph('Producer arithmetic report: PCC-20261116-3717ba, unsigned and not covered by independent standing.',styles['Small']),Spacer(1,6),Image(str(HERE/'flow.png'),width=10.6*inch,height=10.6*inch*flow_size[1]/flow_size[0]),PageBreak(),Paragraph('Raw observations and scope',styles['Heading1'])]
data=[['Degree','Inputs','Default / combined median','Six-product / combined median']]
for case in summary['cases']:
 data.append([str(case['degree']),str(case['n']),f"{case['raw_median_ratio']:.6f}",f"{case['reduction_median_ratio']:.6f}"])
t=Table(data,colWidths=[75,60,230,230]);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e7eef4')),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,-1),7),('GRID',(0,0),(-1,-1),.3,colors.lightgrey)]));story += [t,Spacer(1,10),Image(str(HERE/'ratios.png'),width=10.5*inch,height=4*inch)]
for txt in ['Dots are all six individual paired ratios; black bars are medians. These are observations, not confidence intervals. Ratios below one remain in the data.', 'Sources: run-001/pairs.json, summary.json and host.json; launch receipt; PROTOCOL.md; REPORT.md. Their SHA-256 artifact manifests bind raw bytes. Historical smaller-field two-fold source: crypto docs/perf/RESULTS.md at d390e84ab2973372534120fc4207fb65e52d4f3f; KB source:4aeae310bd8926130ee38d08ce3d9da5. No historical timing ratio is transferred to this implementation.']:
 story += [Paragraph(txt,styles['Small']),Spacer(1,5)]
pdf.build(story)
