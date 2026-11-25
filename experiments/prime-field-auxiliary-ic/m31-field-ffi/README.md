# M31 field inversion through a C ABI

Include m31.h and call `m31_batch_inverse(input, output, count)`. The function accepts any uint32_t encoding, reduces each input modulo 2³¹−1 and writes a canonical uint32_t residue. An input congruent to zero produces zero. Inputs and outputs may be the same array or disjoint arrays. A zero count accepts two null pointers. Callers supply their own output buffer. The implementation uses stack storage bounded independently of count and has no mutable global state.

The portable C++17 path uses 64-element product trees and an exact-length tree for the final partial block. The parent rule in the sibling m31-inverse-arithmetic/Tree.lean proof covers arbitrary binary tree shapes. Fold.lean checks the Mersenne multiplication reduction and intermediate bounds for canonical inputs. These mathematical proofs accompany tests of the compiled C ABI.

## Build and replay

From this directory, on the measured macOS machine:

```sh
clang++ -std=c++17 -O3 -shared -fPIC m31.cpp -o libm31.so
python3 check.py ./libm31.so
clang -std=c11 -O3 client.c ./libm31.so -o client
./client
```

The ctypes check compares 93,440 outputs with Python's modular exponentiation, including every length through 256, larger boundary cases, noncanonical words, zero residues, in-place calls and disjoint calls. Sentinel words surround both buffers. The C client calls the dynamic library from a separate C translation unit and independently checks all outputs by modular multiplication. Build with assertions enabled. Check Fold.lean from a Lean 4.28 project with Mathlib via `lake env lean /absolute/path/to/Fold.lean`.

## Observed local throughput

The shared Apple M4 Pro panel used 65,536 words per pass, eight passes per measurement, and 16 rounds of rotated call-size order. Median ns per input were 85.638 for single-word calls, 10.963 at 17 words, 9.139 at 20, 4.585 at 63, 3.151 at 64, 3.711 at 65, 3.026 at 1,024 and 3.004 at 65,536. timings.csv records round, words per call and ns per input. Timings include the native shared-library call boundary. The ctypes exercise checks correctness only. Collector timing and GPU performance are outside this panel.

## Elementwise multiplication

`m31_batch_multiply(left, right, output, count)` computes one canonical product per element for arbitrary unsigned 32-bit inputs. Each pair of buffers may be identical or disjoint. A zero count accepts null pointers. ARM64 builds with NEON use four independent lanes and a scalar tail. The portable build uses the same C ABI.

To replay the multiplication checks and paired Python ctypes timings on the measured Apple M4 Pro:

```sh
clang++ -std=c++17 -O3 -mcpu=native -shared -fPIC m31.cpp -o native.so
clang++ -std=c++17 -O3 -mcpu=native -DM31_PORTABLE_MULTIPLY -shared -fPIC m31.cpp -o portable.so
python3 check_multiply.py ./portable.so ./native.so
```

The two warm-up rounds precede 24 measured rounds with alternating call order. Each timing covers repeated calls on the same buffers. The check includes exact aliasing, boundary residues, full-width inputs, tails and guard words. Replay Lane.lean in the same Lean environment as Fold.lean to check the arithmetic model.

## Four-lane batch inversion

On ARM64 with NEON, each full 1,024-word block uses four 256-leaf product trees. A remainder of 512–1,023 words uses one partial wide block. Smaller batches use a 256-word block with four 64-leaf trees when it fits. The largest tree and mask arrays occupy 12 KiB of stack. A vector lane owns one tree throughout the upward and downward passes. The final small remainder uses four exact-length trees if it contains at least 65 inputs or is a positive multiple of four. Other remainders and portable builds use the scalar tree. A partial vector is padded with ones and only live lanes are written. Both paths use the same tree and root-inversion code. Zero masks are saved before writing output, including for in-place calls.

From the builds above, run `python3 time_inverse.py ./portable.so ./native.so` to reproduce the paired ctypes benchmark. The original 64-leaf ARM64 measurements (portable time divided by native time) were 1.84× at 256 words, 2.69× at 4,096 and 2.81× at 65,539. The earlier standalone C-client observations above describe the original scalar inversion implementation. The paired raw observations for this version are in inverse-neon-timings.csv.

The wide-tree comparison in `inverse-wide-timings.csv` uses the previous NEON implementation as the control (commit `c414fb141`). On the Apple M4 Pro, paired median ctypes speedups were 1.51× at 1,000 words and 1.69× at 4,096 words. To replay from this directory:

```sh
git show c414fb141:experiments/prime-field-auxiliary-ic/m31-field-ffi/m31.cpp | clang++ -x c++ -std=c++17 -O3 -mcpu=native -shared -fPIC -I. - -o control.so
clang++ -std=c++17 -O3 -mcpu=native -shared -fPIC m31.cpp -o native.so
python3 time_inverse.py ./control.so ./native.so
```

## ARM64 reciprocal correction table for public inputs

Build with `-DM31_PUBLIC_COSET_INVERSE` to use the 256-byte table in the ARM64
batch-inverse implementation. This path uses input-dependent table addresses.
Three cyclic Hamming distances select the correction in each lane.
CosetInverse.lean verifies the table over the entire 2,046-element projection
image and proves the inverse formula for nonzero field elements.

```sh
clang++ -O3 -std=c++17 -mcpu=native -DM31_PUBLIC_COSET_INVERSE -shared -fPIC m31.cpp -o public-coset.so
python3 check.py ./public-coset.so
```
