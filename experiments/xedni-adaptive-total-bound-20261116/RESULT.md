# Adaptive group-label first-hit bound

For any finite typed program that starts with `G,Q=w•G` and chooses each later group addition or subtraction from previously visible labels, the exact first-hit execution count at stage `k≥2` satisfies

`(q−k²) · H_k ≤ k · L_k`,

where `q` is the field cardinality, `H_k` counts scalar-and-bijective-label-encoding executions whose first informative group equality occurs at stage `k`, and `L_k` counts executions still live there. Summing stages 2 through `m−1` gives

`(q−m²) · Σ H_k ≤ m² · q · |A ≃ L|`.

For uniformly sampled scalar and bijective encoding and `q>m²`, division by the execution-space size gives probability at most `m²/(q−m²)` for an informative equality after the two seed points. The proof applies to the exact point trace of a label-adaptive group program with a finite field `F`, finite additive `F`-module `A`, an injective map `s ↦ s•G`, and a finite label set `L` admitting bijective encodings. Each decision may depend on the whole visible label prefix. The event is the first equality of two distinct affine forms in the actual group trace.

`formal/AdaptiveTotalBound.lean` closes the bridge from the prior fixed-bucket bound to actual execution cardinalities. It first decomposes `bucketMass` into exact encoding fibers, sums the per-bucket inequality, applies the adaptive encoding-fiber equivalence, then uses the established live and first-hit bucket identities. The aggregate inequality follows from the stage bounds and the cardinality of the full execution space. Four new declarations build with standard Lean foundations; exact statements and hypotheses are in `PROOF_MAP.md`.

The frozen arithmetic replay in `run.py` checks four stage inequalities against all 35,280 scalar-and-encoding executions of the earlier Z/7 control, and sums the twelve fixed visible Z/101 bucket inequalities by prefix length. The Z/7 inequality has positive `q−k²` at stage 2; later Z/7 stage checks have a zero multiplier. The Z/101 bucket sums are a fixed subset of visible buckets, while the Lean theorem quantifies over every bucket. Both source result hashes are pinned in `protocol.json`, and the replay passes.

Run `cd experiments/xedni-adaptive-total-bound-20261116/formal && lake build AdaptiveTotalBound` for the proof and `python3 experiments/xedni-adaptive-total-bound-20261116/run.py` from the repository root for the arithmetic replay. The next mathematical step is to extend the event accounting to the seed equality and to any further operations or information channels in a proposed xedni construction.
