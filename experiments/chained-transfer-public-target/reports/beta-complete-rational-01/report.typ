#set page(paper:"a4",margin:12mm)
#set text(font:"DejaVu Sans",size:9pt)
#set par(leading:.28em)
#text(size:16pt,weight:"bold")[Complete rational degree-13 Jacobian transfer]
#parbreak()
2026-11-14 · native 3f1ade · conditional Lean 1e2420 · unsigned
#parbreak()
#image("complete-diagram.svg",width:100%,height:107mm,fit:"contain")
#for p in json("identities.json") {text(size:7.5pt,p);parbreak()}
#for p in json("page1.json") {text(p);parbreak()}
#pagebreak()
#text(size:15pt,weight:"bold")[Explicit input coverage and proof scope]
#parbreak()
#image("exceptional-coverage.svg",width:100%,height:66mm,fit:"contain")
#for p in json("page2.json") {text(p);parbreak()}
#text(size:8pt)[Sources: BETA_COMPLETE_RATIONAL_DERIVATION_02; BETA_COMPLETE_RATIONAL_PROOF_MAP_01; evidence/beta-complete-accounting-acceptance-05 (whole native and JSON); evidence/beta-complete-Lean-acceptance-03; beta-complete-rational-bindings-01; beta-CRT-projection-acceptance-02. Earlier 19-workflow CI cd2e03 applies to c77f95dc; this evaluator’s dedicated CI is pending.]
