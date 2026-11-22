#!/usr/bin/env python3
"""Evidence-linked three-path instruction profile, with native limits explicit."""
import json, statistics, subprocess
from pathlib import Path
from xml.sax.saxutils import escape
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.utils import ImageReader
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, Image, PageBreak
P=Path(__file__).resolve().parent
a=json.loads((P/'analysis-profile-001.json').read_text()); replay=json.loads((P/'independent-replay-profile001.json').read_text())
methods=['anchor','current','inverse']; totals=a['totals']; med={m:statistics.median(totals[m]) for m in methods}
plt.rcParams.update({'svg.fonttype':'none','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,ax=plt.subplots(figsize=(8,3.3));bars=ax.bar(['Frozen anchor','Current control','SIMD inverse'],[med[m]/1e6 for m in methods],color=['#6b7f8d','#b78444','#28777d'])
for b,m in zip(bars,methods):ax.text(b.get_x()+b.get_width()/2,b.get_height()+1,f'{med[m]/1e6:.3f}',ha='center')
ax.set_ylim(0,125);ax.set_ylabel('Whole-guest Ir (millions)');ax.set_title('Fixed N27 development input; two captures per IC method');fig.tight_layout()
for ext in ['svg','png']:fig.savefig(P/f'profile-totals.{ext}',dpi=180)
plt.close(fig)
def own(method, predicate):
 rows=[r for r in a['rows'] if r['method']==method]
 return statistics.mean(sum(f['ir'] for f in r['functions'] if predicate(f['function'])) for r in rows)
predicates=[('General m dispatcher',lambda f:'ic_boundary::decompose_mitm::' in f),('Pairwise wrapper',lambda f:'FastCurve>::add_pairwise_vector' in f),('Collector body',lambda f:'ic_boundary::collect_and_solve_with::' in f)]
deltas=[own('current',p)-own('anchor',p) for _,p in predicates];deltas.append(med['current']-med['anchor']-sum(deltas))
labels=[n for n,_ in predicates]+['Other exclusive work']
fig,ax=plt.subplots(figsize=(8,3.1));ax.barh(labels,[d/1e6 for d in deltas],color=['#b78444' if d>0 else '#28777d' for d in deltas]);ax.axvline(0,color='#667078',lw=1);ax.set_xlabel('Current minus anchor exclusive Ir (millions)');ax.set_title('Disjoint exclusive attribution\nResidual makes the full difference explicit');fig.tight_layout()
for ext in ['svg','png']:fig.savefig(P/f'profile-deltas.{ext}',dpi=180)
plt.close(fig)
dot='''digraph G { rankdir=LR; graph [bgcolor="white",fontname="Helvetica"]; node [shape=box,style="rounded,filled",fillcolor="#edf3f5",fontname="Helvetica",fontsize=11]; edge [color="#648493"]; q [label="Same public Q / base / schedule\\nEC1N27Crbh9ce93808c7a5"]; anchor [label="Frozen two-summand oracle"]; current [label="Current and SIMD inverse oracle"]; dispatch [label="General m=2 / m=3 dispatcher\\n55,163 observed extra calls",fillcolor="#faf0df"]; probe [label="Same PairTable::probe\\nSame witnesses and counters"]; q -> anchor; q -> current; anchor -> probe [label="direct"]; current -> dispatch; dispatch -> probe; fix [label="Proposed fixed-m2 source change\\nCall probe directly",fillcolor="#e5f2ed"]; current -> fix [style=dashed]; fix -> probe [style=dashed]; }'''
(P/'profile-flow.dot').write_text(dot)
for ext in ['svg','png']:subprocess.run(['dot','-T'+ext,str(P/'profile-flow.dot'),'-o',str(P/('profile-flow.'+ext))],check=True)
styles=getSampleStyleSheet();story=[];md=[]
def para(text,style='BodyText'):
 md.extend([text,'']);story.extend([Paragraph(escape(text),styles[style]),Spacer(1,9)])
def img(name,width=520):
 w,h=ImageReader(str(P/name)).getSize();story.extend([Image(str(P/name),width=width,height=width*h/w),Spacer(1,10)])
def table(rows,widths):story.extend([Table(rows,colWidths=widths,style=[('FONTSIZE',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),7)]),Spacer(1,10)])
para('Where the collector regression landed','Title')
para('PCC-20261117-1bc12f: unsigned exploratory producer data. Job20261117-013021-5b0f, exact frozen binaries and fixed N27 development fixture0. The native timing panel remains sealed. [pcc:unverified]')
para('The current binary executes more whole-guest instructions than the frozen anchor. The dominant extra call layer is the fixed-two-summand oracle routing through the general m=2/m=3 dispatcher. The arithmetic kernel itself saves instructions, but it also inherits that extra query-dispatch work. The exact effect on native wall time requires a focused source change and a separate paired panel. [pcc:unverified]')
img('profile-totals.png')
table([['Method','Capture1 Ir','Capture2 Ir']]+[[m,str(totals[m][0]),str(totals[m][1])] for m in methods],[160,180,180])
para(f"Supplementary whole-guest rho captures: plain {totals['rho-plain'][0]:,} Ir; negation {totals['rho-negation'][0]:,} Ir, one each. All eight scalar answers and {replay['state_checks']} exported states were checked using the existing Python arithmetic. Repeated instruction counts do not estimate native clock uncertainty. [pcc:unverified]")
story.append(PageBreak());para('A fixed-two-summand path lost specialization','Heading1');img('profile-flow.png');img('profile-deltas.png')
para('Anchor oracle:55,163 direct PairTable::probe calls. Current and inverse oracle:55,163 additional general-dispatch calls. The general dispatcher contributes1,933,760 exclusive Ir in the current capture; the common probe callee remains3,597,613 inclusive Ir. Exclusive categories in the chart are disjoint. The probe inclusive count is a separate call-edge measurement and is never added to caller-inclusive cost. [pcc:unverified]')
para('The ordinary pairwise call edge grows from19,892,502 to19,927,013 inclusive Ir. Its scalar inverse and full-point formula callee work are identical. Thus the runtime inverse selector is a smaller contributor here. Source inspection confirms BinaryBatchMitmOracle accepts exactly two summands, while calling a general dispatcher with the constant2. [pcc:unverified]')
story.append(PageBreak());para('Source change and validation obligations','Heading1')
para('The focused patch replaces that general dispatch call with the same PairTable::probe followed by the same two-index witness allocation. Table preparation, group arithmetic, lookup counters, guards, caps, state schedule, rows/rank and verification remain as before. Generic three-summand handling elsewhere is untouched. Native cost remains pending. [pcc:unverified]')
para('Local validation:27framework tests and strict library/probe Clippy passed; claimPCC-20261117-86dbb3 is unsigned and covers local checks only. Native preparation must match the frozen compiler/environment and repeat175complete maps,15loader cases, five512state traces and the existing overlapping framework/vector/inverse controls. A fresh native panel and post-timing instruction captures must test the optimization. [pcc:unverified]')
para('Accounting: Callgrind Ir covers whole-process guest execution including input/calibration loading, setup, collection, matrix work, scalar group check, JSON and cleanup. It is not hardware-retired instructions, native wall time or the prior collector-only clock. Host placement and memory technology remain unknown; qualification is null. No source-default promotion or mathematical novelty conclusion. [pcc:unverified]')
pin=json.loads((P/'profile-input.json').read_text())
for name in ['anchor','prepared']:
 b=pin[name];para(f"{name}: source {b['source_commit']}; binary SHA256 {b['binary_sha256']}; preparation {b['source_job']}. Receipt and exact job metadata hashes are pinned in profile-input.json. [pcc:unverified]")
para('One L4 allocation,4CPU/8GiB/900seconds; arithmetic pinned to one allowed CPU; controller780seconds, IC120seconds, rho60seconds, instrumented preflights90seconds,32GiB virtual cap. Eight raw totals agree with header/footer, exclusive sums and annotation totals. The existing dimension10/531-column base and curve identity are unchanged. No new curve/isogeny fact; canonical curve and isogeny-route sources are unaffected. [pcc:unverified]')
para('Sources and reproduction: PROTOCOL.md, profile-input.json, run_profile.py, analyze_profiles.py, replay_profiles.py, profile-findings.json, PairTable::probe, decompose_mitm and BinaryBatchMitmOracle::decompose. Raw capture hashes and archive receipts bind the evidence. [pcc:unverified]')
(P/'REPORT-profile001.md').write_text('# Three-path collector regression attribution\n\n'+'\n'.join(md)+'\n![Whole-guest Ir](profile-totals.svg)\n\n![Exclusive deltas](profile-deltas.svg)\n\n![Call flow](profile-flow.svg)\n')
SimpleDocTemplate(str(P/'REPORT-profile001.pdf'),pagesize=A4,leftMargin=36,rightMargin=36,topMargin=30,bottomMargin=30).build(story)
print(json.dumps({'report':'REPORT-profile001.pdf','status':'rendered'}))
