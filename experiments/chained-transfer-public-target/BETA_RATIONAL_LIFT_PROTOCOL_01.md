# Matched odd-degree quotient: rational lifts and complete rational-point evaluation

Prospective before new Lean/Rust implementation. Base scientific consumer398d591b,
producer3d49af7f and every original785 input stay immutable. Existing arithmetic
reference03/22+self23, golden7113-row census and old18 workflows stay unchanged.
Sources checked are pinned in evidence/beta-rational-lift-primary-review-01.
KB unavailable (wrapper127); vault8edec422 locked. No novelty inference.
[pcc:unverified]

## Question and acceptance scope

The written matched HLP(1,0) quotient has global beta with beta Phi0=Phi1 gamma,
degree13^3, F=[2]beta and dual compositions[13]. Complete rational beta evaluation,
especially on the rational cofactor-four classes, is missing. Odd-subgroup halving
alone does not close that requirement. Work toward evaluation on every rational
Jacobian class, preserving the full global-coordinate requirement separately.
No beta factorization is assumed for unmatched HLP(1,1)/(2,1).
[pcc:unverified]

## A. Rational-lift implication and torsion coordinates

Let Phi:A→J be a surjective homomorphism commuting with Frobenius F, with kernel
annihilated by2 and F^3=1 on that kernel. For rational x, choose a geometric lift a
and set c=F(a)−a. Test/prove that a'=a+F(c) still lifts x and is fixed by F^2.
Use only explicit ordinary abelian-group/homomorphism laws in a faithful Lean4.34.1
module; quantify over every rational x, expose geometric surjectivity and all
Frobenius hypotheses. Audit #print axioms and the original proof gate; no holes,
custom claim axioms, native_decide or assumed rational-lift conclusion.
[pcc:unverified]

Prove lift-image independence from kernel containment and the four-torsion bound
when N Phi=[2] and N(x) has exponent2. Keep actual geometric/group bridges explicit.
Exhaustively test the finite-group control A=C4×C2, Phi(a,b)=a mod2,
F(a,b)=(a+2b mod4,b+a mod2): kernel exponent2 and rational target hold, but F^3 on
the kernel need not be identity and the nonzero target should have no F^2-fixed
lift. This is an abstract finite-group control, not an asserted abelian-variety
counterexample. Preserve an unexpected result.
[pcc:unverified]

For the actual source and degree13 target, retain all three nonzero two-torsion
points over K=F223[z]/(z^3−3). Enumerate all sixteen four-torsion points over
L=F223[w]/(w^6−3), z=w^2, by solving halves of each branch point and checking every
point, doubling, closure and both gamma/delta compositions. Validate Frobenius
instead of assuming it from a point count. Under A(F223^2)=E(L), base Frobenius is
coordinate F^3, fixing K. The three K embeddings fixing F223^2 have exponents
0,4,2; their order in an ideal product is immaterial. The F223^2 coefficient
subfield is span(1,w^3), with (w^3)^2=3. Test every asserted inclusion and action.
Do not apply coordinate F to E as though its K coefficients were fixed.
[pcc:unverified]

## B. Actual quadratic-field Picard arithmetic

Create an isolated literal derivative of the original prime-field Picard source.
Keep the original file and prime constructor untouched, including rejection of
49729 as composite. A new explicit quadratic base-extension constructor must
validate the base prime curve, nonsquare parameter and field embedding. It may
reuse prime-field normal-form/base-point caches only with their scalar-extension
argument and native equality controls; recompute base-point setup as a check.
[pcc:unverified]

Use canonical u32 encodings a+p*b for Fp[v]/(v^2−nu), p in5,7,11,223. This is field
arithmetic, never integer arithmetic modulo p^2. Inventory and adapt every
direct modular bypass in evaluation, gradient/tangent setup and sub_nc as well
as Fq multiplication/addition/subtraction/negation/inversion. Compare with the
original FpR field. In particular encoded v=223 must square to3, while integer
modulo49729 incorrectly squares it to0. Reject square nu and unsupported inputs.
Compare base-field classes and operations with original Picard; test genuine
non-base-field classes, Frobenius, exceptional classes and group identities.
[pcc:unverified]

## C. Base-changed complete pullback and beta

Extend the two actual complete fibre-ideal constructions to source L coordinates.
Use the original line/conic ideals, branch/infinity multiplicities and actual P0
origin. Form all three F^2-conjugate ideals and their product; take coefficient
traces L/F223^2 in a genuine three-element basis, reduce in the new Picard field,
and subtract the complete origin class. No reduced-support replacement, fitted
translation, scalar witness, source DLP solve or odd-subgroup lookup is allowed.
[pcc:unverified]

Require exact agreement with each old pullback on original K inputs, both actual
geometric kappa branches, base Frobenius equivariance Phi(F^3P)=F Phi(P), and full
torsion/addition controls. All sixteen E[4](L) inputs are retained, including
nonrational images. Match every F223-rational image to the existing actual
four-element Jacobian cofactor group. All choices of a lift must give identical
Phi1 gamma output in the matched case. Wrong model/kernel/field mutations reject.
[pcc:unverified]

For any rational class x, split its cofactor-four part x2=[ell]x and odd part
xodd=x−x2, ell=2773073≡1 mod4. Evaluate beta(xodd)=[1386537]F(xodd); evaluate beta(x2)
through the actual bounded four-torsion lift and compose the outputs. Construct
the reverse similarly. Test all four cofactor sectors with fixed odd scalars and
the five literal public targets, addition, both[13] compositions, F=[2]beta,
canonical class/model tags and source recovery. The finite cofactor table is
explicitly costed precomputation, never a table for an odd-subgroup discrete log.
[pcc:unverified]

## Execution and reporting

Stages are discriminating units: first faithful Lean and actual torsion/field
controls, then base-changed Picard/pullbacks, then full rational beta. Preserve
each failed attempt before a changed hypothesis or implementation. Rust performs
all research/replay arithmetic; shell is thin orchestration. Ordinary development
checks: build900s, native900s/2GiB, auxiliary120s, dedicated output/cache or declared
existing stock cache, exact command/toolchain/binary/source hashes. These are not
performance measurements. No paid launch without the existing live admission.
[pcc:unverified]

Maintain source manifests/guarded originals, prospective records, written proof,
faithful feasible Lean declarations with exact bindings, and a source-linked
diagram/report/PDF inspected on every page. Publish substantial stages normally
to the existing ready PR; add replay CI without changing old gates or workflows.
Whole raw evidence uses the unchanged genuine publisher; the next artifact
fast-forward requires NEWguard12. No runtime or calibrated advantage is inferred
from a successful map or reduced degree. Complete global rational coordinates,
actual geometric/formal bridges and matched costs remain separately visible.
[pcc:unverified]
