#!/usr/bin/env python3
"""Render the frozen-anchor comparison without qualifying its measurements."""
import argparse,json
from pathlib import Path
from xml.sax.saxutils import escape
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.utils import ImageReader
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,Image,PageBreak
P=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--job',required=True);parser.add_argument('--claim',required=True);args=parser.parse_args()
a=json.loads((P/'analysis.json').read_text());replay=json.loads((P/'independent-arithmetic-timing001.json').read_text());prep=json.loads((P/'prepared-input.json').read_text());anchor=json.loads((P/'anchor-input.json').read_text());inst=json.loads((P/'instances.json').read_text());ids=json.loads((P/'identities.json').read_text())
M=['anchor-vector16-const','current-vector16-const','vector16-inverse'];keys=['vs_anchor','kernel','build_control'];labels=['Frozen anchor / candidate','Current control / candidate','Frozen anchor / current control']
plt.rcParams.update({'svg.fonttype':'none','font.size':9,'axes.spines.top':False,'axes.spines.right':False})
for kind,filename,title in [('through_cleanup_contrasts','primary','Context + pipeline through oracle cleanup'),('contrasts','collector','Collector through owned matrix/collector cleanup')]:
 fig,axes=plt.subplots(1,3,figsize=(10,3.6))
 for ax,key,label in zip(axes,keys,labels):
  selected=[c for c in a['cases'] if key in c.get(kind,{})];y=[c[kind][key]['median'] for c in selected]
  if selected:
   errors=[[v-c[kind][key]['bootstrap95'][0] for c,v in zip(selected,y)],[c[kind][key]['bootstrap95'][1]-v for c,v in zip(selected,y)]]
   ax.errorbar([c['n'] for c in selected],y,yerr=errors,fmt='o',color='#246b81',capsize=3)
  ax.axhline(1,color='#a57d39',ls='--',lw=1);ax.set_xticks([c['n'] for c in a['cases']]);ax.set_title(label,fontsize=9);ax.set_xlabel('Field degree');ax.set_ylabel('Reference / candidate time (ratio)');ax.grid(axis='y',alpha=.15)
 fig.suptitle(title,fontsize=11);fig.tight_layout()
 for ext in ['svg','png']:fig.savefig(P/f'{filename}.{ext}',dpi=180)
 plt.close(fig)
rows=[];cost=[];counts=[]
for c in a['cases']:
 def ratio(k):
  v=c.get('through_cleanup_contrasts',{}).get(k)
  return '-' if v is None else f"{v['median']:.4f} [{v['bootstrap95'][0]:.4f}, {v['bootstrap95'][1]:.4f}]"
 rows.append([f"N{c['n']}",*[ratio(k) for k in keys],str(c['aa_failures'])])
 if 'methods' in c:
  cost.append([f"N{c['n']}",*[f"{1000*c['methods'][m]['mean_context_plus_computation_s']:.3f}" for m in M],*[f"{c['methods'][M[2]]['median_context_rho_over_pipeline'][r]:.4f}" for r in ['rho-plain','rho-negation']]])
  rs=[r['methods'][M[2]]['query_counters'] for r in a['rows'] if r['index']==c['index']]
  counts.append([f"N{c['n']}",str(sum(r['walk_batch_inverse_vector_batches'] for r in rs)),str(sum(r['walk_batch_inverse_vector_elements'] for r in rs)),str(sum(r['walk_batch_inverse_vector_padded_lanes'] for r in rs))])
