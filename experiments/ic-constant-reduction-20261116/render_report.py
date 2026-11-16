#!/usr/bin/env python3
"""Render retained paired data; never qualify a performance result."""
import argparse,json
from pathlib import Path
from xml.sax.saxutils import escape
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,Image,PageBreak

P=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--job',required=True);parser.add_argument('--claim',required=True);args=parser.parse_args()
a=json.loads((P/'analysis.json').read_text());replay=json.loads((P/'independent-arithmetic-timing001.json').read_text());prep=json.loads((P/'prepared-input-amended.json').read_text())
instances=json.loads((P/'instances.json').read_text());ids=json.loads((P/'identities.json').read_text())
cases=a['cases'];modes=['mitm-walk16-vector-narrow','mitm-walk16-vector-const']
plt.rcParams.update({'svg.fonttype':'none','font.size':9,'axes.spines.top':False,'axes.spines.right':False})
fig,axes=plt.subplots(1,3,figsize=(10,3.5))
for ax,key,title in zip(axes,['setup_included','table_setup','collector'],['Context + pipeline cleanup (primary)','Table setup','Collector through owned cleanup']):
 selected=[c for c in cases if key in c['contrasts']]
 y=[c['contrasts'][key]['median'] for c in selected];err=[[v-c['contrasts'][key]['bootstrap95'][0] for v,c in zip(y,selected)],[c['contrasts'][key]['bootstrap95'][1]-v for v,c in zip(y,selected)]]
 ax.errorbar([c['n'] for c in selected],y,yerr=err,fmt='o',color='#246b81',capsize=3)
 ax.axhline(1,color='#a57d39',ls='--',lw=1);ax.set_xticks([c['n'] for c in cases]);ax.set_title(title,fontsize=9);ax.set_xlabel('Field degree');ax.set_ylabel('Dynamic / constant time (ratio)');ax.grid(axis='y',alpha=.15)
fig.tight_layout()
for ext in ['svg','png']:fig.savefig(P/f'ratios.{ext}',dpi=180)
plt.close(fig)
rows=[];cost=[]
for c in cases:
 def ratio(k):
  v=c['contrasts'].get(k)
  return '-' if v is None else f"{v['median']:.4f} [{v['bootstrap95'][0]:.4f}, {v['bootstrap95'][1]:.4f}]"
 rows.append([f"N{c['n']}",ratio('setup_included'),ratio('table_setup'),ratio('collector'),str(c['aa_failures'])])
 if 'methods' in c:
  cost.append([f"N{c['n']}",*[f"{1000*c['methods'][m]['mean_context_plus_computation_s']:.3f}" for m in modes],*[f"{c['methods'][modes[1]]['median_context_rho_over_setup_included'][r]:.4f}" for r in ['rho-plain','rho-negation']]])
