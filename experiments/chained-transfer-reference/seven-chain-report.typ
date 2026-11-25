#set page(paper:"a4",margin:16mm)
#set text(font:"DejaVu Sans",size:10pt)
#set par(justify:true)
= A genuine seven-isogeny beyond the accepted target
2026-11-11 · Chained ECDLP Transfers · CT21

*Unsigned scientific standing.* Consumer PCC d0441a and root eb3240 bind
the written global proof and native evidence. Psi reaches a Jacobian that
is not isomorphic over F101 to the accepted source. No solver or measured
computational advantage is claimed. [pcc:unverified]

#image("seven-chain.svg",width:100%)

== Exact endpoints and subgroup
The accepted T0 sextic is [31,75,74,54,71,55,1]; the new T1 sextic is
[95,26,19,27,94,91,1]. Both rational Jacobian groups have 12317=109·113
classes. Psi has degree 49 and both polarized dual norms [7]. All 109
original source scalars survive E1→J0→T0→T1, with nonzero image of order
109 and exact scalar relations. [pcc:unverified]

Reversing the chain and applying the source norm gives [28]P, recovered
by 74 modulo 109. Direct target coordinates under N1 R1Hat equal
([4]alpha1(P),0). The naive rational-halving and quarter-coordinate
evaluators agree in both directions on all 109 source points. No unknown
DLP label enters either map. [pcc:unverified]

== Global construction, beyond finite-group halving
The actual Phi2 action transports Ker R0 exactly to Ker R1. The composite
C=R1 Phi R0Hat kills ALL 16 geometric T0[2] classes. The regular quotient
property gives C=Psi[2], uniquely over F101. Degrees give 4·49·4/16=49.
Adjoints give [4]PsiHat Psi=[28] and its reverse; torsion-free HOM
cancellation yields [7]. Geometric point groups retain their two-torsion.
[pcc:unverified]

#pagebreak()
= Geometric evidence and global descent

== Actual kernels and complete two-action
The selected elliptic7 kernels give 49 distinct P0 images, all killed by
7, with all 2401 additions and Frobenius closure. Actual eigenscalars are
5 and 6. These are the full degree49 Phi kernel, not all 2401 points of
J0[7]. All 64 product4-torsion lifts cover the 16 geometric source classes,
four preimages each. Actual target images agree on each fiber and pass
all 256 additions and Frobenius checks. [pcc:unverified]

Transport selects matching (0,5),(1,3),(2,4), determinant 33 and raw target
[78,66,56,53,91,29,88]. The actual normalization w=47Y gives T1.
Both actual R1 rational domains pass dual[2], bijections and paired sums.
The explicit constructor retains matching, field, source-factor,
Frobenius, determinant, descent, smoothness and infinity checks. Six
invalid-geometry controls are rejected. [pcc:unverified]

== Resolve the displayed target's global descent
A stable kernel alone leaves a polarized-target twist ambiguity. For
each actual target, enumerate all 120 unique Möbius maps from one fixed
ordered branch triple to every ordered triple. Only the identity preserves
all six roots. Every geometric branch automorphism is captured, since
three roots determine its coefficients in the splitting field.
[pcc:unverified]

Hyperelliptic geometry and strong Torelli give polarized Jacobian
automorphisms {+1,−1}. Frobenius conjugation of either Richelot map must
differ by one of these automorphisms. A nonzero odd-order rational image
rules out −1. Thus the displayed normalized R0/R1 descend globally to
F101. The code tests the finite branch certificate; Torelli and quotient
geometry remain explicit written dependencies. [pcc:unverified]

== Distinct unpolarized Jacobians
All 12 nonzero elliptic2-torsion intersection controls show the two cross
kernels preserve the elliptic embeddings. Traces −7/−11 forbid cross
F101 homomorphisms and make each trace-type elliptic subvariety unique.
An unpolarized F101 isomorphism T0≅T1 would restrict to E1≅E1',
contradicting j12≠87. Distinct equations alone are not this proof; no
algebraic-closure nonisomorphism is asserted. [pcc:unverified]

== Complete bounded correctness
Both entire 12317-class Psi domains pass full bijections, both dual[7],
canonical coefficientwise descent and 12317 deterministic paired sums
per direction. Every immutable evaluator is run on every class once;
test assertions reuse its actual complete graph. There is no production
corpus lookup and these are not all 12317² addition pairs. [pcc:unverified]

#pagebreak()
= Evidence, formal scope and continuing work

== Native checks and faithful partial formalization
The complete local guard passes native 25 and reference 65 unit tests,
plus two existing standalone integrations; one old benchmark remains
ignored. A third integration for the complete automorphism certificate
and strict all-target Clippy also pass. Source guards and formatting pass.
The existing field, elliptic, gluing and Cantor engines are reused.
[pcc:unverified]

Six ChainTransport and four RichelotDescent helpers pass their Lean4.35.0
gates and all local declaration bindings, with standard foundations and
zero trusted native uses. Project census: 90 written source lemmas.
They prove conditional algebra for the square, norm, sign witness and
scalar inverses. Actual finite fields, Picard functoriality, regular
quotients, polarizations, Torelli and elliptic uniqueness remain written.
The full theorem has not been silently replaced by these helpers.
[pcc:unverified]

== Retain corrections and unsuccessful attempts
Unsigned record 9b9e0a mistyped two source coefficients in its claim
prose. Record 2b4435 corrects it explicitly; every evaluator used the
actual constructor. Receipt10 prints and asserts the correct equations.
The wrong record and its ledger row remain intact. Compile/type, RNG
format and Lean tactic failures are retained alongside passing receipts.
No assertion, axiom restriction, validator or corpus was weakened.
[pcc:unverified]

== Sources and reproducibility
SEVEN_CHAIN.md is the full written proof; SEVEN_CHAIN_STATUS.md maps
every stage to immutable raw receipts and PCC records. Sources are
src/seven_torsion.rs, src/seven_chain.rs and the selected-pairing constructor
in src/nonsplit_map.rs, with exact snapshots. Run check.sh on Rust1.99.1.
Upstream native/seven/separate102/five-input guards remain at 75a737b8.
[pcc:unverified]

Primary texts checked: Kunzweiler Sections3.1–3.2/Lemma6/Propositions7–8;
HLP math/9809210v1 Section3.2; Milne Abelian Varieties v2.0, Remark8.12;
Milne Jacobian Varieties, June2021, Theorem12.1. Exact hashes and formal
gaps are in the proof. Earlier collapse, normalization and forced-backtrack
negatives remain part of the queue. [pcc:unverified]

== Integration and next discriminating task
Parent1484's exact focused CI succeeds, but main61/frozenPhi60 ledger
histories diverge after 56 common rows. Preserve both; no rebase, force,
rechain or gate bypass. Two unrelated C-analysis failures retain actual
diagnostics. Final chain CI remains a separate obligation. [pcc:unverified]

CT22 next derives direct base-field elliptic norms for balanced classes,
including repeated/zero support and infinities, then compares both norms
on every C0/C1 class before integration. This is prospective arithmetic
engineering. S3/livebudget still block benchmark/solver/paid work; KB,
locked atlas and root archival gates persist. Same-prime descent supplies
no cross-prime map, novelty or measured algorithmic advantage.
[pcc:unverified]
