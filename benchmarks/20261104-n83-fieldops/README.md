# n = 83 field ops, Tier 1 (2026-11-04)

Copies for browsing of the study
[`experiments/koblitz-n83-fieldops-20261104/`](../../experiments/koblitz-n83-fieldops-20261104/README.md)
(record `benchmarks/records/20261104T1757Z-n83-fieldops.json`):

- `report.pdf`: the experiment report (design, local ranking, result);
- `result.svg`, `result.png` (150 dpi): the frozen ratios with 95% intervals.

Class: engineering. The same states, keys, relations, probes and tables are
computed, with inlined GF(2^83) field products and squares, byte-image linear
maps and a table-evaluated scan self-test. Result: end-to-end cold
A / B = 1.2610 [1.2541, 1.2681] over 36 alternating pairs, Tier 1 run
41869146827, every gate and control passing `[pcc:unverified]`.
