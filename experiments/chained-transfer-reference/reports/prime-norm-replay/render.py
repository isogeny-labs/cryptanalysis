from pathlib import Path
import subprocess,json
p=Path(__file__).resolve().parent
subprocess.run(['dot','-Tsvg',str(p/'flow.dot'),'-o',str(p/'flow.svg')],check=True)
f=p/'flow.svg';f.write_text('\n'.join(x.rstrip() for x in f.read_text().splitlines())+'\n')
d=json.loads((p/'counts.json').read_text());v=d['source_guards_unchanged']
parts=['<svg xmlns="http://www.w3.org/2000/svg" width="900" height="180" viewBox="0 0 900 180">','<rect width="900" height="180" fill="white"/>','<g font-family="DejaVu Sans" fill="#233943">','<text x="25" y="26" font-size="18">Complete replay input guards · exact files, n=773</text>']
for i,(name,n) in enumerate(v.items()):
 y=47+49*i;w=580*n/max(v.values());parts += [f'<text x="25" y="{y+19}" font-size="16">{name}</text>',f'<rect x="135" y="{y}" width="{w}" height="29" fill="#397b64"/>',f'<text x="{149+w}" y="{y+21}" font-size="16">{n}</text>']
parts+=['<text x="25" y="164" font-size="13">All hashes unchanged;not timing or performance observations.</text>','</g></svg>'];(p/'guards.svg').write_text('\n'.join(parts)+'\n')
