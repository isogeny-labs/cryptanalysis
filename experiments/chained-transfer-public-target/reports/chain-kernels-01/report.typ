#set page(paper:"a4",margin:13mm)
#set text(font:"DejaVu Sans",size:9pt)
#set par(leading:.35em)
#text(size:17pt,weight:"bold")[Which chained kernels are free over Z/4?]
#parbreak()
2026-11-13 · actual N4 q223 / seed1 · unsigned / partial formalization
#parbreak()
#image("kernels.svg",width:100%)
#image("intersections.svg",width:100%)
#for p in json("page1.json") {text(p);parbreak()}
#pagebreak()
#text(size:17pt,weight:"bold")[Repeated routes through the same product collapse]
#parbreak()
#image("collapse.svg",width:100%)
#for p in json("page2.json") {text(p);parbreak()}
