# Four-coordinate signed-digit Hensel lift

## Measured result

The frozen minimum signed-digit rule raises the same selected relation
residual from 313-adic depth 1 to 8. It uses signed coordinate digits with
maximum radius 3, independently verified by exhaustive enumeration at each
step. The rational model at depth 8 is 235 bits, compared with 205 bits for
the prior first-axis path. The proxy improves depths 2 through 5 but does
not minimize final rational model height on this paired instance.

| Depth | First-axis model bits | Short-digit model bits | Difference |
| ---: | ---: | ---: | ---: |
| 1 | 23 | 23 | 0 |
| 2 | 54 | 32 | -22 |
| 3 | 74 | 69 | -5 |
| 4 | 102 | 100 | -2 |
| 5 | 119 | 102 | -17 |
| 6 | 148 | 150 | +2 |
| 7 | 177 | 200 | +23 |
| 8 | 205 | 235 | +30 |

The public hit is fixed by the parent run: `p=313`, `q=331`, target scalar
`w=300`, offsets `(0,13)`, points `(15,174)` and `(236,132)`, and relation
vector `(5,4)`. `protocol.json` pins the parent protocol and normalized
result digests. The comparison changes only the coordinate-shift selection
rule. The displayed bit height is the maximum numerator or denominator bit
length among `A,B,x1,y1,x2,y2` on the interpolated rational curve.

## Rule and verification

At depth `k`, the run evaluates `t(5P1+4P2)` modulo `p^(k+1)` and its four
coordinate finite differences. For derivatives `d_i`, it finds signed
digits `δ_i` that cancel the `p^k` coefficient. It minimizes, in order,
`max |δ_i|`, `sum |δ_i|`, and the signed tuple lexicographically. A
pair-sum lookup finds the digit tuple; `audit.py` independently enumerates
all four-tuples through the selected radius and checks the exact optimum.
The audit also reconstructs every probe and accepted curve and group sum
with pure-Python `Fraction` arithmetic. The measured residuals remain
nonidentity at every depth.

The parent [height divisibility proof](../xedni-hensel-height-20261118/formal/HeightDivisibility.lean)
applies to this path under its explicit numerator-bound hypothesis. This
experiment measures the effect of a different digit policy; it introduces
no new universal mathematical theorem. In particular, minimizing a local
digit radius is a different optimization target from minimizing the exact
rational model height. A next experiment can precommit to scoring candidate
digit tuples by exact model height before testing the relation residual.

## Reproduction

Run from the repository root, with the parent result available:

```sh
/Volumes/SSD990/cryptanalysis/sage --runtime-info > experiments/xedni-short-digit-height-20261118/runtime-info.json
/Volumes/SSD990/cryptanalysis/sage -python experiments/xedni-short-digit-height-20261118/run.py
python3 experiments/xedni-short-digit-height-20261118/audit.py
```

`runtime-info.json` records the checked Sage build. `run-result.json`
retains every derivative probe, radius count, digit tuple, exact curve,
point, residual, and formal parameter. `audit-result.json` records the
independent replay. Timing is diagnostic for this construction run and is
not used as an IC/rho or paired solver comparison.
