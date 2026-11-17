#!/usr/bin/env python3
"""Render every frozen contrast and failed control without granting standing."""
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
parser=argparse.ArgumentParser();parser.add_argument('--claim',required=True);parser.add_argument('--job',required=True);parser.add_argument('--conclusion',required=True);args=parser.parse_args()
a=json.loads((P/'analysis-fresh.json').read_text());ar=json.loads((P/'independent-arithmetic-fresh.json').read_text());st=json.loads((P/'independent-states-fresh.json').read_text());post=json.loads((P/'analysis-post-profile.json').read_text());pr=json.loads((P/'independent-replay-post-profile.json').read_text())
assert all(x['status']=='pass' for x in [a,ar,st,post,pr])
focus=['vs_anchor','packed_indexed_ordinary','packed_indexed_inverse'];titles=['Anchor / indexed inverse','Packed / indexed ordinary','Packed / indexed inverse']
windows=[('through_cleanup_contrasts','native-primary','Context + execution through owned oracle cleanup'),('table_setup_contrasts','native-setup','Pair-table preparation (included in primary)'),('contrasts','native-collector','Collector through owned collector/matrix cleanup')]
plt.rcParams.update({'svg.fonttype':'none','font.size':9,'axes.spines.top':False,'axes.spines.right':False})
for window,name,title in windows:
 fig,axes=plt.subplots(1,3,figsize=(10,3.5))
 for ax,k,label in zip(axes,focus,titles):
  values=[c[window][k] for c in a['cases']];xs=[c['n'] for c in a['cases']]
  ax.vlines(xs,[v['bootstrap95'][0] for v in values],[v['bootstrap95'][1] for v in values],color='#28777d');ax.scatter(xs,[v['median'] for v in values],color='#28777d',s=20)
  ax.axhline(1,ls='--',lw=1,color='#b78444');ax.set_xticks(xs);ax.set_xlabel('Field degree');ax.set_ylabel('Reference / candidate time');ax.set_title(label,fontsize=9);ax.grid(axis='y',alpha=.15)
 fig.suptitle(title,fontsize=11);fig.tight_layout()
 for ext in ['svg','png']:
  target=P/(name+'.'+ext);fig.savefig(target,dpi=180)
  if ext=='svg':target.write_text('\n'.join(line.rstrip() for line in target.read_text().splitlines())+'\n')
 plt.close(fig)
styles=getSampleStyleSheet();story=[];md=[]
def para(s,style='BodyText'):
 md.extend([s,'']);story.extend([Paragraph(escape(s),styles[style]),Spacer(1,8)])
def img(name):
 w,h=ImageReader(str(P/name)).getSize();story.extend([Image(str(P/name),width=520,height=520*h/w),Spacer(1,8)])
