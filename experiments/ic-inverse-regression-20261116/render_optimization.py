#!/usr/bin/env python3
"""Render the completed fixed-m2 native panel; never grant standing."""
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
from fresh_common import MODES,CONTRASTS
P=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--claim',required=True);parser.add_argument('--job',required=True);args=parser.parse_args()
a=json.loads((P/'analysis-fresh.json').read_text());replay=json.loads((P/'independent-arithmetic-fresh.json').read_text());states=json.loads((P/'independent-states-fresh.json').read_text());post=json.loads((P/'analysis-post-profile.json').read_text())
assert a['status']=='pass' and replay['status']=='pass' and states['status']=='pass' and post['status']=='pass'
focus=['vs_anchor','dispatch_ordinary','dispatch_inverse'];titles=['Anchor / patched inverse','Old / patched ordinary','Old / patched inverse']
plt.rcParams.update({'svg.fonttype':'none','font.size':9,'axes.spines.top':False,'axes.spines.right':False})
for key,name,title in [('through_cleanup_contrasts','native-primary','Context + pipeline through oracle cleanup'),('contrasts','native-collector','Collector through owned collector/matrix cleanup')]:
 fig,axes=plt.subplots(1,3,figsize=(10,3.6))
 for ax,k,label in zip(axes,focus,titles):
  values=[c[key][k] for c in a['cases']];y=[x['median'] for x in values]
  ax.errorbar([c['n'] for c in a['cases']],y,yerr=[[v-r['bootstrap95'][0] for v,r in zip(y,values)],[r['bootstrap95'][1]-v for v,r in zip(y,values)]],fmt='o',capsize=3,color='#28777d')
  ax.axhline(1,ls='--',lw=1,color='#b78444');ax.set_xticks([c['n'] for c in a['cases']]);ax.set_xlabel('Field degree');ax.set_ylabel('Reference / candidate time');ax.set_title(label,fontsize=9);ax.grid(axis='y',alpha=.15)
 fig.suptitle(title,fontsize=11);fig.tight_layout()
 for ext in ['svg','png']:fig.savefig(P/(name+'.'+ext),dpi=180)
 plt.close(fig)
styles=getSampleStyleSheet();story=[];md=[]
def para(text,style='BodyText'):
 md.extend([text,'']);story.extend([Paragraph(escape(text),styles[style]),Spacer(1,9)])
def img(name,width=520):
 w,h=ImageReader(str(P/name)).getSize();story.extend([Image(str(P/name),width=width,height=width*h/w),Spacer(1,9)])
