"""Prospective report/diagram rendering only, without research calculations."""
from pathlib import Path
import subprocess,shutil,typst
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';p=s/'reports/observer-storage-proposal-02';p.mkdir()
(p/'flow.dot').write_text('''digraph proposed {graph[rankdir=TB,bgcolor="white",ranksep=.34,nodesep=.35];node[shape=box,style=rounded,fontname="DejaVu Sans",fontsize=10];edge[fontname="DejaVu Sans",fontsize=9];
old[label="Original arithmetic and hooks: FROZEN\\nconsumer5ac / producer3d49\\nsame40forward-dual +20inverse cases",color="#295477"];
store[label="PROPOSED observer storage only\\nthread-local first-entry owner check\\ncanonical key index + Vec counters + small cache\\nsame checked increments and v2 schema",style="rounded,dashed",color="#a57535"];
parity[label="Required whole-data parity\\nall12 observed old cold packets\\nboth complete60-case reuse streams\\n4 unfiltered math tests / actual omission controls",color="#295477"];
full[label="Required NEW full cold result: UNKNOWN\\n120 separate processes within900s\\nthen original combined reuse900s\\n2GiB per process; no time/price/gain claim",style="rounded,dashed",color="#a57535"];
old->store[label="no field/map/panel/validation changes",style=dashed];store->parity[label="preserve every field and canonical ledger",style=dashed];parity->full[label="accept only complete unchanged analyzer",style=dashed];}''');subprocess.run(['dot','-Tsvg',str(p/'flow.dot'),'-o',str(p/'flow.svg')],check=True)
(p/'report.typ').write_text(r'''#set page(paper:"a4",margin:14mm)
#set text(font:"DejaVu Sans",size:9.6pt)
#set par(leading:.45em)
#text(size:17pt,weight:"bold")[Complete the cold census with the same observer units]
#v(4pt)
#text(fill:rgb("#a57535"),weight:"bold")[PROSPECTIVE STUDY · no storage implementation or new census result]

The original cold900s census timed out after12 complete cases, with108 missing. Both60-case reused-context arms completed. Preserve those whole records and the unpriced multiplication/inversion tradeoff. This study changes observer bookkeeping to try the same full120 cold processes within the same bound. It does not measure an ECDLP speedup.

#image("flow.svg",width:100%,height:101mm,fit:"contain")

== Acceptance and actual rejection controls
Keep all original field operations, hooks, labels, counts, mathematical branches and validation. Disabled mode is only for four-test mathematical parity; actual census must be enabled. Preserve strict first-owner rejection even on foreign zero-hit/phase/scope/snapshot entry. Test cache collisions and checked increments without unsafe pointers. Full canonical v2 ledgers and every mathematical packet must match the12 old cold observations and both complete reused streams, with no masks. Real missing hooks and an actual whole-packet omission must reject.

The unchanged runner retains120 cold processes in one900s bound and the two reuse arms in their original combined900s bound;2GiB per process. Complete acceptance requires all cases and the unchanged full analyzer. A timeout, mismatch or partial result remains retained and does not discharge the full census requirement. No warm/cold denominator or price is changed.

== Replay resource gate, stated separately
The new22nd replay's initial120s cold compilation failed in both CI and a physical checkout,5d8adb, before native tests. A separate prospective engineering protocol03 permits900s preparation of the unchanged original engine, then the original120s wrapper and900s native checks within the same outer6000s. The old full cold120 compilation remains unmet. The two matched supplied-source models atD12/D24 stay unsupported even after any successful replay.

#text(size:8pt)[Sources: OBSERVER_STORAGE_COLD_PROTOCOL_02.md; NONDUAL_REPLAY_BUILD_PROTOCOL_03.md; original01e617/b5fd45/471848/ee232d; whole raw in genuine17; original norm-arithmetic-audit taps/materializer/runner; native model negatives27fb3a/6d2c97 and finiteproof68cd8c remain scoped. Full accounting still needs calibrated prices, admitted hardware and strongest matched rho/IC references. No novelty, signed execution, new Jacobian map, paid launch or waiver.]
''');typst.compile(str(p/'report.typ'),output=str(p/'report.pdf'),root=str(p))
(p/'REPORT.md').write_text('''# Prospective storage remedy for the incomplete cold census

[Protocol02](../../OBSERVER_STORAGE_COLD_PROTOCOL_02.md) freezes only observer storage/owner bookkeeping changes, all original arithmetic/hooks/case/validation bytes, full whole-ledger parity and actual rejection controls. Original cold12complete/108missing and both complete60-case reuse streams remain mandatory references; the new120 cold result is unknown. No observer implementation or new measurement exists yet. [pcc:unverified]

[PDF](report.pdf) · [editable proposed workflow](flow.dot) · [SVG](flow.svg). No new quantitative result graph exists because this is a prospective protocol. [Engineering protocol03](../../NONDUAL_REPLAY_BUILD_PROTOCOL_03.md) separately records and remedies the observed cold compiler setup limit; its larger explicit preparation allowance does not satisfy the old whole cold120 build requirement. [pcc:unverified]
''');shutil.copyfile(__file__,p/'original-render.py');print('PDF bytes',(p/'report.pdf').stat().st_size)
