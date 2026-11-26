# M31 basis cardinality screen on one public target

The first frozen panel followed `PROTOCOL.md` on the same public M31 curve, generator and target. The auxiliary `s=10` basis has exactly 500 lifted representatives; the `s=11` basis has 1,013 and contains the full 500-point set. The plain control uses the first 500 or 1,013 accepted x coordinates. The 500-point arms regenerated the byte-identical frozen fixture bases. All 48 fresh-process arms returned the same generator-verified public answer `123456789`, and the Rust collector checked each accepted relation. No arm failed or was censored. The two cardinalities have different factor bases and collector workloads by design; their trial counts and table maps must not be asserted equal.

| Construction | Basis size | Charged wall median ms | Charged CPU median ms | Table median ms | Elimination median ms | Trials median | Relations median | Index entries median |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Auxiliary | 500 | 77.970 | 75.251 | 9.778 | 3.371 | 6,144 | 470 | 499,940 |
| Auxiliary | 1,013 | 150.680 | 148.157 | 45.699 | 16.546 | 1,913 | 929 | 2,051,192 |
| Plain | 500 | 68.748 | 64.758 | 10.685 | 3.330 | 5,737 | 455 | 499,916 |
| Plain | 1,013 | 137.998 | 133.559 | 46.866 | 16.440 | 2,003 | 933 | 2,051,300 |

Median paired 500/1,013 wall and CPU ratios were `0.4997`/`0.4986` on auxiliary and `0.4862`/`0.4809` on plain. The 1,013-point arm won wall in 0/12 auxiliary and 1/12 plain blocks, and CPU in 0/12 on either basis. Its relation yield is higher, but table construction rose about 4.7-fold and elimination about 5-fold, while each collector trial also processes 2,026 signed basis points instead of 1,000. The full charged cost regressed by about 2-fold. This rules out this particular nested `s=11` size expansion as a cold single-target improvement on these fixtures; it does not rule out different basis or elimination algorithms. [pcc:unverified]

The wall and parent-plus-child CPU clocks start before Python basis generation and end after Rust process exit. `setup_ns` in the raw Rust output covers only Rust input parsing; it is not the full charged setup. Compilation and frozen JSON loading were outside the timed window; OS caches were not flushed. These are local producer-run measurements and have no independent signed standing. Raw CSV SHA-256: `6a2dc7a4240e2618ad2414d5c09588266e6f3b9c0f0c3f50d80867524a2b5fd3`.

The first panel used source commit `924a82bea` (`main.rs` SHA-256 `5f2d434cceead28317da8448440376bc75fbf3edfec499cd8a03f53d6bfda051`). The following screens use the same Rust algorithm with exact-index capacity scaled for smaller bases.

## Smaller prefixes of the frozen 500-point bases

The separately frozen `PROTOCOL_SMALL.md` used 18 six-arm blocks (108 fresh processes) on sizes 250, 350 and 500. Every arm returned the generator-verified scalar `123456789`; the 500-point bases matched the frozen fixtures and smaller bases matched their prefixes. No arm failed or was censored.

| Construction | Size | Charged wall median ms | Charged CPU median ms | Table median ms | Elimination median ms | Trials median | Relations median |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Auxiliary | 250 | 112.538 | 83.332 | 3.215 | 1.041 | 24,155 | 232 |
| Auxiliary | 350 | 103.022 | 80.341 | 6.346 | 1.649 | 13,675 | 316 |
| Auxiliary | 500 | 102.244 | 79.997 | 11.799 | 3.390 | 6,144 | 470 |
| Plain | 250 | 91.528 | 69.917 | 2.543 | 1.033 | 24,182 | 233 |
| Plain | 350 | 77.533 | 62.517 | 6.312 | 1.499 | 12,496 | 324 |
| Plain | 500 | 89.813 | 70.335 | 13.707 | 3.233 | 5,737 | 455 |

Median paired 500/candidate wall and CPU ratios were auxiliary 250 `0.8626`/`0.9257`, auxiliary 350 `0.9316`/`0.9867`, plain 250 `1.0069`/`0.9715`, and plain 350 `1.0144`/`1.0526`. The plain 350 result is small and host wall timing varied; it needs a separate confirmation before adoption. Neither smaller size improved both constructions under this screen. Their lower table and elimination costs were offset by more collector trials, especially on auxiliary. [pcc:unverified]

Smaller-screen CSV SHA-256: `452152d8914500ed593d676676e4d41a07646c88986ababdaf2534a96a5451fe`.

## Equal-cardinality auxiliary-chain selection

`PROTOCOL_EQUAL.md` held the basis size at 500 and compared the frozen `s=10` basis with the first 500 lifted `s=11` points in 24 matched pairs. Both returned the checked public answer on all 48 fresh-process arms. The `s=10` arm matched the frozen fixture. Table and elimination medians were essentially unchanged: `9.467`/`3.327` ms for `s=10`, `9.532`/`3.189` ms for `s=11`. Median trials were 6,144 versus 5,827, and relation counts 470 versus 456. Rust internal total medians were also nearly equal, `57.690` versus `57.553` ms.

Charged wall medians were `72.965` ms (`s=10`) and `85.249` ms (`s=11`); CPU medians were `71.877` and `84.094` ms. Median paired `s=10/s=11` ratios were `0.9057` wall and `0.8851` CPU, with `s=11` winning only 1/24 pairs on each measure. The extra cold cost is before or around Rust process invocation; the larger `s=11` chain generation is the likely cause, given the nearly equal Rust totals. That attribution is an inference from the clocks, not a separately instrumented causal proof. Equal-size `s=11` selection did not improve the complete pipeline here. [pcc:unverified]

Equal-cardinality CSV SHA-256: `e8da086248c6185ab51daf607a82f610cab8152db544e8b30d1be48e71cdf634`.
