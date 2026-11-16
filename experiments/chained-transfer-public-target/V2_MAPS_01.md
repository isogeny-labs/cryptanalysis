# Actual q223 completed maps and the legacy solver conventions

2026-11-13. Additive P2 implementation under the previously published protocol
7e016c/f888. Native acceptance a5a4a6 is unsigned; the full geometry is written
below, with the existing conditional Lean proof boundaries made explicit.

The new `v2` crate constructs the actual source from `CheckedInstance`. It
reuses the original completed Adapter and canonical Norm bodies, replacing
their fixed-fixture constructors and omitting only the exhaustive toy-domain
enumerators in the new copies. Original V1 admission, all q5/7/11 fixtures,
original engines, N4 source files and frozen P1 remain unchanged. [pcc:unverified]

## Exact objects

K=F223[z]/(z³−3), ell=2773073 and #E(K)=11092292=4ell. The original independent
field/curve/prime checks and the unique Hasse multiple certify this source as
described in the frozen P1 derivation; no new order estimate is substituted.
Native V2 checks all basis products and Frobenius against the original N4
field, and all fifteen normalized plane coefficients equal the actual N4
coefficients. Both use the same Moore basis (1,z,z²), so the actual plane
transport is the identity, with scale1. [pcc:unverified]

The exact plane coefficient vector is
`[0,1,91,68,209,30,216,142,31,72,184,179,36,124,140]` in original descending
degree-four monomial order. The canonical P0 is [1,0,0]. The original winning
factor-base construction (seed102, nfb36) actually chooses [1,74,153]. Both
constructors rebuild their own original normal forms and complete origin
fibre. Field/model tags include the actual representation and P0.

## Source sign and the geometric origin

Write H as y²=t⁴+a t³+b t²+c t+d, B=a/2, s=(b−B²)/2,
alpha=c−2Bs and beta=d−s². The completed short map kappa sends positive
infinity to O and has

    x=2(y+t²+Bt+s), Y=2xt+Bx+alpha, X=x+(B²−4s)/3.

The original N4 map lambda sends negative infinity to O and uses

    v=2t²+a t−2y, w=2t(v+2s)+c+Bv.

Consequently kappa(t,−y)=I(lambda(t,y)), where I(v,w)=(v+b/3,w).
The two short coefficients are checked against the independent original
source curve. If T=kappa(negative infinity), the principal divisor of t−t0
gives kappa(iota P)=T−kappa(P), including ramified multiplicities. Thus
kappa(lambda⁻¹(P))=T−I(P). After subtracting the actual old infinity fibre,
the degree-zero pullback is Phi_old(P)=Phi_new(−I(P)). The signed source
isomorphism is S=−I, with no fitted shift. [pcc:unverified]

In this actual case T=((116,126,164),(133,115,44)); doubling gives
((94,220,17),(137,190,88)). T is not assumed to be two-torsion. At the
winning legacy P0, reduction of the complete fibre at T gives the nonzero
raw origin key
`[1,1,0,118,0,196,191,0,1,91,0,137,202,0,0,0,1,194,7]`.
All sixteen admitted legacy split fibres in the bounded panel equal their
completed raw fibres at that actual P0, and subtracting this geometric
origin gives Phi_new(SP). [pcc:unverified]

## Reference divisors and the two compositions

The original Picard representation uses Dinf=K_C−P0. Changing Pold to Pnew
gives delta=[Pnew−Pold]=Exc_new(Pold). A fixed final degree-three divisor
key acquires +delta; representing the same actual class therefore requires
raw_new(key)−delta. A fixed raw degree-six divisor instead acquires 2delta.
These are different operations: native02 checks

    reduce_new(Z6)=bridge(reduce_old(Z6))+2delta,

as well as zero, inverse, 100 addition pairs and the completed-map bridge.
The actual P0 values are distinct and delta is nonzero. [pcc:unverified]

