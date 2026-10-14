# Wide-partition walk-quality receipt

Single-walk work-to-first-orbit-repeat on the GF(2^23) test curve,
built from generated/eccF23.h (permuted type-II ONB, x^23 + x^5 + 1),
cross-checked bit-for-bit against codegen/field.py and codegen/curves.py
(multiplication, inversion, sigma^j, point addition, a 200-step walk).

ell = 2095853, x-orbits M = ell/46 = 45562, ideal mean sqrt(pi*M/2) = 267.5 steps,
2000 trials per configuration, max steps 6000.

| config | mean | median | IQR | censored | ratio vs r8-shift | 95% CI |
| --- | --- | --- | --- | --- | --- | --- |
| r8-shift | 327.8 | 314.0 | 203.0-435.0 | 0 | 1.0000 | - |
| r16-shift | 338.1 | 315.0 | 203.0-449.0 | 0 | 1.0317 | 0.9994-1.0654 |
| r16-plain | 354.3 | 326.0 | 212.0-478.0 | 13 | 1.0811 | 1.0477-1.1159 |
| r8-ideal | 327.2 | 313.0 | 192.0-442.0 | 0 | 0.9984 | 0.9677-1.0303 |
| r16-ideal | 322.3 | 303.0 | 193.0-429.0 | 0 | 0.9833 | 0.9531-1.0148 |

Lag-1 branch autocorrelation over a 4096-step run:

- r8-shift: -0.0152
- r16-shift: -0.0193
- r16-plain: -0.0608
- r8-ideal: -0.0074
- r16-ideal: 0.0072

Partition balance (exact Binomial(23,1/2) cell probabilities):

| config | min cell | max cell | uniform |
| --- | --- | --- | --- |
| r8-shift | 0.00531 | 0.29756 | 0.12500 |
| r16-shift | 0.00000 | 0.29756 | 0.06250 |
| r16-plain | 0.00127 | 0.16118 | 0.06250 |
| r8-ideal | 0.08768 | 0.16245 | 0.12500 |
| r16-ideal | 0.00127 | 0.16118 | 0.06250 |

Short-cycle recheck (codegen/cycles.py method, widened exponent sets):

| set | curve | multisets tried | hits | expected by chance | degenerate |
| --- | --- | --- | --- | --- | --- |
| m23-ship | 2095853 | 3002 | 0 | 0.066 | 0 |
| m23-r16 | 2095853 | 74612 | 13 | 1.638 | 0 |
| m23-r32 | 2095853 | 2760680 | 243 | 60.592 | 0 |
| m131-ship | 680564733841876926932320129493409985129 | 1286 | 0 | 0.000 | 0 |
| m131-r16 | 680564733841876926932320129493409985129 | 20348 | 0 | 0.000 | 0 |
| m131-r32 | 680564733841876926932320129493409985129 | 435896 | 0 | 0.000 | 0 |

Multiplier orders ord_ell(1 + lambda^j), m=23 (ell = 2095853):

j: 3:1047926 4:1047926 5:2095852 6:523963 7:1047926 8:2095852 9:91124 10:2095852 11:523963 12:523963 13:2095852 14:2095852 15:2095852 16:1047926 17:523963 18:2095852 19:1047926 20:1047926 21:2095852 22:2095852 23:2095852 24:2095852 25:2095852 26:1047926 27:1047926 28:2095852 29:523963 30:1047926 31:2095852 32:91124 33:2095852 34:523963

Multiplier orders ord_ell(1 + lambda^j), m=131 (ell = 680564733841876926932320129493409985129):

j: 

