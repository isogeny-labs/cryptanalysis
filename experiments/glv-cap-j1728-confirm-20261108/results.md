Primary and secondary S1: j = 1728, candidate over ref (1ee4f47, cap 32 everywhere), ratio of curve_solve group operations on the same targets.

| bits | curves | ref S | cand S | rho S | cand/ref (95%) | cand/ref (98.75%) | ref/rho | cand/rho |
|---|---|---|---|---|---|---|---|---|
| 40 | 3000 | 1.475 | 1.470 | 0.959 | 0.9977 [0.9740, 1.0216] | [0.9674, 1.0294] | 0.698 | 0.768 |
| 41 | 3000 | 1.446 | 1.436 | 0.885 | 0.9939 [0.9703, 1.0182] | [0.9643, 1.0253] | 0.890 | 0.761 |
| 42 | 3000 | 1.447 | 1.438 | 0.989 | 0.9945 [0.9711, 1.0187] | [0.9646, 1.0263] | 0.706 | 0.739 |
| 43 | 3000 | 1.452 | 1.422 | 0.934 | 0.9777 [0.9551, 1.0004] | [0.9483, 1.0075] | 0.722 | 0.781 |

S = group_ops / sqrt(n / m) for GLV, group_ops / sqrt(n) for rho (rho on curves 0..59 of each cell; the /rho columns use the same curves).

**Primary** (j = 1728, 40-43 bits, geometric mean of the 4 cell ratios, 97.5% interval): 0.9909 [0.9775, 1.0045], half-width 1.36%, 95% interval [0.9791, 1.0029], NOT confirmed

No-worse check (98.75% per-size intervals; fails if a lower bound is above 1): pass=True; sizes wholly better: []

Secondary S2: j = 0, candidate (cap 32) over current main (318b27bf, cap 128 from 40 bits), same targets.

| bits | curves | main S | cand S | rho S | cand/main (95%) | cand/main (98.75%) | main/rho | cand/rho |
|---|---|---|---|---|---|---|---|---|
| 40 | 800 | 1.455 | 1.510 | 1.019 | 1.0385 [0.9934, 1.0853] | [0.9816, 1.0986] | 0.551 | 0.561 |
| 41 | 800 | 1.454 | 1.461 | 0.954 | 1.0057 [0.9619, 1.0525] | [0.9497, 1.0660] | 0.652 | 0.562 |
| 42 | 800 | 1.434 | 1.455 | 0.938 | 1.0138 [0.9690, 1.0612] | [0.9569, 1.0746] | 0.680 | 0.649 |
| 43 | 800 | 1.440 | 1.437 | 0.903 | 0.9974 [0.9525, 1.0436] | [0.9409, 1.0571] | 0.622 | 0.704 |

S2 pooled (j = 0, 40-43 bits, 97.5%): 1.0138 [0.9878, 1.0402] (95%: [0.9910, 1.0369]); rho on curves 0..39.

Identity (exact): candidate equals ref on all 600 rows (j = 0 at 40-43, j = 1728 at 38-39); candidate equals current main on all 400 j = 1728 rows at 40-43 (first 100 curves per size).

Positive control (forced r = 8 over ref, j = 1728, 42 bits, 200 curves): 1.229 [1.113, 1.352], detector sees it

**Verdict: NOT_CONFIRMED**
