# perfbench wall-time comparison

**Performance index PI = 0.920x** (95% CI 0.904–0.938, 7 paired rounds)

| area | weight | kernels | area index |
|:--|--:|--:|--:|
| dlp | 0.200 | 1 | 0.762x |
| field_ec | 0.200 | 3 | 0.948x |
| pdp | 0.200 | 1 | 0.904x |
| relation | 0.200 | 6 | 0.981x |
| sat | 0.200 | 3 | 1.029x |

| kernel | base ms | cand ms | speedup | 95% CI | A/A noise | verdict |
|:--|--:|--:|--:|:--|--:|:--|
| `dlp/koblitz_signed_rho_k0_n41` | 50.800 | 66.459 | 0.762x | 0.751–0.776 | ±0.8% | slower |
| `field_ec/koblitz_curve_mul_n53_1k` | 5.021 | 5.400 | 0.931x | 0.913–0.942 | ±1.4% | slower |
| `field_ec/koblitz_n53_add_many_lazy_64x2k` | 4.580 | 4.625 | 0.971x | 0.887–0.997 | ±0.3% | slower |
| `field_ec/koblitz_n53_fast_mul_2k` | 9.977 | 10.602 | 0.943x | 0.940–1.186 | ±5.3% | neutral |
| `pdp/pair_table_build_n31_l10` | 65.628 | 72.680 | 0.904x | 0.880–0.913 | ±4.4% | slower |
| `relation/koblitz_collect_k0n41_w164_u4096` | 20.693 | 20.481 | 1.019x | 0.984–1.533 | ±1.3% | neutral |
| `relation/koblitz_collect_k0n53_w477_u1024` | 23.756 | 22.530 | 1.027x | 0.905–1.067 | ±8.9% | neutral |
| `relation/koblitz_descent_k0n53_m2_x4` | 55.954 | 56.511 | 0.983x | 0.960–1.026 | ±10.6% | neutral |
| `relation/koblitz_pair_table_k0n41_folded` | 18.949 | 19.239 | 0.977x | 0.707–1.010 | ±0.8% | neutral |
| `relation/koblitz_rung_k0n31` | 17.156 | 18.980 | 0.902x | 0.897–0.942 | ±4.5% | slower |
| `relation/orbit_ic_j0_34bit_x8` | 65.396 | 65.945 | 0.981x | 0.925–1.040 | ±3.1% | neutral |
| `sat/koblitz_bool_cnf_m3_n15_b1500_x2` | 168.376 | 166.574 | 1.035x | 1.010–1.069 | ±4.3% | neutral |
| `sat/koblitz_bool_native_m2_n19_x2` | 152.552 | 147.291 | 1.036x | 1.017–1.070 | ±3.7% | neutral |
| `sat/koblitz_bool_native_m3_n15_x3` | 60.273 | 59.531 | 1.016x | 1.011–1.028 | ±2.2% | neutral |
