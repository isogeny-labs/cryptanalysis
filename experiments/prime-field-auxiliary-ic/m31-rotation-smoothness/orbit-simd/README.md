# SIMD rotation-orbit smoothness census on M31

This opt-in AArch64 path computes the original four cumulative census rows. For each nonsquare orbit key it visits the 31 distinct rotations and evaluates the auxiliary and target cubic predicates in parallel. The extra vector lane repeats the initial coordinate and is explicitly excluded. The label calculation applies 30 balanced signed squarings and canonicalizes the final word before equality comparison, using the signed-fold identity in the sibling m31-balanced-square experiment.

Compile from the parent directory with `clang++ -O3 -std=c++17 -mcpu=native -DM31_ORBIT_SIMD=1 census.cpp -o census`. Set the macro to zero to generate the same vector inputs using field products. The default scalar build and M31_BATCH_CENSUS build remain available.

| Complete process wall time, median ms | First | Repeat |
|---|---:|---:|
| Scalar census | 340.037 | 340.794 |
| Existing batched product ABI | 98.041 | 100.561 |
| Fused SIMD, compute x² and x³ per vector | 58.548 | 59.348 |
| Fused SIMD, advance x² and x³ by rotation | 57.523 | 57.183 |

Relative to scalar, the rotation arm's median within-block speedups were 5.902× and 5.942×. Relative to the batched ABI they were 1.711× and 1.745×. Holding the fused predicate implementation fixed, replacing field products with rotation gave paired ratios of 1.006× and 1.032× and won 7/12 and 8/12 comparisons. The large gain belongs to the combined SIMD traversal and predicate implementation. The incremental rotation advantage was small and varied across blocks.

Each of the two panels ran 12 four-arm blocks on one Apple M4 Pro. Each observation launches a fresh process and includes smooth integer enumeration, orbit identification, all predicate evaluations and output. Compilation and post-run comparison are outside the clock. Every arm produced byte-identical output to population.txt at bounds 7, 13, 23 and 47. Run `python3 panel.py` to reproduce one panel. Build and run check.cpp with the same compiler options for 1,024 independent orbit controls and 32,768 lane-level predicate comparisons against scalar Euler exponentiation.

OrbitLanes.lean proves that the used rotation widths implement multiplication by powers of two modulo M31, and that advancing four coordinates advances the square and cube by eight and twelve bit positions. Run `lake env lean /absolute/path/to/OrbitLanes.lean` in the project mathlib environment. The Lean results concern arithmetic identities. The timings concern the complete smoothness census.
