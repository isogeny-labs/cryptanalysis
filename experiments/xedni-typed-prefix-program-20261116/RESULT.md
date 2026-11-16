# Typed prefixes preserve adaptive execution and symbolic forms

The checked `takeAt` construction extracts a valid `Program L n k` from
any `Program L n m` with `n≤k≤m`. For every encoding and input,
`runGroup_takeAt` identifies its group execution with the first `k`
points of the complete run. `formsFromTranscript_takeAt` gives the
matching equality for affine forms reconstructed from visible labels.
Consequently, changing unseen suffix labels cannot change any form
already present at stage `k`.

For public `G,Q=wG`, `dlp_prefix_labels_iff_symbolic` applies the prior
whole-program fiber equivalence to this typed prefix. An encoding follows
a proposed visible prefix exactly when it assigns those labels to the
corresponding reconstructed affine points. The checked
`actual_prefix_fiber_count_eq_symbolic` theorem states the equality of
encoding counts for every such prefix, including known form repeats and
prefixes that no execution reaches.

A frozen Z/7 control used the adaptive program that branches from the
seed labels, appends `G−G` twice, and then appends `G+G`. It checked every
proposed complete label tuple, every scalar, every bijective encoding,
and all prefix lengths 2 through 6:

| Form causality checks | Group prefix checks | Scalar–prefix-label fiber cells | Positive fibers | Zero fibers | Mismatches |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 588,245 | 176,400 | 960,743 | 17,437 | 943,306 | 0 |

The independent audit reconstructed all 17,437 positive fibers by
assigning labels to distinct group elements in each algebraic branch.
At each prefix length, its total fiber weight is 35,280, the count of
seven scalars times 7! encodings. The compressed positive rows, frozen
protocol, independent audit, and 3,148-job Lean build are sealed.

The next formal step is to define first informative hit on the extracted
program prefixes and establish that the live and hit execution sets are
exactly the eligibility and next-root fibers summed in
`aggregate_bucket_bound`. This prefix theorem supplies the path and
cardinality equivalence needed for that step. A full success statement
also needs explicit treatment of the initial `G=Q` event and the
program's output rule. Coordinate-guided observations require a separate
model.