claim=f'[pcc:unverified] {args.claim}; unsigned exploratory producer analysis, qualificationnull.'
paras=[
 ('SIMD products in the shared inverse','Title'),
 (claim,'BodyText'),
 (f"Job {args.job}; {len(a['rows'])} triples of fresh fixtures456..479 across five fields. Existing independent Python arithmetic checks {replay['pipeline_answers']} target IC answers, {replay['rho_answers']} rho answers and {replay['aa_answers']} A/A control answers. Analysis status {a['status']}. All rows and controls retained.",'BodyText'),
 ('Primary ratios compare context plus pipeline execution through explicit oracle destruction. Frozen anchor / candidate measures against the previous binary; current control / candidate isolates the new inverse-product path; frozen anchor / current control exposes compiler/layout effects. Per-field paired medians,10000-resample95% intervals, seed20261116 and linear quantiles. Ratios above1 mean lower cost for the denominator method.','BodyText'),
 ('Identical target and schedule; exact cost boundaries','Heading1'),
 ('All three methods use the same Q/G/subgroup/seed, archived base, constant-polynomial table mode3 and vector16 query law. Initialization is unchanged. The candidate vectorizes products in the existing four accumulators, retains one scalar inverse tree, restores zeros and charges padded lanes. Unsupported CPU/field/noncanonical inputs and lengths outside8..16 retain the complete existing inverse. Full-point formulas, guards, restarts, caps, rows/rank and scalar group check remain.','BodyText'),
 ('Primary includes context construction, reusable base/table preparation, target-dependent setup, collector/matrix/group check and explicit oracle cleanup. Prior input/fixture/calibration/spec/empty-oracle allocation, startup/JSON and later context/report destruction are excluded. This is not complete-process cold time. Collector interval includes owned collector/matrix cleanup and is shown separately. Native group checking is inside compute; fixture equality is a harness check. Existing Python elapsed/CPU is outside native timing.','BodyText'),
 ('The millisecond table gives arithmetic means. Rho/IC columns are medians of paired context-plus-reference compute / context-plus-pipeline cleanup, on the exact same target and seed. Plain and negation rho use fresh processes and original arithmetic. Reused-setup precomputation-rho remains open. These scope-defined ratios are supplementary and do not establish a complete cold comparison.','BodyText'),
 ('Collector and actual inverse work','Heading1'),
 (f"Failed A/A controls {len(a['aa_failed_rows'])}; capped IC arms {a['capped_arms']}. All retained. Current-source ordinary-inverse fixture0 brackets each triple, allowed0.85..1.15. Scalar replay also checks those control answers and their public inputs are tied to the fixed preflight point. No host selection, filtering, cap extension or parameter tuning.",'BodyText'),
 ('Actual inverse counters distinguish request from execution and record batches, input elements and padded lanes. Point-vector counts and every other query/row/rank/work/semantic operation are audited across all three arms. The extra inverse counters are the only allowed semantic-signature exclusions. Raw per-target setup, collector, group/rank work, RSS and counter rows remain in analysis and captures.','BodyText'),
 ('Reproduction, curve/base scope and limits','Heading1'),
 (f"Candidate binary SHA256 {prep['binary_sha256']}, source {prep['source_commit']}, preparation {prep['source_job']}. Frozen anchor SHA256 {anchor['binary_sha256']}, source {anchor['source_commit']}, preparation {anchor['source_job']}. Separate receipt/job metadata hashes bind both binaries; host.json retains both toolchains. Source/protocol and exact candidate/workload manifests were published before target timings.",'BodyText'),
 ('Native preparation:175complete maps and15loader controls;5batched-walk/2full-point/1constant/27framework/3inverse test filters, with overlapping counts;58accepted inverse widths and valid-curve-point boundary controls. Five stream variants give four comparisons at512states per registered field. Existing Python replays2560exported coefficient states. Same-allocation preflight repeats both binaries and requires exact frame/group-operation agreement plus positive actual inverse execution.','BodyText'),
 ('One L4CPU4/8GiB900s allocation, CPU work pinned to one allowed CPU; controller780s, target child12s, preflight30s and8GiBvirtual cap. Host/cgroup/affinity/GNU wall/CPU/RSS/fault receipts retained. Physical placement, memory technology/speed/channels and unavailable hardware counters remain unknown. No observer subprocess during target timing. Raw captures are separately archived and losslessly bundled with per-file SHA/URI pins before record closure.','BodyText'),
 ('Known engineering on Montgomery batching already present in Gf2. All measurements remain exploratory/unsigned and invalid for promotion; no trusted performance signature. PCC custody fork retained without rewrite/waiver. No default promotion, mathematical novelty, GPU-throughput or larger-field conclusion. Sources: owning Gf2.batch_inv_body, Simd256, FastCurve, CountedGroup, BatchedWalker, the previous constant-reduction report and KB/atlas receipts in DEVELOPMENT.md. Canonical curve catalog and volcano/isogeny-route graph sources have no changed mathematical facts. Broad optimization remains active.','BodyText')]
md=['# '+paras[0][0],'',claim,'',*sum(([text+' [pcc:unverified]',''] for text,style in paras[2:]),[]),'| Field | Anchor / candidate primary | Current / candidate | Anchor / current | A/A |','|---|---:|---:|---:|---:|',*['| '+' | '.join(r)+' |' for r in rows],'','![Primary costs](primary.svg)','','![Collector](collector.svg)','','![Arithmetic flow](flow.svg)']
styles=getSampleStyleSheet();story=[]
def image(name,width=520):
 iw,ih=ImageReader(str(P/name)).getSize();return Image(str(P/name),width=width,height=width*ih/iw)
def table(data,widths):return Table(data,colWidths=widths,style=[('FONTSIZE',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)])
for i,(text,style) in enumerate(paras):
 if i in [4,8,11]:story.append(PageBreak())
 story += [Paragraph(escape(text),styles[style]),Spacer(1,9)]
 if i==3:story += [image('primary.png'),Spacer(1,8),table([['Field','Anchor / candidate','Current / candidate','Anchor / current','A/A']]+rows,[33,151,151,151,24])]
 if i==4:story += [image('flow.png'),Spacer(1,9)]
 if i==7:story += [table([['Field','Anchor ms','Current ms','Candidate ms','Plain rho / IC','Neg. rho / IC']]+cost,[35,85,85,95,105,105])]
 if i==8:story += [image('collector.png'),Spacer(1,8),table([['Field','Actual vector batches','Input elements','Padded lanes']]+counts,[40,160,160,150])]
for i,entry in enumerate(inst):
 row=ids[str(i)]['archive'];text=entry['curve_id']+'; r='+str(entry['curve']['subgroup_order'])+'; dimension='+str(entry['dimension'])+'; columns='+str(row['effective_columns'])+'; base SHA256 '+row['factor_base_sha256'];md += ['',text+' [pcc:unverified]'];story += [Paragraph(escape(text),styles['BodyText']),Spacer(1,8)]
(P/'REPORT.md').write_text('\n'.join(md)+'\n')
SimpleDocTemplate(str(P/'REPORT.pdf'),pagesize=A4,leftMargin=36,rightMargin=36,topMargin=30,bottomMargin=30).build(story)
print(json.dumps({'report':str(P/'REPORT.pdf'),'claim':args.claim}))
