# CT41: Frobenius–Verschiebung projectors and two-primary gluing bound

**2026-11-12 | scientific standing [pcc:unverified].** Scope: fixed T0, T1, T2 Jacobians over F_101, conditional on CT39's independently counted Weil polynomial. This is an explicit instance of classical Howe–Lauter gluing-exponent mathematics, **not** a new theorem, speedup, or completed attack.

## Correction and stronger conditional result

CT37 constructed the Frobenius-only Bezout identity with constant 404. CT40 used it to split ell-primary modules for all ell != 2,101. The exclusion of ell=101 was a limitation of that chosen integral polynomial, **not** a proven cross-factor obstruction.

Let F denote 101-power Frobenius, V its Verschiebung, and S=F+V. Integral endomorphisms satisfy FV=VF=[101]. The CT39 characteristic polynomial is

    P(T)=(T²+7T+101)(T²+11T+101).

The two ordinary rational isotypic factors have traces -7 (E109) and -11 (E113). For either elliptic factor, F²-tF+101=0 implies S=t. Tate/Honda–Tate gives the corresponding rational isogeny splitting for every J in this class. Hence (S+[7])(S+[11])=0 in End^0(J); as End(J) is torsion-free, the equality is **integral**. Put

    A=S+[11],        B=-(S+[7]);
    A+B=[4],         AB=0;
    A²=4A,           B²=4B.

**Proposition.** For every odd prime ell, **including ell=101**, and n>=1, write u=4^{-1} modulo ell^n. Then e109=uA and e113=uB are complementary idempotent endomorphisms of the finite commutative group scheme J[ell^n]. Their images form the two canonical isotypic pieces. F_101-defined homomorphisms commute with these operators, and F_101-defined finite ell-primary subgroup schemes split into the intersections with the two images. At ell=101 the statement is about finite flat group schemes, not geometric-point enumeration; the operators F and V preserve subgroup schemes by naturality of relative Frobenius and Verschiebung. The two projectors need **not** exist as integral global endomorphisms of J.

The real Weil polynomials are s+7 and s+11. Their resultant and reduced resultant equal **4**, exactly the certificate type of Howe–Lauter (2012), Lemmas 2.9–2.10 and Proposition 2.8. This is the direct prior-art source, and the conclusion is a special-case application.

## Residual two-primary mixing: exponent <=4, size <=16

Let M=T_2(J), with rational decomposition M tensor Q_2=W109 direct-sum W113 by the two eigenvalues of S. Let M_i=M intersect W_i; both are saturated rank-two Z_2 lattices. A and B map M into the respective M_i and A+B=4, so 4M is contained in M109+M113.

Writing G=M/(M109+M113), one obtains 4G=0. Projecting to W109 induces an injection

    G --> (1/4) M109 / M109 = (Z/4Z)^2.

Indeed, if the first projection of an element of M lies in M109, subtract that component and the remaining vector lies in M113. Thus **the gluing quotient has exponent dividing 4 and order at most 16**. This bound is on 2-adic integral lattice mixing and does not determine the actual kernels, the principal polarization or the native Phi2/Psi2 correspondence.

**Pure lattice sharpness, not geometric realization.** Let R=Z_2, use integral 2x2 elliptic companion matrices F109=[[0,-101],[1,-7]] and F113=[[0,-101],[1,-11]], and put V_i=t_i I-F_i. Both F and V matrices are congruent modulo 4. The F/V-stable lattice

    M = {(x,y) in R² × R² : x≡y mod 4}

has intersections M109=4R²×0 and M113=0×4R², so G=(Z/4Z)^2 has order 16 and exponent 4. The bound cannot be improved using only these integral Frobenius/Verschiebung data. This lattice has **not** been proved realizable as the Tate module of a principally polarized Jacobian.

## Independent arithmetic diagnostic

The standalone Node program ct41_verschiebung_glue.js imports **no** producer elliptic, Jacobian, Richelot, or isogeny engine. It independently tests FV=VF=101I, S=tI, both complementary projectors, orthogonality and factor selection for 33 companion prime-power cases: ell=3,5,7,11,13,17,19,23,29,31,101 and n=1,2,3. It includes three matrix examples at the characteristic prime 101, but **does not implement Dieudonne modules or prove the p-divisible group-scheme statement**; that requires the separate argument above.

It exhaustively verifies all 16 diagonal residues of the abstract 2-adic glue, F and V stability, determinant 16 of the glued lattice, and quotient order 16. A mutated second trace -10 fails both the idempotence and lattice-stability controls. Syntax, ordinary Node, and Node --no-opt outputs matched locally.

    node --check experiments/chained-transfer-reference/ct41/ct41_verschiebung_glue.js
    node experiments/chained-transfer-reference/ct41/ct41_verschiebung_glue.js > /tmp/ct41.normal
    node --no-opt experiments/chained-transfer-reference/ct41/ct41_verschiebung_glue.js > /tmp/ct41.noopt
    diff -u /tmp/ct41.normal /tmp/ct41.noopt

Source SHA256: c94f7e76316519418cff4d09aea012c80e39491f1269074e16350254221a4be1; normal stdout SHA256: 2383d222a010898bda467ea5b98cb87ae84717211a9e3c5974812ec8c0178457. Both are local self-checks, not independent signed PCC.

## Sources and open proof obligations

- CT37/CT39/CT40 under cryptanalysis PR #1502, particularly CT39's two-field genus-two point counts and CT40's narrower Frobenius-only splitting; upstream crypto PR #3877, GEOMETRIC_JACOBIAN_DISTINCTION.md and ODD_KERNEL_CHECKPOINT.md.
- Howe and Lauter (2012), *New methods for bounding the number of points on curves over finite fields*, Lemmas 2.9–2.10 and Proposition 2.8; https://arxiv.org/abs/1202.6308 and https://doi.org/10.4171/119-1/12. Its gluing-exponent formalism predates this experiment.
- Poonen and Rybakov (2021), *Lattices in Tate modules*, https://pmc.ncbi.nlm.nih.gov/articles/PMC8670492/ .
- Shared research-KB MCP was not installed and the encrypted lead atlas was unavailable in this runtime. GitHub code searches across crypto, cryptanalysis and crypto-autoresearcher used “gluing exponent”, “Verschiebung” and “Howe Lauter”; no novelty or absence claim.

**Open:** reconstruct the actual 2-primary lattice/polarization of T0/T1/T2; independently certify native Phi2/Psi2 geometric 7-primary kernels and universal adjoints using the 12,317-class Cantor corpus; run approved complete cold rho/IC cost comparisons. No paid cloud job, benchmark, merge bypass, force push, or general ECDLP advantage. **[pcc:unverified].**
