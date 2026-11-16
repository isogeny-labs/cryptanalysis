#!/usr/bin/env python3
"""Render all paired observations and preserved limitations."""
import json
from pathlib import Path
import statistics
import subprocess
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from PIL import Image as PILImage

HERE=Path(__file__).resolve().parent
summary=json.loads((HERE/'run-001/summary.json').read_text())
pairs=json.loads((HERE/'run-001/pairs.json').read_text()) if (HERE/'run-001/pairs.json').exists() else []
for fmt in ['svg','png']:
 subprocess.run(['dot','-T'+fmt,str(HERE/'flow.dot'),'-o',str(HERE/('flow.'+fmt))],check=True)
styles=getSampleStyleSheet()
story=[Paragraph('Direct S3 coefficient construction',styles['Title']),
 Paragraph('Producer stage evidence - 15 November 2026 - timing qualification remains open',styles['BodyText']),Spacer(1,12)]
paragraphs=[
'The optional Rust path replaces generic symbolic polynomial maps with the direct characteristic-two coefficient formula. It calculates each symmetric basis pair once and emits canonical masks directly. The reference is the current symbolic builder from the same source, using the same public descend API.',
'The recorded interval includes fresh field-context construction and the first equation build in a fresh process. Bare first-build time is secondary. These measurements exclude relation search, solving, lifting, linear algebra and final scalar verification. They cannot establish the total IC gain.',
'Validation: 140 ordered coefficient comparisons cover five field widths, seven basis dimensions and four random or degenerate variants. Seven symbolic tests pass with the default and optional paths, and two algebraic-oracle pipeline tests pass. The pinned Lean kernel check covers the coefficient identity and symmetry only. The separate repository axiom-audit helper failed to compile against the pinned Lean API; that failed attempt is retained. A dedicated audit of all five lemmas succeeds with only standard axioms.',
'The feature remains off by default. Symbolic descent and system-packing time are now charged in the framework for both arms, including failed queries. Earlier S values require fresh measurement under that accounting.',
'Host: one L4 allocation with four requested CPUs, 8 GiB and a 900-second cap; this is CPU work. Known gVisor placement evidence is incomplete. All qualified ratios remain null, and the benchmark is invalid for promotion. All calibration shifts and control regressions remain in the raw records.'
]
for txt in paragraphs:story.extend([Paragraph(txt,styles['BodyText']),Spacer(1,8)])
size=PILImage.open(HERE/'flow.png').size
story += [Image(str(HERE/'flow.png'),width=10.5*inch,height=10.5*inch*size[1]/size[0]),PageBreak(),Paragraph('Raw first-call observations',styles['Heading1'])]
if summary['status']=='exploratory_unqualified':
 cases=summary['cases']
 fig,axes=plt.subplots(1,2,figsize=(10.5,3.7),sharey=True)
 labels=[f"{c['n']}/{c['np']} S{c['summands']+1}" for c in cases]
 for ax,key,title in zip(axes,['raw_cold_ratio','raw_build_ratio'],['Context + first build','First build only']):
  for i,c in enumerate(cases):
   values=[p[key] for p in pairs if (p['n'],p['np'],p['summands'])==(c['n'],c['np'],c['summands'])]
   ax.scatter([i+(j-2.5)*.045 for j in range(len(values))],values,color='#25638c',s=24)
   ax.hlines(statistics.median(values),i-.25,i+.25,color='#222222',linewidth=2)
  ax.axhline(1,color='#ad5535',linestyle='--');ax.set_xticks(range(len(labels)),labels,rotation=18);ax.set_title(title);ax.grid(axis='y',alpha=.2)
 axes[0].set_ylabel('Raw reference / optional-path time ratio')
 fig.suptitle('Six fresh fixtures per case; final S4 case is an unchanged-path control',fontsize=10)
 fig.tight_layout();fig.savefig(HERE/'ratios.png',dpi=200);fig.savefig(HERE/'ratios.svg');plt.close(fig)
 svg=HERE/'ratios.svg';svg.write_text('\n'.join(x.rstrip() for x in svg.read_text().splitlines())+'\n')
 data=[['Field / basis / polynomial','Pairs','Cold median ratio','Build median ratio']]
 for c in cases:data.append([f"{c['n']} / {c['np']} / S{c['summands']+1}",str(c['pairs']),f"{c['raw_cold_median']:.4f}",f"{c['raw_build_median']:.4f}"])
 table=Table(data,colWidths=[220,60,180,180]);table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e7eef4')),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),9),('GRID',(0,0),(-1,-1),.3,colors.lightgrey),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
 story += [table,Spacer(1,10),Image(str(HERE/'ratios.png'),width=10.5*inch,height=3.7*inch),Spacer(1,8),Paragraph(f"{summary['pairs']} paired cases; coefficient checksums equal: {summary['all_checksums_equal']}; A/A calibration failures: {summary['calibration_failures']}. Dots retain every pair; bars are medians, not confidence intervals.",styles['BodyText'])]
else:story += [Paragraph('The bounded attempt did not complete: '+str(summary),styles['BodyText'])]
story += [Spacer(1,10),Paragraph('Sources: PROTOCOL.md, PROOF_MAP.md, S3Direct.lean, run_panel.py, raw run-001 output, native-001 logs and artifact SHA-256 manifests. Scientific statements are producer evidence without signed PCC standing.',styles['BodyText'])]
SimpleDocTemplate(str(HERE/'REPORT.pdf'),pagesize=(11.7*inch,8.3*inch),leftMargin=30,rightMargin=30,topMargin=30,bottomMargin=30).build(story)
