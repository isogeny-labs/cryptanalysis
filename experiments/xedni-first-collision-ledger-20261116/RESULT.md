# First-hit buckets conserve execution mass

The checked `first_hit_mass_identity` theorem partitions a stopped
experiment's initial mass into disjoint first-hit buckets and terminal
survivors. `uniform_bucket_count_bound` lifts per-visible-prefix scalar
counts into an encoding-mass inequality while preserving each prefix's
own weight. `first_hit_total_bound` then sums a uniform per-stage bound
over any finite number of stages. The conditional corollary states the
square-over-gap form explicitly: if `m²<q` and each of `m` stages satisfies
`(q-m²)·Hₖ ≤ m·Lₖ`, then

`(q-m²)·ΣHₖ ≤ m²·L₀`.

Here `Lₖ` is live execution mass before stage `k`, and `Hₖ` is its first-hit
mass. The stage inequality is a stated hypothesis; it still needs a
universal derivation from the adaptive group-oracle model.

The frozen Z/7 replay from PR #1637 supplied **30,240** complete executions.
The independent audit reconstructed **1,092** collision-free visible-prefix
buckets: 42 before command 1, 210 before command 2, and 840 before command 3.
Each eligible scalar contributed exactly 120, 24, or 6 encodings at those
respective prefix lengths. The stage ledger is:

| Command | Live before | First hits | Live after | Minimum eligible scalars per bucket | Maximum next-hit scalars per bucket |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 30,240 | 5,040 | 25,200 | 6 | 1 |
| 2 | 25,200 | 5,040 | 20,160 | 5 | 1 |
| 3 | 20,160 | 15,840 | 4,320 | 4 | 4 |

Thus **25,920** first-hit executions plus **4,320** survivors equal the
initial 30,240. The third-stage bucket ratio is 4/4 in this small field,
so that stage's scalar-count cap gives no reduction. These rows validate
the conservation and per-bucket weight accounting; they are not a
large-field performance estimate. `buckets.jsonl.gz` retains every
eligible and next-hit scalar count, including zero-hit buckets.

The next proof step is to derive the per-stage inequality for every
collision-free prefix of the actual adaptive oracle program, with
symbolically identical forms and stopping behavior treated explicitly.
Only then does the square-over-gap corollary become a generic-group
success bound. A coordinate-guided xedni lift requires a separate model.

The protocol pins both parent result hashes and the complete prefix law.
The checked Lean project pins v4.35.0-rc4 and Mathlib
021c46bdd042f67b538b9f9871d556a93713a9a9. `SEAL.sha256` binds the
source, raw buckets, independent audit, proof map, and 3,144-job build
receipt.
