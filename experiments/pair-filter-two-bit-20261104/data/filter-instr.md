# perfbench instruction-count comparison (callgrind Ir, 1 thread)

**INVALID: at least one kernel's output fingerprint changed. No index.**

| area | weight | kernels | area index |
|:--|--:|--:|--:|
| dlp | 0.333 | 1 | 0.999x |
| pdp | 0.333 | 2 | 0.987x |
| relation | 0.333 | 5 | 1.004x |

| kernel | base Ir | cand Ir | speedup | 95% CI | A/A noise | verdict |
|:--|--:|--:|--:|:--|--:|:--|
| `dlp/koblitz_signed_rho_k0_n41` | 336396339.000 | 336604048.000 | 0.999x | 0.999–0.999 | n/a | neutral |
| `pdp/mitm_m3_n31` | 374872036.000 | 378152490.000 | 0.991x | 0.991–0.991 | n/a | neutral |
| `pdp/mitm_m4_n31` | 121176604.000 | 123260989.000 | 0.983x | 0.983–0.983 | n/a | neutral |
| `relation/koblitz_collect_k0n41_w164_u4096` | 314626561.000 | 309189516.000 | 1.018x | 1.018–1.018 | n/a | neutral |
| `relation/koblitz_collect_k0n53_w477_u1024` | 325690283.000 | 321929305.000 | 1.012x | 1.012–1.012 | n/a | neutral |
| `relation/koblitz_descent_k0n53_m2_x4` | 497264567.000 | 501163647.000 | 0.992x | 0.992–0.992 | n/a | neutral |
| `relation/koblitz_pair_table_k0n41_folded` | 163523166.000 | 164717175.000 | 0.993x | 0.993–0.993 | n/a | INVALID |
| `relation/koblitz_rung_k0n31` | 202550785.000 | 201340885.000 | 1.006x | 1.006–1.006 | n/a | neutral |
