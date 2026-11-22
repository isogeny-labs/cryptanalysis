# k0n53 walked descent: walks per shared inversion (2026-11-04)

Copies for browsing. The study is
[`experiments/descent-walks-k0n53-20261104/`](../../experiments/descent-walks-k0n53-20261104/REPORT.md),
measured under a protocol frozen before any data.

Headline (production Rust crate `suite/`, all 3,840 descents verified [pcc:unverified]):

- 512 walks per shared inversion against 64 lower the cost per trial by
  1.095× (95% CI 1.080–1.109; A/A ±1.7%). [pcc:unverified]
- Adopted for subgroups of order at least 2^40.
- Perfbench k0n53 descent against main: 1.222×. [pcc:unverified]
- The k0n31 rung keeps 64 walks: 512 made it 0.835× as fast.

Class: engineering.
