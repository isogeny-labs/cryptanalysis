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
methods=['mitm','mitm-batched','mitm-xonly'];labels=['Original','Full batch','Abscissa only']
fig,axes=plt.subplots(1,2,figsize=(10,3.5))
for i,ax in enumerate(axes):
 selected=[r for r in rows if r['index']==i]
 for j,m in enumerate(methods):
  vals=[r[m]['cold_wall_s']*1e3 for r in selected]
  ax.scatter([j+(k-2.5)*.035 for k in range(6)],vals,s=27,color=['#536775','#c08435','#26796b'][j])
  ax.plot([j-.2,j+.2],[statistics.median(vals)]*2,color='#222')
 ax.set_xticks(range(3),labels);ax.set_title(f'N{[15,18][i]}: all six fresh targets');ax.set_ylabel('Complete cold interval (ms)');ax.grid(axis='y',alpha=.2)
fig.suptitle('Abscissa-only MITM IC versus same-target MITM — raw, unqualified');fig.tight_layout()
for ext in ['svg','png']:fig.savefig(P/f'cold-costs.{ext}',dpi=180)
plt.close(fig)
(P/'flow.dot').write_text('''digraph G {rankdir=TB; node [shape=box, style="rounded,filled",fillcolor="#eef4f6",fontname="Helvetica"];
 input [label="Frozen curve / base / target"];
 setup [label="Cold context + base setup"];
 mitm [label="Original or batched MITM table"];
 affine [label="Abscissa-only native preparation"];
 query [label="Queries + exact signed lifts\\nComplete fallback at caps/zero"];
 end [label="Relations + matrix + scalar check"];
 input -> setup; setup -> mitm; setup -> affine; mitm -> query; affine -> query; query -> end;}
''')
for ext in ['svg','png']:subprocess.run(['dot','-T'+ext,str(P/'flow.dot'),'-o',str(P/f'flow.{ext}')],check=True)
for f in P.glob('*.svg'):f.write_text('\n'.join(line.rstrip() for line in f.read_text().splitlines())+'\n')
lines=['# Abscissa-only MITM IC: fixed-input comparison, 2026-11-16','',f'{claim} Exact registered N15/N18 curves, archived prefix bases and fresh fixtures148..153 compare original MITM, full-point batch and abscissa-only batch in one binary. The native x-only path omits ordinary ordinates and enables PCLMUL after runtime detection. Complete signed query checks are unchanged.','', '| Curve | Method | Median cold interval, ms | Median paired original/method |','|---|---|---:|---:|']
for i,n in enumerate([15,18]):
 for m in methods:
  selected=[r for r in rows if r['index']==i]
  ratio=1 if m=='mitm' else statistics.median(r['raw_cold_ratios'][m] for r in selected)
  lines.append(f'| N{n} | {m} | {statistics.median(r[m]["cold_wall_s"] for r in selected)*1e3:.6f} | {ratio:.6f} |')
failures=[(r['index'],r['fixture'],r['calibration_ratio']) for r in rows if r['calibration_within_bound'] is False]
lines+=['',f'{claim} Twelve frozen triples completed,36 IC and24 rho answers replayed in existing independent Python arithmetic, and non-timing query/matrix counters match across methods. Every arm carries exactly the shared per-curve calibration, with a positive hash-lookup unit. Retained A/A failures: {failures}. Zero process caps. Producer checks are unsigned.','',f'{claim} Native x86 preparation independently executes the fixed whole-domain witness check before timing:883170 comparisons pass with PCLMUL capability true. Local full/x-only comparisons cover1766340 targets plus field/edge cases. The original packed-key error and all correction logs remain archived.','',f'{claim} Full cold wall includes fresh context, base construction, complete oracle/table setup, failed/successful queries, collection, matrix work and scalar verification. The original model prices setup group additions, whereas native arms price whole setup nanoseconds including map/allocation work. Thus the modeled S ratios have different setup scopes and are not an equivalent complete-cost comparison. Raw model components remain visible, without a comparative model claim. A later opt-in native-setup reference will align that boundary.','', '![All cold costs](cold-costs.svg)','', '![Mechanism](flow.svg)','',f'{claim} One L4 allocation, CPU execution,4 requested CPUs,8GiB,900s hard,780s controller,12s per process,one pinned allowed CPU. Fresh process per arm,all six orders. Sourcea375b2145069d9384dc53525cc1e9b90b074e482,locked-j2 default release and separate bounded preparation. Hashes and exact resource snapshots are retained. All qualified values remain null; record invalid for promotion under the frozen exploratory protocol.','',f'{claim} Calibration, unit-file loading, process startup and existing-Python replay remain separate from the cold interval. Earlier204 IC arms with zero lookup pricing remain partial models per correction9ceda4; none is backfilled or promoted. The broad performance objective remains open. Prefix inverse reuse is a separate newly implemented, unmeasured candidate.','', 'Evidence: timing-001 raw files and per-curve calibrations, analysis.json, independent-arithmetic-timing001.json,build-001 preparation receipts. Source b144d0, lookup correction9ceda4 and the appended result statement retain scope. No trust-chain rewrite or ledger bypass.']
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
