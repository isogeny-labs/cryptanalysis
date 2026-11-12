# CT43: mod-4 anti-isometry census and mod-8 obstruction for E109/E113

**2026-11-12 | [pcc:unverified]**. This is an exhaustive *elliptic-factor torsion-module* classification, not a computation of the actual T0/T1/T2 gluing graph. It is classical finite-ring/Weil-pairing arithmetic, not a new algorithm or speedup.

## Hypothesis and scope

CT39 gives E109 and E113 over F101 with Frobenius traces t1=-7, t2=-11 and common determinant p=101. CT42 conditionally proves the actual three Jacobians have an unpolarized (Z/4)^2 gluing quotient. Does a Galois-equivariant maximal isotropic graph exist on the **fixed pair** at level four? Can a full graph exist at level eight? Negative controls: mutate one trace modulo four and replace an anti-isometry by determinant-one isometry.

The mod-2 characteristic polynomial is X²+X+1, irreducible over F2. Consequently the rank-two 2-adic modules are cyclic as modules for Frobenius, with lifted companion bases and

    F_t = [[0,-101],[1,t]].

Because t1=t2=1 modulo four, both Frobenius matrices modulo four are F=[[0,3],[1,1]]. Its entire centralizer in M2(Z/4) is the two-parameter ring (Z/4)[F]. A unit intertwiner is U=aI+bF, with

    det(U)=a²+t1*a*b+101*b² (mod 4).

The 16 pairs (a,b) yield 12 units: six of determinant 1 and **six of determinant -1=3**. On symplectically normalized companion bases, determinant-three means Weil-pairing reversal. A concrete candidate is U0=I+2F=[[1,2],[2,3]], with det=3. Since F has order six modulo four, all six anti-isometries are exactly U0*F^i, i=0,...,5.

The initial companion bases may scale their Weil forms by different odd units c1,c2, but the Frobenius centralizer contains elements of both determinants 1 and 3. Thus the bases can be normalized without changing their F matrices; **six** anti-isometries exist for the actual abstract E109[4],E113[4] modules. Their Frobenius-stable graph subgroups each have order 16 and are maximally isotropic for the product Weil pairing. Sign U↔-U identifies six choices in three unordered pairs via negating one elliptic factor. **No pairing of these three candidates with T0, T1, T2 has been established.**

In contrast t1≡1 and t2≡5 (mod 8). Frobenius would have equal trace on two isomorphic 8-torsion modules; hence there is **no invertible Frobenius-equivariant E109[8]→E113[8]**, and none at 2^n for n≥3. This is a sharp **full-graph** obstruction for these factor traces; it says nothing about partial, non-graph kernels, or different auxiliary factors.

## Independent reproducibility

The standalone Python program searches all invertible 2×2 matrices over Z/2, Z/4, and Z/8; it finds respectively 3, 12, and 0 intertwiners. Each of the six level-four anti-isometries has all 16 graph elements, is Frobenius-stable, and has all 256 symplectic pair tests equal zero; all determinant-one alternatives fail maximal isotropy. A wrong-trace mutant finds zero candidates. The separate JavaScript checker uses only the aI+bF norm formula, checks all 16×16 Weil form scalings, and independently gives six determinant-three and six determinant-one units, with three sign-pairs. These independent oracles are *arithmetic* checks, not signed scientific verification.

    python3 -B experiments/chained-transfer-reference/ct43/ct43_mod4_glue.py
    python3 -O -B experiments/chained-transfer-reference/ct43/ct43_mod4_glue.py
    python3 -m py_compile experiments/chained-transfer-reference/ct43/ct43_mod4_glue.py
    node --check experiments/chained-transfer-reference/ct43/ct43_independent.js
    node experiments/chained-transfer-reference/ct43/ct43_independent.js
    node --no-opt experiments/chained-transfer-reference/ct43/ct43_independent.js

## Prior art, dependencies, and next falsifiable step

Primary reference: Bruin–Doerksen (2011), *The Arithmetic of Genus Two Curves with (4,4)-Split Jacobians*, https://arxiv.org/html/0902.3480v3 , especially §§2,5–7, for anti-isometry graphs and Richelot gluing. See also Howe–Lauter (2012), https://arxiv.org/abs/1202.6308 , and CT37/CT39/CT41/CT42; root crypto #3877 and consumer cryptanalysis #1508. Shared research-KB MCP and wrapped catalog were inaccessible in this runtime; do **not** infer absence of earlier work. Literature was consulted before implementation.

The next discriminating test is **actual** E_i[4] bases from the quartic elliptic quotient embeddings, ramified Y=0 and nonsplit divisor pullbacks, Weil pairing and graph selection. Compare to native geometric Phi2/Psi2 dual/kernel and independently replayed Cantor corpora, keeping geometry separate from module census. Fully priced rho/index-calculus runs require live EKS/S3 budget admission. No paid compute, merge override, or verified PCC claim here.
