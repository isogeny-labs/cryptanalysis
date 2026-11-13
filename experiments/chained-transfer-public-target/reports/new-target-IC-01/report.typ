#set page(paper:"a4",margin:13mm)
#set text(font:"DejaVu Sans",size:9pt)
#set par(leading:.35em)
#text(size:16pt,weight:"bold")[Actual public IC on three prime-field Jacobians]
#parbreak()
2026-11-13 · N4 q223 / seed1 · unsigned / partial formalization
#parbreak()
#image("actual-IC.svg",width:100%)
#image("all60-attempts.svg",width:100%)
#for p in json("page1.json") {text(p);parbreak()}
#pagebreak()
#text(size:16pt,weight:"bold")[Checked-answer soundness and remaining costs]
#parbreak()
#for p in json("page2.json") {text(p);parbreak()}
