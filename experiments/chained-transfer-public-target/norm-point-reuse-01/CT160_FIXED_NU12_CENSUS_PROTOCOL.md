# CT160 — actual fixed nu12 source/target point-count and Frobenius binding protocol

Date: 2026-11-16. Scientific standing: [pcc:unverified].

## Prior evidence and explicit distinction
CT158 counted the original cubic source and *its* quadratic twist, but the fixed nu12 source is the twist of the **third-hop** source instead. Before numerical implementation, inspect the actual `twisted-pair-preflight/src/twist_append.rs` and existing fixed-model publication `reports/twisted-pair-result-01/render-data.json`. The latter published public short-Weierstrass models over K=F_223[z]/(z^3-3):
- fixed nu12 source A=(167,76,41), B=(27,91,187);
- fixed nu12 target A=(207,175,148), B=(175,89,34);
- publicly reported prime-order subgroup q=2,771,711 and complete order 11,086,844, with public generators recorded in the source certificate.
These are **inputs**, not independently verified outcomes.

## Preregistered independent experiment
1. A standalone stdlib C++17 field implementation (not the Rust isogeny library) enumerates every x in K for each *actual* fixed source and target. Build a square-character roster from all 223^3 field squares using z^3=3. Record number of zero, nonzero-square and nonsquare curve RHS values and exact #E=1+n_zero+2*n_square, with internal partition checks.
2. Separately, a Python-only field/group implementation (different formulas from the C++ roster) checks both public model/generator pairs, validates q primality by exact trial division, computes [q]G, and certifies uniqueness of the Hasse-interval multiple of q. Check that the public generators are nonidentity.
3. Negative controls: increment the source curve's B constant coefficient and recount the entire mutated curve; deliberately mutate each generator and reject changed/faulty subgroup certificates. Check Python ordinary versus -O equivalence.
4. Acceptance: both original actual fixed source and target full point counts equal 11,086,844, nonzero-point certificates pass independently, every mutation is rejected, and the fixed nu12 trace is +2724. A change in count, failed generator certificate, inconsistent counts or unsupported field arithmetic is an explicit negative, not a reason to change the fixture.
5. Derive a source-specific base-change obstruction: for each integer t with t²<=4*223, compute cubic trace t³-3*223*t; prove it never equals +2724 and record minimum gap. Only with the *actual source* count should this conclusion be applied to its Weil restriction. Equality of finite-field elliptic trace implies existence of a K-isogeny, **not** a computed rational map or a complete DLP transfer.

## Guardrails and reproducibility
This is free bounded local integer arithmetic only, no EKS, GPU, paid capacity, original 695/701 Jacobian replay, primitive timing, native fixture mutation or protected merge. Prior source literature: CT151/CT152/CT158 and the published rational degree-13 third-hop implementation; standard Tate isogeny theorem for elliptic curves over finite fields. The experiment does **not** prove the proposed degree-eight Jacobian quotient is defined over F223, nor deliver a cold complete prime-field ECDLP advantage. Independent signed PCC remains pending. No novelty claim.
