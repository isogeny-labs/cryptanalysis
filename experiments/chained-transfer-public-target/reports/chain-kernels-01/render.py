"""Visualize the retained intersection/map outputs; no crypto computation."""
from pathlib import Path
import json,lzma,shutil,subprocess,sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';d=Path(sys.argv[1])if len(sys.argv)>1 else s/'reports/chain-kernels-01';d.mkdir()
rows=json.loads(lzma.decompress((s/'evidence/chain-kernel-acceptance-01/all-native-records.json.xz').read_bytes()));inter=next(x['data']for x in rows if x['kind']=='N4_CHAIN_KERNEL_INTERSECTIONS');types=next(x['data']for x in rows if x['kind']=='N4_CHAIN_KERNEL_TYPES')['all9_rational_cases']
bindings=json.loads((s/'evidence/chain-kernel-bindings-01/claims.json').read_text());assert len(bindings)==3
for x in bindings:
 name=x['theorem'].split('.')[-1];v=json.loads((s/'evidence/chain-kernel-bindings-01'/(name+'-verdict.json')).read_text());assert v['verdict']=='pass'and not v['reasons']
(d/'all-native-records.json.xz').write_bytes(lzma.compress(json.dumps(rows,indent=2).encode()+b'\n'))
names=[x['kernel']for x in types];short=[n.replace('product-Q','P').replace('HLP-','G')for n in names];tab={(x['first'],x['second']):x['dimension']for x in inter['all9x9_rational_intersections']};matrix=[[tab[(a,b)]for b in names]for a in names]
fig,axes=plt.subplots(1,2,figsize=(7.6,2.9),gridspec_kw={'width_ratios':[1,1.3]});ax=axes[0];hist=inter['actual_dimension_histogram'];vals=[hist[str(i)]for i in range(4)];bars=ax.bar(range(4),vals,color='#367c97');ax.set(xlabel='Intersection dimension d',ylabel='Lagrangians',title='All135 original kernels',xticks=range(4),ylim=(0,72))
for b,v in zip(bars,vals):ax.text(b.get_x()+b.get_width()/2,v+1,str(v),ha='center',fontsize=9)
ax=axes[1];im=ax.imshow(matrix,vmin=0,vmax=3,cmap='Blues');ax.set(xticks=range(9),yticks=range(9),xticklabels=short,yticklabels=short,title='All9×9 rational intersections');ax.tick_params(axis='both',labelsize=7);plt.setp(ax.get_xticklabels(),rotation=45,ha='right')
for i,row in enumerate(matrix):
 for j,x in enumerate(row):ax.text(j,i,str(x),ha='center',va='center',fontsize=7,color='white'if x>=2 else'black')