For the written global composition argument, over K the Ciani curve has
three degree-two elliptic quotients pi_i. Pull-push gives
pi_i* pi_i^*=[2]. The other two cross terms vanish: the quotient involution
fixes the norm and induces −1 on the other elliptic Picard group. The cross
homomorphism is killed by2 and hence is zero, since a homomorphism of abelian
varieties has connected image and cannot have a nonzero finite image.
This proves Norm Phi=[2] after Frobenius descent. Conversely
sum_i pi_i^* pi_i*=sum_i(1+iota_i)=2+sum_g_in_V4 g. The last term factors
through Pic^0(C/V4)=Pic^0(P1)=0, proving Phi Norm=[2]. These statements
concern degree-zero divisor classes, so origin translations induce the
same homomorphisms after the stated corrections. [pcc:unverified]

On the subgroup of prime order ell, multiplication by2 is invertible, with
inverse1386537. Thus the completed transfer is injective there, commutes
with scalar multiplication, and the transported norm followed by this
coefficient recovers the original point. The five actual public requests
pass this round trip at the actual legacy P0. The native affine raw
three-point differences also cancel the nonzero origin on all five targets,
with a nonzero ratio base. No DLP table, inverse enumeration or witness is
used by the map or norm. [pcc:unverified]

## Evidence and limits

Native02 passes one unfiltered comprehensive test, zero failed/ignored/
filtered, all2203 input guards unchanged. It checks 32 source points (eight
odd multiples crossed with the entire actual four-element 2-Sylow), all224
rational C point classes, both [2] compositions on those panels, nonzero
Phi(G) of exact prime order, sixteen legacy split comparisons at each P0,
100 basepoint addition pairs, all224 line offsets, all twelve geometric
quadratic-branch controls and four infinity-sign controls. This is not an
enumeration of E(K) or J(F223). [pcc:unverified]

The actual triple divisor at [1,1,52] has multiplicity3 and changes the norm
if multiplicity is omitted; an alternate chart agrees with the correct
norm. The first triple-divisor control at [1,0,0] has the same norm after
that omission. That null observation is retained; it was not relabelled
as a discriminating negative control. [pcc:unverified]

The nine P1 and five origin Lean declarations remain the same exact local
bindings f68241/d71088; original producer4.35 and consumer4.34.1 gates pass.
They formalize conditional module/ring identities, not actual Picard,
cover, divisor, Hasse or N4 relation-kernel objects. The parent canonical
norm proof map similarly records its conditional assumptions. The written
quotient and divisor interpretation above remains an explicit formalization
gap. No full formal geometry or signed execution claim is made.

Independent P1 replay67baa2 passes all43 phase pairs (29positive0/0 and
14intentional2/0), both original9+5 proof gates and all14 exact bindings,
with435 guards. OwnCI a5a143 succeeds on exact68d22ce; all13 native records
match the original unit after excluding only recorded wall and wall_total
values, and all14 original canonical claim digests match. Whole failed
full01 and rho01 attempts are retained. Rho accessor e5d852 independently
checks all five recovered native and actual CLI answers; its output-only
three substitutions preserve the original walk. [pcc:unverified]

This restricted extension-field family does not establish generic
prime-field ECDLP coverage or computational advantage. The next candidate
replaces individual-descent split-transfer rejection with completed maps;
its map overhead can outweigh the avoided retries. Performance remains
unadmitted without the actual S3 checkpoint and live budget/capacity gates.

Sources: `evidence/v2-native-02`, `evidence/v2-extension-plan-02`,
`v2/source-pins.json`, `evidence/independent-full-02`,
`evidence/independent-CI-02`, `evidence/rho-acceptance-02`, the frozen
`DERIVATION.md` and `PROOF_MAP.md`, original producer
`genus3-prime-descent/lean/Descent.lean`, and parent
`g3-norm-checker/lean/CanonicalNorm.lean`.
