# Actual prime-field Jacobian transfers through the odd source isogeny

2026-11-13. Prospective56fbbb and52e030 precede the new source/model/API
code. Model9722d7, complete-map01e1e62b and versioned API02_9561ce retain
all outcomes. This is an unsigned written mathematical argument with
finite native observations and partial formalization, not signed execution
or a computational-advantage result. [pcc:unverified]

## Actual models and maps

Keep K=F223[z]/(z³-3), L=F223[w]/(w⁶-3), z=w² and the original
q223/seed1 elliptic source and Jacobian J0 fixed. Actual gamma:E→Eprime
has degree13, target a=(196,168,69),b=(8,82,207), and dual delta with
both compositions[13]. Its full rational identities and disjoint source/
target j-conjugates are de87bd/b9a91f. The new SourceE type copies the
actual target, field, generator and source ID into a separate checked
object; it never mutates the old instance. A nonzero exact prime-ell
generator and the unique Hasse multiple independently identify its
rational order11092292=4*2773073. [pcc:unverified]

The generic builder first matches ALL six old models: equations, H/Q,
factors, kernels, P0s, rational points and complete quotient records.
On Eprime it independently retains all135 product Lagrangians,4096
pairings and9 rational kernels, three product and six classical HLP.
All six models are smooth, with full15-coefficient Moore descent and
three quotient identities. The actual new outcomes are:

| root,sign | T | D=16T | square | P0 |
| --- | --- | --- | --- | --- |
| 0,0 | 95 | 182 | no | 1,1,34 |
| 0,1 | 168 | 12 | no | 1,0,174 |
| 1,0 | 203 | 126 | yes | 1,0,84 |
| 1,1 | 119 | 120 | yes | 1,0,82 |
| 2,0 | 215 | 95 | no | 1,0,7 |
| 2,1 | 138 | 201 | yes | 1,0,75 |

All nonsquare outcomes remain rejected for this specified source. None
has T=0. The actual gamma permutation on sorted nonzero source2-torsion
is1↔3,2 fixed. These facts are native9722d7, not counts selected before
the experiment. No coefficient-array difference is used as an isomorphism
test. The formulas are the classical Howe–Leprévost–Poonen construction,
arXiv math/9809210v1, §4.1; no novelty is asserted. [pcc:unverified]

For each of the three eligible quartics Cprime/F223, let Jprime=Jac(Cprime)
and Aprime=Res(K/F223)(Eprime). The actual complete maps are
PhiPrime:Aprime→Jprime and NormPrime:Jprime→Aprime. Their rational-point
implementations use explicit source coordinates, fields, models and P0
tags. Pullback traces complete conjugate fibre ideals with branch and
infinity multiplicities and subtracts the actual origin fibre. The norm
reconstructs the length3 divisor algebra, including nilpotents, and
subtracts the actual residual-line offset. There is no fitted translation,
scalar, DLP table, reduced-support replacement or doubled-norm halving.
[pcc:unverified]

## Global meaning of the complete maps

Apply the Ciani/V4 correspondence argument from5f7e4c to THIS fresh source.
The sign involutions on each smooth quartic give three degree2 quotient
curves of genus1. The three complete quotient polynomial identities and
square D identify their Jacobians with the three conjugates of Eprime.
The universal identities in GluingModels.lean apply without changing their
field or exceptional hypotheses. Translating by the actual image of P0
identifies based quotient points; translation has trivial action on Pic0.
Both geometric kappa branches differ by a2-torsion translation, so their
based differences agree and descend to K, as checked on all rational
curve points. Galois permutation of the three factors gives the F223
Weil-restriction maps. [pcc:unverified]

For each quotient, norm after pullback is[2]. Cross terms vanish: the
other quotient involution acts by-1 on the source elliptic Pic0, whereas
the norm is invariant; the resulting connected image lies in finite
2-torsion. Summing quotient pullback-after-norm correspondences gives[2]
on Pic0 because the full V4 quotient has genus0. Thus globally

    NormPrime PhiPrime=[2]_Aprime,
    PhiPrime NormPrime=[2]_Jprime.

Norm and pullback are dual for the canonical principal polarizations.
Each map has degree8 and polarization multiplier2. The implemented
scheme fibres/local jets realize pullback at ramification and infinity;
the finite divisor-algebra norm realizes multiplicities. Equality with
these constructions on the dense generic locus, and extension of
homomorphisms of abelian varieties, supplies the global interpretation.
The actual scheme/Picard/duality/descent bridges are written, not fully
formalized or supplied by the finite sample alone. [pcc:unverified]

