#!/usr/bin/env python3
"""Render all frozen contrasts; no timing selection or qualification decisions."""
import argparse,json,statistics
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
p=argparse.ArgumentParser();p.add_argument('--claim',required=True);p.add_argument('--job',required=True);p.add_argument('--conclusion',default='Unsigned exploratory measurements; qualification remains null.');args=p.parse_args()
a=json.loads((P/'analysis-fresh.json').read_text());replay=json.loads((P/'independent-arithmetic-fresh.json').read_text());states=json.loads((P/'independent-states-fresh.json').read_text());post=json.loads((P/'analysis-post-profile.json').read_text())
assert all(x['status']=='pass' for x in [a,replay,states,post])
focus=['vs_anchor','storage_inverse','combined_inverse'];titles=['Anchor / compact inverse','Coefficient / compact inverse','Direct / compact inverse']
plt.rcParams.update({'svg.fonttype':'none','font.size':9,'axes.spines.top':False,'axes.spines.right':False})
for key,name,title in [('through_cleanup_contrasts','native-primary','Context + pipeline through owned oracle cleanup'),('contrasts','native-collector','Collector through owned collector / matrix cleanup'),('table_setup_contrasts','native-setup','Pair-table preparation (charged in primary interval)')]:
 fig,axes=plt.subplots(1,3,figsize=(10,3.6))
 for ax,k,label in zip(axes,focus,titles):
  vals=[c[key][k] for c in a['cases']];xs=[c['n'] for c in a['cases']]
  ax.vlines(xs,[v['bootstrap95'][0] for v in vals],[v['bootstrap95'][1] for v in vals],color='#28777d')
  ax.scatter(xs,[v['median'] for v in vals],color='#28777d',s=22)
  ax.axhline(1,ls='--',lw=1,color='#b78444');ax.set_xticks(xs);ax.set_xlabel('Field degree');ax.set_ylabel('Reference / compact time');ax.set_title(label,fontsize=9);ax.grid(axis='y',alpha=.15)
 fig.suptitle(title,fontsize=11);fig.tight_layout()
 for ext in ['svg','png']:fig.savefig(P/(name+'.'+ext),dpi=180)
 plt.close(fig)
styles=getSampleStyleSheet();story=[];md=[]
def para(s,style='BodyText'):
 md.extend([s,'']);story.extend([Paragraph(escape(s),styles[style]),Spacer(1,9)])
def img(name):
 w,h=ImageReader(str(P/name)).getSize();story.extend([Image(str(P/name),width=520,height=520*h/w),Spacer(1,9)])
