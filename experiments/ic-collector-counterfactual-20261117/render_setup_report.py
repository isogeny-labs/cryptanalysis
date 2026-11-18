#!/usr/bin/env python3
"""Render all preregistered effects without assuming an improvement direction."""
import argparse,json,statistics
from pathlib import Path
from xml.sax.saxutils import escape
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,Image,PageBreak
from setup_fresh_common import MODES,CONTRASTS
P=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--claim',required=True);args=ap.parse_args();assert args.claim.startswith('PCC-')
def read(name):
 p=P/name;return json.loads(p.read_text()) if p.exists() else {}
a=read('analysis-setup-fresh.json');ar=read('independent-arithmetic-setup-fresh.json');st=read('independent-states-setup-fresh.json');binding=read('setup-fresh-snapshot-binding.json');rb=read('readback-timing-setup-001.json');status=read('setup-fresh-runner-status.json');meta=read('setup-fresh-native-job-metadata.json');host=read('timing-setup-001/host.json');summary=read('timing-setup-001/summary.json')
assert a and summary
cases=a.get('cases',[]);rows=a.get('rows',[]);bad=a.get('aa_failed_rows',[])
complete=a.get('status')=='pass'
if complete:
 assert len(rows)==200 and all(c['valid']==40 for c in cases)
 assert ar.get('checks')==2400 and st.get('checks')==10240 and binding.get('status')=='pass' and rb.get('status')=='pass'
LABELS=dict(zip([x[0] for x in CONTRASTS],['S / I','I / O','O / R','R / G','FI / I','FI / R','FI / G','A / I','C / I']))
SHORT=dict(zip(MODES,['A','C','FI','S','I','O','R','G']))
WINDOWS=[('through_cleanup_contrasts','setup-primary','Primary: context + pipeline through oracle cleanup'),('contrasts','setup-collector','Collector through owned cleanup'),('table_setup_contrasts','setup-table','Pair-table setup, included in primary')]
plt.rcParams.update({'font.size':8,'svg.fonttype':'none','svg.hashsalt':'collector-buffer-20261117','axes.spines.top':False,'axes.spines.right':False})
for window,name,title in WINDOWS:
 fig,axes=plt.subplots(3,3,figsize=(7.2,4.6))
 for ax,(key,_,_) in zip(axes.flat,CONTRASTS):
  selected=[c for c in cases if key in c.get(window,{})]
  for c in selected:
   v=c[window][key];ax.vlines(c['n'],*v['bootstrap95'],color='#235f79');ax.scatter(c['n'],v['median'],s=15,color='#235f79',zorder=3)
  ax.axhline(1,color='#996b2f',linestyle='--',linewidth=.7);ax.set_title(LABELS[key],fontsize=9);ax.set_xticks([15,18,21,24,27]);ax.tick_params(labelsize=7);ax.grid(axis='y',alpha=.15)
  if not selected:ax.text(.5,.5,'Incomplete',transform=ax.transAxes,ha='center')
 fig.suptitle(title,fontsize=11);fig.tight_layout()
 for ext in ['png','svg']:fig.savefig(P/(name+'.'+ext),dpi=180,metadata={'Date':None} if ext=='svg' else None)
 plt.close(fig)
fig,ax=plt.subplots(figsize=(7.2,2.5))
for c in cases:
 selected=[r for r in rows if r['index']==c['index'] and r.get('aa_ratio') is not None]
 ax.scatter([r['fixture'] for r in selected],[r['aa_ratio'] for r in selected],label='N'+str(c['n']),s=14,alpha=.65)
