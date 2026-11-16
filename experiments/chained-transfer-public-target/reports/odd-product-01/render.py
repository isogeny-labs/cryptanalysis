"""Render native records and written conclusions only; no cryptographic arithmetic."""
from pathlib import Path
import json,lzma,shutil,subprocess
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';d=s/'reports/odd-product-01';d.mkdir()
models=json.loads(lzma.decompress((s/'evidence/odd-product-models-acceptance-01/all-native-records.json.xz').read_bytes()))
maps=json.loads(lzma.decompress((s/'evidence/odd-product-maps-acceptance-02/all-native-records.json.xz').read_bytes()))
model_rows=[x['data']for x in models if x['kind']=='N4_ODD_PRODUCT_MODEL'];map_rows=[x['data']for x in maps if x['kind']=='N4_ODD_PRODUCT_MAP_CANDIDATE']
assert len(model_rows)==6 and len(map_rows)==3
identities=dict(source=maps[0]['data']['target_source'],old_source_figure='reports/odd-source-01/identities.json',targets=[{k:m[k]for k in ['candidate','quartic','P0','Jacobian_model_tag','HLP_kernel_mask']}for m in map_rows])
(d/'identities.json').write_text(json.dumps(identities,indent=2)+'\n')
fig,axes=plt.subplots(1,2,figsize=(7.6,2.1));ax=axes[0];names=[str((x['root_index'],x['sign_index']))for x in model_rows];vals=[x['T_equals_detH'][0]for x in model_rows]
bars=ax.bar(names,vals,color=['#3d8975'if x['D_square_in_Fp_and_K']else'#9ba4b1'for x in model_rows]);ax.set(title='ALL six actual HLP outcomes',ylabel='T in F223',ylim=(0,245));ax.tick_params(axis='x',labelsize=8)
for b,v in zip(bars,vals):ax.text(b.get_x()+b.get_width()/2,v+3,str(v),ha='center',fontsize=8)
ax=axes[1];names=[str(tuple(x['candidate']))for x in map_rows];x=list(range(3));fk=[len(m['F_rational_cofactor_kernel_indices'])for m in map_rows];gk=[len(m['G_rational_cofactor_kernel_indices'])for m in map_rows]
ax.bar([v-.17 for v in x],fk,width=.34,label='F kernel',color='#367c97');ax.bar([v+.17 for v in x],gk,width=.34,label='G kernel',color='#b47b45');ax.set(title='Actual rational cofactor kernels',ylabel='points',xticks=x,xticklabels=names,yticks=[0,1,2,3,4],ylim=(0,4.8));ax.legend(fontsize=7)
fig.tight_layout();fig.savefig(d/'outcomes.svg');plt.close(fig)
dot=r'''digraph C {graph[rankdir=TB,bgcolor="transparent",nodesep=.6,ranksep=.45,label="ACTUAL F degree140608 / reverse G\nBOTH[52] / polarization52 / odd inverse159985G",labelloc=t,fontname="DejaVu Sans",fontsize=11];node[shape=box,style="rounded,filled",fillcolor="#edf5fb",fontname="DejaVu Sans",fontsize=11];edge[fontname="DejaVu Sans",fontsize=10];J[label="Jold / F223\nfixed q223/seed1"];A[label="A=Res(E) / F223\noriginal source"];B[label="Aprime=Res(Eprime) / F223\na=(196,168,69), b=(8,82,207)\nK=F223[z]/(z^3-3)"];L[label="THREE actual Jprime / F223\n(1,0), (1,1), (2,1)\nP0s/equations/fullIDs:identities.json",fillcolor="#edf8ed"];{rank=same;J;L};{rank=same;A;B};J->A[label="Nold degree8"];A->B[label="Res(gamma) degree13^3\nboth source composites[13]",constraint=false];B->L[label="PhiPrime degree8\nboth new dual[2]",constraint=false];J->L[style=bold,color="#43836b",constraint=false];}'''
(d/'chain.dot').write_text(dot+'\n');subprocess.run(['dot','-Tsvg',str(d/'chain.dot'),'-o',str(d/'chain.svg')],check=True)
api=r'''digraph R {graph[rankdir=LR,bgcolor="transparent",nodesep=.2,ranksep=.3];node[shape=box,style="rounded,filled",fillcolor="#edf5fb",fontname="DejaVu Sans",fontsize=10];edge[fontname="DejaVu Sans",fontsize=9];S[label="Original short E odd point P\nfield/source tag + coordinates"];T[label="New tagged Jacobian class H(P)\nH=F PhiOld / no witness scalar"];S->T[label="Chain::from_source"];T->S[label="Chain::recover_source\n159985 delta NormPrime\nsubgroup + forward roundtrip"];N[label="All five public manual/API images\nand original recovered points agree\nwrong tags/nonodd inputs reject",fillcolor="#edf8ed"];T->N[style=dashed,arrowhead=none];}'''
(d/'runtime.dot').write_text(api+'\n');subprocess.run(['dot','-Tsvg',str(d/'runtime.dot'),'-o',str(d/'runtime.svg')],check=True)
pages=[[
'Prospective56fbbb precedes models and maps;52e030 precedes the reusable API addition. Native9722d7 uses a fresh checked SourceE and exactly matches ALL six original equations/H/Q/factors/kernels/P0s/whole quotient and rational-point records, then independently retains all135 product Lagrangians,4096 pairings and all9 rational kernels of Aprime:3product+6classical HLP. No private old instance is mutated.',
'All six actual target models are smooth; three have square D and three are nonsquare rejections. T values are95,168,203,119,215,138; D values182,12,126,120,95,201. Eligible(1,0),(1,1),(2,1) have P0s[1,0,84],[1,0,82],[1,0,75]. Full15-coefficient Moore descent, all three quotient identities, both geometric branches and actual origins pass. These are the classical HLP formulas, not a novelty claim.',
'Native02/9561ce passes one unfiltered test/all2485 selected hashes unchanged. Every eligible target has complete PhiPrime/NormPrime, both new[2], actual F=PhiPrime gamma Nold and G=PhiOld delta NormPrime. BOTH[52] hold on every224 old and224 new rational curve-point class; all intermediate classes and source points are retained. Each also checks36 source points, nonzero exact-ell2773073 images and all five unchanged public targets.',
'Written1fd6e7: global Ciani/V4 quotient correspondences give the dual[2] pairs, degree8 and polarization2; actual Res(gamma)/Res(delta) give both[13] and degree13^3. Scalar commutation yields GF=FG=[52], degree8*13^3*8=140608 and polarization52. Characteristic223 is coprime to52. Actual scheme/Picard/Galois/duality/degree interpretations remain written, with partial formalization. Finite panels support this argument and do not replace it.',
'The actual source and target elliptic j-conjugate sets are disjoint, so their canonically polarized products differ by the degree-one-column argument. If a new Jprime were F223-ppav-isomorphic to old J, its norm would transport a rational maximal-isotropic2-kernel to old J. The earlier unique-kernel result would force Aprime isomorphic to A, a contradiction. Each of the three actual endpoints differs from old J over F223. Mutual new-target and extension-field Jacobian isomorphisms remain undecided.'
],[
'For the original elliptic DLP define H(P)=F(PhiOld(P)); then delta NormPrime H(P)=[52]P. Exact52*159985=1+3*ell gives actual odd-source recovery159985 delta NormPrime. The reusable Chain API provides F/G and tagged original-source forward/recovery, with explicit source/target/field/order, odd membership and forward roundtrip checks. All five public manual/API images and recovered original points agree; runtime takes no known scalar.',
'All01 complete-map checks remain in02:100Phi+100Norm addition pairs each,48 alternate charts, all224 equal geometric line offsets, true multiplicity3 norm-omission control, all12 dual-number doubled-fibre versus wrong-linear checks, signed geometric infinities2+2, reachable K infinities, actual alternate P0 tags/zero origins and off-curve rejections. New controls reject two foreign translated-conjugate source A/B rows, an actual mismatched chain target, noncanonical/nonodd source, nonodd classes and wrong tags. Whole01/e1e62b remains preserved.',
'All three rational cofactor groups are C4. F has rational kernel sizes2,4,2; G has2,2,2. These observations do not classify the full geometric kernel or establish cost advantages. The specific next algebraic question is the transported Gold intersection on Aprime[2] via the actual gamma permutation[0,3,2,1], together with the13-primary factor, before labeling free(52,52,52) kernels.',
'Two faithful exact Lean bindings4d1338/95d4e6 pass both unchanged original4.35/4.34.1 gates:both global Jacobian52 and original-point52 compositions, derived from genuine dual2/source13 pairs and explicit scalar action/commutation laws. Neither52 conclusion nor an inverse is assumed. Two audited,zero trusted,no axioms;52 accumulated local bindings. Actual geometric interpretations remain written/open. First producer c4ffa9 redundant-rfl build failure is retained; only those tactics were deleted, statements unchanged.',
'Odd-source published3de8c174 is settled:independentfullb2b04d/all640 guards/13phasepairs/four actual admission controls;TEN-workflow CI5fee41/all84 native50 canonical digests match. New models/maps/proofs/report need source checkpoint and strict independent clean replay/CI. Nine new whole closed captures and both complete large map fixtures are queued for the unchanged genuine publisher; no raw data splitting, pruning or threshold change.',
'Original S3 benchmark checkpoint/live budget/capacity, complete transport/cold+online costs and strongest IC/rho references remain required for computational advantage. No performance ratio is reported. Earlier alternative-gluing/kernel/odd-source diagrams were checked and remain correct; new graphs add the actual different-product52 route and executable source recovery. Exact curve equations/P0s/model IDs are in identities.json; full native records remain under their catalogued immutable evidence paths.'
]]
for i,paragraphs in enumerate(pages,1):(d/('page'+str(i)+'.json')).write_text(json.dumps(paragraphs,indent=2)+'\n')
(d/'REPORT.md').write_text('# Actual prime-field Jacobian chains through the odd source\n\n2026-11-13. Unsigned; partial formal geometry.\n\n'+'\n\n'.join(p+' [pcc:unverified]'for page in pages for p in page)+'\n')
(d/'report.typ').write_text('''#set page(paper:"a4",margin:13mm)
#set text(font:"DejaVu Sans",size:9pt)
#set par(leading:.35em)
#text(size:17pt,weight:"bold")[Actual Jacobian transfers through a different product]
#parbreak()
2026-11-13 · N4 q223 / seed1 · unsigned / partial formalization
#parbreak()
#image("chain.svg",width:100%)
#for p in json("page1.json") {text(p);parbreak()}
#pagebreak()
#text(size:17pt,weight:"bold")[Executable source recovery and retained kernel outcomes]
#parbreak()
#image("runtime.svg",width:100%)
#image("outcomes.svg",width:100%)
#for p in json("page2.json") {text(p);parbreak()}
''')
for p in d.glob('*.svg'):p.write_text('\n'.join(x.rstrip()for x in p.read_text().splitlines())+'\n')
shutil.copyfile(s.parent/'chained-transfer-reference/reports/g3-norm-full-02/compile.py',d/'compile.py');shutil.copyfile(__file__,d/'render.py')
