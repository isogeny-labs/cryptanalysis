Ratios of curve_solve group operations to main on the same targets.

| family | bits | curves | r (main -> cand) | main S | cand S | rho S | main/rho | cand/rho | cand/main (95%) |
|---|---|---|---|---|---|---|---|---|---|
| j1728 | 32 | 1000 | 32:1000 -> 32:179; 64:821 | 1.541 | 1.576 | 1.143 | 0.696 | 0.656 | 1.023 [0.987, 1.060] |
| j1728 | 34 | 4000 | 32:4000 -> 64:1537; 128:2463 | 1.515 | 1.607 | 1.099 | 0.669 | 0.713 | 1.062 [1.043, 1.082] |
| j1728 | 36 | 4000 | 32:4000 -> 128:4000 | 1.482 | 1.538 | 1.111 | 0.672 | 0.705 | 1.038 [1.018, 1.058] |
| j1728 | 38 | 4000 | 32:4000 -> 128:4000 | 1.473 | 1.474 | 1.024 | 0.705 | 0.707 | 1.001 [0.981, 1.021] |
| j1728 | 40 | 4000 | 32:4000 -> 128:4000 | 1.476 | 1.459 | 0.945 | 0.786 | 0.873 | 0.989 [0.969, 1.008] |
| j0 | 32 | 1000 | 32:1000 -> 32:816; 64:184 | 1.563 | 1.570 | 1.147 | 0.531 | 0.561 | 1.005 [0.986, 1.024] |
| j0 | 34 | 4000 | 32:4000 -> 64:3832; 128:168 | 1.509 | 1.566 | 1.166 | 0.519 | 0.532 | 1.038 [1.019, 1.058] |
| j0 | 36 | 4000 | 32:4000 -> 128:4000 | 1.499 | 1.572 | 1.038 | 0.570 | 0.604 | 1.050 [1.031, 1.070] |
| j0 | 38 | 4000 | 32:4000 -> 128:4000 | 1.482 | 1.489 | 0.981 | 0.596 | 0.614 | 1.005 [0.985, 1.026] |
| j0 | 40 | 4000 | 32:4000 -> 128:4000 | 1.462 | 1.456 | 0.998 | 0.575 | 0.586 | 0.995 [0.975, 1.015] |

Cell intervals are 95% bootstrap intervals, descriptive. S, main/rho and cand/rho use curves 0..149 of each cell for rho; the r column counts curves per table size under each rule.

Primary (both families, 8 cells at 34-40 bits, geometric mean of cell ratios, 95% interval, K = 1): 1.0220 [1.0149, 1.0291], half-width 0.69%, WORSE (lower bound above 1)

Secondary (98.75% interval, K = 4):

- family:j1728: 1.0220 [1.0098, 1.0346], half-width 1.22%, lower bound above 1
- family:j0: 1.0219 [1.0095, 1.0344], half-width 1.22%, lower bound above 1
- sizes:34-36: 1.0472 [1.0351, 1.0600], half-width 1.19%, lower bound above 1
- sizes:38-40: 0.9974 [0.9847, 1.0101], half-width 1.27%, interval contains 1

Descriptive: 34-36 over 38-40 1.0499 [1.0358, 1.0647] (95%)

Descriptive per size (both families, 95%):

- 34 bits: 1.0503 [1.0362, 1.0644]
- 36 bits: 1.0441 [1.0304, 1.0583]
- 38 bits: 1.0028 [0.9884, 1.0175]
- 40 bits: 0.9920 [0.9780, 1.0062]
- 32 bits: 1.0138 [0.9938, 1.0342]

Identity control (cand with cap 32 vs main): 1000 rows, 0 differing. Rows with equal r under both rules: 995, 0 differing.
Positive control r8_over_main_40: 1.250 [1.183, 1.321] pass=True
Positive control r8_over_main_34_descriptive: 1.138 [1.079, 1.199] pass=True
