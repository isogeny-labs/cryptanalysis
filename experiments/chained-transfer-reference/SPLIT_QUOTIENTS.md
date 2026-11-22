# Explicit elliptic coordinates for the accepted rational groups

Both accepted odd-order source Jacobians now have executable two-elliptic
quotient coordinates and an inverse on their complete rational groups.
Every285 F17 and12,317 shiftedF101 class passes reciprocal completion,
both norm additions,cross-norm zero,sum of pull/norms=[2] and reconstruction.
Every transferred source scalar has coordinates([4]P,0) after Richelot dual.
PCC036d81/96b1e2 bind unsigned correctness receipts. This exposes direct
source controls,without a DLP solver or measured advantage. [pcc:unverified]

## Actual reciprocal coordinates and complete divisor map

Write C:y²=x⁶+a2*x⁴+a4*x²+b,with b=s² nonzero. The coordinate change

    T=s/x, Y=b*y/x³

gives C':Y²=T⁶+a4*T⁴+a2*b*T²+b². Its inverse is
x=s/T,y=s*Y/T³. Thus C' has the second quadratic quotient
E2:v²=u³+a4*u²+a2*b*u+b²,u=T². The first quotient remains
E1:y²=u³+a2*u²+a4*u+b,u=x². These are genuine Fp coordinates,not an
unrecorded twist. Nonsquare/zero b is explicitly unsupported by this adapter.
[pcc:unverified]

`Reciprocal` actually checks the monic target coefficients for general
T=a/x,Y=kappa*y/x³. For source finite support u(x),v(x),degree m≤2:
take monic(T^m*u(a/T)) and v'=kappa*T³/a³*v(a/T) modulo the new support.
Degree lost at x=0 is retained as target infinity with branch
kappa*v(0)/a³=±1,including multiplicity2. Source infinities instead map to
finite points(T=0,Y=±kappa). The pushforward of K is their hyperelliptic
fiber,linear-equivalent to the new K. [pcc:unverified]

For degree m and source plus-infinity count n,the class is assembled from
the finite transformed block,its lost-plus multiplicity times delta,and
n copies of(0,kappa) plus2−m−n copies of(0,−kappa),each relative to new
infinity-minus. This is a complete divisor calculation; dropping zero support
or treating the old infinities as target infinities gives incorrect maps.
All three zero-support multiplicities0/1/2 and every rational class are
covered by both reciprocal inverse and paired-addition tests. [pcc:unverified]

## Pull/norm identities and full rational-group reconstruction

Let sigma(x,y)=(−x,y),and let iota be the hyperelliptic involution.
The first quotient is by sigma; the second is by iota*sigma. On Jac(C),
iota induces−1. Hence P1*N1=1+sigma and P2*N2=1−sigma,so

    P1*N1+P2*N2=[2],  Ni*Pi=[2],  Ni*Pj=0 for i≠j.

The cross-norm relation follows from the opposite involution eigenspaces;
a homomorphism of elliptic varieties killed by2 is zero. The standard
degree2 pull/push construction and this geometric involution identification
remain written primary inputs,not formalized Picard geometry.
[pcc:unverified]

Define N=(N1,N2),P(a,b)=P1(a)+P2(b). Then PN=[2] and NP=[2].
On the fixed odd rational groups,half each elliptic component and apply P
to reconstruct every original class. The API requires explicit odd
annihilators and checks each input point is annihilated; it does not silently
treat caller-supplied integers as certified group orders. [pcc:unverified]

|p|Source coefficients,bottom first|E1/E2 orders|Complete source classes|
|---|---|---|---|
|17|[2,0,2,0,0,0,1]|19/15|285|
|101|[56,0,13,0,6,0,1]|109/113|12317|

The test independently counts both elliptic point sets with the pre-existing
BigUint curve arithmetic. All norm-pair images are distinct,with the full
product cardinality,so these are explicit rational-group isomorphisms.
This does not assert that the underlying abelian varieties are isomorphic
to those products. Rational-group bijections and variety isomorphisms are
different claims; the earlier source/target Frobenius distinction remains.
[pcc:unverified]

## Accepted target coordinates and direct DLP controls

For the accepted Richelot R and sign-corrected dual Rhat,put
M=N*Rhat and S=R*P. The already checked dual/pull identities give
MS=[4] on E1×E2 and SM=[4] on the target. Odd rational orders therefore
give an explicit inverse by quartering components before applying S.
This extends the complete source decomposition through the accepted map;
it is a written consequence of the complete individual identities.
[pcc:unverified]

In particular M(R(P1(P)))=([4]P,0). All19/109 source scalars check that
identity,zero second component,source recovery by inverse5/82,and split
reconstruction of the reversed class. No function reads an unknown scalar.
The second elliptic factor supplies no additional DLP equation for this
transferred subgroup. Generic algorithms still face the same subgroup
order r; merely enlarging the ambient group supplies no generic-query
advantage. A future non-generic destination solver would need its own
complete measured cost comparison. No such solver or gain is supplied here.
[pcc:unverified]

## Formal algebra,evidence and validation scope

Seven upstream `SplitQuotients.lean` lemmas compile/gate7,PCCfffa35:
denominator-cleared reciprocal curve/inverse,complementary norm sum,generic
odd-annihilator halving,conditional split reconstruction,and target
coordinates([4]P,0). Two broad algebra-tactic failures are retained; the
passing proof uses explicit power equalities with unrelated hypotheses
removed from local ring normalization. No axiom was added. Finite fields,
group orders,Jacobian/Picard maps and actual geometric splitting remain
written inputs. Total62 written project lemmas. [pcc:unverified]

New targeted all-class decomposition,full source-component controls,
formatting and strict Clippy pass. Raw proposal/receipts are
split-quotients-proposal-01.txt,split-quotients-01.txt,
split-target-components-01.txt and split-quotients-clippy-01.txt.
Current full49-test CI is pending. Prior CT16 source63cf80560 passes
exact-head focused43024621372:native25/reference47,1 old benchmark ignored,
formatting/strict Clippy/guards(PCCbfa6ff). That immutable receipt is not
relabeled as a current49-test replay. [pcc:unverified]

Run consumer check.sh with Rust1.99.1 and unchanged crypto75a737b8 runtime
guards; or select the two new tests by complete_split_quotients and
accepted_target_elliptic_components. The source is src/balanced.rs and
src/nonsplit_map.rs. The diagram and every page of split-quotients-report.pdf
are inspected before publication. [pcc:unverified]

Next consider rational odd-prime maximal-isotropic kernels as alternatives
to the closed Richelot neighbors; any actual map must preserve the original
odd subgroup and include direct elliptic controls. Production/catalog/large
fields and all solver-cost obligations remain open. S3/live-budget,KB/vault
and crypto frozen-ledger/archive blockers persist. No benchmark,paid job,
novelty,prime-field attack or cross-prime descent claimed. [pcc:unverified]
