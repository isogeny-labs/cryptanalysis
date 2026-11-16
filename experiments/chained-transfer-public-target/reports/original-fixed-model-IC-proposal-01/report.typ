#set page(paper:"a4",margin:16mm)
#set text(font:"DejaVu Sans",size:9.5pt)
#set par(leading:.45em)
#let blue=rgb("#365e87")
#let green=rgb("#267044")
#let gray=rgb("#bbc4cf")
#text(size:17pt,weight:"bold")[IC on the fixed original-prime Jacobian chain]
#v(4pt)
#text(fill:blue,weight:"bold")[PROSPECTIVE · 60 ATTEMPTS · 15 REQUIRED VERIFIED PUBLIC CASES]

The original full-cofactor chain is implemented and accepted on its complete finite population. The individual induced-transfer identities and integer linearity are proved conditionally. This next experiment asks whether the existing class-input index-calculus solver solves the unchanged public targets on each of the three fixed original-prime Jacobians. It reuses the solver; no new IC algorithm or cost advantage is assumed.

== Freeze these models before observing outcomes
#table(columns:(.5fr,.9fr,.7fr,.7fr,1.2fr),inset:8pt,stroke:.5pt+gray,
 [*Side*],[*Source / case*],[*D / root*],[*Prime*],[*Actual P0*],
 [0],[E2 / (2,0)],[116 / 89],[2,773,073],[(1:0:28)],
 [1],[E3 / (0,1)],[39 / 40],[2,773,073],[(1:0:90)],
 [2],[E4 / (2,0)],[36 / 6],[2,773,073],[(1:1:165)],
)

The field is K=F223[z]/(z³−3), the full source order is11,092,292, and each Jacobian is represented over F223. Keep all quartics, tags, masks, field bases, origins, generator and five public Q fixed. They are the actual accepted geometry outputs; no outcome-dependent reselection is allowed.

== Construct the public packets through the actual chain
#table(columns:(1fr,1fr,1fr),inset:9pt,stroke:.6pt+gray,
 [*Original public G,Q*],[*Opaque Jacobian maps*],[*Independent checks*],
 [Existing source map → E2\ Actual prime Phi → J2],[J2 → J3 by degree13\ J2 → J4 by degree169],[Destination source points\ Actual prime Phi equality],
 [No scalar answer at runtime],[Whole generator + Q packets],[Actual target and original source],
)
#align(center)[#text(fill:green,weight:"bold")[Each actual target context → existing IC pipeline → verified scalar]]

The new context selects an exact fixed-geometry side and admits tagged canonical ell-torsion inputs, with a nonzero generator. The solver receives only public G,Q, the target context, ell, ordinary parameters and an RNG seed. It receives no source lift, scalar witness, elliptic DLP solver, recovery fallback or DLP table. Every reported scalar is checked in the actual target and the original independent source group.

== Preserve the existing solver completely
Copy new-target-ic/derived/class_solver.rs byte-for-byte. Adapt only the surrounding context/type boundary to original-full-geometry NormNew. Keep the actual P0 at factor-base index0. Relation collection, large-prime graph, RNG, holdouts, linear algebra, descent and final Picard verification remain literal. Record any additional required source difference before execution.

#text(size:8pt)[Source checkpoint41e35d8; nativee245d0; proofeddc37/resultd90ad1; complete original CI03a93f80; fresh proof run43707728617. Existing IC e869bd and sampler9bc5e6 are prior results on different fixed target selections. This proposal does not transfer their outcomes to the new models. All standing is unsigned.]

#pagebreak()
#text(size:17pt,weight:"bold")[Acceptance, failures and the computational question]
#v(4pt)
#text(fill:green,weight:"bold")[WHOLE POPULATION · ACTUAL GROUP VERIFICATION · COMPLETE RAW REPORTS]

#table(columns:(1fr,2fr),inset:8pt,stroke:.5pt+gray,
 [*Population*],[3 fixed models ×5 public targets ×4 factor-base settings =60 attempts],
 [*Settings*],[FB30/36/48/64; seeds102/103/104/105; rows_mult1.2; max_desc100000; sge=false; maxw12; lp2=true],
 [*Success criterion*],[At least one correct IC solve for each of all15 public cases; all60 attempts retained],
 [*Reject immediately*],[Any reported success failing the actual target or independent original-source check],
 [*Input controls*],[Malformed, noncanonical, foreign tags, zero/non-ell generator, non-ell target, cross-target packet, invalid side and parameters],
 [*Evidence controls*],[Whole record populations; actual entire-class omissions reject without accepted output],
 [*Execution*],[One serial unfiltered test;900s native bound;2GiB address-space limit; exact existing field preparation and runtime binaries],
)

An unsuccessful attempt remains a result. Do not stop after an early success or drop failed factor-base settings. A timeout or a wrong-answer failure preserves its actual completed prefix and leaves the full acceptance criterion open. Keep all complete success/failure reports, counters, raw phase walls, source snapshots, commands, toolchains and real exits. Later replay validates correctness and complete populations; raw timing values remain diagnostics.

== What a computational advantage would still require
Inventory source validation, both geometry origins, model/map construction, known initial point construction, opaque and retained-lift maps, FpR/extension primitives, admission, factor-base setup, relation verification, linear algebra, hashing/lookups, descent and final independent source verification. Existing IC/Picard counters are partial. Missing primitive/setup costs remain unknown, and preparation reuse supplies no cold cost.

The strongest matched IC/rho references and live budget, capacity, isolation and image admission are still open. A correct toy solve cannot establish a calibrated ratio, pipeline improvement or a new ECDLP advantage. After this discriminator, adapt the existing norm-assisted sampler to these same frozen models and preserve all paired reports and shared failures.

== Primary sources and proof boundary
Diem2012, On the discrete logarithm problem for plane curves, Theorem1, gives expected soft-O(q) for nonhyperelliptic genus3 degree-zero class groups. Tian2020 describes transfer through isogenies and the relevant field/genus qualifications. These are established literature results, not new complexity claims from this experiment. Full retained primary texts and reviewed passages are source-linked in the render inputs.

Checked answers and unknown-log preservation use the existing conditional homomorphism/injectivity statements; actual model, field, Frobenius, Picard, order and program identification stays explicit. The implementation must not add a desired transfer identity as an assumption to repair a failure. Preserve the full new source/data/executables/prepared libraries/failures for genuine NEW26, and keep all previous negative results.

#text(size:8pt)[Protocol ORIGINAL_FIXED_MODEL_IC_PROTOCOL_01.md; complete immutable prior reference73/1440 scopes remain unchanged; future custody NEW26. Vault remains locked at8edec422 and KB access unavailable; no novelty or absence follows. No mathematical, performance or signing promotion is supplied by this proposal.]
