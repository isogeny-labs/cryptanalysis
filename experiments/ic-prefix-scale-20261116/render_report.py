#!/usr/bin/env python3
"""Render the entire frozen scaling panel, including failed controls."""
import json,statistics,subprocess
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak
P=Path(__file__).resolve().parent;A=json.loads((P/'analysis.json').read_text());assert A['status']=='pass'
R=A['rows'];T=json.loads((P/'timing-001/triples.json').read_text());H=json.loads((P/'timing-001/host.json').read_text());replay=json.loads((P/'independent-arithmetic-timing001.json').read_text())
N=[15,18,21,24,27];M=['mitm-native','mitm-scalar','mitm-prefix','mitm-auto'];L=['Original','Scalar','Prefix','Adaptive'];C=['#657a86','#b8965b','#287b78','#5771a3'];tag='[pcc:unverified]'
case=lambda i,m:next(c for c in A['cases'] if c['index']==i and c['method']==m)
for kind in ['cold','ratios']:
 fig,axes=plt.subplots(2,3,figsize=(11,6.2));axes=axes.flatten()
 for i,n in enumerate(N):
  ax=axes[i];rows=[r for r in R if r['index']==i]
  for j,m in enumerate(M if kind=='cold' else M[1:]):
   vals=[r[m]['cold_wall_s']*1e3 if kind=='cold' else r['raw_cold_ratios'][m] for r in rows]
   color=C[M.index(m)];ax.scatter([j+(k-11.5)*.012 for k in range(24)],vals,s=10,color=color,alpha=.75)
   med=statistics.median(vals)
   if kind=='cold':ax.plot([j-.22,j+.22],[med]*2,color='#222')
   else:
    lo,hi=case(i,m)['raw_cold_paired_median_bootstrap95'];ax.errorbar(j,med,yerr=[[med-lo],[hi-med]],fmt='o',color='#222',capsize=4)
  ax.set_xticks(range(4 if kind=='cold' else 3),L if kind=='cold' else L[1:],fontsize=8)
  ax.set_title(f'N{n}'+(' — one failed A/A' if n==24 else ''));ax.set_ylabel('Cold wall (ms)' if kind=='cold' else 'Original / candidate');ax.grid(axis='y',alpha=.2)
  if kind=='ratios':ax.axhline(1,color='#888',linestyle=':')
 axes[-1].axis('off');axes[-1].text(.05,.8,'All 24 targets per field\nAll 24 mode orders\nRaw, unqualified container data\nN24 failed A/A retained\nNo replacement or trimming',va='top',fontsize=11)
 fig.tight_layout()
 for ext in ['png','svg']:fig.savefig(P/f'{kind}.{ext}',dpi=180)
 plt.close(fig)
(P/'flow.dot').write_text('''digraph G {rankdir=LR;node[shape=box,style="rounded,filled",fillcolor="#e8f2f1",fontname="Helvetica"];a[label="Frozen curve, base, target"];b[label="Native preparation\\nOriginal / scalar / prefix / adaptive"];c[label="Same relation and matrix work"];d[label="Final scalar check\\nExisting Python replay"];a->b->c->d;}''')
for ext in ['png','svg']:subprocess.run(['dot','-T'+ext,str(P/'flow.dot'),'-o',str(P/f'flow.{ext}')],check=True)
for p in P.glob('*.svg'):p.write_text('\n'.join(l.rstrip() for l in p.read_text().splitlines())+'\n')
intro=f'{tag} All 120 frozen four-way comparisons completed, with zero process caps. Existing independent Python arithmetic replays {replay["pipeline_answers"]} IC answers and {replay["rho_answers"]} fresh-process rho answers. Shared positive units, exact candidate/input manifests, scalar verification, and query/matrix counts agree. These remain unsigned producer checks.'
data=[['Field','Original ms','Scalar ratio','Prefix ratio','Adaptive ratio']];md=['| Field | Original median ms | Scalar paired ratio | Prefix paired ratio | Adaptive paired ratio |','|---|---:|---:|---:|---:|']
intervals=[]
for i,n in enumerate(N):
 rows=[r for r in R if r['index']==i];vals=[f'N{n}',f"{statistics.median(r['mitm-native']['cold_wall_s'] for r in rows)*1e3:.6f}",*[f"{case(i,m)['raw_cold_median_ratio']:.6f}" for m in M[1:]]];data.append(vals);md.append('| '+' | '.join(vals)+' |')
 lo,hi=case(i,'mitm-prefix')['raw_cold_paired_median_bootstrap95'];intervals.append(f'{tag} N{n} prefix paired median {case(i,"mitm-prefix")["raw_cold_median_ratio"]:.6f}; frozen exploratory 95% bootstrap interval [{lo:.6f}, {hi:.6f}].'+(' One failed A/A (fixture 219, pre/post ratio 0.687076) remains in all raw summaries.' if n==24 else ''))
