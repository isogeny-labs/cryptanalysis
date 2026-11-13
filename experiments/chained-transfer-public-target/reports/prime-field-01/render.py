"""Render the exact integer proof scope, not a mathematical computation."""
from pathlib import Path
import json,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';d=s/'reports/prime-field-01';d.mkdir()
dot='''digraph Bound {
graph [rankdir=LR,bgcolor="transparent",ranksep=.35];
node [shape=box,style="rounded,filled",fillcolor="#edf5fb",fontname="DejaVu Sans",fontsize=10];
edge [fontname="DejaVu Sans",fontsize=9];
B [label="Hypothetical B / F223\nm = #B(F223)\n195 <= m <= 253"];
BK [label="Base extension B_K\nm divides #B(K)"];
E [label="Actual E / K\nK = F223 cubed\n#E(K) = 11092292"];
X [label="All59 possible m fail\nm does not divide11092292\noriginal Lean kernel",fillcolor="#fff0e8"];
B -> BK [label="rational-point subgroup"];
BK -> E [label="hypothetical K-isogeny\nequal point count",style=dashed];
E -> X;B -> X;
}'''
(d/'flow.dot').write_text(dot+'\n');subprocess.run(['dot','-Tsvg',str(d/'flow.dot'),'-o',str(d/'flow.svg')],check=True)
paragraphs=[
'Question and exact scope: can the actual q223 extension-field source become isogenous over K=F223³ to an elliptic curve defined over F223? This is an elliptic shortcut question. The positive completed transfer into Jac(C)(F223) is retained and is not contradicted by this obstruction.',
'Written proof: the actual source order is11092292, from the original independent source certificate e08eac. If B/F223 becomes K-isogenous to E, then #B(K)=11092292 by isogeny invariance of finite-field point counts. Rational points embed as a subgroup B(F223)⊂B(K), so m=#B(F223) divides11092292. Hasse gives224−2sqrt223≤m≤224+2sqrt223. Since29²≤4*223<30², the integer m lies in195..253. None of these59 integers divides11092292; contradiction.',
'Exact formal scope: NoBaseFieldCurve.lean checks three statements: the radius bounds; forall k:Fin59, (195+k.val) does not divide11092292; and the quantified implication for any Nat m with195≤m≤253. Both ORIGINAL producerLean4.35 and consumerLean4.34.1 gates pass3 declarations,zero trusted. Exact ORIGINAL PCC local bindings d8f845/180a3c/7c5dfe pass,unsigned. Audited foundations are propext and Quot.sound; the closed radius bounds use none. There is no sorry, custom axiom, native_decide or kernel bypass.',
'The actual elliptic groups, Hasse theorem, rational-point inclusion/Lagrange and isogeny point-count invariance remain standard written mathematical bridges, not formal objects in this module. This is an exact integer kernel proof with an explicit geometric/group formalization gap. It excludes the fixed prime-field elliptic model/isogeny shortcut and does not assert a general impossibility of prime-field descent, ECDLP security or a computational advantage.',
'Custody and correction: the first exact PCC binding returned2/not_covered because the caller PATH lacked lake/lean;953579 preserves the original verdict and partial binding. The SAME d8f845 claim passes after restoring the actual HOME elan path, with unchanged source,statement and verifier. Two whole original proof captures contain24 files each,30544/30564bytes (3809b4/f5d8b9), complete member/raw/archive hashes and exact standard tar/XZ round trips. No fresh lean4checker result is claimed.',
'Decision and next task: retain this negative result and pursue the higher-dimensional completed-transfer individual descent under prospective protocol74e00a. Restricted source j is outside F223, but the order argument here also rules out an isogenous F223 elliptic model. No novelty is claimed; unavailable KB/ecdb tools or a locked atlas supply no evidence of absence. Actual S3 checkpoint/live budget/capacity remain required before performance experiments.'
]
(d/'paragraphs.json').write_text(json.dumps(paragraphs,indent=2)+'\n')
(d/'REPORT.md').write_text('# Fixed q223 prime-field elliptic shortcut obstruction\n\n2026-11-13. All standing unsigned.\n\n'+'\n\n'.join(p+' [pcc:unverified]' for p in paragraphs)+'\n\nSources: prime-field/README.md and NoBaseFieldCurve.lean; evidence/prime-field-plan-01; evidence/prime-field-bindings-02; evidence/prime-field-lean-01 and02; evidence/prime-field-PATH-correction-01; frozen source order certificate. Graphs for the positive Jacobian map were checked and remain current; this additive diagram isolates the rejected elliptic shortcut.\n')
(d/'report.typ').write_text('''#set page(paper:"a4",margin:14mm)
#set text(font:"DejaVu Sans",size:9.2pt)
#set par(leading:.45em)
#text(size:18pt,weight:"bold")[A fixed prime-field elliptic shortcut fails]
#parbreak()
2026-11-13 · actual q223 source · all standing unsigned
#parbreak()
#image("flow.svg",width:100%)
#for p in json("paragraphs.json") {text(p);parbreak()}
#text(size:9pt,weight:"bold")[Sources and proof map]
#parbreak()
prime-field/README.md;NoBaseFieldCurve.lean;d8f845/180a3c/7c5dfe;both original proof captures3809b4/f5d8b9;PATH correction953579. The positive q223 Jacobian map is documented separately in V2_MAPS_01.md and the two-page native report0085e7.
''')
for p in d.glob('*.svg'):p.write_text('\n'.join(line.rstrip() for line in p.read_text().splitlines())+'\n')
shutil.copyfile(s.parent/'chained-transfer-reference/reports/g3-norm-full-02/compile.py',d/'compile.py');shutil.copyfile(__file__,d/'render.py')
