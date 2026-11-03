# Rust suite: GF(2^n) products inlined, Frobenius canon tightened (2026-11-03)

Copies for browsing; the study is
[`experiments/suite-gf2-clmul-canon-20261103/`](../../experiments/suite-gf2-clmul-canon-20261103/REPORT.md).

Headline: Callgrind Ir 1.07–1.27× on the Koblitz index-calculus kernels of
the production Rust crate (`suite/`), fingerprints identical; native wall
neutral or faster (`pair_table_build_n31_l10` 1.088×, `koblitz_n53_fast_mul_2k`
1.063×, index 1.033). Engineering; the requested halving is not reached.
