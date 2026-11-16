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
methods=['mitm','affine-cached','affine-columns'];labels=['MITM','Cached row','Cached column']
fig,axes=plt.subplots(1,2,figsize=(10,3.5))
for i,ax in enumerate(axes):
 selected=[r for r in rows if r['index']==i]
 for j,m in enumerate(methods):
  vals=[r[m]['cold_wall_s']*1e3 for r in selected]
  ax.scatter([j+(k-2.5)*.035 for k in range(6)],vals,s=27,color=['#536775','#c08435','#26796b'][j])
  ax.plot([j-.2,j+.2],[statistics.median(vals)]*2,color='#222')
 ax.set_xticks(range(3),labels);ax.set_title(f'N{[15,18][i]}: all six fresh targets');ax.set_ylabel('Complete cold interval (ms)');ax.grid(axis='y',alpha=.2)
fig.suptitle('Direct-column affine IC versus same-target MITM — raw, unqualified');fig.tight_layout()
for ext in ['svg','png']:fig.savefig(P/f'cold-costs.{ext}',dpi=180)
plt.close(fig)
(P/'flow.dot').write_text('''digraph G {rankdir=TB; node [shape=box, style="rounded,filled",fillcolor="#eef4f6",fontname="Helvetica"];
 input [label="Frozen curve / base / target"];
 setup [label="Cold context + base setup"];
 mitm [label="MITM table preparation"];
 affine [label="Cached row or column plan"];
 query [label="Queries + exact signed lifts\\nComplete fallback at caps/zero"];
 end [label="Relations + matrix + scalar check"];
 input -> setup; setup -> mitm; setup -> affine; mitm -> query; affine -> query; query -> end;}
''')
for ext in ['svg','png']:subprocess.run(['dot','-T'+ext,str(P/'flow.dot'),'-o',str(P/f'flow.{ext}')],check=True)
for f in P.glob('*.svg'):f.write_text('\n'.join(line.rstrip() for line in f.read_text().splitlines())+'\n')
lines=['# Direct-column affine IC: fixed-input comparison, 2026-11-16','',f'{claim} This panel compares the exact same complete cold pipeline with MITM, cached row-affine and cached column-affine. Columns eliminate projected images with coefficient witnesses; prefix product projection uses a shift only when2d-2<n. All preparation and query costs remain in the total.','', '| Curve | Method | Median cold interval, ms | Median paired MITM/method |','|---|---|---:|---:|']
for i,n in enumerate([15,18]):
 for m in methods:
  selected=[r for r in rows if r['index']==i]
  ratio=1 if m=='mitm' else statistics.median(r['raw_cold_ratios'][m] for r in selected)
  lines.append(f'| N{n} | {m} | {statistics.median(r[m]["cold_wall_s"] for r in selected)*1e3:.6f} | {ratio:.6f} |')
failures=[(r['index'],r['fixture'],r['calibration_ratio']) for r in rows if r['calibration_within_bound'] is False]
lines+=['',f'{claim} All twelve frozen triples and matched references completed. All36 IC and24 rho answers are checked by the existing independent Python arithmetic implementation. Cached row/column non-timing counters agree. Full registered-domain tests cover1177560 row/column and cache combinations. These are unsigned producer checks, with no signed standing.','',f'{claim} A/A failures retained in every summary: {failures}. Ratios are medians of same-target paired ratios, which differ from ratios of independent medians. No sample is discarded. Qualified values remain null and the record is invalid for promotion because gVisor placement is unqualified.','', '![All cold costs](cold-costs.svg)','', '![Mechanism](flow.svg)','',f'{claim} Cold wall includes fresh field/curve context, base and plan/cache setup, all successful and failed queries, signed lifts, collection, matrix operations and final verification. Counted-S and context-inclusive counted-S remain distinct from cold wall. Input materialization, calibration, process startup and replay are separate. The native timer subtracts group-add intervals that already receive operation pricing.','',f'{claim} Resources: one L4 allocation with CPU execution,4 requested CPUs,8GiB,900s hard allocation,780s controller,12s per process and one pinned allowed CPU. One default release binary, locked dependencies,-j2 unchanged profile, separate bounded preparation. Exact source/toolchain/binary hashes are bound in prepared-input.json and preparation receipt. All preceding negative/noisy panels remain preserved.','', f'{claim} The broad requested performance breakthrough remains open. Cached column-affine has raw paired cold MITM/column ratios0.823498 at N15 and1.161257 at N18; context-inclusive counted-S ratios0.668039 and1.066163. The separate opt-in batch-inversion MITM implementation passes correctness/accounting checks and awaits its own frozen complete-cost comparison. GPU throughput remains unmeasured.','', 'Raw evidence: timing-001/{arms.jsonl,triples.json,references.json,host.json,summary.json}; analysis.json; independent-arithmetic-timing001.json; native-001/.artifacts.json. Claim trace: PCC-20261116-cf67bb (result), PCC-20261116-efccd1 (source). The existing PCC chain fork remains an integration issue; no trust chain is rewritten.']
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
