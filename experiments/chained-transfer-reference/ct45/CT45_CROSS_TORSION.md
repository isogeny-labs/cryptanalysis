# CT45 — exact finite-level cross-factor Hom and the non-liftable four-gluing

**2026-11-12 · [pcc:unverified].** This independently refines CT37/41/43/44 for the fixed ordinary elliptic curves over F101 with traces -7 and -11. It does not certify a native genus-two transfer or a speedup.

## Exact proposition

For m coprime to p=101, write R=Z/m and take Frobenius-cyclic bases, so the two Frobenius matrices are C_t=[[0,-101],[1,t]], t=-7,-11. Such bases exist on the 2-power torsion because X^2+X+1 is irreducible mod 2, and a cyclic generator lifts to Z/2^k.

Every Frobenius-equivariant R-linear map X:E[m]->F[m] is **exactly**

    X(a,c) = [[a,-101c],[c,a-11c]],   4a=4c=0 (mod m).

**Proof.** Set X=[[a,b],[c,d]] and expand X C_(-7)=C_(-11) X. The first column yields b=-101c and d=a-11c. The upper-right equation yields 101(-11+7)c=0; since gcd(101,m)=1, 4c=0. The lower-right equation yields (-7+11)d=0, thus 4d=0 and then 4a=0. Conversely, substitution shows these conditions are sufficient. Therefore 4X=0 and its image is annihilated by four.

For odd m (coprime to 101), 4 is a unit, so X=0. At m=2^k the additive intertwiner group is (Z/2^min(k,2))^2: four elements at k=1 and 16 for all k>=2. Modulo 4, 12 are invertible and six reverse Weil pairing, as found in CT43. Modulo 8 and higher **none are invertible**, because entries are divisible by 2^(k-2), so in particular every 8-level map is zero on reduction modulo two. No mod-4 anti-isometry can lift to a *full* Frobenius-equivariant 8-torsion isomorphism. At k>=4, every level-k map reduces to zero modulo 4. A compatible homomorphism on the torsionfree 2-adic Tate modules is zero since 4X=0.

This does not contradict CT37's stronger geometric Hom=0 from different CM fields. Galois-equivariant finite-level module maps are not necessarily actual elliptic-curve homomorphisms, and partial/non-graph higher-level Jacobian kernels are not excluded. The argument assumes m coprime to 101; characteristic-101 group schemes require the separate CT41 treatment.

## Independent arithmetic

| m | All intertwiners | Invertible |
|---|---:|---:|
| 2 | 4 | 3 |
| 4 | 16 | 12 (six anti-isometries) |
| 8 | 16 | 0 |
| 16 | 16 | 0 |
| 32 and 256 | 16 each by exact formula | 0 |

Python brute-forces all 2x2 matrices at 2/4/8/16 and odd levels 3/5/7/9/25, then independently checks the formula at 32/256. JavaScript independently brute-forces the matrix equations at 2/4/8/16. Both reject a wrong-level claim and accept the **positive trace mutant -15**, for which 64 intertwiners and 48 invertible matrices occur at level eight (because the trace difference becomes 8). Locally executed, but not signed scientific verification: [pcc:unverified].

    python3 -B experiments/chained-transfer-reference/ct45/ct45_cross_torsion.py
    python3 -O -B experiments/chained-transfer-reference/ct45/ct45_cross_torsion.py
    node --check experiments/chained-transfer-reference/ct45/ct45_cross_torsion.js
    node experiments/chained-transfer-reference/ct45/ct45_cross_torsion.js

## Checked sources and next discriminating experiment

Prior work: [CT43](../ct43/CT43_MOD4_FROBENIUS_GLUE.md), [CT44](../ct44/CT44_WEIL_COVARIANCE.md), crypto [PR #3877](https://github.com/isogeny-labs/crypto/pull/3877) and its `QUARTIC_GLUING_PROOF.md` and `TWO_PRIMARY_QUOTIENT_PROOF.md`; Bruin–Doerksen (2011), DOI [10.4153/CJM-2011-039-3](https://doi.org/10.4153/CJM-2011-039-3). The research-KB tool and the encrypted autoresearcher lead atlas were inaccessible; no novelty/absence claim. The algebra here is elementary standard module theory; formal Lean geometry remains open.

Next, export frozen native kernel graph and Weil-oriented factor bases from root #3877, then identify actual U among CT43's six candidates, compare the root's degree-seven matrices with CT44's U'=B U A^(-1) and adjugate dual, and replay with the complete independently implemented Cantor corpus including ramified, nonsplit and extension-field divisors. This is a necessary finite-module constraint, not an actual-map kernel certification. Matched full cold solver costs still require EKS/S3 admission. No paid compute or merging bypass.
