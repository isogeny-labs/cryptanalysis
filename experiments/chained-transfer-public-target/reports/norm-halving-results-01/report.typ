#set page(paper: "a4", margin: 13mm)
#set text(font: "DejaVu Sans", size: 9.1pt)
#set par(leading: 0.5em)
#set heading(numbering: none)
#let d=json("flow.diagram.json")
#text(size: 18pt, weight: "bold")[Complete norm-halving transfer]
#v(3pt)
#text(fill: rgb("#366c68"), weight: "bold")[FINITE CORRECTNESS / UNSIGNED · computational advantage open]

The new direct evaluator and stronger scalar baseline produce the immutable complete-C degree13 Jacobian transfer on the declared finite panel. Native05 passes all four unfiltered tests; all892 inputs stay unchanged. Entire prior three native JSON records are identical, with no ignored fields. (7ff793; earlier52c01c.)

#image("flow.svg", width: 100%, height: 60mm, fit: "contain")
#text(size: 8pt)[Solid arrows describe native-tested routes at the fixed instance. They do not certify a general geometric construction or a priced cost improvement.]

== Correct the half before evaluation
For every admitted x, the existing odd/cofactor decomposition supplies a full elliptic lift a0 in E(L), with Phi0(a0)=x and 2a0=N0(x). Every half a of N0(x) differs from a0 by E[2](K). Look up t with Phi0(t)=x−Phi0(a), then use the explicit quotient square beta Phi0=Psi:
#raw("Psi(a)+Psi(t)=Psi(a+t)=beta(x).", block: true)
Every four actual halves is checked. The runtime includes quadratic Phi/Psi, the source isogeny, dictionary, curve checks, origin subtraction and rational output check. The direct transfer core has no CRT or half-odd scalar. Common admission still includes the full-order Jacobian scalar. Full inverse still uses the Jacobian scalar3413013.

== Declared checks and negative controls
448 exceptional classes;48 mixed cases;40 public sector/direction rows;96 addition pairs; both new-map compositions equal[13]; full new inverse; original independent public source recovery. The48 coordinate targets match the literal selector, with infinity, nonzero two-torsion, generic and non-K halves. Changed quartic constant, zero denominator and incorrect coordinate-F controls are retained. Both deliberately shifted origins fail original odd-membership validation. The missing whole-record canary exits101. (7ff793/d91395.)

== Exact fields and models
K=F223[z]/(z³−3), L=F223[w]/(w⁶−3), z↦w²; K-Frobenius on L is F³. E: a=(214,144,205), b=(137,218,9); E13: a=(196,168,69), b=(8,82,207). Full quartics and origins retain the frozen complete-C identities.

#text(size: 7.7pt)[J0: #d.old_model]

#text(size: 7.7pt)[J1: #d.new_model]

#pagebreak()
#text(size: 17pt, weight: "bold")[Calls, proofs and remaining obligations]

#image("selected-calls.svg", width: 100%, height: 84mm, fit: "contain")
#text(size: 8pt)[The chart renders actual selected entries from one recorded generic input. Rows have different primitive costs; no totals, ratios or speedup inference. Complete literal-selector, context, field, Picard, admission and verification work remains included and unpriced.]

== Accounting that stays in scope
Both methods include packet parsing, complete validation norm and full-order Jacobian admission. The direct setup records two elliptic two-torsion factorizations, eight prime-field Phi calls, eight source-isogeny calls and two quadratic origin traces. The strong baseline includes immutable complete-C setup and its additional isogeny context. Direct generic evaluation has four ordinate recoveries and eight explicit double checks; literal-selector internal checks remain unpriced. The448 exceptional rows take446 generic branches and two infinity branches. Nonzero two-torsion coordinates are tested separately. No timing claim is made.

== Faithful conditional proofs
Both unchanged Lean4.34.1/4.35.0 gates accept ten declarations, zero trusted research axioms; named roots use standard foundations. Nine new exact statement bindings bring the partial count to82; the existing abscissa identity is reused. Proofs cover the universal ordinate identity, differences of halves, Frobenius-square fixing, odd lift, full lift from actual cofactor data, correction existence, evaluator equality, independence and the stronger scalar baseline. (3ba28f.)

The actual field/order/Weil-restriction/quotient/Picard/cofactor bridges remain written/native. The full lift is derived from odd plus actual cofactor lifts, not geometric surjectivity alone. Exact-Z expansion and the unchanged original certificate checker accept both polynomials; deleting −2B gives an actual original-checker counterexample101. The certificate's Lean pointer does not run Lean. (d91395.)

== Sources, preserved failures and next task
#link("https://math.mit.edu/classes/18.783/2025/LectureNotes2.pdf")[Sutherland2025, Lecture2 §2.2 (duplication)] and #link("https://math.mit.edu/classes/18.783/2025/LectureNotes5.pdf")[Lecture5, Theorems5.8/5.25]. The original project already had the halving quartic, selector and ring proof; no novelty claim. Local literal source, hashes, full derivation and proof map accompany this report.

Build01, constructor03, Lean01/02 and all earlier negative records remain retained. Native04/05 whole sources, outputs and actual binaries have complete indices. Complete primitive coverage, admitted matched algorithm references, full geometric bridges and a genuinely nondual degree13 continuation stay open. Live measurement admission, root regression, signing/merge requirements and locked KB/vault limits persist.
