# Next lead: independent norm from canonical genus-three classes

2026-11-13. Proposed next cryptanalysis component; no new norm implementation,
execution or acceptance is asserted. Native sourcea719 and metadata-only
descendantbb6 supply the completed forward map. Its first GitHub workflow
was rejected before jobs; the versioned context correction is separate.
All mathematical assertions here have unsigned standing. [pcc:unverified]

## Primary review and scope

Read the original `quartic_pic_canonical_20261018/README.md`, the representation,
`gen_mul`, `mul_forms`, `linear_kernel`, completion/reduction and `oracle::zeta_c3`
in `src/cryptanalysis/plane_quartic_pic.rs`; the original Ciani cover in
`diem_quartic.rs`; `G3_DESCENT_DERIVATION.md`, its two corrective contracts and
`G3_PROOF_MAP.md`; original `isogeny_algos` FpR, curve, polynomial and series APIs.
Existing nineteen-source literature receipts remain applicable. The original
Picard source already counts effective degree-three divisors by
`(N1^3+3*N1*N2+2*N3)/6`. The new interface must reuse original engines.
KB tools are still absent from ALL_TOOLS; earlier six actual127 fallback
receipts remain. This is an explicit retrieval gap, not a novelty claim.

The input domain is valid canonical `PicClass` values for the exact checked
fixture and base point, including every exceptional class. A public encoded
interface also needs exact curve/map/base-point tags and canonical validation;
a bare 3x6 matrix does not identify a Jacobian. Initial q=5,7,11 fixtures stay
unchanged. The independent norm may use Fp6 support roots; that cost is part
of this oracle and does not change the root-free forward runtime claim.

## Proposed actual map

For `Exc(P)=[P0-P]`, evaluate the completed cover directly and return
`pi0(P0)-pi0(P)`. For `Typ`, its three conics cut out the unique noncollinear
effective divisor D of degree3 representing x+Dinf. Recover its finite
coordinate algebra A and push the degree-three cycle forward, rather than
searching for a source scalar or using an inverse table.

1. Use the original counted linear kernel to describe R2/I_D(2), dimension3.
   Form all original conic times degree-two products in R4; its quotient must
   also have dimension3. Use annihilator rows as quotient coordinates.
   This is an adapter around original polynomial multiplication and linear
   algebra, not another field, Groebner or Jacobian engine.
2. Select three degree-two basis forms f_j. Enumerate prime-field linear
   forms L deterministically until the matrix of L²*f_j in the R4 quotient
   is invertible. Then A consists of F2/L². Multiply by forming F2*G2 in
   the original R4, projecting, and solving against that same matrix.
   The unit is L²/L²; W_i/L comes from W_i*L/L². Verify the unit,
   commutativity, associativity, defining conics and actual quartic in A.
3. Enumerate A elements T deterministically until (1,T,T²) is a basis.
   Express T³ in that basis to obtain the monic degree-three polynomial u.
   Express each W_i/L as a polynomial of degree≤2 in T. The curvilinear
   divisor algebra should be monogenic for this q≥5 panel; a failure is
   retained and diagnosed, never bypassed by dropping that class.
4. Split u using the original polynomial engine over Fp6. All closed-point
   degrees of a rational degree-three divisor are1,2,3 and divide6.
   Determine multiplicities from u with original exact polynomial division,
   not by counting distinct roots. Evaluate the three projective coordinate
   polynomials at every root and require the actual curve equation.
5. Evaluate the original completed Ciani cover at each support point,
   including u0=0 and both infinities. Derive its short-model parameters
   independently from u0*u2 with original FpR/polynomial operations. Add
   images with the recorded cycle multiplicities using original elliptic
   group operations. No cover derivative is needed to push an effective
   cycle; multiplicity is retained by the algebra polynomial.
6. Subtract the image sum for Dinf~K-P0. Compute it independently from an
   actual PLANE line section through P0 minus P0, using a quartic restriction
   and dividing the known P0 factor once; retain any remaining multiplicity
   and projective infinity. Check every rational line choice gives the same
   elliptic sum. Do not identify a tetragonal infinity fibre with a plane
   canonical section without proof. This shift is geometric, not fitted.
7. The resulting sum must be fixed by q³-Frobenius. Recover its coefficients
   in the explicit embedded K basis(1,theta,theta²) through original linear
   algebra and check the embedding back. Do not reinterpret Fp6 arrays.

## Independent complete panel

Independently count C(Fq), C(Fq²), C(Fq³): enumerate ONE affine coordinate
and find all roots of the remaining degree≤4 polynomial with the original
engine, then include both projective boundary charts. This avoids an
unnecessary q^6 two-coordinate grid. Count distinct points. From these N_i,
the original degree-three divisor formula and the canonical Picard
representation give #Jac = (N1³+3N1N2+2N3)/6 - q*N1. Check exact divisibility
and compare a separate Newton/Frobenius calculation. Written RR and
reciprocity identifications remain explicit geometric bridges.

Predicted counts from the existing written Res(E) isogeny are
(6,26,192),(8,50,380),(12,122,1308), yielding148,356,1324 classes. These are
predictions to independently recompute, not observed results of this lead.

Build a deterministic generating BFS from rational point classes; its
closure must equal the independently counted Jacobian order. If necessary,
extend the fixed candidate pool with degree-two Frobenius pairs plus P0,
degree-three orbits, and repeated-point degree-three divisors, using original
ideal products and canonical reduction. Keep completeness/rank criteria.
No fixture replacement or reduction of the full-class acceptance domain.

Four substantive tests should cover: all field/model/algebra charts; every
Jacobian class and complete generating edges; both actual compositions
`norm(phi(P))=[2]P` on every source point and `phi(norm(J))=[2]J` on every
Jacobian class; all odd-subgroup scalar images and finite recovery after
the public inverse of2; exceptional/nilpotent/infinity/origin/tag/malformed
controls. Keep generator discovery and group-order recomputation separate
from scalar-label tables. Report both observed even kernels, not assumed ones.

Freeze a consumer protocol/source catalog and claim before code/runs, on a
new ready child of cryptanalysis1520. Native Rust/Lean only. Fresh external
caches; initial strict static/unit/CLI bounds900s, proof bounds600s. Whole
source/command/exit/guard raw trees, immutable failures, faithful written and
partial formal proofs, inspected PDF and independent actual CI/publication
are required. No paid cost experiment is admitted. After this component,
continue the executable destination IC pipeline and admitted comparisons.
