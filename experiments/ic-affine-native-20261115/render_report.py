#!/usr/bin/env python3
"""Render the frozen affine panel, retaining all targets and controls."""
import json,statistics,subprocess
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,Table,TableStyle,PageBreak
P=Path(__file__).resolve().parent
A=json.loads((P/'analysis.json').read_text()); rows=A['rows']
assert A['status']=='pass'
claim='[pcc:unverified]'
methods=['mitm','affine','affine-cached'];labels=['MITM','Affine','Affine + cache']
fig,axes=plt.subplots(1,2,figsize=(10,3.5))
for i,ax in enumerate(axes):
 selected=[r for r in rows if r['index']==i]
 for j,m in enumerate(methods):
  vals=[r[m]['cold_wall_s']*1e3 for r in selected]
  ax.scatter([j+(k-2.5)*.035 for k in range(6)],vals,s=27,color=['#536775','#c08435','#26796b'][j])
  ax.plot([j-.2,j+.2],[statistics.median(vals)]*2,color='#222')
 ax.set_xticks(range(3),labels);ax.set_title(f'N{[15,18][i]}: all six fresh targets');ax.set_ylabel('Complete cold interval (ms)');ax.grid(axis='y',alpha=.2)
fig.suptitle('Native affine IC versus same-target MITM — raw, unqualified');fig.tight_layout()
for ext in ['svg','png']:fig.savefig(P/f'cold-costs.{ext}',dpi=180)
plt.close(fig)
(P/'flow.dot').write_text('''digraph G {rankdir=TB; node [shape=box, style="rounded,filled",fillcolor="#eef4f6",fontname="Helvetica"];
 input [label="Frozen curve / base / target"];
 setup [label="Cold context + base setup"];
 mitm [label="MITM table preparation"];
 affine [label="Affine plan + optional\\nbatch-inverse-square cache"];
 query [label="Queries + exact signed lifts\\nComplete fallback at caps/zero"];
 end [label="Relations + matrix + scalar check"];
 input -> setup; setup -> mitm; setup -> affine; mitm -> query; affine -> query; query -> end;}
''')
for ext in ['svg','png']:subprocess.run(['dot','-T'+ext,str(P/'flow.dot'),'-o',str(P/f'flow.{ext}')],check=True)
for f in P.glob('*.svg'):f.write_text('\n'.join(line.rstrip() for line in f.read_text().splitlines())+'\n')
lines=['# Native affine IC: fixed-input comparison, 2026-11-16','',f'{claim} The complete native affine adapter and bounded inverse-square cache are implemented. Exhaustive registered-domain checks cover 588780 targets across two cache modes. Existing independent Python arithmetic replays all36 IC answers and24 same-target rho answers. This is an unsigned producer invocation; timing qualification remains absent.','',f'{claim} The frozen twelve triples completed without process caps. Every scalar and target matches its immutable workload. Cached and uncached affine runs preserve target, relation and rank counts. One N18 fixture117 A/A ratio is1.2339379032393336, outside0.85..1.15; it remains in every summary.','', '| Curve | Method | Median cold interval, ms | Median paired MITM/method |','|---|---|---:|---:|']
for i,n in enumerate([15,18]):
 for m in methods:
  selected=[r for r in rows if r['index']==i]
  ratio=1 if m=='mitm' else statistics.median(r['raw_cold_ratios'][m] for r in selected)
  lines.append(f'| N{n} | {m} | {statistics.median(r[m]["cold_wall_s"] for r in selected)*1e3:.6f} | {ratio:.6f} |')
lines+=['',f'{claim} Ratios use each same-target pair before taking the median; they differ from a ratio of independent medians. The cache improves the affine path, but the full comparison remains mixed: N15 is slower than MITM; N18 has a modest raw wall gain while its context-inclusive counted-S ratio is0.986258. The requested breakthrough remains an open objective.','', '![All cold costs](cold-costs.svg)','', '![Mechanism](flow.svg)','',f'{claim} Complete cold wall includes field/curve construction, base and oracle preparation, all successful and failed queries, signed lifting, collection, matrix work and verification. The counted-S model includes native query time after subtracting already-counted group-add intervals; it is a model distinct from cold wall. Input materialization, calibration and process startup remain separately recorded.','',f'{claim} Resources: one L4 allocation, CPU execution,4 requested CPUs,8GiB,900-second hard limit,780-second controller and12-second process caps, one pinned allowed CPU. The single release binary was prepared separately with locked dependencies, unchanged profile and-j2; source74f35317003ff99799f64b542b93a715434c5621 and hashes are bound in prepared-input.json. gVisor placement remains unqualified. Qualified values are null; the benchmark record is invalid for promotion.','', 'The next implementation lead is to eliminate per-query row transposition and allocation in projected linear constraints, while preserving the current core as an equivalence oracle. It requires new frozen inputs and a new binary receipt before another performance comparison. GPU throughput remains a separate unmeasured path.','', 'Claim trace: PCC-20261116-2c490e. Raw evidence: timing-001/{arms.jsonl,triples.json,references.json,host.json,summary.json}; analysis.json; independent-arithmetic-timing001.json; native-001/full-domains-001.log. The PCC ledger fork remains an integration issue; neither chain was rewritten.']
(P/'REPORT.md').write_text('\n'.join(lines)+'\n')
styles=getSampleStyleSheet();story=[]
for line in lines:
 if line.startswith('# '):story.append(Paragraph(line[2:],styles['Title']))
 elif line.startswith('|') or line.startswith('![') or not line:pass
 else:story += [Paragraph(line.replace('&','&amp;').replace('<','&lt;'),styles['BodyText']),Spacer(1,9)]
 if line.startswith('|---'):
  data=[['Curve','Method','Cold ms','MITM/method']]
  for i,n in enumerate([15,18]):
   for m in methods:
    sel=[r for r in rows if r['index']==i];ratio=1 if m=='mitm' else statistics.median(r['raw_cold_ratios'][m] for r in sel)
    data.append([f'N{n}',m,f'{statistics.median(r[m]["cold_wall_s"] for r in sel)*1e3:.6f}',f'{ratio:.6f}'])
  tab=Table(data,colWidths=[50,130,110,110]);tab.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dfecef')),('GRID',(0,0),(-1,-1),.3,colors.grey),('BOTTOMPADDING',(0,0),(-1,-1),6)]));story.extend([tab,Spacer(1,12)])
# Add legible figures on their own page.
story += [PageBreak(),Paragraph('Complete costs and mechanism',styles['Title']),Image(str(P/'cold-costs.png'),width=470,height=165),Spacer(1,18),Image(str(P/'flow.png'),width=400,height=280,kind='proportional')]
SimpleDocTemplate(str(P/'REPORT.pdf'),rightMargin=54,leftMargin=54,topMargin=45,bottomMargin=45).build(story)
