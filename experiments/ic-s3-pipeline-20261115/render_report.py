#!/usr/bin/env python3
"""Render complete matrix coverage with raw ratios and every capped arm."""
import json
import argparse
from pathlib import Path
import statistics
import sys
import subprocess
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,Table,TableStyle,PageBreak
from PIL import Image as PILImage

HERE=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--analysis-stem',default='analysis');parser.add_argument('--stem',default='REPORT');parser.add_argument('--chart-tag',default='');args=parser.parse_args()
assert args.analysis_stem.replace('-','').isalnum() and args.stem.replace('-','').isalnum()
assert not args.chart_tag or args.chart_tag.replace('-','').isalnum()
analysis=json.loads((HERE/(args.analysis_stem+'.json')).read_text())
rows=analysis['rows'];cases=analysis['cases']
methods=['buchberger-f2','f4-f2','fes-f2-wide','mitm']
labels=['Buchberger','F4','Wide FES','MITM']
for fmt in ['svg','png']:subprocess.run(['dot','-T'+fmt,str(HERE/'flow.dot'),'-o',str(HERE/('flow.'+fmt))],check=True)
if not rows:
 styles=getSampleStyleSheet()
 size=PILImage.open(HERE/'flow.png').size
 story=[Paragraph('Fixed-instance IC panel: build cap',styles['Title']),
        Paragraph('The reference release build reached its330-second limit. The process group was terminated and the allocation exited1 after330.7seconds. No algorithm arm or rho reference ran.',styles['BodyText']),Spacer(1,12),
        Paragraph('The frozen N15/N18 curves, archived bases, candidate identities and twelve target workloads remain intact. This is a censored infrastructure attempt; no IC performance ratio follows. The next step separates bounded compilation and binary hashing from the timing allocation.',styles['BodyText']),Spacer(1,12),
        Image(str(HERE/'flow.png'),width=10.5*inch,height=10.5*inch*size[1]/size[0]),Spacer(1,12),
        Paragraph('Sources: run-001/reference-build.log, host.json, summary.json, PROTOCOL.md, immutable candidate/workload manifests, and analysis.json. Independent prefix-base rebuilds match native points and labels. Timing qualification and the broad optimization objective remain open.',styles['BodyText'])]
 SimpleDocTemplate(str(HERE/(args.stem+'.pdf')),pagesize=(11.7*inch,8.3*inch),leftMargin=28,rightMargin=28,topMargin=28,bottomMargin=28).build(story)
 sys.exit(0)
fig,axes=plt.subplots(1,2,figsize=(10.6,3.7),sharey=True)
for index,ax in enumerate(axes):
 for i,method in enumerate(methods):
  selected=[r for r in rows if r['index']==index and r['method']==method and r['valid_paired_answers']]
  values=[r['raw_cold_ratio'] for r in selected]
  if values:ax.scatter([i+(j-2.5)*.045 for j in range(len(values))],values,color='#27688b',s=23)
  if len(values)==6:ax.hlines(statistics.median(values),i-.25,i+.25,color='#222',linewidth=2)
  ax.text(i,.03,f'{len(values)}/6 pairs',ha='center',fontsize=8,transform=ax.get_xaxis_transform())
 ax.axhline(1,color='#ad5936',linestyle='--');ax.set_xticks(range(4),labels);ax.set_title(['N15: 58 points / 29 columns','N18: 134 points / 67 columns'][index]);ax.grid(axis='y',alpha=.2)
axes[0].set_ylabel('Raw context + pipeline reference/direct ratio')
fig.suptitle('All completed paired answers; bars only when all six frozen pairs finish',fontsize=10)
fig.tight_layout()
for suffix in ['png','svg']:fig.savefig(HERE/('ratios'+args.chart_tag+'.'+suffix),dpi=180)
plt.close(fig)
fig,axes=plt.subplots(1,2,figsize=(10.6,3.7),sharey=True)
for index,ax in enumerate(axes):
 for i,method in enumerate(methods):
  selected=[r for r in rows if r['index']==index and r['method']==method]
  for variant,offset,color in [('reference',-.15,'#73899a'),('direct',.15,'#27688b')]:
   values=[r[variant]['cold_wall_s'] for r in selected if r[variant]['verified']]
   if values:ax.scatter([i+offset]*len(values),values,color=color,s=17,label=variant if i==0 else None)
  capped=sum(r[v]['exit_code']==124 for r in selected for v in ['reference','direct'])
  if capped:ax.text(i,.96,f'{capped} caps',ha='center',va='top',fontsize=8,transform=ax.get_xaxis_transform())
 rho={}
 for row in rows:
  if row['index']==index and 'cold_wall_gap_to_matched_rho' in row['reference']:
   rho[row['fixture']]=row['reference']['cold_wall_s']/row['reference']['cold_wall_gap_to_matched_rho']
 if len(rho)==6:ax.axhline(statistics.median(rho.values()),color='#222',linestyle=':',label='matched rho median')
 ax.set_yscale('log');ax.set_xticks(range(4),labels);ax.set_title(['N15','N18'][index]);ax.grid(axis='y',alpha=.2)
