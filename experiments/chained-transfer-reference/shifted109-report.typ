#set page(paper:"a4",margin:17mm)
#set text(font:"DejaVu Sans",size:10pt)
#set par(justify:true)
= Shifted full-order109 Richelot transfer
2026-11-11 · Chained ECDLP Transfers · predeclared shift2

*Unsigned/unverified standing.* Complete12,317-class source/target checks
and all109 source scalar relations pass. This is a bounded same-field
DLP-preserving transfer, without a solver or demonstrated cost advantage.
PCCe580c9/4c335c bind inventory/full targeted replay. [pcc:unverified]

#image("shifted109.svg",width:100%)

== Models and the retained unshifted negative
Start with E:y²=X³+X+46,G=(2,37),full order109 overF101. Set U=X−2;
the exact cubic becomes U³+6U²+13U+56 and quadratic cover
y²=t⁶+6t⁴+13t²+56. Point counts N1=120,N2=10436 give
Jacobian order12317=109·113. The reciprocal elliptic quotient has order113.
Every109 original/shifted coordinate and pull/norm relation is checked.
[pcc:unverified]

All15 root matchings are considered. Three are Frobenius stable:1 degenerate
and2 smooth targets, with determinants63/38. Both have leading80=22² and
Jacobian order12317. After raw w=22Y, the first monic coefficients are
[31,75,74,54,71,55,1]; the second target is its reflection. Retain that
equivalence. The unshifted cover's6-cycle obstruction remains valid for its
exact input, not for every shifted cover. This family is prior Enge art.
[pcc:unverified]

== Actual maps and recovery
The map uses cubic factor coefficients and quadratic source support inF101⁶.
It retains whole quadratic fibers and balanced infinity contributions before
checking prime-field descent. The sign-corrected dual reads22Y. All12,317
classes in each direction satisfy both compositions[2], paired additivity,
coefficient descent and a12,317-image bijection. [pcc:unverified]

Every109 source scalar relation survives. Reverse Richelot then source norm
gives[4], recovered by82 modulo109. These recover points, not unknown DLP
scalars. No map reads scalar labels. Geometric degree4 and rational kernel
cardinality1 are distinct. No Jacobian nonisomorphism is inferred solely
from curve models at this checkpoint. [pcc:unverified]

#pagebreak()
= Independent arithmetic, proof scope and reproducibility

The producer checks all10201 Fp2 embeddings plus128 wide-coordinate tower
witnesses. A separate pre-existing crypto flat Fp6 engine imports none of
the new field/map code and independently checks the primitive bridge and
Rabin irreducibility. For gamma=T+s,s²=2:

    s=(gamma³+6gamma²+19gamma+68)/(3gamma²+12gamma+15),
    gamma⁶+12gamma⁵+56gamma⁴+18gamma³+2gamma²+46gamma+33=0.

Both128-case F17/F101 product,inverse,Frobenius fixtures replay with exact
seed checks. The F17 fixture remains byte-for-byte unchanged. Existing field
engine arithmetic is untouched; only tests and one new immutable TSV were
added. Crypto PCC5dbc9d binds the passing replay. This validates the bounded
field layer, not independently the entire Jacobian map. Both group layers
use Cantor; producer-authored harnesses/receipts remain unsigned.
[pcc:unverified]

Four new ShiftedCover.lean lemmas pass a4-declaration gate(PCC7c396d):
general quadratic-cover expansion, exact translation, root-product sign and
inverse82 under109-torsion. Existing generic Richelot algebra remains
available. Finite fields, projective/Picard maps and global dual geometry
are not formalized. Written primary inputs remain Kunzweiler DCC92(2024),
§§3.1–3.2/Propositions7–8 and Galbraith corrected ch.8§8.3/ch.10§10.4.2.
[pcc:unverified]

== Reproduce and preserve exact evidence
Consumer check.sh uses unchanged crypto75a737b8 runtime guards,Rust1.99.1,
formatting,strict Clippy,native25 and the reference suite. At this checkpoint
the complete shifted targeted map/inventory,three retained F17 map controls,
both field controls and strict Clippy pass. Current full46-test guarded CI
is pending; the older43-test receipt is not relabeled. The registered
workflow allows25 minutes including cold builds. [pcc:unverified]

Root: `cargo test --release --bin icprog chained_ -- --nocapture`.
Two independent field tests pass. The minimal sparse profile discovers
both tracked compile-time TSVs. Lean proof-gate.sh runs ShiftedCover.lean.
Retained receipts include shifted109-inventory-01/02,
shifted109-map-development-01,generalized-map-controls-01,
field101-controls-01 and shifted109-clippy-01. The initial inventory compile
failure is preserved. Full account/source: SHIFTED109.md,src/nonsplit.rs,
src/nonsplit_map.rs,src/balanced.rs. [pcc:unverified]

== Next bounded obligation
CT16 assesses target Frobenius2-torsion and all stable next kernels. Preserve
any forced dual backtrack and equivalent codomain. Production/catalog,large
primes,extension class coverage and signed independent validation stay open.

No benchmark,solver comparison or paid job ran. Construction,transport,
solver,recovery and checking must all enter any future cost comparison.
S3/live-budget,KB/vault and crypto frozen-ledger/archive gates remain.
No growing-field complexity gain,cross-prime descent or canonical cost edge
has been established. [pcc:unverified]
