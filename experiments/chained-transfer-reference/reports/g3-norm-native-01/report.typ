#set page(paper:"a4",margin:14mm)
#set text(font:"DejaVu Sans",size:9.5pt)
#set par(leading:.55em)
#let ps=json("paragraphs.json")
#text(size:18pt,weight:"bold")[Independent canonical-class genus-three norm]
#parbreak()
2026-11-13 · complete fixed-panel native result · all standing unsigned
#parbreak()
#image("flow.svg",width:76%)
#image("counts.svg",width:100%)
#for p in ps.at(0) {text(p);parbreak()}
#pagebreak()
#text(size:17pt,weight:"bold")[Actual geometry and partial formal proof]
#parbreak()
#for p in ps.at(1) {text(p);parbreak()}
#text(size:11pt,weight:"bold")[Primary sources and exact identities]
#parbreak()
G3_NORM_DERIVATION.md;G3_NORM_PROOF_MAP.md;pre-code source catalog and all historical cases. Original W1 Picard README,plane_quartic_pic.rs,Diem Ciani Core and original FpR/poly/curve routines. identities.json retains full exact source/destination model tags for all three fields;the diagram illustrates q=5. No new EC1/ISO1 registry admission.
#pagebreak()
#text(size:17pt,weight:"bold")[Controls, failures, custody and remaining work]
#parbreak()
#for p in ps.at(2) {text(p);parbreak()}
