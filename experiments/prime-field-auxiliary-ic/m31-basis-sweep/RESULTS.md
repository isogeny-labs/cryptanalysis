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
