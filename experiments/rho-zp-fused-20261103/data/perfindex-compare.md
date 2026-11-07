# perfbench wall-time comparison

**Performance index PI = 1.015x** (95% CI 1.008–1.029, 7 paired rounds)

| area | weight | kernels | area index |
|:--|--:|--:|--:|
| dlp | 0.333 | 14 | 1.019x |
| field_ec | 0.333 | 12 | 1.011x |
| relation | 0.333 | 5 | 1.016x |

| kernel | base ms | cand ms | speedup | 95% CI | A/A noise | verdict |
|:--|--:|--:|--:|:--|--:|:--|
| `dlp/c_bsgs_ec32` | 3.436 | 3.435 | 1.005x | 0.999–1.026 | ±2.1% | neutral |
| `dlp/c_bsgs_zp36` | 7.143 | 7.188 | 0.992x | 0.973–1.014 | ±3.0% | neutral |
| `dlp/c_cheon56` | 13.054 | 13.000 | 1.020x | 0.961–1.052 | ±6.1% | neutral |
| `dlp/c_glv_rho_j0_32` | 16.755 | 16.489 | 0.993x | 0.963–1.116 | ±5.2% | neutral |
| `dlp/c_gpu_rho_emulate_ec32` | 9.239 | 9.033 | 1.020x | 1.001–1.050 | ±6.7% | neutral |
| `dlp/c_grumpy_ec32` | 6.359 | 6.639 | 0.996x | 0.977–1.011 | ±5.1% | neutral |
| `dlp/c_kangaroo_ec56_w34` | 13.076 | 12.882 | 1.008x | 0.995–1.200 | ±3.3% | neutral |
| `dlp/c_kangaroo_zp61_w36` | 8.209 | 8.304 | 1.009x | 0.957–1.034 | ±0.6% | neutral |
| `dlp/c_pohlig_ec48s` | 2.745 | 2.721 | 1.010x | 1.004–1.050 | ±1.3% | neutral |
| `dlp/c_pohlig_zp61s` | 7.007 | 7.011 | 1.001x | 0.998–1.013 | ±1.5% | neutral |
| `dlp/c_precomp_build_ec32` | 53.849 | 53.721 | 0.996x | 0.976–1.007 | ±2.2% | neutral |
| `dlp/c_precomp_online_ec32` | 18.696 | 18.741 | 1.000x | 0.994–1.013 | ±1.1% | neutral |
| `dlp/c_rho_ec36` | 19.915 | 19.811 | 1.000x | 0.958–1.029 | ±3.4% | neutral |
| `dlp/c_rho_zp40` | 29.223 | 23.919 | 1.240x | 1.204–1.269 | ±0.6% | faster |
| `field_ec/c_ec_add_chain` | 17.694 | 17.708 | 1.002x | 0.996–1.011 | ±1.0% | neutral |
| `field_ec/c_ec_batch_add` | 19.428 | 19.463 | 1.003x | 0.997–1.005 | ±0.7% | neutral |
| `field_ec/c_ec_count_points` | 7.332 | 6.413 | 1.141x | 1.000–1.352 | ±22.9% | neutral |
| `field_ec/c_ec_scalar_mul` | 3.696 | 3.697 | 1.000x | 0.979–1.016 | ±0.8% | neutral |
| `field_ec/c_factorize` | 7.949 | 7.925 | 0.999x | 0.975–1.004 | ±1.5% | neutral |
| `field_ec/c_invmod` | 28.473 | 28.496 | 0.992x | 0.986–1.003 | ±1.2% | neutral |
| `field_ec/c_is_prime` | 6.608 | 6.692 | 0.988x | 0.968–1.014 | ±2.9% | neutral |
| `field_ec/c_mont_mul_x8` | 13.171 | 13.178 | 0.996x | 0.986–1.002 | ±0.5% | neutral |
| `field_ec/c_mont_pow` | 8.436 | 8.440 | 1.014x | 0.995–1.052 | ±3.2% | neutral |
| `field_ec/c_powmod` | 8.776 | 8.761 | 1.003x | 0.951–1.003 | ±1.0% | neutral |
| `field_ec/c_sqrtmod` | 8.376 | 8.351 | 1.010x | 0.998–1.025 | ±0.2% | neutral |
| `field_ec/c_zp_op_chain` | 25.151 | 25.145 | 0.998x | 0.993–1.048 | ±1.6% | neutral |
| `relation/c_dense_solve` | 10.934 | 10.001 | 1.056x | 1.049–1.108 | ±2.1% | faster |
| `relation/c_ic_log_zp44` | 2.708 | 2.727 | 1.006x | 0.998–1.016 | ±1.0% | neutral |
| `relation/c_ic_precompute_zp44` | 31.989 | 31.943 | 1.014x | 0.992–1.028 | ±3.2% | neutral |
| `relation/c_ic_randexp_zp36` | 3.367 | 3.377 | 1.000x | 0.991–1.014 | ±2.4% | neutral |
| `relation/c_linsolve_sparse` | 16.918 | 16.803 | 1.006x | 0.998–1.010 | ±0.7% | neutral |
