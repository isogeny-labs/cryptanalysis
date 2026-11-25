# Split and inert places in the j=1728 quadratic factor fields

The unramified quadratic factors over `L=K(√2)` **split at every selected place above 7, 11, and 31**. Above 23, eighteen places split and two degree-1 places are inert in each factor. The two inert places have polynomial-discriminant valuation zero; the positive local order-index valuations recorded in [the preceding experiment](../hecke-432-j1728-relative-quadratic-local-20261026/RESULT.md) occur at split places.

Each irreducible relative quadratic factor defines a degree-72 field over `Q` (`[L:Q]=36`). The local classification gives the following residue-degree multisets for either factor:

| Rational prime | Split / inert places in L | Primes in the degree-72 factor field | Residue-degree multiset |
| ---: | ---: | ---: | --- |
| 7 | 18 / 0 | 36 | 36 of degree 2 |
| 11 | 18 / 0 | 36 | 36 of degree 2 |
| 23 | 18 / 2 | 38 | 4 of degree 1; 34 of degree 2 |
| 31 | 18 / 0 | 36 | 36 of degree 2 |

For each prime ideal `P` of `L`, [`run_sage.py`](run_sage.py) divides the quadratic discriminant `Δ` by `p^{v_P(Δ)}`. The preceding exact ideal calculation established `v_P(p)=1` and even `v_P(Δ)`, so the quotient is a local unit. Its residue `u` is a square exactly when `T²−u` has two distinct linear factors; otherwise that polynomial is irreducible quadratic. The run checks the square test by both the finite-field Euler exponent and direct factorization of `T²−u` at every place. Full ideal generators, normalized residues, square classes and factor degrees are in [`result.json`](result.json).

[`protocol.json`](protocol.json) binds the factor certificates and local valuation result, with a 300-second cap. The completed checked-Sage replay took about 77 seconds; its selected build and command receipt are in [`sage-runtime-info.txt`](sage-runtime-info.txt) and [`attempt.json`](attempt.json). [`audit.py`](audit.py) independently reconciles every saved classification with the previous valuation table and computes the degree-72 splitting multisets; its output is [`audit.json`](audit.json). This audit checks the saved classifications, while the two finite-field algorithms in the checked-Sage run establish their square classes.

## Proof map

[`formal/QuadraticResidueTables.lean`](formal/QuadraticResidueTables.lean) proves the universal factorization identity when a unit is square, and kernel-checks all four exact splitting tables and residue-degree sums. [`formal/lean-check.txt`](formal/lean-check.txt) records the builds and `#print axioms`; only standard Lean foundations occur. The formalization of the concrete residue fields and reduction maps remains **partial**. Its open bridge is to define these source-field prime ideals and normalized units in Lean and prove their residue square classes, then connect those to the table rows. The next experiment should apply a local maximal-order test to the degree-four relative factors of the octic, where discriminant parity alone does not classify ramification.
