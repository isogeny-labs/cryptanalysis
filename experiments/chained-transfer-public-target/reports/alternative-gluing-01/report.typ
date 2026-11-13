#set page(paper:"a4",margin:13mm)
#set text(font:"DejaVu Sans",size:8.8pt)
#set par(leading:.35em)
#text(size:17pt,weight:"bold")[Six classical models; four square candidates]
#parbreak()
2026-11-13 · actual N4 q223 / seed1 · unsigned / partial formalization
#parbreak()
#image("models.svg",width:100%)
#image("all-six.svg",width:93%)
#for p in json("page1.json") {text(p);parbreak()}
#pagebreak()
#text(size:17pt,weight:"bold")[Actual whole-group maps and longer chains]
#parbreak()
#image("chain.svg",width:100%)
#for p in json("page2.json") {text(p);parbreak()}
#pagebreak()
#text(size:17pt,weight:"bold")[Why the three alternatives differ from old J]
#parbreak()
#image("endpoint.svg",width:100%)
#for p in json("page3.json") {text(p);parbreak()}
