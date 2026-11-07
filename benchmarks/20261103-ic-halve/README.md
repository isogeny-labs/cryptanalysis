# Index calculus in (Z/pZ)^*: half the instructions (2026-11-03)

Copies for browsing. The study, with the performance-index outputs, the
figure source and the reproduction commands, is
[`experiments/ic-halve-20261103/`](../../experiments/ic-halve-20261103/REPORT.md).

- `report.pdf`: the report;
- `ic_ir_and_wall.svg`, `ic_ir_and_wall.png` (150 dpi): instruction ratios
  and paired wall speedups with 95% CIs.

Headline: Callgrind instructions 2.30× fewer on `c_ic_precompute_zp44`,
2.40× on `c_ic_log_zp44`, 2.02× on `c_ic_randexp_zp36`, 2.97× on
`c_dense_solve`, 1.88× on `c_linsolve_sparse` (61-bit modulus); 2.36× on a
whole `ca ic` linear-sieve solve at 52 bits; wall 1.18–8.80×; identical
outputs. Engineering.
