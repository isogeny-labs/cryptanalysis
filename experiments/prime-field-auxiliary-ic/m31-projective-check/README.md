# Inversion-free validation of the public M31 auxiliary chain

The complete public auxiliary basis took 1.80 ms to build in a direct comparison with the original 10.76–10.81 ms setup. Both produced all 500 ordered target-curve points from freshly generated auxiliary coordinates. The candidate uses the checked-root ABI and validates all 1,024 coordinates under ten rational maps. The measurement covers setup through the ordered Python list, including foreign calls, marshaling and the public point walk. Library loading, interpreter startup, file I/O and post-timing fixture comparison are outside the clock.

## Map and proof

For an input x represented as X/D, set U = X − rD. The affine map takes u = x − r to u + A + B/u. The homogeneous update is

    X' = U² + A U D + B D²
    D' = U D.

Starting from (x,1), the final test is D ≠ 0 and X = cD. A pole sets D to zero and that state persists through the remaining steps. Chain.lean proves the terminal Boolean condition equivalent to successful evaluation of the affine chain at c, for arbitrary fields, finite map lists, inputs and targets. The theorem includes empty chains and intermediate poles. Each C++ multiplication uses an unsigned 64-bit product of two canonical M31 residues and reduces before the next multiplication.

## Measurements

Each process used 24 blocks. Each four-arm timing includes the native checked-root ABI for the final lifts. The native affine control computes the inverse by field exponentiation. The two native arms use identical call boundaries and allocate the same marshaling buffers. The Python inline control uses its archived modular inverse implementation. Each result is the median complete setup time in milliseconds.

| Validation arm | First process | Repeat process |
|---|---:|---:|
| Archived inline Python | 8.096 | 8.520 |
| Deferred Python, same affine predicate | 7.950 | 8.096 |
| Deferred C++, affine | 2.936 | 3.054 |
| Deferred C++, homogeneous | 1.724 | 1.756 |

The median paired native affine/homogeneous ratios were 1.725 and 1.737. The corresponding inline Python/homogeneous ratios were 4.769 and 4.809. The homogeneous arm won all 24 blocks in every listed pair in both processes.

A separate alternating-order panel compared the original Python setup (original lift and original chain) directly with native roots plus homogeneous validation. In the first process the medians were 10.759 and 1.801 ms, with a paired ratio of 5.978. In the second they were 10.807 and 1.796 ms, with a paired ratio of 6.041. All 48 output comparisons per process reproduced the archived ordered basis. These ratios concern public preparation only.

## Replay

Run `python3 replay.py` for the four-arm comparison and `python3 replay.py --full-control` for the two-arm comparison. Both use SymPy, Python ctypes, the sibling public-basis replay and checked-root source, and pinned archive revision efb9330c1. The deferred variants move the per-coordinate predicate to a check on the complete list before the chain returns. They preserve the public generator, chain construction and its other checks. Native flag vectors are also compared element by element with affine Python on controls with empty chains, poles, random coordinates, and multiple terminal targets. The compiled code and the mathematical proof are verified separately.

Replay the theorem with `lake env lean /absolute/path/to/Chain.lean` in the project mathlib environment. The measured machine was an Apple M4 Pro.
