# CT47: exact extension-degree ceiling for the fixed F101 two-primary torsion

**[pcc:unverified]** Date: 2026-11-12. Stacked on CT45-46 PR #1510 and native producer crypto PR #3877. This is an elementary finite-ring theorem with executable checks, not an evaluated Jacobian correspondence, a signed PCC verdict, an elliptic isogeny, or a cheaper DLP solver.

## Theorem and scope

Let E and F be the elliptic curves over F_101 with Frobenius traces -7 and -11. For integers s,k >= 1, their finite étale 2^s-torsion Galois modules over F_(101^k) are isomorphic **if and only if**

    s <= v_2(k) + 2 + (1 if 3 divides k else 0).

A Weil pairing anti-isometry can be chosen whenever the modules are isomorphic. In particular, for s>=3 the least possible extension degree is **k_min = 2^(s-2)**. Every fixed finite extension k has a finite maximal torsion depth. The geometric Hom(E,F) remains zero because the CM fields Q(sqrt(-355)) and Q(sqrt(-283)) are distinct; finite-level Galois-module isomorphisms do not produce elliptic isogenies.

| k | Largest compatible torsion | Next incompatible |
|---:|---:|---:|
| 1 | 4 | 8 |
| 2 | 8 | 16 |
| 3 | 8 | 16 (despite trace agreement mod 16) |
| 4 | 16 | 32 |
| 6 | 16 | 32 (despite trace agreement mod 32) |
| 12 | 32 | 64 |

## Proof

1. Put C_t = [[0,-101],[1,t]], with t=-7 or -11. Both reduce mod 2 to [[0,1],[1,1]], with irreducible polynomial X^2+X+1 and order 3. The actual Tate modules admit integral companion bases because Z_2[pi] is the unramified quadratic order.

2. If k=2^r u with u odd, conjugacy of C_-7^k and C_-11^k reduces to conjugacy at k=2^r when 3 does not divide u, or at k=3*2^r when 3 divides u. Indeed the principal congruence subgroup GL_2(Z/2^s) -> GL_2(F_2) is a 2-group. In the first case the relevant matrix orders divide 3*2^M, and odd u prime to 3 has a multiplicative inverse modulo those orders. In the second case C_t^(3*2^r) reduces to I mod 2, so its order is a 2-power and the remaining odd exponent can be inverted. Conjugating powers and raising them to such inverse exponents proves both directions.

3. For k=2^r, let U_t(n)=tr(C_t^n) and D_n=U_-7(n)-U_-11(n). The recurrence D_(2n)=D_n (U_-7(n)+U_-11(n)) and D_1=4 give exactly v_2(D_(2^r))=r+2: each sum is 2 modulo 4. C_t^(2^r) remains cyclic modulo 2. Two cyclic 2x2 matrices over Z/2^s are conjugate precisely when their characteristic polynomials agree; both determinants are 101^(2^r), so conjugacy holds exactly for s<=r+2. A direct conjugator at these levels is B_F B_E^(-1), B_t=[e1,C_t^(2^r)e1].

4. For k=3*2^r, the swap matrix P=[[0,1],[1,0]] intertwines C_-7^3 and C_-11^3 modulo 8. Both cubic powers are I modulo 2, so repeated squaring increases this congruence depth, giving existence through s=r+3. To rule out s=r+4: at r=0 write C_t^3=3I+4N_t modulo 16; det(N_-7)=1 and det(N_-11)=3 modulo 4. For r>=1 write C_t^6=I+8N_t modulo 32; det(N_-7)=3 and det(N_-11)=1 modulo 4. The binomial identity (I+8N)^(2^h)=I+2^(h+3)N modulo 2^(h+5) propagates these normalized matrices unchanged modulo 4. Similarity at depth r+4 would force equal normalized determinants, contradiction.

5. For pairing: precomposition with I+b C_-7 preserves Frobenius equivariance and changes determinant by the norm 1-7b+101b^2. Its derivative -7+202b is odd, so every odd prescribed determinant can be attained by successive bit lifting, including the determinant needed to reverse the Weil pairing. This is an *abstract* torsion module statement, not the orientation of the native maps.

6. Minimizing k: if 3 does not divide k, s<=v_2(k)+2 requires k>=2^(s-2). If 3 divides k, s<=v_2(k)+3 requires k>=3*2^(s-3), strictly larger. Thus the minimum for s>=3 is 2^(s-2).

## Reproduction and controls

The local Python oracle checked all invertible 2x2 matrices exhaustively in **48 (k,s) cases** (k=1,2,3,4,5,6,7,8,9,10,12,15; s=1..4), 18 normalized determinants at k=3*2^r, 10 exact trace valuations and constructive determinant-(-1) intertwiners at k=2^r. It rejected three trace-only false-positive cases (k=3,6,12), and normal / -O Python output matched. A separately written JavaScript arithmetic program checked base and normalized matrices, oriented witnesses and odd multipliers. Both are *producer-authored sanity checks*, not signed independent scientific verification.

Historical failed check: the initial Python cyclic-basis conjugator had a wrong upper-right term and failed at k=2. The corrected formula is (B_F[0,0]-B_E[0,0])/B_E[1,0], not B_F[0,0]-B_E[0,0]*B_F[1,0]/B_E[1,0]. The failed attempt is preserved in this report instead of being erased.

Reproduce with:

```sh
python3 -B experiments/chained-transfer-reference/ct47/ct47_extension_depth.py
python3 -O -B experiments/chained-transfer-reference/ct47/ct47_extension_depth.py
node experiments/chained-transfer-reference/ct47/ct47_independent.js
node --no-opt experiments/chained-transfer-reference/ct47/ct47_independent.js
```

Sources reviewed: CT37/CT43/CT44 PR #1502; CT45-46 PR #1510; native 36-hop and catalog proof PR isogeny-labs/crypto #3877; Bruin-Doerksen (2011), DOI 10.4153/CJM-2011-039-3. Shared research-KB and locked lead atlas were inaccessible, so no novelty/absence claim. The concurrent full Cantor/native transfer work in PRs #1509 and crypto #3877 is untouched.

**Open obligations:** Lean formalization of the all-depth normalized determinant obstruction; extraction of the actual symplectic Tate-module bases, principal polarizations and geometric kernels; ramified and nonsplit Cantor replays; fully priced matched cold rho/index-calculus comparisons gated by live EKS/S3 spending admission. No paid compute or protected merge is part of CT47. [pcc:unverified]
