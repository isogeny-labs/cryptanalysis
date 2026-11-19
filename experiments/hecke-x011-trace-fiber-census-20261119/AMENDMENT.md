# Amendment: removable j-map branch at `(16,60)`

The original census classified both points with `x=16` as denominator
exceptions. Exact polynomial arithmetic shows that the pinned rational
function has a removable branch at `(16,60)` and a genuine pole at
`(16,-61)`. The corrected value is **`j(16,60)=-121` over the integers**.
The original protocol, producer, ledger, audit and result remain unchanged;
the v2 files add the correction.

Write the pinned numerator as `A(x,y)=a(x)+b(x)y` on
`y²+y=x³−x²−10x−20`. Its conjugate under `y↦-y-1` is
`A'=a-b-b y`. The exact polynomial norm is
`N(x)=a(x)²-a(x)b(x)-b(x)²(x³−x²−10x−20)`.
The [independent Sage audit](audit_v2_sage.py) proves by exact integer
division that `N(x)` is divisible by `(x−16)^11`, with zero remainder.
The pinned Lean [norm certificate](formal/NormBranch.lean) checks this
identity for all integer `x` and the exact branch evaluations; its
[proof map](formal/PROOF_MAP.md) states the local-ring bridge still to be
formalized.
At `(16,60)`, `A=0`; at the conjugate `(16,-61)`,
`A'=81402749386839761113321 ≠ 0`. The quotient's value at 16 is
`−9849732675807611094711841 = −121 A'(16)`. Because `2·60+1=121`
is nonzero in all three fields, `u=x−16` is a local parameter there,
and dividing the norm by the nonvanishing conjugate gives the local
value `A/u^11=-121`. The [v2 producer](run_v2.py) independently obtains
the same value from the order-11 local series.

| p | corrected j | absolute trace | changed fiber | archived class-list consequence |
| ---: | ---: | ---: | ---: | --- |
| 317 | 196 | 2 | 39→40 | prior 39-point list omits `(16,60)` |
| 941 | 820 | 27 | 35→36 | archived trace-50 list unaffected |
| 1009 | 888 | 49 | 15→16 | no archived comparison |

The affected p941 and p1009 prior fiber sizes in this table are obtained
from the frozen v1 histogram. The full corrected histogram is in
[result_v2.json](result_v2.json). This correction changes the scope of
the archived p317 39-column rank certificate: its arithmetic remains a
valid certificate for those 39 columns, while full-fiber rank requires
adding the omitted modular point and its relations. That is the next
matrix experiment.
