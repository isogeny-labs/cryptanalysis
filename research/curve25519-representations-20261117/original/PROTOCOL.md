# Scope fixed before the toy computations — 2026-11-17

This is a standalone mathematical research bundle, outside the repository benchmark and candidate registries. It uses repository research notes as prior work. No IC speedup, wall-time ratio, asymptotic exponent, or independently replayed benchmark is claimed. All local executions are CPU correctness tests and finite-set diagnostics; no remote resources are provisioned.

Five requested directions: torsion invariants; equation systems retaining intermediate variables; coordinate-dependent and structured factor bases; low-degree isogenies; bounded integer lifts. Extra encoding check: Elligator 2.

Fixed toy fields: 101,229,461,929,1861,3733. Select the first Montgomery coefficient A>=3 with a nonsingular curve, square -(A+2), nonsquare d=-(A-2)/(A+2), and group order 8*r with r prime >=11. Select up to 3 qualifying coefficients per field, scanning A<min(p-2,1000). Save every selected exact instance. No result-dependent replacement. Require a generator G of order r. Use full subgroup enumeration solely for exhaustive diagnostics, never as an efficient attack ingredient.

Factor-base diagnostics: choose k=min(12,max(3,floor(sqrt(r)/2)),(r-1)//2) sign classes by sorting Montgomery u, Edwards y, invariant z=u+1/u, or a fixed-seed random permutation. Equal k on each instance. Include the unchanged base transported to the 2-isogenous curve as a paired identity control. Count all two-summand sums using both signs, and all target points in the subgroup. Report exact coverage, identity inclusion, and collision multiplicity; these are not runtime measurements. Keep full point lists so results are replayable. A/A: reverse enumeration must preserve coverage. Positive: planted pairs must be detected. Negative: factor-base-empty query check. Include cofactor-1 a=-3 controls over the same field and separate subgroup-size-matched fields; do not treat different subgroup orders as an isolated torsion effect.

Equation diagnostics: compare transported same-base two-summand S3 equations in u, shifted Weierstrass X, Edwards y, and quotient z; report input term count and degrees, and compare candidate roots with exact point decompositions. Retained-variable and projective formulations are checked algebraically and by planted relations; no F4/F5 performance result is inferred from sparsity. SymPy is an available reference symbolic engine, not a production F4 implementation.

Isogeny tests: explicit 2-isogeny with kernel {O,(0,0)}, target coefficients (-2A,A^2-4,0), on-curve, addition, order, injectivity on H, and exact transported-base coverage checks. No volcano-level claim.

Integer lifts: scan integer u in [-10000,10000] for the fixed rational model v²=u³+A*u²+u. Count exact integer squares and reduction images in toy H. Also scan A=486662. This excludes neither rational points with denominators nor alternative lifts; no general lifting impossibility claim follows.

Real Curve25519 checks and small-factor inspection of p-1 were performed while the workspace started and are explicitly preliminary, not preregistered by this file. Preserve those records separately. Further real-parameter checks must be reproducible from code.

Uncertainty: no sampling error for exhaustive finite sets; no inference to unseen curves or cryptographic sizes. Fixed-seed random bases are controls, not a statistical ensemble. Stop after the fixed fields and bounded coefficient/lift scans; retain empty selections and failures. Conclusions: identity confirmed/refuted; finite-set difference; solver-performance unknown; no verified competitive attack. A proof is mathematical derivation plus executable checks, not a formal proof-assistant theorem.
