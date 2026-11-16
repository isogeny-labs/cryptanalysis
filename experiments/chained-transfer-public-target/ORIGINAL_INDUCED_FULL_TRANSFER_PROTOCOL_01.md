# Derive the full quotient transfers from source identities

Publish this protocol on the isolated induced-map branch before writing its
Lean module. Base25801fe is running the additive full replay43700115169;
the original research branch and its ledger remain at that base until an
ordinary fast-forward incorporates this branch. Do not append competing
acceptance claims to the old branch or rebase/rechain either ledger.
[pcc:unverified]

## Question and existing boundary

Native e245d0, conditional7b5f49/da2fe7 and report761003 establish their
stated finite and conditional results for the original cases(2,0)/(0,1)/(2,0),
D116/39/36, ell2773073 and full annihilator11092292. Genuine25 and the exact
canonical701 fixture are settled at consumer6343025/rootd93b64d. The old
FullGroupNorm.two_pair_norm derives a composite norm from individual map
norms; its inverse theorem takes a dual norm as a hypothesis. The next task
derives those individual quotient-map norms from elliptic duality and kernel
transport. This is standard quotient algebra formalization, with no novelty
or computational-advantage claim. [pcc:unverified]

Reviewed sources: HLP math/9809210v1 section4.1/Lemma13/Propositions14–15,
including the separably closed setting, degree-eight quotient and quadratic
base-field qualification; the whole current ChainDescent and FullGroupNorm
modules; originalfull protocol1539b6 and the existing known-point/CRT proofs.
The KB status/mechanism/negative/theorem queries exit127; the VLT1 vault stays
locked at8edec422. No absence or novelty inference follows. [pcc:unverified]

## Explicit objects and allowed hypotheses

Use geometric-point IntModules A,B,C and J,K,L. A and B represent the source
products/Weil restrictions over an algebraic closure; J and K represent the
quotients there. A presentation contains Phi:A→J with additive/subtraction/
integer-scalar/zero identities and a section r:J→A satisfying Phi(r(x))=x.
The section need not be linear, equivariant or rational. A compatible edge
contains g:A→B with the same homomorphism identities and the explicit condition
Phi(a)=0 ⇒ Psi(g(a))=0. [pcc:unverified]

Define T(x)=Psi(g(r(x))). For a reverse edge gh, assume the actual elliptic
identities gh(g(a))=n·a and g(gh(b))=n·b, plus reverse kernel transport. These
are source elliptic identities. No desired T linearity, commuting square,
reverse T norm, injectivity or known-point equality is an input field or
hypothesis. Source presentations and edge structures must expose every
assumption in the complete source, with no user axioms. [pcc:unverified]

Geometric sections must not be relabelled as rational sections. Rational
output uses the separate equivariance/kernel argument already represented
by ChainDescent.corrected_output_fixed. Identifying these abstract groups,
sections and edges with the actual HLP quotients, finite-field programs,
Frobenius, Picard arithmetic and accepted encoded inputs remains explicit.
No new geometric bridge is claimed proved here. [pcc:unverified]

## Frozen conclusions and proof population

The standalone module original-induced-transfer-01/lean/InducedFullTransfer.lean
will contain the presentation/edge structures, the transfer definition and
exactly nine theorem roots:

1. Representative independence, specializing the old kernel argument to
   Psi composed with g, from equality of source Phi images.
2. The induced source identity T(Phi(a))=Psi(g(a)), derived from the section.
3. Additivity of T, derived without additive section or assumed T additivity.
4. Integer linearity T(z·x)=z·T(x), supplying the DLP relation.
5. Both individual quotient reverse norms S(T(x))=n·x and T(S(y))=n·y,
   derived from the two source elliptic dual identities.
6. Two-edge chain collapse to one initial section and the factored elliptic
   composition followed by the final quotient, using the middle section.
7. Inverse recovery for each x with order·x=0, using a Bezout witness and the
   newly derived norm, including full cofactor inputs.
8. Injectivity on that annihilator carrier, derived from recovery for the two
   inputs; no annihilation assumption on every geometric point is permitted.
9. Ordinary-kernel original integer witnesses for inverse13=3413013 and
   inverse169=9648325 modulo11092292, quotients−4/−147 and coprimality.

The first root is a restatement/specialization of the existing quotient-kernel
argument. All prior roots, hypotheses, programs, models and fixtures remain
unchanged. The final witness root repeats and independently checks published
original values; it does not certify an actual Jacobian order.
[pcc:unverified]

## Execution and acceptance

Run both unchanged original Lean4.34.1/4.35.0 gates on the exact source, bounded
to120s each, with nine roots and zero trusted assumptions; then all nine
exact local statement bindings. No native_decide, sorry or user axiom is
allowed. Preserve actual source, failed sources, raw gates and real exits;
an elaboration failure or timeout is not a mathematical counterexample.
Do not repair a failure by adding a desired transfer conclusion as a
hypothesis. [pcc:unverified]

Keep all1440 version03 source references and all343 original producer science
hashes unchanged. Record source-linked derivation/proof maps and an inspected
visual report. Publish checkpoints on this isolated branch, then normally
fast-forward the original research branch before appending any acceptance
claims there. The running exact-source CI258 result remains separately scoped;
future proof CI is additive and old workflows/references stay immutable.
[pcc:unverified]

This task supplies conditional proof structure for DLP-preserving full-group
transfers and their chain. It does not construct a new curve, solve a new DLP,
prove all field/HLP/program bridges or lower a calibrated cost. Prime-field IC,
complete primitive/setup/reference comparisons and stronger known-point
baselines remain queued. All results stay unsigned; future custody is NEW26.
[pcc:unverified]
