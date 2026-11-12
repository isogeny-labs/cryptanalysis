# CT48: exact finite-level cross-factor Hom groups over extension fields

**[pcc:unverified]** 2026-11-12. Scope: public elliptic factors over F_101 with traces -7 and -11, and 2-power torsion prime to the characteristic. This is a finite Galois-module computation, not a geometric homomorphism, a genus-2 quotient, or a measured cryptanalytic cost.

## Theorem — full 2-primary Smith classification

Let A=C_{-7}=[[0,-101],[1,-7]], B=C_{-11}=[[0,-101],[1,-11]], and L_k(X)=B^k X-X A^k on Mat_2(Z_2). Put r=v_2(k). The **2-adic Smith invariant valuations** of the four-dimensional Z_2-linear operator L_k are exactly:

- 3 does not divide k: **(0, 0, r+2, r+2)**.
- 3 divides k: **(r+2, r+2, r+3, r+3)**.

Consequently, with a_i these four valuations, the **exact number** of Frobenius-equivariant module homomorphisms E[2^s] -> F[2^s] over F_(101^k) is

`2^{sum_i min(s,a_i)}`.

This counts *all* additive Galois-module maps, including zero and noninvertible maps; it does not count elliptic-curve morphisms. In particular for every s >= 3, at k=1 there are 16 maps; at k=3 and s>=3 there are 2^10=1024. The module-map count can grow over an extension even though geometric Hom(E,F)=0. A large finite-torsion Hom space is therefore not a new ECDLP transfer.

| k | Smith valuations | Number of maps at s=3 | Full 8-torsion isomorphism? |
| ---: | --- | ---: | --- |
| 1 | 0,0,2,2 | 16 | no |
| 2 | 0,0,3,3 | 64 | yes |
| 3 | 2,2,3,3 | 1024 | yes |
| 4 | 0,0,4,4 | 64 | yes |
| 6 | 3,3,4,4 | 4096 | yes |
| 12 | 4,4,5,5 | 4096 | yes |

The displayed map counts follow from the formula; the **number of invertible maps** is a separate question settled at each torsion level by CT47's conjugacy theorem. CT48 does not infer invertibility from cardinality.

## Proof and dependencies

1. Both integral 2-adic Tate representations have a cyclic companion basis because the common Frobenius polynomial modulo two is irreducible. This is the actual-module hypothesis inherited from CT45/CT47, not a choice of an arbitrary unrelated pair of lattices.
2. On any finite 2-power torsion, replacing k=2^r by 2^r*u, with u odd and 3 not dividing u, preserves the entire intertwiner kernel: both Frobenius matrices have finite orders dividing 3 times a power of two, and u has an inverse modulo those orders. When 3 divides k, reduce in the same way to k=3*2^r, because both cubed Frobenius matrices are identity modulo two and so have 2-power order. This equality at all moduli also preserves the 2-adic Smith invariant valuations.
3. The characteristic polynomials of A^k and B^k have equal constant 101^k and traces T_E(k),T_F(k). Thus
`det(L_k)=101^k*(T_E(k)-T_F(k))^2`, up to an irrelevant sign. Since 101 is odd, its 2-adic valuation is twice that of the trace difference.
4. If k=2^r, successive trace doubling gives v_2(T_E(k)-T_F(k))=r+2. The reduction of L_k modulo two is a commutator by the order-three irreducible matrix, so it has rank two and two unit Smith pivots. The two companion matrices are conjugate modulo 2^(r+2) by equality of characteristic polynomials and cyclicity; their intertwiner module there has exactly 2^(2(r+2)) elements. Hence the other two Smith valuations are at least r+2. The determinant valuation 2(r+2) makes both exactly r+2.
5. For k=3*2^r, the initial trace difference has valuation five: T_E(3)=1778, T_F(3)=2002 and their difference is -224. At every doubling the sum of traces is 4 modulo 8, so v_2(trace difference)=5+2r. Both cubes are 3I modulo four, and with N_t=(C_t^3-3I)/4 the linear map X -> N_F X-X N_E has rank exactly two over F_2. Squaring once changes the common scalar from 3 to 1 and preserves the non-scalar normalized difference modulo two; further squaring does likewise. Therefore L_k is divisible by 2^(r+2), and L_k/2^(r+2) has rank two modulo two. Its first two Smith valuations are r+2 and its last two at least r+3. The determinant valuation 2(5+2r) forces both remaining valuations to be exactly r+3.
6. By elementary Smith theory, the kernel of a diagonal element 2^a on Z/2^s has 2^min(a,s) elements, yielding the formula.

**Negative boundary:** These finite Galois-module intertwiners need not extend to compatible maps over all s. Indeed the two ordinary elliptic factors have distinct geometric CM fields Q(sqrt(-355)) and Q(sqrt(-283)); Hom(E,F) over the algebraic closure is zero. More generally, for every fixed n prime to 101 both finite torsion representations become trivial over some extension, so finite torsion identifications alone cannot demonstrate a geometric isogeny. CT47 further bounds the minimum extension degree for each 2^s.

## Reproduction and independent controls

```sh
python3 -B experiments/chained-transfer-reference/ct48/ct48_smith.py
python3 -O -B experiments/chained-transfer-reference/ct48/ct48_smith.py
node experiments/chained-transfer-reference/ct48/ct48_independent.js
node --no-opt experiments/chained-transfer-reference/ct48/ct48_independent.js
```

Python computes all 1x1/2x2/3x3/4x4 minor valuations under exact modular arithmetic (129 cases), then directly enumerates all 2^(4s) candidate maps for fifteen small (k,s) cases. Separate JavaScript performs *2-adic pivot elimination* rather than minor enumeration (129 cases, 516 pivot reductions). Both must reject an altered Frobenius trace -15. Normal and optimized local runs were checked. Producer-authored scripts and CI are not an external scientific signature.

**Sources checked:** CT45/46 PR #1510 and CT47 PR #1511 (existing basis and extension-degree proof); native PR isogeny-labs/crypto #3877 (actual 4-gluing/correspondence status); Bruin–Doerksen, *The Arithmetic of Genus Two Curves with (4,4)-Split Jacobians*, Canadian J. Math. 63 (2011), 992–1024, DOI 10.4153/CJM-2011-039-3; standard Tate-module full-faithfulness theory (Tate, 1966). Research-KB MCP is not exposed here and local repository wrapper unavailable; no novelty/absence assertion.

**Open integration:** Extract native symplectic matrix coordinates and actual glued polarizations for the current root partial-Frobenius/degree-seven maps, and compare geometric kernels and universal adjoints to the independently replayed complete Cantor corpus. No paid benchmarks, frozen-ledger mutation, protected merges, or complete solving-cost claim. [pcc:unverified]
