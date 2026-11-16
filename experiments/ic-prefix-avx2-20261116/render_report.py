#!/usr/bin/env python3
"""All fixed arithmetic controls and raw timing limits, without promotion."""
import json,statistics,subprocess
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak
P=Path(__file__).resolve().parent;A=json.loads((P/'analysis.json').read_text());assert A['status']=='fail' and len(A['errors'])==360 and all(e.startswith('vector-path-inactive ') for e in A['errors'])
R=A['rows'];T=json.loads((P/'timing-001/triples.json').read_text());H=json.loads((P/'timing-001/host.json').read_text());V=json.loads((P/'independent-arithmetic-timing001.json').read_text());B=json.loads((P/'prepared-input.json').read_text())
N=[15,18,21,24,27];M=['mitm-prefix','mitm-vector64','mitm-vector','mitm-vector4096'];L=['Prefix','Fallback\n64','Fallback\n1024','Fallback\n4096'];C=['#647b86','#ac9059','#267e78','#5c6d9b'];tag='[pcc:unverified]'
case=lambda i,m:next(c for c in A['cases'] if c['index']==i and c['method']==m)
failed=[dict(field=N[x['index']],fixture=x['fixture'],ratio=x.get('calibration_ratio')) for x in T if not x.get('calibration_within_bound')]
for kind in ['cold','ratios']:
 fig,axes=plt.subplots(2,3,figsize=(11,6.2));axes=axes.flatten()
 for i,n in enumerate(N):
  ax=axes[i];rows=[r for r in R if r['index']==i]
  for j,m in enumerate(M if kind=='cold' else M[1:]):
   vals=[r[m]['cold_wall_s']*1e3 if kind=='cold' else r['raw_cold_ratios'][m] for r in rows]
   ax.scatter([j+(k-11.5)*.012 for k in range(24)],vals,s=10,color=C[M.index(m)],alpha=.75);med=statistics.median(vals)
   if kind=='cold':ax.plot([j-.22,j+.22],[med]*2,color='#222')
   else:
    lo,hi=case(i,m)['raw_cold_paired_median_bootstrap95'];ax.errorbar(j,med,yerr=[[med-lo],[hi-med]],fmt='o',color='#222',capsize=4)
  ax.set_xticks(range(4 if kind=='cold' else 3),L if kind=='cold' else L[1:],fontsize=8)
  ax.set_title(f'N{n}'+(' — failed A/A retained' if any(f['field']==n for f in failed) else ''));ax.set_ylabel('Complete cold ms' if kind=='cold' else 'Prefix / candidate');ax.grid(axis='y',alpha=.2)
  if kind=='ratios':ax.axhline(1,color='#888',linestyle=':')
 axes[-1].axis('off');axes[-1].text(.05,.8,f'All 24 targets per field\nAll 24 IC mode orders\nOriginal-arithmetic rho references\n{len(failed)} failed A/A controls retained\nRaw, unqualified CPU data',va='top',fontsize=11)
 fig.tight_layout()
 for ext in ['svg','png']:fig.savefig(P/f'{kind}.{ext}',dpi=180)
 plt.close(fig)
(P/'flow.dot').write_text('''digraph G {rankdir=LR;node[shape=box,style="rounded,filled",fillcolor="#e7f2f0",fontname="Helvetica"];a[label="Frozen curve / base / target"];b[label="Prefix inverse cache"];c[label="Feature guard: VPCLMUL absent\\nChunks64 /1024 /4096"];d[label="Scalar fallback witness table"];e[label="Same queries, matrix, scalar check"];a->b->c->d->e;}''')
for ext in ['png','svg']:subprocess.run(['dot','-T'+ext,str(P/'flow.dot'),'-o',str(P/f'flow.{ext}')],check=True)
for p in P.glob('*.svg'):p.write_text('\n'.join(l.rstrip() for l in p.read_text().splitlines())+'\n')
intro=f'{tag} CAPABILITY ADMISSION FAILED: the timing host lacks VPCLMULQDQ; all 360 requested vector arms used the exact scalar fallback. This is not a SIMD performance measurement. All 120 frozen four-way comparisons completed. Existing independent Python arithmetic replays {V["pipeline_answers"]} IC answers and {V["rho_answers"]} fresh-process rho answers. Exact input/candidate manifests, scalar fallback routing, positive shared calibration, scalar answers and query/matrix counts pass unsigned producer checks.'
data=[['Field','Prefix ms','Fallback64 ratio','Fallback1024 ratio','Fallback4096 ratio']];md=['| Field | Prefix median ms | Fallback64 paired ratio | Fallback1024 paired ratio | Fallback4096 paired ratio |','|---|---:|---:|---:|---:|']
intervals=[]
for i,n in enumerate(N):
 rows=[r for r in R if r['index']==i];vals=[f'N{n}',f"{statistics.median(r[M[0]]['cold_wall_s'] for r in rows)*1e3:.6f}",*[f"{case(i,m)['raw_cold_median_ratio']:.6f}" for m in M[1:]]];data.append(vals);md.append('| '+' | '.join(vals)+' |');lo,hi=case(i,M[-1])['raw_cold_paired_median_bootstrap95'];intervals.append(f'{tag} N{n} prefix/fallback4096 diagnostic paired median {case(i,M[-1])["raw_cold_median_ratio"]:.6f}; frozen exploratory 95% bootstrap interval [{lo:.6f}, {hi:.6f}].')
