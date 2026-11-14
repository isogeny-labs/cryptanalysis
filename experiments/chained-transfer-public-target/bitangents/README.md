# Actual q223 bitangents over the degree-six field

Known-case correctness development under prospective361ee8; nativee887a9
passes one unfiltered test and all2338 captured input hashes. The original
field/polynomial engines check28 distinct actual W-coordinate bitangents,
their contact quadratics and Frobenius permutation. [pcc:unverified]

Read [the frozen construction](DERIVATION-01.md) and
[the resulting proof scope](RESULTS-01.md). Full native records and the
source-linked visual report are in evidence/bitangent-acceptance-01 and
reports/bitangents-01. Native dependency caches are reused; timings are not
an admitted benchmark or evidence of computational advantage.
[pcc:unverified]

```sh
cargo test --release --offline --locked --manifest-path \
  experiments/chained-transfer-public-target/bitangents/Cargo.toml \
  --lib -- --nocapture --test-threads=1
```

Four faithful partial declarations in lean/BitangentAlgebra.lean pass both
unchanged original Lean4.35/4.34.1 gates and exact local PCC bindings
a01f8f/5288a0/6cd1a8/d79edc. They prove general polynomial implications and
the exact order of literal permutation data. Actual geometry, theta
characteristics, divisor classes, Weil pairing, kernel construction and
nondual isogenies remain outside those declarations. [pcc:unverified]
