"""Render native Rust report vectors only. No field arithmetic, prices or ratios."""
from pathlib import Path
import json,shutil,subprocess
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
here=Path(__file__).resolve().parent
study=here.parent.parent
source=study/'evidence/arithmetic-audit-vectors-01/report-vectors.json'
data=json.loads(source.read_text())
panels=data['scalar_panels']
colors={'Picard.Fq':'#416b96','cover.Fq':'#d58945','FpR.coefficient':'#398575','fpm.base':'#398575'}
fig,axes=plt.subplots(1,2,figsize=(7.2,3.5))
for ax,op,title in [(axes[0],'mul','Source products'),(axes[1],'inv','Atomic base inversions')]:
 for i,p in enumerate(panels):
  for item in p['q223']['stacks']:
   if item[op]:ax.bar(i,item[op],bottom=item[op+'_bottom'],color=colors.get(item['backend'],'#8c729a'),width=.72)
 ax.set_title(title,fontsize=11);ax.set_xticks(range(6));ax.set_xticklabels([p['target']+'\n'+('Orig'if p['arm']=='original'else'Norm')for p in panels],fontsize=7)
 ax.tick_params(axis='y',labelsize=8);ax.set_ylabel('Raw source events / 75 scalars',fontsize=9);ax.grid(axis='y',alpha=.18);ax.set_axisbelow(True)
fig.legend(handles=[Patch(color=colors['Picard.Fq'],label='Picard Fq'),Patch(color=colors['cover.Fq'],label='Cover Fq'),Patch(color=colors['FpR.coefficient'],label='FpR coefficients / base inverse')],loc='lower center',ncol=3,fontsize=8)
fig.suptitle('q=223: more products and fewer inversions; costs remain unpriced',fontsize=11)
fig.tight_layout(rect=(0,.1,1,.95));fig.savefig(here/'source-vectors.svg');plt.close(fig)
dot='''digraph A {
graph[rankdir=TB,bgcolor="transparent",nodesep=.27,ranksep=.28];
node[shape=box,style="rounded,filled",fillcolor="#eef3f8",fontname="DejaVu Sans",fontsize=9];
edge[fontname="DejaVu Sans",fontsize=8];
F[label="Immutable original closure\nconsumer21af + producer3d + genuine fixture\n785 checked inputs"];
T[label="Separate pure-hook derivative\n24 literal file patches\nfrozen solver bodies + compiled strip checks"];
U[label="ONE unfiltered native unit\n225 exact scalar pairs / 1125 triples\n60 IC pairs / all15 FB30 failures retained"];
P[label="Primitive controls\n281 original-FpR reference inputs\nlazy / nonlazy / degree1 / private Picard"];
C[label="Copied FpR hook control\ncorrect algebra in both probes\npositive11 products; omission2 products"];
J[label="All86 original records exact\nONLY existing raw wall exclusions"];
L[label="7113 scoped source rows\nRust aggregation conserves all counts\nAPI / auxiliary rows stay separate"];
O[label="Observed component tradeoff\nNo calibrated cost or computational advantage",fillcolor="#f8edda"];
F->T;T->U;T->P;T->C;U->J;U->L;P->L;C->L;L->O;J->O;
}
'''
(here/'arithmetic-audit.dot').write_text(dot)
subprocess.run(['dot','-Tsvg',str(here/'arithmetic-audit.dot'),'-o',str(here/'arithmetic-audit.svg')],check=True)
shutil.copyfile(study/'reports/norm-assisted-IC-01/target-identities.txt',here/'target-identities.txt')
shutil.copyfile(study/'reports/norm-assisted-IC-01/identities.json',here/'identities.json')
shutil.copyfile(source,here/'report-vectors.json')
rows=[['HLP','Arm','Products','Squares','Inverses','u128 rem.']]
for p in panels:
 v=p['q223']['totals'];rows.append([p['target'],'original'if p['arm']=='original'else'norm',format(v['mul'],','),format(v.get('sq',0),','),format(v['inv'],','),format(v.get('rem_u128',0),',')])
