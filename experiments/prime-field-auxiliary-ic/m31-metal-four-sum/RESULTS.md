# Metal affine candidate admission, preliminary

**Correction, 2026-11-27:** The earlier `admission.swift` and `verify.rs` runs in `RAW.jsonl` and `RAW_WALK.jsonl` evaluated `target + signed entry`; the production `PairIndex` evaluates `target − signed entry`. Those internally consistent digests, flag counts and timings below do not establish equivalence to the collector. Their raw records remain preserved. The corrected sign mapping was checked against the production Rust first-witness probe on the first 64-lane walk round: all 64 results matched, with 21 hits; the ordinary probe took 36.074 ms and the GPU-mask-assisted Rust probe 7.060 ms, excluding the GPU screen and setup. A first full-process same-Q admission produced identical certificates and scalar 264620306, with 355.555 ms CPU-path internal wall and 239.259 ms Metal-path internal wall including 102.982 ms shader initialization. These are single diagnostic runs, not the frozen confirmation. The new `CONFIRM_PROTOCOL.md` governs the fresh panel. [pcc:unverified]

Status: correctness admission passed for the checked public B195 signed-pair construction; end-to-end admission remains open. These are producer-run local measurements, not an independent speedup claim. [pcc:unverified]

`admission.swift` builds the first 195 liftable x-coordinates on the public M31 curve, enumerates the same i<=j, plus/minus pair rule as `PairIndex`, canonicalizes by y, and creates 38,025 distinct pair entries. It evaluates `Q ± entry` for 1, 8 and 64 lanes, replacing the first four rows with vertical, tangent, left-identity and right-identity cases. All GPU outputs equalled the Swift affine reference point by point. An independent Rust `Curve<31>` run produced matching ordered x/y FNV digests for each size. The Rust digest comparison is a strong replay check, not a formal proof of identical implementation semantics.

| Lanes | Candidates | GPU compile, buffer, dispatch, wait | GPU dispatch and wait | Swift affine | Mismatches | Rust/Swift digest |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 76,050 | 5.168 ms | 2.962 ms | 6.562 ms | 0 | 8369032597423072703 |
| 8 | 608,400 | 8.530 ms | 5.000 ms | 55.339 ms | 0 | 12732938990286056998 |
| 64 | 4,867,200 | 39.941 ms | 18.818 ms | 452.207 ms | 0 | 429071123967448180 |

The independent Rust solver control on the same public Q with interval B195, m4, seed 2911332506172719186, lanes 64 and chunk 16384 reported 608 queries, 192 relations, 332.799 ms decomposition, 334.385 ms online and 0.853 ms pair-index construction. Its replayed answer was 264620306. This implies about 0.55 ms decomposition per walk query and about 33 ms per 64-lane round, but per-query and per-round numbers are derived from one run and are not a matched GPU end-to-end comparison. The GPU 64-lane admission did 40 ms of charged GPU setup and work on 64 distinct, constructed public points; the native control uses its actual dependent walk points and can exit early. The tested GPU path therefore has not cleared the 1.15× native component gate. [pcc:unverified]

The first modular-multiply microbenchmark is superseded as a cost predictor: point inversion, buffers, and dispatch materially change the result. A Lean theorem about timing would have no bearing on this result.

## Compact bitmap path, subsequent admission

The added `compact_screen` kernel holds the 38,025 pair entries and 64 targets as compact input arrays on the device. It derives candidate signs by index and returns one byte per candidate after the exact same 20-bit bitmap check used by `PairIndex`. It no longer transfers 4.87 million affine outputs to the host. On the same constructed public lane targets, all 4,867,200 bitmap flags matched the full point-output kernel and Swift's reference screen; 174,097 were bitmap-positive. Nine fresh-process 64-lane runs charged a median 5.164 ms from compact pipeline creation through buffer creation, dispatch and wait, with a wide 4.346–20.295 ms range. A one-lane run charged 0.751 ms. The full raw observations are in `RAW.jsonl`. These are exploratory local measurements with visible host/GPU contention; the reported median is descriptive, not a frozen performance claim. [pcc:unverified]

This changes the next experiment: a 64-lane batch can amortize dispatch and might beat the native collector's roughly 33 ms per round. The current Rust search invokes `PairIndex::decompose` one target at a time, so integration requires a batched lane-round interface and exact first-witness replay. The compact timing excludes construction of the basis and pair entries, target-walk generation, host scanning of bitmap positives, relation collection, elimination, and cold process startup. It is not a full-solve speedup or a passed Stage C gate.

