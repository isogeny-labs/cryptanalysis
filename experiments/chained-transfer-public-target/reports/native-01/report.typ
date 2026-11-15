#set page(paper:"a4",margin:14mm)
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