fig.colorbar(im,ax=ax,ticks=range(4),label='dimension');fig.tight_layout();fig.savefig(d/'intersections.svg');plt.close(fig)
dots={'kernels':'''digraph K {graph[rankdir=LR,bgcolor="transparent",ranksep=.35];node[shape=box,style="rounded,filled",fillcolor="#edf5fb",fontname="DejaVu Sans",fontsize=10];edge[fontname="DejaVu Sans",fontsize=10];J[label="Jold / F223\nN4 q223 / seed1\nell2773073"];A[label="A=Res(E) / F223\nK=F223[z]/(z^3-3)\nG_old explicit literal kernel"];L[label="Jprime / F223\nactual eligible HLP models\nfull IDs in identities.json"];J->A[label="Nold: degree8"];A->L[label="PhiPrime: degree8"];J->L[label="F: degree64, G F=[4]\nd=dim(Gold intersect G)\nker(F)=C4^(3-d) x C2^(2d)",color="#43836b"];}''',
'collapse':'''digraph C {graph[rankdir=LR,bgcolor="transparent",ranksep=.45];node[shape=box,style="rounded,filled",fillcolor="#edf5fb",fontname="DejaVu Sans",fontsize=11];edge[fontname="DejaVu Sans",fontsize=10];I[label="Jold / F223\nfixed original"];B[label="Jb / F223\nany of4 eligible models"];C[label="Jc / F223\nany of4 eligible models"];I->B[label="PhiB Nold"];B->C[label="PhiC NB"];I->C[label="composition = [2] direct(PhiC Nold)\nALL128 actual route checks",color="#43836b"];S[label="Same A used in both edges\nLonger path = known scalar x direct\nNo implementation cost lower bound",fillcolor="#fff1d8"];B->S[style=dashed,arrowhead=none];}'''}
for name,dot in dots.items():(d/(name+'.dot')).write_text(dot+'\n');subprocess.run(['dot','-Tsvg',str(d/(name+'.dot')),'-o',str(d/(name+'.svg'))],check=True)
shutil.copyfile(s/'reports/alternative-gluing-01/identities.json',d/'identities.json')
eligible=[x for x in types if x['eligible_original_source_Jacobian']];table='; '.join(x['kernel']+': d='+str(x['intersection_dimension_with_Gold'])+', C4^'+str(x['geometric_kerF_C4_factors'])+' × C2^'+str(x['geometric_kerF_C2_factors'])for x in eligible)
pages=[[
'Prospectivea94132 precedes code. Native29830a passes one unfiltered test/all2432 selected hashes unchanged. It independently obtains all135 original Smith Lagrangians, matches the entire actual product-model set and all4096 pairings, and retains every intersection with the literal original Gold plus the whole9x9 rational table. All standing unsigned.',
'The all135 dimension0/1/2/3 histogram is64/56/14/1. Every rational-table entry includes its actual A[2] coordinate triples and every vector, with closure, isotropy, Frobenius, symmetry and diagonal controls. Product kernels and both nonsquare HLP cases remain distinct rows; the latter are not eligible original-source Jacobians over F223.',
'Written2e21d5: F=PhiG*Nold has degree64, its reverse composes to[4], and ker(F) is etale and killed by4 in characteristic223. Restricting Nold:Jold[2]→Gold has kernel8 and image Gold. Therefore ker(F)[2] has8*2^d geometric points, where d=dim(Gold∩G). Finite abelian exponent4 classification gives C4^(3−d)×C2^(2d). Polarization multiplier4 makes the d=0 cases free maximal-isotropic(4,4,4) kernels.',
table+'. The two free cases are(0,0) and(2,0). Degree64 alone does not establish a free kernel. These are derived geometric group types, not constructed Jold[4] divisor coordinates. The actual rational F kernel has only2 points in all four cases, so rational cofactor counts do not distinguish these geometric types.'
],[
'For ALL four eligible interior nodes Jb and ALL four final nodes Jc, the same A gives (PhiC*Nb)*(PhiB*Nold)=PhiC*[2]_A*Nold=[2]_Jc*(PhiC*Nold). This is a global homomorphism consequence of the dual[2] identities, without fitting a path-dependent scalar. A path ofL≥1 such edges reduces to[2^(L−1)] times its direct endpoint transfer.',
'Native29830a checks all4×4×8=128 actual repeated routes on the first eight canonical old curve-point classes, retaining complete intermediate, direct and composed class outputs. The literal original control is included. All four actual rational cofactor kernels contain2 points. These finite checks support the written identity; they do not replace its global proof.',
'Thus longer paths through the SAME A supply no new normalized homomorphism. This does not invalidate the three distinct one-step endpoints and does not prove an implementation cost lower bound: an intermediate representation could still compute the same map more cheaply, requiring admitted measurement.',
'Three faithful exact local Lean bindings pass both unchanged original4.35/4.34.1 gates/zero trusted: cbaaa0 for kernel-type equations,580339 for free4 iffdisjoint,0cc751 for functional collapse from actual dual[2] pairs. The functional theorem uses no axioms; arithmetic uses standard propext/Classical.choice/Quot.sound. Etale degree, exact torsion sequence, finite-abelian classification, polarization and actual Picard-map interpretations remain written bridges. No actual J[4] basis or signed execution is supplied.',
'Next: genuine whole-data publication and current source checkpoint, then a different justified product/degree. An odd-degree source isogeny E→Eprime and dual could lead through Res(Eprime), with expected Jacobian compositions[4*l]; this is a proposed successor requiring its own source review/protocol and actual maps. Original S3 checkpoint/live budget/capacity, complete counters and strongest references remain required for any computational advantage claim. No timing or speed comparison is reported.',
'The existing alternative-gluing model/chain/endpoint graphs were checked: their degree64 and both[4] labels remain correct. New diagrams add the geometric kernel distinction and same-product collapse. Full current target IDs/equations/P0 are in identities.json; old frozen report bytes remain unchanged.'
]]
for i,p in enumerate(pages,1):(d/f'page{i}.json').write_text(json.dumps(p,indent=2)+'\n')
(d/'REPORT.md').write_text('# Actual chain-kernel structure and same-product collapse\n\n2026-11-13. Unsigned; formal geometry partial.\n\n'+'\n\n'.join(p+' [pcc:unverified]'for page in pages for p in page)+'\n')
(d/'report.typ').write_text('''#set page(paper:"a4",margin:13mm)
#set text(font:"DejaVu Sans",size:9pt)
#set par(leading:.35em)
#text(size:17pt,weight:"bold")[Which chained kernels are free over Z/4?]
#parbreak()
2026-11-13 · actual N4 q223 / seed1 · unsigned / partial formalization
#parbreak()
#image("kernels.svg",width:100%)
#image("intersections.svg",width:100%)
#for p in json("page1.json") {text(p);parbreak()}
#pagebreak()
#text(size:17pt,weight:"bold")[Repeated routes through the same product collapse]
#parbreak()
#image("collapse.svg",width:100%)
#for p in json("page2.json") {text(p);parbreak()}
''')
for p in d.glob('*.svg'):p.write_text('\n'.join(line.rstrip()for line in p.read_text().splitlines())+'\n')
shutil.copyfile(s.parent/'chained-transfer-reference/reports/g3-norm-full-02/compile.py',d/'compile.py');shutil.copyfile(__file__,d/'render.py')
