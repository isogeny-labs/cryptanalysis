"""Render retained native/model records and written geometry; no cryptographic arithmetic."""
from pathlib import Path
import json,lzma,shutil,subprocess
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';d=s/'reports/alternative-gluing-01';d.mkdir(exist_ok=True)
models=json.loads(lzma.decompress((s/'evidence/gluing-models-acceptance-01/all-native-records.json.xz').read_bytes()));maps=json.loads(lzma.decompress((s/'evidence/gluing-maps-native-03-acceptance/all-native-records.json.xz').read_bytes()))
for name,rows in [('models-records.json.xz',models),('maps-records.json.xz',maps)]: (d/name).write_bytes(lzma.compress(json.dumps(rows,indent=2).encode()+b'\n'))
ms=[x['data']for x in models if x['kind']=='N4_GLUING_MODEL'];cs=[x['data']for x in maps if x['kind']=='N4_GLUING_MAP_CANDIDATE'];cv=[x['data']for x in maps if x['kind']=='N4_GLUING_MAP_COVERAGE']
fig,ax=plt.subplots(figsize=(6.5,1.8));labels=[str((m['root_index'],m['sign_index']))for m in ms];values=[m['T_equals_detH'][0]for m in ms];colors=['#43836b'if m['D_square_in_Fp_and_K']else'#b3813a'for m in ms];bars=ax.bar(labels,values,color=colors);ax.set(ylabel='T residue in F223',ylim=(0,223),title='All six fixed models: green square, amber nonsquare twist')
for b,v in zip(bars,values):ax.text(b.get_x()+b.get_width()/2,v+3,str(v),ha='center',fontsize=9)
fig.tight_layout();fig.savefig(d/'all-six.svg');plt.close(fig)
diagrams={
'models':'''digraph M {graph[rankdir=LR,bgcolor="transparent",ranksep=.4];node[shape=box,style="rounded,filled",fillcolor="#edf5fb",fontname="DejaVu Sans",fontsize=10];edge[fontname="DejaVu Sans",fontsize=10];A[label="A=Res(E) / F223\nK=F223[z]/(z^3-3)\nell2773073, order11092292"];K[label="135 original product Lagrangians\n9 rational = 3 product + 6 gluing\nALL actual E[2] coordinates"];S[label="4 smooth square models\n1 literal original + 3 alternatives",fillcolor="#e9f4eb"];T[label="2 smooth nonsquare twists\nretained; rejected for original source",fillcolor="#fff1d8"];A->K;K->S[label="all3 roots x both signs"];K->T;}''',
'chain':'''digraph C {graph[rankdir=LR,bgcolor="transparent",ranksep=.4];node[shape=box,style="rounded,filled",fillcolor="#edf5fb",fontname="DejaVu Sans",fontsize=10];edge[fontname="DejaVu Sans",fontsize=10];J[label="Jold / F223\nfixed N4 q223 seed1\nell2773073"];A[label="A=Res(E) / F223\nactual source E/K\nell2773073"];L[label="Jprime / F223\n(0,0), (0,1), (2,0)\nactual new quartics / own P0",fillcolor="#e9f4eb"];J->A[label="Nold : degree8"];A->J[label="Phiold : degree8"];A->L[label="PhiPrime : degree8"];L->A[label="NPrime : degree8"];J->L[label="F=PhiPrime Nold, degree64\nGF=[4], FG=[4]",color="#43836b"];L->J[label="G=Phiold NPrime",color="#43836b"];}''',
'endpoint':'''digraph E {graph[rankdir=LR,bgcolor="transparent",ranksep=.3];node[shape=box,style="rounded,filled",fillcolor="#edf5fb",fontname="DejaVu Sans",fontsize=10];edge[fontname="DejaVu Sans",fontsize=9];U[label="Old J has ONE rational\npolarized 2-kernel\ncensus + written theta bridge"];A[label="Aut(A,lambda) fixes A[2]\n3 distinct elliptic j values\ndegree columns sum to1"];I[label="If Jprime is F223-ppav iso to Jold\nthen gluing kernels equal",fillcolor="#fff1d8"];D[label="Literal control (1,0) identifies G_old\n3 other square masks differ\n3 endpoints differ from old over F223",fillcolor="#e9f4eb"];U->I;A->I;I->D;}'''}
for name,dot in diagrams.items():(d/(name+'.dot')).write_text(dot+'\n');subprocess.run(['dot','-Tsvg',str(d/(name+'.dot')),'-o',str(d/(name+'.svg'))],check=True)
table='; '.join(str((m['root_index'],m['sign_index']))+': T='+str(m['T_equals_detH'][0])+', D='+str(m['D'][0])+', '+('square'if m['D_square_in_Fp_and_K']else'nonsquare')for m in ms)
pages=[[
'Fixed q223 source: K=F223[z]/(z^3−3), prime ell=2773073, #E(K)=11092292. All standing unsigned. Prospective27369d precedes model code; HLP arXiv:math/9809210v1 §4.1 Lemma13/Propositions14–15 was read and its complete PDF digest retained. This is a classical gluing construction, not a novelty claim.',
'Native f33c42 audits all135 original Lagrangians, all4096 basis pairings and actual source2-torsion coordinates. Cyclic factor Frobenius fixes exactly9 kernels:3 product and6 distinct HLP gluings. Whole stable sets, rather than only counts, match the explicit kernels. The original81split/54nonsplit and identity/transvection controls remain.',
'For all3 source2-torsion roots and both signs, form H diagonal hi/off-diagonal−Ai with h2h3=Delta1 cyclically, Q=adj(H). Native checks verify the original HLP model after scaling by−1/4, twisting factor T=det(H), all15 Moore-descended coefficients, original smoothness and all three quotient Jacobians AX=D*Ai,BX=D²*Bi,D=16T. All six models are smooth; four are square eligible and two retain nonsquare twist obstructions.',
table+'. Candidate(1,0) reproduces the original normalized15 coefficients exactly; the other arrays alone are not endpoint evidence.',
'Every model has224 rational curve points. Both Fp6 square-root signs satisfy the quotient equations and differ by actual2-torsion translation. Subtracting the actual P0 image gives sign-independent K descent. Compiler failure01/1e3436 is retained; the fix changes only calls to the original field constructor API.'
],[
'Protocol626d84 fixes ALL four eligible models before map code. The new adapter recomputes quartic/P0/model tags, degree6 normal forms and raw trace origin. PhiPrime traces complete degree2 fibre ideals with multiplicity and subtracts only the actual Q=0 fibre. NPrime reconstructs the original length3 divisor algebra, sums all raw geometric images with multiplicity and subtracts the actual residual-line Dinf offset. It is a whole-group norm, not doubled-norm halving.',
'Native03/7c9bf4 passes one unfiltered test/all2401 input hashes unchanged. Every candidate checks32 source points, all224 new point classes and224 original point classes, both[2] compositions and both[4] chained compositions, nonzero exact-ell generator images, all five public targets and independent known-answer equalities. Runtime inputs contain coordinates and model tags only.',
'Each candidate checks100 pullback and100 norm addition pairs,48 alternate charts and all224 equal geometric line offsets. All12 sign-branch points carry dual-number doubled-fibre controls that reject the wrong linear fibre; multiplicity3 omission changes every candidate norm. Raw quotient infinity signs occur2+2 geometrically. Reachable K inverse-infinity counts are2/0/2/0; in the other cases alpha is nonsquare in K, so those infinities are not K-rational. Fresh alternate-P0 tags, zero origins and off-curve controls pass.',
'First map native01/ec6f14 compiled but failed the trace-origin rank check because the fresh adapter used the default cubic basis. The corrected adapter pins x^3−3 and compares all9 basis products and3 Frobenius images to independent FpR. Whole01, intermediate pass02/8e56fa and expanded03 are preserved; no fitted shift/scalar, source selection or original engine change.'
],[
'Written5f7e4c: the global Ciani V4 quotient is genus0; its group-algebra trace vanishes on the Jacobian. The three degree2 quotient pullback/norm pairs therefore give both[2] compositions; cross homomorphisms vanish by the induced involution−1 and connected image in finite2-torsion. Frobenius permutes the factors, square D lies in F223 and auxiliary sqrt(alpha) choices change only translations, so the induced degree-zero maps descend.',
'Thus F=PhiPrime*Nold and G=Phiold*NPrime satisfy GF=[4],FG=[4]. Odd prime ell makes4 invertible, preserving the original DLP. The literal original candidate returns the old map with fixed sign+1 and the trivial[2] chain. This positive control is retained.',
'Endpoint argument: the old J has one rational polarized2-kernel. Any F223-ppav isomorphism from a candidate to old J would identify their dual quotient maps up to a polarized automorphism of A. The three elliptic j conjugates are distinct and not0/1728. Restricting the product polarization to each factor forces a single degree1 component, so every such automorphism acts by factor signs and fixes A[2]. Hence its gluing kernel must equal the original literal-control kernel. The other three square kernel masks differ, so each target differs from old J over F223. Mutual or geometric-extension isomorphism classes are not asserted.',
'All four rational cofactor groups are C4: that attempted endpoint discriminator is negative. Eleven feasible Lean lemmas pass both unchanged4.35/4.34.1 gates with zero trusted declarations:8 general model identities and3 chain/injectivity/degree implications. Exact local PCC bindings are unsigned. Polynomial/degree lemmas use standard propext/Classical.choice/Quot.sound; two functional lemmas use no axioms. Actual abelian/Picard/V4/Galois/theta/polarization geometry remains written, not fully formalized.',
'No computational advantage or security conclusion follows. Complete map counters, original S3 checkpoint/live budget/capacity admission and strongest reference algorithms remain open. Next: clean independent full/own CI, genuine whole-data handoff, then actual chain-kernel structure and further nondual walks. Existing V2/bitangent/kernel reports remain frozen; this new graph adds the actual alternative route with its unsigned and partial-formal scope.'
]]
identities=[dict(candidate=x['candidate'],field='F223',normalized_quartic=x['quartic'],P0=x['P0'],full_native_Jacobian_model_tag=x['Jacobian_model_tag'])for x in cs]
(d/'identities.json').write_text(json.dumps(identities,indent=2)+'\n')
pages[1].append('Exact target identifiers for the three alternatives in the diagram: '+'; '.join(str(tuple(x['candidate']))+' = '+x['Jacobian_model_tag']for x in cs if not x['literal_original_quartic_control'])+'. identities.json gives every full normalized equation and P0, including the original control.')
for i,page in enumerate(pages,1):(d/f'page{i}.json').write_text(json.dumps(page,indent=2)+'\n')
(d/'REPORT.md').write_text('# Actual alternative gluing models and chained Jacobian maps\n\n2026-11-13. Unsigned; formalization partial.\n\n'+'\n\n'.join(p+' [pcc:unverified]'for page in pages for p in page)+'\n\nSources: protocols27369d/626d84, nativef33c42/7c9bf4, written5f7e4c, all11 exact local bindings, HLP primary-source digest, unchanged original engines. Editable sources and complete native JSON are adjacent. [pcc:unverified]\n')
(d/'report.typ').write_text('''#set page(paper:"a4",margin:13mm)
#set text(font:"DejaVu Sans",size:8.8pt)
#set par(leading:.35em)
#text(size:17pt,weight:"bold")[Six classical models; four square candidates]
#parbreak()
2026-11-13 · actual N4 q223 / seed1 · unsigned / partial formalization
#parbreak()
#image("models.svg",width:100%)
#image("all-six.svg",width:93%)
#for p in json("page1.json") {text(p);parbreak()}
#pagebreak()
#text(size:17pt,weight:"bold")[Actual whole-group maps and longer chains]
#parbreak()
#image("chain.svg",width:100%)
#for p in json("page2.json") {text(p);parbreak()}
#pagebreak()
#text(size:17pt,weight:"bold")[Why the three alternatives differ from old J]
#parbreak()
#image("endpoint.svg",width:100%)
#for p in json("page3.json") {text(p);parbreak()}
''')
for p in d.glob('*.svg'):p.write_text('\n'.join(line.rstrip()for line in p.read_text().splitlines())+'\n')
shutil.copyfile(s.parent/'chained-transfer-reference/reports/g3-norm-full-02/compile.py',d/'compile.py');shutil.copyfile(__file__,d/'render.py')
