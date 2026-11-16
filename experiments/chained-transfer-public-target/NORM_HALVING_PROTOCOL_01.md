# Prospective norm-halving evaluation of the matched degree-13 transfer

Publish this protocol before implementing the new sibling crate. The question is
whether complete rational beta can be evaluated through elliptic halving of its
norm, and how that route compares with the strongest readily derived
norm-assisted scalar baseline. Correctness and complete accounting precede
performance admission. All new outcomes are pending. [pcc:unverified]

## References and frozen inputs

The review receipt is `evidence/norm-halving-primary-review-01` (3da2fc).
Sutherland, 18.783 Fall2025 Lecture2 section2.2 supplies the ordinary duplication
formulas; Lecture5 Theorems5.8 and5.25 give degree/separability and four geometric
halves in characteristic223. The project already implements the complete
abscissa-quartic selector in crypto's
`successor-preflight/src/two_primary_quotient.rs` and proves the quartic identity
in `lean/TwoPrimaryQuotient.lean`. Read and hash-pin those primary code/proof
sources; reuse the literal selector as an oracle. This protocol makes no claim
to have discovered elliptic halving. [pcc:unverified]

KB status, four mechanism/negative/application/adjacent queries and a theorem
query all returned127; no KB MCP tools were available. The autoresearcher vault
at8edec422 remains locked. No absence or novelty conclusion follows. The primary
and accessible repository review is retained whole. [pcc:unverified]

Keep all881 complete-C reference inputs plus manifest self, all prior844,
arithmetic22 and norm784 inputs, all20 workflows, original engines, old A/B/C
crates, fixture, certificates, goldens, reports, claims and ledger prefixes
unchanged. Add `norm-halving-evaluator/`; do not revise the accepted complete-C
implementation to make comparison easier. The science baseline is b691714c;
cc69f16 adds data hydration only. Preserve its automatic CI and original b691
PCC failure separately. [pcc:unverified]

## Exact domain

Use only the matched HLP(1,0) models and the original F223 field presentation.
K=F223[z]/(z^3-3); L=F223[w]/(w^6-3), z maps to w^2. On E/L the base-K
Frobenius is the third power of coordinate F223 Frobenius. Use both actual source
curves, the original rational degree13 isogeny and its actual dual, and the
unchanged complete quadratic fibre/Picard maps with their actual origins and all
three conjugate ideals. [pcc:unverified]

E has a=(214,144,205), b=(137,218,9); E13 has a=(196,168,69), b=(8,82,207).
J0 model is
`Ciani-Jac-pi0-v2-3ba99ad5742ad62540f8addbbe153572696d2e595f64cd2c1b0b52e51ff351a4`;
J1 model is
`Ciani-Jac-odd-product-v1-7ea9d0f9d1a48a48489425beab48274fca7bd0848e47a0bac3a027c01601e2c4`.
Reuse the full quartics, monomial order, P0s, field tags and five public targets
from the frozen complete-C records; do not silently identify classes across
origins or models. The rational group has recorded order N=11092292=4ell,
ell=2773073. Global geometric/order/Picard bridges retain their existing written
and native scope. [pcc:unverified]

## First comparison arm: strengthen the scalar baseline

Let Phi_j and N_j be the complete quotient and norm, and let
Psi=Phi_1 gamma in the forward direction (reverse with the actual dual).
The old evaluator forms x2=[ell]x, xo=x-x2, and
`[1386537] Psi(N_0(xo)) + beta(x2)`, with its large scalar on the Jacobian.
The stronger baseline to implement first is

    baseline(x) = Psi([1386537] N_0(x)) - beta(x2), x2=[ell]x.

Since 2*1386537=ell+1 and N/Phi commute, the term before subtraction is
beta((ell+1)x)=beta(x)+beta(x2). This moves inverse-two multiplication to E(K)
while retaining the one CRT projection on J0. Use the existing complete-C
cofactor table as an explicitly charged baseline setup/reference, and validate
the formula against complete-C on every declared input. No inverse-two
Jacobian baseline alone is an adequate comparison. [pcc:unverified]

Both arms must have the same encoded-class admission. Distinguish common
admission (including any full-order scalar check) from transfer-core work; do
not suppress its cost or claim that the entire entrypoint has no large
Jacobian scalar if common admission still uses one. Constructor validation,
origins, source models and verification remain included and unpriced until
complete primitive coverage and admitted measurement exist. [pcc:unverified]

## Candidate: halve the norm and repair its two-torsion ambiguity

For x in J0(F223), compute Q=N_0(x) in E(K), then all four actual halves a in
E(L). First justify a correct lift a0 in this SAME elliptic domain, with
Phi_0(a0)=x and [2]a0=Q. The existing complete-C rational decomposition supplies
an explicit written existence route: an odd class lifts in E(K) by inverse-two
times its norm, and every one of the four rational cofactor classes has its
actual E[4](L) lift. Add these lifts using the full-order/cofactor and commuting
square hypotheses. That existence proof may use ell even though the candidate
transfer core avoids the CRT calculation. A geometric Weil-restriction
surjection alone does not supply a single elliptic lift without this domain
bridge. [pcc:unverified]

Any other half of Q then differs from a0 by E[2]. Full E[2](K) makes these
differences rational over K; separately, the K-Frobenius acting on a halving
torsor squares to the identity. State both arguments and their hypotheses
explicitly. All E(L) is not the preimage subgroup of J0(F223).
[pcc:unverified]

