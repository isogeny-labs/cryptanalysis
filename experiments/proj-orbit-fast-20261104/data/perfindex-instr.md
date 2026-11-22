# perfbench instruction-count comparison (callgrind Ir, 1 thread)

**Performance index PI = 1.032x** (95% CI 1.032–1.032, 1 paired rounds)

| area | weight | kernels | area index |
|:--|--:|--:|--:|
| dlp | 0.500 | 1 | 0.999x |
| relation | 0.500 | 6 | 1.065x |

| kernel | base Ir | cand Ir | speedup | 95% CI | A/A noise | verdict |
|:--|--:|--:|--:|:--|--:|:--|
| `dlp/koblitz_signed_rho_k0_n41` | 336396139.000 | 336603906.000 | 0.999x | 0.999–0.999 | n/a | neutral |
| `relation/koblitz_collect_k0n41_w164_u4096` | 314746695.000 | 314791300.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `relation/koblitz_collect_k0n53_w477_u1024` | 326057058.000 | 326191936.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `relation/koblitz_descent_k0n53_m2_x4` | 731165938.000 | 573015816.000 | 1.276x | 1.276–1.276 | n/a | faster |
| `relation/koblitz_pair_table_k0n41_folded` | 163523162.000 | 163523154.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `relation/koblitz_rung_k0n31` | 231453917.000 | 202615780.000 | 1.142x | 1.142–1.142 | n/a | faster |
| `relation/sparse_solve_r45_c4800_w3` | 559021803.000 | 559177213.000 | 1.000x | 1.000–1.000 | n/a | neutral |
