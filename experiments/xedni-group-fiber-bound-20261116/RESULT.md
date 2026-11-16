# Exact group-fiber candidate bound

For a fixed visible prefix of length `k`, eligible scalars induce the same equality pattern among group points. Uniform bijective group labels therefore give every eligible scalar the same exact encoding-fiber weight. Combining that constant weight with the affine candidate-root count gives

`(q - k²) · M_hit ≤ k · M_live`,

where `M_hit` is the fiber mass of eligible next-candidate scalars in that bucket and `M_live` is the fiber mass of all eligible scalars. The bound is unconditional as a natural-number inequality; it is informative when `q > k²`.

The Lean module `formal/GroupFiberBound.lean` contains checked theorems for equality of eligible group-fiber weights and the weighted inequality over finite fields, finite additive group modules, an injective scalar map, arbitrary affine prefix forms, a next form, and any visible label tuple. Its adaptive-prefix bridge identifies a program's actual encoding fiber with the group-fiber weight of the affine forms reconstructed from that same prefix. This permits the bucket bound to be applied to label-dependent programs once the bucket-mass sums are rewritten. The resulting total program inequality remains the next proof obligation.

The frozen Z/101 control in `protocol.json` checks twelve visible buckets across prefix lengths 2–5. `run.py` evaluates every scalar in each bucket, counts compatible bijective encodings as `(101-d)!` for `d` distinct group points, and checks the weighted inequality with exact integers. All twelve buckets pass. Repeated labels give zero eligible mass where they conflict with the equality pattern; these rows are retained. The prior exhaustive Z/7 execution control is referenced by SHA-256 in the protocol and checked by the run script.

This arithmetic is a fixed-bucket control, not an enumeration of all 101! encodings. Its output is `result.json`; rerun with `python3 experiments/xedni-group-fiber-bound-20261116/run.py` from the repository root. The next proof step is to sum the pointwise bound over all visible prefixes and connect those sums to the live and first-hit execution cardinalities in `BucketFiberPartition.lean`.