Let A=Res(E), u=Res(gamma):A→Aprime and v=Res(delta):Aprime→A.
They are defined over F223 by restriction of scalars of the actual
K-defined maps. Over the algebraic closure they are products of the
three conjugate degree13 maps. Therefore deg u=deg v=13³,
vu=[13]_A, uv=[13]_Aprime and u*lambdaAprime=13lambdaA. On rational
points their implementation is exactly gamma/delta on E(K), followed by
the existing Frobenius trace descent in Phi. [pcc:unverified]

## Both actual chain compositions, degree and DLP transport

Define the implemented prime-field homomorphisms

    F=PhiPrime u N0 : J0→Jprime,
    G=Phi0 v NormPrime : Jprime→J0.

Using the old and new dual pairs and scalar commutation of homomorphisms,

    GF=Phi0 v [2]_Aprime u N0
      =Phi0 [26]_A N0=[52]_J0,
    FG=PhiPrime u [2]_A v NormPrime
      =PhiPrime [26]_Aprime NormPrime=[52]_Jprime.

The degree is8*13³*8=140608. Pulling back the canonical polarization gives
F*lambdaJprime=52lambdaJ0. Characteristic223 is coprime to52, so F is
separable, with geometric kernel order140608 killed by52. Its complete
geometric kernel type is not established by the rational cofactor table;
the transported2-kernel intersection and13-primary factor remain a
specific successor calculation. [pcc:unverified]

Since52 is coprime toell2773073, F is injective on the ell subgroup.
The exact certificate52*159985=1+3*ell gives inverse[159985]G there.
For the original elliptic DLP, define H(P)=F(Phi0(P)). Then

    delta NormPrime H(P)=[52]P,
    P=[159985]delta NormPrime H(P)  for [ell]P=0.

This is the reusable Chain API's source recovery. Its runtime takes
coordinates/classes and identity tags, checks source/codomain and odd
membership, and requires a forward recovery roundtrip. A test-only
known scalar is never an input to these maps. Thus Q=[k]P gives
H(Q)=[k]H(P), and a DLP solver on the new image would recover the original
k. The existence and cost of a faster solver remain separate questions.
[pcc:unverified]

## Endpoint distinction and native evidence

Aprime and A have disjoint geometric elliptic j-conjugate sets. A
polarized product isomorphism would have degree-one columns and force
an elliptic isomorphism across those sets, excluded by b9a91f. If one of
the new Jprime were F223-ppav-isomorphic to J0, its norm transported to
J0 would have an F223-rational maximal-isotropic2-kernel. The earlier
unique-kernel argument c2270b would identify that kernel with ker N0.
The resulting principally polarized quotients would identify Aprime with
A, a contradiction. Each new target therefore differs from old J0 over
F223 as a principally polarized abelian variety, hence as a curve by
Torelli. Mutual new-target and extension-field Jacobian isomorphisms are
not decided by this argument. [pcc:unverified]

Native02_9561ce passes one unfiltered test and all2485 selected hashes
remain unchanged. Each of the three cases covers36 source points,
every224 new and224 old rational C-point class, both[2], both[52], the
nonzero exact-ell image and all five unchanged public targets. It checks
100 pullback and100 norm addition pairs,48 alternate charts, all224
geometric residual-line offsets, actual multiplicity3 omissions, all12
doubled-fibre jets versus wrong linear fibres, signed geometric
infinities2+2, reachable K infinities, alternate actual P0/tag/zero origins
and off-curve controls. Every intermediate chain class/point is retained.
[pcc:unverified]

The versioned runtime addition52e030 supplies F/G, original odd-source
forward and tagged source recovery. All five public API/manual images
and original recovered points agree; noncanonical/offcurve/nonodd source,
nonodd class, wrong tags and an actual mismatched chain target reject.
The new constructor recomputes all three translated source A/B conjugates;
two foreign metadata mutations reject. All01_e1e62b checks and its whole
capture remain intact. The actual rational cofactor groups are all C4;
F kernel sizes are2,4,2 and G kernel sizes2,2,2. These counts do not give
the geometric degree or free-kernel type and establish no cost advantage.
[pcc:unverified]

Whole native records/fixtures exceed the Git data threshold and are queued
for the unchanged genuine artifact publisher, with original hashes and
member indices retained. Source checkpoint, clean physical independent
replay/CI, feasible faithful Lean implications and the visual report
follow. Original S3 benchmark checkpoint/live budget/capacity, complete
cost accounting and strongest IC/rho references remain necessary for the
requested computational-advantage conclusion. [pcc:unverified]
