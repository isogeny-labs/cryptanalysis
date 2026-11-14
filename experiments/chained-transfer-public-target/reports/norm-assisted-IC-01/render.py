"""Render retained native output; scientific arithmetic remains in Rust/Lean."""
from pathlib import Path
import json,lzma,shutil,subprocess
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';d=s/'reports/norm-assisted-IC-01';d.mkdir(exist_ok=True)
rows=json.loads(lzma.decompress((s/'evidence/norm-sampling-native-acceptance-01/all-native-records.json.xz').read_bytes()))
inputs=[x['data']for x in rows if x['kind']=='N4_NORM_SAMPLER_INPUT'];attempts=[x['data']for x in rows if x['kind']=='N4_NORM_SAMPLER_ATTEMPT'];cases=[x['data']for x in rows if x['kind']=='N4_NORM_SAMPLER_CASE'];assert len(inputs)==3 and len(attempts)==60 and len(cases)==15
identity=dict(q=223,field='K=F223[z]/(z^3-3)',ell=2773073,order=11092292,inputs_with_exact_quartics_based_tags_generators_and_prepared_public_sources=inputs,original_public_source_identity=next(x['data']for x in json.loads((s/'evidence/unit-acceptance-01/all-native-records.json').read_text())if x['kind']=='N4_PUBLIC_IDENTITY'),unchanged_public_source_requests=json.loads((s/'fixtures/public-five.json').read_text()),known_answers='OUTSIDE solver runtime;fixtures/expected-OUTSIDE-input.json',prospective='4a6745/b57 published beforecode',native='9bc5e6',written='e7a860')
(d/'identities.json').write_text(json.dumps(identity,indent=2)+'\n')
cells=[];labels=[];matrix=[]
for item in inputs:
 for i in range(5):
  xs=[next(x for x in attempts if x['target']==item['target']and x['public_index']==i and x['nfb']==fb)for fb in [30,36,48,64]]
  assert all(x['original']['ok']==x['candidate']['ok']for x in xs)
  cells.append([int(x['original']['ok'])for x in xs]);labels.append('HLP'+str(tuple(item['target']))+' / Q'+str(i))
  matrix.append(dict(target=item['target'],public_index=i,all_settings=[dict(nfb=x['nfb'],seed=x['seed'],both_ok=x['original']['ok'],failure=x['original']['fail'],tentative_k=x['original']['k_found'])for x in xs]))
(d/'all60-paired-outcomes.json').write_text(json.dumps(matrix,indent=2)+'\n')
fig,ax=plt.subplots(figsize=(7.3,3.5));ax.imshow(cells,cmap=ListedColormap(['#d5c7b8','#367f66']),vmin=0,vmax=1,aspect='auto')
for i,row in enumerate(cells):
 for j,v in enumerate(row):ax.text(j,i,'correct'if v else'fail: eta'if i<5 else'fail: check',ha='center',va='center',fontsize=7,color='white'if v else'#25303c')
