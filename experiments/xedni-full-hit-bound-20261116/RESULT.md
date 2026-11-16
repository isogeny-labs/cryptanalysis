# Complete first-hit bound for adaptive group-label programs

The first informative group equality in an adaptive add/subtract program has an exact seed term and a quadratic later-stage bound. Starting from `G,Q=w•G`, a seed equality occurs exactly at `w=1`; with all bijective group-label encodings, its execution mass is `|A ≃ L|`. For a program with `m` point positions over a field of cardinality `q`, the checked Lean theorem gives

`(q−m²) · H_all ≤ (q−m²+m²q) · |A ≃ L|`,

where `H_all` is the sum of first informative hit counts over every stage. When `q>m²` and scalar and encoding are uniform, the equivalent probability bound is `Pr(hit) ≤ 1/q + m²/(q−m²)`. The theorem's natural-number form keeps its exact finite counting boundary and handles `q≤m²` without division.

The program is typed from two seed points. Each subsequent step chooses two prior points and adds or subtracts them based on the visible encoded point labels. The group is a finite additive module over the finite field; `s ↦ s•G` is injective, and encodings are bijections from group points to labels. An informative hit means equal actual group points represented by distinct affine forms. `formal/FullHitBound.lean` establishes that stage 0 has no hit and stage 1 is equivalent to `w=1`, then counts the seed fiber and combines it with the late-stage theorem from `AdaptiveTotalBound.lean`.

The frozen controls in `protocol.json` test both ends of this count. An independent exhaustive Z/7 replay enumerates all 35,280 scalar-and-encoding executions and records 5,040 seed hits, 17,640 later first hits, and 12,600 survivors. It agrees with the earlier sealed stage counts. For a three-point Z/101 program, exact seed-label order symmetry counts every bijective encoding without enumerating 101! permutations. The first-hit probability is `5/202`: one full encoding fiber each at scalars 0 and 1, plus half a fiber at scalar 51. The aggregate bound passes with positive `q−m²`.

This theorem resolves the complete informative-equality event in the specified adaptive group-label model. The original xedni lifting proposal uses rational-curve lifts and a reduction lattice; formal treatment of that construction requires its lift and lattice-search semantics. The next proof work should connect those objects to an explicit sampled candidate family or identify a construction that evades the counting mechanism.

Rebuild with `cd experiments/xedni-full-hit-bound-20261116/formal && lake build FullHitBound`; replay the controls from the repository root with `python3 experiments/xedni-full-hit-bound-20261116/run.py`. The proof map, build output, exact result, and SHA-256 seal are kept alongside the source.
