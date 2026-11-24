# Delayed canonical reduction for M31 dot products

Both NEON kernels load packed canonical 32-bit words, form four unsigned widening products per 64-bit lane and sum those products. The control folds each lane twice at bit 31 and conditionally subtracts the modulus. The alternative folds each lane once and carries that representative forward. Both kernels sum both lanes, reduce the horizontal result modulo the prime, and handle any trailing words identically. The comparison isolates the intermediate reduction in this standalone implementation.

DotBlocks.lean verifies that four canonical products fit in 64 bits, that a single fold preserves the residue, and that the folded value is below five times 2^31. For lists of up to 2^30 four-product lane blocks, it proves that the sum of folded words fits in 64 bits and reduces to the same value as the full sum. The bound counts both lanes together. All timed lengths fit this condition.

Build dot-blocks.cpp with Apple Clang 21.0.0 using -std=c++17 -O3 -mcpu=native. Run the binary separately with seeds 51 through 55 on an Apple M4 Pro. Every length uses 4096 independent rows, including a maximal-input row and a zero row. Both arms receive identical operands. Row generation and scalar unsigned 128-bit oracle evaluation occur before timing. Method order alternates across rounds. Every output is compared after each traversal. Exclude four warmups and retain twelve rounds per method and seed. Seed 56 also passed a separate AddressSanitizer and UndefinedBehaviorSanitizer build. The raw CSV includes every measured round.

| Terms | Minimum and maximum canonical/partial ratio across five process medians |
|---:|---:|
| 8 | 0.992–1.006 |
| 17 | 1.123–1.201 |
| 32 | 1.246–1.352 |
| 64 | 1.282–1.410 |
| 128 | 1.028–1.299 |
| 257 | 1.209–1.237 |

The experiment measures traversal throughput on preallocated public operand rows. The archived native x86 implementation uses wider storage for its words. Conversion, dispatch, real operand distributions, and whole-program performance remain outside the measurement.

## Operand layout and narrowing cost

The wide-input build stores each canonical field element in a uint64_t and narrows adjacent inputs inside the timed kernel. Output stays uint32_t throughout. Both NEON arms use the same loads. The narrow_exact theorem verifies lossless truncation for canonical 64-bit words, and tail_fits covers a scalar product added to a reduced accumulator.

Seeds 61–66 compare default packed inputs with -DM31_WIDE_INPUT in separate processes. Each paired seed generates identical numeric operands for both layouts. Packed runs first on odd seeds and wide runs first on even seeds. Each cell uses four warmups and twelve measured traversals. The table shows the median across seeds of the within-seed canonical/partial time ratio.

| Terms | Packed inputs | Wide inputs |
|---:|---:|---:|
| 8 | 1.003 | 1.141 |
| 17 | 1.200 | 1.102 |
| 32 | 1.253 | 1.245 |
| 64 | 1.375 | 1.037 |
| 128 | 1.289 | 1.168 |
| 257 | 1.223 | 1.128 |

At 64 terms the wide within-seed ratios ranged from 1.026 to 1.089. Layout changes both the input traffic and the instructions feeding the multipliers. This experiment measures their combined effect.

A second wide-input panel adds -DM31_NATIVE_PRODUCT. Its third arm multiplies the original uint64_t inputs in C++, letting the compiler choose instructions, and folds every four products once. Seeds 71–76 use six warmups and eighteen measured traversals per arm with rotating order. At 64 terms the medians across processes were 11.90 ns/dot for canonical NEON, 11.36 for partial NEON and 16.15 for the compiler-selected products. The third arm lost to partial NEON in every seed and length. All timed outputs passed the same independent reference. Seed 77 passed AddressSanitizer and UndefinedBehaviorSanitizer for the three-arm build. dot-layout.csv retains both panels. These measurements are local ARM throughput.

## Paying for conversion from wide input

dot-conversion.cpp compares narrowing on each load with copying both full 64-bit operand arrays into 32-bit scratch before traversal. Both arms call the same partially reduced NEON kernel. Every timed packed traversal copies both arrays afresh. Scratch allocation, fixture generation and reference computation are outside the timer. The scratch buffers require eight bytes per pair of input words (2 MiB at 64 terms and 4096 rows). The wide arrays remain resident. These are warmed processes on the M4 Pro.

Each pass pairs row r of A with row (r + 37k) modulo 4096 of B for pass index k. Thus each operand row is reused once per pass with a different partner. A scalar 128-bit oracle checks every dot after each traversal. The Lean theorem packed_dot proves entrywise narrowing preserves the dot product for any two canonical rows of equal length. Compile dot-conversion.cpp with the same flags as the original benchmark. Seeds 81 through 86 use the default reuse counts. For fresh seeds 91 through 96 pass refine after the seed. Both panels alternate arm order, discard four warmups and retain eight measured rounds per arm and condition. Seed 97 passed the refine panel under AddressSanitizer and UndefinedBehaviorSanitizer. dot-conversion.csv contains the raw observations.

| Terms | Last tested reuse count where wide won in all six fresh seeds | First tested reuse count where packing won in all six | Median wide/packed ratio at that first win |
|---:|---:|---:|---:|
| 17 | 8 | 14 | 1.032 |
| 64 | 2 | 3 | 1.058 |
| 128 | 3 | 4 | 1.066 |

At 17 terms, packing won in three of six seeds at ten uses and five of six at twelve uses. At 64 terms in the initial panel, one use cost median 11.13 ns/dot wide and 18.56 ns/dot with packing, while sixteen uses cost 9.38 and 5.87 ns/dot respectively. Actual caller reuse, allocation of new scratch, and host memory behavior can shift these crossovers.

## Archived collector dispatch

At revision 9a1d8a6cf4158197c06b0782f833d4626931ebff the benchmark driver's run_one selects chain_batch for v2_batch and supplies five argv entries. In native_v2.cpp this selects auxiliary for the main loop and leaves the optional validation branch disabled. Both call sites of dot are inside explicitBase. Consequently the recorded source and invocation imply zero calls to dot for seeds 0, 1 and 2. Changing only the arithmetic inside that helper saves zero executed dot-product operations in these runs. The packing crossover applies to workloads that actually evaluate these dot products.

All three audited records give source_sha256 equal to the native_v2.cpp digest 52c20890f4c920742e339c5c66e04b76b819604d913160ee8b63967e6e0aa341. The driver computes this digest from source bytes and can reuse an executable based on modification time. The pinned optimized snapshot omits native31. This audit establishes source-level reachability. Executable identity and historical hardware counters remain unverified.
