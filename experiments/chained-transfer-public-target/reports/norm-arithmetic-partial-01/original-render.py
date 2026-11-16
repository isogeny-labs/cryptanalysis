"""Render exact native vector fields only; no research arithmetic or cost models."""
from pathlib import Path
import json,shutil,subprocess,typst
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';p=s/'reports/norm-arithmetic-partial-01';p.mkdir();raw=Path('/workspace/scratch/ct75-norm-arithmetic-partial-analysis-01')
shutil.copyfile(raw/'reused-render-data.json',p/'data.json');shutil.copyfile(raw/'all-partial-vectors.json.xz',p/'all-partial-vectors.json.xz');d=json.loads((p/'data.json').read_text())
plt.rcParams.update({'svg.fonttype':'none','font.family':'DejaVu Sans','font.size':9})
arms=d['all_arms'];labels=[x['phase']for x in arms[0]['q223_by_phase']];assert labels==[x['phase']for x in arms[1]['q223_by_phase']]
fig,axes=plt.subplots(1,2,figsize=(9.4,3.8),sharey=True)
for ax,op,title in zip(axes,['mul','inv'],['Source mul events at modulus223','Atomic inv events at modulus223']):
 for arm,color,offset in zip(arms,['#b57b34','#347d83'],[-.18,.18]):
  vals=[x['all_operations'][op]for x in arm['q223_by_phase']];ax.barh([i+offset for i in range(len(labels))],vals,height=.34,color=color,label=arm['arm'])
 ax.set_xscale('log');ax.set_title(title,fontsize=10);ax.set_xlabel('Unpriced event count · logarithmic axis');ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True)
