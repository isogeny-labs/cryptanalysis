from pathlib import Path
import json,subprocess
p=Path(__file__).resolve().parent;d=json.loads((p/'counts.json').read_text())
subprocess.run(['dot','-Tsvg',str(p/'flow.dot'),'-o',str(p/'flow.svg')],check=True)
f=p/'flow.svg';f.write_text('\n'.join(x.rstrip() for x in f.read_text().splitlines())+'\n')
v=d['c0_norm']['degrees'];svg=['<svg xmlns="http://www.w3.org/2000/svg" width="900" height="225" viewBox="0 0 900 225">','<rect width="900" height="225" fill="white"/>','<g font-family="DejaVu Sans" fill="#253d48">','<text x="20" y="26" font-size="19">C0 complete rational input population · n=12317</text>','<text x="20" y="47" font-size="13">Exact classes · disjoint finite degrees · no performance scale</text>']
for i,n in enumerate(v):
 y=63+40*i;w=600*n/max(v)
 svg += [f'<text x="20" y="{y+18}" font-size="15">degree{i}</text>',f'<rect x="117" y="{y}" width="{max(2,w)}" height="26" fill="#367c65"/>',f'<text x="{w+130}" y="{y+18}" font-size="15">{n}</text>']
svg += ['<text x="20" y="209" font-size="14">Overlapping controls: repeated118 · nonsplit5116 · z=0 supports238</text>','</g></svg>'];(p/'counts.svg').write_text('\n'.join(svg)+'\n')
