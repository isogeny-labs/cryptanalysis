# Frozen D=-1295 multiplicity and sheet-cycle replay

The input is the existing `D_K=-1295, f=6, p=11719` 432-point,
360-row class matrix at
`experiments/hecke-two-sheet-small-order-20261023/data/exp11_class_walk_D1295_f6.json`,
SHA-256 `33854aefc3ba05b93917aa9b2dd0ebaa558c96ba3dd5d500bea3a2d3b7736baa`.
Use the regularized Hecke producer at
`experiments/hecke-new-quotient-holdout-20261026/tools/hecke11.py`,
SHA-256 `d13a8663c1beb145c0b66147305831bb15678208d126df5b69ddf5e17962b32b`,
and the generic multiplicity-aware collector at
`experiments/hecke-multiplicity-collector-20261026/multiplicity.py`,
SHA-256 `89a6cfd5951666587589834d8b8e288aaf0dfc48d9e310df62ef44c48f5bca1e`.

For every saved point and degree 2 or 3, record the neighbor x-root
multiplicity pattern. On repeated-root fibers, run the generic collector;
on simple-root fibers use the archived producer. Retain explicit statuses,
complete rows, old/new multiset differences, classical modular-polynomial
checks, and group-sum checks. Compare matrix rank over `QQ`, `GF(23)`, and
`GF(1000000007)`. Reconstruct the conductor-2 degree-3 graph and verify
whether its four 18-point sheet cycles and projected kernel dimension 8
survive any added rows. Save exact runtime and independent integer replay.
