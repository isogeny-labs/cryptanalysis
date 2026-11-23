# How informative was the depth-12 M31 yield panel?

Each archived base has 4,096 distinct x-coordinates. Exactly 2,025 lift on the target curve and each gives two signed points. The chain and expanded encodings share the same base. All three arms used the same 16 queries. The replay checks these facts against the frozen files.

For a uniform finite target, the chance of any two-point decomposition is bounded by the number of unordered signed pairs divided by the number of finite group points. Allow repeated points. Of the 4,050 × 4,051 / 2 unordered pairs, exactly 2,025 sum to infinity. The remaining 8,201,250 pairs cover at most that many of the 2,147,505,292 finite targets. Collisions can only lower coverage.

A union bound gives at least 93.8896% probability of zero hits in 16 queries for either specified base. Across both bases the probability of zero hits is at least 87.7793%. These are design bounds under the archive's uniform finite-target sampling model. They require uniform marginals and allow dependence between queries and between bases. The archived seeds and their observed results are fixed. The bounds do not estimate the difference in yields.

Coverage.lean proves the unordered-pair image bound for any finite set in an additive commutative group. Its numerical inequality certifies a conservative 87.7% floor even when inverse pairs are included. The Python replay subtracts the inverse pairs for the sharper reported figure.

Run `python3 replay.py` from this directory. Replay the Lean file with `lake env lean -DwarningAsError=true /absolute/path/to/Coverage.lean` in the mathlib Lean 4.34.1 environment.
