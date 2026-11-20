# prime-field-m3-cdclt (Lead 2B)

Compact binary-selector arity-three disjoint-window chained-`S_3` CDCL(`F_p`)
propagator with independent SAT group-law replay and streaming DRAT(T) UNSAT
checking.

## Status (2026-11-20)

Crate compiles and the preregistered `m = 3`, `s = 5..12` scaling screen completed
with exact verification on every row:

- planted targets: SAT + independent signed group replay;
- exact-UNSAT targets: UNSAT + independent DRAT(T) transcript replay;
- natural targets: same checks; enum-ref model-set agreement where
  `|W|^2 <= 2^20` (`s <= 10`).

Structural compact-binary sizing replaces the Sinz one-hot blowup
(`805,306,365` Boolean vars at `s = 27` → `3s + 3` compact vars).

Log-linear fits on this panel (`fp_ops` vs `s`) [pcc:unverified] (claim `PCC-20261120-114937`, producer-recorded):

| fit | value | gate |
| --- | ---: | --- |
| online `e` (natural `fp_ops`) | ≈ 1.33 | `e < 0.5` **not met** |
| setup `a` (setup `fp_ops`) | ≈ 0.79 | `a < 1.5` met |

UNSAT rows show near-`2^{2s}` decision counts (complete `W_0 × W_1` index
enumeration before theory conflict), so the compact selector removes the
representation wall but does not yet move the online exponent under the
sub-rho gate.

Artifact: [`screen-s5-12.txt`](screen-s5-12.txt).

## Build / test / screen

```sh
export CARGO_TARGET_DIR=/tmp/prime-field-m3-cdclt-target
cargo test --manifest-path crates/prime-field-m3-cdclt/Cargo.toml
cargo run --release --manifest-path crates/prime-field-m3-cdclt/Cargo.toml \
  --bin m3-cdclt-screen -- 12
```

## Modules

| module | role |
| --- | --- |
| `field` | counted `F_p` / Montgomery arithmetic |
| `curve` | Weierstrass group law, chained `S_3`, lambda lift, instance IR |
| `selector` | compact binary vs Sinz one-hot sizing |
| `cdclt` | CDCL(`F_p`) + `ChainedS3LambdaTheory` propagator |
| `proof` | independent SAT replay + streaming DRAT(T) + mutation controls |
