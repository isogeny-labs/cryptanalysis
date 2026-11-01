# Section 5a band

Points: 2 (s000, s001). Reference: rT. Weights (GAE per unpriced native operation): 0, 0.1, 1.
Rho scalar multiplications not decomposed by the rho: priced at 0 and 104 GAE each (both ends).

| arm | mean group ops | mean unpriced native ops | cost w=0 | cost w=0.1 | cost w=1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| S | 1.011e+05 | 3.093e+09 | 1.011e+05 | 3.094e+08 | 3.093e+09 |
| rT | 9.28e+06 | 1.87e+07 | 9.28e+06-9.283e+06 | 1.115e+07-1.115e+07 | 2.798e+07-2.799e+07 |

| gap to rT | w=0 | w=0.1 | w=1 |
| --- | ---: | ---: | ---: |
| S | 0.01089 [0.007123, 0.02314] / 0.01089 [0.007121, 0.02312] | 27.75 [18.14, 58.97] / 27.74 [18.13, 58.93] | 110.5 [72.24, 234.9] / 110.5 [72.24, 234.8] |

Pairs (ranked only where the order holds across the band):

- S vs rT: unresolved: the order of S and rT is not the same at every weight (it changes by w = 0.1, 1)

## Sensitivity: Frobenius at 1 GAE

# Section 5a band

Points: 2 (s000, s001). Reference: rT. Weights (GAE per unpriced native operation): 0, 0.1, 1.
Rho scalar multiplications not decomposed by the rho: priced at 0 and 104 GAE each (both ends).

| arm | mean group ops | mean unpriced native ops | cost w=0 | cost w=0.1 | cost w=1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| S | 4.98e+08 | 2.595e+09 | 4.98e+08 | 7.575e+08 | 3.093e+09 |
| rT | 9.28e+06 | 1.87e+07 | 9.28e+06-9.283e+06 | 1.115e+07-1.115e+07 | 2.798e+07-2.799e+07 |

| gap to rT | w=0 | w=0.1 | w=1 |
| --- | ---: | ---: | ---: |
| S | 53.66 [35.08, 114.1] / 53.64 [35.07, 114] | 67.93 [44.4, 144.4] / 67.91 [44.39, 144.3] | 110.5 [72.24, 234.9] / 110.5 [72.24, 234.8] |

Pairs (ranked only where the order holds across the band):

- S vs rT: rT is cheaper than S at every weight of the band
