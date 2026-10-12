# Exact N131 coverage bound for fixed-list ten-pair joins

**A fixed five-versus-five group join with five million left states and
five million right probes covers at most `3,275,000,000,000,000` public
targets when all 131 Frobenius rotations are tested.** Against a uniform
target in the ECC2K-130 challenge subgroup, that is a success-probability
upper bound of **`4.81218×10^-24`**. The bound counts each labeled
left/right/rotation triple generously; repeated sums and failed column
checks only reduce coverage. The [Lean theorem](PROOF_MAP.md) proves the
counting statement with explicit cofactor and inverse-Frobenius hypotheses.

This projects the exact list caps from the [verified N41 ten-pair
join](../n41_w8_tenpair_density_control_20261012/RESULT.md) onto the
`EC1N131Ckb1heb5f1998f20b` subgroup of order
`680564733841876926932320129493409985129`. The [frozen
protocol](protocol.json) binds the N41 caps, N131 subgroup census,
131-rotation source, proof, and arithmetic producer. The N41 run recovered
an independently replayed public-point relation after five million stored
states and 898,812 kept right probes; this projection uses its full
five-million right cap. It does not reinterpret that fixed N41 hit as a
random N131 yield measurement.

For each stored half-sum `A`, probed half-sum `B`, and rotation `j`, the
raw sum determines **one** subgroup point `[4](A+B)`. A public target `Q`
matches a selected Frobenius image only when `[4](A+B)=τ^j(Q)`; applying
the inverse Frobenius map assigns at most one `Q` to the triple. Four raw
preimages of `Q` therefore do not contribute an extra factor of four.
This argument applies to half-state lists fixed independently of a
uniform public target, including random lists whose coins are drawn
before the target. It makes no fixed-point claim about the archived
public point or a generator that adapts its lists to that point.

| Fixed-list scenario on N131 | Covered targets, upper bound | Uniform-Q success, upper bound |
| --- | ---: | ---: |
| Five million × five million, no orbit | `25,000,000,000,000` | `3.67342×10^-26` |
| Five million × five million, 131 rotations | `3,275,000,000,000,000` | `4.81218×10^-24` |
| 4-GiB table at an illustrative 17 bytes per exact point, five million probes, 131 rotations | `165,482,563,425,000,000` | `2.43155×10^-22` |

The 17-byte row is an optimistic compact-point **example** that omits
hash-table overhead and witness indices; it is not a universal memory
lower bound. Even at that capacity, half-coverage under the fixed-list
law requires at least `10,281,517,275,237,315,942,193,504,994` right
probes, or over `1.71×10^25` probes per second in 600 seconds. A balanced
left/right join would need at least `1,611,699,512,938,799,596` states
on each side for its union bound to reach one-half; storing that many
left points at 17 bytes each would take about 27.4 exabytes before
index overhead. These are necessary coverage conditions, not runtime
predictions for a different algorithm.

The [exact projection](result.json) retains every integer numerator and
denominator. The [independent verifier](verify.py) recomputes the bounds
from the archived source records; `lean JoinCoverage.lean` checks the
structural theorem and prints its axioms. This gate rejects the direct
N41 sampled join as a uniform-target N131 method under the resource
envelope; the archived fixed point is outside that probability claim. The next
construction must use the public target to reject or generate whole
multi-pair families *before* sampling a bounded half-state table. Its
N41 control should preserve the verified ordinary relation and measure
rejection and useful rank; only a source-bound N131 method under
600 seconds and 4 GiB merits a fresh ordinary query. `candidate_id`
remains `null` pending a complete IC pipeline.
