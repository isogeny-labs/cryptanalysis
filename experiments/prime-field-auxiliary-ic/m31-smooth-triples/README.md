# Three-point coverage for signed 211-smooth M31 coordinates

The depth-15 structured base retains 195 liftable x-coordinates, giving 390 signed points. Enumerating unordered triples with repeats gives 9,962,680 representations. An inverse pair cancels in 76,050 of them. The remaining 9,886,630 representations cover 9,864,412 distinct finite points. None sums to infinity or lands on a base point. Exactly 400 of those distinct points are also covered by a two-point sum.

The 76,050 cancelling representations add only the 390 base points to the union. The Lean proof shows that a cancelling triple uniquely determines its leftover point and the unordered inverse pair. Hence m inverse pairs and 2m possible leftover points give exactly 2m² cancelling multisets.

For a uniform finite target, the noncancelling three-point hit probability is 9,864,412 / 2,147,505,292. The two-point hit probability on the same basis is 76,050 / 2,147,505,292. Their ratio is 129.710. With independent uniform queries, the expected waits are 217.70 and 28,238.07 queries. With fixed per-query costs and equal setup, 129.710 is the break-even three-point/two-point cost ratio for time to first hit. This calculation measures neither per-query runtime nor the number of independent relations a full solve requires.

The random archive filter retains 166 coordinates, so its aggregate counts in counts.json are a second workload with a different size. A positive control on ±{P,2P,3P} compares the x-bitset result with direct enumeration of full points, exercising inverse cancellation, infinity and overlapping supports. For the two archive sets, the bitset suffices because global negation preserves noncancellation and each rational affine ordinate is nonzero.

The separate archived depth-10 three-point panel has 500 liftable coordinates and recorded zero relations for four targets per encoding. Even without collisions the triple support including trivial cancellations is at most choose(1002,3) − 500,000 + 1,000 = 166,668,000. For either fixed base, the probability of four misses is at least 68.95% by a union bound under uniform marginals.

Run `uv run --isolated --with sympy --python 3.13 python replay.py` from this directory. Replay Cancellation.lean with mathlib on Lean 4.34.1.