def table(rows,widths):
 story.extend([Table(rows,colWidths=widths,repeatRows=1,style=[('FONTSIZE',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]),Spacer(1,8)]);md.extend([' | '.join(map(str,row)) for row in rows]);md.append('')
def ratio(c,w,k):
 v=c[w][k];return f"{v['median']:.4f} [{v['bootstrap95'][0]:.4f},{v['bootstrap95'][1]:.4f}]"
def focus_table(w):table([['Field','A / II','PO / IO','PI / II']]+[[f"N{c['n']}",*[ratio(c,w,k) for k in focus]] for c in a['cases']],[35,158,158,159])
def page(title):story.append(PageBreak());para(title,'Heading1')
para('Index-driven pair preparation','Title');para(f"{args.claim}; unsigned exploratory producer data. Job {args.job}; 210 same-target blocks, 42 points per field, seven logical methods/four immutable binaries. Qualification remains null. [pcc:unverified]");para(args.conclusion+' [pcc:unverified]')
para(f"Existing independent Python arithmetic checks {ar['pipeline_answers']} IC, {ar['rho_answers']} matched-rho, {ar['aa_answers']} A/A answers and {st['checks']} exported states. All {len(a['aa_failed_rows'])} failed A/A controls and {a['capped_arms']} capped IC arms are retained. [pcc:unverified]")
para('Ratios above1 favor the denominator. Paired medians and 10000-resample pointwise95% intervals use seed20261116/linear quantiles; all42rows perfield remain. No pooling, filtering or cross-panel products. Primary includes context through owned oracle cleanup; prior fixture/calibration/spec/empty allocation, startup/JSON and later context/report destruction are excluded. Full-process cold remains open. [pcc:unverified]')
img('native-primary.png');focus_table('through_cleanup_contrasts');para('A=anchor ordinary; CO/CI=compact ordinary/inverse; PO/PI=packed ordinary/inverse; IO/II=indexed ordinary/inverse. PO/IO and PI/II isolate index-driven preparation; compact control comparisons remain in the full contrast table. [pcc:unverified]')
page('Table preparation and process memory');img('native-setup.png');focus_table('table_setup_contrasts')
table([['Field','A ms','CO','CI','PO','PI','IO','II']]+[[f"N{c['n']}",*[f"{1000*c['methods'][m]['mean_table_setup_s']:.3f}" for m in MODES]] for c in a['cases']],[35]+[68]*7)
rss=[['Field','Packed inv. MiB','Indexed inv. MiB']]
for c in a['cases']:
 row=[f"N{c['n']}"]
 for m in [MODES[4],MODES[6]]:
  vals=[r['methods'][m]['peak_rss_kib'] for r in a['rows'] if r['index']==c['index']];row.append(f"{statistics.mean(vals)/1024:.3f}" if all(v is not None and v>0 for v in vals) else 'unknown')
 rss.append(row)
table(rss,[35,238,238]);para('Setup costs and complete-child GNUtime peak RSS are arithmetic means. RSS includes startup/reporting and is not heap-allocation telemetry. Compact, packed and indexed representations have identical compact8byte entry payloads, excluding control metadata/rounding. No setup subtraction/amortization changes the primary interval. [pcc:unverified]')
page('Collector and matched same-point references');img('native-collector.png');focus_table('contrasts')
table([['Field','A ms','CO','CI','PO','PI','IO','II']]+[[f"N{c['n']}",*[f"{1000*c['methods'][m]['mean_context_plus_computation_s']:.3f}" for m in MODES]] for c in a['cases']],[35]+[68]*7)
table([['Field','Plain rho / PI','Negation rho / PI']]+[[f"N{c['n']}",*[f"{c['methods'][MODES[6]]['median_context_rho_over_pipeline'][k]:.5f}" for k in ['rho-plain','rho-negation']]] for c in a['cases']],[35,238,238]);para('Millisecond table: primary arithmetic means. References: medians of paired context-plus-rho compute / indexed-inverse primary cost on the exact same Q/G/r/seed. Original rho arithmetic in the compact baseline; fresh processes. Setup-reused rho remains open. [pcc:unverified]')
page('Exact change and separate development instruction evidence');img('kernel-flow.png')
para('The indexed path retains the bounded witness-index buffer and reads each four-lane group from the immutable base, avoiding the two full-point chunk buffers. Pair and chunk order, first witnesses, hash/storage and previous packed-constant arithmetic remain unchanged. Public guards remain; exceptions/tails use cached scalar fallback. Native complete maps, indexed pair totals and SIMD counts are mandatory; local ARM checks do not execute the native indexed kernel. [pcc:unverified]')
receipt=json.loads((P/'build-001/receipt.json').read_text())
insts=json.loads((P/'instances.json').read_text())
table([['Field','Indexed','Combined','Constant','All packed']]+[[str(insts[i]['field']['degree']),str(r['indexed_prepare_pairs']),str(r['vector_const_packed_square_pairs']),str(r['vector_const_pairs']),str(r['vector_packed_square_pairs'])] for i,r in enumerate(receipt['native_table_smoke'])],[40,120,110,120,120])
para('These are source-reported pair counters across the preparation map comparisons. Indexed totals include fallback lanes and require the index-driven preparation path to execute and do not measure hardware retirement or native throughput. The scalar/native complete maps must agree exactly. [pcc:unverified]')
table([['Path','Whole-guest Ir','Generic dispatcher Ir','Hot wide rem. calls']]+[[r['method'],str(r['ir']),str(r['generic_dispatch_exclusive_ir']),str(sum(e['calls'] for e in r['walker_wide_remainder_edges']))] for r in post['rows']],[90,140,140,140])
para(f"Preparation development profiles replay {pr['answer_checks']} answers/{pr['state_checks']} states against original pinned calibration/tools/point/work. They precede fresh timing and are not native clocks, hardware retirement or cache measurements. Existing scalar/group arithmetic replay and full disassembly are retained. [pcc:unverified]")
table([['Field','Attempted','Failed A/A','Ratio min','Ratio max']]+[[f"N{c['n']}",str(c['attempted']),str(c['aa_failures']),f"{min(r['aa_ratio'] for r in a['rows'] if r['index']==c['index']):.5f}",f"{max(r['aa_ratio'] for r in a['rows'] if r['index']==c['index']):.5f}"] for c in a['cases']],[35,100,100,137,138]);para('A/A band0.85..1.15; every failed row is listed in the final appendix and raw JSON. All rows remain in intervals. [pcc:unverified]')
page('Reproduction and limits')
para('Fixtures642..683; fourteen Williams orders repeated3. Each method position and ordered adjacent pair occurs6times perfield. One L4/4CPU/8GiB/900s allocation; CPU arithmetic pinned to one allowed CPU. Controller780s, child12s/preflight30s,8GiB native virtual cap. No observer subprocess while timing; physical placement and memory technology/speed/channels unknown. No GPU arithmetic throughput measured. [pcc:unverified]')
for n in ['anchor-input.json','prepared-input.json','packed-input.json','optimized-input.json']:
 b=json.loads((P/n).read_text());para(f"{n}: binary {b['binary_sha256']}; source {b['source_commit']}; preparation {b['source_job']}. [pcc:unverified]")
ids=json.loads((P/'fresh-identities.json').read_text())
for i,inst in enumerate(json.loads((P/'instances.json').read_text())):
 b=ids[str(i)]['archive'];para(f"{inst['curve_id']}; r={inst['curve']['subgroup_order']}; base dimension{inst['dimension']}, columns{b['effective_columns']}; base SHA256{b['factor_base_sha256']}. [pcc:unverified]")
para('Reconstruction pins the original source archive, coefficient and compact overlays, then the four declared sources change. All16source hashes are admitted, with exact four-file deltas against compact and packed controls and matching compiler/root/environment. Prior packed-candidate failures and all earlier evidence remain separate in the parent study. No fresh data or failed control is discarded. [pcc:unverified]')
para('All raw captures, per-file SHA/URI bundles and independent checks are archived via scoped default/us-west-2/crypto-autoresearcher before record closure. Root legacy storage and separate CI credential/proof checksum issues remain separate. No qualified promotion, complete-cold, broad-field, asymptotic or mathematical-novelty assertion. The full requested performance goal remains open. [pcc:unverified]')
page('Every predeclared paired contrast')
labels=['A/II','CO/IO','CI/II','PO/IO','PI/II','IO/II','PO/PI','CO/CI','A/IO'];assert len(labels)==len(CONTRASTS)==9
for w,_,title in windows:
 para(title,'Heading2');table([['Contrast',*[f"N{c['n']}" for c in a['cases']]]]+[[label,*[ratio(c,w,k) for c in a['cases']]] for label,(k,_,_) in zip(labels,CONTRASTS)],[60]+[90]*5)
para('Ratios are reference/candidate paired medians[pointwise95% intervals], all42rows perfield. A anchor; C compact; P packed; I indexed; O ordinary/I inverse. [pcc:unverified]')
page('All failed A/A controls retained')
if a['aa_failed_rows']:table([['Field index','Fixture','A/A ratio']]+[[str(r['index']),str(r['fixture']),f"{r['ratio']:.9f}"] for r in a['aa_failed_rows']],[120,160,230])
else:para('No failed A/A controls in this allocation. [pcc:unverified]')
para('No failed control is discarded or replaced. Qualification remains null; raw records and benchmark invalid status preserve exploratory standing. [pcc:unverified]')
(P/'REPORT.md').write_text('# Index-driven pair preparation\n\n'+'\n'.join(md)+'\n![Primary](native-primary.svg)\n\n![Setup](native-setup.svg)\n\n![Collector](native-collector.svg)\n')
SimpleDocTemplate(str(P/'REPORT.pdf'),pagesize=A4,leftMargin=36,rightMargin=36,topMargin=30,bottomMargin=30).build(story)
print(json.dumps({'status':'rendered','report':'REPORT.pdf'}))
