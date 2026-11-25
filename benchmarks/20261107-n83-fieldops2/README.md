# n = 83 field ops 2 (R1), Tier 1 (2026-11-07)

Copies for browsing of the study
[`experiments/koblitz-n83-fieldops2-20261107/`](../../experiments/koblitz-n83-fieldops2-20261107/README.md)
(record `benchmarks/records/20261108T0023Z-n83-fieldops2.json`):

- `report.pdf`: the experiment report (design, local ranking, result);
- `result.svg`, `result.png` (150 dpi): the frozen ratios with 95% intervals.

Class: engineering. The same states, keys, relations, probes and tables are
computed; at n = 83 the inlined GF(2^83) field product and square are called
with the field degree and mask as constants. Result: end-to-end cold
A / B = 1.0256 [1.0236, 1.0278] over 36 alternating pairs, Tier 1 run
42424680756, every gate and control passing `[pcc:unverified]`. The saving is in
the index build (1.0500 [1.0484, 1.0515]); the self-test and the online stage did
not move.
