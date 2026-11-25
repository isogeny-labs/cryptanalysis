# perfbench wall-time comparison

**Performance index PI = 1.202x** (95% CI 1.133–1.373, 15 paired rounds)

| area | weight | kernels | area index |
|:--|--:|--:|--:|
| relation | 1.000 | 2 | 1.202x |

| kernel | base ms | cand ms | speedup | 95% CI | A/A noise | verdict |
|:--|--:|--:|--:|:--|--:|:--|
| `relation/koblitz_descent_k0n53_m2_x4` | 96.217 | 78.981 | 1.254x | 1.118–1.371 | ±12.9% | neutral |
| `relation/koblitz_rung_k0n31` | 35.230 | 25.995 | 1.151x | 1.088–1.396 | ±15.0% | neutral |
