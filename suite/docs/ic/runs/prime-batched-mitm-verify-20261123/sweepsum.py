import json,glob,re
rows=[]
for f in glob.glob('sweep/s*-b*/audit-results.json'):
    m=re.search(r's(\d+)-b(\d+)',f); size,b=int(m[1]),int(m[2]); r=list(json.load(open(f)).values())[0]; a=r['arms']
    rows.append((b,size,a['B0']['S_mean'],a['B3']['S_mean'],a['L2']['S_mean'],a['L2']['S_vs_B0'][0],a['L2']['wall_vs_B0'][0],r['L2_vs_B3']['wall'],a['L2']['S_over_rho'],a['B0']['S_over_rho'],a['L3']['S_mean'],a['L3']['S_over_rho']))
print('bits size | S B0  B3(native scalar folded)  L2 | L2 S ratio vs B0, wall ratio vs B0 | L2 vs B3 wall [CI] | S/rho L2 (B0) | L3 S, S/rho')
for r in sorted(rows): print('%d %5d | %6.1f %6.1f %6.1f | %.2f %.2f | %.2f [%.2f,%.2f] | %.1f (%.1f) | %.1f %.1f'%(r[0],r[1],r[2],r[3],r[4],r[5],r[6],*r[7],r[8],r[9],r[10],r[11]))
