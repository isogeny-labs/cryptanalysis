# Exact five-pair sign certificates and their code-choice boundary

The public-target six-point determinant is **quadratic in five pair-output
sign bits** when the five output x-coordinates are fixed. Sixteen determinant
values determine that quadratic, and a 41-bit coordinate-linear certificate
can then reject all 32 sign assignments at once. On the frozen N41 W11
public-point source, the method certified **all 32 randomly selected
sign families**; the independently replayed ordinary relation survived
with sign mask 30.

The same certificate has a sharp boundary at source-code choice. In nine
frozen boxes with two output-root choices in each of five slots, the
determinant-variation span reached all **41 field bits after the third
root-choice tuple**. Eight boxes had no group hit among their 1,024
assignments, yet no single coordinate-linear certificate covered any of
those boxes. Across every box, exhaustive tests found **zero compatible
four-root-tuple certificate sets**. The eight ordinary boxes each have 16
explicit certificates covering consecutive root-tuple pairs; therefore
the exact certificate count for any such box lies between **11 and 16**.
This narrows the target-conditioned design: one linear certificate handles
signs effectively, while a code-choice method needs conditional or
nonlinear structure.

## Exact instance and input law

The curve is `y²+xy=x³+1` over
`GF(2)[u]/(u^41+u³+1)`, curve ID
`EC1N41Ckb1h7d5e80d3c4d0`, prime subgroup order
`549756390943`, cofactor four. The frozen public raw point is
`(1936680952394,910597499030)`. The W11 source has 281 valid pair
codes and 1,124 signed pair-output states per slot, with Frobenius
rotations `(0,0,12,12,24)`. Each accepted five-pair relation uses ten
distinct folded source columns. The source and the ordinary relation
were established in the [prior native join](../n41_w11_fivepair_native_join_20261018/RESULT.md).

The [first panel](panel.json) contains the prior independently replayed
relation plus 32 source families selected by Python RNG seed `411019`
before determinant evaluation. Selection used only exact source-state
data, ten-column disjointness, and distinct output x-coordinates. The
[second panel](code_box_panel.json) expands that positive family and the
first eight random families with one independently selected alternative
root/code per slot under seed `411020`. All 20 source columns and all
ten output x-coordinates in each box are distinct. Each box contains
`2^5` root-choice tuples and `2^5` sign assignments per tuple.
Both panels and their input hashes were frozen before their corresponding
workers ran.

## Quadratic determinant and certificate

For five pair-output points `P₀,…,P₄` and `−Q`, form the six evaluation
rows of `1,x,y,x²,xy,x³` in `L(6O)`. With six distinct finite points,
the determinant `D` vanishes exactly when
`P₀+⋯+P₄=Q`. The input panels enforce distinct x-coordinates, which
also gives distinct points. This equivalence was checked independently
against the curve group law for every tested assignment.

For a fixed output-root choice, flipping sign `bᵢ` changes only the
`y` and `xy` entries in row `i`, since on this binary curve
`−(x,y)=(x,y+x)`. A determinant term can use at most the two y-bearing
columns. Multilinearity therefore gives

`D(b)=c₀+Σᵢ cᵢbᵢ+Σᵢ<ⱼ cᵢⱼbᵢbⱼ`.

The 16 coefficients come from `D(0)`, five singleton evaluations, and
ten pair evaluations; in characteristic two,
`cᵢⱼ=D(eᵢ+eⱼ)+D(eᵢ)+D(eⱼ)+D(0)`.
For a binary-linear coordinate functional `L`, the conditions
`L(c₀)=1` and `L(cᵢ)=L(cᵢⱼ)=0` prove
`L(D(b))=1` for every sign assignment. The worker solves this
16-row binary system and saves its 41-bit mask. It also evaluates all
32 signs directly and checks each determinant against the exact curve
group sum. The independent audit rebuilds every selected pair state
from source masks and repeats every group comparison.

For multiple root-choice tuples, one shared mask must annihilate each
tuple's 15 nonconstant coefficients and the differences of its constant
term from one base constant. If those differences span all 41
coordinates, such a mask cannot exist. The pooling worker classified
all `C(32,k)` subsets for `k=1,2,3,4` in each box. An independent
low-pivot GF(2) elimination replayed **373,032 subset decisions** from
a separately exported coefficient table and verified all saved
paired-mask witnesses.

## Frozen results and resource boundaries

| Stage | Exact result | Parent wall | Sampled combined peak RSS |
| --- | --- | ---: | ---: |
| Sign-family screen | 32/32 random families certified; positive sign 30 survives | 8.519 s | 289,669,120 B |
| Two-code boxes | 9/9 spans full after third root tuple; positive box has one group hit, eight others have none | 20.824 s | 288,276,480 B |
| Independent source and group replay | 400 signed states rebuilt from 156 source codes; 10,272 assignments replayed | 5.913 s | 290,357,248 B |
| Independent folded-column audit | All 400 selected states and 9 boxes pass | 3.947 s | 265,240,576 B |
| Certificate pool | 0 compatible quadruples in all 9 boxes; 16 explicit paired masks per random box | 37.915 s | 289,521,664 B |
| Separate coefficient export | 16 coefficients for each of 288 root tuples | 17.020 s | 278,839,296 B |
| Independent rank census | All 373,032 subset decisions and saved paired masks match | 78.400 s internal Python time | See [receipt](pool_audit_result.json) |

Every checked-Sage stage used the [accepted repository launcher](sage_runtime_info.json),
one worker, a 120-second parent cap, and a 4-GiB sampled combined-RSS
cap. The pure Python rank replay had the same declared wall and RSS
limits and completed within them. These are ordinary-host component
measurements; their intervals include different work and do not form a
single-target IC online comparison. The [terminal audit](terminal_v2_result.json)
hash-binds 77 source and output artifacts, run statuses, source and
column replays, rank counts, and the Lean build. The initial scratch
launcher failed because system Python lacked `psutil`; its exact
[failure](pilot_attempt1_failure.txt) and the subsequent scratch pilot
receipts are retained separately. The repository replay supplies the
reported measurements.

The general certificate theorem and two-bit coefficient identity are
checked in [SignQuadratic.lean](SignQuadratic.lean) under pinned Lean
4.34.1; [lean.stdout](lean.stdout) contains their `#print axioms`
audit. The written determinant argument above connects those abstract
lemmas to the five-pair curve equation. The [proof map](PROOF_MAP.md)
states the remaining formalization boundary.

## Next constructive test

The certificate count lower bound of 11 for only 32 root-choice tuples
rules out one shared linear mask as the needed broad family filter.
The next target-conditioned experiment should eliminate the sign
variables **symbolically while retaining several source-code bits free**,
then test a nonlinear condition on the resulting 16 determinant
coefficients. It should preserve the public witness and reject code
regions on the same N41 W11 source before measuring an N131 source-bound
projection. A viable N131 promotion still requires an independently
replayed ordinary relation on the frozen public point within one worker,
600 seconds, and 4 GiB. This component retains `candidate_id: null`.