ax.set(yticks=range(15),yticklabels=labels,xticks=range(4),xticklabels=['FB30 / seed102','FB36 / seed103','FB48 / seed104','FB64 / seed105'],title='Same outcome in both arms / all60 pairs retained')
ax.tick_params(axis='y',labelsize=7);ax.tick_params(axis='x',labelsize=8)
for y in [4.5,9.5]:ax.axhline(y,color='white',lw=2)
fig.tight_layout();fig.savefig(d/'all60-paired-outcomes.svg');plt.close(fig)
dot='''digraph S {
graph[rankdir=TB,bgcolor="transparent",nodesep=.25,ranksep=.28];
node[shape=box,style="rounded,filled",fillcolor="#edf3f9",fontname="DejaVu Sans",fontsize=9];
edge[fontname="DejaVu Sans",fontsize=8];
G[label="Public tagged G in J(F223)\nnonzero ell-torsion"];
B[label="Original Picard scalar\n[r]G"];
U[label="Prepare u = inv2 Norm(G)\ncheck actual Phi(u) = G"];
E[label="Original Eprime(K) scalar\n[r]u"];
P[label="One completed Phi\nexact same R = [r]G"];
D[label="Unchanged R+G, R+Q\nrelation / LA / descent"];
V[label="Unchanged final Picard check\nAND independent source check",fillcolor="#e4f1e8"];
G->B[label="baseline"];G->U[label="candidate setup"];U->E[label="public r"];E->P;P->D;B->D;D->V;
}
''';(d/'norm-assisted-sampling.dot').write_text(dot);subprocess.run(['dot','-Tsvg',str(d/'norm-assisted-sampling.dot'),'-o',str(d/'norm-assisted-sampling.svg')],check=True)
pages=[['The candidate computes the same random Jacobian class R=[r]G through the existing elliptic source. For an admitted public generator, prepare u=[1386537]NormNew(G), where 2*1386537=ell+1. The completed maps have the existing written scalar-equivariance and PhiNorm=[2] bridges. Preparation also checks actual Phi(u)=G, source and target ell-membership, canonical tags and nonzero G. It uses no source DLP solver, scalar witness or lookup table.', 'Native claim 9bc5e6 follows protocol 4a6745, published at b57b1024 before code. One unfiltered test passes with all 4,082 selected source hashes unchanged. All 225 source-sampler versus original Picard scalar pairs and all 1,125 R,R+G,R+Q triples match exact canonical classes. All three actual new Jacobians and all five unchanged public targets receive every fixed setting. The whole 86-record output retains the scalar lists, source points, class keys, 120 reports and controls.', 'All 60 paired IC attempts agree on outcomes, failure text, tentative scalars, non-wall stats, phase order and non-descent counters. Both arms accept 45 correct solves; all 15 public cases have three common correct settings. Every accepted answer passes the ORIGINAL target Picard check and independent original-source check. All 15 shared FB30 failures remain, including ten tentative scalars rejected by those checks.'], ['Only the context type and one random R expression change in the frozen 39b class solver. Relation collection, large-prime graph, linear algebra, holdouts, RNG, log recovery and inner descent remain literal. The FINAL ORIGINAL Picard[k]G=Q check stays in place and does not call the sampler. The full original snapshot, literal diff and native text assertion retain every changed byte.', 'All three faithful conditional Lean declarations pass BOTH unchanged original 4.35/4.34.1 gates: three named declarations, zero trusted, empty axiom lists. Bindings 789d94/a9a7af/ed533b pass the original statement/declaration verifier locally and remain unsigned. They derive the inverse-two roundtrip from genuine scalar laws, equivariance, PhiNorm=[2] and ell-torsion; exact all-r sampling from an admitted preimage; and rejection of omitted inverse-two from group cancellation. Actual Picard, scalar and geometric interpretations remain explicit bridges.', 'Controls reject scalar>=ell, changing prepared G, zero/nonodd/foreign/noncanonical/malformed inputs, and actual packets from another valid P0 on the same quartic. The wrong-half control evaluates PhiNorm(G)=[2]G and checks that it differs from G. FB30 failures are retained: five HLP(1,0) pairs lack a full relation, and ten HLP(1,1)/(2,1) pairs produce rejected tentative values. All their whole reports remain.', 'For each R, the baseline calls a Picard scalar multiplication. The candidate calls an elliptic scalar multiplication plus one completed Phi. Setup separately includes norm, admission, source inverse-two/order multiplication and checked transfer. The call vector records API boundaries, with nested decode/norm work. Existing IC/pc counters omit FpR and map/setup/admission/verification work; their descent changes establish no stage win or price. Complete isolated-fork arithmetic coverage, cold/online boundaries, a fresh original checkpoint, live budget/capacity, isolation and strongest matched references precede a performance comparison.', 'Full source and target identities are in identities.json; the coefficient lists above use the original mons_of_degree(4) order. Claims 9bc5e6/e7a860 and NORM_ASSISTED_SAMPLING_PROOF_MAP_01.md link the native data and conditional statements. The first binding collector failed on a relative path before claim/verifier execution (a3273c); collector 02 passes the unchanged original tool. Whole proof captures b79da6/31f2f6 and every negative result remain.', 'Sources checked: Howe-Leprévost-Poonen, Large torsion subgroups of split Jacobians, section 4.1, printed pp23-24 (math.mit.edu/~poonen/papers/large.pdf); Tian, Cover attacks for elliptic curves with prime order, sections 1/4 (arxiv.org/pdf/2012.07173); EFD short-Weierstrass/Jacobian-coordinate formulas (hyperelliptic.org/EFD/g1p/). KB status and four queries each exited 127; this supports no absence or novelty inference. Next are strict independent replay and complete arithmetic coverage.']]
for i,page in enumerate(pages,1):(d/f'page{i}.json').write_text(json.dumps(page,indent=2)+'\n')
(d/'REPORT.md').write_text('# Exact-class norm-assisted sampling in three actual Jacobians\n\n2026-11-14 · unsigned / conditional formal scope\n\n'+'\n\n'.join(p+' [pcc:unverified]'for page in pages for p in page)+'\n')
identities=[]
for x in inputs:identities.append('HLP'+str(tuple(x['target']))+'; P0='+str(tuple(x['P0']))+'; quartic='+str(x['quartic'])+'\n'+x['model'])
(d/'target-identities.txt').write_text('\n\n'.join(identities)+'\n')
(d/'report.typ').write_text('''#set page(paper:"a4",margin:13mm)
#set text(font:"DejaVu Sans",size:9pt)
#set par(leading:.32em)
#text(size:16pt,weight:"bold")[Exact-class sampling through the norm inverse]
#parbreak()
2026-11-14 · all three actual HLP targets · unsigned / conditional formal scope
#parbreak()
#image("norm-assisted-sampling.svg",width:100%,height:65mm,fit:"contain")
#image("all60-paired-outcomes.svg",width:100%,height:80mm,fit:"contain")
#for p in json("page1.json") {text(p);parbreak()}
#pagebreak()
#text(size:15pt,weight:"bold")[Literal integration,proof scope and cost boundary]
#parbreak()
#text(size:8pt)[K=F223[z]/(z^3-3); ell=2773073; Both J(F223) and Eprime(K) have order11092292.]
#parbreak()
#text(size:7pt)[Eprime: y²=x³+(196,168,69)x+(8,82,207). Prepared u=(64,152,78 ; 36,12,9) in allthree cases.]
#parbreak()
#text(font:"DejaVu Sans Mono",size:6pt)[#raw(read("target-identities.txt"))]
#parbreak()
#for p in json("page2.json") {text(p);parbreak()}
''')
for p in d.glob('*.svg'):p.write_text('\n'.join(x.rstrip()for x in p.read_text().splitlines())+'\n')
shutil.copyfile(s/'reports/odd-product-01/compile.py',d/'compile.py');shutil.copyfile(__file__,d/'render.py')
