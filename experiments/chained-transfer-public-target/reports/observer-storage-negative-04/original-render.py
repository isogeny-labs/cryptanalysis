"""Render native partial classifications; no mathematical computation or pricing."""
from pathlib import Path
import hashlib,json,shutil,typst
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';p=s/'reports/observer-storage-negative-04';p.mkdir()
raw=Path('/workspace/scratch/ct80-observer-partial-diagnostic-native-04/actual-partial-vectors.json');v=json.loads(raw.read_text())
data=dict(source=str(raw),bytes=raw.stat().st_size,sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),native_claim='b3a1bc',full_cold_population_accepted=v['full_cold_population_accepted'],completed=[dict(index=x['index'],arm=x['arm']) for x in v['all_actual_complete_cold_records']],missing=v['all_missing_or_incomplete_cold_records'],cold_panel_actual_exit=v['cold_panel_actual_exit'],reuse_processes=v['complete_reused_context_processes'],scope='render-only classification projection; all whole packets/vectors and complete old/new pairs retained in native capture; no population mixing, scalar price or timing inference')
(p/'render-data.json').write_text(json.dumps(data,indent=2)+'\n')
fig,axes=plt.subplots(2,1,figsize=(10.5,2.35),sharex=True)
for ax,arm in zip(axes,['baseline','direct']):
 ax.set_ylim(-.5,.5);ax.set_xlim(-.5,59.5);ax.set_yticks([]);ax.set_ylabel(arm,rotation=0,labelpad=32,va='center',fontsize=10)
 for i in range(60):
  complete=any(x['arm']==arm and x['index']==i for x in data['completed']);entry=next((x for x in data['missing'] if x['arm']==arm and x['index']==i),None)
  color='#46754a' if complete else ('#bb8843' if entry and entry['raw_log_exists'] else '#dddddd')
  ax.add_patch(plt.Rectangle((i-.45,-.4),.9,.8,facecolor=color,edgecolor='white'))
 for spine in ax.spines.values():spine.set_visible(False)
axes[1].set_xticks(range(0,60,5));axes[1].set_xlabel('Frozen case index; one independent process per arm and case',fontsize=9)
fig.text(.5,.98,'Cold panel: actual124, 18 completed / 102 missing or incomplete; full120 requirement FAILS',ha='center',va='top',fontsize=11,weight='bold')
fig.text(.5,.01,'Green: completed and native-validated. Amber: started without success receipt. Gray: not started. Both separate60-case reuse streams complete0.',ha='center',fontsize=8)
fig.tight_layout(rect=[.03,.08,1,.88]);fig.savefig(p/'actual-coverage.svg',bbox_inches='tight');plt.close(fig)
(p/'report.typ').write_text(r'''#set page(paper:"a4",margin:14mm)
#set text(font:"DejaVu Sans",size:9.6pt)
#set par(leading:.45em)
#text(size:17pt,weight:"bold")[Observer storage preserves observations; cold census stays incomplete]
#v(4pt)
#text(fill:rgb("#8b3434"),weight:"bold")[NEGATIVE FULL-CENSUS RESULT · partial observations only · unsigned]

The same frozen120 separate cold processes hit the unchanged900s bound with exit124. Eighteen processes have complete success receipts;102 are missing or incomplete. Both complete60-case reused-context streams finish0 within their original combined900s panel. The unchanged full analyzer and full-population parity checker reject101 without accepted output. No complete cold population, extrapolation or calibrated gain is claimed.

#image("actual-coverage.svg",width:100%,height:54mm,fit:"contain")

== What was independently checked
The preserved original partial Rust analyzer validates all18 complete cold outputs against the frozen fixture, all monotone canonical ledgers and both60-output reuse packets. The separate retrospective diagnostic compares ALL12 previous complete cold packets and BOTH previous whole60-output reuse packets exactly, including every cumulative ledger, without masks or deduplication. Removing an actual whole reuse packet rejects101/no output. Its accepted diagnostic explicitly says full_cold_population_accepted=false.

The original mathematics, field expressions, hooks, labels, units, fixtures, full admission/output/inverse work and original runner remain unchanged. Four unfiltered observer-OFF mathematical tests and allfour whole records, enabled unit collision/overflow/foreign-entry controls, actual FpR/quadratic missing-hook controls and disabled-mode rejection pass. Both original Lean gates and exact statement bindings cover the conditional storage functions; insertion, Vec/u64/TLS and full Rust execution remain bridges.

== Process interruption is a separate result
Earlier03 has17 successful cold receipts and no panel or reuse terminal outcome; the enclosing session later reports an unknown process id. Its cause stays unknown and it is not labeled124. Detached04 survives the deadline and records its actualcold124/reuse0, all source guards0 and terminal worker/supervisor1 for the unmet full criterion. The supervisor-recording gap is resolved for this run; the cold-census resource gap remains open.

== These units do not establish a speedup
The whole historical reuse packets are equal, so the previously reported unpriced source-vector tradeoff remains: more source products and fewer atomic inversions. No arbitrary scalar price, time ratio, machine-instruction count, stage win or ECDLP advantage follows. Cold and reused populations stay separate. These observations concern the earlier original norm-halving transfer and are not applied to the distinct new fixed-twist instance.

== Next work and evidence
Preserve every complete/incomplete/missing case, failed mode/build/launch attempt, actual executable/source closure and original/full/partial analyzer outcome in NEWgenuine19. Any future observer or constructor optimization needs a new prospective protocol retaining the full original criterion. Continue the original DLP-preserving chain and prime-field model research; admitted hardware/isolation/budget and strongest matched references are still required for actual performance claims.

#text(size:8pt)[Sources: original01e617 and storage289a79/build65433a before code; originalb5fd45/471848/ee232d; controls7b7e97, terminalnegativef0f3ae and nativepartialb3a1bc. Exact clean4378 original checkpoint15aa68 precedes diagnostic. Complete raw: ct80-observer-validation-04 and ct80-observer-partial-diagnostic-native-04. render-data.json pins the full native vector file. Original analyzer and full120 acceptance remain unchanged; no paid launch, waiver, novelty or signed execution claim.]
''')
typst.compile(str(p/'report.typ'),output=str(p/'report.pdf'),root=str(p))
(p/'REPORT.md').write_text('''# Observer storage: preserved whole observations, incomplete cold panel

Actualf0f3ae cold124/18complete and both60case reuse0 fails unchanged full120cold acceptance. Nativepartialb3a1bc validates all18 complete outputs/ledgers and102 missing/incomplete, both complete60-output streams and ALL14 prior whole-packet comparisons; actual whole-packet omission101/no output. This is explicitly partial, unpriced and unsigned. [pcc:unverified]

[PDF](report.pdf) · [actual coverage](actual-coverage.svg) · [render-only native projection/hash](render-data.json) · [named resource gap](../../../../problems/chained-transfer-incomplete-cold-arithmetic-census.md). Earlier03 stays interrupted/unknown, not124. [pcc:unverified]

The original norm-arithmetic-partial-01 source-vector graph was checked and remains current because both full reuse packets match exactly. The new fixed-twist result is a separate instance and gets none of these cost observations. No gain, complete census, extrapolation or arbitrary scalar price is claimed. [pcc:unverified]
''')
shutil.copyfile(__file__,p/'original-render.py');print('PDF bytes',(p/'report.pdf').stat().st_size)
