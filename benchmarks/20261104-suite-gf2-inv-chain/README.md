# Rust suite: GF(2^n) inversion chain, trinomial fold, shared field tables, IFMA rows (2026-11-04)

Copies for browsing. The study is
[`experiments/suite-gf2-inv-chain-20261104/`](../../experiments/suite-gf2-inv-chain-20261104/REPORT.md).

Headline (production Rust crate `suite/`, perfindex against `main`):

- Performance index 1.215× (95% CI 1.176–1.285); fingerprints identical.
- Single `Gf2::inv` at n = 53: 4.14× faster (Callgrind Ir 2.78×). [pcc:unverified]
- `KoblitzCurve::mul`: 1.46× faster. [pcc:unverified]
- Signed Frobenius rho at n = 41: 1.20× faster. [pcc:unverified]
- k0n31 IC rung: 1.11× faster. [pcc:unverified]
- PDP enumeration: 1.72–1.93× faster. [pcc:unverified]
- n = 53 multiply and lazy addition: neutral.

Class: engineering.
