# M31 x bitmap capacity sweep and confirmation

The capacity sweep followed `BITMAP_SIZE_PROTOCOL.md`: 30 matched five-arm blocks, 150 fresh Rust processes, over the frozen public auxiliary and plain M31 fixtures. Its control was the merged 128 KiB x bitmap (`b20`); capacities from 32 to 512 KiB varied only the bitmap size. Before timing, all five arms emitted byte-identical complete sorted point-key/first-payload maps. Map SHA-256 was `ce7dab41355b3b236be455dbeaf9c46aaac83d29b272de5db727f54676407879` on auxiliary and `8b55e48edff4cbc66ac73ba30bc601ade0e7ae03fbf5439aaaaf2d807ec0d6fa` on plain. Within all 30 blocks, basis digest, verified scalar `123456789`, trial count, relation count, and index entries agreed. No arm failed or was censored.

| Basis | Capacity | Wall median ms | CPU median ms | Median paired b20/candidate wall | Median paired b20/candidate CPU | Wall wins | CPU wins |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Auxiliary | 32 KiB | 216.143 | 204.786 | 0.5832 | 0.6492 | 0/15 | 0/15 |
| Auxiliary | 64 KiB | 182.547 | 178.017 | 0.7628 | 0.7641 | 0/15 | 0/15 |
| Auxiliary | 128 KiB | 143.557 | 135.353 | 1.0000 | 1.0000 | — | — |
| Auxiliary | 256 KiB | 108.939 | 100.470 | 1.3093 | 1.3321 | 11/15 | 13/15 |
| Auxiliary | 512 KiB | 104.365 | 95.231 | 1.4611 | 1.4601 | 12/15 | 14/15 |
| Plain | 32 KiB | 191.678 | 178.784 | 0.6565 | 0.6542 | 1/15 | 0/15 |
| Plain | 64 KiB | 157.454 | 152.896 | 0.8262 | 0.7933 | 2/15 | 0/15 |
| Plain | 128 KiB | 128.341 | 122.395 | 1.0000 | 1.0000 | — | — |
| Plain | 256 KiB | 91.126 | 86.598 | 1.3644 | 1.3511 | 15/15 | 15/15 |
| Plain | 512 KiB | 81.972 | 76.593 | 1.5724 | 1.6042 | 15/15 | 15/15 |

The separately frozen `BITMAP_SIZE_CONFIRM_PROTOCOL.md` then compared only 128 and 512 KiB with 24 new matched blocks per basis (96 fresh-process arms). Both complete maps again matched byte for byte, all 48 blocks agreed on every recorded workload identity and the checked scalar, and no arm failed or was censored.

| Basis | Control wall median ms | 512 KiB wall median ms | Median paired wall ratio | 512 KiB wall wins | Control CPU median ms | 512 KiB CPU median ms | Median paired CPU ratio | 512 KiB CPU wins |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Auxiliary | 205.142 | 137.231 | 1.4821 | 20/24 | 167.558 | 99.768 | 1.5956 | 24/24 |
| Plain | 170.154 | 102.443 | 1.8117 | 22/24 | 142.819 | 83.558 | 1.6818 | 24/24 |

The confirmation wall medians drifted upward relative to the sweep; paired comparisons and CPU retain the same direction on both bases. These are direct end-to-end ratios of the two capacities, not products of stage ratios. The charged wall and parent-plus-child CPU windows include basis regeneration and checking, input writing, table and bitmap setup, relation collection, elimination, generator answer verification, and process exit. Compilation, fixture JSON loading, and complete index-map audits preceded timing; OS caches were not flushed. The Rust code still uses the archived explicit three-point collector, not the library `PreparedSolver` circuit.

The larger bitmap lowers full-pipeline cost on these two fixtures in both panels, under this local producer-run protocol. This is capacity tuning; neither asymptotic complexity nor other targets or hosts have been established. Independent signed PCC verification remains pending. [pcc:unverified]

Raw SHA-256: sweep `66bb4f309817ca050646bc2ebebd4754f2f8c780f4a1b9872412474b4398dd60`; confirmation `9ee91ddd0fa16f060818bef6c91607e115895904e7b8e7672c53f32661a23c25`.

## Direct cumulative comparison

The independently frozen `BITMAP_SIZE_DIRECT_PROTOCOL.md` compared the original checked flat-index collector directly with the selected 512 KiB bitmap collector. All 48 matched blocks across the two bases agreed on regenerated basis digest, index entry count, trial count, relation count, and generator-verified answer `123456789`. The complete sorted point-key/first-payload maps were byte-identical with the SHA-256 values above. No arm failed or was censored.

| Basis | Original wall median ms | 512 KiB wall median ms | Median paired original/candidate wall ratio | Candidate wall wins | Original CPU median ms | 512 KiB CPU median ms | Median paired CPU ratio | Candidate CPU wins |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Auxiliary | 256.277 | 90.949 | 2.8126 | 22/24 | 242.394 | 86.647 | 2.7142 | 24/24 |
| Plain | 223.455 | 79.880 | 2.7510 | 24/24 | 210.960 | 74.261 | 2.8347 | 24/24 |

This directly measured cumulative gain includes all charged basis generation, table/bitmap setup, relation collection, elimination, answer verification, and process exit. It is local evidence for these fixtures and this implementation, not an independently signed performance result or an asymptotic claim. The matched rho gap needs a new same-panel measurement rather than a ratio assembled from old panels. [pcc:unverified]

Direct raw CSV SHA-256: `fb009db76695dab6fe48edd274033a2e5e5ee37c9c5e930cf169edac58dc865b`.

## Same-target rho distance

The separate `BITMAP_SIZE_RHO_PROTOCOL.md` paired the selected collector with the archived C++ rho program on the same public generator and target. All 96 fresh-process arms returned the checked scalar `123456789`; all 48 blocks completed. The auxiliary and plain bases share the target, and rho was repeated for balanced pairing.

| Basis | IC wall median ms | Rho wall median ms | Median paired IC/rho wall | IC CPU median ms | Rho CPU median ms | Median paired IC/rho CPU |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Auxiliary | 87.562 | 10.181 | 8.6049 | 84.250 | 8.620 | 9.4339 |
| Plain | 87.228 | 17.333 | 6.5405 | 75.294 | 10.795 | 7.8078 |

This is a directly measured same-target distance to the archived rho implementation, with every IC phase and rho process charged as specified in the protocol. The rho program and Rust collector have different arithmetic implementations, and one host/target does not settle scaling or the strongest rho reference. The capacity gain is a meaningful index-calculus baseline improvement under local measurement, while the remaining rho gap is substantial. [pcc:unverified]

Rho comparison CSV SHA-256: `a5614cd513d2a72e6189397f438f8dbed24e71e36a94a2d8503511dbd05da979`.
