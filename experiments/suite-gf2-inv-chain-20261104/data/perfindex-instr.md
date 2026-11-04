# perfbench instruction-count comparison (callgrind Ir, 1 thread)

**Performance index PI = 1.239x** (95% CI 1.239–1.239, 1 paired rounds)

| area | weight | kernels | area index |
|:--|--:|--:|--:|
| dlp | 0.250 | 1 | 1.312x |
| field_ec | 0.250 | 6 | 1.293x |
| pdp | 0.250 | 5 | 1.280x |
| relation | 0.250 | 7 | 1.084x |

| kernel | base Ir | cand Ir | speedup | 95% CI | A/A noise | verdict |
|:--|--:|--:|--:|:--|--:|:--|
| `dlp/koblitz_signed_rho_k0_n41` | 441242023.000 | 336396040.000 | 1.312x | 1.312–1.312 | n/a | faster |
| `field_ec/gf2_n53_batch_inv_4x64k` | 63242076.000 | 65019308.000 | 0.973x | 0.973–0.973 | n/a | slower |
| `field_ec/gf2_n53_inv_16k` | 54902826.000 | 19775530.000 | 2.776x | 2.776–2.776 | n/a | faster |
| `field_ec/gf2_n53_mul_sqr_1m` | 124937578.000 | 124938100.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `field_ec/koblitz_curve_mul_n53_1k` | 96250347.000 | 54008142.000 | 1.782x | 1.782–1.782 | n/a | faster |
| `field_ec/koblitz_n53_add_many_lazy_64x2k` | 66163632.000 | 67221552.000 | 0.984x | 0.984–0.984 | n/a | neutral |
| `field_ec/koblitz_n53_fast_mul_2k` | 148905037.000 | 150705981.000 | 0.988x | 0.988–0.988 | n/a | neutral |
| `pdp/enumerate_m2_n23` | 26397911.000 | 18733372.000 | 1.409x | 1.409–1.409 | n/a | faster |
| `pdp/enumerate_m3_n15` | 15392679.000 | 11623444.000 | 1.324x | 1.324–1.324 | n/a | faster |
| `pdp/mitm_m3_n31` | 420647388.000 | 374870369.000 | 1.122x | 1.122–1.122 | n/a | faster |
| `pdp/mitm_m4_n31` | 148231146.000 | 121176613.000 | 1.223x | 1.223–1.223 | n/a | faster |
| `pdp/subspace_oracle_n20_l7` | 221626486.000 | 165407168.000 | 1.340x | 1.340–1.340 | n/a | faster |
| `relation/block_wiedemann_r45_n768_w13` | 483328716.000 | 483349767.000 | 1.000x | 1.000–1.000 | n/a | neutral |
| `relation/koblitz_collect_k0n41_w164_u4096` | 381318973.000 | 314744546.000 | 1.212x | 1.212–1.212 | n/a | faster |
| `relation/koblitz_collect_k0n53_w477_u1024` | 331686721.000 | 326059256.000 | 1.017x | 1.017–1.017 | n/a | neutral |
| `relation/koblitz_descent_k0n53_m2_x4` | 771552630.000 | 731162666.000 | 1.055x | 1.055–1.055 | n/a | faster |
| `relation/koblitz_pair_table_k0n41_folded` | 191714347.000 | 163523162.000 | 1.172x | 1.172–1.172 | n/a | faster |
| `relation/koblitz_rung_k0n31` | 267808431.000 | 231419594.000 | 1.157x | 1.157–1.157 | n/a | faster |
| `relation/sparse_solve_r45_c4800_w3` | 559077679.000 | 559130907.000 | 1.000x | 1.000–1.000 | n/a | neutral |
