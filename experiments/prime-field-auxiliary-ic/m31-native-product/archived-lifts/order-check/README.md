# Shared doubling ladder for public auxiliary-generator order checks

For a curve of order 2^k, generate G by k−s doublings of the candidate T,
then compute H by a further s−1 doublings of G. If H is nonzero and H+H
is infinity, G has order 2^s and T has order 2^k. Ladder.lean proves both
order statements together in an additive commutative group. The map-kernel
checks also use exact repeated doubling for their power-of-two multiples.
General scalar multiplication is unchanged.

The previous public chain called the general multiplier several times and
recomputed common prefixes. On the archived depth-five fixture, profiling
100 preparations of the sibling-validator revision identified 200 calls to
Curve.add per preparation. Instrumentation in an untimed replay counts calls
including infinity shortcuts, and counts actual pow(...,-1,p) inversions in
the chain. Sharing the doublings reduces 200 add calls to 85 and 161 field
inversions to 96. The unmodified archive used 321 field inversions in total.

The timing panel rebuilds the complete public basis for every call. The
original arm uses the pinned archived chain and Python lifting. The two
native arms use the same canonical NEON lift library, paired respectively
with the sibling-only and shared-ladder chains. All three verify the full
archived chain metadata, all 32 coordinates in order and all 17 points.
The additional compatibility panel compares chain return values at seven
Mersenne prime fields for full and limited enumerations. The ladder change
applies through the ordinary chain entry point for supported positive depths.

On one shared Apple M4 Pro, 24 blocks balance the six arm orders. Median
full-basis wall times were 389.52, 213.85 and 136.00 microseconds for original,
sibling/native and shared/native. The median within-block ratios against
shared/native were 2.857 and 1.611 respectively. Counts and timings are
stored separately; imports and library loading precede the timed loops.

Build neon.so as in the parent README. Run python3 replay.py /path/to/neon.so
to emit timings on stdout and operation counts on stderr. The benchmark uses
Python with SymPy and the pinned Git objects available in this checkout.
Replay Ladder.lean in the Lean 4.34.1 mathlib environment.
