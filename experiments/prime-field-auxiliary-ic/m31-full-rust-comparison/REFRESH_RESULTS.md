# Refreshed cold flat versus reflected Rust collector panel

This is a repeat of the full Rust comparison on the same frozen public M31 auxiliary and plain fixtures. Each arm regenerates and checks its 500-point factor base, writes the public input, starts a fresh Rust process, builds the flat index, collects relations, eliminates them, verifies the answer by generator multiplication, parses the result, and waits for process exit. The charged wall clock and parent-plus-child CPU window start before basis generation. Compilation, loading frozen JSON, and OS cache flushing are outside the timer; cache state was not controlled. Both arms use the same contiguous flat hash table and collector; only pair-row construction changes. The direct arm computes all rows, while the reflected arm reconstructs odd rows from negated even-row sums.

The first panel uses block shuffle seed 112527 and the confirmation seed 112539. Each has 24 matched blocks per basis: seeds 0, 1, 2, eight balanced arm-order rounds each. All 96 matched pairs across both panels have identical basis SHA-256, signed table entries, trial count, relation count, and scalar `123456789`; both arms verify this scalar against the public generator and target. No arms failed or were censored. The raw CSVs are `refresh-raw.csv` and `refresh-confirm.csv`.

| Panel | Basis | Flat wall median ms | Reflected wall median ms | Median paired flat/reflected wall ratio | Reflected wall wins | Flat CPU median ms | Reflected CPU median ms | Median paired CPU ratio | Reflected CPU wins |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| First | Auxiliary | 300.625 | 333.161 | 0.9405 | 11/24 | 222.579 | 235.231 | 0.9724 | 8/24 |
| First | Plain | 269.115 | 265.885 | 0.9153 | 8/24 | 202.538 | 210.340 | 0.9485 | 7/24 |
| Confirm | Auxiliary | 240.942 | 249.290 | 0.9542 | 9/24 | 213.498 | 216.552 | 0.9761 | 8/24 |
| Confirm | Plain | 215.989 | 212.517 | 1.0268 | 14/24 | 192.026 | 185.966 | 1.0197 | 15/24 |

The first panel's host was substantially slower in wall time than the confirmation panel, while CPU medians moved less. Ratios are medians of paired ratios and need not equal ratios of the displayed arm medians. Table-build-only median paired ratios were 0.9419/1.0801 in the first panel and 1.0226/1.1221 in confirmation (auxiliary/plain). Since table construction is a small fraction of the complete run and the plain whole-run sign changed between panels, this does not establish a cold end-to-end reflected-row speedup. The earlier `raw.csv` panel also remains available; it was near parity and should not be pooled without a prespecified analysis.

Source at measurement: `field.rs` SHA-256 `a7ed21f1a3cd689cf12b1732dec53f2e4397f2d0dda4521b3f7a55902df7f7a2`, `main.rs` SHA-256 `ee3234f7badb0b578e759dcea0eaad13d60a563f18d02ae816ecaf41dc6d4fa2`. The runner copies current `field.rs` into an isolated archive build so the standalone collector and arithmetic API match. The final runner additionally accepts an order seed from the environment; timing logic is unchanged. Raw CSV SHA-256 values are `e3c537724d93d53caa48d792477ab47c3e368a2f9ee85688eef91fb9147cf433` and `6ad3d37204041361273d1e24577760fdebb7ffe5f5c591689ae5a27fbb333cee`.

These are local producer measurements on a shared Apple M4 Pro host. The checked fixture answers and matched workload counts establish deterministic equivalence for these runs; they do not validate broad performance claims or native x86/GPU behavior. [pcc:unverified]
