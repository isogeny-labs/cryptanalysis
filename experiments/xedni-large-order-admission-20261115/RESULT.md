# Larger-order admission for the xedni rank-gap bound

The frozen selector found eight prime fields whose fixed base curve
`y²=x³−x−2` has a largest prime-order subgroup in `[289,600]`. Every
selected subgroup passes the numerical hypotheses of the checked two-point
rank-gap obstruction at `L=4`, `d=1`, `c=1`, `K=4`, and one torsion label:

`d<2`, `K≤cL`, `T(2c+1)^d=3<4`, `2L=8<q`, and
`(4L+1)^2−1=288<q`.

| Field prime `p` | `#E(F_p)` | Largest prime subgroup `q` | Cofactor |
| ---: | ---: | ---: | ---: |
| 313 | 331 | 331 | 1 |
| 421 | 439 | 439 | 1 |
| 431 | 419 | 419 | 1 |
| 547 | 571 | 571 | 1 |
| 571 | 599 | 599 | 1 |
| 593 | 626 | 313 | 2 |
| 617 | 586 | 293 | 2 |
| 677 | 706 | 353 | 2 |

The rule scanned primes in `[293,5000]` in increasing order and selected
the first eight whose curve order met the subgroup band. It used only the
base-curve group order; no target, lift, relation, or outcome was inspected
during selection. `result.json` retains all 62 screened primes, factors,
selected flags, and the numerical gate for each selected field. The checked
Sage launcher produced the result after saving its runtime receipt.
`audit.py` independently counted points using quadratic residues and
factored every recorded order with integer trial division. It reproduced
all 62 records and eight selections; both stderr files are empty.

These conditions admit a future arithmetic test; they do not establish the
rank-one bounded-coordinate representation of selected rational lifts. A
complete ordered two-offset scan on these subgroups would contain
`1,471,112` queries before lift construction and auxiliary probes. A next
lift experiment should freeze a query sample and charge every failed
construction, while measuring the actual rank, coordinate radius, and
torsion labels for accepted rational curves. The theorem that defines this
gate is `XedniObstruction.no_uniform_rank_gap_cover` in PR #1596.

Reproduce from the repository root:

```sh
./sage --runtime-info > experiments/xedni-large-order-admission-20261115/sage-runtime-info.json
./sage -python experiments/xedni-large-order-admission-20261115/run.py > experiments/xedni-large-order-admission-20261115/result.json 2> experiments/xedni-large-order-admission-20261115/run.stderr
python3 experiments/xedni-large-order-admission-20261115/audit.py > experiments/xedni-large-order-admission-20261115/audit.json 2> experiments/xedni-large-order-admission-20261115/audit.stderr
```

This is an exact arithmetic admission diagnostic, with no CPU performance
comparison or measured rational-lift yield.
