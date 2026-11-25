# Frozen full native relation-scan accounting

This protocol is frozen before the batch of solver calls. It replaces the
sum-table oracle in the corrected cold network panel with a native `msolve`
call at every attempted relation and target-descent query. The target is
`7001*G` from `COLD_NETWORK_V2_PROTOCOL.md`. The prior 137-target scan remains
archived and is excluded from this comparison. Local output has producer-only
standing `[pcc:unverified]`.

## Exact query streams

- Reconstruct the six arms, curve models, x-bound factor bases, and two-
  variable Semaev systems as in `NATIVE_NETWORK_PROTOCOL.md`.
- Precomputation: for each arm independently, run one `msolve -v 2 -t 1`
  call for each `s*G` in ascending `s=1,...,10192`, skipping 7001, through
  the full-rank cutoff recorded in `cold_network_v2.json`. Expected call
  counts in base/degree-list order are `739, 1054, 2229, 1273, 991, 803`.
  The native result must agree with exact group-law x-pair enumeration on
  every call. A mismatch or process failure stays in the record.
- Descent: run the exact query streams from `cold_network_v2.json`: base
  curve at offsets `t=0..34`; fifth isogeny at `t=0..5`; and all five
  isogenies in degree-list order at `t=0..5`, stopping at the fifth arm on
  the final offset. Count repeated query inputs separately for each route,
  because these are distinct cold strategies.

## Charges and custody

For every call retain the exact input SHA-256, raw solver stdout/stderr and
output bytes in a compressed per-arm or per-route archive, exit code, wall
and child CPU time, ideal degree, F4 round count, maximum step degree, and
maximum matrix shape. Report per-arm and per-route sums of wall and CPU,
call counts, failed/mismatched calls, and distribution of ideal degrees.
Aggregate wall/CPU is from one serial run on the same host, with process
launch included. Also retain the sum-table build counts from the corrected
cold panel separately; do not add group additions to seconds as if they
were the same unit.

This batch charges the native decomposition solver. Isogeny construction,
map evaluation, scalar-point generation, and sparse linear algebra remain
outside its wall/CPU totals. It is not an end-to-end rho comparison.
`[pcc:unverified]`