if bad:ax.scatter([r['fixture'] for r in bad],[r['ratio'] for r in bad],marker='x',s=29,color='#ac3131',label='Failed control')
for y in [.85,1.15]:ax.axhline(y,color='#996b2f',linestyle='--',linewidth=.8)
ax.set_xlabel('Fixture');ax.set_ylabel('Ordinary indexed pre / post collector time');ax.set_title('All attempted A/A rows; failures retained');ax.legend(ncol=3,fontsize=7);fig.tight_layout()
for ext in ['png','svg']:fig.savefig(P/('setup-aa.'+ext),dpi=180,metadata={'Date':None} if ext=='svg' else None)
plt.close(fig)
styles=getSampleStyleSheet();styles.add(ParagraphStyle(name='BodySmall',fontName='Helvetica',fontSize=9,leading=12,spaceAfter=5));styles.add(ParagraphStyle(name='CellSmall',fontName='Helvetica',fontSize=7.1,leading=9));styles.add(ParagraphStyle(name='NoteSmall',fontName='Helvetica',fontSize=7.5,leading=10))
story=[];md=[]
def para(text,style='BodySmall'):
 if '[pcc:' not in text:text+=' [pcc:unverified]'
 story.extend([Paragraph(escape(text),styles[style]),Spacer(1,4)]);md.extend([text,''])
def page(title):
 if story:story.append(PageBreak())
 story.extend([Paragraph(escape(title),styles['Heading1']),Spacer(1,7)]);md.extend(['# '+title,''])
def table(data,widths=None):
 widths=widths or [520/len(data[0])]*len(data[0]);cells=[[Paragraph(escape(str(x)).replace(' /CI/ ','<br/>'),styles['CellSmall']) for x in row] for row in data];t=Table(cells,colWidths=widths,repeatRows=1,hAlign='LEFT')
 t.setStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e6edf1')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),4),('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3),('LINEBELOW',(0,0),(-1,0),.5,colors.HexColor('#b8c7d0'))]);story.extend([t,Spacer(1,7)])
 md.extend(['| '+' | '.join(map(str,data[0]))+' |','| '+' | '.join('---' for _ in data[0])+' |']);md.extend('| '+' | '.join(str(x).replace(' /CI/ ',' ') for x in row)+' |' for row in data[1:]);md.append('')
def image(name,height):story.extend([Image(str(P/(name+'.png')),width=520,height=height),Spacer(1,5)]);md.extend(['!['+name+']('+name+'.svg)',''])
def ratio(c,window,key):
 v=c.get(window,{}).get(key)
 return 'Unavailable' if not v else f"{v['median']:.5f} /CI/ [{v['bootstrap95'][0]:.5f}, {v['bootstrap95'][1]:.5f}]"
def equivalence(c,key):
 v=c.get('contrasts',{}).get(key)
 return bool(v and v['bootstrap95'][0]>=.99 and v['bootstrap95'][1]<=1.01)
page('Collector buffer-state comparison')
para('Measured outcome: neither reservation nor gather improves the primary interval against the frozen indexed path with a pointwise interval entirely above 1 on any field. Gather reduces N24 collector time by about 3.5%, but increases charged primary time by about 6.7%. The buffer-state remedies therefore do not establish a useful performance improvement; the earlier regression mechanism remains unresolved.')
para('Standing: unsigned exploratory producer evidence, '+args.claim+'. Qualification remains null; this report does not promote a baseline or establish a physical allocator/cache mechanism. All failed A/A rows, caps and incomplete outcomes are retained.')
para(f"Analysis status: {a.get('status')}; controller status: {summary.get('status')}. Observed blocks: {len(rows)} of200. Independent replay: {ar.get('pipeline_answers','unavailable')}IC, {ar.get('rho_answers','unavailable')}rho and {ar.get('aa_answers','unavailable')}A/A answers; {st.get('checks','unavailable')}walk states. Failed A/A controls: {len(bad)}. Capped IC arms: {a.get('capped_arms','unavailable')}.")
para('Post-launch disclosure: I/O also changes explicit-default input-key presence, so it is not an isolated opaque-barrier effect. O/R and R/G input key sets match. The source-control limitation is preserved in SCIENTIFIC_ADDENDUM_001.md; no frozen row, estimator or source was changed. Corrected disclosure claim PCC-20261118-4f626b remains unsigned.')
para('A=frozen anchor ordinary; C=frozen compact inverse; FI=frozen indexed inverse. S=new staged inverse; I=new indexed inverse; O=observed empty buffers; R=observed reserved buffers; G=observed gathered buffers. The five new configurations share one admitted binary and inverse-vector query implementation. The indexed counter is present throughout; O/R/G share the opaque observation.')
table([['Field','Blocks','Failed A/A','FI / R primary','FI / G primary']]+[['N'+str(c['n']),c['attempted'],c['aa_failures'],ratio(c,'through_cleanup_contrasts','reserved_vs_frozen'),ratio(c,'through_cleanup_contrasts','gathered_vs_frozen')] for c in cases],[40,45,55,190,190])
para('Ratios are reference/candidate time; above1favors the denominator. Collector restoration alone is insufficient: a candidate must lower charged primary against the frozen indexed path on separately fresh points. Pointwise intervals are exploratory, without familywise coverage. No full-process-cold or GPU-throughput result follows.')
if a.get('errors'):para('Retained analysis errors: '+repr(a['errors']))
for window,name,title in WINDOWS:
 page(title);image(name,332)
 table([['Effect',*['N'+str(c['n']) for c in cases]]]+[[LABELS[key],*[ratio(c,window,key) for c in cases]] for key,_,_ in CONTRASTS],[70]+[90]*len(cases))
 para('All9predeclared effects. Paired medians and pointwise95% bootstrap intervals,10000resamples, seed20261116, linear quantiles. All40rows per field remain when complete; no filtering, pooling, replacement host or cross-panel products. Incomplete estimates are unavailable.','NoteSmall')
