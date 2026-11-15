# Actual fixed F101 degree 49 Jacobian transfer

The native prototype now evaluates Phi:J0→J1 and its polarized dual on
both complete12317-class rational groups. Both signed compositions equal
[7],both maps are bijective,and fixed paired additions pass in both
directions. All 109 original source scalars and direct elliptic-coordinate
controls pass. Full geometric2-kernel certificates and the written quotient
proof supply the global map;halving rational points alone would not.
PCC6a1231/c78fb3 remain unsigned. [pcc:unverified]

## Exact models and existing engines

    F=F101,
    C0:y²=x⁶+6x⁴+13x²+56,
    C1:y²=x⁶+26x⁴+42x²+68,
    J_i=Jac(C_i), #J_i(F)=12317=109*113.

Selected original elliptic factors are E1:(1,46),E2:(44,21),short
coefficients. Their actual7-kernels are[72,100,35,1] and[59,46,8,1],
with targets(26,58)/(69,50). Their normalized duals were already accepted
in the bounded CT19 tests and separately replayed with another unchanged
Montgomery field/polynomial/kernel engine. All new arithmetic is Rust;
the Kohel/FpR,balanced and tower arithmetic engines are reused unchanged.
The seven native input guards,separate102 construction/five independent
verifier guards and crypto75a737b8 source pin remain distinct. [pcc:unverified]

The four gluing models were independently published while this execution
workspace was unavailable:cryptoPR3920,headcc3229d103638190a08d4948b103004cbd567768.
Its historical Python oracle is preserved,not rerun. Native replay agrees
with all four raw models,descent,smoothness,L-polynomial and quotient
identifications(PCCef4a7b). That inventory is prior work,not a new discovery.
Its E2 A/B names reverse our predeclared lexical kernel order:our first
supported pair[1,0] has raw[19,0,86,0,34,0,79],w=33Y and the C1 above.
The other supported monic model[33,0,44,0,92,0,1] remains retained.
Raw leading41/46 are nonsquares;no silent retwist normalizes them.
[pcc:unverified]

The C1 direct/reciprocal elliptic quotients are in SWAPPED order:E2',E1'.
Long-to-short shifts are76/14,and actual target isomorphisms scale(X,Y)
by(21²,21³). Both coefficient equations and entire point-set bijections
are checked. Old C0 shifts are2/38. Ignoring either the swap or the scale
gives the wrong map. [pcc:unverified]

## Global construction and geometric kernel

Let N_i be the two actual quadratic-cover norms in original elliptic-factor
order,and P_i their dual pull sum. The standard involution argument gives
P_i N_i=[2] and N_i P_i=[2]. Let alpha be the product of actual elliptic7
maps. A=P1 alpha N0 has degree 784 and polarized norm[28]. [pcc:unverified]

The code constructs all 16 geometric J0[2] classes as zero plus the fifteen
distinct branch pairs. Actual branch-point norms have graph image4/kernel4.
The old P0 kills that matched graph. Under alpha,the matched pairs in C1
long coordinates satisfy U*V=68;the two pulls have identical supports
x²−U=x²−68/V,ordinate0 and the same balanced infinity count. Actual tower
divisor additions verify P1 alpha N0=0 on every source2-class. Because
char101 is prime to2,these are all points of the finite etale kernel scheme.
[pcc:unverified]

Thus A factors uniquely as Phi[2] through the separable quotient by J0[2],
and uniqueness descends Phi to F101. Its degree is784/16=49,separable.
Taking polarized adjoints gives[4]PhiHat Phi=[28] and the reverse identity;
torsion-freeness of the HOM group cancels[4],giving both global norms[7].
This establishes the genuine(7,7) isogeny before interpreting the rational
halving evaluator. No torsion-freeness of geometric POINT groups is assumed.
[pcc:unverified]

