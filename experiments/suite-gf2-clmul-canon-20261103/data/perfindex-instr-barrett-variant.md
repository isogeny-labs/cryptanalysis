# perfbench instruction-count comparison (callgrind Ir, 1 thread)

**Performance index PI = 1.034x** (95% CI 1.034–1.034, 1 paired rounds)

| area | weight | kernels | area index |
|:--|--:|--:|--:|
| dlp | 0.333 | 13 | 1.039x |
| pdp | 0.333 | 1 | 1.000x |
| relation | 0.333 | 20 | 1.064x |

| kernel | base Ir | cand Ir | speedup | 95% CI | A/A noise | verdict |
|:--|--:|--:|--:|:--|--:|:--|
| `dlp/aut_folded_rho_j0_p25` | 40503931.000 | 40503931.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `dlp/bsgs_fast_toy40_w1_x4` | 581161704.000 | 581161704.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `dlp/bsgs_fast_toy40_w4_interval38_x8` | 824819723.000 | 824819777.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `dlp/collab_walkers_demo32_x8` | 1529410909.000 | 1529143611.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `dlp/gaudry_schost_negation_demo32` | 2222313028.000 | 2222314301.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `dlp/koblitz_signed_rho_k0_n41` | 560832157.000 | 352767018.000 | 1.590x | 1.590–1.590 | n/a | faster |
| `dlp/orbit_rho_baseline_40bit_x4` | 853773456.000 | 850324018.000 | 1.004x | 1.004–1.004 | n/a | neutral |
| `dlp/pohlig_hellman_smooth47_x8` | 108467315.000 | 108464888.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `dlp/rho_dp_zp_multi_q34_x3` | 36229753.000 | 35246204.000 | 1.028x | 1.028–1.028 | n/a | faster |
| `dlp/rho_floyd_zp_q36` | 111996099.000 | 111996126.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `dlp/weak_mov_supersingular_k2_160` | 1756525794.000 | 1754735870.000 | 1.001x | 1.001–1.001 | n/a | neutral |
| `dlp/weak_pohlig_hellman_smooth_128` | 1301237142.000 | 1301673244.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `dlp/weak_smart_anomalous_256` | 105692587.000 | 105692606.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `pdp/relation_solver_u1024` | 184363533.000 | 184363541.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `relation/block_wiedemann_r45_n768_w13` | 483330032.000 | 483330032.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `relation/gnfs_semiprime_30d` | 1536508896.000 | 1539745172.000 | 0.998x | 0.998–0.998 | n/a | neutral |
| `relation/koblitz_collect_k0n41_w164_u4096` | 470184141.000 | 367567209.000 | 1.279x | 1.279–1.279 | n/a | faster |
| `relation/koblitz_collect_k0n53_w477_u1024` | 401451057.000 | 297545195.000 | 1.349x | 1.349–1.349 | n/a | faster |
| `relation/koblitz_descent_k0n53_m2_x4` | 888629088.000 | 608098823.000 | 1.461x | 1.461–1.461 | n/a | faster |
| `relation/koblitz_pair_table_k0n41_folded` | 231062807.000 | 193067212.000 | 1.197x | 1.197–1.197 | n/a | faster |
| `relation/koblitz_rung_k0n31` | 313471552.000 | 260904836.000 | 1.201x | 1.201–1.201 | n/a | faster |
| `relation/nfs_linalg_deps_40d` | 782400472.000 | 778878295.000 | 1.005x | 1.005–1.005 | n/a | neutral |
| `relation/nfs_line_sieve_40d_b8` | 1314481952.000 | 1314481952.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `relation/orbit_ic_j0_34bit_x8` | 220670313.000 | 226206854.000 | 0.976x | 0.976–0.976 | n/a | slower |
| `relation/pm1_stage2_95bit` | 150170367.000 | 150170367.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `relation/pq_sparse_solve_m127_c640` | 270741276.000 | 270741276.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `relation/pq_wiedemann_m127_c160` | 435460033.000 | 432994492.000 | 1.006x | 1.006–1.006 | n/a | neutral |
| `relation/qs_semiprime_20d` | 77086692.000 | 77798876.000 | 0.991x | 0.991–0.991 | n/a | neutral |
| `relation/qs_semiprime_30d` | 98035030.000 | 99400025.000 | 0.986x | 0.986–0.986 | n/a | neutral |
| `relation/qs_semiprime_40d` | 526770267.000 | 532053918.000 | 0.990x | 0.990–0.990 | n/a | neutral |
| `relation/residual_walk_lmw_b22_x3` | 264360728.000 | 264360728.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `relation/rho_factor_big_115bit_x4` | 113131965.000 | 113131965.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `relation/rho_factor_u64_62bit_x24` | 35260306.000 | 35260306.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `relation/sparse_solve_r45_c4800_w3` | 559037031.000 | 559035033.000 | 1.000x | 1.000–1.000 | n/a | neutral |
