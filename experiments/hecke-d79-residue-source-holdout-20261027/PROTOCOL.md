# Prospective residue-priority D79 source holdout

The source-order rule was chosen from the completed p63317 and p68437 catalog inspection before this new prime and its degree-13 source outputs were selected. It is trained on those two cases and is evaluated prospectively on a different prime.

## Instance selection before degree-13 work

Scan odd `v=273,275,...,501` and set `p=v²+316`. Keep prime `p` with `5 | #E(F_p)`, `5 ∤ p−1`, and largest prime divisor of `#E(F_p)` at least 53, for `E: y²+y=x³−x²−10x−20`. Inspect at most the first eight eligible primes. For each eligible prime, construct the D79 conductor-four class using the pinned degree-2/5 source, accepting the first case with exactly 40 sorted class points. Retain every rejected or failed case; no degree-13 source output participates in selection. If none qualifies, stop `NO_CLASS`.

## Frozen source order and stage gate

Project the 40 class points to the order-five quotient exactly as in the pinned prior class builder, using its first nonidentity point as the residue generator. Build buckets by residue. Visit residues 1 and 4 in round-robin order, then 2 and 3 in round-robin order, then residue 0, with ascending point index within each bucket. Record the order and digest before any degree-13 lift. Compare against the existing all-residue round-robin order as a descriptive comparator only when all required source receipts are available.

Build the degree-2/5 rows and enumerate direct signed relations with support at most four before degree-13 work. Record their rank over the largest prime-order field. Lift sources only in the frozen new order, using the hash-pinned degree-13 function cache. At source counts 5, 10, 15, 20, 25, 30, 35 and 40, enumerate signed cancellations among lifted outside-class totals with support at most four, derive group-verified Hecke rows, and measure relation rank modulo the largest prime factor. Stop at the first checkpoint with rank at least 39, otherwise at 40. Preserve every checkpoint, status, row, source lift time, and validation failure. Rank 39 plus a valid anchor is only a class-log readiness gate; this experiment does not supply a target or an IC speedup.

The primary outcomes are source count at rank 39 or `CAP40_RANK_DEFICIT`, and the charged source-lift sum and row-enumeration time up to that stop. A stop before 40 is a prospective result under the frozen ordering, not an estimate derived from a completed source pool.