Detailed proof,primary-source hashes and every remaining formal bridge:
[crypto:SEVEN_JACOBIAN_PROOF.md](https://github.com/isogeny-labs/crypto/blob/research/chained-jacobian-transfer-20261110/research/chained_jacobian_transfers_20261110/SEVEN_JACOBIAN_PROOF.md).
Primary inputs read:HLP arXiv math/9809210v1 Section3.2 Propositions3/4/proof;
Milne AV v2.0(2008),Remark8.12;existing SPLIT_QUOTIENTS.md global
pull/norm/involution argument. This uses standard gluing/quotient theory,
not a new transfer theorem. [pcc:unverified]

## Actual evaluation and complete checks

    Phi(D)    =P1 alpha(N0(D)/2),
    PhiHat(Q) =P0 alphaHat(N1(Q)/2).

Half the109/113 elliptic components by55/57. Coordinates undergo the
explicit matched component swap/scales. Maps read coordinates only,not
unknown DLP scalars. Every rational operation is over F101;extension fields
are used in geometric kernel checks. This is same-prime coefficient
descent,not a cross-prime transfer. [pcc:unverified]

|Check|Actually executed coverage|
|---|---|
|Source and target groups|12317 canonical classes EACH|
|Both signed dual[7] identities|Every class in each domain|
|Forward/dual image sets|Each equals the complete opposite corpus|
|Additivity tests|12317 fixed paired additions in each direction;not12317² pairs|
|Original source|All 109 scalars,nonzero image,Jacobian inverse78|
|Reversed elliptic source norm|[14]P;inverse39 mod109 recovers P|
|Direct target coordinates|([2]alpha1(P),0),every source scalar|
|Full geometric2-kernel|All 16 sourceJ0[2] points;graph4/kernel4|
|Elliptic embedding2-torsion|All three nonzero points of each old/new factor|
|Extension pullbacks|444 old/new elliptic points,including4 origins,4 U0 and4 V0 cases|
[pcc:unverified]

Global additivity follows from the morphism argument;finite paired-addition
tests do not replace it. The direct alpha1 elliptic map stays mandatory
in any future computational comparison. No destination solver or timing
comparison was run. Full-test elapsed times are correctness receipts only.
[pcc:unverified]

## Distinct unpolarized F101 Jacobians

Each elliptic pull has kernel contained in E[2],and all three nonzero
geometric2-torsion pullbacks are nonzero/distinct;therefore the elliptic
factors embed. The trace types−7/−11 admit no nonzero F101 cross homomorphism.
Consequently the trace−7 elliptic subvariety is unique in each Jacobian:
it is the identity component of the other norm's kernel. An F101 Jacobian
isomorphism would restrict to E1≅E1',contradicted by j12≠87. This proves
unpolarized F101 distinction using the embedding/uniqueness argument;
j-values alone would not prove it. No algebraic-closure distinction is
claimed. Full written proof is linked above. [pcc:unverified]

## Formalization and identity artifacts

Eight new upstream SevenJacobian.lean helpers pass gate8 and local PCC
b320bb binding:matched supports,kernel fiber constancy,unique FUNCTIONAL
descent/additivity,conditional torsion-free Hom cancellation and source
recoveries[14]/[28] under109 torsion.0 trusted native uses;80 total project
lemmas. Actual finite fields,Picard maps,regular morphism descent,polarized
quotients and elliptic-factor uniqueness are NOT formalized by those helpers.
The full geometric theorem remains the explicit written proof,not a weaker
Lean substitute. Two failed Lean diagnostics are retained before the passing
attempt;no assumptions or axiom policy were weakened. [pcc:unverified]

Native polynomial records IDC1hef947795d0f8d235(scaling) and
IDC1he970a46be821e787(support clearing) check32 issue+16 extra points over
2^61−1,with exact proof-source SHA256 pointers to separately checked core
Lean CommRing statements. Their native checker does not execute Lean or
cover noncommutative Hom composition. Root PCC3ed6c9 records that scope.
CI/replay/Lean compilation and producer agreement do not create signed
scientific standing. [pcc:unverified]

## Evidence and continuing queue

Implementation:src/seven_glue.rs is a child of the existing nonsplit map
module,so extension arithmetic is reused. Raw native inventory02,source03,
complete rational04,geometric kernel05,embeddings06 and exceptional pulls07
are retained in evidence/. Frozen source snapshots03/06 distinguish the
stages. Strict Clippy's first iterator diagnostic is retained;the corrected
iterator preserves the paired-root calculation. Full guarded local matrix
passes native25/reference57 unit+two integrations,one old benchmark ignored;
all guards,formatting and strict Clippy pass(evidence/seven-complete-11.txt).
Exact-head CI remains pending and will be recorded separately. No old receipt is
relabelled as a new-head run. [pcc:unverified]

Next compute all sixteen Phi2-torsion images from64 product4-torsion lifts,
transport the old Richelot cross-kernel,validate R1 and factor the composite
R1 Phi R0Hat through[2] to Psi from the accepted six-cycle target. That next
chain is not claimed implemented by this report. Existing forced-backtrack
negatives remain valid. [pcc:unverified]

Graphs checked:study-local elliptic-seven and split-quotient diagrams remain
historical;this report adds the actual Phi diagram. No independently signed
finding or cost row permits promotion into the canonical scoreboard,
progress timeline,curve graph or encrypted lead atlas. Root frozen ledger/
archive gates,S3 admission/live-budget and KB/ecdb/vault gaps remain open.
No benchmark,paid job or novelty claim. [pcc:unverified]
