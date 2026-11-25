# perfbench instruction-count comparison (callgrind Ir, 1 thread)

**Performance index PI = 1.011x** (95% CI 1.011–1.011, 1 paired rounds)

| area | weight | kernels | area index |
|:--|--:|--:|--:|
| dlp | 0.333 | 14 | 1.034x |
| field_ec | 0.333 | 12 | 1.000x |
| relation | 0.333 | 5 | 1.000x |

| kernel | base Ir | cand Ir | speedup | 95% CI | A/A noise | verdict |
|:--|--:|--:|--:|:--|--:|:--|
| `dlp/c_bsgs_ec32` | 39956244.000 | 39956244.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `dlp/c_bsgs_zp36` | 85814768.000 | 85814768.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `dlp/c_cheon56` | 76953945.000 | 76953945.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `dlp/c_glv_rho_j0_32` | 115360112.000 | 115360112.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `dlp/c_gpu_rho_emulate_ec32` | 74211602.000 | 74211602.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `dlp/c_grumpy_ec32` | 50675874.000 | 50675874.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `dlp/c_kangaroo_ec56_w34` | 171410743.000 | 171410743.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `dlp/c_kangaroo_zp61_w36` | 186207666.000 | 186207666.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `dlp/c_pohlig_ec48s` | 30540401.000 | 30540401.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `dlp/c_pohlig_zp61s` | 118903535.000 | 118903535.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `dlp/c_precomp_build_ec32` | 586842473.000 | 586842473.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `dlp/c_precomp_online_ec32` | 82521617.000 | 82521617.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `dlp/c_rho_ec36` | 190785114.000 | 190186983.000 | 1.003x | 1.003–1.003 | n/a | neutral |
| `dlp/c_rho_zp40` | 233308726.000 | 146925023.000 | 1.588x | 1.588–1.588 | n/a | faster |
| `field_ec/c_ec_add_chain` | 74948797.000 | 74948797.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `field_ec/c_ec_batch_add` | 233479793.000 | 233479793.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `field_ec/c_ec_count_points` | 57999568.000 | 57999568.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `field_ec/c_ec_scalar_mul` | 21975143.000 | 21975143.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `field_ec/c_factorize` | 35554129.000 | 35554129.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `field_ec/c_invmod` | 110946230.000 | 110946230.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `field_ec/c_is_prime` | 32920849.000 | 32920849.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `field_ec/c_mont_mul_x8` | 174064098.000 | 174064098.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `field_ec/c_mont_pow` | 43952298.000 | 43952298.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `field_ec/c_powmod` | 50014372.000 | 50014372.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `field_ec/c_sqrtmod` | 44556823.000 | 44556823.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `field_ec/c_zp_op_chain` | 136315228.000 | 136315228.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `relation/c_dense_solve` | 40035301.000 | 40035301.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `relation/c_ic_log_zp44` | 52139182.000 | 52139182.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `relation/c_ic_precompute_zp44` | 428257845.000 | 428257845.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `relation/c_ic_randexp_zp36` | 53065586.000 | 53065586.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `relation/c_linsolve_sparse` | 205043666.000 | 205043666.000 | 1.000x | 1.000–1.000 | n/a | neutral |
