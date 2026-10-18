# Exact implicit W9 left-pair membership and its serial work boundary

**A one-slot product-inverse oracle preserved the archived N41 public
relation without storing the 79,424-entry left-pair table.** On 385 frozen
target-conditioned keys it recovered the known left-pair state IDs
`(0,130)` and classified all 384 public-target-derived controls as exact
pair-membership misses. The oracle's product-code lookup agreed with a
direct point lookup for all **109,340** first-slot candidate checks.
Independent checked Sage rebuilt all 80,656 raw left-pair sums and
reproduced every key and hit classification.

For each first-slot state `A` and key `K`, the oracle forms `V=K−A`.
Undoing the second slot's Frobenius rotation gives its raw x-coordinate.
The fixed-seed pair equation `Cz²+pz+H=0`, with `z=1/x`, then forces
`p=C/x+Hx`. A 71-product map returns the possible second-slot source
codes; exact signed point comparison and folded-column checks identify
witnesses. The oracle stores 284 first-slot states and the one-slot
product map. Its positive input is the left-pair sum from the archived
five-pair public relation. The 384 other keys are deterministic
`target−third−right` residuals, 128 each from the previously exhausted
Frobenius orientations 0, 1, and 2.

| Frozen W9 panel | Measured result |
| --- | ---: |
| Keys | 1 known relation residual; 384 target-derived controls |
| First-slot candidate checks | 109,340 = 385 × 284 |
| Direct/product-inverse pair hits | 1 / 1, same `(0,130)` witness |
| One-worker parent wall | 0.660 s |
| Native sum of per-key intervals | 0.640 s |
| Sampled combined peak RSS | 25,870,336 B |
| Independent Sage direct-sum replay | 27.224 s after startup; all 385 keys checked |

The one-worker query had a frozen 120-second wall cap and 4-GiB combined
RSS cap. The checked Sage runtime receipt, panel and query protocols,
source/binary hashes, raw logs, complete Sage replay, Lean proof, and
`python3 verify.py` are retained. The ordinary-host wall measurements are
component diagnostics. `candidate_id` is null.

## Full-path serial-policy floor

The frozen exact N41 2+1 join made **83,612,805** target-conditioned
left-pair lookups before its first relation and reported only **two**
left-pair hash matches. Thus at least **83,612,803** keys are complete
membership misses. Applying this serial oracle separately to every key
would require at least

`83,612,803 × 284 = 23,746,036,052`

first-slot candidate checks, each with a target-dependent point subtraction
and source-product inference. The [work receipt](work_result.json) derives
the count from the frozen join output; the checked Lean recurrence is in
[the proof map](PROOF_MAP.md). Completing that check count in 600 seconds
would require at least **39.58 million checks per second** before any
relation-matrix or target-log work. The frozen panel measured about
170,788 checks per native case-second while also performing the direct
comparison; that rate is an exploratory diagnostic, not a full-path
runtime extrapolation or a hardware limit.

The precise next gate is **whole-block rejection** for still-free
first-slot source codes. Given a target-derived key and a block of first
codes, an exact predicate must reject the block without computing `K−A`
for each signed state, preserve the `(0,130)` positive, and beat the
charged serial policy on the frozen 384 controls. Only a source-bound
method that also fits the N131 one-worker 600-second/4-GiB public-point
gate can advance to a full relation attempt.
