"""Native-record plots, diagrams and written proof/proposal rendering only."""
from pathlib import Path
import json,lzma,shutil,subprocess
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';d=s/'reports/kernel-census-01';d.mkdir()
c=json.loads(Path('/workspace/scratch/ct59-kernel-census-native-01/all-native-records.json').read_text());v=json.loads(Path('/workspace/scratch/ct59-kernel-replay-native-01/all-native-records.json').read_text())
for name,rows in [('census-records.json.xz',c),('replay-records.json.xz',v)]: (d/name).write_bytes(lzma.compress(json.dumps(rows,indent=2).encode()+b'\n'))
controls=next(x['data']for x in c if x['kind']=='N4_KERNEL_CENSUS_CONTROLS')
fig,ax=plt.subplots(figsize=(6.8,2.4));values=[controls['identity_kernels'],controls['transvection_kernels'],controls['generic_representative_stable_count']];bars=ax.bar(['Identity control','Transvection control','Actual compatible class'],values,color=['#38749b','#bd852d','#43836b']);ax.set(ylabel='Stable kernels among135',ylim=(0,150),title='Exact finite counts; all compatible actions share the last count')
for b,y in zip(bars,values):ax.text(b.get_x()+b.get_width()/2,y+3,str(y),ha='center')
fig.tight_layout();fig.savefig(d/'kernel-counts.svg');plt.close(fig)
diagrams={
'finite':'''digraph F {graph[rankdir=LR,bgcolor="transparent",ranksep=.25];node[shape=box,style="rounded,filled",fillcolor="#edf5fb",fontname="DejaVu Sans",fontsize=11];edge[fontname="DejaVu Sans",fontsize=10];G[label="ALL Sp6(F2) actions\n1,451,520 distinct matrices"];M[label="Actual28-line cycle type\nand2 fixed vectors\n120,960 actions"];K[label="ONE stable Lagrangian\noriginal135 kernels\ncentralizer cross-check12",fillcolor="#fff3da"];G->M[label="both predicates"];M->K[label="all135 / conjugacy"];}''',
'norm':'''digraph N {graph[rankdir=LR,bgcolor="transparent",ranksep=.55];node[shape=box,style="rounded,filled",fillcolor="#edf5fb",fontname="DejaVu Sans",fontsize=10];edge[fontname="DejaVu Sans",fontsize=10];A[label="A=Res(E) / F223\nA(F223)=E(K), K=F223[z]/(z^3-3)\nell=2773073, order=11092292\nnatural product principal polarization"];J[label="J=Jac(C) / F223\nfixed N4 q223 / seed1\nell=2773073, order=11092292\ncanonical principal polarization"];A->J[label="Phi: degree8\nquotient pullbacks"];J->A[label="N: degree8 / unique kernel\nN*lambda_A=2lambda_J"];}''',
'proposal':'''digraph P {graph[rankdir=LR,bgcolor="transparent",ranksep=.32];node[shape=box,style="rounded,filled",fillcolor="#edf5fb",fontname="DejaVu Sans",fontsize=11];edge[fontname="DejaVu Sans",fontsize=10];J[label="Actual J / F223\nN4 q223 / seed1\nell2773073"];A[label="A=Res(E) / F223\nexisting norm target\nchoose different gluing"];T[label="Jprime / F223\nPROPOSED target\nmodel/maps not implemented",fillcolor="#fff3da"];J->A[label="existing N"];A->T[label="proposed PhiPrime\ndifferent kernel",style=dashed];T->J[label="reverse proposed\ncompositions[4] required",style=dashed,color="#8b6e42"];}'''}
for name,dot in diagrams.items():(d/(name+'.dot')).write_text(dot+'\n');subprocess.run(['dot','-Tsvg',str(d/(name+'.dot')),'-o',str(d/(name+'.svg'))],check=True)
pages=[[
'Unsigned computational premises c88589/907dfc: the actual fixed q223 quartic has bitangent Frobenius cycles1,3,6,6,6,6 and exactly2 rational geometric2-torsion points from its rational C4 cofactor group. Odd theta characteristics give a Galois-equivariant quadratic-refinement interpretation; this standard geometric bridge is explicit, not an identification with actual hyperelliptic Weierstrass points.',
'The producer certifies all135 original Lagrangians and an explicit abstract symplectic basis, including4096 pairing pairs. It enumerates all1,451,520 distinct symplectic matrices. Exactly120,960 match both actual predicates; all have one stable kernel. Identity and transvection controls give135 and15, with odd fixed counts28 and16. Every matrix, including rejected ones, remains in the13,063,688-byte binary.',
'A different read-only replay uses Gaussian rank, quadratic truth-table fixed powers and sixth-power identity. It reads all1,451,520 rows and matches every producer predicate/count byte. The original S8 representative has one stable kernel and centralizer12. Its conjugacy class has1,451,520/12=120,960 elements; conjugacy invariance plus inclusion and equal finite cardinality identifies the entire compatible set with that class.',
'One unfiltered test passes in each crate, all2361 producer and2366 replay input hashes unchanged, including the binary. These are finite algebra correctness observations, not a benchmark or a trusted producer-independent execution backend. No actual torsion basis, kernel coordinates or new quotient map is output.'
],[
'Written polarization audit c2270b: for A=Res(K/F223)E and J=Jac(C), the three Ciani degree-two quotient pullbacks sum to Phi and their norms give N. Canonical Jacobian/product polarizations make them dual. The written V4 argument gives both compositions[2], hence equal degrees8 and N*lambda_A=2lambda_J. Source model signs/translations do not change that induced polarized statement.',
'Therefore ker N lies in J[2], is etale of order8 in characteristic223, and is maximal isotropic by the polarization descent criterion. It is defined over F223, so is the unique stable Lagrangian found above. Every F223-rational polarized(2,2,2) quotient has the same kernel and is principally polarized isomorphic to A.',
'Geometrically the product theta divisor of A is reducible. The canonical theta divisor of a smooth connected genus3 Jacobian is a translate of W2, the image of the irreducible symmetric square, hence irreducible. Thus this fixed J has no further F223-rational polarized(2,2,2) Jacobian target. Other degrees, fields, polarizations, arbitrary degree8 maps and longer chains are not excluded.',
'Five faithful named Lean bindings392a95/039ca3/9f99f1/e7e736/ea637d pass both unchanged original4.35/4.34.1 gates:8 audited declarations including3 generated count equations,zero trusted. They prove closed arithmetic, stability/isotropy transport and finite inclusion/equal-count implications. Actual group cardinality, execution, theta/Galois/Weil-pairing and polarized/Jacobian geometry remain written bridges. Original failed01 redundant generalizing annotations are preserved6956b2; only those two tactics changed and all5 statement hashes remain identical.',
'Primary sources actually read: Mumford(1971),pp181–182 for theta parity/quadratic refinements; Milne AV,Theorem11.1,Proposition16.8,Remark16.9; Milne JV,Section5/Theorem5.1 and Summary6.11. URLs and complete PDF digests are in evidence/kernel-primary-math-01. They support standard mathematical bridges, not native execution verification.'
],[
'The fixed-degree obstruction does not stop longer chains. A different gluing A→Jprime could extend the existing J→A norm. The expected nine rational kernels of A[2], split into three product and six gluing candidates, require a separate check. These are not the single kernel of J[2]. Proposal f1d44f freezes all3 actual source2-torsion roots and both simultaneous sign choices, without discarding failed candidates.',
'Proposed coordinate construction: translate a chosen source2-torsion root to0 to obtain Ei:y²=x(x²+Ai*x+Bi), with conjugate coefficients. Let Delta_i=Ai²−4Bi, choose h2*h3=Delta1,h1*h3=Delta2,h1*h2=Delta3, and set H diagonal hi with off-diagonals−A3,−A2,−A1. The proposed Ciani matrix is adj(H). Independent native/Lean and primary split-gluing literature checks are required before any new model claim.',
'The predicted quotient coefficients are D*Ai,D²*Bi with D=16det(H). Require Frobenius descent of all15 curve coefficients, nonzero smoothness factors and an actual square-twist test. Keep singular, nonsquare, repeated and inconclusive models. Matching quotient invariants alone supplies no homomorphism. Actual origins, finite/infinite fibres, multiplicity, field descent and nonzero prime-ell transport remain required.',
'If actual PhiPrime/NPrime with both[2] compositions and a distinct Jprime are constructed, PhiPrime*N and Phi*NPrime should have both[4] compositions. The identical original gluing remains the trivial[2] control. Endpoint distinctness needs a valid projective invariant or explicit isomorphism analysis, not different coefficient arrays. No proposed target, new map or computational advantage is yet established.',
'Next: publish this census/proof/report checkpoint, execute its clean independent replay and own CI, then validate the proposed alternative gluing coordinates. Parent bitangent source85b independently passes fullaf9044/all523 guards and allsix workflows/f9535f, matching50 native records and25 original canonical PCC digests. New raw captures need the next genuine whole-data handoff. Benchmark checkpoint/live budget/capacity, complete accounting and strongest references remain open.'
]]
for i,page in enumerate(pages,1):(d/f'page{i}.json').write_text(json.dumps(page,indent=2)+'\n')
(d/'REPORT.md').write_text('# Actual q223 kernel census and a fixed polarized-degree obstruction\n\n2026-11-13. Standing unsigned; formalization partial.\n\n'+'\n\n'.join(p+' [pcc:unverified]'for page in pages for p in page)+'\n\nSources: KERNEL_CENSUS_PROTOCOL_01.md,KERNEL_REPLAY_PROTOCOL_01.md,KERNEL_OBSTRUCTION_DERIVATION_01.md,GLUING_CHAIN_PROPOSAL_01.md; nativec88589/907dfc; original Smith module; exact five bindings/whole proof captures; primary sources metadata. Existing reports/v2-native-02/flow.dot and bitangent coordinate graph remain current; no new verified isogeny endpoint is added. The dashed gluing route is a proposal only. Editable DOT/SVG/plot/renderer/Typst and native JSON are adjacent.\n')
(d/'report.typ').write_text('''#set page(paper:"a4",margin:14mm)
#set text(font:"DejaVu Sans",size:9.2pt)
#set par(leading:.4em)
#text(size:18pt,weight:"bold")[A complete compatible-kernel census]
#parbreak()
2026-11-13 · fixed N4 q223 / seed1 · unsigned / partial formalization
#parbreak()
#image("finite.svg",width:100%)
#image("kernel-counts.svg",width:96%)
#for p in json("page1.json") {text(p);parbreak()}
#pagebreak()
#text(size:18pt,weight:"bold")[The unique kernel is the original norm kernel]
#parbreak()
#image("norm.svg",width:100%)
#for p in json("page2.json") {text(p);parbreak()}
#pagebreak()
#text(size:18pt,weight:"bold")[Next: a different gluing on the intermediate]
#parbreak()
#image("proposal.svg",width:100%)
#for p in json("page3.json") {text(p);parbreak()}
#text(size:8.5pt)[All exact matrices and observations are retained. Conditional written geometry and partial formalization are explicit; no stronger ECDLP/security or performance conclusion is made.]
''')
for p in d.glob('*.svg'):p.write_text('\n'.join(line.rstrip()for line in p.read_text().splitlines())+'\n')
shutil.copyfile(s.parent/'chained-transfer-reference/reports/g3-norm-full-02/compile.py',d/'compile.py');shutil.copyfile(__file__,d/'render.py')
