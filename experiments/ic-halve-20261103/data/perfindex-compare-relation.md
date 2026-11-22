# perfbench wall-time comparison

**Performance index PI = 2.139x** (95% CI 1.979–2.170, 7 paired rounds)

| area | weight | kernels | area index |
|:--|--:|--:|--:|
| relation | 1.000 | 5 | 2.139x |

| kernel | base ms | cand ms | speedup | 95% CI | A/A noise | verdict |
|:--|--:|--:|--:|:--|--:|:--|
| `relation/c_dense_solve` | 11.013 | 1.245 | 8.800x | 6.355–9.314 | ±0.9% | faster |
| `relation/c_ic_log_zp44` | 2.774 | 2.144 | 1.306x | 1.282–1.349 | ±1.4% | faster |
| `relation/c_ic_precompute_zp44` | 32.611 | 17.412 | 1.878x | 1.766–1.883 | ±2.6% | faster |
| `relation/c_ic_randexp_zp36` | 3.377 | 2.861 | 1.178x | 1.177–1.193 | ±2.0% | faster |
| `relation/c_linsolve_sparse` | 16.921 | 9.615 | 1.761x | 1.736–1.781 | ±2.4% | faster |
