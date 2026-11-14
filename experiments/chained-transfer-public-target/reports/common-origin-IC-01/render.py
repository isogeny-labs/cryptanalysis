"""Render retained native records only;all arithmetic/tests remain in Rust."""
from pathlib import Path
import json,lzma,shutil,subprocess
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';d=s/'reports/common-origin-IC-01';d.mkdir(exist_ok=True)
records=json.loads(lzma.decompress((s/'evidence/common-origin-acceptance-01/all-native-records.json.xz').read_bytes()))
settings=[x['data']for x in records if x['kind']=='N4_ORIGIN_SETTING'];attempts=[x['data']for x in records if x['kind']=='N4_ORIGIN_ATTEMPT'];geometry=[x['data']for x in records if x['kind']=='N4_ORIGIN_GEOMETRY'];assert len(settings)==4 and len(attempts)==len(geometry)==20
(d/'identities.json').write_text(json.dumps(dict(q=223,source_field='F223[z]/(z^3-3)',ell=2773073,order=11092292,settings_with_full_quartic_P0_tags_and_classes=settings,public_source_requests=json.loads((s/'fixtures/public-five.json').read_text()),source_pin='1816c3b99cb69e2072a7f0a246bdeb98b9f005e8',prospective='2dd807/0a3412cd before code',known_answers='OUTSIDE runtime:fixtures/expected-OUTSIDE-input.json'),indent=2)+'\n')
identity_path=d/'identities.json';identity=json.loads(identity_path.read_text());old=json.loads((s/'evidence/unit-acceptance-01/all-native-records.json').read_text());identity['original_public_source_identity']=next(x['data']for x in old if x['kind']=='N4_PUBLIC_IDENTITY');identity['original_public_source_identity_evidence']='evidence/unit-acceptance-01/all-native-records.json:N4_PUBLIC_IDENTITY';identity_path.write_text(json.dumps(identity,indent=2)+'\n')
fig,axes=plt.subplots(1,2,figsize=(7.3,2.1),sharey=True)
for ax,arm,title in zip(axes,['original','candidate'],['Original source-bound IC','Class input / same actual P0']):
    cells=[[next(x for x in attempts if x['public_index']==i and x['setting']==j)[arm]['ok']for j in range(4)]for i in range(5)]
    ax.imshow(cells,cmap=ListedColormap(['#cbd0d5','#367f66']),vmin=0,vmax=1,aspect='auto')
    for i,row in enumerate(cells):
        for j,v in enumerate(row):ax.text(j,i,'pass'if v else'fail',ha='center',va='center',fontsize=8,color='white'if v else'#25303c')
    ax.set(title=title,xticks=range(4),xticklabels=['30','36','48','64'],yticks=range(5),yticklabels=['Q0','Q1','Q2','Q3','Q4'],xlabel='factor-base points / all settings retained')
axes[0].set_ylabel('unchanged public target');fig.tight_layout();fig.savefig(d/'all20-pairs.svg');plt.close(fig)
fig,axes=plt.subplots(1,2,figsize=(7.3,1.7))
for ax,key,title in zip(axes,['available_legacy_points','available_legacy_triples'],['Original raw points / 495 per origin','Complete raw triples / 165 per origin']):
    values=[sum(x[key]for x in geometry if x['setting']==j)for j in range(4)]
    ax.bar(range(4),values,color='#476e99',width=.6)
    for i,v in enumerate(values):ax.text(i,v+max(values)*.025,str(v),ha='center',va='bottom',fontsize=8)
    ax.set(title=title,xticks=range(4),xticklabels=['P0 / 30','P0 / 36','P0 / 48','P0 / 64'],ylim=(0,max(values)*1.2));ax.spines[['top','right']].set_visible(False)
