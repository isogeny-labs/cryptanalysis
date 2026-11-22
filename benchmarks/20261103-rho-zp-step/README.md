# The native (Z/pZ)^* rho step inline (2026-11-03)

Copies for browsing. The study, with the performance-index outputs, the
figure source and the reproduction commands, is
[`experiments/rho-zp-step-20261103/`](../../experiments/rho-zp-step-20261103/REPORT.md).

- `report.pdf`: the report;
- `ir_and_wall.svg`, `ir_and_wall.png` (150 dpi): whole-solve Ir per group
  operation, perfindex `c_rho_zp40` Ir, paired wall speedups with 95% CIs.

Headline: 125.6 → 107.0 Callgrind instructions per group operation on a
`Z_p^*` rho solve (0.852×); perfindex `dlp/c_rho_zp40` 0.853× Ir, 1.111×
wall (95% CI 1.092–1.135); every other kernel 1.000 except `c_rho_ec36`
1.007 (code layout, neutral); identical outputs. Engineering.
