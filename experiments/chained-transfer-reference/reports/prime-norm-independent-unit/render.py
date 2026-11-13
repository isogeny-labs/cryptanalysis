from pathlib import Path
import json,subprocess
p=Path(__file__).resolve().parent
d=json.loads((p/'counts.json').read_text())
subprocess.run(['dot','-Tsvg',str(p/'flow.dot'),'-o',str(p/'flow.svg')],check=True)
f=p/'flow.svg';f.write_text('\n'.join(x.rstrip() for x in f.read_text().splitlines())+'\n')
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="900" height="265" viewBox="0 0 900 265">','<rect width="900" height="265" fill="white"/>','<g font-family="DejaVu Sans" fill="#233943">','<text x="25" y="27" font-size="19">Independent complete rational input population</text>','<text x="25" y="49" font-size="13">Exact unit:classes · n=12317 · disjoint finite-support degrees</text>']
for i,value in enumerate(d['degrees']):
 y=69+43*i;w=610*value/max(d['degrees'])
 svg += [f'<text x="25" y="{y+18}" font-size="16">degree{i}</text>',f'<rect x="120" y="{y}" width="{max(2,w)}" height="27" fill="#397b64"/>',f'<text x="{132+w}" y="{y+19}" font-size="16">{value}</text>']
svg+=['<text x="25" y="222" font-size="14">Overlapping controls:repeated118 · nonsplit5116 · pole supports2/cover</text>','<text x="25" y="246" font-size="13">Full enumeration;no statistical uncertainty or performance estimate.</text>','</g></svg>']
(p/'counts.svg').write_text('\n'.join(svg)+'\n')