(here/'table.json').write_text(json.dumps(rows,indent=2)+'\n')
pages=[[
 'This audit asks whether the norm-assisted sampler actually saves computation once the previously uncounted backend arithmetic is visible. It records executed source-level arithmetic, not hardware instructions or calibrated field costs. The fixed panel uses q223, K=F223[z]/(z³−3), ell2773073, and all three actual transferred Jacobians. No stage improvement or computational advantage is claimed.',
 'Unsigned native8d0c27: one serial unfiltered unit passes; all225 scalar pairs and1125 R,R+G,R+Q triples agree, and all60 paired IC attempts retain120 reports. All15 public cases have three common correct settings;45 answers per arm are accepted after the ORIGINAL Picard and independent source checks. All15 shared FB30 failures remain, including ten rejected wrong tentative scalars.',
 'All86 whole original records match in the native Rust comparator after ONLY the frozen ATTEMPT phase.wall and stats.wall_total exclusions. All785 original inputs, the entire backend derivative and19 files in the fresh sampler root remain unchanged. Existing frozen solver files stay byte exact. Each compiled solver removes only two declared tap insertions to recover its frozen body, while the old two-substitution sampler check also passes.',
 'The four original-FpR reference corpora contain281 inputs across q223 degrees1,3,6 and a legal nonlazy degree3 field over2^62−57. Dense, sparse, zero, one and fixed-RNG cases agree. The original reference FpR body is untapped and shares disclosed instrumented Zp/fpm dependencies; its control work is outside the primary comparison vectors. Existing60 conditional Lean bindings remain partial and unsigned; this instrumentation adds no geometric theorem.'
], [
 'Unsigned native aggregation8c2406 retains all7113 census rows and conserves every recorded event count. The chart and table show total q223 source events over the same75 ordered scalars per actual model, including zero and duplicate draws. Counts are deterministic at this finite scope; no performance uncertainty interval or growing-size extrapolation is implied.',
 'The candidate uses more source products and fewer atomic base inversions in every model. Old Picard-only counters omit the cover and FpR work and therefore cannot establish a stage win. Products, coefficient squares, constant-two products, additions, subtractions, negations, modular remainders and atomic inverses remain separate, with full per-backend/modulus vectors in the retained native JSON.',
 'This is a sampling control against the original Picard scalar method. It excludes the separately recorded public-G preparation from the75-scalar vectors. The solver, setup, admission and independent verification vectors are retained separately; the model scope also includes test validation. Arms share setup and are not independently cold pipelines. Strongest fixed-base scalar, IC, rho and precomputation-rho references and calibrated complete cold/online costs are still required.'
], [
 'The actual source is Eprime/K: y²=x³+(196,168,69)x+(8,82,207), with order11092292 and ell2773073. The public-G-only prepared point is x=(64,152,78), y=(36,12,9) in each model. The complete existing Phi and Norm bridges, exact base points, quartics and model identifiers above are unchanged. No new isogeny edge or kernel claim is added.',
 'The genuine copied-source counter canary preserves the correct algebra [7,5,3] in both probes. Positive native0 observes11 coefficient products. Removing ONE convolution-hook site leaves the same correct algebra but observes2 products and rejects101. The ordinary counter-unit test also checks nested scopes and actual foreign-thread rejection. A legacy Picard reset cannot reset the new ledger.',
 'Preserved negatives: first materialization128 tried to read a genuine external fixture as a Git blob; native01 assumed constructor counters were nonzero; native02 reused a stale Cargo artifact; native03 used unit coefficients optimized without multiplication. The fixed build emits its source manifest path and exact controls digest. The first comparator101 wrongly required wall_total on early failures. Canary PATH127 and build124 are retained; matching original serde derive features resolves the rebuild. No criterion or original verifier was weakened.',
 'Protocols c20aaf/2c and cda454/584 preceded their respective hook code; storage/replay protocol da6dab precedes the new workflow and canonical links. All observations are unsigned. The unchanged PCC workflow hydrates canonical docs; relative links preserve the whole native-log and report bytes. Whole closed source/output custody, fresh full replay and exact source CI remain next at report drafting.',
 'Sources checked: pinned common/ic/ghs, FpR/field/fpm and cover/Picard source files in hook-inventory.json; native8d0c27 and vectors8c2406; original source21af/producer3d; prior conditional norm-assisted proof map. The earlier HLP section4.1, Tian cover-attack and EFD source review remains relevant. KB/lead wrappers exit127 and the vault stays locked; no novelty or absence inference follows.',
 'Graphs checked: norm-assisted-sampling, common-origin compatibility, chain kernels/collapse and prime-field descent diagrams retain their mathematical claims and identities. This report adds an accounting flow and raw-vector plot. Complete global beta coordinates, actual geometry/log-extension bridges, root124/clock101 and main-ledger/review/signing/conflict requirements remain open. Live budget/capacity are unknown and no paid build or benchmark has launched.'
]]
for i,page in enumerate(pages,1):(here/f'page{i}.json').write_text(json.dumps(page,indent=2)+'\n')
(here/'REPORT.md').write_text('# Source arithmetic in norm-assisted Jacobian sampling\n\n2026-11-14 · finite native observation · unsigned\n\n'+'\n\n'.join(p+' [pcc:unverified]'for page in pages for p in page)+'\n\n[Diagram](arithmetic-audit.svg) · [raw vector plot](source-vectors.svg) · [native vector data](report-vectors.json) · [PDF](report.pdf)\n')
for p in here.glob('*.svg'):p.write_text('\n'.join(x.rstrip()for x in p.read_text().splitlines())+'\n')
