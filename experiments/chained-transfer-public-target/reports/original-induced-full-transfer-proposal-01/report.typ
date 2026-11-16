#set page(paper:"a4",margin:16mm)
#set text(font:"DejaVu Sans",size:9.5pt)
#set par(leading:.45em)
#let blue=rgb("#365e87")
#let green=rgb("#267044")
#let gray=rgb("#bbc4cf")
#text(size:17pt,weight:"bold")[Derive the full quotient transfers from source identities]
#v(4pt)
#text(fill:blue,weight:"bold")[PROSPECTIVE · NINE PLANNED ROOTS · NO NEW LEAN MODULE YET]

The complete original full-group evaluator passes its finite701-record study (e245d0). Existing conditional proofs retain the descent/correction argument and derive composite norms from individual norms. This next proof task derives the individual quotient-map norms, additivity and integer linearity from quotient representations, kernel transport and elliptic duality. The desired transfer conclusions are not hypotheses.

== Objects to define explicitly
#table(columns:(1fr,1fr,1fr),inset:10pt,stroke:.6pt+gray,
 [*Geometric source A*],[*g and signed reverse gh*],[*Geometric source B*],
 [Phi:A→J\ section r:J→A],[Source homomorphisms\ gh(g(a))=n·a\ g(gh(b))=n·b],[Psi:B→K\ section s:K→B],
 [Phi(r(x))=x],[Full forward/reverse kernel transport],[Psi(s(y))=y],
 [*Quotient J*],[*T and S to derive*],[*Quotient K*],
)
#align(center)[#text(fill:green,weight:"bold")[T(x) := Psi(g(r(x)))  ·  S(y) := Phi(gh(s(y)))]]

The presentations expose additive, subtraction, integer-scalar and zero identities for Phi and Psi. Compatible edges expose the same identities for g and gh and the kernel implications. Neither section is assumed additive, linear, equivariant or rational. No field contains a desired T/S norm, commuting square, injectivity or output equality.

#table(columns:(1fr,1fr),inset:7pt,stroke:.5pt+gray,
 [*Given*],[*To derive*],
 [Equal source Phi images + kernel transport],[Equal Psi∘g images; section independence],
 [Phi(r(x))=x],[T(Phi(a))=Psi(g(a))],
 [Source homomorphism identities],[T(x+y)=T(x)+T(y); T(z·x)=z·T(x)],
 [Both source elliptic dual identities],[S(T(x))=n·x and T(S(y))=n·y],
 [A middle presentation + compatible second edge],[Two quotient maps collapse to one source lift],
 [A point annihilator + Bezout witness],[Full-cofactor recovery and carrier injectivity],
)

== Keep geometric and rational sections distinct
The modules model geometric points over an algebraic closure. A geometric quotient section is not a rational-point section. Rational output is a separate equivariance/kernel consequence already addressed by ChainDescent.corrected_output_fixed. The actual HLP quotient, Frobenius, Picard, finite-field encoding, accepted runtime lifts and group-order bridges remain explicit.

The recovery theorem assumes order·x=0 for the particular input. It must not assume that every point of a geometric abelian variety is annihilated by the finite rational order. The original full-order inverses13=3,413,013 and169=9,648,325 modulo11,092,292 are independently rechecked as integer witnesses, with quotients−4 and−147.

#text(size:8pt)[Source base25801fe; original full-group protocol1539b6/d4f9d6b; finite nativee245d0; conditional7b5f49/da2fe7; inspected report761003; genuine25 settled at consumer6343025/rootd93b64d. This proposal formalizes standard quotient algebra and makes no novelty, new-DLP-solution, calibrated-cost or signed-standing claim.]

#pagebreak()
#text(size:17pt,weight:"bold")[Frozen proof population and acceptance boundary]
#v(4pt)
#text(fill:green,weight:"bold")[BOTH ORIGINAL GATES · EXACT STATEMENT BINDINGS · PRESERVE ALL FAILURES]

The standalone module will define the presentations, compatible edges and induced transfer, then prove exactly these nine roots:

+ Representative independence, specializing the existing equal-images kernel argument to Psi composed with g.
+ The source identity T(Phi(a))=Psi(g(a)), using the section and independence.
+ Additivity, without an additive section or assumed transfer additivity.
+ Integer linearity, supplying the unknown-log relation.
+ Both individual reverse norms from source elliptic duality.
+ Two-edge collapse to the factored elliptic composition and one final quotient.
+ Inverse recovery for each input on the full stated annihilator.
+ Injectivity for two inputs on that carrier, derived from recovery.
+ Ordinary-kernel original inverse/Bezout/coprimality witnesses.

The first root restates/specializes the old quotient-kernel argument. Existing ChainDescent, FullGroupNorm and known-point/CRT statements and every hypothesis stay unchanged. Source structures must expose all assumptions; a failed proof may not be repaired by adding its desired transfer conclusion as a field or hypothesis.

== Primary and repository sources reviewed
HLP math/9809210v1 section4.1 works with products of elliptic curves and maximal isotropic two-torsion kernels, first over a separably closed field. Lemma13 classifies the finite135 maximal isotropic subgroups. Propositions14–15 and their proofs supply the degree-eight quotient and the quadratic base-field qualification. Their hypotheses are retained as actual geometric bridges; this generic module does not reprove those constructions.

The current ChainDescent equal-images/correction/Frobenius arguments and FullGroupNorm two_pair_norm/inverse_on_full_annihilator statements are reviewed as complete source. The latter are valid conditional results; the new task supplies the preceding quotient-map norm derivation. KB status, mechanism, negative and theorem lookups exit127. The autoresearcher vault remains VLT1-locked at8edec422; no novelty or absence follows from these access gaps.

== Execution and continuous checkpoints
Publish the protocol and this inspected proposal before creating the Lean module. Run the unchanged original4.34.1 and4.35.0 gates on the exact source, each bounded120s: nine roots, zero trusted assumptions, all nine exact local statement bindings. No native_decide, sorry or user axiom is allowed. Keep actual sources, failed sources, raw gates and real exits. An elaboration failure or timeout is not a mathematical counterexample.

All1,440 version03 source references and343 original producer science hashes remain fixed. The current additive native replay43700115169 continues against exact25801fe. The isolated branch has the sole active consumer ledger; normal fast-forward to it precedes any acceptance-ledger append on the original research branch. No rebase, rechain or force update is permitted.

== What remains after the algebra
Connecting the abstract presentations and edges to actual quotients/programs, rational descent and group-order/admission remains explicit. This task constructs no new curve and asserts no calibrated advantage. Prime-field index calculus, complete primitive/setup/online costs, strongest matched references and known-point baselines remain queued. Future custody is NEW26, and all standing remains unsigned.
