#set page(paper: "a4", margin: 14mm)
#set text(font: "DejaVu Sans", size: 9.4pt)
#set par(leading: 0.55em)
#set heading(numbering: none)
#let d=json("flow.diagram.json")
#text(size: 18pt, weight: "bold")[Norm-halving a degree-13 transfer]
#v(3pt)
#text(fill: rgb("#966122"), weight: "bold")[PROSPECTIVE / UNSIGNED — native and proof outcomes pending]

The matched rational map beta: J0(F223) → J1(F223) already has the complete-C evaluator. This proposal compares a direct elliptic norm-halving implementation against an optimized norm-assisted scalar baseline. The original implementation, inputs and negative records stay frozen.

#image("flow.svg", width: 100%, height: 105mm, fit: "contain")
#text(size: 8pt)[Dashed arrows are proposed evaluation routes. No performance data exist for this comparison, so the diagram explains the algorithm; it is not a measured cost graph.]

== Strengthen the baseline first
#raw("x2=[ell]x; k=1386537; 2k=ell+1\nbaseline(x)=Phi1 gamma([k]N0(x)) - beta(x2)", block: true)
Move inverse-two multiplication to E(K), retaining the Jacobian CRT projection. Include the cofactor table, constructor and the same admission/output checks in both arms. Selected call counts do not price primitive operations.

== Candidate and required correction
Compute Q=N0(x); choose a half a in E(L). Retain d=x-Phi0(a), an actual two-torsion correction t with Phi0(t)=d, and return Psi(a)+Psi(t), where Psi=Phi1 gamma. Check the corrected lift a+t and require all four choices of half to give the same complete-C answer. Reverse with the actual dual.

== Exact models
#text(size: 8pt)[J0: #d.old_model]

#text(size: 8pt)[J1: #d.new_model]

K=F223[z]/(z³−3), L=F223[w]/(w⁶−3), z↦w². E has a=(214,144,205), b=(137,218,9); E13 has a=(196,168,69), b=(8,82,207). Model origins and full quartics remain the frozen complete-C identities. On E(L), the K-Frobenius is F³.

#pagebreak()
#text(size: 17pt, weight: "bold")[Reuse the halving algebra; test the transfer]

The project already has a complete elliptic-halving selector and universal Lean ring proof of its abscissa quartic. Reuse the original code literally as the native oracle. The new question is the complete norm-halving evaluator and its cost against the stronger baseline.

== Complete coordinate cases
#raw("H(X)=X^4-4uX^3-2AX^2-4(Au+2B)X+A^2-4Bu\nT=X^3-3uX^2-AX-Au-2B;  Y=T/(2v)  (v != 0)\nT^2-4(u^3+Au+B)(X^3+AX+B)=H(X)(X-u)^2", block: true)
For Q=O use all E[2]. For nonzero two-torsion Q, retain both ordinates at each distinct abscissa; there need only be two abscissas. Check all four points on the actual curve and [2]a=Q. The fast ordinate formula rejects v=0. Preserve denominator and source-isogeny admission checks.

== Discriminating controls
Retain whole rows for all448 rational exceptional inputs, all48 mixed-sector cases, the five public targets in every cofactor sector, both directions and both [13] compositions. Require direct/optimized/reference agreement, all four corrected lifts, infinity/two-torsion/four-torsion coverage, F³ controls and actual output/source checks. Wrong correction, field action, model/origin, changed quartic term and omitted record must reject. Compiler/CLI failures remain separate from mathematical negatives.

== Proof and accounting boundaries
Check a general-ring ordinate identity, exact-Z coefficient expansion and the original identity-certificate checker. Faithful conditional group lemmas must prove Frobenius halving, lift difference/correction and baseline equality with all geometry hypotheses explicit. Run both unchanged original Lean gates and exact statement binding. The actual Weil-restriction, quotient and Picard bridges remain written/native dependencies.

Record real call-site counts for setup, admission, norm, factorization, ordinates, complete quadratic Phi/Psi, source isogeny, correction and verification. Common full-order admission may still use a large Jacobian scalar. Include it. No calibrated cost, stage win or computational advantage follows from fewer named scalar calls. Existing live budget, isolation, tested image and matched-reference admission remains required for timing.

== Sources and reproducible next step
#link("https://math.mit.edu/classes/18.783/2025/LectureNotes2.pdf")[Sutherland, 18.783 (2025), Lecture2 §2.2: duplication.]

#link("https://math.mit.edu/classes/18.783/2025/LectureNotes5.pdf")[Sutherland, Lecture5, Theorems5.8 and5.25: separable degree and [2].]

Local sources: crypto/successor-preflight/src/two_primary_quotient.rs; lean/TwoPrimaryQuotient.lean; TWO_PRIMARY_QUOTIENT_PROOF.md; algebra-certificates/src/main.rs. Exact hashes and full primary/API review are beside the protocol (3da2fc). KB status/four queries/theorem fallback returned127; the autoresearcher vault is locked. No novelty or absence inference.

Publish NORM_HALVING_PROTOCOL_01.md before new sibling code. Then bounded Rust/Lean correctness (900s build/native; 2GiB serial), preserve every failure, whole replay/CI/custody, complete primitive coverage, and admitted performance work when unblocked. Existing complete-C and historical A/B diagrams were checked and retain their scope; this proposal adds the separate editable diagram above.
