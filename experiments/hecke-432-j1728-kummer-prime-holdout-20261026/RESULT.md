# Prospective Kummer splitting test at five new primes

The two exact Kummer square classes from the degree-144 quartic construction predicted all **52** local relative splitting patterns at rational primes 13, 17, 19, 29, and 37. The predictions were written and SHA-256 sealed before a separate script reduced either quartic. Every observed reduction was squarefree and every pattern matched. This extends the prior four-prime splitting checks to five disjoint primes with a prospective prediction/observation boundary.

| Rational prime | Base places in degree-36 field | Quartic sides | Relative pattern at every place | Matches |
| ---: | ---: | ---: | --- | ---: |
| 13 | 2 | 2 | `[2,2]` | 4/4 |
| 17 | 2 | 2 | `[2,2]` | 4/4 |
| 19 | 18 | 2 | `[1,1,1,1]` | 36/36 |
| 29 | 2 | 2 | `[2,2]` | 4/4 |
| 37 | 2 | 2 | `[2,2]` | 4/4 |

## Frozen method and receipts

`protocol.json` fixes the primes, both ordered quartics, input file hashes, valuation policy, and 300-second stage caps. The checked repository Sage launcher was used for both stages; `sage-runtime-info.txt` records the loaded arithmetic build. `predict_sage.py` used the two Kummer radicands and their product. At each unramified base place, it required even valuations and evaluated the unit square characters after dividing by `p^valuation`. The pair `(1,1)` predicted four degree-one primes; any other pair predicted two degree-two primes. `prediction_attempt.json` records 36.488 seconds and `predictions.json` contains all 52 predictions.

`observation_protocol.json` sealed SHA-256 `4f9429aa07b54b102f9d81b2cced0857d31d31657a886908c726655ac8b1277b` for that prediction file before observation. `observe_sage.py` read only the factor and split certificates, the frozen protocol, and the prediction **hash**. It reconstructed the exact degree-36 field and ordered quartics, reduced each quartic at each base place, and factored the residue polynomial. Because every reduction was squarefree, those factor degrees give the relative residue degrees. `observation_attempt.json` records 38.599 seconds. `compare.py` checks the hashes, row identities, and all degree patterns; `comparison.json` reports `PASS_ALL_PROSPECTIVE_PREDICTIONS` with 52 matches.

The observation code retains `REPEATED_REDUCTION` and `REDUCTION_ERROR` states with unknown degree patterns if encountered. The five-prime set excludes the previously checked 7, 11, 23, and 31. All timings here are stage wall times on this local host, not isolated performance measurements.

## Mathematical statement and proof map

For an unramified place in the biquadratic splitting field, the two Kummer square characters determine its Frobenius element in `C₂ × C₂`. Under the regular action on the four roots, identity has four fixed points and every nonidentity element has two orbits of length two. Consequently the relative residue degrees are `[1,1,1,1]` for the character pair `(1,1)` and `[2,2]` otherwise. The exact field/radicand identities and nonsquare independence are in the predecessor's `kummer_result.json`; this experiment checks the predicted local patterns independently.

`KummerOrbit.lean` proves the regular-action fixed-point and two-cycle statements for all sign pairs (`identity_fixes_four`, `nonidentity_is_fixed_point_free`, `every_orbit_has_length_at_most_two`, `nonidentity_has_two_cycles`). `lean-output.txt` contains successful compilation and `#print axioms`: the first and third theorems have no axioms; the other two use standard `propext`. Toolchain `leanprover/lean4:v4.35.0-rc4`, mathlib4 revision `021c46bdd042f67b538b9f9871d556a93713a9a9`. The formalization is **partial**: the exact number-field Kummer isomorphism, Frobenius-to-character bridge, and polynomial-to-prime decomposition bridge are mathematical arguments here and are not encoded in Lean. The next proof step is to formalize those bridges for the exact field and radicands.

## Replay

From the repository root:

```sh
python3 experiments/hecke-432-j1728-kummer-prime-holdout-20261026/predict_bounded.py
python3 experiments/hecke-432-j1728-kummer-prime-holdout-20261026/observe_bounded.py
python3 experiments/hecke-432-j1728-kummer-prime-holdout-20261026/compare.py
```

Both bounded runners invoke `/Volumes/SSD990/cryptanalysis/sage -python` for their local Sage stages. Preserve the frozen `observation_protocol.json` when replaying; the comparison verifies its prediction hash.
