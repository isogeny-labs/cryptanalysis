# Shifted full-order109 non-split Richelot transfer

The predeclared shift2 of the existing E109/F101 source admits an executable
non-split Richelot map and dual. All12,317 rational classes in each direction
pass both dual norms[2], coefficient descent, paired additivity and a
12,317-image bijection. All109 source scalar/recovery relations pass.
Claims e580c9/4c335c bind the inventory and complete targeted replay; these
are unsigned development checks, without a computational advantage or
cross-prime descent result. [pcc:unverified]

## Exact models, coordinate bridge and retained alternatives

Original E: y²=X³+X+46, G=(2,37), full group order109. Set U=X−2:

    E': y²=U³+6U²+13U+56, G'=(0,37).
    C: y²=t⁶+6t⁴+13t²+56, #Jac(F101)=12317=109*113.
    Ct: Y²=z⁶+55z⁵+71z⁴+54z³+74z²+75z+31.

The whole quadratic pullback uses U=t². The existing independent elliptic
group engine checks every109 coordinate translation, pullback and norm[2]
relation. Raw point counts on both genus2 models are N1=120,N2=10436;
#J=(N1²+N2)/2−101=12317. The reciprocal elliptic quotient
y²=x³+13x²+33x+5 has order113. The point counter shares the existing Fp2
lineage, so this is not an independent field-layer validation.
[pcc:unverified]

The checked cubic quotient is F101[T]/(T³+6T²+13T+56). A checked square
root β²=T and its conjugates give a3+3 Frobenius action. Of all15 matchings,
3 are stable: opposite pairs have determinant0; the two cross matchings have
determinants63/38 and raw target coefficients
[56,41,62,78,24,57,80]/[56,60,62,23,24,44,80]. Both are smooth and have
Jacobian order12317. The leading80 is22², so raw ordinate w=22Y gives the
monic target above. The second monic target is its reflection z→−z; retain
this equivalence rather than counting a second destination. [pcc:unverified]

The unshifted E109 cover's6-cycle negative remains valid for that exact
model. A change of elliptic coordinate changes the quadratic cover; its
negative is not an obstruction to this shifted construction. The cover
family was already used in the Enge study; no novelty claim is made.
[pcc:unverified]

## Actual map, dual and source recovery

`src/nonsplit.rs` parameterizes checked irreducible cubic quotients, their
deterministic Tonelli–Shanks roots and complete stable-kernel inventory.
`src/balanced.rs` accepts a general monic elliptic cubic for the quadratic
cover. `src/nonsplit_map.rs` derives the actual determinant, factors and raw
scale from that assessment. Checked primes remain5..101, with monic source
and square-leading degree6 targets. Unsupported nonsquare leading targets
return an error; no implicit twist is substituted. [pcc:unverified]

The first nondegenerate pairing is(0,4),(1,5),(2,3), determinant63.
Source support of degree≤2 and cubic factor coefficients are combined in
F101⁶. The correspondence retains quadratic target fibers, multiplicities,
degree-drop/infinity contributions and the completed balanced sum
Σψ(P)+(2n+m−2)ψ(∞+). Descent is checked after summing the complete class.
The sign-corrected dual reads22Y and returns the original source model.
Neither direction reads scalar labels. [pcc:unverified]

The complete targeted test checks all12,317 classes in each direction:
both compositions[2], coefficient descent, bijection and paired additivity.
All109 elliptic scalar relations survive; reversing the Richelot hop and
applying the source norm gives[4], inverted by82 modulo109. This recovers
points, without finding their unknown DLP scalars. Geometric Richelot
degree4 and rational kernel cardinality1 are distinct; odd rational group
order makes doubling invertible. [pcc:unverified]

Precomputed Fp2 roots and zero-class additions keep the bounded correctness
run practical. No timing comparison was made. Future solver accounting must
include field construction, tables, transport, solver, recovery and checking.
No growing-field complexity or advantage over existing ECDLP algorithms
follows from a larger ambient Jacobian. [pcc:unverified]

## Independent field replay and formal scope

Two field-control tests retain the exact frozen F17 TSV and generate128
wide-coordinate F101 witnesses; all10201 Fp2 embedding cases pass. The
pre-existing crypto `icprog/b5a.rs` flat Fp6 engine and Rabin checker replay
both fixtures without importing producer field/map code. For F101:

    γ=T+s, s²=2,
    s=(γ³+6γ²+19γ+68)/(3γ²+12γ+15), T=γ−s,
    γ⁶+12γ⁵+56γ⁴+18γ³+2γ²+46γ+33=0.

The independent engine arithmetic is unchanged; only test/fixture code was
added. Crypto claim5dbc9d binds products, inverses, Frobenius powers and
exact seed checks. This validates the bounded field layer, not independently
the whole Jacobian map. Both group engines use Cantor and all harnesses and
receipts are producer-authored; standing remains unsigned. [pcc:unverified]

Four crypto `ShiftedCover.lean` lemmas pass a4-declaration gate: general
cover expansion, exact original coordinate translation, root-product sign
and inverse82 under109-torsion(PCC7c396d). Existing generic Richelot algebra
lemmas remain available. Neither file constructs finite fields, Picard maps
or a global dual morphism. Geometry remains a written primary-source input:
Kunzweiler DCC92(2024),§§3.1–3.2/Propositions7–8 and Galbraith corrected
ch.8§8.3/ch.10§10.4.2. [pcc:unverified]

## Reproduction, evidence and next obligation

Run `check.sh` with Rust1.99.1 and the unchanged crypto75a737b8 runtime
closure. At this checkpoint, targeted shifted inventory/full map, the three
F17 map controls, both field controls, formatting and strict Clippy pass.
The new full guarded matrix is pending exact-head CI; do not relabel the
older43-test receipt as a current46-test replay. Workflow timeout25 minutes
allows the complete class checks and cold builds. The first inventory
compile failure is preserved beside the successful second attempt.
[pcc:unverified]

See evidence/shifted109-inventory-01.txt/02.txt,
shifted109-map-development-01.txt, generalized-map-controls-01.txt,
field101-controls-01.txt and shifted109-clippy-01.txt. The inspected
shifted109-report.pdf and shifted109.svg show actual directions/domains.
Prior operational F17 source9cd20ac5f passed focused43014776243 and merged
asf387be120; its immutable log is retained(PCCf0e470). [pcc:unverified]

CT16 next computes target Frobenius action on geometric2-torsion and all
stable next kernels, distinguishing any genuine continuation from the dual
backtrack. No target Jacobian nonisomorphism theorem is inferred here solely
from curve models. CT14 production/catalog/large-prime coverage stays open.
S3/live-budget, KB/vault and crypto frozen-ledger/archive blockers remain;
no benchmark, paid allocation or canonical performance edge is promoted.
[pcc:unverified]
