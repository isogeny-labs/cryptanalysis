# Actual q223 rational two-primary scout

Fixed known-case correctness development. All standing unsigned. The native
plan c3b30d predates the Rust source; the published plan/result are exploratory,
with no held-out selection or performance claim. Native02/510d03 captures2318
selected files and matches all four JSON records of the preserved partial
capture01. Correction1311d9 records01's omitted V2 dependency snapshots.
[pcc:unverified]

Run the single unfiltered serial test with the repository's pinned Rust1.99.1:

```sh
cargo test --release --offline --locked --manifest-path \
  experiments/chained-transfer-public-target/two-primary/Cargo.toml \
  --lib -- --nocapture --test-threads=1
```

Read [the full derivation](DERIVATION-01.md) for the rational C4 group and
minimal geometric2-torsion field F223^6. The original Ciani isogeny's
degree-even kernel does not identify source and target geometric2-torsion.
No new nondual isogeny is implemented. [pcc:unverified]

The four feasible declarations in [FrobeniusSix.lean](FrobeniusSix.lean) pass
both unchanged original proof gates under Lean4.35 and4.34.1 with zero trusted
declarations. Bindings4e7bfe/cc7273/abcfec/5facfe pass the original local PCC
checker, unsigned. They formalize the exact integer, module and divisor
implications, with the full geometric bridges explicitly open. Audited
foundations: exact trace none; orbit/divisor propext and Quot.sound; module
implication propext. No fresh lean4checker result is claimed.
[pcc:unverified]

Native/source proof capture, exact bindings and the source-linked visual
report are under evidence/two-primary-* and reports/two-primary-01. Further
kernel construction requires actual geometric torsion coordinates and
Frobenius action or an equally explicit descent construction; a necessary
polynomial condition or genus-two Richelot API is insufficient.

```sh
ELAN_TOOLCHAIN=leanprover/lean4:v4.35.0 bash tools/lean/proof-gate.sh \
  --out /tmp/two-primary-proof \
  experiments/chained-transfer-public-target/two-primary/FrobeniusSix.lean
```