def table(rows,widths):story.extend([Table(rows,colWidths=widths,style=[('FONTSIZE',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]),Spacer(1,8)])
def value(c,interval,k):
 d=c[interval][k];return f"{d['median']:.4f} [{d['bootstrap95'][0]:.4f}, {d['bootstrap95'][1]:.4f}]"
def contrast_table(interval,keys):
 table([['Field',*keys]]+[[f"N{c['n']}",*[value(c,interval,k) for k in keys]] for c in a['cases']],[30]+[480/len(keys)]*len(keys))
para('Restoring the fixed-two-summand query path','Title')
para(f"{args.claim}; unsigned exploratory producer data, qualificationnull. Job{args.job}. {len(a['rows'])} same-target blocks across five registered fields,30points per field, five methods and three immutable binaries. [pcc:unverified]")
para(f"Existing Python arithmetic checks {replay['pipeline_answers']} IC answers, {replay['rho_answers']} matched-rho answers and {replay['aa_answers']} A/A answers. It also checks {states['checks']} exported preflight states. All {len(a['aa_failed_rows'])} failed A/A controls and {a['capped_arms']} capped IC arms are retained. [pcc:unverified]")
para('Primary ratios include context construction and pipeline execution through explicit oracle cleanup. Ratios above1 mean lower denominator cost. Fieldwise paired medians and10000-resample95% intervals use frozen seed20261116 and linear quantiles. An interval containing1 remains inconclusive. No cross-panel ratios are multiplied. [pcc:unverified]')
img('native-primary.png');contrast_table('through_cleanup_contrasts',focus)
para('The source change replaces the fixed-two-summand oracle call through the general m=2/m=3 dispatcher with the same PairTable.probe and two-index witness allocation. Table preparation, arithmetic, state schedule, guards, caps, counters, matrix work and scalar group check are preserved. [pcc:unverified]')
story.append(PageBreak());para('Collector effect and matched references','Heading1');img('native-collector.png');contrast_table('contrasts',focus)
rows=[['Field','Anchor ms','Old ord.','Old inv.','New ord.','New inv.','Plain rho/IC','Neg. rho/IC']]
for c in a['cases']:
 m=c['methods'];rows.append([f"N{c['n']}",*[f"{1000*m[k]['mean_context_plus_computation_s']:.3f}" for k in MODES],*[f"{m[MODES[4]]['median_context_rho_over_pipeline'][k]:.4f}" for k in ['rho-plain','rho-negation']]])
table(rows,[30,65,65,65,65,65,77,78])
para('The millisecond columns are arithmetic means at the primary boundary; rho/IC columns are medians of paired context-plus-reference compute / patched-inverse primary time. Both rho variants use the frozen current binary, exact same Q/G/r/seed and fresh processes. Setup-reused precomputation-rho remains open. These intervals exclude process startup and later context/report destruction and do not establish a complete-process cold comparison. [pcc:unverified]')
story.append(PageBreak());para('All remaining contrasts and setup cost','Heading1')
other=[c[0] for c in CONTRASTS if c[0] not in focus]
para('patched_kernel = patched ordinary / patched inverse; old_kernel = old ordinary / old inverse; patched_ordinary_vs_anchor = anchor / patched ordinary; old_ordinary_vs_anchor = anchor / old ordinary. All paired intervals and every field are retained. [pcc:unverified]')
para('Primary interval','Heading2');contrast_table('through_cleanup_contrasts',other)
para('Collector interval','Heading2');contrast_table('contrasts',other)
table([['Field',*['Anchor','Old ord.','Old inv.','New ord.','New inv.']]]+[[f"N{c['n']}",*[f"{1000*c['methods'][m]['mean_table_setup_s']:.3f}" for m in MODES]] for c in a['cases']],[30,96,96,96,96,96])
para('Bottom table: mean pair-table preparation milliseconds. No setup subtraction is used to create an online result. Primary includes reusable base/table work, target-dependent collection, matrix/scalar check and owned cleanup; prior input/fixture/calibration/spec/empty-oracle allocation, startup/JSON and later context/report destruction are excluded. Collector has its own owned-cleanup boundary. [pcc:unverified]')
para('A/A failures: '+json.dumps(a['aa_failed_rows'],separators=(',',':'))+' [pcc:unverified]')
story.append(PageBreak());para('Instruction attribution and the focused fix','Heading1');img('profile-flow.png')
original=json.loads((P/'analysis-profile-001.json').read_text());postrows={r['method']:r for r in post['rows']}
table([['Path','Whole-guest Ir','Generic dispatcher Ir']]+[['Frozen anchor',str(original['totals']['anchor'][0]),'0']]+[[label,str(row['ir']),str(row['generic_dispatch_exclusive_ir'])] for label,row in [('Patched ordinary',postrows['current']),('Patched inverse',postrows['inverse'])]],[170,180,160])
para('The earlier frozen profile showed55,163 additional generic-dispatch calls in current/inverse paths,1,933,760 exclusive Ir absent from the anchor, while probe work was unchanged. The patched development captures test removal of that call layer. This is supplementary whole-guest instruction attribution, not native wall time, hardware retirement or the collector-only clock. [pcc:unverified]')
para('Post-timing profiles run only after every native row and A/A control finishes, on the original development point and fixed calibration. Compiler/environment match the frozen current receipt. The16-source manifest differs in exactly batch_mitm.rs. Binary/receipt/job/source hashes, actual CLI routing, public input identity and semantic query/rank/row/work counts are audited across all methods; only physical inverse-vector counters are excluded from count equality and are checked separately. [pcc:unverified]')
para('Original attribution claimPCC-20261117-1bc12f; local27framework tests/strict Clippy claim86dbb3; native175maps/15loader/overlapping5walker2full1constant27framework3inverse filters and2560Python states claima1d56d. These are unsigned producer invocations, without a trusted signed execution/performance verdict. [pcc:unverified]')
story.append(PageBreak());para('Reproduction, scope and limitations','Heading1')
para('Thirty fixtures480..509 per field, ten frozen orders repeated three times. Every method occupies every position six times per field, and every ordered adjacent method pair appears six times. Patched-ordinary fixture0 brackets each block with the unchanged0.85..1.15 A/A threshold. All failures remain in analysis. No target or host selection, filtering, cap extension or resampling. [pcc:unverified]')
for name in ['anchor-input.json','prepared-input.json','optimized-input.json']:
 b=json.loads((P/name).read_text());para(f"{name}: binary {b['binary_sha256']}; source {b['source_commit']}; preparation {b['source_job']}. [pcc:unverified]")
instances=json.loads((P/'instances.json').read_text());ids=json.loads((P/'fresh-identities.json').read_text())
for i,inst in enumerate(instances):
 row=ids[str(i)]['archive'];para(f"{inst['curve_id']}; r={inst['curve']['subgroup_order']}; base dimension{inst['dimension']}, columns{row['effective_columns']}, base SHA256 {row['factor_base_sha256']}. [pcc:unverified]")
para('One L4CPU4/8GiB900second allocation, CPU arithmetic pinned to one allowed CPU, controller780seconds, target children12seconds, preflight30seconds, native virtual cap8GiB. Host/cgroup/affinity/GNUtime/RSS/fault receipts are retained. Physical placement and memory technology/speed/channels remain unknown. Post-timing profiling has a separate bounded interval. All raw captures and a lossless per-file SHA/URI bundle are archived before closure. [pcc:unverified]')
para('All measurements remain exploratory/unsigned and invalid for promotion. No mathematical novelty, broader-field, GPU-throughput or asymptotic conclusion. The fields have distinct subgroup orders and bases; the plot is not an asymptotic scaling argument. Broad performance and independent-verification obligations remain open. Sources: FRESH_PROTOCOL.md, fresh_common.py, execution/analysis/replay scripts, native receipts, the original profile and the owning query implementation. [pcc:unverified]')
(P/'REPORT-optimization001.md').write_text('# Fixed-two-summand direct-probe comparison\n\n'+'\n'.join(md)+'\n![Primary](native-primary.svg)\n\n![Collector](native-collector.svg)\n')
SimpleDocTemplate(str(P/'REPORT-optimization001.pdf'),pagesize=A4,leftMargin=36,rightMargin=36,topMargin=30,bottomMargin=30).build(story)
print(json.dumps({'report':'REPORT-optimization001.pdf','status':'rendered'}))
