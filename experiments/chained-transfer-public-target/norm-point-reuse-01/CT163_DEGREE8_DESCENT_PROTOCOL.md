# CT163 — prospective finite 2-torsion gluing search for fixed nu12

2026-11-16. [pcc:unverified]. Additive source-only follow-up to CT160–162 on cryptanalysis #1589; no native Jacobian arithmetic or paid execution.

## Priority and coordination

Checked crypto root #3877, cross-repo active #4357 (explicit genus-3 transfers), #4301 (GHS), cryptanalysis parent #1533, owner-admitted primitive run #1562, and CT162. This is a **new finite level-2 descent filter** on the *fixed nu12* Weil restriction, NOT duplication of #4357's genus-3 curve constructions. Shared research-KB and Conductor cannot be called from this connector environment; fallback is the linked primary files/PRs and Costa et al. (2022), DOI 10.1007/978-3-030-80914-0_7. Consult Howe–Leprévost–Poonen split-Jacobian gluing as contextual literature; no novelty or unproved global-Jacobian claim.

The mathematical exploratory enumeration of potential stable kernels occurred **before** this protocol; treat the discovery as retrospective. This protocol freezes the subsequent executable independent-implementation, negative controls and reporting requirements.

## Input and claim boundaries

Let k=F_223, K=F_(223^3), and E/K be the actual fixed nu12 endpoint counted in CT160. The frozen source evidence reports full E(K)[2] of size 4 and order 11,086,844, with trace 2724 over K. Put A=Res_(K/k)(E), carrying the induced product principal polarization after geometric splitting. Geometrically A[2] is W=(F_2^2)^3 with the direct-sum standard alternating form. Since E[2] is K-rational, arithmetic k-Frobenius acts on W as a cyclic permutation of the three factors after choosing Frobenius-compatible bases.

Do not assume that `W` identifies with a computable point map on arbitrary inputs or that an 8-isogenous principally polarized quotient is a Jacobian, much less an index-calculus advantage. No global cross-characteristic transfer is inferred.

## Precommitted finite calculation

1. Enumerate all 3-dimensional subspaces of F_2^6 by their full eight-element spans; show independently that 135 are symplectic Lagrangians.
2. Filter for Frobenius cyclic invariance; count and publish canonical sorted eight-element subspaces, basis vectors, rational fixed subgroup sizes, and factor-support pattern for each. Distinguish local product-line kernels (one nonzero line from each factor) and genuinely mixed kernels (no nonzero vector supported on a single factor).
3. Verify each displayed kernel has eight elements, alternating form vanishes pairwise, Frobenius acts bijectively, and every invariant subspace is included once. Independently implement exhaustive enumeration in *Python and Node* with different algorithms (row-span combinatorics vs 3-subspace RREF).
4. Include negative controls: nonisotropic 8-element span; dimension-2 span; isotropic but Frobenius-nonstable span; altered pairing; altered permutation; malformed source assumption about the size of E(K)[2]. Reject every control; compare full canonical stable-kernel lists byte-for-byte across languages.
5. Optionally calculate abstract diagonal GL_2(F_2) orbits on these finite subspaces, without identifying quotients as geometric isomorphism classes (not every mod-2 matrix lifts to an automorphism of E).

## Mathematical conclusion permitted

For each Galois-stable Lagrangian kernel H⊂A[2], the separable quotient A/H over k has a descended principal polarization of degree one, with pullback twice the original. Three factorwise kernels yield geometrically decomposable principally polarized products; their quotient cannot be a smooth genus-3 Jacobian with its canonical polarization. The mixed kernels are *candidates only*; existence of a smooth k-curve, explicit maps, DLP preservation and fast cost remain separate proof obligations. Distinguish this degree-eight kernel screen from CT162's mod-2 hyperelliptic branch-orbit necessary condition.

## Gates and constraints

The original 695/701 full Jacobian native original/reuse parity, native C169/C13a/C13b/D and matched rho/BSGS/IC cold solves remain the owner priority, with setup, transports, corrections, LA, verification, RSS, uncertainties and signed PCC. Do not touch the CT125/CT141 code or frozen source/ledgers, execute owner-admitted jobs without approval, merge any PR, or claim a speedup from this finite screen. Source-only CI may run the two small scripts and their negative controls. [pcc:unverified].
