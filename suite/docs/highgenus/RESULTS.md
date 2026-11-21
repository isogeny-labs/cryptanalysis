# Higher-genus panel results (2026-11-21)

Functional verification of `suite/src/highgenus/` on one 4-core cloud host,
produced by `suite/examples/highgenus_panel.rs`; raw rows (JSON lines,
`highgenus.panel/v1`) are in [`panel/`](panel/). Every "verified" means the
solver's logarithm equals the planted one (or, in order mode, that the
recovered logarithm reproduces the target by a scalar multiplication). Costs
are group operations from the engines' own counters and wall seconds for
orientation. **No speed claim; `[pcc:unverified]` throughout.** Random curves
are seeded (`--seed 1`) and printed in the JSON rows.

Engines: `cantor` = hyperelliptic Mumford/Cantor; `kummer` = one-point
superelliptic ideal arithmetic (non-hyperelliptic for `m ≥ 3`, `g ≥ 5`).

## Pollard rho on planted instances (known prime subgroup order)

| engine | g | curve | #Jac bits | N bits | walk ops | setup ops | S_walk = walk ops / sqrt N | wall s | result |
|---|---|---|---|---|---|---|---|---|---|
| cantor | 5 | y^2 = x^11 + 92 over F_353 | 43 | 24 | 5724 | 2084 | 1.55 | 0.0 | verified |
| cantor | 7 | y^2 = x^15 + 57 over F_151 | 52 | 23 | 3621 | 2028 | 1.28 | 0.0 | verified |
| cantor | 11 | y^2 = x^23 + 267 over F_277 | 90 | 24 | 2461 | 2089 | 0.66 | 0.1 | verified |
| cantor | 23 | y^2 = x^47 + 1811 over F_2539 | 261 | 22 | 3751 | 1918 | 1.85 | 0.4 | verified |
| cantor | 47 | y^2 = x^95 + 190 over F_191 | 356 | 28 | 28548 | 2500 | 1.76 | 1.5 | verified |
| cantor | 97 | y^2 = x^195 + 560 over F_1171 | 990 | 22 | 673 | 1863 | 0.39 | 0.7 | verified |
| cantor | 131 | y^2 = x^263 + 1442 over F_1579 | 1393 | 22 | 5083 | 1810 | 3.40 | 40.3 | verified |
| kummer | 5 | y^11 = x (1-x)^2 over F_23 | 24 | 14 | 288 | 266 | 3.13 | 4.7 | verified |
| kummer | 7 | y^3 = x^8 + 27 over F_193 | 53 | 13 | 70 | 270 | 0.93 | 0.1 | verified |
| kummer | 11 | y^23 = x (1-x)^2 over F_461 | 98 | 15 | 335 | 323 | 1.94 | 179.0 | verified |
| kummer | 23 | y^47 = x (1-x)^2 over F_941 | 227 | 10 | 109 | 188 | 4.36 | 2663.8 | verified |
| kummer | 97 | y^3 = x^98 + 643 over F_1471 | 1020 | 18 | 585 | 347 | 1.55 | 20.8 | verified |

## Index calculus, known prime subgroup order (Jacobi-sum curves)

| engine | g | curve | N bits | B | FB | trials | smooth rate | walk ops | LA dim | LA ms | wall s | result |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cantor | 5 | y^2 = x^11 + 16 over F_23 | 18 | 2 | 200 | 8334 | 2.59e-02 | 9827 | 190 | 6 | 0.1 | verified |
| cantor | 11 | - | - | 2 | 8832 | - | - | - | - | - | 1281.3 | error: budget exhausted: relation search trials |
| cantor | 11 | - | - | 2 | 8832 | - | - | - | - | - | 1224.4 | error: budget exhausted: relation search trials (dlp mode) |
| kummer | 7 | y^3 = x^8 + 2 over F_73 | 21 | 2 | 2836 | 55418 | 5.15e-02 | 77863 | 2741 | 3567 | 41.4 | verified |

## Index calculus, order from the relation lattice, then a verified logarithm (random curves over small fields)

