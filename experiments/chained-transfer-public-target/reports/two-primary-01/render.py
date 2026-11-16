"""Render original native JSON and written proof scope only."""
from pathlib import Path
import json,shutil,subprocess,hashlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';d=s/'reports/two-primary-01';d.mkdir()
rows=json.loads(Path('/workspace/scratch/ct59-two-primary-native-02/all-native-records.json').read_text())
group=next(x['data'] for x in rows if x['kind']=='N4_TWO_PRIMARY_GROUP')
(d/'native-records.json.xz').write_bytes(__import__('lzma').compress(json.dumps(rows,indent=2).encode()+b'\n'))
fig,ax=plt.subplots(figsize=(6.8,2.3));x=range(4)
ax.bar([i-.18 for i in x],[1,2,2,2],width=.35,label='E(K): C2 x C2',color='#2c6a9e')
ax.bar([i+.18 for i in x],group['exact_orders'],width=.35,label='J(F223): C4',color='#b76531')
ax.set(xticks=list(x),xticklabels=['Identity','Class1','Class2','Class3'],yticks=[1,2,3,4],ylabel='Exact element order',title='All4 rational cofactor classes in each group')
ax.legend(loc='upper left',fontsize=8);fig.tight_layout();fig.savefig(d/'orders.svg');plt.close(fig)
dot='''digraph T {
graph [rankdir=LR,bgcolor="transparent",ranksep=.35];
node [shape=box,style="rounded,filled",fillcolor="#edf5fb",fontname="DejaVu Sans",fontsize=10];
edge [fontname="DejaVu Sans",fontsize=9];
E [label="Fixed N4 q223 / seed1\nE(K), K=F223[z]/(z^3-3)\nell=2773073, order=11092292\nrational 2-Sylow: C2 x C2"];
J [label="Same fixed Ciani C / F223\nJ=Jac(C), genus3\nell=2773073, order=11092292\nrational 2-Sylow: C4"];
E -> J [label="Original completed Phi\nrational cofactor kernel2 / image2"];
J -> E [label="Original canonical Norm\nrational cofactor kernel2 / image2"];
}'''
(d/'maps.dot').write_text(dot+'\n');subprocess.run(['dot','-Tsvg',str(d/'maps.dot'),'-o',str(d/'maps.svg')],check=True)
page1=[
'Fixed native observation510d03, unsigned: original Picard arithmetic closes a four-element group from all224 rational C point classes projected byell and the actual Phi(E(K)[2]) images. Exact orders are1,2,4,4, all16 sums,64 associative triples and inverses pass. The written global Ciani isogeny supplies the order4ell bound, so this is the entire rational2-Sylow,C4. Native annihilators alone would not establish that conclusion.',
'The independent source engine finds all three distinct K-rational roots of the elliptic cubic, hence E(K)[2]=C2×C2. Actual Phi and Norm each have rational cofactor kernel2/image2, all16 homomorphism pairs and both[2] compositions pass. The nonzero transported odd generator separately has exact prime orderell. This difference is consistent with a degree-even isogeny.',
'Native02 passes one unfiltered serial test, all2318 selected input hashes unchanged. All four native JSON records match01 exactly as JSON. The first capture omitted direct V2 dependency snapshots; whole01 and correction1311d9 remain preserved. Its incomplete provenance was not promoted to full closure. This is known-case correctness development with a reused cache, not a performance experiment.'
]
page2=[
'Written derivation: the Ciani quotient maps give an F223-isogeny J~Res(K/F223)E. With q=223,t=q³+1−11092292=−2724, the Weil polynomial is P(T)=T⁶+2724T³+11089567. Its integral2-adic characteristic polynomial reduces to T⁶+1 on the actual six-dimensional geometric J[2]. This use of isogeny invariance does not transfer two-torsion through a degree-even isogeny. Cayley-Hamilton gives F⁶=1.',
'There are64 geometric2-torsion points and exactly2 fixed by F, because the rational2-Sylow is C4. If F³=1, all remaining orbits have length3, requiring64=2+3c, impossible. If F²=1, the minimal polynomial divides(T+1)²; the characteristic polynomial must be(T+1)⁶=T⁶+T⁴+T²+1, different from T⁶+1. Thus F has exact order6: the full geometric2-torsion has minimal field F223⁶, not the original cubic field.',
'Partial Lean proof map: four faithful declarations cover exact trace/parity, the integer orbit obstruction, the annihilating-polynomial implication on an arbitrary exponent-two module, and the divisor-of-six conclusion. Both unchanged original producer4.35 and consumer4.34.1 gates pass4/0trusted. Exact original PCC local bindings4e7bfe/cc7273/abcfec/5facfe pass,unsigned. Foundations are propext/Quot.sound only; no proof holes, custom axioms or native_decide. No fresh lean4checker result is claimed.',
'The full geometric bridges remain written: actual Jacobian/torsion definitions, Ciani isogeny and Weil polynomial, Tate module reduction, Cayley-Hamilton, Frobenius orbit decomposition, characteristic/minimal polynomial and minimal splitting field. The module lemma assumes the faithful polynomial identity, not the desired sixth-iterate conclusion. Integer lemmas do not discharge these geometric obligations.',
'Decision: do not assume geometric J[2] is cubic-rational or that Frobenius is semisimple of order3. A rational isogeny can still have a Frobenius-stable kernel with non-rational individual points. Actual geometric basis/action, stable maximal-isotropic kernel census, a second nondual map and target equation remain open. The next discriminating construction is explicit geometric2-torsion over F223⁶ or a coordinate kernel-descent construction. No computational advantage is established.'
]
for name,p in [('page1.json',page1),('page2.json',page2)]: (d/name).write_text(json.dumps(p,indent=2)+'\n')
(d/'REPORT.md').write_text('# Actual q223 two-primary structure and splitting field\n\n2026-11-13. Standing unsigned; formalization partial.\n\n'+'\n\n'.join(x+' [pcc:unverified]' for x in page1+page2)+'\n\nSources: two-primary/DERIVATION-01.md, FrobeniusSix.lean, original V2_MAPS_01.md; native510d03, provenance correction1311d9; formal plan573f88 and exact bindings; evidence/two-primary-plan-01/sources-checked.json. Existing positive-map and completed-descent graphs remain current; no new isogeny endpoint is added. Editable maps.dot/orders.svg/render.py and native records are adjacent.\n')
(d/'report.typ').write_text('''#set page(paper:"a4",margin:14mm)
#set text(font:"DejaVu Sans",size:9.3pt)
#set par(leading:.45em)
#text(size:18pt,weight:"bold")[The actual rational two-primary groups]
#parbreak()
2026-11-13 · fixed N4 q223 / seed1 · unsigned / partial formalization
#parbreak()
#image("maps.svg",width:100%)
#image("orders.svg",width:96%)
#for p in json("page1.json") {text(p);parbreak()}
#pagebreak()
#text(size:18pt,weight:"bold")[Why the full two-torsion needs degree six]
#parbreak()
#for p in json("page2.json") {text(p);parbreak()}
#text(size:9pt,weight:"bold")[Reproducible evidence]
#parbreak()
Native02/510d03; all224 point projections and all4 classes in adjacent compressed native JSON. Full equations: V2_MAPS_01.md / unit-acceptance-01/instance.json. Written proof and exact formal gaps: two-primary/DERIVATION-01.md. Four local PCC bindings: evidence/two-primary-bindings-01/claims.json. No new nondual map or cost comparison.
''')
for p in d.glob('*.svg'):p.write_text('\n'.join(line.rstrip() for line in p.read_text().splitlines())+'\n')
shutil.copyfile(s.parent/'chained-transfer-reference/reports/g3-norm-full-02/compile.py',d/'compile.py');shutil.copyfile(__file__,d/'render.py')
