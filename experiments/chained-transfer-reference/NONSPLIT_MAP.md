# Operational non-split Richelot map over F17

The fixed prototype in `src/nonsplit_map.rs` now evaluates the frozen
determinant11 correspondence and its sign-corrected dual on every rational
balanced source/target class. The complete guarded suite passes native25 and
reference43 tests, one existing benchmark ignored, formatting, strict Clippy
and immutable runtime guards. Claims383894/bd303e remain unsigned/unverified.
This is an executable same-field DLP-preserving transfer, with no demonstrated
computational advantage or cross-prime descent. [pcc:unverified]

## Fixed chain and actual domains

    E/F17: y²=x³+2x+2, #E=19, G=(5,1).
    C: y²=x^6+2x²+2, #Jac(F17)=285.
    Ct: Y²=z^6+3z^5+7z^4+4z³+11z²+12z+3, #Jac(F17)=285.

The elliptic whole-fiber pullback is the bounded balanced quadratic map.
The Richelot factors lie in `F17[T]/(T³+2T+2)`, with six roots ordered as
the three Frobenius conjugates of the first encoded β²=T and their negatives.
The frozen pairing is(0,4),(1,5),(2,3), δ11. The raw target has coefficient
array[10,6,14,2,12,10,9], with raw ordinate w=3Y. The other nondegenerate
kernel's target is reflection-equivalent, as retained in NONSPLIT_KERNELS.md.
Source and target curves are F17-nonisomorphic by the complete earlier PGL2
audit; no unpolarized-Jacobian distinction is inferred. [pcc:unverified]

Map inputs are checked canonical balanced classes, with exact model/field
tags and both infinities. No map reads an unknown scalar or calls a DLP
solver. The full finite domain is285 classes in each direction, not all
classes over extension fields or other primes. [pcc:unverified]

## Evaluation and descent

Finite source support of degree≤2 splits over F17². Combining it with the
F17³ factor coefficients uses F17⁶. The prototype stores a+b*s over the
cubic quotient, s²=3, using the unchanged BigUint polynomial layer.
Irreducibility of the cubic and the nonsquare adjunction are checked.
The target fiber stays a quadratic Mumford pair, so it needs neither a chosen
target root nor an F17¹² splitting. [pcc:unverified]

For each source point, the actual correspondence is

    U(z)=G1(x)H1(z)+G2(x)H2(z),
    V(z)=G1(x)H1(z)(x−z)/(y*3) mod U.

Repeated support retains multiplicity. Degree-drop fibers include the proper
target infinity, and zero-y branch cases use the completed correspondence.
Source infinity uses the leading-coefficient limit. All intermediate pairs
are validated on the monic target and added using balanced arithmetic over
the compositum. For finite support degree m and plus-infinity count n, the
completed class is `Σψ(P)+(2n+m−2)ψ(∞+)`, relative to K=∞++∞−. Individual
fiber classes may have extension coefficients; descent is checked only after
the complete balanced sum. Every reduced output must descend coefficientwise
to F17 and pass the separate prime-field class validator. [pcc:unverified]

The dual reverses G/H, reads source ordinate3Y, outputs the original source
scale1 and negates to obtain positive doubling. All285 source classes satisfy
dual-after-map=[2], all285 target classes satisfy map-after-dual=[2], and
paired additivity holds. The map has285 distinct rational images. Its
geometric degree4 is distinct from its rational kernel cardinality1; the
odd rational class group makes doubling invertible. [pcc:unverified]

All19 elliptic source scalars pass the chain; the final image is nonzero of
order19. Reversing the Richelot hop then applying the first source norm gives
[4] on E, recovered by inverse5 modulo19. This recovers source points; it
does not calculate their discrete logarithms. [pcc:unverified]

## Independent arithmetic and formal algebra

The crypto replay imports **none** of the new field or map code. Its
pre-existing `src/bin/icprog/b5a.rs` flat Fp⁶ engine and Rabin checker replay
128 frozen products, inverses and Frobenius powers, with exact seed-coordinate
checks. The independently checked flat modulus is

    γ^6+12γ^4+4γ³+14γ²+10γ+14,
    γ=T+s, s=(γ³+11γ+2)/(3γ²+5), T=γ−s.

This changes both field representation and arithmetic implementation. The
engine is unchanged; only a unit test/fixture is added. Crypto claim167595
binds the passing replay and TSV. It validates the bounded extension layer,
not independently the entire Jacobian map. Both balanced group engines use
Cantor, and all harnesses/receipts are producer-authored and unsigned.
[pcc:unverified]

Four generic core Lean lemmas in crypto `RichelotAlgebra.lean` compile,
gate7 declarations, claimf7eb4f. In particular, for arbitrary quadratics

    Σ Gi(x) [G'j Gk−Gj G'k](z) = −δ(x−z)².

After normalized division by nonzero δ, the correspondence equation implies
G3H3=−(x−z)². Together with the source and ordinate equations this gives the
denominator-cleared target-curve identity. The other lemmas check balanced
infinity accounting and inverse5 recovery under19-torsion. They do not
construct finite fields, projective extension, Picard maps or the dual as a
global geometric morphism. Those remain written inputs from Kunzweiler
§§3.1–3.2/Propositions7–8 and Galbraith corrected ch.8§8.3/ch.10§10.4.2.
[pcc:unverified]

## Reproduction, failures and next task

From cryptanalysis, run `experiments/chained-transfer-reference/check.sh`
with Rust1.99.1 on PATH and the unchanged crypto75a737b8 runtime closure.
Receipt nonsplit-map-pinned-01.txt freezes the43-test reference replay.
The first map-development run passed but had an unused-import warning;
cleanup and strict Clippy subsequently pass. The first new Lean file failed
on a variable-scalar module tactic; explicit module rewrites fix it without
new axioms. Both proof attempts are retained. [pcc:unverified]

From crypto, run `cargo test --release --bin icprog
chained_nonsplit_compositum_witnesses -- --nocapture`. The existing sparse
checkout script discovers the committed TSV automatically; its minimal
profile includes that exact compile-time fixture. No new field arithmetic
was added to the reference engine or frozen B5a benchmark code.

The subsequent [CT15 shifted109 checkpoint](SHIFTED109.md) now evaluates
the frozen shift2 source with full12,317-class dual/descent controls. This
supersedes the earlier prospective shift plan, without changing this F17
receipt. The cover family was already in the Enge study; its unshifted6-cycle
negative and equivalent targets stay retained. Production/catalog integration, larger fields,
extension-field class coverage and signed independent validation remain open.

No benchmark, solver comparison or paid job ran. S3 admission and live IsoLab
budget/capacity remain unavailable; KB and encrypted-atlas access remain
blocked. Crypto PR3877 stays ledger/history/archive-gated. Canonical transfer
and leaderboard graphs are unchanged: no signed scientific or measured cost
edge is promoted. Larger ambient Jacobians alone supply no cost advantage.
[pcc:unverified]