| engine | g | p | curve | B | FB | trials | smooth rate | walk ops | order bits | Hasse–Weil | h·R = 0 | det ms | wall s | DLP |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cantor | 23 | 3 | y² = x^47 + x^46 + 2*x^45 + x^44 + x^40 + x^3… | 5 | 86 | 23518 | 4.34e-03 | 23610 | 38 | True | True | 507 | 1.3 | N 15 bits: verified (23892 trials, 1 ms LA) |
| cantor | 31 | 3 | y² = x^63 + x^62 + 2*x^61 + x^60 + x^59 + x^5… | 6 | 210 | 1515127 | 1.49e-04 | 1515331 | 49 | True | True | 3440 | 98.7 | N 24 bits: verified (1481936 trials, 8 ms LA) |
| kummer | 5 | 7 | y³ = x^5 + 5*x^4 + 6*x^2 + 3*x + 4 · (x + 4)² | 2 | 41 | 88 | 6.48e-01 | 121 | 17 | True | True | 7 | 0.1 | N 10 bits: verified (98 trials, 1 ms LA) |
| kummer | 11 | 7 | - | 3 | 146 | - | - | - | - | - | - | - | - | error: budget exhausted: every sampled minor was singular (relations do not span) |
| kummer | 11 | 7 | y³ = x^11 + x^10 + 2*x^9 + 2*x^8 + 4*x^7 + x^… | 3 | 146 | 1833 | 9.93e-02 | 1995 | 35 | True | True | 1261 | 2.8 | N 15 bits: verified (1962 trials, 3 ms LA) |
| kummer | 23 | 2 | y³ = x^23 + x^20 + x^19 + x^17 + x^16 + x^14 … | 6 | 22 | 1115 | 3.77e-02 | 1158 | 24 | True | True | 1 | 1.4 | N 10 bits: verified (1585 trials, 0 ms LA) |
| kummer | 47 | 2 | y³ = x^47 + x^44 + x^41 + x^40 + x^36 + x^34 … | 10 | 231 | 144371 | 1.99e-03 | 144631 | 51 | True | True | 4577 | 609.8 | N 37 bits: verified (141888 trials, 8 ms LA) |
| kummer | 47 | 2 | - | 10 | 231 | - | - | - | - | - | - | - | - | error: budget exhausted: every sampled minor was singular (relations do not span) |

## Relation-rate probes at a trial cap (no solve)

| engine | g | p | B | FB | trials | smooth | relations | needed | smooth rate | ms / trial | wall s |
|---|---|---|---|---|---|---|---|---|---|---|---|
| cantor | 47 | 3 | 7 | 492 | 100000 | 1 | 0 | 508 | 1.00e-05 | 0.123 | 12.3 |
| cantor | 131 | 3 | 12 | 69923 | 20000 | 2 | 0 | 69939 | 1.00e-04 | 1.210 | 24.2 |
| kummer | 97 | 2 | 12 | 711 | 20000 | 1 | 0 | 727 | 5.00e-05 | 14.443 | 288.9 |
| kummer | 131 | 2 | 12 | 738 | 20000 | 2 | 0 | 754 | 1.00e-04 | 25.922 | 518.4 |

## Reading the tables

- **Rho, hyperelliptic**: planted `y² = x^{2g+1} + a` with the exact order from Jacobi sums; verified at every sampled genus 5, 7, 11, 23, 47, 97, 131. Genus 131 (1393-bit Jacobian, 22-bit subgroup) took 40 s.
- **Rho, non-hyperelliptic**: `y³ = x⁸ + a` (g = 7) and `y³ = x⁹⁸ + a` (g = 97, 1020-bit Jacobian) through the rank-3 ideal engine; `y^{2g+1} = x(1−x)²` at g = 5, 11, 23 through the rank-`2g+1` engine (rank 47 ≈ 7 s per group operation, 44 min for the genus-23 solve). No known-order non-hyperelliptic curve of genus 131 with usable arithmetic in this version.
- **IC, known order**: works where places of degree ≤ 2 make degree-`g` norms smooth often enough: g = 5 (hyperelliptic, F₂₃) and g = 7 (`y³ = x⁸ + a` over F₇₃, 2836 places, dense solve of dimension 2741 in 3.6 s). The g = 11 hyperelliptic cell on F₁₃₉ exhausted 5·10⁷ trials with 8832 places: that regime needs `B = 3` and sparse linear algebra, which this version does not have.
- **IC, order from the relation lattice** (the `g ≫ log q` regime): hyperelliptic g = 23, 31 over F₃ and trigonal g = 5, 11 (F₇), 23, 47 (F₂), each followed by a verified logarithm in the largest prime subgroup. The genus-47 trigonal row (231 places, 1.4·10⁵ trials, 51-bit order, 37-bit prime subgroup) is the largest complete non-hyperelliptic solve here. The first g = 11 and g = 47 trigonal attempts failed because unused factor-base columns made every minor singular; the fix (index over the occurring places) is in the same PR and the reruns are the rows shown.
- **Probes**: at g = 47 over F₃ (`B = 7`, 492 places) the measured rate 10⁻⁵ per trial at 0.12 ms per trial puts a full run at ~1.5 h; at g = 97 and 131 the measured rates with `B = 12` (and a 69923-place base at g = 131 over F₃) confirm the Enge–Gaudry regime is out of reach on one host, as the `L(1/2)` estimate says.
