#!/usr/bin/env python3
"""Render all fixed prefix-cache data and the declared measurement limits."""
import json,statistics,subprocess
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak
P=Path(__file__).resolve().parent
A=json.loads((P/'analysis.json').read_text());assert A['status']=='pass'
R=A['rows'];T=json.loads((P/'timing-001/triples.json').read_text());H=json.loads((P/'timing-001/host.json').read_text())
M=['mitm-native','mitm-batched','mitm-xonly','mitm-prefix'];L=['Original','Full batch','X only','Prefix cache'];C=['#647782','#b79354','#397b88','#287455'];tag='[pcc:unverified]'
case=lambda i,m:next(c for c in A['cases'] if c['index']==i and c['method']==m)
fig,axes=plt.subplots(1,2,figsize=(10.4,3.6))
for i,ax in enumerate(axes):
 rows=[r for r in R if r['index']==i]
 for j,m in enumerate(M):
  vals=[r[m]['cold_wall_s']*1e3 for r in rows];ax.scatter([j+(k-11.5)*.012 for k in range(24)],vals,s=14,color=C[j]);ax.plot([j-.22,j+.22],[statistics.median(vals)]*2,color='#222')
 ax.set_xticks(range(4),L);ax.set_title(f'N{[15,18][i]}: every frozen target');ax.set_ylabel('Complete cold wall (ms)');ax.grid(axis='y',alpha=.2)
fig.suptitle('Prefix inverse reuse — raw, unqualified');fig.tight_layout()
for ext in ['svg','png']:fig.savefig(P/f'cold-costs.{ext}',dpi=180)
plt.close(fig)
fig,axes=plt.subplots(1,2,figsize=(10.4,3.4))
for i,ax in enumerate(axes):
 for j,m in enumerate(M[1:]):
  rows=[r for r in R if r['index']==i];vals=[r['raw_cold_ratios'][m] for r in rows];c=case(i,m);med=c['raw_cold_median_ratio'];lo,hi=c['raw_cold_paired_median_bootstrap95']
  ax.scatter([j+(k-11.5)*.012 for k in range(24)],vals,s=13,color=C[j+1],alpha=.7);ax.errorbar(j,med,yerr=[[med-lo],[hi-med]],fmt='o',color='#111',capsize=5)
 ax.axhline(1,color='#888',linestyle=':');ax.set_xticks(range(3),L[1:]);ax.set_title(f'N{[15,18][i]}');ax.set_ylabel('Original / candidate, paired cold ratio');ax.grid(axis='y',alpha=.2)
fig.suptitle('All paired ratios and frozen exploratory 95% intervals');fig.tight_layout()
for ext in ['svg','png']:fig.savefig(P/f'paired-ratios.{ext}',dpi=180)
plt.close(fig)
(P/'flow.dot').write_text('''digraph G {rankdir=TB; node[shape=box,style="rounded,filled",fillcolor="#edf4f4",fontname="Helvetica"];
 input[label="Frozen curve / base / target"];
 cache[label="Prepare bounded prefix inverses\\nCharge construction + cleanup"];
 pairs[label="Ordered pair sums: denominator lookup\\nExact fallback / exceptional addition"];
 map[label="Abscissa x+1 key, first witness retained"];
 query[label="Query + actual signed group-sum check"];
 finish[label="Relations, matrix and scalar verification"];
 input->cache->pairs->map->query->finish;}
''')
for ext in ['svg','png']:subprocess.run(['dot','-T'+ext,str(P/'flow.dot'),'-o',str(P/f'flow.{ext}')],check=True)
for f in P.glob('*.svg'):f.write_text('\n'.join(l.rstrip() for l in f.read_text().splitlines())+'\n')
lines=['# Prefix inverse reuse: fixed-input comparison, 2026-11-16','',f'{tag} All 48 frozen quadruples completed. Existing independent Python arithmetic replays 192 IC and 96 rho answers. Common positive calibration, whole-native-setup pricing and query/matrix counts agree across all four arms. All 48 A/A checks pass; zero process caps. These are unsigned producer checks.','', '| Curve | Method | Median cold ms | Original/candidate median paired ratio |','|---|---|---:|---:|']
data=[['Curve','Method','Cold ms','Paired ratio']]
for i,n in enumerate([15,18]):
 for m,label in zip(M,L):
  rows=[r for r in R if r['index']==i];cold=statistics.median(r[m]['cold_wall_s'] for r in rows)*1e3;ratio=1 if m==M[0] else case(i,m)['raw_cold_median_ratio']
  lines.append(f'| N{n} | {label} | {cold:.6f} | {ratio:.6f} |');data.append([f'N{n}',label,f'{cold:.6f}',f'{ratio:.6f}'])
