"""Evidence-linked rendering only; no scientific arithmetic or verifier."""
from pathlib import Path
import json,shutil,subprocess
s=Path('/workspace/cryptanalysis/experiments/chained-transfer-reference')
d=s/'reports/g3-norm-ci-01';d.mkdir()
summary=json.loads((s/'evidence/g3-norm-own-ci-acceptance-01/acceptance.json').read_text())
(d/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
dot='''digraph CI {
graph [rankdir=LR,bgcolor="transparent",nodesep=.25,ranksep=.35];
node [shape=box,style="rounded,filled",fillcolor="#edf5fb",fontname="DejaVu Sans",fontsize=11];
edge [fontname="DejaVu Sans",fontsize=10];
S [label="Frozen sources\nconsumer 069644bf\nproducer 3d49af7f"];
L [label="Local full02\n438 source guards\n7b231c"];
C [label="Own run 43400864083\nall seven jobs SUCCESS\n168c99, unsigned"];
B [label="Remaining research\npublic-target IC bridge\ncomplete cost comparison",fillcolor="#fff3df"];
S -> L; S -> C; L -> B; C -> B;
}'''
(d/'flow.dot').write_text(dot+'\n');subprocess.run(['dot','-Tsvg',str(d/'flow.dot'),'-o',str(d/'flow.svg')],check=True)
paragraphs=[
'Observed scope, 168c99 (unsigned): all seven terminal jobs in the exact-source run completed successfully. The new canonical-norm job 131803082298 contains 36 native JSON records, all equal to the original accepted 12 consumer and 24 producer records. All 24 exact original PCC verdicts pass; claim IDs, commits and canonical digests agree using the unchanged original PCC claim_digest function.',
'Independent local full02, 7b231c (unsigned): exact clean consumer069644bf / producer3d49af7f; all 438 outer input guards unchanged; all 23 outer and 20 nested producer native/tee pairs return zero. These are phase pairs, not 43 independent mathematical tests. Both original norm proof gates audit 13 declarations with zero trusted declarations. Actual algebraic-geometry bridges remain written/native.',
'Custody: raw02 is one whole 790,964-byte standard tar/XZ archive with 471 files, every-member hashes, raw/archive hashes and an exact round trip (8f9f11). All seven whole logs and API responses, dispatch/discovery, 438 source snapshots and the collector are retained. The prior partial 134,968-byte raw01 remains immutable (d82dd3). Remote availability is a separate actual-publication receipt.',
'Preserved failures: the first collector compared canonical claim hashes with raw pretty-JSON file hashes and stopped. Frozen b15b45 precedes the bookkeeping correction; no native source, theorem, verifier or acceptance criterion changed. Optional artifact ZIP access received storage-proxy403 (963670); zero ZIPs downloaded. Exit/guard observations derive from the unchanged driver success marker and successful job step; standalone job-artifact exit files were not downloaded.',
'Next and limits: CI is settled; no re-poll or re-dispatch. The existing N4/B2 destination solver has a planted-target API and a q mod 12 = 7 field restriction. Add a public-Q interface and explicit field/model/basepoint bridges under a new pre-code protocol. Preserve the withdrawn subgroup-enumeration result. No measured computational advantage or signed execution/full-geometry verdict is established. Main merge and authentic root-fixture access requirements remain open.'
]
(d/'paragraphs.json').write_text(json.dumps(paragraphs,indent=2)+'\n')
(d/'REPORT.md').write_text('# Canonical norm: exact-source CI addendum\n\n2026-11-13. Additive evidence report; earlier frozen reports remain unchanged. All standing unsigned.\n\n'+'\n\n'.join(p+' [pcc:unverified]' for p in paragraphs)+'\n\nSources: `evidence/g3-norm-own-ci-acceptance-01/acceptance.json`, `evidence/g3-norm-own-ci-raw-02/custody.json`, `evidence/g3-norm-ci-collector-correction-01/failure-and-plan.json`, `evidence/g3-norm-ci-artifact-access-01/failure.json`, `G3_NORM_DERIVATION.md`, `G3_NORM_PROOF_MAP.md`. Editable flow.dot/flow.svg and full observation JSON are adjacent. Existing canonical transfer graph and native/full reports were checked; mathematical vertices/edges remain unchanged.\n')
(d/'report.typ').write_text('''#set page(paper:"a4",margin:14mm)
#set text(font:"DejaVu Sans",size:9.3pt)
#set par(leading:.48em)
#text(size:18pt,weight:"bold")[Canonical norm: exact-source CI receipt]
#parbreak()
2026-11-13 · all standing unsigned · no cost claim
#parbreak()
#image("flow.svg",width:100%)
#for p in json("paragraphs.json") {text(p);parbreak()}
#text(size:10pt,weight:"bold")[Source-linked evidence]
#parbreak()
g3-norm-own-ci-acceptance-01/acceptance.json; g3-norm-own-ci-raw-02/custody.json; g3-norm-ci-collector-correction-01; g3-norm-ci-artifact-access-01; full02 acceptance7b231c; written derivation/proof map. Sources and editable figure accompany this report. Mathematical transfer graph is unchanged.
''')
shutil.copyfile(s/'reports/g3-norm-full-02/compile.py',d/'compile.py')
shutil.copyfile(__file__,d/'render.py')
