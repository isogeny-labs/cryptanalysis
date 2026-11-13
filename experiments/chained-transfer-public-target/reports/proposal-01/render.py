"""Prospective report rendering only; native inputs/results do not exist yet."""
from pathlib import Path
import json,subprocess,shutil
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';d=s/'reports/proposal-01';d.mkdir(parents=True)
dot='''digraph P {
graph [rankdir=LR,bgcolor="transparent",nodesep=.25,ranksep=.32];
node [shape=box,style="rounded,filled",fillcolor="#edf5fb",fontname="DejaVu Sans",fontsize=11];
edge [fontname="DejaVu Sans",fontsize=10];
O [label="Existing N4/B2\ncomplete IC body\nq mod 12 = 7"];
P [label="Proposed P1\npublic Q only\noriginal body derivative",fillcolor="#fff3df"];
B [label="Proposed P2\nfield / model / P0\ncompleted-map bridge",fillcolor="#fff3df"];
E [label="Future comparison\nadmission required\nall cold solving costs",fillcolor="#fff3df"];
O -> P [style=dashed,label="API equivalence"];
P -> B [style=dashed]; B -> E [style=dashed];
}'''
(d/'flow.dot').write_text(dot+'\n');subprocess.run(['dot','-Tsvg',str(d/'flow.dot'),'-o',str(d/'flow.svg')],check=True)
paragraphs=[
'Question and source status: connect the completed G3 coordinate transfer and canonical-class norm to a solver taking a public elliptic target. Original N4/B2 already implements relations, linear algebra and individual target descent. Twelve whole primary sources are retained in parent b992d8 and genuinely published 5327f4; their catalog hashes match. Historical speed tables are not newly validated results. Protocol7e016c is prospective; no new case or solver has run.',
'P1 proposal: original Inst::search(223,1,200000), generated only after normal protocol publication and a ready child PR. Exact curve/subgroup identity is not generated yet; candidate_id remains null. Derive public IC and plain-rho bodies solely by replacing the scalar argument with Q and removing target construction. Retain original bodies as controls. Known witnesses stay outside actual public requests; admission rejects unknown scalar/witness fields, wrong tags, noncanonical and invalid points.',
'Frozen correctness scope: five targets from witness residues1,2,17,floor(ell/2),ell-1; each has the original six-attempt B2 retry schedule. Retain every failure and verify every success with original independent source arithmetic. All five IC solves must succeed before that smoke is accepted. Field, nonsingularity, exact subgroup and Hasse-interval order checks are explicit. Plain rho is a separate correctness control, never an IC fallback or a strongest-reference claim.',
'P2 proposal: additive versioned constructor and completed maps, reusing original field/polynomial/Picard engines. Check explicit field basis products and Frobenius; all model polynomial coefficients and infinity/ordinate signs; plane Moore transport; geometric origin and multiplicities. The same raw class key at a new P0 changes by delta=[P0_new-P0_old]; the same actual old class is raw_new-delta. Prove and test that bridge rather than fit a scalar shift. Give faithful written arguments and feasible exact Lean bindings; actual geometry gaps stay explicit.',
'Negative results and limits: old q<=11 subgroup-enumeration IC smokes were withdrawn. N4 requires q mod12=7; q5/q11 do not satisfy that constructor domain. Keep all old q5/7/11 exhaustive transfer/norm controls unchanged. Never mutate V1 private old normal forms/origin to admit q223. An API accounting correction is not an algorithmic improvement. Comparative runs still need the original S3 checkpoint and live budget/capacity admission, strongest applicable references, all cold phases, isolation and memory/reuse accounting.',
'Decision and next action: publish this pre-code protocol in a ready child under PR1521, implement P1 and preserve the full bounded development evidence, then advance to P2 and admitted cost work. Current KB tools are unavailable; prior actual fallback127 receipts and direct primary reads are retained, with no novelty/absence inference. crypto-autoresearcher remains vault8edec422 locked. Existing transfer/native/full/CI graph sources were checked; mathematical map edges remain unchanged. Dashed edges above are proposals.'
]
(d/'paragraphs.json').write_text(json.dumps(paragraphs,indent=2)+'\n')
(d/'summary.json').write_text(json.dumps(dict(protocol_claim='PCC-20261113-7e016c',status='prospective/no new case or native solver',candidate_id=None,proposed_constructor=dict(q=223,seed=1,max_tries=200000),source_catalog='../../evidence/primary-01/catalog.json',parent='1e4f1292',primary_whole='b992d8/5327f4',standing='unsigned/sourceobservations andproposals only'),indent=2)+'\n')
(d/'REPORT.md').write_text('# Public-target destination calculus: prospective source review\n\n2026-11-13. Protocol7e016c, before new cases/code.\n\n'+'\n\n'.join(p+' [pcc:unverified]' for p in paragraphs)+'\n\nSources: [protocol](../../PROTOCOL-01.md), [whole-primary source catalog](../../evidence/primary-01/catalog.json), parent G3_NORM_DERIVATION.md/G3_NORM_PROOF_MAP.md, original N4/B2 README/PROTOCOL/solver/common/ghs/ic files in b992d8. Editable DOT/SVG, Typst and JSON are adjacent. Existing canonical graphs checked; no new mathematical edge admitted.\n')
(d/'report.typ').write_text('''#set page(paper:"a4",margin:14mm)
#set text(font:"DejaVu Sans",size:9.2pt)
#set par(leading:.45em)
#text(size:18pt,weight:"bold")[Public-target destination calculus]
#parbreak()
2026-11-13 · prospective protocol7e016c · all standing unsigned
#parbreak()
#image("flow.svg",width:100%)
#for p in json("paragraphs.json") {text(p);parbreak()}
#text(size:10pt,weight:"bold")[Sources]
#parbreak()
PROTOCOL-01.md; evidence/primary-01/catalog.json; parent primary archiveb992d8/actual5327f4; original N4/B2 study; parent canonical-norm derivation/proof map. No new executable transfer edge, native result or timing ratio is represented.
''')
shutil.copyfile(r/'experiments/chained-transfer-reference/reports/g3-norm-full-02/compile.py',d/'compile.py');shutil.copyfile(__file__,d/'render.py')
