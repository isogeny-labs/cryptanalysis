# Prime-ideal overlap of relative discriminants and pair resultants

The quartic and octic j=1728 factor discriminants have an exact place-by-place decomposition above the unramified common rational primes 7, 11, 23, and 31. In particular, **23 contributes to both integer norms but to no common prime ideal** of the degree-18 source field. The rational-prime gcd from [the root-support certificate](../hecke-432-j1728-root-prime-support-20261026/RESULT.md) therefore overstates local overlap at 23.

For each factor `q_d=g_+g_-` over `L=K(√2)`, this experiment forms `E_d=Disc(g_+)Disc(g_-)` and `R_d=Res(g_+,g_-)` in `K`. It verifies `Disc(q_d)=E_d R_d²`, then records their ideal valuations at every prime `P` of `K` over the selected rational prime. The norm-weight check is `v_p(N_K/Q(E_d))=Σ_P f(P/p)v_P(E_d)`, and likewise for `R_d`.

| Factor degree over K | p=7 common places | p=11 common places | p=23 common places | p=31 common places |
| ---: | --- | --- | --- | --- |
| 4 | none | one degree-1 and one degree-2 | none | none |
| 8 | three degree-2 | one degree-1 and one degree-2 | none | three degree-2 |

The full ideal generators, residue degrees, both valuations, weighted norm valuations, and source-field coefficient vectors are in [`result.json`](result.json). The p=31 quartic cell has neither component in its norm support. At 23 both components have positive rational norm valuation in both factors, but their prime-ideal supports are disjoint. The present calculation identifies shared places; it does not determine inertia or a full relative discriminant ideal of the factor fields.

[`protocol.json`](protocol.json) freezes four input hashes and a 240-second cap. The checked-Sage run completed in about 65 seconds; [`sage-runtime-info.txt`](sage-runtime-info.txt) and [`attempt.json`](attempt.json) record the runtime and execution. [`audit.py`](audit.py) independently reduces the saved `K` elements and defining polynomial modulo each unramified prime. Its factor-by-factor divisibility and polynomial-gcd degrees reproduce every positive-support pattern; see [`audit.json`](audit.json). This finite-field audit checks whether each valuation is positive, while the checked-Sage ideal arithmetic supplies the exact higher valuations.

## Proof map

[`formal/IdealOverlapTables.lean`](formal/IdealOverlapTables.lean) defines the finite prime-ideal row model and kernel-checks eight declarations `degree_<d>_prime_<p>_check`. Each verifies the exact saved overlap count and both residue-degree-weighted valuation sums. [`formal/lean-check.txt`](formal/lean-check.txt) records the build and `#print axioms` results; all eight table theorems use no axioms. Formalization of the concrete number field, its prime ideals, and the valuation computations is **partial**. The exact missing bridge is a Lean representation of these `K` elements and their ideal valuations that proves the input rows; checked Sage and independent finite-field reduction currently supply that bridge empirically.

The next calculation is local in the factor extensions: at the overlapping places above 7, 11, and 31, determine whether the factor-field maximal orders ramify or whether the polynomial discriminant valuations are partly explained by nonmaximal orders. The p=23 places provide a useful disjoint-support control.
