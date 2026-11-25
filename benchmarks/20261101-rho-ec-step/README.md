# EC rho step: inline arithmetic, four interleaved inversion chains (2026-11-01)

Copies for browsing. The study, with raw rounds, performance-index outputs,
figure source and the reproduction commands, is
[`experiments/rho-ec-step-20261101/`](../../experiments/rho-ec-step-20261101/REPORT.md).

- `report.pdf`: the report;
- `ir_and_wall.svg`, `ir_and_wall.png` (150 dpi): Callgrind instructions per
  group operation for the baseline (`main` 8a93e468d), the variants tried and the kept code,
  and the interleaved wall rounds of the kept variant against the baseline
  with a baseline-against-itself arm.

Headline: 311.9 → 292.7 Callgrind instructions per rho step on a 44-bit
prime-order curve (0.938×); perfindex `dlp/c_rho_ec36` 0.948×; every
`dlp` and `field_ec` fingerprint identical; wall median 0.219 → 0.192 s on
the 44-bit solve (L0, quiet host, A/A arms within 1%). Engineering: `S` and every
reported constant unchanged.
