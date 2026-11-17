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
focus=['vs_anchor','output_ordinary','output_inverse'];titles=['Anchor / patched inverse','Compact / patched ordinary','Compact / patched inverse']
windows=[('through_cleanup_contrasts','native-primary','Context + execution through owned oracle cleanup'),('table_setup_contrasts','native-setup','Pair-table preparation (included in primary)'),('contrasts','native-collector','Collector through owned collector/matrix cleanup')]
plt.rcParams.update({'svg.fonttype':'none','font.size':9,'axes.spines.top':False,'axes.spines.right':False})
for window,name,title in windows:
 fig,axes=plt.subplots(1,3,figsize=(10,3.5))
 for ax,k,label in zip(axes,focus,titles):
  values=[c[window][k] for c in a['cases']];xs=[c['n'] for c in a['cases']]
  ax.vlines(xs,[v['bootstrap95'][0] for v in values],[v['bootstrap95'][1] for v in values],color='#28777d');ax.scatter(xs,[v['median'] for v in values],color='#28777d',s=20)
  ax.axhline(1,ls='--',lw=1,color='#b78444');ax.set_xticks(xs);ax.set_xlabel('Field degree');ax.set_ylabel('Reference / candidate time');ax.set_title(label,fontsize=9);ax.grid(axis='y',alpha=.15)
 fig.suptitle(title,fontsize=11);fig.tight_layout()
 for ext in ['svg','png']:fig.savefig(P/(name+'.'+ext),dpi=180)
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
def focus_table(w):table([['Field','A / PI','BO / PO','BI / PI']]+[[f"N{c['n']}",*[ratio(c,w,k) for k in focus]] for c in a['cases']],[35,158,158,159])
def page(title):story.append(PageBreak());para(title,'Heading1')
para('Specializing SIMD abscissa output','Title');para(f"{args.claim}; unsigned exploratory producer data. Job {args.job}; 150 same-target blocks, 30 points per field, five logical methods/three immutable binaries. Qualification remains null. [pcc:unverified]");para(args.conclusion+' [pcc:unverified]')
para(f"Existing independent Python arithmetic checks {ar['pipeline_answers']} IC, {ar['rho_answers']} matched-rho, {ar['aa_answers']} A/A answers and {st['checks']} exported states. All {len(a['aa_failed_rows'])} failed A/A controls and {a['capped_arms']} capped IC arms are retained. [pcc:unverified]")
para('Ratios above1 favor the denominator. Paired medians and 10000-resample pointwise95% intervals use seed20261116/linear quantiles; all30rows perfield remain. No pooling, filtering or cross-panel products. Primary includes context through owned oracle cleanup; prior fixture/calibration/spec/empty allocation, startup/JSON and later context/report destruction are excluded. Full-process cold remains open. [pcc:unverified]')
img('native-primary.png');focus_table('through_cleanup_contrasts');para('A=anchor ordinary; BO/BI=compact baseline ordinary/inverse; PO/PI=patched ordinary/inverse. BO/PO and BI/PI isolate the two output append replacements. [pcc:unverified]')
page('Table preparation and process memory');img('native-setup.png');focus_table('table_setup_contrasts')
table([['Field','A ms','BO','BI','PO','PI']]+[[f"N{c['n']}",*[f"{1000*c['methods'][m]['mean_table_setup_s']:.3f}" for m in MODES]] for c in a['cases']],[35]+[95]*5)
rss=[['Field','Baseline inv. MiB','Patched inv. MiB']]
for c in a['cases']:
 row=[f"N{c['n']}"]
 for m in [MODES[2],MODES[4]]:
  vals=[r['methods'][m]['peak_rss_kib'] for r in a['rows'] if r['index']==c['index']];row.append(f"{statistics.mean(vals)/1024:.3f}" if all(v is not None and v>0 for v in vals) else 'unknown')
 rss.append(row)
