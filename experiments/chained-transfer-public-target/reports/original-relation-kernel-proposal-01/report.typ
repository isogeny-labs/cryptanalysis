#set page(paper:"a4",margin:16mm)
#set text(font:"DejaVu Sans",size:9.5pt)
#set par(leading:.45em)
#let blue=rgb("#365e87")
#let green=rgb("#267044")
#let gray=rgb("#bbc4cf")
#text(size:17pt,weight:"bold")[Why does FB30 return a rejected candidate?]
#v(4pt)
#text(fill:blue,weight:"bold")[PROSPECTIVE · SIXTY COMPLETE CALLS · NO DIAGNOSTIC RESULT YET]

Original IC 7df2ae keeps fifteen rejected FB30 attempts and forty-five verified FB36/48/64 attempts. Paired sampler 4fd903 preserves the same shared failures. This first diagnostic study observes the original unassisted path and asks which recorded constraints separate a genuine character from the returned relation vector. The production solver is unchanged.

== Freeze the original models and every outcome
#table(columns:(.45fr,1fr,.8fr,1.1fr),inset:7pt,stroke:.5pt+gray,
 [*Side*],[*Source / case*],[*D / root*],[*Actual P0*],
 [0],[E2 / (2,0)],[116 / 89],[(1:0:28)],
 [1],[E3 / (0,1)],[39 / 40],[(1:0:90)],
 [2],[E4 / (2,0)],[36 / 6],[(1:1:165)],
)

Keep F223, K=F223[z]/(z^3-3), ell 2773073, source order 11092292, all masks, generator and five public targets. Run all 3 models x 5 targets x 4 settings: FB30/36/48/64, seeds 102-105, rows_mult 1.2, max_desc 100000, sge=false, maxw 12, lp2=true. Never select only successful calls or assume matrices repeat across targets.

== Observe first; interpret after the reports are frozen
#table(columns:(1fr,1fr,1fr),inset:8pt,stroke:.6pt+gray,
 [*Unchanged original path*],[*Passive whole captures*],[*Independent post-solver work*],
 [Collection; graph; rows; Lanczos; propagation; descent; actual final group check],
 [Every available row/graph; training, holdouts, remap; kernel and full log table; all three descent descriptions],
 [Exact RREF and row certificates; norm and source character checks; propagated logs/descents; counterexamples],
)

Observers clone existing values without field/group operations, RNG consumption or control-flow changes. No scalar answer, source lift, BSGS table or character witness enters the solver. Preserve complete raw reports and require every non-time field and counter to match the original observation under contract b5e431. Instrumentation overhead is unpriced.

== The mathematical gap being tested
A vector can annihilate selected and held-out rows without extending to a global logarithm on the actual class group. NewTargetIC223.common_offset_log_ratio explicitly assumes that genuine additive/scalar logarithm. Rank excess alone is not a causal explanation for the wrong answer.

#text(size:8pt)[Sources: complete literal solver and graph/Lanczos implementation; original norm and Lean hypotheses; Diem, JTNB 24(3), 2012, 639-667, line-section/large-prime and linear-algebra discussions. KB status/four queries/theorem query 127; primary-review receipt ct101 retained. Unsigned proposal; no rank calculation or diagnostic solver implemented.]

#pagebreak()
#text(size:17pt,weight:"bold")[Certificates, independent characters and decisions]
#v(4pt)
#text(fill:green,weight:"bold")[WHOLE INPUTS · EXACT FINITE CERTIFICATES · NEGATIVE RESULTS RETAINED]

== Exact numerical evidence
Compute RREF over F_ell for training, training-plus-heldout and all available matrices. Retain original sparse encodings, complete dimensions, active/full column identities, pivots, RREF, nullspace basis and elementary row-operation certificate. An independent Rust validator replays the certificate and checks every basis vector. Inactive logs remain unknown; retain every row excluded from a candidate-residual check.

Formalize row-operation kernel preservation and conditional character/ratio implications with both original Lean gates. Do not describe numerical matrices as Lean-verified until a concrete specialization exists. Keep actual Picard/norm/program interpretation explicit.

== Independent source character, after solver completion
For an observed class D, compute the existing norm nu(D), project by cofactor 4, and find w with [w]B=[4]nu(D) using bounded BSGS only in the post-solver validator. Independently check every scalar equation in the actual source group. Retain all points, bounds, encodings, failures and table parameters; no oracle result is injected into the solver.

Build eta from an actual full relation. Check every relation against the witness; compare every known solver log up to one nonzero common scalar. Recheck the three descent classes and their retained descriptions. Handle zero anchors explicitly. Finite agreement does not prove a global class-group extension.

#table(columns:(1.3fr,1.7fr),inset:7pt,stroke:.5pt+gray,
 [*Observed separator*],[*Permitted conclusion*],
 [Added rows reject the candidate],[Selected rows did not enforce those recorded constraints],
 [Extra kernel directions; character disagreement],[Finite ambiguity; attribution needs descent evidence],
 [Active vector agrees; propagated logs differ],[Investigate propagation under the checked interpretation],
 [Known logs agree; descent or ratio differs],[Investigate a later descent/model/program bridge],
 [Witness relation failure or no separator],[Retain the failure or null result; do not strengthen it],
)

== Controls and execution boundary
Alter a matrix coefficient, a constrained kernel coordinate, a checked scalar witness, and omit an entire capture stage. Require actual independent rejection with no accepted output and preserve each whole input. Keep every old domain and final group check.

Use the existing exact field-engine closure and full prepared/runtime copies. Compiler phases 120 seconds; complete native, diagnostic and independent-validator phases 900 seconds each, 2 GiB virtual memory bounds. A cap gives a retained incomplete result. Local finite correctness diagnostics do not admit calibrated EKS or performance claims.

#text(size:8pt)[Publish the full protocol before instrumentation or measurements. Preserve every source, report, rejected attempt, matrix, certificate, executable, full prepared copy and failed control. Future whole custody NEW27. Assisted-path instrumentation and production solver changes require a prospective addendum.]
