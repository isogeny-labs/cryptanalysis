#set page(paper:"a4",margin:16mm)
#set text(font:"DejaVu Sans",size:9.4pt)
#set par(leading:.42em)
#let blue=rgb("#365e87")
#let green=rgb("#267044")
#let gray=rgb("#bbc4cf")
#let d=json("complete-record-diagnostics.json")
#text(size:17pt,weight:"bold")[IC solves all15 original-prime public cases]
#v(4pt)
#text(fill:green,weight:"bold")[60 ATTEMPTS · 45 VERIFIED ANSWERS · 15 REJECTED FB30 CANDIDATES]

At source0cb4ab3, the complete frozen panel passes on the three accepted original-prime Jacobians. All60 attempts finish. Every one of the15 public cases has an answer checked in the actual target Jacobian and in the independent original source group. The existing class-input IC solver remains byte-for-byte unchanged; only its fixed original-geometry context and harness are adapted.

== Same fixed models, every factor-base setting retained
#table(columns:(1fr,1fr,1fr,1fr,1fr),inset:8pt,stroke:.5pt+gray,
 [*Model / P0*],[*FB30*],[*FB36*],[*FB48*],[*FB64*],
 [E2 · D116\ (1:0:28)],[0/5 accepted],[5/5 verified],[5/5 verified],[5/5 verified],
 [E3 · D39\ (1:0:90)],[0/5 accepted],[5/5 verified],[5/5 verified],[5/5 verified],
 [E4 · D36\ (1:1:165)],[0/5 accepted],[5/5 verified],[5/5 verified],[5/5 verified],
)

All15 FB30 reports contain the original solver rejection “recovered k does not satisfy kG = Q”. These are retained rejected candidates, not accepted wrong answers. No model, kernel, origin, prime, public input, factor-base setting, seed or success criterion was reselected. FB36/48/64 provide45 verified answers across the same five public Q on each model.

== Actual transfers construct the public solver inputs
#table(columns:(1fr,1fr,1fr),inset:9pt,stroke:.6pt+gray,
 [*Original public G,Q*],[*Opaque Jacobian chain*],[*Independent validation*],
 [Existing point map to E2\ Actual prime Phi to J2],[J2 → J3, degree13\ J2 → J4, degree169],[Destination source-point maps\ Actual destination Phi],
 [Five original public targets],[Exact field/model/key packets],[All packets agree before IC],
)

The context binds the exact original case, kernel mask, P0, field and order. The solver receives admitted public G,Q, the target context, ell, ordinary parameters and a seed. Expected scalar answers occur only in the outside test harness. No point lift, scalar witness, elliptic DLP solver, recovery fallback or DLP table is supplied to the solver.

== Complete bounded result and custody
The one unfiltered test returns0. All30 phases have their original expected exits: source/checkpoint/custody, whole native run, whole freeze/compare, seven complete omission-input materializations/integrity checks and seven omission rejections101/no output, then final actual binaries and source guards. The whole100 records retain86 new IC records and14 original constructor records, including full setup and every success/failure report.

#text(size:8pt)[Prospective3da7fe and inspected proposal were published7550409 BEFORE Rust. Compiledf9e8c9/build02 at03769fb; native launchad4030/source0cb4ab3; exact original checkpoint20 run43710462830/job132800676430/art14159918729/all28/remote+localgate0. Initial Cargo101 type errors and both full source attempts are retained. Full new evidence awaits genuineNEW26. Unsigned correctness evidence only.]

#pagebreak()
#text(size:17pt,weight:"bold")[Diagnostic counters and the remaining advantage test]
#v(4pt)
#text(fill:blue,weight:"bold")[PARTIAL IC/PICARD COUNTERS · ALL FIVE ATTEMPTS PER ROW · NO PRICE]

These are sums of the existing reported phases for each five-attempt group, including every failed attempt. They omit complete FpR/extension primitives, model/map construction, admission, input transfers and independent source verification. The full JSON retains all original counters and raw walls. No calibrated ratio or complete pipeline comparison follows from this table.

#table(columns:(.5fr,.6fr,.8fr,1.1fr,1fr),inset:6pt,stroke:.5pt+gray,
 [*Side*],[*FB*],[*Verified*],[*Partial mul*],[*Partial inv*],
 ..d.all12_attempt_setting_groups.map(row=>(
  [#row.side],[#row.nfb],[#row.verified_successes /5],
  [#row.summed_original_partial_phase_counters.mul],[#row.summed_original_partial_phase_counters.inv],
 )).flatten(),
)

== Exact checks and faithful proof boundary
All1,465 immutable prior/proof/protocol guards pass. Actual compiled/runtime test and auditor bytes agree, with complete old field-engine preparation, dependency/features/targets closure and fresh reuse checked. Every whole XZ omission input is independently decompressed and compared against all original retained line bytes. The full native stream, both whole100-record reconstructions, all15 rejected reports, actual binaries and prepared libraries remain intact.

The unchanged checked-target-solution and common-offset log-ratio statements pass both original Lean gates: two roots, zero trusted assumptions, both exact original bindings01efbf/671d42. InducedFullTransfer supplies the earlier conditional integer-linearity, reverse-norm and recovery identities. Actual model/field/Frobenius/Picard/order/program/lift and global relation-log extension remain explicit bridges; neither result establishes solver completeness.

== What advances next
Adapt the existing norm-assisted sampler to these same original models and preserve all paired reports and shared failures. Complete primitive/setup/known-point/opaque-input/strong-reference coverage and obtain live budget/capacity/isolation/image admission before a performance conclusion. Publish the full new source/data/failures/executables/prepared copies through genuineNEW26 before canonical fixtures and additive native replay.

This is a complete finite correctness discriminator on three fixed toy Jacobians, using an existing IC solver. It makes no new asymptotic, novelty, calibrated ECDLP advantage, global-CI or signed-standing claim. Cold120, global/main-ledger, root124, clock101 and review/signing obligations stay open.
