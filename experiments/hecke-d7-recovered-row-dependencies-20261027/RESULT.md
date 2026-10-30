# Exact certificates explain all thirteen stable-rank D=-7 row additions

Every one of the **thirteen** multiplicity-recovered Hecke rows at
`D_K=-7` conductors 42, 60, 70, 90, 150, and 210 lies in the exact
`QQ` span of its own archived relation matrix. The saved certificates
express each recovered integer row as an integer combination of
archived rows divided by a positive denominator, with the equality
checked in every matrix column. This directly explains why adding
the recovered rows changed coverage but not the six exact ranks.

| Conductor | Recovered rows | Original certificate supports | Final supports after finite Fricke transport |
| ---: | ---: | --- | --- |
| 42 | 3 | 41, 41, 9 | 41, 41, 9 |
| 60 | 2 | 6, 31 | 6, 6 |
| 70 | 2 | 52, 30 | 30, 30 |
| 90 | 2 | 8, 36 | 8, 8 |
| 150 | 2 | 15, 57 | 15, 15 |
| 210 | 2 | 38, 311 | 38, 38 |

For each conductor, [solve.py](solve.py) selects independent archived
rows from deterministic transpose pivots modulo 1,000,000,007. The
selected basis size equals the archived rational rank. It then solves
each target over `QQ`, clears denominators, and saves the complete
coefficient list in `certificates_f*.json`. Denominators range from 1
to 4. The [frozen input manifest](inputs.json) pins all six matrices
and both collector replay receipts; [PROTOCOL.md](PROTOCOL.md) fixes
the exact row-identity gate.

The archived ledgers at conductors 60, 70, 90, 150, and 210 are
Fricke-closed, and each conductor's two recovered degree-2 rows map
to one another. Under the [frozen transport rule](TRANSPORT_PROTOCOL.md),
[transport.py](transport.py) maps the shorter certificate's archived
rows through the exact point and row permutation, then verifies the
partner identity over the integers. This reduces the five larger
partner supports from **487 to 97** coefficient terms in total; the
conductor-210 partner falls from 311 to 38. Conductor 42 retains its
original certificates because its archived row multiset lacks one
Fricke partner. The final thirteen certificates contain 285 nonzero
terms, versus 675 from independent basis solves.

The separate [pure-Python verifier](verify.py) checks the pinned
inputs and all original and transported certificates by summing the
archived integer rows and comparing every column to the target row.
It returned `INDEPENDENT_EXACT_DEPENDENCIES_PASS` for all thirteen
targets and all five transported identities. The certificates are
deterministic witnesses, not minimum-support solutions; their support
counts describe the recorded algorithm and inputs.

Run from the repository root:

```sh
./sage --runtime-info > experiments/hecke-d7-recovered-row-dependencies-20261027/runtime-info.json
for f in 42 60 70 90 150 210; do
  ./sage -python experiments/hecke-d7-recovered-row-dependencies-20261027/solve.py --conductor "$f"
done
python3 experiments/hecke-d7-recovered-row-dependencies-20261027/transport.py
python3 experiments/hecke-d7-recovered-row-dependencies-20261027/verify.py
```

The next question is whether the short conductor-60/90 certificates
arise from a uniform local Hecke/Fricke identity. A proof would need
to identify the relevant rows by class-action structure, beyond the
finite integer identities retained here.
