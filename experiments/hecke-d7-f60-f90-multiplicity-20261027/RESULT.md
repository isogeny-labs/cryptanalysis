# Four repeated-root Hecke rows complete the D=-7 conductor-60/90 ledgers

The multiplicity-aware collector recovers **four previously omitted
degree-2 rows**, two each in the frozen `D_K=-7` conductor-60 and
conductor-90 class walks. Every archived complete neighbor multiset is
preserved. The new rows pass the classical modular-polynomial and
Hecke group-sum checks, and the augmented ledgers remain closed under
the Fricke involution. Exact rational and two modular ranks are stable.

| Reached conductor | Field | Degrees | Rows before → after | Rank over `QQ`, `GF(23)`, `GF(1000000007)` | Fricke row pairs after |
| ---: | ---: | --- | ---: | ---: | ---: |
| 60 | 6301 | 2, 3, 5 | **234 → 236** | 184 → 184 | 118 |
| 90 | 14431 | 2, 3, 5 | **444 → 446** | 332 → 332 | 223 |

The four new rows come from rational degree-2 x-root pattern `(1,2)`.
Their source columns are 134 and 145 at conductor 60, and 157 and 311
at conductor 90. The archived producer returned no complete neighbor
multiset at those sources; the generic collector returned a unique
three-point multiset satisfying every frozen moment equation and the
elliptic-curve group sum. Each neighbor passes `Φ₂` against its source
`j` value. The [checked-Sage replay](replay.py) retains all root-pattern
and collector-status counts, exact added rows, old-neighbor comparison,
ranks, and complete reconstructed row ledgers.

The [protocol](PROTOCOL.md) froze both matrix hashes, field and degree
sets, archived row/rank counts, and the exact producer and collector
hashes before the run. The separate [integer validator](validate.py)
rechecks the four added row identities and all **682** reconstructed
group sums using affine arithmetic on
`y²+y=x³−x²−10x−20`. It compares the archived and rebuilt integer row
multisets, computes ranks before and after by sparse elimination
modulo 23 and 1,000,000,007, and independently verifies Fricke row
closure in both the archived and augmented ledgers. The archived
ledgers were already Fricke-closed; the added rows form two further
Fricke pairs. The validator returned `INDEPENDENT_D7_F60_F90_PASS`.

Run from the repository root:

```sh
./sage --runtime-info > experiments/hecke-d7-f60-f90-multiplicity-20261027/runtime-info.json
./sage -python experiments/hecke-d7-f60-f90-multiplicity-20261027/replay.py
python3 experiments/hecke-d7-f60-f90-multiplicity-20261027/validate.py
```

This is a relation-stage coverage result with `candidate_id: null` and
`timing_claim: null`. Alongside the nine recovered rows in the earlier
four-conductor panel, the saved D=-7 conductor set now has thirteen
recovered repeated-root rows across conductors 42, 60, 70, 90, 150,
and 210. The next experiment is to apply the complete ledgers to a
frozen density or rank-deficiency model, where the question is whether
coverage corrections alter the model's fitted trend rather than only
individual row counts.
