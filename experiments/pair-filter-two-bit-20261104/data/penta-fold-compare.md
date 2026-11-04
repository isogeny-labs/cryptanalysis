# perfbench wall-time comparison

**Performance index PI = 0.991x** (95% CI 0.950–1.043, 9 paired rounds)

| area | weight | kernels | area index |
|:--|--:|--:|--:|
| dlp | 0.333 | 1 | 1.057x |
| field_ec | 0.333 | 7 | 0.936x |
| relation | 0.333 | 5 | 0.984x |

| kernel | base ms | cand ms | speedup | 95% CI | A/A noise | verdict |
|:--|--:|--:|--:|:--|--:|:--|
| `dlp/koblitz_signed_rho_k0_n41` | 71.309 | 66.493 | 1.057x | 1.015–1.196 | ±7.5% | neutral |
| `field_ec/frobenius_canon_n53_bulk_256k` | 5.323 | 6.218 | 0.983x | 0.686–1.019 | ±1.6% | neutral |
| `field_ec/gf2_n53_batch_inv_4x64k` | 8.762 | 8.611 | 0.994x | 0.682–1.570 | ±59.5% | neutral |
| `field_ec/gf2_n53_inv_16k` | 2.242 | 2.647 | 0.869x | 0.713–1.367 | ±63.4% | neutral |
| `field_ec/gf2_n53_mul_sqr_1m` | 10.886 | 14.228 | 0.794x | 0.557–0.860 | ±11.4% | slower |
| `field_ec/koblitz_curve_mul_n53_1k` | 5.791 | 6.116 | 0.961x | 0.800–1.015 | ±5.9% | neutral |
| `field_ec/koblitz_n53_add_many_lazy_64x2k` | 9.935 | 9.817 | 0.989x | 0.936–1.286 | ±35.6% | neutral |
| `field_ec/koblitz_n53_fast_mul_2k` | 15.840 | 16.744 | 0.984x | 0.915–1.060 | ±4.2% | neutral |
| `relation/koblitz_collect_k0n41_w164_u4096` | 48.727 | 49.483 | 0.996x | 0.886–1.655 | ±79.6% | neutral |
| `relation/koblitz_collect_k0n53_w477_u1024` | 61.342 | 70.652 | 0.865x | 0.644–0.990 | ±14.1% | neutral |
| `relation/koblitz_descent_k0n53_m2_x4` | 90.440 | 89.379 | 0.972x | 0.854–1.059 | ±33.2% | neutral |
| `relation/koblitz_pair_table_k0n41_folded` | 46.858 | 31.312 | 1.115x | 0.933–1.658 | ±24.2% | neutral |
| `relation/koblitz_rung_k0n31` | 28.552 | 29.738 | 0.988x | 0.718–1.586 | ±100.5% | neutral |
