Ratios of curve_solve group operations to main on the same targets.

| family | bits | curves | main S | rho S | main/rho | r64/main | r128/main |
|---|---|---|---|---|---|---|---|
| j1728 | 42 | 1600 | 1.464 | 0.970 | 0.740 | 0.971 [0.940, 1.003] | 0.990 [0.959, 1.023] |
| j1728 | 44 | 1130 | 1.451 | 0.981 | 0.729 | 0.994 [0.956, 1.033] | 0.977 [0.940, 1.015] |
| j1728 | 46 | 800 | 1.440 | 0.942 | 0.734 | 1.029 [0.983, 1.076] | 0.972 [0.930, 1.015] |
| j0 | 42 | 1600 | 1.468 | 0.978 | 0.607 | 0.980 [0.949, 1.011] | 0.987 [0.956, 1.018] |
| j0 | 44 | 1130 | 1.441 | 0.989 | 0.538 | 1.006 [0.967, 1.046] | 0.992 [0.954, 1.032] |
| j0 | 46 | 800 | 1.486 | 0.924 | 0.729 | 0.965 [0.921, 1.012] | 0.964 [0.921, 1.010] |

Cell intervals are 95% bootstrap intervals, descriptive. S and main/rho use curves 0..149 of each cell for rho.

Primary (both families, geometric mean of the six cell ratios, 97.5% interval, K = 2):

- r64: 0.9905 [0.9723, 1.0090], half-width 1.85%, not confirmed
- r128: 0.9802 [0.9627, 0.9978], half-width 1.79%, CONFIRMED (upper bound below 1)

Secondary (one family alone, 99.167% interval, K = 6):

- r64:j1728: 0.9977 [0.9670, 1.0296], half-width 3.13%, not confirmed
- r64:j0: 0.9833 [0.9528, 1.0138], half-width 3.10%, not confirmed
- r128:j1728: 0.9796 [0.9509, 1.0100], half-width 3.02%, not confirmed
- r128:j0: 0.9807 [0.9516, 1.0099], half-width 2.97%, not confirmed

Descriptive per size (both families, 95%):

- r64:42: 0.9753 [0.9534, 0.9980]
- r64:44: 0.9998 [0.9727, 1.0277]
- r64:46: 0.9965 [0.9640, 1.0293]
- r128:42: 0.9886 [0.9666, 1.0107]
- r128:44: 0.9840 [0.9565, 1.0115]
- r128:46: 0.9680 [0.9374, 0.9992]

Positive control (table 8 vs main, 42 bits, both families, 95%): 1.221 [1.145, 1.305] pass=True
