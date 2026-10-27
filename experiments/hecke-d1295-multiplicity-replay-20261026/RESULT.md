# D=-1295 two-sheet cycles survive independent multiplicity replay

The generic multiplicity-aware collector from PR #1202 independently
recovers the sole repeated-x degree-2 Hecke fiber in the frozen
`D_K=-1295, f=6, p=11719` class walk. It reproduces the archived
360-row integer multiset and rank 288 over `QQ`, `GF(23)`, and
`GF(1000000007)`. Reconstructing the conductor-2 degree-3 graph from
the new row ledger gives four 18-point cycles, paired by identical
`j`-sets, with projected kernel dimension 8. These are the same
two-sheet measurements as in the prospective D=-1295 experiment.

| Check | Cross-replay result |
| --- | ---: |
| Rational class points | 432 |
| Degree-2 rational x-root patterns | 215 complete `(1,1,1)`; 1 repeated `(1,2)`; 216 partial `(1,)` |
| Degree-3 rational x-root patterns | 144 complete `(1,1,1,1)`; 288 partial `(1,)` |
| Repeated fiber | source 49, degree 2, `RECOVERED_REPEATED` |
| Complete relation rows | archived 360; reconstructed 360; integer multisets equal |
| Matrix rank | 288 in each of `QQ`, `GF(23)`, `GF(1000000007)` |
| Conductor-2 degree-3 cycles | four of length 18 |
| Paired cycle `j`-sets | `(0,3)` and `(1,2)` |
| Conductor-2 projected cycle kernel | dimension 8 |

The [protocol](PROTOCOL.md) freezes SHA-256 for the source matrix, the
regularized Hecke producer, and the generic collector. The checked-Sage
[replay](replay.py) records all root patterns, collector statuses, complete
rows, classical modular-polynomial and group-sum checks, and exact and
modular ranks. The repeated row agrees with the archived producer; the
generic collector adds no row to this matrix. The full row ledger is
retained in `ledger.json` and `reconstructed_rows.json`.

The separate [integer validator](validate.py) compares the persisted
integer row multisets and modular ranks, checks the repeated neighbor
x-multiplicities and group sum using affine arithmetic on
`y²+y=x³−x²−10x−20` over `GF(11719)`, then rebuilds the four
conductor-2 degree-3 cycles from the new ledger. It checks rank 16 on
each cycle and full/projected degree-3 ranks 144/136. The conductor
labels and `j` values come from the saved upstream audit; the cycle
edges and ranks are recomputed from the new rows.

Run from the repository root:

```sh
./sage --runtime-info > experiments/hecke-d1295-multiplicity-replay-20261026/runtime-info.json
./sage -python experiments/hecke-d1295-multiplicity-replay-20261026/replay.py
python3 experiments/hecke-d1295-multiplicity-replay-20261026/validate.py
```

The retained results report `D1295_MULTIPLICITY_CROSS_REPLAY_PASS` and
`INDEPENDENT_INTEGER_SHEET_REPLAY_PASS`. This is a correctness and
structural replay of one frozen matrix, with no wall-time comparison.
The next collector test should target a class whose archived ledger
omits repeated-root fibers, then re-evaluate rank and cycle structure
after inserting those rows.
