"""Use native document table text; preserve complete first PDF and SVG plot."""
from pathlib import Path
import json,shutil,typst
p=Path('/workspace/cryptanalysis/experiments/chained-transfer-public-target/reports/twisted-pair-result-01');d=json.loads((p/'render-data.json').read_text());panels=[]
for endpoint in d['panels']:
 cells=['[Old case / D]','[New case / D]','[Fixed kernel]']
 for row in endpoint['rows']:
  for prefix in ['old','new']:
   color='#dcebdc' if row[prefix+'_square'] else '#f0dddd';case=','.join(map(str,row[prefix+'_case']));cells.append(f'table.cell(fill:rgb("{color}"))[({case}) / {row[prefix+"_D"][0]}]')
  cells.append('[*MATCH*]' if row['fixed_match'] else '[]')
 panels.append('[#text(size:9pt,weight:"bold")['+endpoint['endpoint'].capitalize()+' endpoint: allsix]\n#v(4pt)\n#set text(size:8pt)\n#table(columns:(1fr,1fr,1fr),inset:4pt,align:center,stroke:.3pt+gray,\n'+',\n'.join(cells)+')]')
(p/'model-table.typ').write_text('#grid(columns:(1fr,1fr),gutter:8pt,\n'+',\n'.join(panels)+')\n#v(3pt)\n#text(size:7.5pt)[Green: square D. Red: nonsquare D. All correspondences and fixed-kernel matches come from the whole native records.]\n')
t=(p/'report.typ').read_text();t=t.replace('#image("all-six-correspondences.svg",width:100%,height:65mm,fit:"contain")','#include "model-table.typ"');(p/'report.typ').write_text(t)
typst.compile(str(p/'report.typ'),output=str(p/'report.pdf'),root=str(p));shutil.copyfile(__file__,p/'final-render.py');print('final PDF bytes',(p/'report.pdf').stat().st_size)
