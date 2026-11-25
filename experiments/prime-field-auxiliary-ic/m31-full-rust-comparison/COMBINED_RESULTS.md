# Direct combined M31 full-collector comparison

The frozen protocol is in `COMBINED_PROTOCOL.md`. This compares two builds of
the same Rust source on the frozen public M31 auxiliary and plain fixtures.
The original arm uses the checked batch API, SplitMix-style hash and 8 MiB
flat point-key index. The combined arm uses the documented prevalidated batch
API, one-multiply hash and 6 MiB sign-packed index. Both use direct pair rows,
the same relation walk and modular elimination.

Two local panels each ran 24 balanced-order matched blocks per fixture on an
Apple M4 Pro with Rust 1.93.1. Every arm regenerated its 500-point basis in a
fresh process, collected checked three-point relations, eliminated them, and
verified scalar 123456789 by generator multiplication. All 96 matched pairs
agreed on basis digest, signed index entry count, trial count, relation count
and answer. Before each panel, the complete sorted `(point key, first payload)`
maps were byte-identical between arms on both bases. Their SHA-256 values were
`ce7dab41355b3b236be455dbeaf9c46aaac83d29b272de5db727f54676407879`
and `8b55e48edff4cbc66ac73ba30bc601ade0e7ae03fbf5439aaaaf2d807ec0d6fa`.
[pcc:unverified]

| Panel | Fixture | Original wall median ms | Combined wall median ms | Median paired original/combined wall ratio | Combined wins |
| --- | --- | ---: | ---: | ---: | ---: |
| Initial | Auxiliary | 182.610 | 139.165 | 1.2794 | 24/24 |
| Initial | Plain | 163.849 | 125.643 | 1.2887 | 24/24 |
| Repeat | Auxiliary | 184.053 | 143.943 | 1.2717 | 23/24 |
| Repeat | Plain | 164.766 | 128.822 | 1.3150 | 23/24 |

| Panel | Fixture | Original CPU median ms | Combined CPU median ms | Median paired original/combined CPU ratio | Combined wins |
| --- | --- | ---: | ---: | ---: | ---: |
| Initial | Auxiliary | 181.617 | 138.248 | 1.2800 | 24/24 |
| Initial | Plain | 162.855 | 124.750 | 1.2907 | 24/24 |
| Repeat | Auxiliary | 182.924 | 143.022 | 1.2723 | 24/24 |
| Repeat | Plain | 163.752 | 127.717 | 1.3192 | 24/24 |

The charged wall and parent-plus-child CPU clocks cover basis regeneration and
fixture comparison, input writing, index build, relation collection,
elimination, answer verification and process exit. Compilation, frozen JSON
loading and the exact-map audit precede timing. OS caches were not flushed.
The ratios use matched observations, not ratios of displayed arm medians.
`combined-raw.csv` and `combined-confirm.csv` retain all 192 arms. The runner
checks the exact map and every matched workload identity before it completes.

This is a direct, setup-charged local gain on the same frozen public target,
with no product-of-separate-ratios extrapolation. It does not establish an
asymptotic improvement or performance across other targets. The standalone
explicit-pair collector differs from the library `PreparedSolver` circuit
path. `SignPacked.lean` proves the sign-packed logical first-payload map for
any insertion stream; it does not prove the measured runtime or the Rust
prevalidated batch API contract. Independent replay remains pending.

Evidence SHA-256: runner
`adbf61cc44e4a243390edbdcbe2c727776e3bad14d2d9084bc299c76e7ad31d8`,
initial CSV `7ea8a16e19a5e8cd58cee075895f62959a038f5ca79f363b7efb34cd934c08b8`,
repeat CSV `8c059bf07096c2f1c034d3466c7f6a550bde6b19816c03a9d49b7d020c8fd9aa`.
