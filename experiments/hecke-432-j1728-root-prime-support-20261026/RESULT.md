# Exact common prime support of the j=1728 discriminant roots

The relative discriminant sixth root and conjugate-pair resultant cube root share a fully determined, small prime support for each base factor. Their exact greatest common divisors are

| Factor degree over the degree-18 source field | Complete common-root gcd factorization |
| --- | --- |
| 4 | `2^6 · 3^3 · 7^2 · 11^2 · 23^2` |
| 8 | `2^39 · 3^20 · 7^8 · 11^4 · 23^4 · 31^2` |

The factors in the table are prime. Consequently every other prime divisor of either root is absent from the other root. This isolates the shared component of the exact discriminant norm decomposition from [the preceding certificate](../hecke-432-j1728-discriminant-norms-20261026/RESULT.md). It also supplies a compact cross-check for future local ramification calculations.

[`protocol.json`](protocol.json) fixes the source digest and a deterministic prime division cap of one million. [`run.py`](run.py) computes the exact integer gcd first, divides it by all primes up to the cap, and checks that no residual remains. The same script records bounded small-prime divisions of each full root, reconstructs the input integers from the factors and residuals, and checks the two residuals are coprime. The full factors and residual integers are in [`result.json`](result.json). The residuals of the individual roots are **not** assigned primality or full factorizations by this run; only the common gcd has a complete factorization.

## Proof map

[`formal/RootGcd.lean`](formal/RootGcd.lean) has kernel-checked `degree_4_root_gcd` and `degree_8_root_gcd` for the exact 37/72- and 245/335-digit saved root pairs, and `degree_4_gcd_factors` and `degree_8_gcd_factors` for the exact products shown above. All four `#print axioms` checks report only `propext`; [`formal/lean-check.txt`](formal/lean-check.txt) records the command, pinned Lean/mathlib versions, and checker availability. The source-field discriminant and resultant identities remain tied to the checked Sage construction and the proof map in the preceding certificate. The next mathematical step is to identify which primes in these roots divide the field index or relative discriminant ideals, so that integer norm support is linked to local splitting and inertia.