controls=f'{tag} 119 of 120 pre/post A/A checks satisfy the frozen 0.85–1.15 interval with correct calibration answers; N24 fixture 219 fails. No failed control or outlier is removed, and no target is replaced. Raw medians are exploratory diagnostics, with qualified values null. Ratios are paired before taking medians. Scalar-only dispatch gives little benefit across the panel; it does not support the earlier dispatch hypothesis. The adaptive selector does not consistently improve on prefix alone.'
resources=f'{tag} One L4 allocation requested 4 CPUs, 8 GiB and 900 seconds; CPU execution only, one pinned exposed CPU, controller 780 seconds and child cap 12 seconds. Exposed quota is 20 CPUs and cgroup memory limit 181842173952 bytes (about 169.35 GiB). Requested limits and physical isolation are unverified; throttle/OOM and memory technology/speed/channels remain unavailable. Each child inherits RLIMIT_AS 8 GiB and GNU-time RSS/CPU/fault receipts. Record invalid for promotion.'
account=f'{tag} Cold wall includes fresh instance context, factor-base construction, complete native table/cache setup and cleanup, all failed/successful queries, matrix work and final scalar verification. Process startup, public materialization, unit calibration/loading and independent replay remain separate. Whole native preparation is charged once for every arm; the remaining phase model is primitive pricing, not instruction counts. Plain and negation rho execute in separate fresh processes on the identical point and seed. Even the optimized IC cold walls remain above those matched rho references on this panel.'
source=f'{tag} Exact registered fields N15/18/21/24/27 use archived prefix dimensions 6/7/8/9/10 and 29/67/127/257/531 sign columns. Source 42380ff2e83a1bd7bbdbed5c270365733295e726; default release, locked-j2; binary 7e54b6bc8304aa4570a7d551ce3f521bf184f5b4410a6ce5c98d2cb0b0f7f9a2. Native preparation passes 45 complete first-witness-map comparisons and 15 unit-loader checks. The original receipt contains the literal label HEAD; clean launcher metadata and exact source hashes separately bind the resolved commit. No receipt is rewritten.'
scope=tag+' These measurements extend registered field sizes, with every case retained. They do not establish cryptographic-size performance, GPU throughput, asymptotic improvement, Tier1 admission or the broad requested breakthrough. The separate reciprocal matrix implementation is unmeasured and is absent from this frozen binary. Existing ledger custody fork and unsigned status remain unchanged.'
evidence='Evidence: analysis.json, independent-arithmetic-timing001.json, raw-timing-001.tar.gz and raw-bundle-receipt.json bind all 977 raw outputs; split raw outputs are archived individually. Earlier negative results and pricing limitations remain preserved.'
lines=['# Registered prefix scaling: 2026-11-16','',intro,'',*md,'',*intervals,'',controls,'','![Cold wall](cold.svg)','','![Paired ratios](ratios.svg)','',resources,'',account,'',source,'',scope,'',evidence,'','![Mechanism](flow.svg)']
(P/'REPORT.md').write_text('\n'.join(lines)+'\n')
styles=getSampleStyleSheet();styles['BodyText'].fontSize=9.2;styles['BodyText'].leading=12
para=lambda s:Paragraph(s.replace('&','&amp;').replace('<','&lt;'),styles['BodyText'])
table=Table(data,colWidths=[43,100,100,100,100]);table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dfeded')),('GRID',(0,0),(-1,-1),.3,colors.grey),('FONTSIZE',(0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
story=[Paragraph('Native IC prefix scaling',styles['Title']),para('2026-11-16 — all fixed targets; raw, unqualified CPU measurements'),Spacer(1,12),para(intro),Spacer(1,12),table,Spacer(1,12)]
for x in intervals:story += [para(x),Spacer(1,7)]
story += [para(controls),PageBreak(),Paragraph('Every target and paired interval',styles['Title']),Image(str(P/'cold.png'),width=493,height=278),Spacer(1,10),Image(str(P/'ratios.png'),width=493,height=278),PageBreak(),Paragraph('Accounting, resources and scope',styles['Title'])]
for x in [resources,account,source,scope,evidence]:story += [para(x),Spacer(1,10)]
story += [Image(str(P/'flow.png'),width=493,height=65,kind='proportional')]
SimpleDocTemplate(str(P/'REPORT.pdf'),leftMargin=42,rightMargin=42,topMargin=38,bottomMargin=38).build(story)
