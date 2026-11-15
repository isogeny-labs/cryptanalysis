"""Render only Rust-produced observations; no research arithmetic in Python."""
from pathlib import Path
import hashlib,json,shutil,subprocess
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import typst
o=Path('/workspace/scratch/ct103-relation-character-result-report-03');o.mkdir();shutil.copyfile(__file__,o/'original-render-command.py')
input=Path('/workspace/scratch/ct103-character-summary-native-01/complete-summary.json');data=json.loads(input.read_text());(o/'whole-Rust-report-data.json').write_bytes(input.read_bytes())
groups={(g['side'],g['factor_base']):g for g in data['all_twelve_groups']}
for g in groups.values():
 for k in ['rank_all_five_equal','nullity_all_five_equal','candidate_column_disagreements_all_five_equal','known_log_disagreements_all_five_equal']:assert g[k]is True
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})
fig,axes=plt.subplots(1,2,figsize=(10.4,3.2),layout='constrained')
for side,label,color in [(0,'E2 / D116','#235a8a'),(1,'E3 / D39','#bc6c25'),(2,'E4 / D36','#5a8466')]:
 rows=[groups[(side,fb)]['all_five_public_observations'][0]for fb in [30,36,48,64]]
 axes[0].plot(['30','36','48','64'],[r['nullity']for r in rows],marker='o',label=label,color=color)
 axes[1].plot(['30','36','48','64'],[r['known_log_disagreements']for r in rows],marker='o',label=label,color=color)
