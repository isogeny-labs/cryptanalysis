#set page(paper:"a4",margin:13mm)
#set text(font:"DejaVu Sans",size:9pt)
#set par(leading:.35em)
#text(size:17pt,weight:"bold")[An actual odd source isogeny over the cubic field]
#parbreak()
2026-11-13 · N4 q223 / seed1 · unsigned / partial formalization
#parbreak()
#image("actual.svg",width:100%)
#image("frobenius.svg",width:100%)
#for p in json("page1.json") {text(p);parbreak()}
#pagebreak()
#text(size:17pt,weight:"bold")[A different product; the next Jacobian remains proposed]
#parbreak()
#image("proposed.svg",width:100%)
#for p in json("page2.json") {text(p);parbreak()}
