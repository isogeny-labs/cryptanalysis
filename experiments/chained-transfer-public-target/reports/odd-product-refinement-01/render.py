"""Render native observations and written text only; no cryptographic arithmetic."""
from pathlib import Path
import json,lzma,shutil,subprocess
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';d=s/'reports/odd-product-refinement-01';d.mkdir()
records=json.loads(lzma.decompress((s/'evidence/odd-product-refinement-acceptance-01/all-native-records.json.xz').read_bytes()))
gamma=records[0]['data'];types=records[2]['data']['all9'];panels=[x['data']for x in records if x['kind']=='N4_REFINEMENT_SOURCE_API'];assert len(panels)==3
identities=json.loads((s/'reports/odd-product-01/identities.json').read_text());identities['old_J0_quartic']=gamma['original_quartic'];identities['old_J0_P0']=gamma['original_P0'];identities['all9_kernel_types']=types
(d/'identities.json').write_text(json.dumps(identities,indent=2)+'\n')
fig,axes=plt.subplots(1,2,figsize=(7.5,2.25));eligible=[x for x in types if x['eligible_actual_Jacobian']];names=[x['target'].replace('HLP-','').replace('-',',')for x in eligible];x=list(range(3));ax=axes[0]
ax.bar([i-.17 for i in x],[x['C4_factors']for x in eligible],width=.34,label='C4 factors',color='#357a91');ax.bar([i+.17 for i in x],[x['C2_factors']for x in eligible],width=.34,label='C2 factors',color='#be7b45');ax.set(title='Eligible geometric 2-primary kernels',xticks=x,xticklabels=names,yticks=range(7),ylabel='cyclic factors');ax.legend(fontsize=7)
ax=axes[1];hist=records[1]['data']['histogram'];bars=ax.bar(list(hist),list(hist.values()),color='#427c69');ax.set(title='ALL 135 transported intersections',xlabel='dimension d (Gaussian rank/cardinality)',ylabel='Lagrangians',ylim=(0,75))
for b,value in zip(bars,hist.values()):ax.text(b.get_x()+b.get_width()/2,value+1,str(value),ha='center',fontsize=8)
fig.tight_layout();fig.savefig(d/'kernels.svg');plt.close(fig)
beta=r'''digraph B {graph[rankdir=LR,bgcolor="transparent",ranksep=.55,nodesep=.4];node[shape=box,style="rounded,filled",fillcolor="#edf4fa",fontname="DejaVu Sans",fontsize=9];edge[fontname="DejaVu Sans",fontsize=9];J[label="J0 / F223 / original P0=(1,0,0)\nf=[0,1,91,68,209,30,216,142,\n31,72,184,179,36,124,140]"];L[label="J'(1,0) / F223 / P0=(1,0,84)\nCiani-Jac-odd-product-v1-\n7ea9d0f9d1a48a48489425beab48274f\nca7bd0848e47a0bac3a027c01601e2c4",fillcolor="#eef8eb"];A[label="A=Res(E) / F223\nE/K:a=(214,144,205),b=(137,218,9)\nK=F223[z]/(z^3-3)"];B[label="Aprime=Res(Eprime) / F223\nN4-E13-short-\n936b863521fdce08d2724c468f27979cb3\n9d9443d082b4be14209bb08f408414"];{rank=same;A;J};{rank=same;B;L};A->J[label="Phi0 / degree8"];A->B[label="u=Res(gamma) / degree13^3"];B->L[label="PhiPrime / degree8"];J->L[label="beta / degree13^3 / polarization13\nGLOBAL WRITTEN FACTOR\ncomplete coordinates remain open",style=dashed,color="#30724b"];J->L[label="F=[2]beta / degree52^3\ncomplete F coordinates implemented",color="#357a91",style=bold];}'''
(d/'matched-factor.dot').write_text(beta+'\n');subprocess.run(['dot','-Tsvg',str(d/'matched-factor.dot'),'-o',str(d/'matched-factor.svg')],check=True)
api=r'''digraph S {graph[rankdir=LR,bgcolor="transparent",ranksep=.28,nodesep=.2];node[shape=box,style="rounded,filled",fillcolor="#edf4fa",fontname="DejaVu Sans",fontsize=10];edge[fontname="DejaVu Sans",fontsize=9];P[label="Original admitted odd P\ncoordinates + field/model tags"];R[label="old Phi -> old Norm\nthen gamma -> new Phi"];C[label="original elliptic double\nthen gamma -> new Phi",fillcolor="#eef8eb"];H[label="EXACT SAME H(P)\ncomplete class + tags\nall3 targets / public5"];P->R[label="frozen Chain"];P->C[label="FastSourceChain"];R->H;C->H;H->P[label="unchanged159985 delta NormPrime\nsubgroup + forward-roundtrip checks",constraint=false];}'''
(d/'source-api.dot').write_text(api+'\n');subprocess.run(['dot','-Tsvg',str(d/'source-api.dot'),'-o',str(d/'source-api.svg')],check=True)
pages=[[
'Prospective579e08/c37ad390 was normally published BEFORE refinement code. Native147b66 uses the frozen45ee45d2 maps and original engines. One unfiltered comprehensive test passes/all2514 selected hashes unchanged. Actual gamma2 has permutation[0,3,2,1]. All3 coefficient-conjugate Kohel maps,64 coordinate-vector images,4096 linearity/pairing checks and Frobenius commutation pass; the entire135 original Smith census equals the fresh model census.',
'Transported Gold is2341872925073736705,not the literal original9232380353346274305. Every transported intersection is retained with actual coordinates and independent Gaussian rank. The histogram d=0,1,2,3 is64,56,14,1. All9 rational cases remain:3 product and6 HLP. Eligible(1,0),(1,1),(2,1) have d=3,2,1. The wrong untransported calculation gives2,3,0 and falsely labels the last target free.',
'Written03/f46ce2:etale kerF has order52^3 and exponent52. Restricting N0 to J0[2] has image Gold and kernel order8,so #kerF[2]=8*2^d. Finite abelian classification gives C4^(3-d) x C2^(2d) x C13^3. None of the three implemented Jacobian targets has free C52^3 kernel. All3 nonsquare HLP cases and product-Q3 have d=0 but are not implemented specified-source F223 Jacobian maps. This is a bounded panel result,not an obstruction to other products,degrees,twists or chains.',
'Matched target(1,0) has Gprime=u(Gold). Genuine quotient universality supplies beta Phi0=PhiPrime u,degree13^3=2197 and polarization13 over F223. Its dual has both[13],and F=2beta,G=2betaDual. This is a written global odd-degree DLP-preserving factor;complete beta coordinate evaluation on arbitrary rational Jacobian classes remains open. Odd-subgroup halving of F alone would not implement that complete map.'
],[
'The global old dual pair gives N0 Phi0=[2]. Therefore H(P)=F(Phi0(P))=PhiPrime gamma([2]P) for every original source point. FastSourceChain implements this identity with original elliptic doubling,gamma,and the complete new pullback. Its state holds no old Phi/Norm instance. It preserves the old class outputs,tags,canonical coordinates,field/source/target/order checks,odd-subgroup admission and forward roundtrip recovery. The undoubled PhiPrime gamma control differs and doubles to H.',
'Native147b66 compares33 inputs(32 fixed odd scalars plus zero) and all5 unchanged literal public targets for EACH of the3 endpoints:complete class equality,tagged packet equality,source recovery,nonzero exactell2773073 and independent original known-answer checks. Runtime takes coordinates/tags,never scalar witnesses or a DLP table. It rejects noncanonical/offcurve points,all3 nonzero source2-torsion points,all3 nonzero target rational-cofactor classes,foreign field/model packets and an actual mismatched target.',
'Three faithful exact Lean bindings a08ad5/cc8b69/f8b42f pass BOTH unchanged original4.35/4.34.1 gates:3 audited,zero trusted,no axioms;55 local bindings total. They derive killed52 projectors13/40 and trivial4/13 intersection;derive beta existence/F=beta double from general quotient universality and actual kernel containment;and prove exact source-pair elimination from the genuine old dual pair. No beta factorization or source-output conclusion is assumed. Actual etale/group-classification/quotient-category/degree/polarization/Picard/scalar interpretation remains written.',
'Primary review reads Milne CourseNotes2008Remark8.12,printedp39,for kernel-containment factorization,and xnotes AVs Section8/Theorem11.1/Proposition16.8/Remark16.9 for degree/etale/duality/polarization. Version01 erroneous Mumford title and version02 page38 locator remain immutable;active03 corrects only references. All mathematics,code,Lean signatures and verdicts remain unchanged. Two whole original proof captures are retained as standard tarXZ archives with every member hash roundtrip.',
'This is a structural forward-algorithm change:remove old Phi and old Norm,add one elliptic doubling. No operation-count ratio,timing gain,pipeline improvement or advantage over IC/rho is claimed. Original S3 checkpoint/livebudget/capacity admission,complete cold+online transport/solver/verification counters and strongest matched references remain required. Strict independent replay/CI and genuine whole-data publication follow;then actual new-target solver coverage and complete odd-degree coordinate options.',
'Previous odd-source/odd-product/chain-kernel graphs were checked and remain historically correct. New editable graphs add the written matched odd-degree factor and same-output API;the kernel plot derives directly from retained native JSON. Full equations,P0s,field and model identifiers for all3 targets are in identities.json. Reports/claims are unsigned;actual geometry is partially formalized and signed execution remains open.'
]]
for i,page in enumerate(pages,1):(d/('page'+str(i)+'.json')).write_text(json.dumps(page,indent=2)+'\n')
(d/'REPORT.md').write_text('# Transported kernels and identical-output source maps\n\n2026-11-13.Unsigned;partial formal geometry.\n\n'+'\n\n'.join(p+' [pcc:unverified]'for page in pages for p in page)+'\n')
(d/'report.typ').write_text('''#set page(paper:"a4",margin:13mm)
#set text(font:"DejaVu Sans",size:9pt)
#set par(leading:.35em)
#text(size:16pt,weight:"bold")[Transported kernels and a written odd-degree factor]
#parbreak()
2026-11-13 · N4 q223 / seed1 · unsigned / partial formalization
#parbreak()
#image("matched-factor.svg",width:100%)
#image("kernels.svg",width:100%)
#for p in json("page1.json") {text(p);parbreak()}
#pagebreak()
#text(size:16pt,weight:"bold")[Identical source images with fewer map calls]
#parbreak()
#image("source-api.svg",width:100%)
#for p in json("page2.json") {text(p);parbreak()}
''')
for p in d.glob('*.svg'):p.write_text('\n'.join(x.rstrip()for x in p.read_text().splitlines())+'\n')
shutil.copyfile(s/'reports/odd-product-01/compile.py',d/'compile.py');shutil.copyfile(__file__,d/'render.py')