fig.tight_layout();fig.savefig(d/'retained-legacy-availability.svg');plt.close(fig)
dot='digraph C {graph[rankdir=TB,bgcolor="transparent",nodesep=.2,ranksep=.28];node[shape=box,style="rounded,filled",fillcolor="#edf3f9",fontname="DejaVu Sans",fontsize=9];edge[fontname="DejaVu Sans",fontsize=8];\n'
nodes={'E':'Original E(K) / public G,Q\nK=F223[z]/(z^3-3), ell=2773073','P':'Same actual P0 and entire factor base\n(1,74,153), (1,59,13), (1,66,1), (1,92,137)','A':'Original source-bound solver\nraw affine A(P)=H(P)+T','H':'Genuine completed H(P)=PhiNew(SP)\nS=-I; actual T from old infinity fibre','B':'Class-input IC in that SAME based Jacobian\npublic H(G),H(Q); no source DLP fallback','V':'Returned k checked in actual target\nAND independent original source'}
for name,label in nodes.items():dot+=name+'[label='+json.dumps(label)+'];\n'
for a,b,label in [('E','A','original transfer'),('E','H','completed map'),('H','B','public canonical classes'),('P','A','same P0 / fb0'),('P','B','same P0 / fb0'),('A','V','retain every outcome'),('B','V','retain every outcome')]:dot+=a+'->'+b+'[label='+json.dumps(label)+'];\n'
dot+='}\n';(d/'same-origin-control.dot').write_text(dot);subprocess.run(['dot','-Tsvg',str(d/'same-origin-control.dot'),'-o',str(d/'same-origin-control.svg')],check=True)
pages=[[
'Prospective2dd807 was normally published at0a3412cd before code. Native8a77f3 passes one unfiltered test with all3,304 selected input hashes unchanged. The control compares the unchanged original source-bound solver with a separate borrowed-Picard class-input derivative on the original q223/seed1 problem. Allfive literal public targets receive allfour settings:FB30,36,48,64 with explicit seeds102,103,104,105. All20 pairs,40 whole reports and51 complete native JSON records remain.',
'Both arms have15 correct solves and agree on all20 success/failure outcomes. Each public Q has three common correct settings. For FB30/seed102,both arms fail on20 relation rows for30 columns in allfive cases;those failures remain. Every reported success is checked in the actual target group and by the independent original source engine. Known scalars stay outside both runtime interfaces. No source ECDLP solver,scalar witness or DLP table supplies the class-input answer.',
'For each setting,the original and copied point samplers produce identical complete factor-base vectors and RNG states. The first P0 accepted by the original Picard constructor determines a fresh actual NormV2;the candidate uses exactly that P0,all15 original quartic coefficients and the same swap. Its anchor is already in the sampled base,so no point is replaced. An actual different valid P0 rejects as a foreign model;zero generator packets also reject.'
],[
'The original raw transfer is affine. With the genuine source sign S=-I,the completed homomorphic map is H(P)=PhiNew(SP). At the SAME actual Picard origin,T is the canonical reduction of the old negative-infinity fibre. Whenever the original transfer exists,A(P)=H(P)+T. The native panel checks all660 source triples rG,rG+G,rG+Q for r=0..32 and allfour origins,with1,980 completed images. All1,004 available original raw points satisfy this exact identity;allfour actual T are nonzero,and omitting T fails on every one of those1,004 points.',
'The completed differences are H(rG+G)-H(rG)=H(G) and H(rG+Q)-H(rG)=H(Q). The same differences hold for A because T cancels. All92 triples with three available original transfers pass the full raw-class and difference comparisons. Every unavailable transfer and availability count is retained. Equal availability counts across origins are retained observations;the test does not force rejection sampling or claim that random descent paths agree.',
'The derivative changes ONLY the context type and access to a borrowed actual PlaneQuartic. Byte-exact original snapshots,complete literal diff and Rust comparisons preserve the relation/large-prime/matrix/Lanczos/SGE/holdout/log-recovery and inner-descent bodies. The original frozen NormNew context and all729 earlier replay inputs remain unchanged. This supplies the previously open finite same-origin/factor-base/DLP-data compatibility control.',
'Existing faithful bindings01efbf/671d42 are reused,so the accumulated total remains57 local bindings,not59. Given a genuine equivariant H and left inverse,an actually checked target answer reflects to the source. For this old target,Recover=S^-1[1386537]Norm on the ell subgroup. Given a genuine additive scalar log and denominator inverse,a common affine offset cancels in the recovered ratio. The original two proof toolchains already checked those same declarations;actual geometry and relation-vector extension to a global log remain written/native or open. Holdouts do not prove general completeness.',
'This is a bounded representation and answer control. It does not establish equal random paths,counters or costs. Original phase counters and raw walls remain diagnostic;FpR,source/model setup,maps,input admission and independent verification need complete operation coverage. Prepared models are not a cold run. The original checkpoint transport now passes for clean39e9(ffe675);later changes require a fresh original checkpoint before an experiment. Live budget,capacity,isolation and strongest matched references remain separate.',
'Full identities and native data links are in identities.json and evidence/common-origin-acceptance-01. The existing new-target and refinement diagrams were checked and remain historical sources;this editable graph adds the exact compatibility control. Next are strict independent replay/CI,genuine whole-capture publication with a fresh guard08,and complete operation coverage. No S,ratio or computational advantage is claimed.'
]]
for i,page in enumerate(pages,1):(d/f'page{i}.json').write_text(json.dumps(page,indent=2)+'\n')
(d/'REPORT.md').write_text('# Native common-origin control for class-input IC\n\n2026-11-14. Unsigned;conditional formal scope.\n\n'+'\n\n'.join(p+' [pcc:unverified]'for page in pages for p in page)+'\n')
(d/'report.typ').write_text('''#set page(paper:"a4",margin:13mm)
#set text(font:"DejaVu Sans",size:9pt)
#set par(leading:.35em)
#text(size:16pt,weight:"bold")[Class-input IC at the original sampled origins]
#parbreak()
2026-11-14 · q223 / seed1 · unsigned / conditional formal scope
#parbreak()
#image("same-origin-control.svg",width:100%,height:70mm,fit:"contain")
#image("all20-pairs.svg",width:100%)
#for p in json("page1.json") {text(p);parbreak()}
#pagebreak()
#text(size:16pt,weight:"bold")[Actual affine correction and remaining costs]
#parbreak()
#image("retained-legacy-availability.svg",width:100%)
#for p in json("page2.json") {text(p);parbreak()}
''')
for p in d.glob('*.svg'):p.write_text('\n'.join(x.rstrip()for x in p.read_text().splitlines())+'\n')
shutil.copyfile(s/'reports/odd-product-01/compile.py',d/'compile.py');shutil.copyfile(__file__,d/'render.py')