claim=f'[pcc:unverified] {args.claim}; unsigned exploratory controls and analysis, qualificationnull.'
text=[
 ('Constant-polynomial SIMD reduction in index calculus','Title'),
 (claim,'BodyText'),
 (f"Job {args.job}; {len(a['rows'])} paired targets, {replay['pipeline_answers']} IC and {replay['rho_answers']} rho producer invocations of existing independent Python scalar arithmetic. Analysis status {a['status']}. Native binary {prep['binary_sha256']}, prepared source {prep['source_commit']}.",'BodyText'),
 ('Exact same archived base, table first witnesses, ordinary-PCLMUL table backend and vector16 query law. The candidate specializes degree and polynomial at compile time; the control retains runtime reduction. Ratio above1 means lower candidate time. Per-field medians and paired10000-resample95% intervals, seed20261116 and linear quantiles. All attempted rows and failed controls remain.','BodyText'),
 ('What the comparison includes','Heading1'),
 ('Primary: context construction plus run_pipeline through explicit oracle destruction, including reusable base/table preparation, target-dependent collector/matrix/scalar group check and owned cleanup. Prior spec/empty-oracle allocation, inputs/fixture, calibration, startup, JSON and later context/report destruction are excluded. This is not complete-process cold time. Collector and table setup diagnostics are separate; no subtractive repricing or cross-study ratio multiplication.','BodyText'),
 ('The millisecond table reports arithmetic means; ratio rows are paired medians. Native [d]G=Q is inside compute; fixture scalar equality is outside as a harness input control. Existing Python replay is outside native intervals with its own elapsed and CPU receipt. Plain and negation rho use the same Q/G/subgroup/seed in separate fresh processes; context-plus-reference compute is compared with the primary setup-included interval. These are supplementary scoped ratios, not a complete cold or reused-precomputation-rho conclusion.','BodyText'),
 ('Controls, reproducibility and remaining work','Heading1'),
 (f"Failed A/A controls {len(a['aa_failed_rows'])}; capped IC arms {a['capped_arms']}. A/A brackets ordinary-narrow fixture0, threshold0.85..1.15. No filtering, host selection, cap extension or target tuning. Both arms retain exact query/row/rank/work/semantic-operation checks and actual vector/preparation counters.",'BodyText'),
 ('Source/protocol25be1116c published before fixtures432..455. Exact candidates/workloads live in identities.json and ic-bench manifests. Prepared bindings and exact source-job metadata precede timing. First kernel preparation150833-4f87 and its binary51a949de are retained separately; the comparison-interface amendment has its own build002/bindings. Earlier2pass1stale validation-test failure remains; its corrected supported3/4 and rejected5 tests are recorded with the source.','BodyText'),
 ('One L4CPU4/8GiB900s allocation; CPU arithmetic, one allowed CPU pinned, controller780s, child12s/preflight30s,8GiB virtual cap. Host/cgroup/affinity/GNU wall/CPU/RSS/fault receipts remain distinct from unknown physical placement, memory technology/speed/channels and unavailable hardware counters. No observer subprocess during target timing.','BodyText'),
 ('Evidence: PROTOCOL.md, NATIVE_AMENDMENT.md, run_prepared.py, analyze.py, scalar and preflight-state replays, immutable raw outputs and lossless SHA/URI bundle. Raw upload completes before benchmark-record closure. All numbers remain unsigned and invalid for promotion; PCC custody fork is retained without rewrite or waiver. No default, mathematical, GPU-throughput or larger-field conclusion. Broad optimization remains active.','BodyText'),
 ('Next: inspect measured setup-inclusive and collector intervals separately, retain null/negative fields, then use instruction attribution to select the next isolated kernel. Batch-inverse products are a separately scoped followup. Sources: owning koblitz_fast.rs, ic_boundary.rs and ic_framework/batch_mitm.rs; preceding vector-query instruction report; KB/atlas receipts in DEVELOPMENT.md. Canonical curve catalog and volcano/isogeny-route graph sources have no changed mathematical facts.','BodyText')
]
md=['# '+text[0][0],'',claim,'',*sum(([t+' [pcc:unverified]',''] for t,s in text[2:]),[]),'| Field | Primary dynamic / constant | Table setup | Collector | A/A failures |','|---|---:|---:|---:|---:|',*['| '+' | '.join(r)+' |' for r in rows],'','![Paired costs](ratios.svg)','','![Same-target flow](flow.svg)']
(P/'REPORT.md').write_text('\n'.join(md)+'\n')
md += ['','## Exact curve and base scope','']
for i,inst in enumerate(instances):
 row=ids[str(i)]['archive'];md += [inst['curve_id']+'; r='+str(inst['curve']['subgroup_order'])+'; dimension='+str(inst['dimension'])+'; columns='+str(row['effective_columns'])+'; base SHA256='+row['factor_base_sha256']+' [pcc:unverified]','']
(P/'REPORT.md').write_text('\n'.join(md)+'\n')
styles=getSampleStyleSheet();story=[]
for i,(t,style) in enumerate(text):
 if i in [4,7]:story.append(PageBreak())
 story += [Paragraph(escape(t),styles[style]),Spacer(1,9)]
 if i==3:
  story += [Image(str(P/'ratios.png'),width=520,height=182),Spacer(1,8),Table([['Field','Primary','Table setup','Collector','A/A']]+rows,colWidths=[33,151,151,151,24],style=[('FONTSIZE',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)])]
 if i==4:
  iw,ih=ImageReader(str(P/'flow.png')).getSize();story += [Image(str(P/'flow.png'),width=520,height=520*ih/iw),Spacer(1,9)]
 if i==6:story += [Table([['Field','Dynamic ms','Constant ms','Plain rho / IC','Neg. rho / IC']]+cost,colWidths=[45,100,100,125,125],style=[('FONTSIZE',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),7)])]
story += [PageBreak(),Paragraph('Exact curve and base scope',styles['Heading1']),Spacer(1,10)]
for i,inst in enumerate(instances):
 row=ids[str(i)]['archive'];detail=inst['curve_id']+'; subgroup r='+str(inst['curve']['subgroup_order'])+'; dimension='+str(inst['dimension'])+'; columns='+str(row['effective_columns'])+'; geometric points='+str(row['fb_points'])+'; archived base SHA256 '+row['factor_base_sha256']
 story += [Paragraph(escape(detail),styles['BodyText']),Spacer(1,12)]
story += [Paragraph(escape(claim),styles['BodyText'])]
SimpleDocTemplate(str(P/'REPORT.pdf'),pagesize=A4,leftMargin=36,rightMargin=36,topMargin=30,bottomMargin=30).build(story)
print(json.dumps({'pdf':str(P/'REPORT.pdf'),'claim':args.claim}))
