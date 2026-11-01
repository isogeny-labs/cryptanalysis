# perfbench instruction-count comparison (callgrind Ir, 1 thread)

**Performance index PI = 1.003x** (95% CI 1.003–1.003, 1 paired rounds)

| area | weight | kernels | area index |
|:--|--:|--:|--:|
| dlp | 1.000 | 14 | 1.003x |

| kernel | base Ir | cand Ir | speedup | 95% CI | A/A noise | verdict |
|:--|--:|--:|--:|:--|--:|:--|
| `dlp/c_bsgs_ec32` | 39956244.000 | 39956244.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `dlp/c_bsgs_zp36` | 85814768.000 | 85814768.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `dlp/c_cheon56` | 76953945.000 | 76953945.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `dlp/c_glv_rho_j0_32` | 115276168.000 | 115276168.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `dlp/c_gpu_rho_emulate_ec32` | 74211602.000 | 74211602.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `dlp/c_grumpy_ec32` | 50675874.000 | 50675874.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `dlp/c_kangaroo_ec56_w34` | 171410743.000 | 171410743.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `dlp/c_kangaroo_zp61_w36` | 186207666.000 | 186207666.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `dlp/c_pohlig_ec48s` | 30540401.000 | 30540401.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `dlp/c_pohlig_zp61s` | 118903535.000 | 118903535.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `dlp/c_precomp_build_ec32` | 586842473.000 | 586842473.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `dlp/c_precomp_online_ec32` | 82521617.000 | 82521617.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `dlp/c_rho_ec36` | 199957434.000 | 189530435.000 | 1.055x | 1.055–1.055 | n/a | faster |
| `dlp/c_rho_zp40` | 270988160.000 | 273556841.000 | 0.991x | 0.991–0.991 | n/a | neutral |
