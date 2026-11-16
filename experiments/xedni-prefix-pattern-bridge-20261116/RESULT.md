# Equality-pattern coupling gives a weighted prefix bound

The checked `weighted_first_hit_bound` theorem establishes the one-step
inequality `(q − n²)·H ≤ n·L` for a fixed visible prefix of `n` affine
forms over a field with `q` elements. Here `L` sums the bijective-encoding
mass of eligible scalars, and `H` sums any designated first-hit set contained
in the eligible next-form candidates. The argument preserves the visible
label event and allows symbolic forms to repeat.

The structural lemmas identify the exact source of the bound. Outside the
prefix collision set, evaluated equality has the same pattern as symbolic
form equality. Any two traces with that pattern are related by a permutation
of the group-element domain; hence each eligible scalar has equal encoding
weight for the same visible label event. At most `n²` scalar values create
an informative equality among old forms, and the new form supplies at most
`n` candidate roots. The weighted inequality follows by counting each
eligible scalar at its actual label-fiber weight.

A frozen Z/7 control enumerated all seven scalars and all 7! bijective
encodings for old forms `(0,1), (0,1)` and new form `(1,0)`. The repeated
old form gives equal visible labels at every scalar and encoding. The
independent audit checked all seven label buckets:

| Buckets | Live scalar-encoding pairs | New hits | Encodings per eligible scalar in each bucket | Eligible scalars per bucket | Hit scalars per bucket |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 7 | 35,280 | 5,040 | 720 | 7 | 1 |

For this control, the exact bound reads `3·5,040 ≤ 2·35,280`. Raw bucket
counts and the independent audit are sealed with the theorem source and
3,145-job Lean build receipt.

The next formal step is to partition executions of an arbitrary adaptive
program by each visible prefix and show that its reconstructed forms,
remaining eligible scalars, and newly informative hit set instantiate this
fixed-prefix theorem. The current theorem provides the one-step counting
bridge; the whole-program aggregation remains to be connected to it.
