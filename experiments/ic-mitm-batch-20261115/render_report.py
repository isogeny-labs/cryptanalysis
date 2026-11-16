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
methods=['mitm','mitm-batched','affine-columns'];labels=['MITM','Batched MITM','Column affine']
fig,axes=plt.subplots(1,2,figsize=(10,3.5))
for i,ax in enumerate(axes):
 selected=[r for r in rows if r['index']==i]
 for j,m in enumerate(methods):
  vals=[r[m]['cold_wall_s']*1e3 for r in selected]
  ax.scatter([j+(k-2.5)*.035 for k in range(6)],vals,s=27,color=['#536775','#c08435','#26796b'][j])
  ax.plot([j-.2,j+.2],[statistics.median(vals)]*2,color='#222')
 ax.set_xticks(range(3),labels);ax.set_title(f'N{[15,18][i]}: all six fresh targets');ax.set_ylabel('Complete cold interval (ms)');ax.grid(axis='y',alpha=.2)
fig.suptitle('Batched MITM IC versus same-target MITM — raw, unqualified');fig.tight_layout()
for ext in ['svg','png']:fig.savefig(P/f'cold-costs.{ext}',dpi=180)
plt.close(fig)
(P/'flow.dot').write_text('''digraph G {rankdir=TB; node [shape=box, style="rounded,filled",fillcolor="#eef4f6",fontname="Helvetica"];
 input [label="Frozen curve / base / target"];
 setup [label="Cold context + base setup"];
 mitm [label="Original or batched MITM table"];
 affine [label="Cached column-affine plan"];
 query [label="Queries + exact signed lifts\\nComplete fallback at caps/zero"];
 end [label="Relations + matrix + scalar check"];
 input -> setup; setup -> mitm; setup -> affine; mitm -> query; affine -> query; query -> end;}
''')
for ext in ['svg','png']:subprocess.run(['dot','-T'+ext,str(P/'flow.dot'),'-o',str(P/f'flow.{ext}')],check=True)
for f in P.glob('*.svg'):f.write_text('\n'.join(line.rstrip() for line in f.read_text().splitlines())+'\n')
lines=['# Batched MITM IC: fixed-input comparison, 2026-11-16','',f'{claim} This panel compares complete cold MITM, batched MITM and cached column-affine on the same registered curves, archived prefix bases and fresh target fixtures136..141. Batched preparation preserves pair order and first witness selection while sharing inversions across bounded chunks. All setup remains charged.','', '| Curve | Method | Median cold interval, ms | Median paired MITM/method |','|---|---|---:|---:|']
for i,n in enumerate([15,18]):
 for m in methods:
  selected=[r for r in rows if r['index']==i]
  ratio=1 if m=='mitm' else statistics.median(r['raw_cold_ratios'][m] for r in selected)
  lines.append(f'| N{n} | {m} | {statistics.median(r[m]["cold_wall_s"] for r in selected)*1e3:.6f} | {ratio:.6f} |')
failures=[(r['index'],r['fixture'],r['calibration_ratio']) for r in rows if r['calibration_within_bound'] is False]
lines+=['',f'{claim} All twelve frozen triples and matched references completed. All36 IC and24 rho answers pass the existing independent Python arithmetic implementation. Original/batched MITM query and matrix counters agree; setup counters intentionally differ because complete native preparation replaces independent-addition pricing. Separate source checks match883170 exact returned witnesses across chunk sizes1,7,1024. These are unsigned producer checks.','',f'{claim} Retained A/A failures: {failures}. Ratios are medians of same-target paired ratios, rather than ratios of independent medians. Qualified values remain null; the record is invalid for promotion under the frozen exploratory protocol. No sample is discarded.','', '![Cold costs](cold-costs.svg)','', '![Mechanism](flow.svg)','',f'{claim} Cold wall includes fresh context, base construction, oracle/table setup, all successful and failed queries, signed lifts, collection, matrix work and final verification. Batch setup includes map/scratch allocation, batch inversions and exceptional additions. Its measured native nanoseconds are charged once, without hypothetical independent-addition charges. The archived counted-S and context-inclusive counted-S models omit lookup/guard pricing because ns_per_lookup is zero. They are partial models; see problems/ic-probe-lookup-pricing.md and the adjacent audit. They are separate from complete cold wall; calibration, process startup and independent replay are separate.','',f'{claim} Resources: one L4 allocation with CPU execution,4 requested CPUs,8GiB,900s hard allocation,780s controller,12s process cap and one pinned allowed CPU. A single separately prepared default release executable uses locked dependencies,-j2 unchanged profile. Source935528687a0afcfa0132b7253386d00c8ffefcef; exact source/toolchain/binary/workload hashes are bound by prepared-input.json, receipt and immutable candidate/workload manifests.','',f'{claim} This exploratory comparison does not establish a qualified performance breakthrough or a general complexity improvement. Earlier negative/noisy results remain intact. A future Tier1 claim needs a separately frozen qualifying allocation, noise receipts and paired confidence rule; GPU throughput remains unmeasured.','', 'Raw evidence: timing-001/{arms.jsonl,triples.json,references.json,host.json,summary.json}, analysis.json and independent-arithmetic-timing001.json. Source claim PCC-20261116-ebf2bf; result claim PCC-20261116-a3e74d; pricing correction PCC-20261116-9ceda4. The PCC ledger fork is preserved; no trust-chain rewrite or promotion.']
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
