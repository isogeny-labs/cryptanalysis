# Finite kernel-character and EDS-normalizer comparison

The [frozen independent controls](NORMALIZER_KERNEL_EQUIVALENCE_PROTOCOL.md)
tested the curve-oriented character identity
`chi_p(K_E(x(P))) = c_E*chi_p(y(P)*Phi(P))`. The prior `D=-19`
60-point equality was a pilot. Results after the freeze:

| Control | Tested labels | Agreement | Orientation `c_E` |
| --- | ---: | ---: | ---: |
| `D=-163`, `p=47`, `r=53` | all 52 | 52/52 | +1 |
| `p=1009`, `r=1069` source | 8 predeclared | 8/8 | +1 |
| degree-5 horizontal codomain | 8 predeclared | 8/8 | +1 |

After those controls, a [separate full-census protocol](NORMALIZER_KERNEL_FULL_PROTOCOL.md)
was frozen. It found **1068/1068** agreement on the source and
**1068/1068** on the codomain, each with orientation `+1`. Every
tested normalizer ratio was nonzero and `Phi(-P)=-Phi(P)` was checked.
The first independent-control run had a JSON serialization error for
a Sage integer after computing its rows; the script's serialization
was fixed before a successful full run, without selecting observations.
The complete records are in
[`normalizer_kernel_equivalence_results.json`](normalizer_kernel_equivalence_results.json)
and [`normalizer_kernel_full_results.json`](normalizer_kernel_full_results.json).
[pcc:unverified]

These are finite equalities. A proof for the EDS-normalizer character
identity on arbitrary curves is still missing. A different identity,
the exact generic **kernel value** formula, is proved in
[`GENERIC_KERNEL_EVALUATION_IDENTITY.md`](GENERIC_KERNEL_EVALUATION_IDENTITY.md).
Neither statement makes this character a known function of the hidden
scalar: the direct `D=-19` ray test disagrees at `d=4`. Nor does the
finite equality show a horizontal-isogeny cost advantage.
[pcc:unverified]
