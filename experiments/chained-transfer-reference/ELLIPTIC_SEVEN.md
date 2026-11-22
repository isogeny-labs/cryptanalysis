# Certified degree7 maps for both elliptic factors

Four actual F101 degree7 maps and their normalized duals now pass exact
curve/global dual-x identities and complete109/113-point group controls.
The pre-existing construction engine is unchanged;another unchanged
Montgomery field/polynomial/kernel engine replays every frozen certificate.
PCCa51d74/beeac7/45f608 and crypto7e9547 remain unsigned. These are known
elliptic isogeny algorithms,preparing a genuine Jacobian continuation;
no Jacobian7-hop or computational advantage is accepted yet.
[pcc:unverified]

## Exact sources,kernels and distinct models

E1 is the original full-order109 source y²=X³+X+46. The accepted quadratic
cover uses U=X−2. E2:y²=x³+13x²+33x+5,order113,has short coordinates
X=x+38,y unchanged,and short coefficients(44,21). The entire101² affine
coordinate bridge is checked. Every valid source point,including infinity,
is covered by both map and recovery tests. [pcc:unverified]

|Order|Source(A,B),j|Degree3 kernel,bottom first|Codomain(A,B),j|Dual kernel|
|---|---|---|---|---|
|109|(1,46),12|[9,76,20,1]|(5,39),91|[49,69,62,1]|
|109|(1,46),12|[72,100,35,1]|(26,58),87|[58,26,58,1]|
|113|(44,21),58|[59,46,8,1]|(69,50),92|[29,88,45,1]|
|113|(44,21),58|[77,86,71,1]|(13,42),89|[42,13,8,1]|

Each source and its two targets have distinct j-invariants,so the targets
are distinct from the source and from each other even geometrically.
Explicit F101 coefficient-scale checks also reject those isomorphisms;
the independent engine repeats that control. Development attempt02 had
mislabelled the existing iso_exists_over helper's unchecked scale candidates
as isomorphism answers. That diagnostic is retained;03 replaces it with
actual equations. The helper and arithmetic engines were not edited.
No incorrect equivalence became an accepted result. [pcc:unverified]

## Exact certificates,duals and global geometric bridge

`src/seven.rs` reuses existing division-polynomial factorization and Kohel
maps. The old finder uses sampled x checks;these alone are not acceptance.
The new verifier requires smooth source/codomain,squarefree degree3 kernel,
no source-branch intersection,division-polynomial membership,coprime rational
numerator/denominator and the exact polynomial identity below.
[pcc:unverified]

For x-map N/D,write S=N'D−ND',D=h². The actual point map is
(N/D,y*S/D²),and the checked F101[x] identity is

    f_source*S²=D*(N³+A_target*N*D²+B_target*D³).

This is a polynomial equality,not evaluation at sampled points. The
nonconstant pointed map extends between smooth projective elliptic curves;
its rational x-degree7 makes it a degree7 separable isogeny in
characteristic101. Those geometric extension/group facts remain written
primary inputs,not a finite-field Lean construction. [pcc:unverified]

Each actual dual kernel is found on the codomain. Its raw model scales to
the source by u=1/7=29,x→u²x,y→u³y. Both coefficient equations are
checked. Both global rational-x compositions are compared with the existing
division-polynomial multiplication map
x([7]P)=x−4*f*g6*g8/psi7². All source/codomain point checks determine
the positive ordinate sign. Equal x-maps of nonconstant elliptic maps
have at most the two global ordinate signs in odd characteristic;these
controls distinguish them. [pcc:unverified]

Both full rational groups have bijective images,all pair additions/scalar
relations and both dual compositions[7]. Source recovery uses inverse78
mod109 or97 mod113 after the dual. Maps read point coordinates,not DLP
labels. Recovering a point does not find its unknown discrete logarithm.
[pcc:unverified]

## Independent replay and immutable source closure

The small TSV fixes all four forward/dual kernels,models,rational maps,
orders and scale. SHA25678f0b33e611113f8b6c8340874c39f153c0620b91a86c8242c606c675a927615.
Crypto example chained_elliptic_seven_reference imports no producer Kohel
or new transfer code. Its pre-existing Montgomery field/poly/kernel engine
independently checks division-polynomial/subgroup closure,Vélu codomain,
exact curve and both global x identities,and all109/113 point norms,
bijections,j/coordinate controls. Local example replay passes.
[pcc:unverified]

The same verifier harness also passes as tests/seven_independent.rs through
a thin dependency adapter. This is one independent implementation with two
entrypoints,not two independent verdicts. Both arithmetic engines are
unchanged at crypto75a737b8:seven-reference.sha256 binds102 existing
construction inputs;seven-independent.sha256 binds five verifier modules.
The original seven native runtime guards stay distinct. Registered CI
checks out both exact closures;Cargo.lock pins adapter dependencies.
[pcc:unverified]

Adapter workspace/formatting errors were fixed before acceptance. The
adapter uses ordinary dependency cfg and does not change upstream test
modules or algorithms. The first format diff and all mathematical attempt
receipts remain preserved. Strict Clippy,formatting and all source guards
pass;no lint exemption or arithmetic engine change. Harnesses/receipts are
producer-run and unsigned,so this is not an independent signed scientific
verdict. [pcc:unverified]

Four crypto EllipticSeven.lean lemmas pass gate4,PCC58dbb8: general cleared
long-to-short translation,coordinate scaling and the two inverse7 recovery
identities. Total72 written project lemmas. They do not construct kernels,
division polynomials,elliptic geometry or any Jacobian7-map. [pcc:unverified]

## Validation and continuing task

New targeted full-map/dual tests,independent replay,source guards,formatting
and strict Clippy pass. Complete current native25/reference51-unit-plus2-
integration CI is pending;one old benchmark remains ignored. Prior75e5064d1
exact-head43030710539 passes native25/reference50-unit-plus1-integration
(PCCceb332),andPR1482 merged29c4d7206 at13:48:49Z. Do not relabel that
immutable receipt as the current matrix. [pcc:unverified]

Run consumer check.sh with Rust1.99.1 and pinned sibling sources. Targeted:
actual_seven_kernels_duals_global_identities_and_full_groups and
`--test seven_independent`. Root:cargo test --release --example
chained_elliptic_seven_reference. Reports/diagram/every PDF page inspected.
Source receipts:elliptic-seven-01/02/03/04,independent-seven-ci-01/02/03,
seven-source-guards-01,elliptic-seven-clippy-final-01 and wrapper format
attempts. Exact current-head CI remains next. [pcc:unverified]

CT20 now uses the four pairs of actual elliptic maps in compatible
genus2 gluing. It must check actual two-torsion matching,global kernel
factorization,twist/coordinate descent,duals,all rational classes and
original order109 preservation before accepting a genuine Jacobian7-hop.
Direct elliptic and original-source controls remain mandatory. A different
model or ambient group alone demonstrates no computational advantage.
[pcc:unverified]

The algorithms are prior art:existing code implements Vélu/Kohel and
division-polynomial methods. Direct Kohel thesis retrieval failed;that
primary source is not falsely marked read. Reviewed Milne geometric
inputs and exact identities/independent replay support the stated scope.
No benchmark,solver,paid job,novelty or cross-prime descent claim.
S3/live-budget,KB/vault and crypto frozen-ledger/archive blockers remain.
[pcc:unverified]
