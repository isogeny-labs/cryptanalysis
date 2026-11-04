# The native (Z/pZ)^* rho round, fused (2026-11-03)

Copies for browsing. The study, with the performance-index outputs, the
figure source and the reproduction commands, is
[`experiments/rho-zp-fused-20261103/`](../../experiments/rho-zp-fused-20261103/REPORT.md).

- `report.pdf`: the report;
- `ir_and_wall.svg`, `ir_and_wall.png` (150 dpi): Ir per group operation
  across the two rounds and per seed, paired wall speedups with 95% CIs.

Headline: 107.0 → 67.2 Callgrind instructions per group operation on a
`Z_p^*` rho solve (0.628×; target was under 100); perfindex
`dlp/c_rho_zp40` 0.630× Ir, 1.240× wall (95% CI 1.204–1.269); every other
kernel neutral; identical outputs on seeds 1–6. Engineering.
