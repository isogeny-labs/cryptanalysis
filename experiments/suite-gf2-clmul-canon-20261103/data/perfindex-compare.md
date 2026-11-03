# perfbench wall-time comparison

**Performance index PI = 1.033x** (95% CI 1.020–1.047, 7 paired rounds)

| area | weight | kernels | area index |
|:--|--:|--:|--:|
| dlp | 0.200 | 1 | 1.012x |
| field_ec | 0.200 | 3 | 1.028x |
| pdp | 0.200 | 1 | 1.088x |
| relation | 0.200 | 6 | 1.022x |
| sat | 0.200 | 3 | 1.015x |

| kernel | base ms | cand ms | speedup | 95% CI | A/A noise | verdict |
|:--|--:|--:|--:|:--|--:|:--|
| `dlp/koblitz_signed_rho_k0_n41` | 50.202 | 49.475 | 1.012x | 1.000–1.027 | ±1.3% | neutral |
| `field_ec/koblitz_curve_mul_n53_1k` | 4.996 | 4.833 | 1.018x | 0.967–1.036 | ±0.6% | neutral |
| `field_ec/koblitz_n53_add_many_lazy_64x2k` | 4.579 | 4.572 | 1.002x | 0.991–1.037 | ±2.9% | neutral |
| `field_ec/koblitz_n53_fast_mul_2k` | 9.898 | 9.329 | 1.063x | 1.055–1.090 | ±1.8% | faster |
| `pdp/pair_table_build_n31_l10` | 62.889 | 56.854 | 1.088x | 1.061–1.100 | ±1.9% | faster |
| `relation/koblitz_collect_k0n41_w164_u4096` | 20.576 | 19.377 | 1.062x | 1.047–1.087 | ±3.2% | neutral |
| `relation/koblitz_collect_k0n53_w477_u1024` | 23.638 | 22.255 | 1.047x | 1.022–1.173 | ±6.1% | neutral |
| `relation/koblitz_descent_k0n53_m2_x4` | 53.876 | 52.828 | 1.012x | 0.991–1.057 | ±5.3% | neutral |
| `relation/koblitz_pair_table_k0n41_folded` | 18.853 | 17.894 | 1.038x | 1.026–1.065 | ±4.0% | neutral |
| `relation/koblitz_rung_k0n31` | 17.474 | 16.744 | 0.988x | 0.982–1.054 | ±2.8% | neutral |
| `relation/orbit_ic_j0_34bit_x8` | 59.056 | 62.429 | 0.986x | 0.959–1.027 | ±5.3% | neutral |
| `sat/koblitz_bool_cnf_m3_n15_b1500_x2` | 163.886 | 164.420 | 1.036x | 0.989–1.039 | ±8.0% | neutral |
| `sat/koblitz_bool_native_m2_n19_x2` | 147.047 | 149.407 | 1.002x | 0.945–1.031 | ±3.4% | neutral |
| `sat/koblitz_bool_native_m3_n15_x3` | 59.948 | 59.490 | 1.008x | 0.974–1.016 | ±0.8% | neutral |
