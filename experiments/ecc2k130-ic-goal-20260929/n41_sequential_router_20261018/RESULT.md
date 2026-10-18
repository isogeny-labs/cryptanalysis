# Conditional synthesis lowers the N41 router degree stage by stage

**An exact staged router leaves the single archived two-code family
on a fixed-suffix N41 ordinary residual while lowering the source-mask formula
degree from five to four, three, two, and one as earlier gates reject
families.** The first target-conditioned gate reduces 766
trace-compatible source pairs to 661; the 36 remaining labels then
admit degree-four formulas on that survivor set. After five gates,
380 families remain and degree three suffices. At stages 16 and 28,
the needed degree falls to two and one. All 37 gates leave source
index 966, the independently checked witness family in the frozen
ordinary-residual panel.

The exact source is `EC1N41Ckb1h7d5e80d3c4d0`,
`GF(2)[t]/(t^41+t^3+1)`, `y^2+xy=x^3+1`, with the two-code W8
seed-56 factor-base family from the [frozen router
work](../n41_router_degree6_coefficients_20261015/RESULT.md).
The target x-coordinate is `1819606493820`; the predecessor selected
37 quadratic coordinate products of its source outputs as exact
rejection labels. Each family has eight x-coordinates. The 16 source
mask bits are the two canonical eight-bit product masks. A label is
one if its target-selected coordinate product is zero on all eight
source outputs. Every genuine family with the target output therefore
has label zero.

The staged procedure selects the still-unapplied label rejecting the
most current families, breaking ties by label index. It then
interpolates *all remaining labels* only on families that passed the
selected gates. A binary rank calculation finds the lowest monomial
degree with full row rank; high- and low-pivot elimination each
construct an explicit coefficient vector. Every vector is evaluated
against every family in its stage domain. The [independent
audit](audit_result.json) reconstructs all 766 labels from the frozen
source, checks every staged coefficient vector and survivor list, and
recomputes selected ranks with the opposite pivot convention.

| Gates already applied | Families remaining | Least full-rank degree | Remaining gates |
| ---: | ---: | ---: | ---: |
| 0 | 766 | 5 | 37 |
| 1 | 661 | 4 | 36 |
| 5 | 380 | 3 | 32 |
| 16 | 96 | 2 | 21 |
| 28 | 14 | 1 | 9 |
| 37 | **1, index 966** | 0 | 0 |

The first frozen protocol stopped after three gates; its
[protocol](protocol_v1.json) and [result](result_v1.json) remain
unchanged. A second protocol extended the same deterministic rule to
all 37 gates. The independent audit confirms the first three selected
gates and every coefficient from the first run are an exact prefix of
the longer run. The full synthesis took **7.186 seconds** inside one
ordinary-host Python process and reached **38,174,720 bytes** peak
self RSS under its 120-second/4-GiB declared envelope. The interval
includes source loading, label construction, rank checks, two
coefficient solutions at every stage, and their exact replay; it
excludes process launch.

| Formula/work count over the same 37-gate order | Static degree-five formulas | Stage-specific formulas | Ratio |
| --- | ---: | ---: | ---: |
| High-pivot monomial occurrences in chosen formulas | 11,911 | **2,859** | 4.17 |
| High-pivot monomial evaluations, short-circuiting rejected families | 1,952,605 | **1,154,126** | 1.69 |
| Low-pivot monomial occurrences in chosen formulas | 13,999 | **3,003** | 4.66 |
| Low-pivot monomial evaluations, same short-circuit order | 2,242,949 | **1,197,038** | 1.87 |

The occurrence and evaluation counts use the declared monomial
representation; they are exact operation proxies, not measured
one-target wall speedups. Both static and staged totals use the same
gate order and the same survivor counts, so the evaluation comparison
charges the static router for its own early exits. The target-specific
synthesis and source-label preparation must also be charged online
if reused in an IC candidate. The current construction reads the
finite N41 two-code output table; it does not yet provide an implicit
N131 synthesis over its vastly larger source domain.

The [protocol](protocol.json), full [result](result.json),
[independent audit](audit_result.json), checked
[Lean proof](ConditionalRouter.lean), and [proof map](PROOF_MAP.md)
retain the exact method and its limits. `candidate_id: null` remains
correct for this router component. The next scaling gate is a
source-implicit way to compute stage labels and coefficient formulas
without enumerating code pairs, then an unpinned N41 relation query
using those formulas with all target-dependent work charged before
any N131 promotion.
