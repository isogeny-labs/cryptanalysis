# perfbench wall-time comparison

**Performance index PI = 0.999x** (95% CI 0.945–1.025, 5 paired rounds)

| area | weight | kernels | area index |
|:--|--:|--:|--:|
| dlp | 0.333 | 14 | 1.018x |
| field_ec | 0.333 | 12 | 1.000x |
| relation | 0.333 | 5 | 0.979x |

| kernel | base ms | cand ms | speedup | 95% CI | A/A noise | verdict |
|:--|--:|--:|--:|:--|--:|:--|
| `dlp/c_bsgs_ec32` | 4.305 | 4.433 | 0.984x | 0.871–1.256 | ±10.9% | neutral |
| `dlp/c_bsgs_zp36` | 7.740 | 7.968 | 0.973x | 0.919–1.021 | ±7.5% | neutral |
| `dlp/c_cheon56` | 16.779 | 17.047 | 1.000x | 0.878–1.080 | ±5.1% | neutral |
| `dlp/c_glv_rho_j0_32` | 21.151 | 21.722 | 0.976x | 0.823–1.176 | ±7.8% | neutral |
| `dlp/c_gpu_rho_emulate_ec32` | 12.211 | 12.068 | 1.012x | 0.950–1.082 | ±6.0% | neutral |
| `dlp/c_grumpy_ec32` | 8.373 | 7.537 | 1.088x | 0.878–1.292 | ±26.0% | neutral |
| `dlp/c_kangaroo_ec56_w34` | 16.815 | 15.896 | 1.014x | 0.698–1.126 | ±8.4% | neutral |
| `dlp/c_kangaroo_zp61_w36` | 11.279 | 11.066 | 0.999x | 0.667–1.078 | ±3.9% | neutral |
| `dlp/c_pohlig_ec48s` | 3.484 | 3.508 | 1.006x | 0.862–1.052 | ±8.6% | neutral |
| `dlp/c_pohlig_zp61s` | 9.036 | 9.077 | 1.017x | 0.898–1.353 | ±2.8% | neutral |
| `dlp/c_precomp_build_ec32` | 67.913 | 69.908 | 0.953x | 0.903–1.068 | ±9.2% | neutral |
| `dlp/c_precomp_online_ec32` | 24.420 | 24.287 | 1.039x | 0.967–1.073 | ±4.0% | neutral |
| `dlp/c_rho_ec36` | 31.034 | 27.015 | 1.180x | 1.052–1.282 | ±7.5% | faster |
| `dlp/c_rho_zp40` | 46.030 | 44.975 | 1.031x | 0.899–1.080 | ±4.5% | neutral |
| `field_ec/c_ec_add_chain` | 23.025 | 22.602 | 1.025x | 0.948–1.059 | ±7.1% | neutral |
| `field_ec/c_ec_batch_add` | 25.100 | 25.299 | 0.997x | 0.944–1.034 | ±1.1% | neutral |
| `field_ec/c_ec_count_points` | 8.199 | 8.260 | 1.002x | 0.882–1.047 | ±8.0% | neutral |
| `field_ec/c_ec_scalar_mul` | 4.955 | 4.974 | 1.003x | 0.984–1.021 | ±5.1% | neutral |
| `field_ec/c_factorize` | 10.397 | 10.113 | 1.010x | 0.966–1.055 | ±8.1% | neutral |
| `field_ec/c_invmod` | 35.721 | 36.381 | 0.973x | 0.941–1.053 | ±6.5% | neutral |
| `field_ec/c_is_prime` | 8.594 | 8.531 | 1.007x | 0.944–1.089 | ±11.5% | neutral |
| `field_ec/c_mont_mul_x8` | 17.169 | 16.814 | 1.017x | 0.955–1.357 | ±3.9% | neutral |
| `field_ec/c_mont_pow` | 10.909 | 10.808 | 1.010x | 0.968–1.020 | ±4.7% | neutral |
| `field_ec/c_powmod` | 11.362 | 11.224 | 1.000x | 0.963–1.403 | ±3.7% | neutral |
| `field_ec/c_sqrtmod` | 10.127 | 10.354 | 0.990x | 0.963–1.056 | ±5.0% | neutral |
| `field_ec/c_zp_op_chain` | 30.966 | 31.585 | 0.970x | 0.938–1.031 | ±7.9% | neutral |
| `relation/c_dense_solve` | 13.428 | 13.518 | 0.993x | 0.844–1.160 | ±3.0% | neutral |
| `relation/c_ic_log_zp44` | 3.852 | 4.078 | 0.945x | 0.718–1.029 | ±3.4% | neutral |
| `relation/c_ic_precompute_zp44` | 42.845 | 41.183 | 1.040x | 0.966–1.157 | ±9.4% | neutral |
| `relation/c_ic_randexp_zp36` | 4.482 | 4.723 | 0.946x | 0.903–1.217 | ±2.3% | neutral |
| `relation/c_linsolve_sparse` | 22.311 | 23.463 | 0.975x | 0.679–1.004 | ±4.1% | neutral |
