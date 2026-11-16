"""Native JSON visualization and report rendering only, no crypto arithmetic."""
from pathlib import Path
import json,shutil,subprocess
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';d=s/'reports/completed-descent-01';d.mkdir()
records=json.loads((s/'evidence/completed-descent-acceptance-01/all-native-records.json').read_text());attempts=[x['data']for x in records if x['kind']=='N4_COMPLETED_ATTEMPT'];assert len(attempts)==10
(d/'all-native-records.json').write_text(json.dumps(records,indent=2)+'\n')
fig,ax=plt.subplots(figsize=(7.3,2.45))
for row in attempts:
 for offset,key in [(0,'baseline'),(5,'candidate')]:
  ok=row[key]['ok'];ax.scatter(row['attempt'],offset+row['target_index']+1,s=70,marker='o'if ok else'x',color='#18794e'if ok else'#b8403d',linewidths=1.7)
ax.set(xticks=[1,2],xticklabels=['Attempt1 / FB30','Attempt2 / FB36'],yticks=range(1,11),yticklabels=['Baseline Q'+str(i)for i in range(1,6)]+['Complete Q'+str(i)for i in range(1,6)],xlim=(.6,2.4),ylim=(10.6,.4),title='All20 method-attempt outcomes; no cost comparison')
ax.axhline(5.5,color='#555',linewidth=.7);fig.tight_layout();fig.savefig(d/'attempts.svg');plt.close(fig)
dot='''digraph Complete {
graph [rankdir=LR,bgcolor="transparent",nodesep=.2,ranksep=.25];
node [shape=box,style="rounded,filled",fillcolor="#edf5fb",fontname="DejaVu Sans",fontsize=10];
edge [fontname="DejaVu Sans",fontsize=9];
Q [label="Strict public Q\noriginal instance / no witness"];
R [label="Original relation collection\noriginal linear algebra"];
M [label="Changed admission only\n3 complete Gen spaces\nactual P0 / geometric origin",fillcolor="#fff3da"];
D [label="Original class descent\nthree-point differences\noriginal scalar recovery"];
V [label="Original independent\nsource answer check"];
Q -> R;R -> M;M -> D;D -> V;
}'''
(d/'flow.dot').write_text(dot+'\n');subprocess.run(['dot','-Tsvg',str(d/'flow.dot'),'-o',str(d/'flow.svg')],check=True)
p1=[
'Observed unsigned5ff070: one unfiltered serial Rust test passes, zero failed/ignored/filtered, all2307 input hashes unchanged. All five candidate public-target solves and the original baseline succeed under the same frozen six-attempt cap. The10 paired attempts preserve5 initial26-row/30-column failures in each method, followed by5 FB36 successes in each. Every reported scalar passes the original independent source engine.',
'Prospective boundary: active protocol74e00a was actually normally published in ready PR1523 at093134ba BEFORE candidate implementation (7823d2). This is the same q223/seed1 source, K=F223[z]/(z³−3),ell2773073/order11092292. Known witnesses remain outside public requests and both public solvers. The original N4 algorithm is the named baseline; moving target construction is not a speedup.'
]
p2=[
'Implementation: the complete solver derivative differs by only6 literal substitutions: bind the certified CheckedInstance; construct the actual completed adapter at the actual selected P0; replace split-cubics triple admission with completed Gen spaces; record3 maps; and reduce each actual Gen. Relation collection, matrix/linear-algebra work, class descent walk, logarithm assignment, final recovery and original rho bytes remain. Whole original source/diff and exact substitutions are retained.',
'Geometry: the helper obtains T from the actual negative-infinity branch and computes T−I(P) through the original source group, where I(v,w)=(v+a2/3,w). This is kappa(lambda⁻¹P), so the completed divisor space extends the old raw map. It keeps the affine geometric origin: the original three-target differences cancel that same origin. There is no fitted scalar shift, inverse/DLP table, old split-map fallback or generic-DLP fallback.',
'Native compatibility controls: rebuild actual winning P0=[1,74,153], require its nonzero origin, evaluate32 complete points and match all16 legacy admitted split classes. All five public point half-inverses and affine difference identities pass with a nonzero ratio base. Candidate successes report exactly3 complete maps. The previous actual V2 control panels and written divisor/Ciani argument remain in V2_MAPS_01.md; the17 conditional/integer Lean bindings do not formalize the N4 relation kernel or all actual Picard geometry.',
'Independent parent checks are settled: published093 passes full0815f7 with469guards and17 phase pairs;both scientific CI workflows succeed at that exact head. Auditb6c1db matches all25 native records and17 original canonical claim digests. The first collector regex omitted the digit2 in V2 names;whole partial01 and frozen7176d7 correction are retained before complete02. This is a bookkeeping correction,not a missing native record or changed test.',
'Limits and next task: this new candidate result is a bounded known-answer correctness smoke,not an independent candidate full/CI replay or performance comparison. The dependency cache is reused and non-cold. Original counters omit arithmetic in the separate completed-map engine;all raw timings/counters remain but no totalS,ratio or computational advantage is inferred. Next commit/source publication,then clean independent candidate replay and ownCI. Actual S3 checkpoint/livebudget/capacity and strongest applicable references are required for performance experiments.'
]
(d/'page1.json').write_text(json.dumps(p1,indent=2)+'\n');(d/'page2.json').write_text(json.dumps(p2,indent=2)+'\n')
(d/'REPORT.md').write_text('# Completed-transfer individual descent: fixed correctness result\n\n2026-11-13. All standing unsigned.\n\n'+'\n\n'.join(p+' [pcc:unverified]'for p in p1+p2)+'\n\nSources: completed-descent/README.md and derived/source-pins.json; evidence/completed-descent-acceptance-01; prospective74e00a/boundary7823d2; original public solver; V2_MAPS_01.md; parent full0815f7/CIb6c1db. Editable diagram,plot,complete native records and report source are adjacent. The positive q223 model graph remains current;this diagram changes the individual-descent admission stage only,not the graph of isogeny endpoints.\n')
(d/'report.typ').write_text('''#set page(paper:"a4",margin:14mm)
#set text(font:"DejaVu Sans",size:9.2pt)
#set par(leading:.45em)
#text(size:18pt,weight:"bold")[Completed-transfer individual descent]
#parbreak()
2026-11-13 · five known-answer public targets · all standing unsigned
#parbreak()
#image("flow.svg",width:100%)
#image("attempts.svg",width:98%)
#for p in json("page1.json") {text(p);parbreak()}
#pagebreak()
#text(size:18pt,weight:"bold")[Exact change, controls and remaining costs]
#parbreak()
#for p in json("page2.json") {text(p);parbreak()}
#text(size:9pt,weight:"bold")[Evidence]
#parbreak()
5ff070/native01;74e00a/activeprotocol02;093134ba/actualnormalpublication;7823d2/precodeboundary;completed-descent/derived/source-pins.json/full literal diff;parent0815f7/b6c1db. Native raw timings are correctness diagnostics,not an admitted cost comparison.
''')
for p in d.glob('*.svg'):p.write_text('\n'.join(line.rstrip()for line in p.read_text().splitlines())+'\n')
shutil.copyfile(s.parent/'chained-transfer-reference/reports/g3-norm-full-02/compile.py',d/'compile.py');shutil.copyfile(__file__,d/'render.py')
