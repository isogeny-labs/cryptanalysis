**MODEL band: rho counted in this run; IC units modelled from the archived counted run 39882571652 (see band_model.py); not a counted run of the field-ops producer**

# Section 5a band

Points: 20 (s000, s001, s002, s003, s004, s005 ...). Reference: rT. Weights (GAE per unpriced native operation): 0, 0.1, 1.
Rho scalar multiplications not decomposed by the rho: priced at 0 and 104 GAE each (both ends).

| arm | mean group ops | mean unpriced native ops | cost w=0 | cost w=0.1 | cost w=1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| A | 2859 | 1.175e+08 | 2859 | 1.175e+07 | 1.175e+08 |
| B | 841 | 7.52e+07 | 841 | 7.521e+06 | 7.52e+07 |
| rT | 8.607e+06 | 1.735e+07 | 8.607e+06-8.611e+06 | 1.034e+07-1.035e+07 | 2.595e+07-2.596e+07 |

| gap to rT | w=0 | w=0.1 | w=1 |
| --- | ---: | ---: | ---: |
| A | 0.0003322 [0.0002612, 0.0004442] / 0.0003321 [0.0002611, 0.000444] | 1.136 [0.8876, 1.518] / 1.136 [0.8874, 1.517] | 4.527 [3.536, 6.046] / 4.526 [3.536, 6.045] |
| B | 9.771e-05 [7.681e-05, 0.0001307] / 9.767e-05 [7.679e-05, 0.0001306] | 0.7272 [0.5657, 0.9728] / 0.727 [0.5655, 0.9724] | 2.897 [2.254, 3.876] / 2.897 [2.254, 3.875] |

Pairs (ranked only where the order holds across the band):

- A vs B: B is cheaper than A at every weight of the band
- A vs rT: unresolved: the order of A and rT is not the same at every weight (it changes by w = 0.1, 1)
- B vs rT: unresolved: the order of B and rT is not the same at every weight (it changes by w = 1)
