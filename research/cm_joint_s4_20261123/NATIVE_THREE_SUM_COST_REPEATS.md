# Frozen repeat of the native S4 component screen

The first fixed-stream result under the [cost protocol](NATIVE_THREE_SUM_COST_PROTOCOL.md)
was retained in `native_three_sum_cost_results.json`. Its source and
endpoint solve-time totals are close enough that one stream cannot
support a cost ranking. This addendum freezes four independent
target-stream seeds, `20261125`, `20261126`, `20261127`, and
`20261128`, before those repeats. The first seed is intentionally
rerun to measure process wall and CPU in the same way as the other
three. The source code, bases, 64 retained nonzero targets per seed,
seven interleaved repeats, and truth checks remain those of
`native_three_sum_cost.py` at commit `be44ddf27`. [pcc:unverified]

Run each seed in a separate process, sequentially on the same host.
Set the script's global `SEED` before calling `main()`, so its target
stream and deterministic arm interleaving use that seed. Capture JSON
stdout and `/usr/bin/time -p` stderr separately. Preserve all rows,
all 448 solve times per arm per seed, map and base setup, build times,
truth mismatches, and the process `real/user/sys` receipts. Do not
select a stream after seeing its outcome. [pcc:unverified]

For each seed report the sum of 64 per-query solve medians and the
ratio of expected solve work per useful relation, using the **exact
full-group** hit counts `96/1068` for source and `92/1068` for
endpoint. These fractions avoid treating a few observed positives
in 64 queries as a stable yield estimate. A candidate component gain
requires zero truth mismatches and at least 10% lower endpoint
expected solve work in **all four** seeds. This is only a triage gate;
passing it would still require setup, transfer, full relation
collection, rank, descent, and matched rho before a full cost claim.
Failure to pass it leaves the cost difference unresolved at this
scale rather than proving an impossibility. [pcc:unverified]