for ax in axes:ax.set_xlabel('Factor-base size');ax.grid(axis='y',alpha=.2);ax.set_ylim(bottom=0)
axes[0].set_ylabel('Nullity of all available rows');axes[0].set_title('FB30 leaves several matrix directions');axes[0].legend(frameon=False,fontsize=9)
axes[1].set_ylabel('Known logs disagreeing with source character');axes[1].set_title('The mismatch is present before descent')
fig.savefig(o/'rank-and-known-log-separator.svg');plt.close(fig)
diagram='''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="120" viewBox="0 0 1000 120"><defs><marker id="a" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8" fill="#49667e"/></marker></defs><rect width="1000" height="120" fill="#fff"/><g fill="#edf3f8" stroke="#49667e"><rect x="5" y="12" width="195" height="76" rx="8"/><rect x="265" y="12" width="195" height="76" rx="8"/><rect x="525" y="12" width="195" height="76" rx="8"/><rect x="785" y="12" width="210" height="76" rx="8"/></g><g fill="#17384f" font-family="DejaVu Sans" font-size="16" text-anchor="middle"><text x="102" y="42">Original IC</text><text x="102" y="68">60 complete calls</text><text x="362" y="42">Passive parity</text><text x="362" y="68">100 records / 660 events</text><text x="622" y="42">Exact certificates</text><text x="622" y="68">360 matrices</text><text x="890" y="42">Post-solver norm checks</text><text x="890" y="68">13,200 witnesses</text></g><g stroke="#49667e" stroke-width="2" marker-end="url(#a)"><path d="M200 50 H255"/><path d="M460 50 H515"/><path d="M720 50 H775"/></g><text x="500" y="113" text-anchor="middle" font-family="DejaVu Sans" font-size="14" fill="#49667e">Evidence flows forward. No character or BSGS witness enters the original solver.</text></svg>'''
(o/'evidence-flow.svg').write_text(diagram+'\n')
md='''# The FB30 functional disagrees before descent

Unsigned finite resultsc0479c/19c467/3a7d56: all fifteen FB30 calls retain several matrix directions and disagree with the independently checked source character before geometric descent. Every one of the180canonical Picard and source-character split/walk decompositions holds. The forty-five FB36/48/64 calls agree on every candidate column, known log and computed descent value. No production solver or accepted population was changed. [pcc:unverified]

![Complete finite rank and known-log observations](rank-and-known-log-separator.svg)

The plot displays all twelve model/setting groups. Rust checks that each shown rank, nullity and known-log disagreement count agrees across all five public targets; all sixty original records remain retained. The lines connect only these measured finite settings. Source diagram: evidence-flow.svg; original transfer graph and all 343 producer source hashes remain unchanged. [pcc:unverified]

| Fixed original model | FB30 rank / columns / nullity | FB30 disagreeing known logs | FB36 / FB48 / FB64 nullities |
|---|---|---|---|
| E2, case (2,0), D116/root89, P0(1:0:28) | 24 / 30 / 6 | 179 | 1 / 1 / 1 |
| E3, case(0,1), D39/root40, P0(1:0:90) | 20 / 30 / 10 | 171 | 1 / 1 / 1 |
| E4, case (2,0), D36/root6, P0(1:1:165) | 17 / 30 / 13 | 174 | 1 / 1 / 1 |

Each matrix result holds for training, training plus every holdout, and all available rows, with both full and active columns, for all five targets. Every FB30 candidate disagrees on 29active columns under the checked nonzero common multiplier. All available FB30 rows are already training rows; adding the recorded unused-row population supplies no separator here. [pcc:unverified]

## What was independently checked

Protocol 8e7e1c was normally publishedCBC before all instrumentation and rank/character code. Keep q=223, K=F223[z]/(z^3-3), ell=2773073, source order 11092292, the three fixed masks/origins, all five public targets, FB30/36/48/64, seeds 102–105 and original solver settings. Whole passive native d118b9 at 6d823770 preserves100native records/60calls/660journal events and every input/scalar/check/non-time report/counter under elapsed-only b5e431. Seven reversible insertions change no solver, RNG or selection body. [pcc:unverified]

Rank c0479c at d06ab02f retains360full sparse/dense matrices, complete RREF/pivots/nullspace bases and 1,440,470 elementary operations. Separate Rust replay checks each operation, inverse, canonical basis and source binding. Conditional Lean19c467 passes both unchanged4.34.1/4.35 gates:27declarations, nine named mathematical roots and eighteen generated declarations, zero trusted; all nine exact local statement bindings pass. Two failed development sources and full diagnostics remain preserved. Numeric matrices are Rust certificates, without a concrete Lean specialization. [pcc:unverified]

Character 3a7d56 at 5408b9db computes13,200post-solver class witnesses satisfying [w]B=[4]nu(D), with all three full integer-bound BSGS tables. A separate auditor re-evaluates the actual original NormNew, cofactor projection and direct source scalar equation for each witness. It reconstructs eta from the geometric full relation, independently of the producer's matrix reconstruction. All 15,125 available relation occurrences have zero character residual; scalar residuals are crosschecked in the actual source point group. All sixty post-solver ratios pass direct actual target-group checks; these are diagnostic BSGS-assisted answers, never inputs to the original solver. [pcc:unverified]

The entire known-log table is compared with the source character up to one nonzero multiplier. All 45 FB30 computed descent values disagree; their45canonical and character decompositions still hold. The 135 larger-FB descent values agree. This locates an observed functional mismatch before descent and distinguishes it from a finite failure of those geometric decompositions. Rank excess remains an association; the study does not prove a causal or global class-group theorem. [pcc:unverified]

## Controls, execution and remaining requirements

Four whole capture-stage omissions, a modified matrix coefficient, a constrained kernel coordinate and a source scalar witness all return 101 without accepted output. The scalar mutation fails the auditor's direct source equation. Every positive/negative whole input, raw output, failed source, source/build/runtime/full prepared copy and exact original checkpoint receipt is retained. Observer native28phases, ranknative22phases and characternative22phases meet their recorded expected exits. Compiler phases120seconds; complete diagnostics900seconds and2GiBvirtual memory. Exact original field-engine closure/fullRLIB-RMETA/freshreuse holds; there is no second unreported preparation. [pcc:unverified]

The full raw roots are scratch/ct101-original-relation-kernel-native-01, scratch/ct102-original-relation-rank-native-01 and scratch/ct103-original-relation-character-native-01. Complete Rust reporting data and source are scratch/ct103-character-summary-native-01; byte inventories and whole immutable evidence are in experiments/chained-transfer-public-target/evidence/original-relation-{kernel,rank,character}-*. GenuineNEW27 is pending for every post26source/raw/runtime/prepared/failure/control/CI-artifact-log/report root. Frozen producer source3d49af7 remains unchanged; producer mirror4cea0760 currently covers accepted CI/capture/rank/proofs, with character mirror next. [pcc:unverified]

Actual model/field/Frobenius/Picard/order/program interpretation, a global character extension, concrete numeric Lean specialization, calibrated live budget/capacity/isolation/image admission, complete primitive/setup accounting and strongest matched references remain explicit requirements. This finite diagnosis makes no calibrated speed, asymptotic, novelty or signed claim. Preserve the negative result and review a prospective unassisted relation-completion experiment before any production-solver change. [pcc:unverified]

Primary source: Claus Diem, JTNB24(3),2012,639–667, especially line-section/large-prime and linear-algebra discussions, primary URL http://jtnb.cedram.org/item?id=JTNB_2012__24_3_639_0; primary PDF/text and KB status/four-query/theorem-query127 receipts at scratch/ct90-prime-descent-primary-review-01 and scratch/ct101-relation-kernel-primary-review-01. No KB or atlas availability gap supports an absence or novelty inference. Original primary solver, PicClass representation, NormNew and NewTargetIC hypotheses were read. See original-relation-rank-01/PROOF_MAP_01.md for exact hypotheses and binding identifiers. [pcc:unverified]
'''
(o/'REPORT.md').write_text(md)
typ='''#set page(paper:"a4",margin:15mm)
#set text(font:"DejaVu Sans",size:9pt)
#set par(leading:.4em)
#let blue=rgb("#235a8a")
#let gray=rgb("#bac6cf")
#text(size:17pt,weight:"bold")[The FB30 functional disagrees before descent]
#v(3pt)
#text(fill:blue,weight:"bold")[COMPLETE FINITE EVIDENCE · SIXTY CALLS · UNSIGNED]

All fifteen FB30 candidates disagree with the checked source character before descent. All 180 canonical Picard and source-character split/walk decompositions hold. The forty-five FB36/48/64 calls agree on every candidate column, known log and descent value. No production solver, factor base or accepted population was changed.

#image("evidence-flow.svg",width:100%)
#image("rank-and-known-log-separator.svg",width:100%)

#table(columns:(1.3fr,1fr,.9fr,.9fr),inset:6pt,stroke:.5pt+gray,
 [*Fixed model*],[*FB30 rank/columns/nullity*],[*FB30 wrong known logs*],[*Larger FB nullities*],
 [E2 / D116 / root89],[24 / 30 / 6],[179],[1 / 1 / 1],
 [E3 / D39 / root40],[20 / 30 / 10],[171],[1 / 1 / 1],
 [E4 / D36 / root6],[17 / 30 / 13],[174],[1 / 1 / 1],
)

Each cell holds for all five public targets and all six matrices: training, training plus every holdout, and all available rows, each with full and active columns. The entire available/selected/kernel/known-log capture is equal across each group of five; all sixty records remain. FB30 already uses every collected row. Each FB30 candidate differs on 29active columns under the checked common multiplier.

The original models remain E2/case (2,0)/P0(1:0:28), E3/(0,1)/(1:0:90), E4/(2,0)/(1:1:165); q=223, K=F223[z]/(z^3-3), ell=2773073, full source order 11092292. Keep all masks, five public targets, FB30/36/48/64, seeds 102–105, rows_mult 1.2, max_desc 100000, sge=false, maxw 12 and lp2=true.

#text(size:8pt)[Claims c0479c/19c467/3a7d56 are unsigned. A finite matrix direction is not automatically a global logarithm. The result locates a recorded functional mismatch; it is not a causal, asymptotic or calibrated speed theorem. Full source-linked report and complete data accompany this PDF.]

#pagebreak()
#text(size:17pt,weight:"bold")[How the separator was checked]
#v(3pt)
#text(fill:blue,weight:"bold")[NO ORACLE FEEDBACK · COMPLETE INPUTS · NEGATIVES PRESERVED]

== Observe without changing the solving path
Protocol 8e7e1c was normally published at CBC before all instrumentation and measurements. Seven reversible passive insertions preserve the original solver/RNG/selection bodies. Native d118b9 at 6d823770 retains 100 native records, 60 calls, 660 journal events and every full input/scalar/check/non-time report/counter under elapsed-only b5e431.

== Exact finite matrices and conditional proof
Rank c0479c at d06ab02f retains 360 sparse/dense matrices, RREF, pivots, complete nullspace bases and 1,440,470 elementary operations. A separate Rust replay checks every operation/inverse/basis and whole source binding. Both unchanged Lean 4.34.1/4.35 gates audit 27 declarations: nine named roots and eighteen generated declarations, zero trusted; all nine exact local bindings pass. Two failed proof-development attempts remain. The proofs derive row-operation/finite-trace kernel preservation and conditional RREF/character-ratio implications. Numerical matrices have no concrete Lean specialization.

== Actual post-solver norm witnesses
Character 3a7d56 at 5408b9db supplies 13,200 class witnesses [w]B=[4]nu(D), with all three entire integer-bound BSGS baby tables. A separate auditor recomputes the original actual norm/cofactor projection and direct source scalar equation for each witness. Eta is reconstructed independently from the geometric full relation. All 15,125 available relation occurrences have zero character residual, crosschecked in the actual source point group. All sixty post-solver ratios pass direct actual target-group checks; these BSGS-assisted diagnostic answers are never supplied to the solver.

All 45 FB30 computed Y values disagree with the checked character, while their full canonical and source-character decompositions hold. All 135 larger-FB values agree. Actual model/group/program and global character hypotheses remain explicit: finite agreement does not close them.

== Controls and execution custody
Four entire capture-stage omissions, a matrix coefficient, a constrained kernel coordinate and a scalar witness mutation each return 101 without accepted output. The scalar mutation fails its actual direct source equation. Observer/rank/character native phases 28/22/22 meet all recorded expected exits. Compiler caps 120 seconds; complete diagnostics 900 seconds / 2 GiB. Exact original field closure / full RLIB-RMETA / fresh reuse holds, without a second preparation. All whole inputs / raw sources/failures/executables/full prepared copies are retained for genuine NEW27; publication is pending.

== What remains
Complete primitive/setup accounting, strongest matched references, calibrated live budget/capacity/isolation/image admission, concrete numeric Lean specialization and actual global model / Picard / character / program bridges stay open. Review a prospective unassisted relation-completion experiment before modifying the production solver. The established transfer graph and all 343 producer scientific hashes are unchanged.

#text(size:8pt)[Sources: whole-60 Rust verdict/reporting data; original solver/PicClass/NormNew/NewTargetIC hypotheses; Diem, JTNB24(3),2012,639–667, line-section/large-prime and linear-algebra discussions. KB status/four queries/theorem query 127 and primary PDFs/text retained; no absence/novelty inference. Reproduction paths, exactclaims, commands, controls and full raw inventories: REPORT.md and original-relation-rank-01/PROOF_MAP_01.md.]
'''
(o/'report.typ').write_text(typ)
typst.compile(str(o/'report.typ'),output=str(o/'report.pdf'))
q=subprocess.run(['pdfinfo',str(o/'report.pdf')],capture_output=True);(o/'pdfinfo.txt').write_bytes(q.stdout+q.stderr);assert q.returncode==0;print(q.stdout.decode(),flush=True)
q=subprocess.run(['pdftoppm','-png','-scale-to','1300',str(o/'report.pdf'),str(o/'page')],capture_output=True);(o/'raster.txt').write_bytes(q.stdout+q.stderr);(o/'raster.exit').write_text(str(q.returncode)+'\n');assert q.returncode==0
(o/'render-input-custody.json').write_text(json.dumps(dict(whole_Rust_input=str(input),whole_Rust_input_sha256=hashlib.sha256(input.read_bytes()).hexdigest(),rendering_only=True,all_figured_group_values_equal_across_five=True,PDF_bytes=(o/'report.pdf').stat().st_size,PDF_sha256=hashlib.sha256((o/'report.pdf').read_bytes()).hexdigest(),visual_inspection='PENDING; every final page must actually be opened'),indent=2)+'\n')
print('PDF bytes',(o/'report.pdf').stat().st_size,flush=True)
