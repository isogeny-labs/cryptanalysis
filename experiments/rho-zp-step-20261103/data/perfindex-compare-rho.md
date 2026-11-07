# perfbench wall-time comparison

**Performance index PI = 1.071x** (95% CI 1.059–1.093, 7 paired rounds)

| area | weight | kernels | area index |
|:--|--:|--:|--:|
| dlp | 1.000 | 2 | 1.071x |

| kernel | base ms | cand ms | speedup | 95% CI | A/A noise | verdict |
|:--|--:|--:|--:|:--|--:|:--|
| `dlp/c_rho_ec36` | 20.101 | 19.094 | 1.032x | 1.009–1.053 | ±3.6% | neutral |
| `dlp/c_rho_zp40` | 32.752 | 29.187 | 1.111x | 1.092–1.135 | ±2.7% | faster |
