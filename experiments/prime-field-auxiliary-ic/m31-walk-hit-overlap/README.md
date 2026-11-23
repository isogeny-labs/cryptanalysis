# Short-lag returns to the fixed M31 depth-5 hit set

For each of the three archived v2 seeds, reconstruct the 32 group increments from the frozen C++ PRNG initialization and the fixture's two public points. The runner checks the source SHA-256 against the batch receipts. It enumerates the 578 finite signed two-point sums H. For shift d the number of possible starts in H ending in H is the multiplicity of d among the ordered differences of H. Enumerating multisets of step indices and weighting their permutations counts all ordered words, including repeated steps.

For all three seeds there is no hit-to-hit path of length 1, 2 or 3. Seed 1 has no such path of length 4 either. Seeds 0 and 2 have respectively 144 and 72 at length 4 out of 606,076,928 choices of starting hit and ordered step word. The zero counts apply to every choice of steps and require no probability model. Nonzero ratios in counts.csv use uniform starting hits and independent uniform step indices, divided by the stationary one-query hit probability 578 / 2,147,505,293.

The batch interleaves 64 walk lanes. For batch seed 1, hits on one lane must be separated by at least five lane updates (320 global query positions on that lane). Hits on different lanes can occur in adjacent global positions. These results exclude short same-lane clustering as the explanation for seed 1's early stopping time. They do not determine the cause of that outcome.

Run `uv run --isolated --with sympy --python 3.13 python replay.py`. Replay Overlap.lean against Lean 4.34.1 mathlib for the difference-set criterion. The runner also independently counts all one-step transitions by direct group addition.