page('Transfer checks and causal limits')
table([['Field','FI / I collector','Inside1%band','I / O collector','Inside1%band']]+[['N'+str(c['n']),ratio(c,'contrasts','rebuilt_indexed'),str(equivalence(c,'rebuilt_indexed')),ratio(c,'contrasts','opaque_observation'),str(equivalence(c,'opaque_observation'))] for c in cases],[40,180,60,180,60])
para('The protocol requires both collector95% intervals entirely inside0.99..1.01 before attributing a reservation/gather contrast to the earlier regression. An interval containing1does not establish equivalence. If either transfer check fails, retain the new-binary contrasts but historical attribution remains inconclusive.')
para('Additional source limitation, disclosed after launch: I explicitly includes suppress_indexed_counter=0 in oracle_params, whereas O/R/G omit the key and use the same default. This configuration is constructed before primary and may alter allocation history. Therefore I/O is a joint configuration-presence/opaque-observation contrast, not a pure barrier effect. O/R and R/G retain matching parameter key sets. Do not infer a unique physical cause from transfer bands. See SCIENTIFIC_ADDENDUM_001.md.')
para('Reservation is O/R; gather traffic is R/G. These are conditional effects, not a factorial interaction. Even successful transfer only supports the declared setup-state contrast in this build; cache placement, allocator behavior, branch history and physical placement require separate evidence.')
page('Primary means and same-point rho')
table([['Field',*[SHORT[m]+' ms' for m in MODES]]]+[['N'+str(c['n']),*[f"{1000*c['methods'][m]['mean_context_plus_computation_s']:.4f}" if 'methods' in c else 'Unavailable' for m in MODES]] for c in cases],[38]+[482/8]*8)
para('Arithmetic means in milliseconds are distinct from the paired median-ratio effects. Primary includes context plus factor-base/table/collector/matrix/scalar verification through owned oracle cleanup. Prior fixture/calibration/spec/empty allocation, startup/JSON and later context/report destruction remain excluded.')
def ref(c,m,kind):
 v=c.get('methods',{}).get(m,{}).get('median_context_rho_over_pipeline',{}).get(kind)
 return 'Unavailable' if v is None else f'{v:.5f}'
table([['Field','Negation rho / I','Negation rho / R','Negation rho / G']]+[['N'+str(c['n']),*[ref(c,m,'rho-negation') for m in [MODES[4],MODES[6],MODES[7]]]] for c in cases],[40,160,160,160])
para('These are paired context-plus-rho / primary ratios on identical Q/G/r/seed. Below1favors rho. Plain and negation references remain separately available in the raw analysis. A comparison with A includes older cumulative optimizations and does not isolate a gain from reservation or gather changes. RSS is complete-child GNUTime peak, not an allocation or causal measurement.')
def rss(c,m):
 selected=[r for r in rows if r['index']==c['index']]
 values=[r.get('methods',{}).get(m,{}).get('peak_rss_kib') for r in selected]
 return f"{statistics.mean(values)/1024:.3f}" if values and all(v is not None for v in values) else 'Unavailable'
