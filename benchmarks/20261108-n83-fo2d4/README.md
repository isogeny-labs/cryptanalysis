# n = 83 field-ops-2 (R1) against field-ops, both on the D4 closure base, Tier 1 (2026-11-08)

Copies for browsing of the study
[`experiments/koblitz-n83-fo2d4-20261108/`](../../experiments/koblitz-n83-fo2d4-20261108/README.md)
(record `benchmarks/records/` `n83-fo2d4`):

- `report.pdf`: the result report (design, result, stages, controls, distance to rho, limits);
- `result.svg`, `result.png` (150 dpi): the frozen ratios with 95% intervals.

Class: engineering, stacking the two merged n=83 changes: both sides run the D4 base (K' = 4, 400 orbits); only the binary differs
(`ic_online_fieldops_r770` against `ic_online_fieldops2_r770`, R1). Result: end-to-end cold A / B = 1.0504 [1.0467, 1.0541] over 36
alternating pairs, Tier 1 run 42450569196, every gate and control passing `[pcc:unverified]`. The saving is in the index build
(1.0745) and the rank stage (1.0505); the self-test is unchanged (1.0027). In-run gap to rT770: 2.1455 (field-ops on D4) and 2.0426 (R1 on D4).