summary=[]
for i,n in enumerate([15,18]):
 c=case(i,'mitm-prefix');lo,hi=c['raw_cold_paired_median_bootstrap95'];rows=[r for r in R if r['index']==i];inc=statistics.median(r['mitm-xonly']['cold_wall_s']/r['mitm-prefix']['cold_wall_s'] for r in rows)
 summary.append(f'{tag} N{n} original/prefix paired median {c["raw_cold_median_ratio"]:.6f}, frozen exploratory 95% interval [{lo:.6f},{hi:.6f}]. Secondary paired x-only/prefix median {inc:.6f} compares the cache with the strongest prior N18 implementation; it is distinct from the cumulative comparison with original code.')
lines+=['',*summary,'',f'{tag} N15 does not establish a raw gain because its interval includes 1. N18 has a raw gain in this frozen panel. All values remain unqualified; these intervals do not establish Tier1 admission, portability or a broader breakthrough. Ratios are paired before taking medians, so they differ from ratios of independent medians.','', '![Cold intervals](cold-costs.svg)','', '![Paired ratios](paired-ratios.svg)','',f'{tag} Whole native table preparation is charged once for every arm, including cache allocation, construction and cleanup; observed group additions remain diagnostics. The remaining phase model prices declared group/lookup/matrix primitives and is not an instruction-count measurement. N18 original/prefix context-inclusive phase-priced ratio is 1.386676. Earlier zero-lookup and asymmetric-setup model results remain limited as documented; none is repriced.','',f'{tag} Requested allocation: one L4, 4 CPUs, 8 GiB, 900 seconds; CPU execution only, one pinned exposed CPU, 780s controller, 12s per process. Apparent v1 quota is 20 CPUs and memory limit approximately 340 GiB, which do not verify the requested envelope. Throttle/OOM counters remain unavailable. CPU reported model is unknown; family/model and flags are archived. Physical memory technology/speed/channels are unknown. GNU-time child RSS/CPU/fault receipts are retained; no physical-isolation or Tier1 claim.','',f'{tag} Cold interval is fresh context plus first full pipeline, including base/table setup, failed/successful queries, matrix and final verification. Input materialization, model calibration/loading, process startup and existing-Python replay are separate. Negation rho executes after plain rho in each reference process, so its contextual wall is not a first-solve cold-rho comparison. The next scaling protocol separates the two rho processes.','', '![Mechanism](flow.svg)','',f'{tag} Exact instances and archived bases are fixed N15 dimension 6 and N18 dimension 7. Source 9583f67c93f00be9e79094672a0306089d5feb61, default release, locked-j2, binary c42bab53f55591ea09a308487691968ee7996851aec06f7f797718909eef6ccd. Native preparation passes 883170 complete-domain cached witness checks. Local cache/edge/field checks cover 2649510 full/batch/x-only/cached target comparisons.','', 'Evidence: analysis.json, independent-arithmetic-timing001.json and raw-timing-001.tar.gz. The lossless raw bundle includes all 347 output files and a per-file SHA/URI manifest; split outputs are also stored individually. Result claim PCC-20261116-14ebfc; source 6f5dd0; pricing correction 9ceda4. Ledger histories are preserved. The broad objective remains open.']
(P/'REPORT.md').write_text('\n'.join(lines)+'\n')
styles=getSampleStyleSheet();styles['BodyText'].fontSize=9.4;styles['BodyText'].leading=12.5
para=lambda text:Paragraph(text.replace('&','&amp;').replace('<','&lt;'),styles['BodyText'])
tab=Table(data,colWidths=[48,124,105,105]);tab.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#deecec')),('GRID',(0,0),(-1,-1),.3,colors.grey),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
story=[Paragraph('Prefix inverse reuse: fixed-input comparison',styles['Title']),para('2026-11-16 — raw, unqualified CPU measurements'),Spacer(1,12),para(lines[2]),Spacer(1,12),tab,Spacer(1,12)]
for s in summary:story += [para(s),Spacer(1,10)]
story += [para('The N15 interval includes 1. All cases, controls and resource limits remain visible; no qualification or broad performance claim follows.'),PageBreak(),Paragraph('All targets and paired intervals',styles['Title']),Image(str(P/'cold-costs.png'),width=480,height=166),Spacer(1,18),Image(str(P/'paired-ratios.png'),width=480,height=157),PageBreak(),Paragraph('Accounting, resources and mechanism',styles['Title'])]
for line in lines:
 if line.startswith(tag) and any(x in line for x in ['Whole native','Requested allocation','Cold interval','Exact instances']):story += [para(line),Spacer(1,8)]
story += [Image(str(P/'flow.png'),width=430,height=185,kind='proportional'),Spacer(1,9),para(lines[-1])]
SimpleDocTemplate(str(P/'REPORT.pdf'),leftMargin=48,rightMargin=48,topMargin=40,bottomMargin=40).build(story)
