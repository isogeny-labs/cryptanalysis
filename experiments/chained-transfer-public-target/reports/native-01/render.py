"""Render original native observations; no cryptographic computation."""
from pathlib import Path
import json,subprocess,shutil
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';d=s/'reports/native-01';d.mkdir(exist_ok=True)
records=json.loads((s/'evidence/unit-acceptance-01/all-native-records.json').read_text());identity=json.loads((s/'evidence/unit-acceptance-01/instance.json').read_text())
attempts=[x['data'] for x in records if x['kind']=='N4_PUBLIC_ATTEMPT']
(d/'identity.json').write_text(json.dumps(identity,indent=2)+'\n');(d/'attempts.json').write_text(json.dumps(attempts,indent=2)+'\n')
fig,ax=plt.subplots(figsize=(7.4,2.15))
for row in attempts:
    success=row['public']['ok'];ax.scatter(row['attempt'],row['target_index']+1,s=130,marker='o' if success else 'x',color='#18794e' if success else '#ba3b39',linewidths=2)
ax.set(xticks=[1,2],xticklabels=['Attempt1: FB30','Attempt2: FB36'],yticks=[1,2,3,4,5],ylabel='Public target index',xlim=(.6,2.4),ylim=(5.5,.5),title='Actual retained IC attempts: five known-answer fixtures')
ax.grid(axis='x',alpha=.2);fig.tight_layout();fig.savefig(d/'attempts.svg');plt.close(fig)
dot='''digraph Native {
graph [rankdir=LR,bgcolor="transparent",nodesep=.2,ranksep=.25];
node [shape=box,style="rounded,filled",fillcolor="#edf5fb",fontname="DejaVu Sans",fontsize=10];
edge [fontname="DejaVu Sans",fontsize=9];
S [label="E / F223 cubed\na2=(127,56,199)\na4=(152,35,36)\na6=(212,109,150)\nmodulus z cubed - 3"];
Q [label="Strict public Q\nno witness field\nexact model tags"];
I [label="Original N4/B2\nrelation / LA / descent\nall retries retained"];
V [label="Original independent\nFpR + source curve\nk_found G = Q"];
S -> Q; Q -> I; I -> V;
}'''
(d/'flow.dot').write_text(dot+'\n');subprocess.run(['dot','-Tsvg',str(d/'flow.dot'),'-o',str(d/'flow.svg')],check=True)
page1=[
'Observed, unsigned e08eac: three unfiltered native tests pass, zero failed/ignored/filtered, all2188 source guards unchanged. All five public IC targets solve through the literal original-body derivative; all five answers pass the original independent FpR/curve check. Ten paired legacy/public attempts agree on success/failure/recovered scalar. The five first attempts fail with26rows/30columns; the five second attempts with FB36 succeed. The chart records that complete attempt history, not a performance comparison.',
'Full source identity (identity.json is adjacent): q223, seed1, extension degree3, modulus [220,0,0,1]. G=((162,197,140),(45,11,207)); ell2773073, cofactor4, #E(Fq³)=11092292. Original independent irreducibility/primality/curve/nonzeroG/ellG checks and the unique Hasse multiple4 certify this source order. Hasse interval [11082908,11096228], radius6660. Native j=(166,136,127), outside Fq; this is the existing restricted GHS family, not a generic prime-field curve result.',
'Field tag: '+identity['field'],
'Model tag: '+identity['model']
]
page2=[
'Actual executable interface, 9e522f: describe and solve processes return0 for the same five literal public targets; the entire description JSON matches the unit fixture. All14 invalid-input processes return2: foreignq/schema/field/model, noncanonical coordinate, off-curve point, actual nonmember, unknown scalar, unknown witness, empty/six targets, oversize, overwrite and extra argument. Rejected outputs are absent and the original overwrite bytes remain unchanged. Actual output retains all ten IC attempts. Known-answer witnesses stay outside public requests.',
'Reuse and scope: four whole original N4 files are byte exact. The public solver derivative has only four literal plumbing substitutions: two scalar arguments become Q, and two target-construction lines are removed. Original relation/LA/descent/random/verification bodies remain. Legacy scalar-taking solver entry points are test-only. Static compiler/own-source format checks pass with all2187 guards unchanged; original compiler warnings, including the unused test-helper parameter, are retained. No strict-Clippy or warning-free claim is made.',
'Partial formal result, f68241: the same nine basepoint/affine-log/model declarations pass both ORIGINAL producerLean4.35 and consumerLean4.34.1 gates, zero trusted declarations. All nine exact original PCC bindings locally pass, unsigned. Lean01 fails the final quartic proof body; wholefef40b is retained. Frozene58e94 precedes only the explicit proof-body rewrite after the Rust terminal guards. No theorem statement, verifier or trust manifest was weakened.',
'Written bridge and remaining work: a final divisor key shifts by delta when P0 changes, while the same raw degree-six input shifts by2delta. The common quartic ordinate reflection gives the proposed source orientation S=-I for the completed map; actual V2 field/model/P0/origin/fibre/norm checks remain open. The nine abstract/ring lemmas do not construct those objects or prove N4 relation-kernel correctness. The public rho derivative exists, but its old return type does not expose its recovered scalar; independent rho-answer replay remains a separate accessor task.',
'Custody and decision: complete static/unit/CLI trees are ONE standard tar/XZ each, sizes9005108/9008132/9010244 bytes (f426af/4db2f4/069a13), with every-member/raw/archive hashes and exact round trips. Genuine remote publication is a separate receipt. Continue to independent source CI, the rho accessor and additive V2 bridges. Parent norm/CI/raw results remain settled. Preserve the withdrawn subgroup-enumeration history, all compiler/launcher/proof and relation failures.',
'Limits: this is one fixed constructor and five known-answer correctness fixtures. No benchmark, timing ratio, computational advantage, complete Jacobian enumeration or full formal geometry is established. Original outside build cache is reused for the CLI and explicitly not a cold comparison. Future experiments require the original S3 checkpoint/live budget/capacity admission and strongest applicable references with all material cold costs.'
]
(d/'page1.json').write_text(json.dumps(page1,indent=2)+'\n');(d/'page2.json').write_text(json.dumps(page2,indent=2)+'\n')
(d/'REPORT.md').write_text('# Public-target N4: native and executable correctness\n\n2026-11-13. All standing unsigned.\n\n'+'\n\n'.join(p+' [pcc:unverified]' for p in page1+page2)+'\n\nSources: unit-acceptance-01/all-native-records.json and instance.json; cli-acceptance-01/summary.json; formal-scope-01; lean-bindings-01; literal-original.diff and original/source-pins.json. Full written derivation and proof map are at ../../DERIVATION.md and ../../PROOF_MAP.md. Editable plot/flow source and exact identity/attempt JSON are adjacent. Parent canonical transfer graphs checked; no new completed V2 map edge is admitted.\n')
(d/'report.typ').write_text('''#set page(paper:"a4",margin:14mm)
#set text(font:"DejaVu Sans",size:9.3pt)
#set par(leading:.45em)
#text(size:18pt,weight:"bold")[Public-target N4: native correctness]
#parbreak()
2026-11-13 · one fixed case / five known-answer targets · all standing unsigned
#parbreak()
#image("flow.svg",width:100%)
#image("attempts.svg",width:95%)
#for p in json("page1.json") {text(p);parbreak()}
#pagebreak()
#text(size:18pt,weight:"bold")[Executable, proofs and exact limits]
#parbreak()
#for p in json("page2.json") {text(p);parbreak()}
#text(size:10pt,weight:"bold")[Source-linked evidence]
#parbreak()
e08eac/unit-acceptance-01;9e522f/cli-acceptance-01;f68241/DERIVATION.md/PROOF_MAP.md/formal-scope-01;lean-bindings-01/claims.json;wholef426af/4db2f4/069a13;failedLean01fef40b/correctione58e94. Full native identity and editable figures accompany this report. Parent transfer graph remains unchanged; V2 edges are pending.
''')
shutil.copyfile(r/'experiments/chained-transfer-reference/reports/g3-norm-full-02/compile.py',d/'compile.py');shutil.copyfile(__file__,d/'render.py')

# Normalize only textual SVG trailing whitespace; plotting/data are unchanged.
for p in d.glob("*.svg"):
    p.write_text("\n".join(line.rstrip() for line in p.read_text().splitlines())+"\n")
