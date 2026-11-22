# M31 field inversion through a C ABI

Include m31.h and call `m31_batch_inverse(input, output, count)`. The function accepts any uint32_t encoding, reduces each input modulo 2³¹−1 and writes a canonical uint32_t residue. An input congruent to zero produces zero. Inputs and outputs may be the same array or disjoint arrays. A zero count accepts two null pointers. Callers supply their own output buffer. The implementation uses stack storage bounded independently of count and has no mutable global state.

The C++17 implementation uses 64-element product trees and an exact-length tree for the final partial block. The parent rule in the sibling m31-inverse-arithmetic/Tree.lean proof covers arbitrary binary tree shapes. Fold.lean checks the Mersenne multiplication reduction and intermediate bounds for canonical inputs. These mathematical proofs accompany tests of the compiled C ABI.

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
