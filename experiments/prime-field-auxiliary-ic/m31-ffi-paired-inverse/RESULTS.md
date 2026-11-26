# Native M31 batch inverse inside the Rust paired collector

The frozen comparison followed `PROTOCOL.md` on the public auxiliary and plain M31 fixtures. Both arms linked the same C++ static library and used the same Rust source; `M31_FFI_INV` selected the existing ARM64 NEON `m31_batch_inverse` for all 500 paired denominators per target-walk trial. The control retained the Rust four-lane Montgomery inverse path. The C ABI checker verified 1,097,730 outputs including zero and noncanonical inputs, aliasing and boundary lengths. An audit binary then checked `denominator × native_inverse = 1` for every nonzero paired denominator in full runs at seeds 0, 1 and 2 on both bases. Complete sorted exact-index maps matched byte for byte; auxiliary SHA-256 was `ce7dab41355b3b236be455dbeaf9c46aaac83d29b272de5db727f54676407879` and plain was `8b55e48edff4cbc66ac73ba30bc601ade0e7ae03fbf5439aaaaf2d807ec0d6fa`.

All 48 matched blocks had identical basis SHA-256, trials, target relation counts, index entries and generator-verified public scalar `123456789`; all 96 fresh-process arms completed without failure or censoring.

| Basis | Control wall median ms | FFI wall median ms | Median paired control/FFI wall | FFI wall wins | Control CPU median ms | FFI CPU median ms | Median paired CPU ratio | FFI CPU wins |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Auxiliary | 66.644 | 66.600 | 1.0020 | 14/24 | 65.644 | 65.641 | 1.0015 | 14/24 |
| Plain | 53.964 | 54.439 | 0.9882 | 9/24 | 52.852 | 53.387 | 0.9883 | 7/24 |

The charged clocks cover basis regeneration, input writing, table construction, relation collection, elimination, answer verification and process exit. Compilation, native ABI checks, fixture JSON loading and complete map audits preceded timing; OS caches were not flushed. Rust-internal paired medians were 1.0010 auxiliary and 0.9873 plain. The FFI path did not meet the protocol's both-bases gain rule, so no confirmation or promotion follows. Independent signed performance standing remains pending. [pcc:unverified]

Median Rust internal totals were about 51/47 ms (auxiliary/plain), whereas table build was about 8 ms and target elimination about 2–3 ms. This leaves the paired relation-collection loop as the dominant measured phase. The inverse replacement's near-parity result indicates that per-denominator inversion alone was not its limiting term; the next kernel candidate should fuse slope, x-coordinate and bitmap work and measure the complete pipeline. That is an inference from stage times, not a proof of a specific machine instruction bottleneck.

Existing `m31-field-ffi` Lean files prove arithmetic statements about the standalone native field operations; they do not prove Rust/C++ ABI refinement or runtime speed. No Lean timing theorem is asserted here. Raw CSV SHA-256: `f999c2020be39d005b743613e8f42d5edc513daba3cfc1856eb72a8d6302fd9f`.
