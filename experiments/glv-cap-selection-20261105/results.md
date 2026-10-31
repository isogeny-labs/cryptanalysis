Ratios of curve_solve group operations to main (r = 32) on the same targets.

| size | both families r64/main | both families r128/main |
|---|---|---|
| 38 | 0.994 [0.959, 1.028] | 1.008 [0.976, 1.042] |
| 39 | 1.016 [0.981, 1.053] | 0.999 [0.965, 1.032] |
| 40 | 0.974 [0.941, 1.008] | 0.982 [0.948, 1.017] |
| 41 | 0.972 [0.938, 1.007] | 0.970 [0.936, 1.005] |
| 42 | 0.954 [0.922, 0.988] | 0.969 [0.938, 1.003] |

| family | bits | curves | main S | r64/main | r128/main |
|---|---|---|---|---|---|
| j1728 | 38 | 700 | 1.494 | 0.989 [0.942, 1.039] | 1.009 [0.962, 1.058] |
| j1728 | 39 | 700 | 1.456 | 1.023 [0.974, 1.075] | 1.022 [0.973, 1.076] |
| j1728 | 40 | 700 | 1.516 | 0.931 [0.887, 0.976] | 0.964 [0.916, 1.013] |
| j1728 | 41 | 700 | 1.480 | 0.983 [0.935, 1.033] | 0.987 [0.939, 1.038] |
| j1728 | 42 | 700 | 1.511 | 0.964 [0.920, 1.011] | 0.967 [0.922, 1.016] |
| j0 | 38 | 700 | 1.485 | 0.998 [0.949, 1.048] | 1.008 [0.963, 1.056] |
| j0 | 39 | 700 | 1.483 | 1.009 [0.959, 1.060] | 0.975 [0.932, 1.020] |
| j0 | 40 | 700 | 1.446 | 1.020 [0.971, 1.071] | 1.000 [0.953, 1.050] |
| j0 | 41 | 700 | 1.493 | 0.961 [0.913, 1.010] | 0.953 [0.905, 1.003] |
| j0 | 42 | 700 | 1.500 | 0.944 [0.899, 0.990] | 0.971 [0.928, 1.017] |

Intervals are 95% bootstrap intervals over curves (descriptive); S = group_ops / sqrt(n / m).

- r64: fitted ratios by size 1.0066, 0.9941, 0.9818, 0.9695, 0.9575; slope -0.0125 per bit; T = 39; T over bootstrap draws {'38': 0.1984, '39': 0.3433, '40': 0.4145, '41': 0.0403, '42': 0.0014, 'none': 0.0021}
  - suffix [39, 40, 41, 42]: geomean 0.9788, one-sided 90% upper bound 0.9898, 95% interval [0.9621, 0.9959], sizes wholly worse [], robust True
- r128: fitted ratios by size 1.0072, 0.9963, 0.9855, 0.9748, 0.9643; slope -0.0109 per bit; T = 40; T over bootstrap draws {'38': 0.1782, '39': 0.264, '40': 0.4496, '41': 0.0909, '42': 0.0079, 'none': 0.0094}
  - suffix [40, 41, 42]: geomean 0.9737, one-sided 90% upper bound 0.9863, 95% interval [0.9542, 0.9932], sizes wholly worse [], robust True

**Verdict: GO: cap = 32 for lg < 40, cap = 128 for lg >= 40 (all larger sizes)**

Positive control (table 8 vs main, 42 bits, both families, 95%): 1.133 [1.018, 1.259] pass=True
Identity control (forced 32 vs main): 160 rows, all identical
