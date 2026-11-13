"""Render retained native data and written conclusions; no cryptographic computation."""
from pathlib import Path
import json,lzma,shutil,subprocess
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';d=s/'reports/odd-source-01';d.mkdir()
raw=(s/'evidence/odd-source-acceptance-02/all-native-records.json.xz').read_bytes();rows=json.loads(lzma.decompress(raw));m=rows[0]['data'];js=rows[3]['data']
(d/'all-native-records.json.xz').write_bytes(raw)
(d/'identities.json').write_text(json.dumps({key:m[key]for key in ['field_modulus','field_tag','source_quadratic_model','source_short','target_short','target_id','degree','original_order','ell']},indent=2)+'\n')
fig,ax=plt.subplots(figsize=(7.2,1.8));steps=m['forward_kernel']['all_six_Frobenius_steps'];degrees=[len(x['gcd'])-1 for x in steps]
ax.plot(range(1,7),degrees,'o-',color='#287b8e');ax.set(xlabel='Iterated qK Frobenius power n',ylabel='gcd degree',title='Actual full psi13: both source and target',xticks=range(1,7),yticks=[0,6,12],ylim=(-1,14))
for i,v in enumerate(degrees,1):ax.annotate(str(v),(i,v),xytext=(0,5),textcoords='offset points',ha='center',fontsize=9)
fig.tight_layout();fig.savefig(d/'frobenius.svg');plt.close(fig)
dots={
'actual':'''digraph I {graph[rankdir=LR,bgcolor="transparent",ranksep=.55];node[shape=box,style="rounded,filled",fillcolor="#edf5fb",fontname="DejaVu Sans",fontsize=10];edge[fontname="DejaVu Sans",fontsize=10];E[label="E / K=F223[z]/(z^3-3)\ny^2=x^3+a*x+b\na=(214,144,205)\nb=(137,218,9)\norder11092292 / ell2773073"];P[label="Eprime / SAME K\ny^2=x^3+aPrime*x+bPrime\naPrime=(196,168,69)\nbPrime=(8,82,207)\nfull IDs in identities.json"];E->P[label="gamma: actual degree13\nKohel kernel / SEA eigenvalue2"];P->E[label="delta: actual normalized dual\nSEA eigenvalue4; divide x/13^2,y/13^3"];S[label="BOTH compositions=[13]\nALL full x/y polynomial identities\nnonzero odd image / five public targets",fillcolor="#edf8ed"];E->S[style=dashed,arrowhead=none];P->S[style=dashed,arrowhead=none];}''',
'proposed':'''digraph J {graph[rankdir=TB,bgcolor="transparent",nodesep=.5,ranksep=.45,label="PROPOSED F degree140608 / reverse G\\nCONDITIONAL both[52]; no cost conclusion",labelloc=t,fontname="DejaVu Sans",fontsize=11];node[shape=box,style="rounded,filled",fillcolor="#edf5fb",fontname="DejaVu Sans",fontsize=11];edge[fontname="DejaVu Sans",fontsize=10];J[label="Jold / F223\\nactual q223/seed1"];A[label="A=Res(E) / F223\\noriginal product"];B[label="Aprime=Res(Eprime) / F223\\nactual disjoint j-conjugate sets"];L[label="Jprime / F223\\nNOT YET CONSTRUCTED",fillcolor="#fff1d8"];{rank=same;J;L};{rank=same;A;B};J->A[label="Nold degree8 / actual"];A->B[label="Res(gamma) degree13^3\\nwritten interpretation",constraint=false];B->L[label="PhiPrime degree8\\nPROPOSED",style=dashed,constraint=false];J->L[style=dashed,color="#ad6b24",constraint=false];}'''}
for name,dot in dots.items():(d/(name+'.dot')).write_text(dot+'\n');subprocess.run(['dot','-Tsvg',str(d/(name+'.dot')),'-o',str(d/(name+'.svg'))],check=True)
pages=[[
'Prospectivee9234b precedes code. Native02/de87bd passes one unfiltered test and all2452 selected hashes remain unchanged. Original field, polynomial, division-polynomial, Kohel, SEA and affine group engines are reused as ordinary dependencies. First build101/1ea2d5 preserved seven nonexistent-square-API errors; the sole repair calls existing original multiplication. No native failure is omitted.',
'The entire degree84 psi13 is squarefree. Six actual qK Frobenius gcd degrees are0,0,6,0,0,12. D6/D3 gives the degree6 forward kernel/eigenvalue2. On Eprime, D3 gives the normalized dual kernel/eigenvalue4. Their first-power gcds are1, so neither kernel has a K-rational nonidentity point. No unsupported point-extension representation or placeholder generator is used.',
'For each normalized map xPrime=N/D, yPrime=y*T/D^2, T=Nprime*D-N*Dprime. The FULL identity S*T^2=N^3*D+aPrime*N*D^3+bPrime*D^4 has zero polynomial residual. Each deliberately wrong target b coefficient fails. Numerator/denominator degrees13/12 and gcd1, plus smooth projective extension and O preservation, give actual degree13 homomorphisms in the written argumentb9a91f (Milne AV Cor2.2/Thm3.1).',
'The normalized dual codomain is E(13^4*a,13^6*b); output scaling x/13^2,y/13^3 gives delta:Eprime→E. BOTH full x AND y composition cross-polynomials agree with multiplication[13], each x degree169/168/coprime. Raw division polynomials retain leading13; y13=y*x13prime/13. Whole coefficients are in all-native-records.json.xz, not replaced by random point evaluations.'
],[
'Native checks retain all36 source and36 target samples, both[13] compositions,1024 homomorphism pairs in each direction, all four rational2-torsion points bijectively, two off-curve rejections, the nonzero exact-ell2773073 generator image and all five unchanged public targets. Known answers are test-only and stay outside runtime map inputs. Source and target equations, field/model tags and full map polynomials are explicit.',
'Actual source j conjugates are(166,136,127),(166,135,47),(166,175,49); target conjugates(217,167,46),(217,10,10),(217,46,167). They are disjoint. A polarized product isomorphism would have degree-one columns, forcing an elliptic isomorphism between the two sets. The written argument excludes this, so Aprime is a different canonically polarized product. This establishes no computational advantage.',
'Since both exact rational kernels are trivial, gamma and delta inject finite K-point groups in opposite directions; their orders equal the original11092292 and gamma is bijective. Odd inverse=[639940]delta uses13*639940=1+3*ell. Whole rational inverse=[3413013]delta uses13*3413013=1+4*11092292. These inverse scopes are distinct; no DLP table or scalar fitting is used.',
'Six faithful exact partial Lean bindings pass both unchanged original4.35/4.34.1 gates/zero trusted: c6dca4 curve-equation clearing,796f92 scaling,7781ea scalar recovery from action/composition/torsion axioms and Bezout,ee0e7e odd13,82763b whole13,caa2b3 proposed52 integer certificates. Ring lemmas use standard propext/Classical.choice/Quot.sound; recovery and integers use no axioms. Whole proof capturesb32320/67342c. Initial caller PATH not-covered78ddb7 is retained; the SAME first claim later passes. Actual curves/morphisms/degree/dual/finite-group/product interpretations remain written,50 local bindings total.',
'Next independently construct every HLP outcome for Aprime with fresh typed source/model/origin identities and complete PhiPrime/NormPrime. Only CONDITIONAL on those maps, F=PhiPrime*Res(gamma)*Nold and G=PhiOld*Res(delta)*NormPrime give both[52], degree140608 and odd inverse[159985]G. No new Jacobian or actual[52] map is yet supplied. Original S3 checkpoint/live budget/capacity, complete costs and strongest references remain required for a performance claim.',
'Prior kernel fullf4c0a7/all617 guards and nine-workflow CI6add5b/all80 native44 canonical digests are settled. New odd-source ci_odd freezes639 portable inputs/640 with manifest, thirteen phases,ALL4 whole JSON,both original6-proof gates/6 bindings; own clean full/CI is pending. New diagrams add the actual odd source and explicitly conditional successor. Previous gluing/kernel diagrams were checked and remain correct.'
]]
for i,paragraphs in enumerate(pages,1):(d/('page'+str(i)+'.json')).write_text(json.dumps(paragraphs,indent=2)+'\n')
(d/'REPORT.md').write_text('# Actual degree13 source map and a different product\n\n2026-11-13. Unsigned; partial formal geometry.\n\n'+'\n\n'.join(p+' [pcc:unverified]'for page in pages for p in page)+'\n')
(d/'report.typ').write_text('''#set page(paper:"a4",margin:13mm)
#set text(font:"DejaVu Sans",size:9pt)
#set par(leading:.35em)
#text(size:17pt,weight:"bold")[An actual odd source isogeny over the cubic field]
#parbreak()
2026-11-13 · N4 q223 / seed1 · unsigned / partial formalization
#parbreak()
#image("actual.svg",width:100%)
#image("frobenius.svg",width:100%)
#for p in json("page1.json") {text(p);parbreak()}
#pagebreak()
#text(size:17pt,weight:"bold")[A different product; the next Jacobian remains proposed]
#parbreak()
#image("proposed.svg",width:100%)
#for p in json("page2.json") {text(p);parbreak()}
''')
for p in d.glob('*.svg'):p.write_text('\n'.join(line.rstrip()for line in p.read_text().splitlines())+'\n')
shutil.copyfile(s.parent/'chained-transfer-reference/reports/g3-norm-full-02/compile.py',d/'compile.py');shutil.copyfile(__file__,d/'render.py')
