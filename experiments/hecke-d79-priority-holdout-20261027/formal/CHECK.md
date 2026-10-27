# Lean check

The toolchain is pinned by `lean-toolchain` to Lean `v4.35.0-rc4`; `lake-manifest.json` has no external packages. The generated modules are reproducible from the hash-pinned source and audit receipts:

```sh
cd /Volumes/SSD990/cryptanalysis/experiments/hecke-d79-priority-holdout-20261027
python3 formal/generate.py
cd formal
lake build
```

`build-output.txt` records a successful seven-job build of `RankP63317Ascending`, `RankP63317Priority`, and `RankP68437Ascending`, including `#print axioms` for every finite certificate. The reported foundations are `propext` and, for the integer-kernel Boolean reduction, `Classical.choice` and `Quot.sound`. `lean4checker --fresh` was not installed on this host. The first generation attempt duplicated `allRowsQ`; its build failed at that declaration and prompted a generator correction. The final generated modules passed.
