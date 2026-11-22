# Native checked square roots on M31

The kernel takes 4096 canonical field elements and emits the smaller square root or p as a failure sentinel. Each input needs 29 field squarings for the candidate and one to verify it. Arm 0 uses scalar C++ with compiler optimizations enabled. Arm 1 uses four NEON lanes with widening products and narrowing shifts. Arm 2 combines the low word multiply with SQDMULH to obtain bits 31 and above of the square directly in each of four lanes.

For 0 ≤ x < p, the doubled square fits in a signed 64-bit integer. The signed high word of that doubled square therefore equals floor(x²/2³¹). HighSquare.lean checks both statements. The reduction is the one-fold formula in ../m31-field-ffi/Fold.lean. The root criterion is proved in ../m31-root-cache/Root.lean on the companion PR #1889. The mathematical proofs concern the arithmetic identities. The executable is tested separately.

Build with Apple clang 21.0.0 using clang++ -O3 -std=c++17 -mcpu=native -Wall -Wextra -Werror bench.cpp -o bench. Run the binary to emit a CSV. Disassembly on the Apple M4 Pro showed sqdmulh.4s in arm 2. Each process generated 36 blocks of 4096 inputs. Every block included zero, one, p−1 and p−2. Before timing and after each timed arm, all outputs were checked against a separate modular exponentiation with integer remainder. Each timed arm reused its block 64 times. Each of the six arm orders occurred six times per process.

| Process | Scalar ns/element | Widening NEON ns/element | High multiply ns/element | Median paired widening/high | Median paired scalar/high |
|---|---:|---:|---:|---:|---:|
| First | 33.556 | 16.894 | 11.008 | 1.534 | 2.816 |
| Repeat | 40.904 | 23.163 | 14.903 | 1.519 | 2.756 |

Times are block medians on one shared host. The repeat used the same input seed and a new process. High multiply beat widening in 35/36 and 34/36 blocks respectively. These measurements cover bulk arithmetic on resident input and output buffers. Coordinate generation, point-list selection and collection were outside the measurement.
