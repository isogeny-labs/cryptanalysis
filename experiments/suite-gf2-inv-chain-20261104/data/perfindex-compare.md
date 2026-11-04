# perfbench wall-time comparison

**Performance index PI = 1.215x** (95% CI 1.176–1.285, 7 paired rounds)

| area | weight | kernels | area index |
|:--|--:|--:|--:|
| dlp | 0.250 | 1 | 1.199x |
| field_ec | 0.250 | 6 | 1.348x |
| pdp | 0.250 | 5 | 1.323x |
| relation | 0.250 | 20 | 1.018x |

| kernel | base ms | cand ms | speedup | 95% CI | A/A noise | verdict |
|:--|--:|--:|--:|:--|--:|:--|
| `dlp/koblitz_signed_rho_k0_n41` | 66.864 | 54.489 | 1.199x | 1.171–1.336 | ±4.9% | faster |
| `field_ec/gf2_n53_batch_inv_4x64k` | 6.648 | 6.745 | 0.983x | 0.965–1.006 | ±2.4% | neutral |
| `field_ec/gf2_n53_inv_16k` | 8.904 | 2.173 | 4.144x | 4.096–4.312 | ±1.5% | faster |
| `field_ec/gf2_n53_mul_sqr_1m` | 9.765 | 9.629 | 1.015x | 0.988–1.626 | ±69.6% | neutral |
| `field_ec/koblitz_curve_mul_n53_1k` | 7.098 | 4.857 | 1.464x | 1.460–1.475 | ±1.1% | faster |
| `field_ec/koblitz_n53_add_many_lazy_64x2k` | 8.166 | 8.294 | 1.004x | 0.927–1.014 | ±1.3% | neutral |
| `field_ec/koblitz_n53_fast_mul_2k` | 13.774 | 13.845 | 0.990x | 0.803–1.028 | ±5.0% | neutral |
| `pdp/enumerate_m2_n23` | 4.186 | 2.127 | 1.932x | 1.856–1.987 | ±2.7% | faster |
| `pdp/enumerate_m3_n15` | 2.781 | 1.587 | 1.720x | 1.658–1.988 | ±8.2% | faster |
| `pdp/mitm_m3_n31` | 56.972 | 53.791 | 1.022x | 0.770–1.165 | ±6.8% | neutral |
| `pdp/mitm_m4_n31` | 17.794 | 19.276 | 1.160x | 0.863–1.295 | ±5.3% | neutral |
| `pdp/subspace_oracle_n20_l7` | 18.659 | 18.000 | 1.031x | 0.760–1.071 | ±3.7% | neutral |
| `relation/block_wiedemann_r45_n768_w13` | 42.351 | 42.006 | 1.016x | 0.991–1.426 | ±26.5% | neutral |
| `relation/gnfs_semiprime_30d` | 230.805 | 221.376 | 1.050x | 1.008–1.061 | ±12.8% | neutral |
| `relation/koblitz_collect_k0n41_w164_u4096` | 42.500 | 42.684 | 1.193x | 0.844–1.227 | ±6.5% | neutral |
| `relation/koblitz_collect_k0n53_w477_u1024` | 50.908 | 48.270 | 1.012x | 0.970–1.054 | ±6.4% | neutral |
| `relation/koblitz_descent_k0n53_m2_x4` | 114.359 | 85.414 | 1.254x | 1.157–1.371 | ±15.4% | neutral |
| `relation/koblitz_pair_table_k0n41_folded` | 26.969 | 33.671 | 0.864x | 0.778–1.263 | ±4.5% | neutral |
| `relation/koblitz_rung_k0n31` | 28.098 | 25.754 | 1.108x | 1.091–1.160 | ±2.8% | faster |
| `relation/nfs_linalg_deps_40d` | 136.033 | 133.106 | 1.012x | 0.847–1.026 | ±13.6% | neutral |
| `relation/nfs_line_sieve_40d_b8` | 183.904 | 168.136 | 1.021x | 0.878–1.084 | ±8.9% | neutral |
| `relation/orbit_ic_j0_34bit_x8` | 81.186 | 80.680 | 1.001x | 0.963–1.015 | ±5.8% | neutral |
| `relation/pm1_stage2_95bit` | 33.509 | 31.325 | 0.995x | 0.989–1.174 | ±16.3% | neutral |
| `relation/pq_sparse_solve_m127_c640` | 28.460 | 28.628 | 0.992x | 0.971–1.181 | ±2.6% | neutral |
| `relation/pq_wiedemann_m127_c160` | 34.804 | 34.459 | 0.990x | 0.613–1.011 | ±7.1% | neutral |
| `relation/qs_semiprime_20d` | 8.861 | 9.204 | 0.979x | 0.958–1.001 | ±7.8% | neutral |
| `relation/qs_semiprime_30d` | 12.703 | 13.016 | 0.976x | 0.684–0.999 | ±1.8% | neutral |
| `relation/qs_semiprime_40d` | 60.004 | 61.416 | 0.993x | 0.965–1.021 | ±3.2% | neutral |
| `relation/residual_walk_lmw_b22_x3` | 63.124 | 66.489 | 0.960x | 0.949–1.230 | ±12.0% | neutral |
| `relation/rho_factor_big_115bit_x4` | 15.616 | 15.251 | 0.992x | 0.977–1.270 | ±3.7% | neutral |
| `relation/rho_factor_u64_62bit_x24` | 9.066 | 9.051 | 1.003x | 1.002–1.024 | ±0.7% | neutral |
| `relation/sparse_solve_r45_c4800_w3` | 57.512 | 56.753 | 1.015x | 0.978–1.041 | ±1.8% | neutral |