table([['Field','FI mean RSS MiB','I mean RSS MiB','R mean RSS MiB','G mean RSS MiB']]+[['N'+str(c['n']),*[rss(c,m) for m in [MODES[2],MODES[4],MODES[6],MODES[7]]]] for c in cases],[40,120,120,120,120])
para('RSS means include all attempted rows only when each child measurement is present; unavailable is not zero. These values include child startup/reporting and do not identify the collector mechanism.')
page('Every failed A/A control retained');image('setup-aa',181)
table([['Field','Attempted','Failed']]+[['N'+str(c['n']),c['attempted'],c['aa_failures']] for c in cases],[70,225,225])
if bad:table([['Field index','Fixture','Pre / post ratio']]+[[r['index'],r['fixture'],f"{r['ratio']:.8f}"] for r in bad],[80,100,340])
else:para('No failed A/A rows were recorded; qualification still remains null and unsigned.')
para('A/A uses ordinary indexed fixture0 in the new binary before/after each block, acceptance band0.85..1.15. Every failed row remains in all estimates; a field with zero failures does not qualify the full panel or establish a physical cause.')
page('Identity, source and raw custody')
para('Timing job '+str(meta.get('job','unavailable'))+'; clean controller/input source '+str(meta.get('git',{}).get('commit','unavailable'))+'. All40candidate IDs and200workload IDs were published before timing; the contemporary separately rebuilt ARM probe generated identities only. Native binary/source hashes remain in setup-frozen-inputs.json and the original preparation receipts.')
table([['Binding','Value']]+[[k,str(binding.get(k,'Unavailable'))] for k in ['snapshot_sha256','runner_status_sha256','metadata_sha256','published_identities_revision','generation_receipt_sha256']],[125,395])
para('The existing benchmark record was initialized2026-11-17T18:09:05UTC before this run. Native source/hardware/timestamps come from the original runner receipt; the original coordinator capture and record creation time remain retained. No backdating or replacement record is used.')
para('Working-store raw bundle readback: '+repr(rb.get('rows',[]))+'. Exact per-member byte/hash checks and per-file S3 addresses are retained. Current CI artifact-pull403 failures are separately diagnosed; local custody does not establish CI credential access or a signed verdict.')
page('Protocol and remaining work')
para(f"One approved L4/4CPU/8GiB/900second allocation; actual runner seconds={status.get('seconds','unavailable')}, exit={status.get('returncode','unavailable')}. CPU arithmetic only, pinned to one exposed allowed CPU. No observer subprocess or profiling ran on the timing worker. Physical placement, memory technology/speed/channels and qualified isolation remain unknown.")
para('Fixtures768..807 per field; eight Williams rows repeated5times, each method position and directed adjacency5times. Rotated field order gives8appearances per field position. Matched plain/negation rho uses fresh compact-control processes and the exact same public targets/seeds. Controller780seconds, child12seconds, preflight30seconds,8GiB native virtual-memory cap.')
para('The record inventory is180metrics and25raw references for a complete panel. Keep all failures and caps, native source/binary bindings, replay outputs and initial infrastructure failures. No signed speedup, baseline promotion, full-cold result or mathematical novelty follows automatically from these producer checks.')
para('Next action is determined from the separately reported primary effects and transfer checks. A retained gain requires independent review and the existing evidence gates; an inconclusive or negative configuration remains a measured outcome rather than a successful remedy. The broader performance objective remains open.')
def footer(canvas,doc):
 canvas.saveState();canvas.setFont('Helvetica',7);canvas.setFillColor(colors.HexColor('#506675'));canvas.drawString(36,22,'Unsigned exploratory evidence | all controls retained | qualification null');canvas.drawRightString(A4[0]-36,22,str(doc.page));canvas.restoreState()
SimpleDocTemplate(str(P/'SETUP_REPORT.pdf'),pagesize=A4,rightMargin=36,leftMargin=36,topMargin=32,bottomMargin=36,title='Collector buffer-state comparison',author='Cryptanalysis research').build(story,onFirstPage=footer,onLaterPages=footer)
(P/'SETUP_REPORT.md').write_text('\n'.join(md).rstrip()+'\n');print('Rendered complete predeclared effects and controls')