axes[0].set_yticks(range(len(labels)),labels);axes[0].invert_yaxis();axes[1].legend(loc='lower right',frameon=False)
fig.suptitle('Complete fixed60-case reused-context processes; setup once per arm',fontsize=11)
fig.tight_layout();fig.savefig(p/'source-vectors.svg',bbox_inches='tight');plt.close(fig)
(p/'flow.dot').write_text('''digraph actual {graph[rankdir=LR,bgcolor="white",fontname="DejaVu Sans",nodesep=.16,ranksep=.2];node[shape=box,style="rounded",fontname="DejaVu Sans",fontsize=10,margin=.1];edge[fontname="DejaVu Sans",fontsize=8];f[label="Frozen60 whole packets\\nuntouched complete-C reference"];c[label="Cold planned120 processes\\n12 complete /108 incomplete\\n900s actual124",color="#a57535"];u[label="Two reused-context processes\\neach all60 outputs and ledgers\\nactual0 / no masks",color="#347d83"];v[label="Rust exact partial analysis\\nsource unit vectors + differences\\nall rows / diagnostics retained"];f->c;f->u;u->v;c->v[style=dashed,label="partial only"]; }''')
subprocess.run(['dot','-Tsvg',str(p/'flow.dot'),'-o',str(p/'flow.svg')],check=True)
meta={'status':'complete reused panel and incomplete cold panel; unsigned','protocol':'../../NORM_HALVING_ARITHMETIC_PROTOCOL_01.md','claims':['PCC-20261114-b5fd45','PCC-20261114-471848','PCC-20261114-ee232d'],'source':'5ac59843a0cc6546b0f007c0bd2f79212d169c43','prototype':'5c9a5559d2dfff4abb54acdddd5f262157eec8ad','J0':'Ciani-Jac-pi0-v2-3ba99ad5742ad62540f8addbbe153572696d2e595f64cd2c1b0b52e51ff351a4','J1':'Ciani-Jac-odd-product-v1-7ea9d0f9d1a48a48489425beab48274fca7bd0848e47a0bac3a027c01601e2c4','source_data':'Rust partial analysis, whole all-partial-vectors.json.xz and native rendering projection data.json','quantitative_graph':'all observed phase q223 mul and inv counts for each complete fixed60-case reused process; API/aux/encoding excluded by native classification and all retained in full vectors; units unpriced, logarithmic axes','canonical_graphs_checked':['../norm-halving-results-01/flow.dot','../norm-halving-results-01/selected-calls.svg','../norm-arithmetic-proposal-01/flow.dot'],'decision':'Prior mathematical and selected-API graphs remain frozen at their scope; new source vector graph exposes arithmetic tradeoff, not calibrated advantage.'}
(p/'flow.diagram.json').write_text(json.dumps(meta,indent=2)+'\n')
(p/'report.typ').write_text(r'''#set page(paper: "a4", margin: 13mm)
#set text(font: "DejaVu Sans", size: 9pt)
#set par(leading: .4em)
#set heading(numbering: none)
#let d=json("flow.diagram.json")
#text(size: 16.5pt,weight: "bold")[Norm-halving: actual source arithmetic]
#v(3pt)
#text(fill: rgb("#a57535"),weight: "bold")[UNSIGNED · cold panel incomplete · reused panel complete]

The direct map trades more source products for fewer inversions in the complete reused-context transfer sequence. These source vectors are unpriced. They establish neither a calibrated total cost nor an ECDLP advantage; the planned full cold comparison remains incomplete.

#image("flow.svg",width:100%,height:27mm,fit:"contain")
#image("source-vectors.svg",width:100%,height:72mm,fit:"contain")

== Same fixed operations and all validation work
The prospective01e617 protocol was published before code. Each arm processes40 public-sector/direction cases and20 full inverses in the same order. Expected whole field/model/key packets came first from untouched complete-C. Include context construction, complete input norm/geometry/fullORDER admission, transfer, original output norm/order validation and inverse scalar3413013. All60 individual online vectors and signed differences remain in the whole compressed record.

== Observed tradeoff, with no assigned operation prices
For the complete reused transfer phase, q223 source mul events are16,792,793 baseline and91,064,595 direct; atomic inv events are97,858 and24,422. Arm construction uses347,475,059 and263,218,246 source mul events. Common input norm/order, output validation and full inverse are retained as separate phases. The chart keeps source mul and atomic inv distinct, with logarithmic axes; it does not combine operations into a cost or divide a batch into a one-target DLP price.

== Preserve the incomplete experiment
The cold caller hit its frozen900s bound124:12 complete records,108 missing or incomplete. The separate two reused-context processes each closed0 with all60 whole packets exact, complete monotone ledgers and final snapshots. Original full120+2 analysis rejects101 and writes no accepted output. The retrospective partial report labels the missing rows explicitly; no cold extrapolation or criterion change is used.

== Controls and limits
Primitive controls include all49728 nonzero quadratic inverses, delegation/reset checks, actual omitted-FpR and quadratic-hook rejection101, disabled-observer rejection2, and FOUR unfiltered production tests with all4 wholeJSON exact/no masks while observation is explicitly OFF. Actual census observation is ON with strict ownership. API, encoding and auxiliary rows stay separate; all row counts are conserved. Atomic inverse internals, allocation, parsing, I/O and bookkeeping remain unpriced. Failed builds124 and wrong-toolchain auditor invocation1 are preserved.

#text(size:7.2pt)[J0: #d.J0]

#text(size:7.2pt)[J1: #d.J1]

#text(size:7.8pt)[Evidence: protocol01e617; parity87af78; controls3da93a/1430fd/e70b64; checkpoint93464c; cold/reuse outcomesb5fd45; native partial analysis471848 and projectionee232d. Whole source/count records, actual executables and failed attempts are retained. Existing mathematical/API graphs remain unchanged. Next: exact faster observation with whole-ledger controls if needed; genuine nondual13 elliptic/model preflight23ab48; full geometry and admitted matched-algorithm cost comparison remain open.]
''')
typst.compile(str(p/'report.typ'),output=str(p/'report.pdf'),root=str(p))
(p/'REPORT.md').write_text('''# Actual source arithmetic: complete reuse, incomplete cold

The prospective01e617 experiment has an incomplete cold population and two complete fixed60-case reuse processes. Cold124 and strict full comparator101 remain explicit; the separate Rust partial report checks12 actual complete cold records, lists108 missing/incomplete, and checks every whole packet/cumulative ledger in both complete reuse sequences. [pcc:unverified]

The complete reused transfer sequence uses more q223 source mul events and fewer atomic inv events for the direct map:16,792,793/91,064,595 mul and97,858/24,422 inv, baseline/direct (ee232d). Context construction differs. All common admission, output validation, full inverse and diagnostics remain included and separately keyed. No calibrated cost, runtime ratio, extrapolation or ECDLP gain follows. [pcc:unverified]

[PDF](report.pdf) · [exact native render data](data.json) · [whole partial unit record](all-partial-vectors.json.xz) · [source vector graph](source-vectors.svg) · [editable actual process diagram](flow.dot) · [metadata](flow.diagram.json) · [prospective protocol](../../NORM_HALVING_ARITHMETIC_PROTOCOL_01.md). Numerical grouping and comparisons are Rust; Python only renders native fields. [pcc:unverified]

Prior norm-halving mathematical flow, selected-API chart and census proposal were checked and stay frozen at their stated scope. This adds a quantitative source-operation graph. Primitive leaves, atomic inverse, API and auxiliary work remain distinct; all excluded rows are retained. Remaining requirements include complete cold census, faithful actual geometric/program bridges, original live benchmark admission and strongest matched references. The genuine nondual13 preflight is a separate authorized successor under23ab48. [pcc:unverified]
''')
shutil.copyfile(__file__,p/'original-render.py')
print('partial results PDF bytes',(p/'report.pdf').stat().st_size)
