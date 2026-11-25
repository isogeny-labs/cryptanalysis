# Direct original versus bitmap-combined Rust collector

The direct comparison followed `BLOOM_DIRECT_PROTOCOL.md`, frozen before timing. The original arm uses checked batch arithmetic, an 8 MiB flat point-key index and SplitMix-style slot hash. The candidate combines validated shared-x paired arithmetic, a 6 MiB sign-packed index, one-multiply hash and a 128 KiB x bitmap prefilter. Both compute direct pair rows and use the same deterministic relation walk, checked relation equations, modular elimination and generator-multiplication answer verification.

The audit reconstructed both frozen public 500-point M31 bases and compared the *complete sorted key/first-payload maps*, byte for byte, between arms. Auxiliary SHA-256 was `ce7dab41355b3b236be455dbeaf9c46aaac83d29b272de5db727f54676407879`; plain was `8b55e48edff4cbc66ac73ba30bc601ade0e7ae03fbf5439aaaaf2d807ec0d6fa`. Every one of 96 matched pairs across two panels had the same basis digest, signed entry count, trial count, relation count and verified scalar `123456789`. No arms failed or were censored.

| Panel | Basis | Original wall median ms | Candidate wall median ms | Median paired original/candidate wall ratio | Candidate wall wins | Original CPU median ms | Candidate CPU median ms | Median paired CPU ratio | Candidate CPU wins |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| First | Auxiliary | 244.862 | 145.872 | 1.6873 | 23/24 | 232.049 | 135.319 | 1.6673 | 24/24 |
| First | Plain | 233.822 | 144.090 | 1.7009 | 24/24 | 215.639 | 129.190 | 1.7253 | 24/24 |
| Confirm | Auxiliary | 259.404 | 152.697 | 1.8132 | 23/24 | 237.388 | 139.196 | 1.7351 | 24/24 |
| Confirm | Plain | 222.159 | 133.078 | 1.6788 | 24/24 | 210.029 | 120.242 | 1.6600 | 24/24 |

These ratios are measured *directly* from paired runs, not products of component ratios. The charged wall and parent-plus-child CPU windows start before basis regeneration and end after fresh Rust process exit, charging table build, relation collection, elimination and answer verification. Compilation, frozen JSON loading and complete index-map audit precede the timer. OS caches were not flushed. Ratios are medians of paired ratios and need not equal ratios of arm medians.

`Bloom.lean` proves the logical no-false-negative marking invariant and first-payload preservation under explicit exact-index support. An audit-only replay after the panels additionally asserted that each occupied Rust x slot has its bitmap bit set; this audit addition is outside the measured hot path. Local Rust arithmetic tests and the complete map and workload checks cover the frozen fixtures. The standalone Rust collector reproduces the archived explicit-pair method; the library `PreparedSolver` uses a separate circuit path.

The result is a substantial local same-target constant-factor improvement for these two frozen public fixtures on a shared Apple M4 Pro. It does not establish improved asymptotic complexity, performance on other targets or hosts, or independent performance replay. [pcc:unverified]

The bitmap mechanism has prior art in binary-field index-calculus lookup
tables; this is a measurement of its particular placement in the M31
paired-chord collector. See `BLOOM_RESULTS.md` for the original sources checked.

Raw CSV SHA-256: first `20e0e24f64039dc53e0a7078ebf4dc6ce0eb9bf1b0444f05c855777d89137187`, confirmation `262d42961abf706a7a0cf49bd06fdc3e3f431e6825e2e7cea47c30a78605ecce`.