## Exact first walk round

`walk.rs` reproduces the Rust solver's SplitMix64 jump table, initial 64 lane points and first lane round from the public Q and frozen seed. `FIRST_ROUND.csv` contains the resulting public coordinates. On these 64 points, Metal, Swift affine arithmetic and Rust `Curve<31>` again agreed: 4,867,200 candidates, 172,755 bitmap positives, zero point and flag mismatches, ordered digest 18400854821465442306. Five fresh-process compact screens charged 4.646, 4.681, 4.680, 11.582 and 4.761 ms (median 4.681 ms). See `RAW_WALK.jsonl`. The walk reproduction is source-matched but has not yet been independently compared to an instrumented `m31-fast` trace. [pcc:unverified]

The next discriminating check is to instrument the actual Rust 64-lane query stream, transfer only bitmap-positive indices back from Metal, and replay the first exact witnesses in pair-index order. This must preserve relations, equation checks, rank and final scalar across all rounds. Then the charged cold same-target end-to-end comparison can decide whether the 64-lane component gain survives integration.

A scalar lane-batch interface was added to the Rust solver as a correctness control. `batch_control.rs` compares the ordinary indexed path against that adapter on the same public Q, seed, B195 index and 64-lane walk. The complete `MultiSolveOutcome` objects, including certificate relations and work counts, were equal: scalar 264620306, 608 queries, 192 relations, rank 191. This preceded the GPU integration below. [pcc:unverified]

## Frozen 15-block full Rust panel

The full Metal backend in `gpu_ffi.swift` and `screen.metal` now receives the pair points and bitmap from the Rust index. `solve_multi_indexed_screened` applies its lane flags to Rust's exact point lookup, first-witness selection, row replay, elimination and full certificate verification. The executable `full.rs` separately verifies the answer by public generator multiplication. The frozen source is commit `e93837b8b`; the seed, target, order and accounting plan is in `CONFIRM_PROTOCOL.md`. All 30 fresh-process arms completed correctly across five public targets and three independent seeds. The independent affine implementation in `independent_check.py` checked all 30 scalar answers; paired relation digests, scalar, queries, relation count and rank matched in all 15 blocks. [pcc:unverified]

| Metric | CPU | Metal |
| --- | ---: | ---: |
| Median process wall across 15 arms | 341.831 ms | 221.755 ms |
| Median child user+system CPU across 15 arms | 308.889 ms | 118.475 ms |
| Median paired CPU/Metal wall ratio | \- | 1.486× |
| Median paired CPU/Metal CPU ratio | \- | 2.623× |
| Paired wins, wall / CPU | \- | 15/15 / 15/15 |

Per-target median paired wall ratios for Q0–Q4 were 1.593, 1.371, 1.419, 1.524 and 1.575; CPU ratios were 2.702, 2.056, 2.620, 2.623 and 2.628. The process wall charge starts before each fresh Rust launch and includes basis generation, pair index, Metal shader loading and compilation, all GPU calls, collection, elimination, certificate replay and exit. Child CPU includes the Swift/Metal host process, while GPU device time contributes to wall rather than child CPU. These are producer-run local observations on a shared Apple M4 Pro host, with no cache flushing. All raw records, manifest and paired ratios are preserved. [pcc:unverified]

**Audit limitation:** `full.rs` labels a digest as `certificate_digest`, but its current hash covers relation coefficients and signed terms only; it omits certificate weights and metadata. The internal Rust verifier checked each complete certificate, and the independent Python checker verified each scalar, but the panel does not establish byte-identical complete certificates across arms. The frozen protocol required exact certificate-digest agreement, so this first panel cannot by itself clear that requirement. A new frozen confirmation must include a full-certificate digest before promoting the result. The earlier Stage B and pre-orientation figures above remain historical diagnostics; the corrected full panel is the relevant performance comparison. [pcc:unverified]

Reproduce locally on Apple Metal: `swiftc -O admission.swift -o /tmp/m31-metal-admission`, run it with `195 1`, `195 8` and `195 64`; compile `verify.rs` against the current `prime_field_auxiliary_ic` rlib and compare `digest`. The repository control is `m31-fast --qx 1767503692 --qy 244402461 --seed 2911332506172719186 --columns 195 --summands 4 --method indexed --base interval --lanes 64 --chunk 16384 --max-queries 100000 --max-ms 5000 --profile`.
