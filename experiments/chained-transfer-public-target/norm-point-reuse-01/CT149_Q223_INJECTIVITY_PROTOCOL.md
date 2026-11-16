# CT149 — q223 degree-13/169 injectivity certificate protocol

Date: 2026-11-15 America/Denver. Root: crypto#3877; continuation cryptanalysis#1589. [pcc:unverified]

## Scope and frozen source custody

This is a mathematical necessary-condition audit, not an ECDLP benchmark or a certificate of the actual rational map formulas. Do not edit CT148, original q223 Rust, 695/701 records, fixtures, PCC ledger or cost workflows. No paid compute.

Source-reported q223 original model: subgroup ell=2,773,073, full group order 11,092,292 (root #3877 2026-11-15 session log). Source-reported alternative fixed-nu12 model: subgroup ell=2,771,711 (CT129 #1537 protocol), full group 11,086,844 (root fixed-model log). Treat parameters as unverified until separately reproduced against original field, generator and point-count sources. Never substitute the alternative for original.

## Mathematical proof obligation

Let gamma:E->E' be an actual finite isogeny over a field, of degree d dividing 13^2, and H a finite subgroup of E with gcd(|H|,d)=1. Its geometric kernel has at most d elements (exactly d in separable case). Therefore H intersects ker(gamma) trivially; gamma is injective on H. For H=<G> order n, ord(gamma(G))=n. This extends to a composition of degree-13 maps. If a dual gamma_hat satisfies gamma_hat gamma=[d], then multiplying gamma_hat by d inverse modulo n gives a left inverse on H (for H of exponent n). Actual map degree, dual composition, descent and source parameters are separate required validations.

This only rules out CT148's 13-primary collision on the specified certified group. It does not certify q223 maps, Jacobian transfer, cofactor corrections, 695/701 parity, single-target costs or signed PCC.

## Predeclared checks

1. Hardcode both distinct source-reported subgroup and full-group orders. Require full=4*ell. Prove each ell prime by deterministic complete trial division through integer sqrt (no probabilistic libraries).
2. Require gcd of each subgroup and full-group order with 13 and 169 equals one; compute and check exact inverses of 13 and 169 modulo both ell values.
3. Explicit negative controls: modulus 104 has a 13-factor and lacks inverse; a deliberately mismatched full-group order must be rejected.
4. Deterministic JSON. Normal and optimized Python must agree byte-for-byte. Scoped CI only executes source-only arithmetic; never run native pricing or cloud.
5. Preserve CT148 F229 104-to-8 counterexample as valid outside these q223 groups. No measured speed claim.

## Prior sources

CT148 report/code (cryptanalysis#1589); CT129 protocol (cryptanalysis#1537); root crypto#3877 source log; CT125#1533; crypto#4215; Silverman, Arithmetic of Elliptic Curves III.4 (isogeny degrees, kernels and dual). Research-KB and Conductor unavailable in this runtime; no novelty claim. [pcc:unverified]
