# CT49: explicit non-split Richelot neighbors of the four new two-glue models

**2026-11-12 · [pcc:unverified] · public F_101 models only.** This is an independently executable algebraic-curve *construction candidate*, not a completed correspondence evaluator, signed proof or DLP cost claim. Exact native producer: [crypto PR #3877](https://github.com/isogeny-labs/crypto/pull/3877) head \`338d154b\`; predecessor [CT42](../ct42/CT42_MAXIMAL_GLUE.md) and [CT48](../ct48/CT48_LOCAL_SMITH.md). The separate older [TARGET_FROBENIUS.md](../TARGET_FROBENIUS.md) used the same branch-permutation idea on *different* genus-two fixtures; this report applies it to the four newly constructed even-sextic models, with explicit codomains.

## Finding: two nondegenerate rational Richelot kernels per model

The four actual two-glue curves have equations \`y²=f(x)\`, with ascending coefficients:

| Source | f[0..6] | Branch factorization over F_101 |
| --- | --- | --- |
| Cpi1 | 52,0,25,0,77,0,84 | 84 (x³+3x²+26x+3)(x³-3x²+26x-3) |
| Cpi2 | 72,0,85,0,14,0,93 | 93 (x³+18x²-3x+3)(x³-18x²-3x-3) |
| C10 | 89,0,93,0,8,0,61 | 61 (x³+7x²-16x-38)(x³-7x²-16x+38) |
| C20 | 40,0,45,0,75,0,18 | 18 (x³+24x²+46x+3)(x³-24x²+46x-3) |

Each cubic is irreducible over F_101 (the committed JS checker exhaustively rejects F_101 roots). Thus the six branch points form **two Frobenius three-cycles**. Of the 15 geometric perfect matchings, precisely **three** are Frobenius-stable. One matches each root to its negative, giving three even quadratics and a **vanishing Richelot determinant**. The other two pair roots in an offset of one or two along the second three-cycle. They have *nonzero determinant* and give two rational (2,2)-Richelot kernel candidates, including the exact F_101 codomain equations below. All three kernels are Galois-stable, despite none of the three individual quadratic factors of the nonzero cases being F_101-rational.

In F_101[t]/g(t), let a_i=t^(101^i), i=0,1,2, and
\`q_{i,j}(x)=(x-a_i)(x+a_(i+j mod 3))\`, j=0,1,2.
Let \`Delta_j=det((constant,linear,quadratic coefficients of q_{i,j})_(i=0..2))\` and
\`B_i=q'_(i+1)q_(i+2)-q_(i+1)q'_(i+2)\`, with indices modulo three. The native-reference normalization for \`f=lambda * product(q_i)\` is

\`\`\`text
        H_j(x) = product_i(B_i(x)) / (lambda * Delta_j^3).
\`\`\`

The trace of \`Delta_j\` and all coefficients of \`H_j\` are fixed by Frobenius. The JS checker constructs these in the cubic field, verifies Frobenius covariance on every factor, descent of every coefficient, the nonzero determinant, the full 7-coefficient polynomial, and both finite-field point counts. The separately written local Python cubic arithmetic and prime-field polynomial Euclidean oracle agreed. This is the standard Richelot bracket formula with the scalar convention pinned; a general Mumford correspondence is **not** implemented here.

## New exact target sextic presentations

Every list below is **ascending** coefficients of \`H(x)=h0+h1 x+...+h6 x^6\`. The two shifts for each source differ by \`x -> -x\` and so represent *at most four* target isomorphism classes among the eight presentations. No claim of distinctness from the old T_i or of additional catalog classes is made.

| Source | Shift 1: Delta / H coefficients | Shift 2: Delta / H coefficients |
| --- | --- | --- |
| Cpi1 | **50** / 46,8,49,99,4,78,54 | **51** / 46,93,49,2,4,23,54 |
| Cpi2 | **81** / 77,81,100,16,0,40,71 | **20** / 77,20,100,85,0,61,71 |
| C10 | **73** / 49,17,85,87,33,9,10 | **28** / 49,84,85,14,33,92,10 |
| C20 | **34** / 25,98,69,38,52,39,76 | **67** / 25,3,69,63,52,62,76 |

For **all eight target sextics**, independently constructed Python polynomial-gcd/Frobenius tests give six-cycle branch factorization and squarefreeness, and Python two-field character enumeration gives \`N1=120, N2=10436, #J(F101)=12317\`. The separately authored committed JavaScript constructs the same eight exact targets and rechecks \`N1/N2/#J\` without using the Python algorithm. No retwist was selected by matching orders.

## A strict parity gate for proposed chain edges

The original T0/T1/T2 four-glue sextics have one six-cycle on their six branch roots (CT42, independently reproduced locally). The new Cpi/C10/C20 two-glue sextics have two three-cycles. Using the standard even-subset/complement description of geometric Jacobian 2-torsion gives:

| Class | \`#J[2](F_(101^3))\` | Frobenius-stable perfect matchings |
| --- | ---: | ---: |
| T0/T1/T2, 6-cycle | 4 | 1 |
| Cpi1/Cpi2/C10/C20, 3+3 | 16 | 3 (one degenerate, two nondegenerate) |

An F_101-isogeny of **odd degree** restricts to an isomorphism of 2-torsion Galois modules; it must preserve the number of Frobenius-cubed fixed 2-torsion classes. Thus **no odd-degree isogeny from any listed T_i to any listed two-glue model** is possible [pcc:unverified]. This does *not* contradict PR #3877's degree-7/49 or degree-101 partial-Frobenius routes: those are between two-glue quotient surfaces \`C0 -> C10/C20/Cpi1/Cpi2\`, not \`T_i -> Cpi\`. The Richelot degree-four candidate edges are compatible with this parity obstruction.

This parity and matching argument uses established Richelot/branch-point theory; it is a new *application to these fixtures*, not a new general theorem.

## Reproduce (no paid compute)

\`\`\`sh
python3 -B experiments/chained-transfer-reference/ct49/ct49_branch_audit.py
python3 -O -B experiments/chained-transfer-reference/ct49/ct49_branch_audit.py
node --check experiments/chained-transfer-reference/ct49/ct49_richelot.js
node experiments/chained-transfer-reference/ct49/ct49_richelot.js
node --no-opt experiments/chained-transfer-reference/ct49/ct49_richelot.js
\`\`\`

Local Python cubic arithmetic separately derived Delta_j=(0,50,51),(0,81,20),(0,73,28),(0,34,67) and all eight codomains, independently of the JS implementation; its full local reproduction package and the original ordinary/optimized outputs are retained as supplemental files outside this PR. The committed Python instead audits seven original curves via a *different* full quadratic-character method over F_(101²), reconstructs the Frob³ fixed even-subset classes, and verifies the seven recorded Weil polynomials. Normal and optimized Python and ordinary and no-opt Node passed locally. The bounded workflow reruns the committed oracles. The producer cannot self-sign scientific results: **[pcc:unverified]**.

## Sources, unresolved bridges and next strongest discriminators

Sources checked before construction: crypto PR #3877's \`PARTIAL_FROBENIUS_PROOF.md\`, \`UNBALANCED_MODEL_PROOF.md\`, its native \`richelot.rs\` bracket normalization, CT42's actual six-cycle \`J[2]\` data, cryptanalysis \`TARGET_FROBENIUS.md\`; standard Richelot theory in Bruin–Doerksen (2011), DOI [10.4153/CJM-2011-039-3](https://doi.org/10.4153/CJM-2011-039-3), and Kunzweiler's Richelot correspondence as referenced by native. Shared research-KB and locked atlas are not accessible to this runtime; no novelty/absence inference.

**Next:** independently evaluate each nondegenerate correspondence on every class of the source 12,317-element Jacobian, including nonmonic charts, all ramified and nonsplit divisors and infinity fibres; verify degree-four group homomorphism, kernel, dual \`dual * map=[2]\`, and explicit orientation against the old T_i. Determine whether any target is already a named catalog surface. Only then assemble a full cold construction/transport/recovery/solve cost comparison with optimized rho and the existing index-calculus baseline under approved EKS/S3 budget. The present result is **explicit codomain and kernel geometry**, not a fully evaluated ECDLP transfer or an attack. [pcc:unverified]


## Exact finite-field isomorphism exclusion for the four target classes

The independent C++ enumerator [ct49_pgl2.cpp](ct49_pgl2.cpp) traverses all
\`|PGL₂(F_101)|=(101+1)·101·100=1,030,200\` projective fractional-linear
changes of hyperelliptic x-coordinate for **each pair**. It normalizes the
four matrix entries either to \`c=1\` or \`c=0,d=1\`, checks nonzero determinant,
and compares the *homogeneous binary sextics* at seven distinct F101 points.
A polynomial of degree at most six vanishing at all seven is zero, so this
is exhaustive rather than a probabilistic root sampling. The scale factor
is allowed to be **any nonzero F101 element**, not merely a square; zero
matches therefore exclude both F101-isomorphism and scalar quadratic-twist
equivalence. The test does not distinguish unpolarized isomorphisms of
the resulting Jacobians.

**Result [pcc:unverified]:** zero equivalences in the twelve comparisons
between the three older T0/T1/T2 models and the four new target
representatives; also zero equivalences in all six pairwise comparisons
among the four new target representatives. The two shifts for each source
are related by x↦−x and have a verified positive equivalence. Consequently
the eight Richelot sextic presentations give **exactly four distinct
F101 genus-two curve-isomorphism classes**, all different from the three
T_i models even allowing quadratic twists. These are not proven to be
previously absent from the broader fixed 72-Jacobian catalog.

Three mutation controls reject false-negative-only checkers: the self-pair
T0/T0 has one detected projective equivalence, the x-mirror pair has
one, and the altered T0 constant coefficient 31→37 has none.
Both \`g++ -O0\` and \`g++ -O3\`, with \`-Wall -Wextra -Werror\`,
give byte-identical outputs; the bounded workflow reruns both.

\`\`\`sh
g++ -O3 -std=c++17 -Wall -Wextra -Werror \
 experiments/chained-transfer-reference/ct49/ct49_pgl2.cpp -o /tmp/ct49-pgl2
/tmp/ct49-pgl2
\`\`\`

A full nonmonic Cantor correspondence, polarization/duality and the
actual endpoint subgroup costs are still open. The exhaustive PGL2
check certifies a **curve-model classification under this exact field**,
not an independently signed theorem or an ECDLP solving advantage.
