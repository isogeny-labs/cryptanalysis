# Local Metal inversion over the M31 prime field

This experiment compares the sibling CPU product-tree implementation with two GPU kernels on identical arrays of unsigned 32-bit words. Every output is reduced modulo 2³¹−1 and represents the inverse, with zero mapped to zero. The first shader inverts each word independently. The second shader processes up to eight words per GPU thread, sharing one inversion across those words. The buffers are distinct and use shared Metal storage.

On a shared Apple M4 Pro, the eight-word shader reached a median paired 17.37× speedup over one CPU thread at 1,048,576 words, including encoding, dispatch and waiting for completion. The descriptive 95% block-bootstrap interval was [15.41, 19.03]. Median CPU wall time was 3.627 ms, batch GPU wall time 0.211 ms, and batch command-buffer device time 0.043 ms. At 65,536 words the paired speedup was 1.95×. At 8,192 words the CPU took 32 μs and the batch GPU path took 137 μs. These timings apply to a warmed pipeline with preallocated shared buffers. The observed initial device, pipeline, queue and buffer setup took 0.365 s in this process.

The driver checks every CPU and GPU output by independent 64-bit modular multiplication and enforces canonical output. Inputs include the two nonzero uint32 multiples of the modulus and the upper uint32 boundary. The 262,147-word case exercises a partial group. After an untimed warm-up, 18 rounds rotate array size and balance all six method orders. The panel checks 78,975,723 output words including warm-up. rows.csv columns are round, word count, method (0 CPU, 1 GPU individual, 2 GPU batch), wall seconds, and device seconds (zero for CPU). Validation and input generation are outside the clocks. Device times come from Metal command-buffer timestamps.

From this directory on macOS with the Metal and Foundation frameworks:

```sh
clang++ -O3 -std=c++17 -fobjc-arc panel.mm ../m31-field-ffi/m31.cpp \
  -framework Foundation -framework Metal -o panel
./panel
python3 analyze.py
```

The driver reads inverse.metal at runtime. analyze.py summarizes the archived rows with NumPy. Check SplitWord.lean in a Lean 4.28 Mathlib environment. It proves the arithmetic high-word reconstruction, low-word reduction and intermediate word bounds. The sibling Tree.lean and Fold.lean cover the field product identity and Mersenne reduction. Shader compilation, memory addressing and driver execution are validated by the measured run.
