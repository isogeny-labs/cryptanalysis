Ratios of curve_solve group operations, candidate over main, on the same targets.

| family | bits | curves | main S | cand S | rho S | cand/main | main/rho | cand/rho |
|---|---|---|---|---|---|---|---|---|
| j1728 | 40 | 1600 | 1.483 | 1.432 | 1.093 | 0.967 [0.936, 0.999] | 0.651 | 0.645 |
| j1728 | 41 | 1600 | 1.454 | 1.439 | 0.957 | 0.988 [0.957, 1.020] | 0.802 | 0.697 |
| j1728 | 42 | 1600 | 1.471 | 1.426 | 1.017 | 0.970 [0.941, 1.000] | 0.676 | 0.660 |
| j1728 | 43 | 1600 | 1.474 | 1.397 | 0.974 | 0.948 [0.918, 0.979] | 0.767 | 0.671 |
| j0 | 40 | 1600 | 1.463 | 1.488 | 0.932 | 1.016 [0.985, 1.049] | 0.642 | 0.616 |
| j0 | 41 | 1600 | 1.442 | 1.430 | 1.004 | 0.990 [0.959, 1.024] | 0.561 | 0.545 |
| j0 | 42 | 1600 | 1.442 | 1.439 | 0.977 | 0.995 [0.962, 1.029] | 0.601 | 0.608 |
| j0 | 43 | 1600 | 1.440 | 1.450 | 0.956 | 1.007 [0.975, 1.040] | 0.598 | 0.588 |

Cell intervals are 95% bootstrap intervals (descriptive). S = group_ops / sqrt(n / m) for GLV, group_ops / sqrt(n) for rho; rho on curves 0..59 of each cell (cand/rho and main/rho use the same curves).

Primary (8 cells, geometric mean of cell ratios, 97.5% interval): 0.9849 [0.9725, 0.9978], half-width 1.28%, 95% interval [0.9738, 0.9963], CONFIRMED (upper bound below 1)

No-worse check per size (both families, 98.75% intervals; fails if a lower bound is above 1): pass=True

- 40 bits: 0.9914 [0.9633, 1.0206] (95%: [0.9689, 1.0143])
- 41 bits: 0.9890 [0.9608, 1.0186] (95%: [0.9670, 1.0118])
- 42 bits: 0.9821 [0.9539, 1.0106] (95%: [0.9602, 1.0046])
- 43 bits: 0.9773 [0.9496, 1.0071] (95%: [0.9553, 1.0002])

Per family (sizes 40-43 pooled, 95%, descriptive):

- j1728: 0.9682 [0.9530, 0.9836]
- j0: 1.0020 [0.9860, 1.0187]

Identity cells (38 and 39 bits, 320 rows): candidate group_ops equal main's on every row.

**Verdict: CONFIRMED**
