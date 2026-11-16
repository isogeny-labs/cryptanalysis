# Minimal point-lift shift in the CRT xedni panel

A deterministic lift shift removes the integral-chord prefilter while keeping
all reduced target points fixed. For each distinct-x pair of centered integer
lifts, the arm changes only the first y coordinate by `k p`, choosing the
smallest `(|k|,k)` for which the chord slope is integral. On the same eight
fields and 30,008 ordered target queries as the parent matched-subgroup panel,
this arm produced six rational relations in three sign-related pairs: four
at `p=47` and two at `p=251`. The parent policy produced two relations at
`p=47`. This is a finite-panel effect of the changed point lifts, with the
same public points and complete coefficient-search accounting.

| `p` | Subgroup `r` | Queries | Nonzero y shifts | Accepted curves | Accepted reduced relations | Rational relations: parent → shift | Shifted auxiliary probes |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 47 | 43 | 1,849 | 1,460 | 1,344 | 34 | 2 → 4 | 305,850 |
| 101 | 53 | 2,809 | 2,380 | 2,072 | 44 | 0 → 0 | 498,852 |
| 191 | 53 | 2,809 | 2,468 | 2,096 | 40 | 0 → 0 | 531,858 |
| 211 | 79 | 6,241 | 5,564 | 4,648 | 60 | 0 → 0 | 1,140,922 |
| 251 | 61 | 3,721 | 3,364 | 2,664 | 50 | 0 → 2 | 647,397 |
| 281 | 73 | 5,329 | 4,792 | 3,928 | 46 | 0 → 0 | 935,207 |
| 347 | 47 | 2,209 | 1,940 | 1,608 | 38 | 0 → 0 | 377,926 |
| 349 | 71 | 5,041 | 4,640 | 3,736 | 54 | 0 → 0 | 890,931 |
| **Total** | | **30,008** | **26,608** | **22,096** | **366** | **2 → 6** | **5,328,943** |

The parent used 5,282,834 auxiliary coefficient probes. The shifted arm used
46,109 more, about 0.87% of that parent count. These are inspected candidate
coefficients, a lower bound on complete work, not elapsed time or a same-target
online comparison. The shifted arm stayed below its frozen 12,000,000-probe cap. The largest
observed `|k|` was 157 and the largest absolute shifted y coordinate was
54,764. The arm includes every failed query status in compressed raw shards.

The new `p=251` witness at `t=(9,21)` uses `k=19`, lifted points
`(87,4805)` and `(-36,8)`, and the rational Weierstrass coefficients
`[a₁,a₂,a₃,a₄,a₆]=[-251,-8283,-1255,-298189,108932]`. Its chord slope is
39, and both the checked Sage group law and independent exact-rational
arithmetic give `U+2V=O`. The reduced subgroup order is 61, so
`(9+2·21)/3=17 (mod 61)`; independent scalar replay yields the fixed public
point. Its sign-related row is `t=(25,13)` with `k=-19`. At `p=47`, the new
sign-related rows are `t=(10,42)` and `(24,35)` with `k=10` and `-10`.
The other two p47 rows are the prior witnesses with `k=0`. These six rows
comprise three sign-related rational curve shapes, not six independent
instances.

## Why the shift exists

Let `d=|x₁−x₂|`. Distinct centered x representatives modulo the prime `p`
give `1≤d<p`, hence `gcd(p,d)=1`. Bézout coefficients `u,v` satisfy
`up+vd=1`. Taking `k=−u(y₁−y₂)` gives
`y₁−y₂+kp=v d(y₁−y₂)`, so `d` divides the new y difference. The chosen
minimal absolute residue has `|k|≤d/2`; its height cost is therefore visible
in the saved `k` and coordinate statistics. The pinned Lean module proves
existence from `gcd(p,d)=1` and from the prime-and-range hypotheses. The
minimal representative rule is checked for every row by the independent
finite-panel audit.

## Reproduction and next test

`protocol.json` fixes the fields, input law, lift rule, auxiliary orders,
12,000,000-probe cap, and source hashes before the run. The checked repository
Sage launcher generated `sage-runtime-info.json` before executing `run.py`.
The producer's result and zero-length stderr are retained. The pure-Python
`audit.py` independently recomputes field points, generators, every shifted
lift and minimality condition, all auxiliary coefficient probes, CRT models,
all accepted group relations, scalar recovery, and uncompressed shard hashes.
It exited `PASS` with empty stderr. `SEAL.sha256` seals the protocol, sources,
raw rows, receipts, result, and audit.

The shift repairs one exact necessary condition, while the monic equality
holds on six of the 366 accepted reduced rows. A follow-up can freeze a
coefficient policy that uses the integral slope directly, then charge its
coefficient search and height growth on previously unseen fields. The current
row set is the parent's deterministic panel; the six relation counts are not
an asymptotic success-rate estimate.
