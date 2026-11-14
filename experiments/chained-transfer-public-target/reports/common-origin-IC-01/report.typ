#set page(paper:"a4",margin:13mm)
#set text(font:"DejaVu Sans",size:9pt)
#set par(leading:.35em)
#text(size:16pt,weight:"bold")[Class-input IC at the original sampled origins]
#parbreak()
2026-11-14 · q223 / seed1 · unsigned / conditional formal scope
#parbreak()
#image("same-origin-control.svg",width:100%,height:70mm,fit:"contain")
#image("all20-pairs.svg",width:100%)
#for p in json("page1.json") {text(p);parbreak()}
#pagebreak()
#text(size:16pt,weight:"bold")[Actual affine correction and remaining costs]
#parbreak()
#image("retained-legacy-availability.svg",width:100%)
#for p in json("page2.json") {text(p);parbreak()}
