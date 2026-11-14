"""Render original native observations only;no cryptographic computation."""
from pathlib import Path
import json,lzma,shutil,subprocess
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';d=s/'reports/new-target-IC-01';d.mkdir(exist_ok=True)
records=json.loads(lzma.decompress((s/'evidence/new-target-IC-acceptance-01/all-native-records.json.xz').read_bytes()))
inputs=[x['data']for x in records if x['kind']=='N4_NEW_JACOBIAN_IC_INPUT'];attempts=[x['data']for x in records if x['kind']=='N4_NEW_JACOBIAN_IC_ATTEMPT'];assert len(inputs)==3 and len(attempts)==60
identities=dict(original_source=json.loads((s/'reports/odd-source-01/identities.json').read_text()),actual_targets=inputs,public_requests='fixtures/public-five.json',known_answers_OUTSIDE_runtime='fixtures/expected-OUTSIDE-input.json')
(d/'identities.json').write_text(json.dumps(identities,indent=2)+'\n')
fig,axes=plt.subplots(1,3,figsize=(7.5,2.3),sharey=True)
for ax,row in zip(axes,inputs):
 panel=[x for x in attempts if x['target']==row['target']];assert len(panel)==20
 cells=[[next(x for x in panel if x['public_index']==public and x['nfb']==nfb)['report']['ok']for nfb in [30,36,48,64]]for public in range(5)]
 ax.imshow(cells,cmap=ListedColormap(['#c8ccd1','#3e886e']),vmin=0,vmax=1,aspect='auto')
 for i,line in enumerate(cells):
  for j,value in enumerate(line):ax.text(j,i,'pass'if value else'fail',ha='center',va='center',fontsize=8,color='white'if value else'#263238')
 ax.set(title='Actual J'+str(tuple(row['target'])),xticks=range(4),xticklabels=['30','36','48','64'],yticks=range(5),yticklabels=['Q0','Q1','Q2','Q3','Q4'],xlabel='factor-base points')
axes[0].set_ylabel('unchanged public target');fig.tight_layout();fig.savefig(d/'all60-attempts.svg');plt.close(fig)
dot='''digraph I {graph[rankdir=TB,bgcolor="transparent",nodesep=.15,ranksep=.35];node[shape=box,style="rounded,filled",fillcolor="#edf4fa",fontname="DejaVu Sans",fontsize=8];edge[fontname="DejaVu Sans",fontsize=8];E[label="Original E(K) public G,Q / ell2773073\nK=F223[z]/(z^3-3)\na=(214,144,205),b=(137,218,9)"];O[label="Original plane-quartic IC on ACTUAL target classes\nrelations / large primes / linear algebra / class descent\nreturn k and check[k]H(G)=H(Q)\nindependent ORIGINAL source check",fillcolor="#edf8ed"];
'''
for i,row in enumerate(inputs):
 tag=row['model'];prefix,hexpart=tag.rsplit('-',1)
 label='J'+str(tuple(row['target']))+' / F223 / P0='+str(tuple(row['P0']))+chr(10)+prefix+'-'+chr(10)+hexpart[:32]+chr(10)+hexpart[32:]
 dot+='J'+str(i)+'[label='+json.dumps(label)+'];\n'
 dot+='E->J'+str(i)+'[label="H=PhiPrime gamma double\nactual tagged class output"];J'+str(i)+'->O[label="public H(G),H(Q)"];\n'
