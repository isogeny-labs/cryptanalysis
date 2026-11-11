#set page(paper:"a4",margin:17mm)
#set text(font:"DejaVu Sans",size:10pt)
#set par(justify:true)
= Frobenius-stable kernels: codomain assessment
2026-11-11 · Chained ECDLP Transfers · fixed F17/F101 controls

*Unsigned/unverified standing.* The code constructs kernel splittings and
codomain models. The actual non-split divisor correspondence remains next.
PCC-42713c binds development results. No benchmark or cost gain.
[pcc:unverified]

#image("nonsplit.svg",width:100%)

== Exact F17 outcome
Use predeclared E:y²=x³+2x+2,order19,G=(5,1), with C:y²=x⁶+2x²+2.
In F17[T]/(T³+2T+2), choose β²=T by the first coefficient encoding.
Its three conjugates and negatives give Frobenius(012)(345).
All15 pairings are enumerated;3 are stable. Opposite pairs have δ0.
The two cross pairings have determinants11 and6 and smooth target arrays
shown above. All coefficients descend to F17. Leading9 has square root3;
monic normalization divides the equation by9. Each Jacobian has285 rational
classes. [pcc:unverified]

Both targets are isomorphic by z↦−z,w↦w, so they are one destination.
The full4,896-matrix PGL2(F17) audit finds no curve isomorphism from source
to either target. It finds2 source self-maps on the quotient line and1 for
each target. This is a curve-level distinction, without an unpolarized
Jacobian-isomorphism inference. Higher-degree elliptic maps remain possible.
[pcc:unverified]

== Exact F101 negative
For the existing E109 source y²=x³+x+46, the cubic is irreducible and a root
has nonsquare norm55. Euler's criterion in its cubic field makes that root
nonsquare. Its square roots give a sextic6-cycle. Only the opposite-root
matching is stable; the resulting quadratics X²−αi have zero linear column
and δ0. This specific quadratic cover cannot directly start a nondegenerate
F101-rational Richelot hop to a genus2 codomain. [pcc:unverified]

#pagebreak()
= Proof scope, deduplication and next implementation

The F101 result is a fixture-specific kernel restriction. It does not rule
out shifted/other covers, other degrees, paths through elliptic products,
extension fields or computational transfers generally. The earlier broad
rational-factor limitation is not promoted to universal impossibility.
[pcc:unverified]

Five upstream Lean certificate/accounting lemmas audit the explicit15-row
matching table, its stable filters for6 and(3,3) cycles, the zero determinant
column and odd-norm exponent identity. The5-declaration gate passes;
crypto PCC465142 remains unsigned. Geometric kernel identification and
finite-field norm theory remain written primary-source inputs. No finite
field or actual Richelot map is constructed by these lemmas. [pcc:unverified]

Primary source: Kunzweiler,DCC92(2024),§§3.1–3.2,Lemma6 and Propositions7–8,
DOI10.1007/s10623-024-01366-1. Its normalized determinant/brackets fix twists
and signs. Galbraith corrected ch.10§10.4.2 supplies the balanced model;
ch.8§8.3 supplies Picard norm/pullback. Full account: NONSPLIT_KERNELS.md.
Source: src/nonsplit.rs, reusing pre-existing BigUint polynomial arithmetic.

== Frozen next-map acceptance criteria
Use the first nondegenerate pairing in the complete ordering, δ11, before
evaluating images. Target raw ordinate w=3Y. Combine F17² source support and
F17³ coefficients inside F17⁶. Keep each target fiber as a quadratic Mumford
pair, avoiding target root selection. Handle the balanced infinity terms
and require coefficientwise descent to F17. [pcc:unverified]

Implement the actual correspondence and sign-corrected reversed dual, then
check both dual norms[2] on every285 rational class, additivity, all19 source
scalar relations and reversed-chain/source norm[4] with inverse5 modulo19.
These are prospective tests. Target construction alone is not an executable
ECDLP transfer. [pcc:unverified]

The two equivalent target models and degenerate source pairings remain in
the record. Future chain searches must track them instead of counting each
model as a new Jacobian destination. No cost, solver or prime-field descent
result is inferred from a smooth codomain or preserved odd-group theorem.
[pcc:unverified]

Reproduce with check.sh and the unchanged crypto75a737b8 runtime pin.
Final receipt nonsplit-pinned-02.txt passes guards/formatting/strict Clippy,
native25/reference40 tests and1 existing ignored benchmark. PCC-3c51f5 is
unsigned. Earlier development and complete passing receipts are retained.
[pcc:unverified]

No experiment/paid job launched. S3 checkpoint and live IsoLab budget gates
remain unavailable; KB/atlas retrieval is blocked. Crypto's frozen ledger
fork and archived CI requirements still block PR3877. The persistent queue
is crypto3904; source resume state is CHECKPOINT.md. Canonical leaderboard
and transfer graphs remain unchanged: no signed or measured edge promoted.
