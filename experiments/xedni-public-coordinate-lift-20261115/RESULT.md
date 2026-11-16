# Public-coordinate rational lifts in a fixed integer window

The frozen public-`x` rule inspected 69,230 integer candidates across all
3,318 points in the eight larger-order subgroups. It found 14 rational
lifts: exactly `P=(2,2)` and `−P=(2,−2)` in seven fields, and none in the
cofactor-two field. The 14 ordered pairs with two distinct lifted points
produce 14 rational relations, all with coefficient vector `(1,1)` and
independent scalar replay of the public target fixture.

| Field `p` | Subgroup `q` | Point lifts | Candidate `x` probes | Ordered lifted pairs | Rational relation hits |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 313 | 331 | 2 | 6,890 | 2 | 2 |
| 421 | 439 | 2 | 9,158 | 2 | 2 |
| 431 | 419 | 2 | 8,738 | 2 | 2 |
| 547 | 571 | 2 | 11,930 | 2 | 2 |
| 571 | 599 | 2 | 12,518 | 2 | 2 |
| 593 | 313 | 0 | 6,552 | 0 | 0 |
| 617 | 293 | 2 | 6,092 | 2 | 2 |
| 677 | 353 | 2 | 7,352 | 2 | 2 |
| **Total** | | **14** | **69,230** | **14** | **14** |

For each public reduced point `R_t=Q−tG`, the rule centers its `x` residue,
then tests shifts `0,−1,+1,...,−10,+10` for an integer `x` with
`x³−x−2` an exact nonnegative square. It accepts the first integer `y`
whose reduction equals the public `y`. All 3,296 nonidentity failures,
eight identity rows, successful shifts, and per-point probe counts are
retained in deterministic gzip JSONL shards. The point rule uses no target
scalar or rational generator coordinate in its search.

The seven positive fields have lifts at offsets `t=16` and `t=18`, giving
`P` and `−P`. Thus `P+(−P)=O`; after reduction, the fixed vector `(1,1)`
gives `2w=t₁+t₂ (mod q)` and replays `w=17`. Every rational hit is also a
publicly testable reduced-group relation. The frozen 14-vector primitive
family incurred 196 rational group tests on the 14 admitted ordered pairs;
its other vectors produced no rational hits in this window.
The structural reduction and scalar-recovery implications for finite
coefficient vectors are checked in the earlier Lean declarations
`XedniDirectRelation.finite_group_identity` and
`XedniDirectRelation.finite_relation_recovers`; this run evaluates
their `(1,1)` case on the saved points.

The recorded 69,230 probes build each point lift once and reuse it across
ordered pairs. The full independent two-offset schedule has 1,471,112
ordered queries. If each pair reconstructed both lifts without reuse, its
probe charge would be **derived** as 61,406,948 candidate `x` tests; that
schedule was not executed. These are exact finite-window yield and probe
counts, with no isolated wall-time comparison or general success-rate
estimate. A wider or different public lift law remains a separate method.

## Verification and next falsifier

`protocol.json` froze the eight-field input hash, complete point law, shift
order, first-success rule, and coefficient family before the run. The
pure-Python producer saved every status and exact rational relation. The
repository's checked Sage launcher saved `sage-runtime-info.json` and
independently replayed all 3,318 point searches and 196 rational group
tests, including reduction and scalar replay. Both stderr files are empty.
`SEAL.sha256` binds the source, protocol, raw rows, and results.

The next falsifier should vary the public-coordinate lift law under a frozen
search budget, retaining unsuccessful point searches. A rational model with
denominator search or a vector-dependent curve choice could find lifts that
this integer-`x` window misses; its extra candidate work and any rank or
coordinate-radius measurement must be charged on the same public queries.
