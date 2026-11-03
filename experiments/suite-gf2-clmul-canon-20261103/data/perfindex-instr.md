# perfbench instruction-count comparison (callgrind Ir, 1 thread)

**Performance index PI = 1.128x** (95% CI 1.128–1.128, 1 paired rounds)

| area | weight | kernels | area index |
|:--|--:|--:|--:|
| dlp | 0.200 | 1 | 1.271x |
| field_ec | 0.200 | 3 | 1.095x |
| pdp | 0.200 | 1 | 1.116x |
| relation | 0.200 | 6 | 1.159x |
| sat | 0.200 | 3 | 1.016x |

| kernel | base Ir | cand Ir | speedup | 95% CI | A/A noise | verdict |
|:--|--:|--:|--:|:--|--:|:--|
| `dlp/koblitz_signed_rho_k0_n41` | 560831640.000 | 441241420.000 | 1.271x | 1.271–1.271 | n/a | faster |
| `field_ec/koblitz_curve_mul_n53_1k` | 102657009.000 | 96250347.000 | 1.067x | 1.067–1.067 | n/a | faster |
| `field_ec/koblitz_n53_add_many_lazy_64x2k` | 72409072.000 | 66163632.000 | 1.094x | 1.094–1.094 | n/a | faster |
| `field_ec/koblitz_n53_fast_mul_2k` | 167323097.000 | 148905037.000 | 1.124x | 1.124–1.124 | n/a | faster |
| `pdp/pair_table_build_n31_l10` | 808474004.000 | 724467567.000 | 1.116x | 1.116–1.116 | n/a | faster |
| `relation/koblitz_collect_k0n41_w164_u4096` | 470182704.000 | 381318583.000 | 1.233x | 1.233–1.233 | n/a | faster |
| `relation/koblitz_collect_k0n53_w477_u1024` | 401451260.000 | 331685302.000 | 1.210x | 1.210–1.210 | n/a | faster |
| `relation/koblitz_descent_k0n53_m2_x4` | 888648815.000 | 771557180.000 | 1.152x | 1.152–1.152 | n/a | faster |
| `relation/koblitz_pair_table_k0n41_folded` | 231062807.000 | 191714565.000 | 1.205x | 1.205–1.205 | n/a | faster |
| `relation/koblitz_rung_k0n31` | 313464830.000 | 267788086.000 | 1.171x | 1.171–1.171 | n/a | faster |
| `relation/orbit_ic_j0_34bit_x8` | 220670313.000 | 220701087.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `sat/koblitz_bool_cnf_m3_n15_b1500_x2` | 1036026184.000 | 985059314.000 | 1.052x | 1.052–1.052 | n/a | faster |
| `sat/koblitz_bool_native_m2_n19_x2` | 1190045502.000 | 1188671485.000 | 1.001x | 1.001–1.001 | n/a | neutral |
| `sat/koblitz_bool_native_m3_n15_x3` | 547997519.000 | 550469038.000 | 0.996x | 0.996–0.996 | n/a | neutral |
