# Exact sixth-power discriminant norms in the j=1728 source field

The quartic and octic factors of the degree-18 j=1728 source-field construction have **exact sixth-power absolute discriminant norms**. Their split over `K(√2)` supplies the mechanism: for each factor `q_d=g_+g_-`, the checked identity

`Disc(q_d) = Disc(g_+) Disc(g_-) Res(g_+,g_-)²`

gives `N_K/Q(Disc(q_d)) = N_L/Q(Disc(g_+)) N_K/Q(Res(g_+,g_-))²`, where `L=K(√2)`. The relative discriminant norm is an exact sixth power and the conjugate-pair resultant norm is an exact cube in both degrees, so the base norm is the sixth power of the product of their integer roots. This is an exact ramification and normalization certificate for these two factors, extending the conjugate-resultant cube certificates in the preceding experiment.

## Method and exact results

The frozen input hashes and 90-second cap for the first norm run are in [`protocol.json`](protocol.json). [`run_sage.py`](run_sage.py) reconstructs the degree-18 number field and both factors from the earlier factor certificate, checks the derivative-resultant formula for each discriminant, and computes exact number-field norms. The measured launch used the repository's checked Sage launcher; [`sage-runtime-info.txt`](sage-runtime-info.txt) records that build. [`attempt.json`](attempt.json) records completion in approximately 82 seconds. All calculations here are exact; wall time is a resource receipt, not a performance comparison.

| Factor degree over K | Base discriminant norm digits | Relative discriminant norm digits | Base sixth-root digits | Selected prime valuations of base norm |
| --- | ---: | ---: | ---: | --- |
| 4 | 648 | 220 | 108 | `4335978784654674076339691`: 6; `4196094289`: 6; `669968600281`: 6 |
| 8 | 3474 | 1465 | 579 | `414340033`: 6; `431435018569`: 6 |

The full integers, coefficients, and checked valuations are in [`result.json`](result.json), [`relative_result.json`](relative_result.json), and [`audit.json`](audit.json). For both factors the norm denominators are one. The earlier pair-resultant norms contribute the square factor exactly; their known-prime valuations are three at the corresponding primes. The independent integer replay in [`audit.py`](audit.py) checks the saved equality, sixth and cube powers, root-product identity, denominators, and listed valuations without invoking Sage.

The relative-field replay is frozen in [`relative_protocol.json`](relative_protocol.json), with its 300-second completion cap. [`relative_sage.py`](relative_sage.py) reconstructs both conjugate factors, verifies their product equals the base factor and the discriminant-product identity in `L`, then checks the exact norms and integer roots. [`relative_attempt.json`](relative_attempt.json) records completion in approximately 196 seconds. The earlier 90-second cap ended after the quartic; [`relative_attempt_90s_timeout.json`](relative_attempt_90s_timeout.json) preserves that result. The earlier failed attempts in this directory record Python/Sage rational conversion and an accidental second absolute norm during script development; they were corrected before the completed replay.

## Proof map

| Result | Lean declaration | Exact scope | Status |
| --- | --- | --- | --- |
| Sixth-power conclusion from a discriminant-norm product and cubic pair norm | `J1728DiscriminantNorms.sixth_power_from_product` | Arbitrary commutative ring, with product and power equalities as explicit hypotheses | Kernel checked |
| Relative quartic norm is a sixth power | `J1728DiscriminantNorms.relative_4_sixth_power` | Exact saved 220-digit integer and its 37-digit root | Kernel checked |
| Relative octic norm is a sixth power | `J1728DiscriminantNorms.relative_8_sixth_power` | Exact saved 1465-digit integer and its 245-digit root | Kernel checked |

The sources are in [`formal/`](formal/). [`formal/lean-check.txt`](formal/lean-check.txt) records both successful Lean builds, `#print axioms` output, toolchain and mathlib revision. The checked proofs use only `propext` from Lean's foundations; `lean4checker --fresh` was unavailable. Formalization of the polynomial discriminant-product identity and the specific number-field norm computations remains partial: the current Lean theorem takes their exact equalities as hypotheses, while checked Sage verifies those equalities from the reconstructed polynomials. A faithful Lean completion needs a source-field and relative-factor model plus the discriminant/resultant bridge, not only the saved integer statements.

The next algebraic step is to factor or otherwise characterize the 37- and 245-digit relative sixth roots and relate their prime support to ramification of the quadratic and quartic subfactors. The numerical sixth-power structure alone does not identify local inertia groups.
