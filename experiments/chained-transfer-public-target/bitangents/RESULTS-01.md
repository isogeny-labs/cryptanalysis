# Actual coordinate result and remaining geometric bridges

2026-11-13. Nativee887a9 is an unsigned execution observation. It passes one
unfiltered serial test with no ignored/filtered cases; all2338 selected source
hashes remain unchanged. Prospective361ee8 precedes the new Rust source.
[pcc:unverified]

The original Rabin constructor admits L=F223[w]/(w^6−3). The embedding
K→L sends z to w², with all basis products and Frobenius checked. The six
Ciani coefficients from the original rmat and the original inverse Moore
matrix expand to all15 original quartic coefficients with the correct
normalizing scalar. [pcc:unverified]

There are28 distinct normalized actual W-coordinate lines:12 in the
coordinate-zero families and16 generic. The degree10 elimination polynomial
has6 distinct U candidates; no L=C=0 branch occurs in this fixed curve.
That branch is implemented but not claimed exercised. Every accepted line
has an independently recomputed restriction of the original quartic equal
to scale times a quadratic squared, with all five coefficients checked.
All gradient/line minors vanish modulo the contact quadratic in both charts.
All28 deliberately mutated contact certificates fail. [pcc:unverified]

All28 contact quadratics have affine degree2 in the chosen charts. Sixteen
split over L;12 have no roots over L and remain as nonsplit contact schemes.
No condition requiring all contact points to lie in L is imposed. A scalar
times Q² cuts twice the geometric degree2 contact divisor, so each line is
a bitangent. The standard28-odd-theta theorem for smooth plane quartics in
odd characteristic supplies the completeness bridge. It is written here,
not formalized by the supplied Lean module. [pcc:unverified]

Applying the original q-Frobenius to actual normalized line coordinates
gives the permutation stored in native records. Its disjoint cycle lengths
are6,6,6,3,6,1. Exactly1/1/4/28 bitangents are fixed by F/F²/F³/F⁶.
Thus the minimal field containing all line coordinates is F223^6. This
direct coordinate finding agrees with the separate written Jacobian
two-torsion argument65f7a4, without assuming the Frobenius matrix is
semisimple of order3. [pcc:unverified]

The four new exact local PCC bindings are a01f8f (denominator factor),
5288a0 (constant factor),6cd1a8 (resultant necessity under both actual
equations), and d79edc (exact order6 of the literal28-entry permutation).
Both unchanged original gates pass4/0trusted. The three commutative-ring
proofs use propext,Classical.choice,Quot.sound; the closed permutation proof
uses no foundations. No proof holes, custom axioms or native_decide occur;
no fresh lean4checker result is claimed. [pcc:unverified]

The actual curve and theta-characteristic definitions, geometric
Frobenius identification, half-canonical divisor map, Weil pairing, torsion
basis and stable maximal-isotropic kernel construction remain explicit
formalization and implementation gaps. A line/contact/Frobenius census is
not a new isogeny. Next use the actual permutation to constrain stable
kernels through an independently checked symplectic calculation, then
construct actual kernel/divisor coordinates and a nondual codomain if one
exists. No kernel count, nonexistence theorem or advantage is asserted at
this stage. [pcc:unverified]
