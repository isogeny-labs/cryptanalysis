# Frozen matched Cayley panel, 2026-11-25

This protocol precedes the eight-case run. It extends the independent pilot
and does not replace the unavailable `m4_L20_w5.ms`, `m4_L24_w6.ms`, or
`m4_L28_w7.ms` systems.

## Fixed inputs

- Field: `GF(15359)`; curve: `y^2=x^3+2x+8`, group order 15581 prime.
- Same six-root factor bases, source generator, and Semaev chain as the
  committed pilot in `generate_msolve_pilot.py` and `pilot_fixture.json`.
- Source generator SHA-256:
  `29485f0283dc4c6e71c680f13e216a165e6775c4ec27817b47ff9edfb906c81c`.
- Reference input hashes: Cayley
  `b6fe3243bb257045fa55d24dc85835bda93d62c7e97ec9cc929ce08f66d7ae2a`;
  matched roots
  `7dea3daf7feebcd5fefc0c4b026492a0a0f8b8544352d03d9958bd32258825b6`.
- Four positive controls are sums of the three shared factor-base points
  with signs `+++`, `-++`, `+-+`, `++-`. Their target coordinates are,
  respectively, `(4660,8866)`, `(5131,10178)`, `(8142,5977)`, `(1996,13869)`.
- Four further targets are `[k]G`, with `G=(1893,12621)` and
  `k=1,137,271,997`. Their coordinates are `(1893,12621)`,
  `(8541,12965)`, `(10498,13654)`, `(5370,9573)`. These cases remain in the
  panel whether either arm has a relation or not.

## Procedure and decision boundary

Run `sage -python research/p1_smoothness_leads_20261125/panel.py` once with
SageMath 10.10.rc0 and local `msolve` 0.11.0. One thread and default
genericity/linear-algebra settings, `-v 2`. Execute Cayley then matched roots
for each target. Keep all 16 input files, solver outputs, and compressed raw
logs. `panel.py` records exit status, wall time, full-log SHA-256, step-degree
maximum, all F4 round geometry, ideal degree, and whether the solver returned
the no-solution marker. A nonzero exit or timeout is retained as a failure,
not rerun silently.

The primary structural comparison is the paired sequence of F4 step degree,
selected pairs, outstanding pairs, matrix rows, and matrix columns. The four
shared-relation controls must produce at least one solution in both arms.
Single-run wall times are diagnostic only; no speedup or asymptotic claim is made here. `[pcc:unverified]`
The exact L20/L24/L28 comparison remains a separate
requirement. Amend this protocol explicitly before any changed run.
