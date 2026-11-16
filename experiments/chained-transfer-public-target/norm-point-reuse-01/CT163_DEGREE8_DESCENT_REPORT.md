# CT163 — complete Galois-stable degree-eight kernel screen for fixed nu12

2026-11-16 · **[pcc:unverified]** · Additive source-only finite-level follow-up to CT160–162. The finite pattern was explored locally before the prospective repository protocol; the committed comparative replay follows \`CT163_DEGREE8_DESCENT_PROTOCOL.md\`. Nothing here is a native transferred ECDLP solve.

## Actual input and what is being constructed

Let \(k=\mathbb F_{223}\), \(K=\mathbb F_{223^3}\), and let \(E/K\) be one *actual fixed nu12 elliptic endpoint*, not the earlier unrelated original q223 curve. CT160's source-only exhaustive census reports \(\#E(K)=11,086,844=4\cdot2,771,711\), and three \(K\)-rational roots of \(y=0\), so \(E[2](K)\simeq(\mathbb Z/2)^2\). These are inherited, unsigned CT160 inputs; no independent native source binding or signed PCC is newly asserted.

Set \(A=\mathrm{Res}_{K/k}(E)\). The canonical product principal polarization after base extension to \(\bar k\) makes
\[
  A[2](\bar k)\simeq W=(\mathbb F_2^2)^3,\quad
  \langle v,w\rangle=\sum_{i=0}^{2}(a_i b'_i+b_i a'_i)\in\mathbb F_2.
\]
Pick a basis of \(E[2](K)\) and its Frobenius-conjugate bases on the three factors. Arithmetic \(k\)-Frobenius acts by \(F(v_0,v_1,v_2)=(v_2,v_0,v_1)\); \(F^3=1\). This action is *not* the scalar \(p\)-power map on each coordinate of an arbitrary fixed basis; the bases must be conjugated coherently.

Every \(F\)-stable 3-dimensional totally isotropic subspace \(H\leq W\) is an order-eight subgroup scheme defined over \(k\). Standard polarization descent gives a separable degree-eight isogeny \(A\to B=A/H\) of \(k\)-abelian varieties, and a principal polarization on \(B\) whose pullback is twice the polarization on \(A\). This is an **abstract algebraic quotient**: no explicit quotient equations, fast map evaluation or genus-3 curve are constructed here.

## Exhaustive enumeration

The Python implementation obtains all rank-three subspaces from spans of 3-tuples among the 63 nonzero vectors, deduplicating by full spans. The independent JavaScript implementation enumerates unique reduced-row-echelon bases. Both locally gave identical canonical JSON (including every kernel), identical optimized-Python output, and each rejected six deliberate mutations. Frozen source-only SHA-256 of the canonical single-line output with newline: \`8bed32aa7b27d81ee45c19d6650494e80ffdd573f2d7f6f4dea897d4bdb06602\`. A hosted CI result must be checked separately; these are producer-local checks, not signed independent execution. **[pcc:unverified]**

| Exact finite count | Result |
|---|---:|
| All dimension-3 subspaces of \(\mathbb F_2^6\) | 1,395 |
| Symplectic Lagrangians | 135 |
| Frobenius-stable Lagrangians | **9** |
| Factorwise line-product kernels | **3** |
| Mixed kernels, zero intersection with each isolated factor | **6** |
| \(k\)-rational points of each kernel \(H(k)\) | **2** |
| \(K\)-rational points of each kernel \(H(K)\) | **8** |

Canonical basis representatives (each generator is a six-bit integer, factor \(i\) occupying bits \(2i,2i+1\)):

- Factorwise: \`(1,4,16)\`, \`(2,8,32)\`, \`(3,12,48)\`.
- Mixed: \`(5,17,42)\`, \`(5,17,43)\`, \`(10,21,34)\`, \`(10,23,34)\`, \`(15,21,38)\`, \`(15,22,37)\`.

All 9 full eight-element subspaces, with canonical bases, factor support and Frobenius-fixed counts, are preserved in \`CT163_RESULT.json\`.

There is also a useful counting check: \({6\brack3}_2=1395\) and the number of Lagrangians in a 6-dimensional symplectic \(\mathbb F_2\)-space is \((2+1)(2^2+1)(2^3+1)=135\). Since \(3\) is odd, the \(C_3\) action is semisimple over \(\mathbb F_2\); the 2-dimensional fixed module and 4-dimensional nontrivial isotypic module constrain an invariant Lagrangian to a line plus a 2-dimensional invariant isotropic piece, consistent with \(3\times3=9\). The enumeration gives explicit exhaustive witnesses and verifies stability/pairing, rather than treating this structural count as a genus-3 existence theorem.

## Consequences for proposed genus-3 transfer

The three factorwise kernels are Weil restrictions of \(K\)-rational order-two lines and give \(\mathrm{Res}_{K/k}(E/L)\) with *geometrically product* principal polarization. They do **not** give principally polarized Jacobians of smooth geometrically connected genus-3 curves. The **six mixed kernels** remain candidate principally polarized threefolds; finite 2-torsion gluing alone does **not** show their polarizations are geometrically indecomposable or that they arise as Jacobians (hyperelliptic or plane quartic). The previously screened four CT162 hyperelliptic branch-orbit patterns are a separate necessary condition and have not been matched to any particular quotient.

Since the selected source subgroup has odd order \(r=2,771,711\), each kernel \(H\) has \(H\cap A[r]=0\). Thus every resulting abstract quotient homomorphism is injective on the original \(r\)-primary subgroup. This provides a **DLP-preservation argument for this extension-field source if and when an explicit quotient evaluator is constructed**. It does not provide an inexpensive complete solver: the image of a public point, target-group representation, genus-3 divisor arithmetic, relation search and logarithm recovery remain to be implemented and priced.

Importantly, the CT161 irreducible degree-six Frobenius polynomial \(\ X^6-2724X^3+223^3\ \) implies \(A\) and every \(k\)-isogenous quotient \(B\) are \(k\)-simple of dimension 3. Hence **no nonzero \(k\)-defined homomorphism from an elliptic curve over \(\mathbb F_{223}\) into any of these \(B\)** exists. These nine kernels cannot, *by themselves*, supply the owner's required prime-field elliptic-input transfer: the source here is \(E(\mathbb F_{223^3})\).

## Controls, reproduction, research governance

From the checkout root:

\`\`\`sh
D=experiments/chained-transfer-public-target/norm-point-reuse-01
python3 -B "$D/ct163_degree8_lagrangians.py" --self-test > /tmp/ct163-py.json
python3 -O -B "$D/ct163_degree8_lagrangians.py" --self-test > /tmp/ct163-opt.json
node "$D/ct163_degree8_independent.cjs" --self-test > /tmp/ct163-js.json
cmp /tmp/ct163-py.json /tmp/ct163-opt.json
cmp /tmp/ct163-py.json /tmp/ct163-js.json
cmp /tmp/ct163-py.json "$D/CT163_RESULT.json"
sha256sum /tmp/ct163-py.json
\`\`\`

Controls reject: non-isotropic rank-three spans, wrong dimension, Frobenius-nonstable isotropic spans, zero-pairing sabotage, identity-Frobenius sabotage, false full source 2-torsion assumption. The independent RREF enumeration is algorithmically different but still producer-authored; signed PCC is not present. New bounded source-only workflow \`ct163-degree8-descent.yml\` does not invoke Cargo, EKS, paid GPU, actual source/Jacobian native diagnostics or protected merges.

Research checked: CT160/161/162 original reports, CT125 #1533 source audit, root crypto #3877, concurrent explicit genus-3 #4357 and GHS #4301, CT141 owner-admitted timing path #1562, and Costa–Donepudi–Fernando–Karemaker–Springer–West, *Restrictions on Weil Polynomials of Jacobians of Hyperelliptic Curves*, Springer (2022), DOI [10.1007/978-3-030-80914-0_7](https://doi.org/10.1007/978-3-030-80914-0_7). The shared research-KB/Conductor interfaces were unavailable in the connector runtime; no absence/novelty statement is inferred.

## Owner priority / next experiment

Retrieve original **complete** 695/701 native original/reuse logs (the published 48-row subset is not enough), perform independent whole-record parity with every exception retained, and run genuine paired isolated same-host \(C_{169},C_{13a},C_{13b},D\) pricing **only after owner budget/admission**. Follow with a genuinely complete cold *prime-field* public-target ECDLP comparison against optimized rho/BSGS/IC, including all setup, map, corrections, linear algebra, verification, process/memory cost, uncertainty and signed independent PCC. Existing CT163 result is a finite necessary engineering screen, not a demonstrated speedup. **[pcc:unverified]**
