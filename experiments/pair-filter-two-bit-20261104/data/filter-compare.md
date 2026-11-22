# perfbench wall-time comparison

**Performance index PI = 1.027x** (95% CI 0.997–1.044, 15 paired rounds)

| area | weight | kernels | area index |
|:--|--:|--:|--:|
| pdp | 0.500 | 2 | 0.996x |
| relation | 0.500 | 4 | 1.060x |

| kernel | base ms | cand ms | speedup | 95% CI | A/A noise | verdict |
|:--|--:|--:|--:|:--|--:|:--|
| `pdp/mitm_m3_n31` | 64.954 | 67.349 | 0.996x | 0.932–1.012 | ±12.6% | neutral |
| `pdp/mitm_m4_n31` | 16.637 | 16.733 | 0.995x | 0.953–1.023 | ±6.3% | neutral |
| `relation/koblitz_collect_k0n41_w164_u4096` | 50.031 | 48.173 | 1.030x | 0.938–1.137 | ±10.6% | neutral |
| `relation/koblitz_collect_k0n53_w477_u1024` | 64.023 | 55.922 | 1.136x | 1.093–1.162 | ±3.9% | faster |
| `relation/koblitz_descent_k0n53_m2_x4` | 88.022 | 80.664 | 1.085x | 0.996–1.159 | ±11.5% | neutral |
| `relation/koblitz_rung_k0n31` | 28.929 | 29.754 | 0.993x | 0.930–1.081 | ±10.7% | neutral |
