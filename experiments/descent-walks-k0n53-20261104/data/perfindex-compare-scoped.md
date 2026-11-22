# perfbench wall-time comparison

**INVALID: at least one kernel's output fingerprint changed. No index.**

| area | weight | kernels | area index |
|:--|--:|--:|--:|
| dlp | 0.500 | 1 | 1.028x |
| relation | 0.500 | 4 | 1.039x |

| kernel | base ms | cand ms | speedup | 95% CI | A/A noise | verdict |
|:--|--:|--:|--:|:--|--:|:--|
| `dlp/koblitz_signed_rho_k0_n41` | 69.224 | 66.279 | 1.028x | 0.993–1.044 | ±7.8% | neutral |
| `relation/koblitz_collect_k0n41_w164_u4096` | 41.718 | 41.607 | 1.005x | 1.003–1.016 | ±15.5% | neutral |
| `relation/koblitz_collect_k0n53_w477_u1024` | 50.748 | 48.686 | 1.038x | 0.995–1.343 | ±6.5% | neutral |
| `relation/koblitz_descent_k0n53_m2_x4` | 103.817 | 89.052 | 1.222x | 1.088–1.362 | ±9.7% | INVALID |
| `relation/koblitz_rung_k0n31` | 32.170 | 34.511 | 0.913x | 0.788–1.493 | ±19.7% | neutral |