dot+='}\n';(d/'actual-IC.dot').write_text(dot);subprocess.run(['dot','-Tsvg',str(d/'actual-IC.dot'),'-o',str(d/'actual-IC.svg')],check=True)
pages=[[
'Prospective98c6f0 was normally published at2aee9ef5 BEFORE code. Nativee869bd passes one unfiltered comprehensive test/all2543 selected hashes unchanged. Every actual HLP(1,0),(1,1),(2,1) Jacobian receives all5 unchanged public targets at all4 fixed factor-base sizes30,36,48,64:ALL60 attempts are retained,including failures. Each of15 public cases has correct IC solves;the native case records show3 successful attempts each. Complete82 JSON records retain all inputs,answers,failures,counters and raw timings.',
'This is actual IC in the new prime-field Jacobians. Runtime receives the actual checked NormNew,tagged public Jacobian G,Q,ell and ordinary IC parameters. It checks field/model/canonical class/odd membership/nonzero generator;it never receives a known scalar,looks up the DLP,recovers to a source elliptic DLP,or calls an elliptic solver. Every reported answer is checked in the target group AND by the original independent source curve engine;known answers stay outside runtime.',
'The additive derivative preserves the original relation collection,large-prime graph,matrix assembly,Lanczos/SGE,holdouts,log recovery and inner split3/random-add descent. Only target context,actualP0/fb0 anchoring,class inputs R=rG,R+G,R+Q and final target verification change;the unused source-rho function is omitted. A byte-exact original solver snapshot and complete literal derivative diff are retained. No original engine or private Inst is mutated.'
],[
'The actual P0 must occupy fb[0] because the original matrix omits that column and sets its log to zero. The new solver deterministically swaps the actual P0 into place,or replaces the first sampled point if absent,while retaining the same based Picard model used by H. It does not reinterpret class keys under a newly chosen origin. Zero generator,nonodd generator/target,foreign field/source/target tags,noncanonical and malformed class packets and actual cross-model inputs reject.',
'Conditional IC algebra:if relation-vector values extend a genuine additive scalar-linear L to Fell,and Q=kG,then the same offset c in y0=L(R)-c,y1=L(R+G)-c,y2=L(R+Q)-c cancels. The differences are L(G) and kL(G),so a genuine denominator inverse recovers k. The original eta subtraction is retained. A zero denominator is a recorded failure. The extension of a sampled relation kernel to a genuine global L and general solver completeness remain open;holdouts alone do not prove them.',
'Checked-answer soundness needs less:the actual H is scalar-equivariant and Recover=159985 delta NormPrime has Recover(H(P))=P on the original ell subgroup. Thus[k]H(G)=H(Q) implies H([k]G)=H(Q),then[k]G=Q. Native independent source checks support this interpretation and protect against a bad reported answer;they are not the mathematical premise of a fitted scalar.',
'Two faithful exact Lean bindings01efbf/671d42 pass BOTH unchanged original4.35/4.34.1 gates:2 audited,zero trusted;57 local bindings total. Target reflection has no axioms;the ring log-ratio proof uses only standard propext,Classical.choice,Quot.sound. Actual Picard/scalar/recovery interpretation and relation-vector global-log extension remain written/open. Whole original producer/consumer proof captures636aec/377526 retain every build/audit/input byte.',
'The original source-bound solver chooses random P0 and affine legacy-transfer triples. An exact same-origin/same-input native compatibility bridge remains open;it is not silently replaced by an ECDLP fallback. Original IC/wrapped Picard counters and raw wall values are diagnostics only. FpR has no exposed counters;source/model setup,map setup/evaluation,input admission and independent verification are unpriced unknown. Prepared model reuse is not a cold pipeline cost. No S,ratio,pipeline win or advantage over IC/rho is established.',
'Prior odd-source/odd-product/refinement graphs were checked and remain historically correct. New editable figures add actual target IC and every retained attempt. Full field/curve/P0/model/class identities are in identities.json. Independent source replay/CI and genuine whole-data publication follow. Separately,the authentic original root fixture is restored through43516010720/14081195285 and the same-binary targeted test passes1ea795;the unchanged full root gate and original performance/merge requirements remain separate.'
]]
for i,page in enumerate(pages,1):(d/('page'+str(i)+'.json')).write_text(json.dumps(page,indent=2)+'\n')
(d/'REPORT.md').write_text('# Actual IC on three new prime-field Jacobians\n\n2026-11-13.Unsigned/partial formalization.\n\n'+'\n\n'.join(p+' [pcc:unverified]'for page in pages for p in page)+'\n')
(d/'report.typ').write_text('''#set page(paper:"a4",margin:13mm)
#set text(font:"DejaVu Sans",size:9pt)
#set par(leading:.35em)
#text(size:16pt,weight:"bold")[Actual public IC on three prime-field Jacobians]
#parbreak()
2026-11-13 · N4 q223 / seed1 · unsigned / partial formalization
#parbreak()
#image("actual-IC.svg",width:100%)
#image("all60-attempts.svg",width:100%)
#for p in json("page1.json") {text(p);parbreak()}
#pagebreak()
#text(size:16pt,weight:"bold")[Checked-answer soundness and remaining costs]
#parbreak()
#for p in json("page2.json") {text(p);parbreak()}
''')
for p in d.glob('*.svg'):p.write_text('\n'.join(x.rstrip()for x in p.read_text().splitlines())+'\n')
shutil.copyfile(s/'reports/odd-product-01/compile.py',d/'compile.py');shutil.copyfile(__file__,d/'render.py')
