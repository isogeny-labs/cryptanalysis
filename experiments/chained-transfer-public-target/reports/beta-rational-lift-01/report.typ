#set page(paper:"a4",margin:13mm)
#set text(font:"DejaVu Sans",size:9pt)
#set par(leading:.32em)
#text(size:16pt,weight:"bold")[Quadratic lifts for the matched Jacobian quotient]
#parbreak()
2026-11-14 · fb21de / 7f5766 / b28edc · unsigned / finite and conditional scope
#parbreak()
#image("lift-diagram.svg",width:100%,height:95mm,fit:"contain")
#for p in json("page1.json") {text(p);parbreak()}
#pagebreak()
#text(size:15pt,weight:"bold")[Genuine quadratic Picard arithmetic: checked coverage]
#parbreak()
#image("inverse-coverage.svg",width:100%,height:68mm,fit:"contain")
#table(columns:5,align:left,stroke:.4pt,inset:4pt,..json("table.json").flatten().map(x=>text(size:8pt,x)))
#parbreak()
#for p in json("page2.json") {text(p);parbreak()}
