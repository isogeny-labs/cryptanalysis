#set page(paper:"a4",margin:14mm)
#set text(font:"DejaVu Sans",size:9.2pt)
#set par(leading:.4em)
#text(size:18pt,weight:"bold")[A complete compatible-kernel census]
#parbreak()
2026-11-13 · fixed N4 q223 / seed1 · unsigned / partial formalization
#parbreak()
#image("finite.svg",width:100%)
#image("kernel-counts.svg",width:96%)
#for p in json("page1.json") {text(p);parbreak()}
#pagebreak()
#text(size:18pt,weight:"bold")[The unique kernel is the original norm kernel]
#parbreak()
#image("norm.svg",width:100%)
#for p in json("page2.json") {text(p);parbreak()}
#pagebreak()
#text(size:18pt,weight:"bold")[Next: a different gluing on the intermediate]
#parbreak()
#image("proposal.svg",width:100%)
#for p in json("page3.json") {text(p);parbreak()}
#text(size:8.5pt)[All exact matrices and observations are retained. Conditional written geometry and partial formalization are explicit; no stronger ECDLP/security or performance conclusion is made.]