table(rss,[35,238,238]);para('Setup costs and complete-child GNUtime peak RSS are arithmetic means. RSS includes startup/reporting and is not heap-allocation telemetry. Baseline and patched representation are identical compact8byte entry payloads, excluding control metadata/rounding. No setup subtraction/amortization changes the primary interval. [pcc:unverified]')
page('Collector and matched same-point references');img('native-collector.png');focus_table('contrasts')
table([['Field','A ms','BO','BI','PO','PI']]+[[f"N{c['n']}",*[f"{1000*c['methods'][m]['mean_context_plus_computation_s']:.3f}" for m in MODES]] for c in a['cases']],[35]+[95]*5)
table([['Field','Plain rho / PI','Negation rho / PI']]+[[f"N{c['n']}",*[f"{c['methods'][MODES[4]]['median_context_rho_over_pipeline'][k]:.5f}" for k in ['rho-plain','rho-negation']]] for c in a['cases']],[35,238,238]);para('Millisecond table: primary arithmetic means. References: medians of paired context-plus-rho compute / patched-inverse primary cost on the exact same Q/G/r/seed. Original rho arithmetic in the compact baseline; fresh processes. Setup-reused rho remains open. [pcc:unverified]')
page('Exact change and separate development instruction evidence');img('output-flow.png')
para('Two normal-block statements change from extend(iterator.map(Some)) to extend_from_slice(array.map(Some)). Safe Rust preserves Option representation, vector output order and pre-existing prefix. Arithmetic, exceptional-pair group fallback and tails stay identical. Local tests are ARM-side evidence; native table positive controls exercise actual SIMD. [pcc:unverified]')
table([['Path','Whole-guest Ir','Generic dispatcher Ir','Hot wide rem. calls']]+[[r['method'],str(r['ir']),str(r['generic_dispatch_exclusive_ir']),str(sum(e['calls'] for e in r['walker_wide_remainder_edges']))] for r in post['rows']],[90,140,140,140])
para(f"Preparation development profiles replay {pr['answer_checks']} answers/{pr['state_checks']} states against original pinned calibration/tools/point/work. They precede fresh timing and are not native clocks, hardware retirement or cache measurements. Existing scalar/group arithmetic replay and full disassembly are retained. [pcc:unverified]")
table([['Field','Attempted','Failed A/A','Ratio min','Ratio max']]+[[f"N{c['n']}",str(c['attempted']),str(c['aa_failures']),f"{min(r['aa_ratio'] for r in a['rows'] if r['index']==c['index']):.5f}",f"{max(r['aa_ratio'] for r in a['rows'] if r['index']==c['index']):.5f}"] for c in a['cases']],[35,100,100,137,138]);para('A/A band0.85..1.15; every failed row is listed in the final appendix and raw JSON. All rows remain in intervals. [pcc:unverified]')
page('Reproduction and limits')
para('Fixtures582..611; ten Williams orders repeated3. Each method position and ordered adjacent pair occurs6times perfield. One L4/4CPU/8GiB/900s allocation; CPU arithmetic pinned to one allowed CPU. Controller780s, child12s/preflight30s,8GiB native virtual cap. No observer subprocess while timing; physical placement and memory technology/speed/channels unknown. No GPU arithmetic throughput measured. [pcc:unverified]')
for n in ['anchor-input.json','prepared-input.json','optimized-input.json']:
 b=json.loads((P/n).read_text());para(f"{n}: binary {b['binary_sha256']}; source {b['source_commit']}; preparation {b['source_job']}. [pcc:unverified]")
ids=json.loads((P/'fresh-identities.json').read_text())
for i,inst in enumerate(json.loads((P/'instances.json').read_text())):
 b=ids[str(i)]['archive'];para(f"{inst['curve_id']}; r={inst['curve']['subgroup_order']}; base dimension{inst['dimension']}, columns{b['effective_columns']}; base SHA256{b['factor_base_sha256']}. [pcc:unverified]")
para('Reconstruction pins original source archive, coefficient overlay and three compact overlays, then only koblitz_fast.rs changes. Sixteen manifest hashes, actual clean preparation Git revision, full snapshot/overlay bytes, compiler/environment/build path are admitted. The first local cache-path failure is retained; shared cache was not repaired. Local claim467209 is unsigned. [pcc:unverified]')
para('All raw captures, per-file SHA/URI bundles and independent checks are archived via scoped default/us-west-2/crypto-autoresearcher before record closure. Root legacy storage and separate CI credential/proof checksum issues remain separate. No qualified promotion, complete-cold, broad-field, asymptotic or mathematical-novelty assertion. The full requested performance goal remains open. [pcc:unverified]')
page('Every predeclared paired contrast')
labels=['A/PI','BO/PO','BI/PI','PO/PI','BO/BI','A/PO','A/BO'];assert len(labels)==len(CONTRASTS)==7
for w,_,title in windows:
 para(title,'Heading2');table([['Contrast',*[f"N{c['n']}" for c in a['cases']]]]+[[label,*[ratio(c,w,k) for c in a['cases']]] for label,(k,_,_) in zip(labels,CONTRASTS)],[60]+[90]*5)
para('Ratios are reference/candidate paired medians[pointwise95% intervals], all30rows perfield. A anchor; B compact baseline; P fixed-array-output patch; O ordinary/I inverse. [pcc:unverified]')
page('All failed A/A controls retained')
if a['aa_failed_rows']:table([['Field index','Fixture','A/A ratio']]+[[str(r['index']),str(r['fixture']),f"{r['ratio']:.9f}"] for r in a['aa_failed_rows']],[120,160,230])
else:para('No failed A/A controls in this allocation. [pcc:unverified]')
para('No failed control is discarded or replaced. Qualification remains null; raw records and benchmark invalid status preserve exploratory standing. [pcc:unverified]')
(P/'REPORT.md').write_text('# SIMD abscissa output specialization\n\n'+'\n'.join(md)+'\n![Primary](native-primary.svg)\n\n![Setup](native-setup.svg)\n\n![Collector](native-collector.svg)\n')
SimpleDocTemplate(str(P/'REPORT.pdf'),pagesize=A4,leftMargin=36,rightMargin=36,topMargin=30,bottomMargin=30).build(story)
print(json.dumps({'status':'rendered','report':'REPORT.pdf'}))
