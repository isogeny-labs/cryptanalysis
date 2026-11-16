"""Rendering only: display recorded Rust values and the written/formal scope."""
from pathlib import Path
import json,lzma,subprocess
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import typst
import sys
r=Path(__file__).resolve().parents[4];s=r/'experiments/chained-transfer-public-target'
if len(sys.argv)!=2:raise SystemExit('usage: render.py NEW_OUTPUT_DIRECTORY')
p=Path(sys.argv[1]).resolve()
if p.exists():raise SystemExit('output must be fresh; preserve the frozen report')
p.mkdir(parents=True)
raw=json.loads(lzma.decompress((s/'evidence/beta-complete-accounting-acceptance-05/all-native-records.json.xz').read_bytes()));data={x['kind']:x['data']for x in raw};c=data['N4_BETA_COMPLETE_RATIONAL'];ex=data['N4_BETA_ALL_EXCEPTIONAL'];fib=data['N4_BETA_BASECHANGE_FIBRES']
render_data=dict(core=c,exceptional_histograms=[x['cofactor_sector_histogram']for x in ex['all448_inputs']],exceptional_outputs=[x['exceptional_outputs']for x in ex['all448_inputs']],full_data_source='../../evidence/beta-complete-accounting-acceptance-05/all-native-records.json.xz',scope='projection for layout only; full1191975B raw JSON retained losslessly')
(p/'render-inputs.json').write_text(json.dumps(render_data,indent=2)+'\n')
plt.rcParams.update({'svg.fonttype':'none','font.family':'DejaVu Sans','font.size':10})
fig,axes=plt.subplots(1,2,figsize=(8,2.6),sharey=True)
for ax,row,title in zip(axes,ex['all448_inputs'],['J0: all 224 rational exceptional classes','J1: all 224 rational exceptional classes']):
 values=row['cofactor_sector_histogram'];bars=ax.bar(['0','1','2','3'],values,color='#4477aa',width=.58);ax.set_title(title,fontsize=10);ax.set_xlabel('Cofactor sector, canonical order in this model');ax.set_ylim(0,80);ax.grid(axis='y',alpha=.20);ax.set_axisbelow(True)
 for bar,value in zip(bars,values):ax.annotate(str(value),(bar.get_x()+bar.get_width()/2,value),xytext=(0,4),textcoords='offset points',ha='center')