Precompute the actual images of all four E[2](K) points under Phi_0 and Psi,
checking every collision gives the same matched beta image. For each selected
half calculate d=x-Phi_0(a). Admit only an actual dictionary entry Phi_0(t)=d
with t in E[2](K), and return Psi(a)+Psi(t). Independently test the equivalent
route using the corrected lift a+t. Require the same answer for all four
halves, compare complete-C and the stronger baseline, and repeat both
directions. No odd-DLP table, input scalar witness, search through the large
rational group or source recovery oracle may enter evaluation. [pcc:unverified]

## Complete coordinates and exact algebra

For Q=(u,v), E:y^2=X^3+A X+B, use the existing quartic

    H(X)=X^4-4uX^3-2A X^2-4(Au+2B)X+(A^2-4Bu).

For v nonzero, independently derive and check

    T=X^3-3uX^2-A X-Au-2B, Y=T/(2v),
    T^2-4(u^3+Au+B)(X^3+A X+B)=H(X)(X-u)^2.

The first identity
`(3X^2+A)^2-4(X^3+A X+B)(2X+u)=H(X)` already has the project's universal
ring proof. Reuse it, and prove the ordinate identity over a general
commutative ring with ordinary Lean kernel checking. Native exact-Z coefficient
expansion and the original identity issuer/checker are additional independent
controls, not formal geometry. Retain a missing-term negative, the whole
certificate and both original verifier outcomes. [pcc:unverified]

When Q=O use all E[2](K). When v=0 use the actual E[4](L) panel or the literal
complete old selector, allowing two distinct X roots with two ordinates each.
Never assume four distinct abscissas in that case. Sort canonically, deduplicate
points, require exactly four, check on-curve and [2]a=Q, and compare with the
literal old selector on every chosen test Q. The generic ordinate formula must
reject v=0 rather than divide by it. Use source isogeny rational functions only
on their admitted domain; preserve or explicitly handle denominator/pole
checks, including the fixed-field fact relevant to degree13. [pcc:unverified]

## Native controls and proof obligations

Run unfiltered bounded Rust unit targets. Cover all original448 rational
exceptional classes (224 each model), all48 mixed sector cases from complete-C,
all five public targets in every rational cofactor sector, the original
cofactor group, both degree13 compositions, the original F=2beta identity,
full-group inverse and every declared source-recovery check. Retain each full
row, all four lifts, differences/corrections and each arm's output, including
failures. Every emitted proposed answer is checked on the actual destination
and independently on its source where the original interface supplies that
check. [pcc:unverified]

Include infinity, all nonzero source two-torsion and four-torsion norm cases,
actual non-K halves, F^3 and wrong coordinate-F controls, incorrect cofactor
correction, wrong matched model/origin, omitted whole output records, zero
denominator and a changed quartic term. Reuse the existing basis/ring controls;
do not count a compiler error or missing executable as a mathematical negative.
All native JSON comparison is Rust, whole-tree and without new ignored fields.
[pcc:unverified]

Lean targets must faithfully state: halving-torsor Frobenius rationality under
explicit two-torsion hypotheses; arbitrary lift difference is two-torsion;
the correction evaluator equals the quotient-induced beta; independence of
the four halves; and the optimized baseline identity under explicit group
order/cofactor/commuting-square hypotheses. Reuse existing DLP equivalence
and inverse13 results without inflating them into a formal construction of the
actual geometry. Both original gates and exact statement-binding checkers must
check the actual sources; no holes, custom axioms, trusted native shortcuts or
assumed evaluator-correctness conclusions. [pcc:unverified]

## Accounting, limits and decision

Record actual selected call-site counts for setup, common admission, norm,
quartic factorization, ordinate handling, full quadratic Phi/Psi, source
isogeny, correction and output verification on both arms. Identify every
unpriced primitive/context operation. Counts of selected entries are not
a complete cost ledger, calibrated benchmark or speedup. Timing requires the
existing frozen end-to-end protocol, isolation/budget/capacity, tested image
binding and matched IC/rho/precomputation references; those admissions remain
unavailable, and no paid job is authorized by this document. [pcc:unverified]

Use existing pinned Rust1.99.1 and Lean4.34.1/4.35.0. Correctness build/native
bounds are900s each, serial native with2GiB address-space bound, auxiliaries120s,
fresh output and cache or an explicitly retained warm development cache. Keep
actual compiler-reported executed binaries, raw stdout/stderr, commands, exits,
whole certificates, source hashes and unchanged881+self882 guards. Before
retries retain the entire failed attempt and change only its diagnosed cause.
Source protocol/checkpoint publication precedes the new code; complete source
publication precedes fresh independent replay and own-source CI. [pcc:unverified]

If the correction dictionary, complete halving, field descent or any equality
fails, preserve the full counterexample and identify the exact missing
hypothesis. If correctness passes, record complete rational norm-halving as an
implementation component and proceed to whole replay/CI/custody and primitive
coverage. An elliptic quartic root computation may outweigh eliminated scalar
work; the stronger baseline remains mandatory. No computational advantage is
concluded by this protocol. Then continue the next unblocked chained-map or
prime-field task. [pcc:unverified]
