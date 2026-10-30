# D=-2631 repeated-root cross-replay preserves the 480-rank Hecke matrix

The generic multiplicity-aware collector from PR #1202 independently recovers
the degree-3 repeated-root fiber in the `D_K=-2631, f=6, p=23743` class walk.
Rebuilding all 576 relation rows gives exactly the archived integer row
multiset and rank 480 over `QQ`, `GF(23)`, and `GF(1000000007)`. Thus the
matrix used by the six-component floor and Fricke eigenspace analyses is
unchanged under this collector substitution.

## Frozen inputs and method

`PROTOCOL.md` pins SHA-256 for the 768-point source matrix, regularized
Hecke-function producer, and generic collector. `replay.py` imports those
exact sources, rebuilds degree-2 and degree-3 functions, enumerates the
neighbor x-root patterns for every point, and substitutes the generic
collector on repeated-root fibers. It verifies the repeated fiber against
the classical modular polynomial and group sum, then reconstructs each
complete relation row. The full reconstructed rows are retained in
`reconstructed_rows.json`.

| Check | Result |
| --- | ---: |
| Frozen points | 768 |
| Degree-2 patterns | 384 split `(1,1,1)`; 384 irreducible `(1,)` |
| Degree-3 patterns | 191 split `(1,1,1,1)`; 1 repeated `(1,1,2)`; 576 irreducible `(1,)` |
| Repeated fiber | source 247, degree 3, `RECOVERED_REPEATED` |
| Repeated neighbor row | columns 23, 247, 278, 279, 493 with coefficient 1 each |
| Complete relation rows | archived 576; reconstructed 576; integer multisets equal |
| Rank over `QQ`, `GF(23)`, `GF(1000000007)` | 480 in both matrices for each field |

The repeated row has four neighbors; its fifth unit coefficient is the
source term because the degree-3 Hecke trace is `a_3=-1`. `validate.py`
separately reads the persisted integer rows, compares their multisets,
recomputes both modular ranks using sparse elimination, and checks the
repeated neighbors' x-multiplicities and group sum with independent affine
arithmetic on `y^2+y=x^3-x^2-10x-20` over `GF(23743)`.

## Reproduction

From the repository root, with the three pinned inputs present:

```sh
./sage --runtime-info > experiments/hecke-d2631-multiplicity-replay-20261026/runtime-info.json
./sage -python experiments/hecke-d2631-multiplicity-replay-20261026/replay.py
python3 experiments/hecke-d2631-multiplicity-replay-20261026/validate.py
```

The checked Sage run reported `D2631_MULTIPLICITY_CROSS_REPLAY_PASS` in
`replay.json`; the separate integer replay reported
`INDEPENDENT_INTEGER_REPLAY_PASS` in `validation.json`. This is an
algorithmic correctness cross-check on the frozen matrix, without a timed
CPU comparison. A next experiment is to use the collector on a larger
class walk with repeated fibers that the archived producer did not admit,
then measure any new rows and the resulting component ranks.
