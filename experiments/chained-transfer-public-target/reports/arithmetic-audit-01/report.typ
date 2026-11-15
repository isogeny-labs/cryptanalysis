#set page(paper:"a4",margin:13mm)
#set text(font:"DejaVu Sans",size:9pt)
#set par(leading:.32em)
#text(size:16pt,weight:"bold")[What the sampling arithmetic actually does]
#parbreak()
2026-11-14 · native8d0c27 / vectors8c2406 · unsigned / finite scope
#parbreak()
#image("arithmetic-audit.svg",width:100%,height:105mm,fit:"contain")
#for p in json("page1.json") {text(p);parbreak()}
#pagebreak()
#text(size:15pt,weight:"bold")[More products, fewer inversions: an unpriced tradeoff]
#parbreak()
#image("source-vectors.svg",width:100%,height:105mm,fit:"contain")
#table(columns:6,align:left,stroke:.4pt,inset:4pt,..json("table.json").flatten().map(x=>text(size:7.5pt,x)))
#parbreak()
#for p in json("page2.json") {text(p);parbreak()}
#pagebreak()
#text(size:15pt,weight:"bold")[Exact identities, negative controls and remaining work]
#parbreak()
#text(font:"DejaVu Sans Mono",size:6.5pt)[#raw(read("target-identities.txt"))]
#parbreak()
#for p in json("page3.json") {text(p);parbreak()}
