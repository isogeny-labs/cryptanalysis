# n = 83 closure base D4 (K' = 4, 400 orbits) against M38 (K' = 16, 608 orbits), Tier 1 (2026-11-07)

Copies for browsing of the study
[`experiments/koblitz-n83-k4c400-20261107/`](../../experiments/koblitz-n83-k4c400-20261107/README.md)
(record `benchmarks/records/` `n83-k4c400`):

- `report.pdf`: the result report (owner ruling, result, stages, controls, distance to rho, limits);
- `result.svg`, `result.png` (150 dpi): the frozen ratios with 95% intervals.

Class: engineering, one frozen producer binary on both sides (`ic_online_fieldops_r770`); only the closure base differs.
Per the owner ruling of 2026-11-07 a closure base with K' >= 4 counts as an index-calculus row. Result: end-to-end cold
A / B = 2.0014 [1.8777, 2.1308] over 60 alternating pairs, Tier 1 run 42425640847, every gate and control passing
`[pcc:unverified]`. The saving is in the setup (index build 2.3928, self-test 4.9689) and the rank stage (1.7485); the
online stage is slower (0.6487 [0.3347, 1.1395], not separated). Not stacked on R1 (field-ops-2): R1 x D4 was not run.
