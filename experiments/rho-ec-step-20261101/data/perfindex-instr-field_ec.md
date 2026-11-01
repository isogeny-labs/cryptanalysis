# perfbench instruction-count comparison (callgrind Ir, 1 thread)

**Performance index PI = 1.000x** (95% CI 1.000–1.000, 1 paired rounds)

| area | weight | kernels | area index |
|:--|--:|--:|--:|
| field_ec | 1.000 | 12 | 1.000x |

| kernel | base Ir | cand Ir | speedup | 95% CI | A/A noise | verdict |
|:--|--:|--:|--:|:--|--:|:--|
| `field_ec/c_ec_add_chain` | 74948797.000 | 74948797.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `field_ec/c_ec_batch_add` | 233479793.000 | 233479793.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `field_ec/c_ec_count_points` | 57787732.000 | 57999568.000 | 0.996x | 0.996–0.996 | n/a | neutral |
| `field_ec/c_ec_scalar_mul` | 21975143.000 | 21975143.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `field_ec/c_factorize` | 35554129.000 | 35554129.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `field_ec/c_invmod` | 110946230.000 | 110946230.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `field_ec/c_is_prime` | 32920849.000 | 32920849.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `field_ec/c_mont_mul_x8` | 174064098.000 | 174064098.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `field_ec/c_mont_pow` | 43952298.000 | 43952298.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `field_ec/c_powmod` | 50014372.000 | 50014372.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `field_ec/c_sqrtmod` | 44556823.000 | 44556823.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `field_ec/c_zp_op_chain` | 136315228.000 | 136315228.000 | 1.000x | 1.000–1.000 | n/a | neutral |
