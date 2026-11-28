# Dual-projection x bitmap on the frozen public M31 collector

The first screen and separate confirmation each compared the 512 KiB direct-high bitmap control with the candidate high-and-low bitmaps (1 MiB total). Both use the same 6 MiB sign-packed exact index and explicit three-point Rust collector. The full sorted point-key/first-payload maps were byte-identical on each basis, with SHA-256 `ce7dab41355b3b236be455dbeaf9c46aaac83d29b272de5db727f54676407879` (auxiliary) and `8b55e48edff4cbc66ac73ba30bc601ade0e7ae03fbf5439aaaaf2d807ec0d6fa` (plain). All 144 fresh-process arms completed. Within every matched block, basis digest, entry count, trial count, relation count and generator-verified public answer `123456789` agreed. No arm failed or was censored. The two bases use the same public target.

| Panel | Basis | High wall median ms | Dual wall median ms | Paired high/dual wall | Dual wall wins | High CPU median ms | Dual CPU median ms | Paired CPU | Dual CPU wins |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Screen, 12 pairs | Auxiliary | 58.691 | 52.960 | 1.1074 | 12/12 | 58.041 | 52.447 | 1.1112 | 12/12 |
| Screen, 12 pairs | Plain | 47.534 | 42.187 | 1.1203 | 12/12 | 46.745 | 41.611 | 1.1244 | 12/12 |
| Confirmation, 24 pairs | Auxiliary | 59.598 | 53.217 | 1.1225 | 24/24 | 58.926 | 52.327 | 1.1272 | 24/24 |
| Confirmation, 24 pairs | Plain | 48.210 | 42.525 | 1.1333 | 24/24 | 47.730 | 41.856 | 1.1366 | 24/24 |

The candidate's table construction was slower: confirmation medians were 7.435 to 7.709 ms on auxiliary and 7.527 to 7.646 ms on plain. The net gain came in the subsequent collector. Ratios are medians of matched ratios, not ratios of displayed arm medians. Wall and parent-plus-child CPU clocks ran from before basis regeneration to after process exit and answer parsing, charging basis generation, input writing, bitmap and table setup, relation collection, elimination and generator verification. Compilation and frozen JSON loading preceded the clock; OS caches were not flushed. Source and run records are `main.rs`, `replay.py`, `raw.csv` and `confirm.csv`.

`DualBitmap.lean` kernel-checks that marking both projections for every inserted x and rejecting a candidate only when either bit is absent preserves the first successful exact-index payload, assuming the support invariant. It does not verify Rust memory operations, compiler output or elapsed time. The Rust audit checked every occupied x against both bitmaps and compared the complete exact-index maps. This is a constant-factor local improvement in the standalone explicit-pair collector, not an asymptotic result or a library `PreparedSolver` result.

**Standing of the first two panels:** exploratory producer evidence [pcc:unverified]. The two protocols were committed before their respective timing runs, but the repository's newer `experiment-seeds/v1` policy also requires a complete seed manifest, PR publication before held-out measurement, and stronger isolation/independent verification for a qualified speed claim. Those conditions were not all met. The 0/1/2 walk seeds are deliberate repeated inputs, not independent target instances; the two bases share one target.

Environment: Apple M4 Pro, Rust 1.93.1, Python 3.13.1, Lean 4.36.0; single fresh Rust process per arm. Source SHA-256: `main.rs` `28dedfe7648e36e04b6eee198677f79d361cfc3967af48df9137ae552b6b3605`; initial `replay.py` `071a52dabadfa0fb229da7c31e3d3b5817f5611a2fc8bb1ebfe3db1486fb36af`. Raw CSV SHA-256: `raw.csv` `b9212bcb03aa36d83d5a56d9e1160e523c7d1967d40b2d87b15d4741b211e5e1`; `confirm.csv` `0060fd5eee5af796d2b5e566c63340821d9be00d8826823cf51bc2f3128dee1b`.

## Manifest-frozen validation

The validation protocol and `SEEDS.json` were committed and published on PR #2014 before this panel. The manifest SHA-256 is `bd7c6f0d5348639ff68425df2e77d48e914e9cd5eb4b7c40490cf1f14647b630`. It derives three new walk seeds (`3576555053178744226`, `1007646413420971989`, `6034286023384815533`) and schedule seed `5209552740903009770` from a fixed 128-bit master with domain-separated SHA-256. Both arms use the same seed in each block; eight repeats per seed measure timing noise. All 96 fresh-process arms completed; all 48 matched blocks agreed on basis SHA-256, exact table entries, trials, relations and generator-verified answer. Both exact payload-map audits again matched the digests above. No arm failed or was censored.

| Basis | High wall median ms | Dual wall median ms | Paired high/dual wall | Dual wall wins | High CPU median ms | Dual CPU median ms | Paired CPU | Dual CPU wins |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Auxiliary | 61.297 | 54.571 | 1.1246 | 24/24 | 60.460 | 53.936 | 1.1241 | 24/24 |
| Plain | 51.309 | 45.040 | 1.1407 | 24/24 | 50.718 | 44.320 | 1.1455 | 24/24 |

The candidate's median table build again increased, from 7.623 to 7.972 ms on auxiliary and 7.548 to 7.839 ms on plain. The same-target, charged full-collector gain therefore came after setup and exceeded the prespecified local gate. The validation panel still covers one public target on one host with repeated seeds, without CPU isolation, independent signed performance verification, or a matched rho arm. It supports a local implementation improvement under this protocol [pcc:unverified], not a general algorithmic breakthrough.

Validation `replay.py` SHA-256: `44e94b2d361a2a62579d3749e785af758887789e35c3f2aac78893a0c42b8ce9`. `validation.csv` SHA-256: `2e2f5a61d231c86257a84823028695d427b839822919f998ee0ac3bcc5de8e3d`. The replay command is in `VALIDATION_PROTOCOL.md`.