axes[0].set_ylabel('Exceptional inputs checked (classes)');fig.tight_layout();fig.savefig(p/'exceptional-coverage.svg');fig.savefig(p/'exceptional-coverage.png',dpi=150);plt.close(fig)
def wrap_id(x):return '\\n'.join(x[i:i+48]for i in range(0,len(x),48))
dot='''digraph Complete {
 graph[rankdir=TB,bgcolor="white",nodesep=.35,ranksep=.35];
 node[shape=box,style="rounded,filled",fillcolor="#edf4fa",fontname="DejaVu Sans",fontsize=10,margin=".14,.10"];
 edge[fontname="DejaVu Sans",fontsize=9,color="#275875"];
 j0[label="J0(F223), order 11092292\\nOLDID"];
 xo[label="xo = x - [ell]x\\n[ell]xo = 0"];
 x2[label="x2 = [ell]x\\n[4]x2 = 0"];
 odd[label="[1386537] F(xo)\\nF = Phi1 gamma N0 = [2] beta"];
 table[label="Actual 4-entry cofactor table\\nBoth choices of lift give the same image",fillcolor="#e8f3e7"];
 pre[label="Precompute on ALL 16 E[4](L), each side\\nComplete quadratic fibre ideals + actual origins\\n8 images:4 rational;2 lifts per rational class\\n32 torsion fibre +2 origin traces\\n16 source-isogeny evaluations",fillcolor="#f6f0df"];
 j1[label="Sum = beta(x) in J1(F223)\\nNEWID",fillcolor="#e8f3e7"];
 {rank=same;xo;x2;} {rank=same;odd;table;}
 j0->xo;j0->x2;xo->odd;x2->table;pre->table[label="explicit setup",style=dotted];odd->j1;table->j1;
}'''.replace('OLDID',wrap_id(c['old_model'])).replace('NEWID',wrap_id(c['new_model']))
(p/'complete-diagram.dot').write_text(dot);subprocess.run(['dot','-Tsvg',str(p/'complete-diagram.dot'),'-o',str(p/'complete-diagram.svg')],check=True);subprocess.run(['dot','-Tpng','-Gdpi=150',str(p/'complete-diagram.dot'),'-o',str(p/'complete-diagram.png')],check=True)
(p/'complete-diagram.diagram.json').write_text(json.dumps(dict(source_model=c['old_model'],target_model=c['new_model'],ell=c['ell'],order=c['rational_order'],geometry='written matched HLP10 quotient degree13^3; not a fully formal geometric edge',implemented='complete rational evaluator; native 3f1ade; conditional Lean 1e2420',setup=c['explicit_preprocessing']),indent=2)+'\n')
page1=[
 'Implemented: a reusable full-rational evaluator for the matched HLP(1,0) quotient, including the cofactor-four classes. Native 3f1ade passes three unfiltered tests with zero failed/ignored/filtered and845 original guards unchanged. The full-tree audit checks exactly three accounting metadata changes; every other class, scalar and control field equals the prior records. Old raw/golden data is retained; the corrected whole fixture has no masks. The diagram shows the implemented split; the written global quotient has degree13³ and both dual compositions[13].',
 'For ell=2773073≡1 modulo4, split x2=[ell]x and xo=x−x2. Then4x2=0 andell·xo=0. Evaluate the odd component as [1386537]F(xo), and the even component through the actual four-entry lift table. Their sum is beta(x). The full rational inverse is [3413013]betaDual; source recovery on the odd subgroup uses319970 as the inverse of26.',
 'Quadratic preprocessing uses L=F223[w]/(w⁶−3), K=F223[z]/(z³−3), z=w²; F223² is span(1,w³). All three F²-conjugate line/conic ideals, multiplicities, infinity branches and actual origin are retained. Coefficient traces use1,w²,w⁴, and reduction uses genuine quadratic Picard arithmetic. All16 four-torsion inputs each side,256 addition pairs each, both kappa branches, original K agreement and F³ equivariance pass.',
 'Only four of the eight quadratic images are F223-rational. In the group proof, the source group is the preimage of rational J0 inside A(F223²), not all quadratic source points. Each rational cofactor class has two actual lifts; their matched gamma/delta images agree. No scalar witness, fitted translation, reduced-support substitution or odd-DLP table enters the runtime.'
]
page2=[
 'Native coverage: 48 mixed-sector classes (six fixed odd scalars × four sectors × two directions), 96 ordered addition pairs, all five literal public targets × four sectors, and all 448 rational exceptional inputs. Both [13] compositions, the full inverse and F=[2]beta/G=[2]betaDual pass. Exceptional outputs number 1 per model. Sector indices are ordered independently by each model’s canonical keys; the chart is exhaustive coverage, with no sampling uncertainty and no timing data.',
 'Faithful conditional algebra1e2420: ordinary group/homomorphism laws, natural multiplication defined from addition, rational decomposition, odd normalization, evaluate=beta for every class, full inverse13 and DLP equivalence in both directions. Both original Lean 4.34.1/4.35.0 gates accept 44 declarations with zero trusted; all 19 named roots use no axioms beyond propext. Actual geometric/order/finite-lift/reducer bridges remain explicit written/native hypotheses.',
 'The scalar projection e²−e=4me, e=4m+1, has separate exact Int proof and original native certificate IDC1h2576687cb0806346: exact integer coefficient expansion, 64 sealed plus32 extra checker points, issue/replay0 and actual missing-term rejection101. Both original gates accept one Int declaration/zero trusted. The checker itself does not execute Lean. Six group bindings plus 4036be bring the partial unique total to 73; none is signed main standing.',
 'Preserved negatives: the old setup label counted the full verification panel instead of the filtered constructor. Dynamic counts3f1ade and an actual legacy32 rejection101 correct this; the strict old fixture still rejects101. Initial Lean5f5a15 and CRT callera284e5 also remain preserved. The whole-record comparator rejects101 when the entire exceptional record is omitted, without writing an output; all 3 records are required. Earlier path, workspace, field-ring, wrong tentative DLP and same-product chain-collapse results remain intact.',
 'Selected setup calls are 32 torsion fibre evaluations, two separate quadratic origin traces and 16 torsion source-isogeny evaluations. Both four-entry tables, all original/context setup and validation remain in the implementation and unpriced. These are selected entry counts, not a primitive-cost ledger. Calibrated cold/online costs and computational advantage are not established. This report covers the complete rational-point evaluator; global closed rational coordinates and actual geometric formalization remain separate. Next: dedicated replay/fresh full/own CI, whole genuine custody, then a prospectively reviewed optimization or genuine next chained map.'
]
for name,obj in [('page1.json',page1),('page2.json',page2)]: (p/name).write_text(json.dumps(obj,indent=2)+'\n')
identity=[
 'K=F223[z]/(z³−3); E: a=(214,144,205), b=(137,218,9). E13: a=(196,168,69), b=(8,82,207).',
 'C0, original monomial order: '+str(c['old_quartic'])+'; P0='+str(c['old_P0'])+'.',
 'C1, same order: '+str(c['new_quartic'])+'; P0='+str(c['new_P0'])+'.'
]
(p/'identities.json').write_text(json.dumps(identity,indent=2)+'\n')
(p/'report.typ').write_text('''#set page(paper:"a4",margin:12mm)
#set text(font:"DejaVu Sans",size:9pt)
#set par(leading:.28em)
#text(size:16pt,weight:"bold")[Complete rational degree-13 Jacobian transfer]
#parbreak()
2026-11-14 · native 3f1ade · conditional Lean 1e2420 · unsigned
#parbreak()
#image("complete-diagram.svg",width:100%,height:107mm,fit:"contain")
#for p in json("identities.json") {text(size:7.5pt,p);parbreak()}
#for p in json("page1.json") {text(p);parbreak()}
#pagebreak()
#text(size:15pt,weight:"bold")[Explicit input coverage and proof scope]
#parbreak()
#image("exceptional-coverage.svg",width:100%,height:66mm,fit:"contain")
#for p in json("page2.json") {text(p);parbreak()}
#text(size:8pt)[Sources: BETA_COMPLETE_RATIONAL_DERIVATION_02; BETA_COMPLETE_RATIONAL_PROOF_MAP_01; evidence/beta-complete-accounting-acceptance-05 (whole native and JSON); evidence/beta-complete-Lean-acceptance-03; beta-complete-rational-bindings-01; beta-CRT-projection-acceptance-02. Earlier 19-workflow CI cd2e03 applies to c77f95dc; this evaluator’s dedicated CI is pending.]
''')
# SVG formatting is normalized before inspection or any immutable report claim.
for f in p.glob('*.svg'):f.write_text('\n'.join(line.rstrip()for line in f.read_text().splitlines())+'\n')
typst.compile(str(p/'report.typ'),output=str(p/'report.pdf'))
print('report',p/'report.pdf',(p/'report.pdf').stat().st_size,flush=True)
