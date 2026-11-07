# Folded pair table: two-bit presence filter (2026-11-04)

Copies for browsing. The study is
[`experiments/pair-filter-two-bit-20261104/`](../../experiments/pair-filter-two-bit-20261104/REPORT.md).

Production Rust crate `suite/`, measured against `main` a08cbbef7. The
decompositions are the same.

- **Two-bit filter.** k0n53 relation collection runs 1.136× faster (95% CI
  1.093–1.162). [pcc:unverified] The k0n53 descent reads 1.085× within
  noise. Instruction counts are unchanged.
- **Pentanomial shift fold.** Measured and dropped: 0.794× on
  `gf2_n53_mul_sqr_1m`.

Class: engineering.