controls=f'{tag} {120-len(failed)} of 120 pre/post A/A controls pass the frozen 0.85–1.15 bound with correct answers and unchanged calibration. Failed controls: {json.dumps(failed)}. No rows, outliers or controls are removed; zero process caps. Ratios are paired before taking medians. These ratios describe fallback paths only. Every comparison is unqualified; no SIMD timing result is admitted.'
find=lambda ending:next((v for k,v in H['initial'].items() if k.endswith(ending)),None)
quota,period,mem=find('cpu.cfs_quota_us'),find('cpu.cfs_period_us'),find('memory.limit_in_bytes')
resources=f'{tag} Requested one L4, 4 CPUs, 8 GiB, 900 seconds; CPU execution only, one pinned exposed CPU, controller 780 seconds, child cap 12 seconds. Exposed cgroup CPU quota/period: {str(quota).strip()}/{str(period).strip()}; memory limit: {str(mem).strip()} bytes. Requested allocation and physical placement remain unqualified; unavailable throttle/OOM counters and physical memory technology/speed/channels remain unknown. Child RLIMIT_AS is 8 GiB; GNU-time RSS/CPU/fault receipts retained. Record invalid for promotion.'
account=f'{tag} Every IC arm uses the same prefix-cached table strategy. Cold wall includes context, base/table/cache construction and cleanup, all queries, matrix work and final scalar verification. Public materialization, calibration/unit loading, process startup and independent replay remain separate. Original shared positive units are reused across all four requested preparation modes; no candidate-specific repricing. The remaining phase model is primitive pricing, not instruction counts; unchanged operation counts do not price a faster arithmetic implementation by themselves.'
rho=f'{tag} Plain and negation rho use original arithmetic in separate fresh processes on the identical point and seed. Their order and placement alternate by fixture parity. No field-inverse or matrix change is combined with this comparison. Wall gaps below are median per-target IC/matched-negation-rho ratios.'
gaps=[['Field','Prefix / matched rho','Fallback4096 / matched rho']]
for i,n in enumerate(N):
 c=case(i,M[-1]);gaps.append([f'N{n}',f"{c[M[0]+'_median_cold_wall_gap_to_matched_rho']:.4f}",f"{c[M[-1]+'_median_cold_wall_gap_to_matched_rho']:.4f}"])
source=f'{tag} Static disassembly contains YMM VPCLMUL instructions, which the timing host correctly skips. Exact source {B["source_commit"]}; default release, locked-j2; binary {B["binary_sha256"]}. Native preparation checks 100 complete first-witness maps and 15 unit-loader controls; vector product tests exercise {B["native_vector_field_widths"]} accepted field widths. The separate preparation host exercised vector instructions, but timing vector_pairs is zero in every requested vector arm; the frozen admission gate fails. Runtime AVX2/VPCLMUL and sparse-tail guards preserve complete scalar fallback on unsupported CPUs/fields and exceptional/missing-cache pairs. The original inverse, matrix and defaults remain.'
scope=f'{tag} These are engineering measurements on fixed registered N15/18/21/24/27 curves, with 29/67/127/257/531 sign columns. They do not establish cryptographic-size performance, GPU throughput, asymptotic novelty, Tier1 admission or completion of the broad goal. Known unsigned status and ledger custody fork remain unchanged. Earlier negative/noisy results and model limitations are preserved.'
evidence='Evidence: analysis.json, independent-arithmetic-timing001.json and lossless raw-timing-001.tar.gz with per-file SHA/URI inventory. Split raw outputs are also archived individually. Source claim c3b75f is unsigned. Native claim 4e89f7 and failed-admission claim 28dc44 are unsigned statements; all receipts remain alongside this report.'
lines=['# AVX2 cached pair preparation: 2026-11-16','',intro,'',*md,'',*intervals,'',controls,'','![Cold](cold.svg)','','![Ratios](ratios.svg)','',resources,'',account,'',rho,'','| Field | Prefix/matched rho | Fallback4096/matched rho |','|---|---:|---:|',*['| '+' | '.join(x)+' |' for x in gaps[1:]],'',source,'',scope,'',evidence,'','![Mechanism](flow.svg)']
(P/'REPORT.md').write_text('\n'.join(lines)+'\n')
styles=getSampleStyleSheet();styles['BodyText'].fontSize=9.1;styles['BodyText'].leading=11.8
para=lambda s:Paragraph(s.replace('&','&amp;').replace('<','&lt;'),styles['BodyText'])
def tab(data,widths):
 t=Table(data,colWidths=widths);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dfeded')),('GRID',(0,0),(-1,-1),.3,colors.grey),('FONTSIZE',(0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,-1),6)]));return t
story=[Paragraph('Requested AVX2: scalar fallback receipt',styles['Title']),para('2026-11-16 — prefix baseline; raw, unqualified CPU measurements'),Spacer(1,10),para(intro),Spacer(1,12),tab(data,[43,100,100,100,100]),Spacer(1,12)]
for x in intervals:story += [para(x),Spacer(1,7)]
story += [para(controls),PageBreak(),Paragraph('Every fixed target and paired interval',styles['Title']),Image(str(P/'cold.png'),width=493,height=278),Spacer(1,10),Image(str(P/'ratios.png'),width=493,height=278),PageBreak(),Paragraph('Accounting, resources and rho references',styles['Title'])]
for x in [resources,account,rho]:story += [para(x),Spacer(1,8)]
story += [tab(gaps,[43,190,190]),Spacer(1,10)]
for x in [source,scope,evidence]:story += [para(x),Spacer(1,8)]
story += [Image(str(P/'flow.png'),width=493,height=55,kind='proportional')]
SimpleDocTemplate(str(P/'REPORT.pdf'),leftMargin=42,rightMargin=42,topMargin=36,bottomMargin=36).build(story)