def table(rows,widths):story.extend([Table(rows,colWidths=widths,style=[('FONTSIZE',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]),Spacer(1,8)])
def ratio(c,window,name,digits=4):
 v=c[window][name];return f"{v['median']:.{digits}f} [{v['bootstrap95'][0]:.{digits}f},{v['bootstrap95'][1]:.{digits}f}]"
def focus_table(window):table([['Field','A / PI','CI / PI','DI / PI']]+[[f"N{c['n']}",*[ratio(c,window,k) for k in focus]] for c in a['cases']],[35,158,158,159])
def page(title):story.append(PageBreak());para(title,'Heading1')
para('Compact exact pair-table witnesses','Title')
para(f"{args.claim}; unsigned producer data, qualificationnull. Job{args.job};210same-target blocks,42points perfield, seven methods/four immutable binaries. [pcc:unverified]")
para(args.conclusion+' [pcc:unverified]')
para(f"Existing Python arithmetic replays {replay['pipeline_answers']} IC, {replay['rho_answers']} same-point rho and {replay['aa_answers']} A/A answers; {states['checks']} preflight states. All {len(a['aa_failed_rows'])} failed A/A controls and {a['capped_arms']} capped IC arms remain in the data. [pcc:unverified]")
para('Primary ratios include context plus execution through owned oracle cleanup. Values above1 favor the denominator. Paired medians/10000-resample pointwise95% intervals use seed20261116 and linear quantiles; intervals containing1 remain inconclusive. Full-process cold and setup-reused rho costs remain open. No cross-panel ratios are multiplied. [pcc:unverified]')
img('native-primary.png');focus_table('through_cleanup_contrasts')
para('Legend: A=anchor ordinary; DO/DI=direct ordinary/inverse; CO/CI=coefficient ordinary/inverse; PO/PI=compact ordinary/inverse. CI/PI isolates the storage change against the coefficient source. DI/PI measures its combined effect against the direct control. All thirteen contrasts are retained in the appendices. [pcc:unverified]')
page('Table preparation and observed process memory')
img('native-setup.png');focus_table('table_setup_contrasts')
table([['Field','A ms','DO','DI','CO','CI','PO','PI']]+[[f"N{c['n']}",*[f"{1000*c['methods'][m]['mean_table_setup_s']:.3f}" for m in MODES]] for c in a['cases']],[35]+[68]*7)
rr=[['Field','Direct inv. MiB','Coeff. inv. MiB','Compact inv. MiB']]
for c in a['cases']:
 row=[f"N{c['n']}"]
 for m in [MODES[2],MODES[4],MODES[6]]:
  vals=[r['methods'][m]['peak_rss_kib'] for r in a['rows'] if r['index']==c['index']]
  row.append(f"{statistics.mean(vals)/1024:.3f}" if all(v is not None and v>0 for v in vals) else 'unknown')
 rr.append(row)
table(rr,[35,158,158,159])
para('Setup table shows arithmetic means in milliseconds; RSS table shows means of complete-child GNUtime peak RSS in MiB, including startup/reporting. This is not heap-allocation telemetry. Entry payload is8bytes versus16bytes, excluding control metadata, allocation rounding and other pipeline memory. No setup subtraction or amortization changes the primary interval. [pcc:unverified]')
page('Collector and matched same-point references')
img('native-collector.png');focus_table('contrasts')
table([['Field','A ms','DO','DI','CO','CI','PO','PI']]+[[f"N{c['n']}",*[f"{1000*c['methods'][m]['mean_context_plus_computation_s']:.3f}" for m in MODES]] for c in a['cases']],[35]+[68]*7)
table([['Field','Plain rho / PI','Negation rho / PI']]+[[f"N{c['n']}",*[f"{c['methods'][MODES[6]]['median_context_rho_over_pipeline'][k]:.5f}" for k in ['rho-plain','rho-negation']]] for c in a['cases']],[35,238,238])
para('Millisecond table: primary arithmetic means. Reference table: medians of paired context-plus-reference compute / compact-inverse primary cost. Rho uses direct9f, original arithmetic, exact same Q/G/r/seed and fresh processes. Setup-reused precomputation rho remains open. Ratios describe only these declared intervals and points. [pcc:unverified]')
page('Exact representation, controls and instruction evidence')
img('storage-flow.png')
para('Selection checks degree1..31, at most65536points and canonical finite coordinates. Exact u32 keys and packed u16 indices preserve ordered first witnesses; wider shapes retain the original map. Out-of-range lookup keys cannot alias. Hash primitive dispatch follows the same mixing rule. Width selection is outside the per-pair flush loop; calibration probes real buckets. [pcc:unverified]')
table([['Field','Attempted blocks','Failed A/A','Ratio min','Ratio max']]+[[f"N{c['n']}",str(c['attempted']),str(c['aa_failures']),f"{min(r['aa_ratio'] for r in a['rows'] if r['index']==c['index']):.5f}",f"{max(r['aa_ratio'] for r in a['rows'] if r['index']==c['index']):.5f}"] for c in a['cases']],[35,110,100,125,125])
para('All failed controls are retained individually in analysis-fresh.json and the raw triples.json; none are filtered from these intervals. Frozen A/A band0.85..1.15; all source/routing/semantic setup/query/group/rank/row/work checks must pass. Only the two explicit physical storage counters and existing inverse-vector physical counters are excluded from count equality, with positive-use checks instead. [pcc:unverified]')
table([['Post-timing path','Whole-guest Ir','Hot wide-remainder calls']]+[[r['method'],str(r['ir']),str(sum(e['calls'] for e in r['walker_wide_remainder_edges']))] for r in post['rows']],[160,175,175])
para('Post-timing fixed-development captures preserve the original point/calibration/tool hashes and check actual compact use. Generic m2 dispatcher and hot coefficient wide-remainder calls remain absent. Whole-guest instruction totals include startup/reporting and are separate from native clocks or hardware retirement; they do not measure cache misses. [pcc:unverified]')
page('Reproduction and claim boundaries')
para('Fresh fixtures540..581; fourteen balanced seven-method orders repeated3. Each method position and ordered adjacent pair occurs6times perfield. One CUDA-host allocation: L4/4CPU/8GiB/900s, CPU arithmetic pinned to one allowed CPU, controller780s, child12s, preflight30s and8GiB native virtual cap. No observer subprocess runs during timing. Physical placement and memory technology/speed/channels remain unknown. No GPU arithmetic throughput is measured. [pcc:unverified]')
for name in ['anchor-input.json','prepared-input.json','coefficient-input.json','optimized-input.json']:
 b=json.loads((P/name).read_text());para(f"{name}: binary {b['binary_sha256']}; source {b['source_commit']}; preparation {b['source_job']}. [pcc:unverified]")
ids=json.loads((P/'fresh-identities.json').read_text())
for i,inst in enumerate(json.loads((P/'instances.json').read_text())):
 base=ids[str(i)]['archive'];para(f"{inst['curve_id']}; r={inst['curve']['subgroup_order']}; base dimension{inst['dimension']}, columns{base['effective_columns']}; base SHA256{base['factor_base_sha256']}. [pcc:unverified]")
para('The compact binary reconstructs the exact admitted coefficient tree, overlaying only ic_boundary.rs, batch_mitm.rs and the probe example. Compiler, environment, source root and build arguments are matched. Full source snapshot and overlay/controller bytes are admitted against the actual job Git revision. The coefficient control retains its explicit historical source-label erratum; no old receipt is rewritten. Local tests/Clippy claim022145 and native175maps/25compact/15loader/6walker2full1const27framework3inverse3compact/2560states claimf8ca33 are unsigned. [pcc:unverified]')
para('All raw captures, per-file SHA/URI bundles, independent arithmetic outputs and failed controls are archived using the scoped crypto-autoresearcher/us-west-2/default route before record closure. Root legacy configuration and CI credential/proof checksum issues remain separate. No qualified promotion, broad-field, asymptotic or mathematical-novelty assertion. The plots describe distinct registered fields, not an asymptotic scaling result. [pcc:unverified]')
labels=['A/PI','CO/PO','CI/PI','DO/PO','DI/PI','PO/PI','CO/CI','DO/DI','DO/CO','DI/CI','A/PO','A/CO','A/DO']
assert len(labels)==len(CONTRASTS)==13
for window,title in [('through_cleanup_contrasts','All primary paired contrasts'),('contrasts','All collector paired contrasts'),('table_setup_contrasts','All table-setup paired contrasts')]:
 page(title)
 para('Ratios are reference / candidate, median[95% pointwise interval]. A anchor; D direct; C coefficient; P compact; O ordinary and I SIMD inverse. All42rows perfield remain in each comparison. [pcc:unverified]')
 rows=[['Contrast',*[f"N{c['n']}" for c in a['cases']]]]
 for label,(name,_,_) in zip(labels,CONTRASTS):rows.append([label,*[ratio(c,window,name,3) for c in a['cases']]])
 table(rows,[70]+[88]*5)
 for label,(name,reference,candidate) in zip(labels,CONTRASTS):para(f"{label}: {name}; {reference} / {candidate}. [pcc:unverified]")
(P/'REPORT.md').write_text('# Compact exact pair-table witnesses\n\n'+'\n'.join(md)+'\n![Primary](native-primary.svg)\n\n![Setup](native-setup.svg)\n\n![Collector](native-collector.svg)\n')
SimpleDocTemplate(str(P/'REPORT.pdf'),pagesize=A4,leftMargin=36,rightMargin=36,topMargin=30,bottomMargin=30).build(story)
print(json.dumps({'report':'REPORT.pdf','status':'rendered'}))
