# Read-only algebraic replay of the complete matrix capture

Use the original raw binary produced by kernel-census. The separate test
checks matrix legality and uniqueness, uses ranks and quadratic truth-table
fixed powers for compatibility, and counts the original representative's
centralizer. All records are read; the input remains unchanged.
[pcc:unverified]

```sh
export N4_KERNEL_CENSUS_IN=/tmp/unique-output/all-symplectic-matrices.bin
cargo test --release --offline --locked --manifest-path \
  experiments/chained-transfer-public-target/kernel-replay/Cargo.toml \
  --lib -- --nocapture --test-threads=1
```

Native907dfc passes one unfiltered test and all2366 source/input guards,
including the binary. It reproduces120,960 compatible matrices and
centralizer12, matching the original135-kernel routec88589. The mathematical
conjugacy/cardinality and geometric bridges are explicit in the written
derivation. Signed execution/full formalization, actual kernel coordinates,
a new isogeny and computational advantage are not supplied by this replay.
[pcc:unverified]