axes[0].set_ylabel('Raw context + pipeline seconds (completed answers)')
axes[0].legend(fontsize=8)
fig.suptitle('Absolute cost by tested method; cap counts remain explicit',fontsize=10)
fig.tight_layout()
for suffix in ['png','svg']:fig.savefig(HERE/('costs'+args.chart_tag+'.'+suffix),dpi=180)
plt.close(fig)
for name in ['ratios'+args.chart_tag+'.svg','costs'+args.chart_tag+'.svg']:
 p=HERE/name;p.write_text('\n'.join(x.rstrip() for x in p.read_text().splitlines())+'\n')
styles=getSampleStyleSheet()
story=[Paragraph('Direct S3 in fixed-instance index calculus',styles['Title']),Paragraph('Producer diagnostic; timing qualification and broad performance objective remain open',styles['BodyText']),Spacer(1,10)]
paras=[
'This panel tests the optional direct-coefficient constructor inside the actual IC framework. The same-source reference uses the generic symbolic builder. Both include the corrected symbolic-descent/system-packing charges. The reference controls are Buchberger, F4, wide FES and negation-folded MITM on exactly the same public curve, base and target.',
'Inputs reuse exact registered N15 and N18 curves, including their generators. Prefix bases contain 58 and 134 rational points and have 29 and 67 sign-folded columns. Independent pure-Python field/group arithmetic reproduces every sorted point and column label. The full rational lifts use prime-order cofactor-quotient logarithms; strict subgroup counts are 26 and 20, and neither base contains pure torsion.',
'Twelve frozen single-target workloads use fixtures100 through105. Every arm runs in a fresh process with the same target and walk seed. Each curve/target also has plain and negation-map rho runs. The attack interval includes field/curve context plus first run_pipeline execution, including base construction, oracle preparation, unsuccessful queries, solving, linear algebra and scalar verification. Input loading, planted-input generation and benchmark calibration are reported separately.',
'One L4 allocation requests four CPUs and 8 GiB, with a900-second hard cap. The workload runs on one pinned CPU. Each process has a 12-second deadline and the controller a 780-second limit. Binary preparation is separate and hash-pinned; no compiler runs in the timing allocation. Every failure, cap, unfinished reference and calibration excursion remains in the raw data. Known gVisor placement evidence is incomplete, all qualified values are null, and this record is invalid for promotion.'
]
for txt in paras:story.extend([Paragraph(txt,styles['BodyText']),Spacer(1,7)])
size=PILImage.open(HERE/'flow.png').size
story += [Image(str(HERE/'flow.png'),width=10.5*inch,height=10.5*inch*size[1]/size[0]),PageBreak(),Paragraph('Coverage and paired observations',styles['Heading1'])]
data=[['Curve','Method','Valid pairs / frozen','Capped arms','Raw cold median ratio']]
for c in cases:data.append([str([15,18][c['index']]),c['method'],f"{c['valid_pairs']}/6",str(c['capped_arms']),f"{c['raw_cold_median_ratio']:.4f}" if 'raw_cold_median_ratio' in c else 'partial: no headline'])
t=Table(data,colWidths=[55,160,160,100,240]);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e7eef4')),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),9),('GRID',(0,0),(-1,-1),.3,colors.lightgrey),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
story += [t,Spacer(1,8),Image(str(HERE/('ratios'+args.chart_tag+'.png')),width=10.6*inch,height=3.1*inch),Paragraph('Dots retain every completed pair. Medians require all six frozen pairs; partial completion does not become a headline ratio. A constructor gain for one method does not establish a gain over the best tested complete pipeline.',styles['BodyText']),PageBreak(),Paragraph('Cost and interpretation',styles['Heading1']),Image(str(HERE/('costs'+args.chart_tag+'.png')),width=10.6*inch,height=3.7*inch)]
for txt in [f"Run status: {analysis['run_status']}; completed pair records: {analysis['pairs']}; reference records: {analysis['references']}; producer recomputation status: {analysis['status']}. See the corresponding timing report and analysis file for same-target counted-S and wall-cost gaps, phase shares and calibration outcomes.",'All96 pipeline answers and24 rho answers also pass a producer invocation of the existing independent Python field/group implementation. One A/A bound failure and one large N18 MITM timing outlier remain in the raw data. Counted S uses the framework model. Context-inclusive counted S adds context time converted through this host addition calibration. Complete-interval wall-derived group equivalents are a separate quantity. These outputs have unsigned producer standing; neither inherits qualification from matching checksums or metadata gates.','Sources: immutable IC1 candidate and one-target workload manifests, PREPARED_TIMING_PROTOCOL.md, run_prepared.py, analyze.py, archived base recipes, raw timing-001 files and SHA-256 manifests. Source/input publication precedes timing. The whole optimization objective remains active pending a current-baseline full-phase improvement with appropriate verification and resource controls.']:
 story.extend([Paragraph(txt,styles['BodyText']),Spacer(1,8)])
SimpleDocTemplate(str(HERE/(args.stem+'.pdf')),pagesize=(11.7*inch,8.3*inch),leftMargin=28,rightMargin=28,topMargin=28,bottomMargin=28).build(story)
