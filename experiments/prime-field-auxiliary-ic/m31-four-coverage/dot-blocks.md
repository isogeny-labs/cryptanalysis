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
