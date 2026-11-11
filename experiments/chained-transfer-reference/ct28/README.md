# CT28: native quotient norms — pending compilation

**[pcc:unverified]** Engineering continuation of [CT27 #1489](https://github.com/isogeny-labs/cryptanalysis/pull/1489), based on exact head `06aafcad7537e0f69f524dc1c86a507388f8736e`. Existing engines, frozen proofs, ledger and pins are not modified.

The newly added `src/ct28_direct_norm.rs` implements formulas for both elliptic quotient norms of the two fixed even genus-two F101 sextics. It handles degree-zero and degree-one supports; split, nonsplit and repeated quadratic supports without factoring; s=0, t=0, x=0; and balanced infinity contributions. It rejects wrong-curve inputs and unsupported fields. The implementation evaluates no unknown scalar and uses elliptic group arithmetic only for tangencies and infinity corrections.

Its native regression enumerates 12,317 classes **per fixed curve**, comparing both coordinates against the unchanged `SplitQuotients::norms`, checking support census, exceptions, infinity and wrong-curve rejection. **These are unexecuted assertions, not successful test results**: this tool environment has neither Rust nor a network checkout. No performance or correctness claim for this new Rust code is accepted until it compiles and passes the independently replayed test.

Reproduction with pinned sibling checkout:

```sh
cd experiments/chained-transfer-reference
./check.sh
cargo test --release --locked ct28_complete_direct_norms_vs_frozen_generic_norms -- --nocapture
cargo clippy --locked --all-targets -- -D warnings
```

The earlier [CT27 Python F101/F101² development oracle](../ct27/README.md) remains the independent-formula control, but is unsigned, and cannot certify this Rust file. After a successful exact-head native differential, instrument complete field-operation counts and elliptic additions, then seek independently signed PCC and authorized cold rho/index-calculus cost comparisons. Neither S3 admission nor live budget is available, so no paid job was launched.

Parent [#1488](https://github.com/isogeny-labs/cryptanalysis/pull/1488) already provides the complete global Jacobian chain. Its review, forked append-only ledger and static-analysis issues remain unresolved. No rebase/force/merge/gate bypass, no cross-prime construction, and no solving speedup claim. [pcc:unverified]
