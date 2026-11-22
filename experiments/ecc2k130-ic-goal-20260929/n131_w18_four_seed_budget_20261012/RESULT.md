# Exact W18 four-seed budget fixes the target-selection requirement

The largest exact W18 pair-seed family has **133,152 signed,
distinct-column states**. Four families selected before a uniform subgroup
target therefore cover at most `133152⁴ = 314,333,578,284,751,650,816`
target-producing state tuples, a success-probability ceiling of
**4.61871681934×10⁻¹⁹** for one fixed seed tuple. Even granting every
state tuple a different target, **1,082,551,755,296,979,644 fixed seed
tuples** are necessary before the union-bound ceiling reaches one half.
This exact budget closes seed-blind tuple enumeration as the transfer path
for the fast N41 fixed-family join and quantifies the required target
concentration for a new selector.

## Source, bound and independent replay

The curve is `EC1N131Ckb1heb5f1998f20b` over
`GF(2)[t]/(t^131+t^13+t²+t+1)`, with
`y²+xy=x³+1` and prime subgroup order
`r=680564733841876926932320129493409985129`. The frozen W18 source has
131,307 rational masks, 131,068 folded columns, and
34,482,792,912 signed pair states per rotation. The source count includes
the distinct-column filter within each pair. The four-slot relation source
uses rotations `(0,32,64,96)`; cross-slot column exclusions only reduce its
target coverage. This is a source-budget component with `candidate_id: null`.

For seed `s`, let `c_s` be its signed pair-state count. A fixed four-seed
tuple `(s₀,s₁,s₂,s₃)` has at most `∏ c_si` labeled source tuples. Each
tuple determines one cofactor-four projected subgroup target. Thus for
`T` seed tuples fixed independently of a uniform subgroup target,
the success probability is at most
`min(1, T max_s(c_s)^4/r)`. Four raw preimages of a projected target do not
add another factor: each source tuple projects to exactly one subgroup
point. The bound is deliberately generous about duplicate sums, chart
failures and cross-slot column collisions.

The [frozen producer](run.py) reads the archived exact 262,144 seed counts,
verifies their digest and total, and computes the integer threshold. The
[independent audit](audit.py) reconstructs **all 262,144 counts** from the
W18 mask-to-column source: it computes the XOR autocorrelation with a
Walsh transform, subtracts same-column ordered pairs, and applies the
four-sign/unordered-pair conversion. It matched every archived count and
the maximizing seed `123000`. Both completed under one local worker; the
arithmetic producer took 0.054 s internally and the full independent
replay took 1.612 s. These are verification diagnostics on an unisolated
host, not attack runtime measurements.

| Quantity | Exact value |
| --- | ---: |
| Maximum seed / signed states `c_max` | `123000 / 133152` |
| Largest fixed two-family Cartesian half | `17,729,455,104` state pairs |
| Largest fixed four-family tuple count `c_max⁴` | `314,333,578,284,751,650,816` |
| One fixed tuple uniform-target upper probability | `c_max⁴/r ≈ 4.61871681934×10⁻¹⁹` |
| Minimum fixed tuples for a one-half union ceiling | `1,082,551,755,296,979,644` |
| Tuple tests per second needed for that count in 600 s | `1,804,252,925,494,967` |
| Illustrative 17-byte exact half-state list at the maximum | `301,400,736,768` bytes |
| Full source labeled-tuple mean `N⁴/r` before exclusions | `2077.4964736457…` |

The 17-byte list is an optimistic compact-point example with no hash-table
overhead or witness index. It describes a literal half-list implementation,
not a lower bound on every symbolic representation. The full-source mean
explains why the complete four-pair source can support relations even though
each fixed seed tuple has very small uniform-target coverage.

The exact [schedule rows](result.json) show the necessary conditional
concentration if a selector proposes few tuples. For example, one million
fixed tuples have a union ceiling of about `4.62×10⁻¹³`; a target-derived
selector examining one million tuples would need at least a
`1,082,551,755,297`-fold increase in conditional hit probability to
support one-half coverage. This is a necessary statistical target for a
selector, not a predicted achievable rate or a fixed-point claim for the
archived public Q.

## Proof status and next experiment

The [Lean proof map](PROOF_MAP.md) binds the finite-list schedule theorem
and exact integer threshold to checked Lean declarations. The structural
theorem proves that `T` fixed families with half-lists bounded by
`c_max²` cover at most `T c_max⁴` distinct targets. The numeric theorem
checks the first half-ceiling `T`. The concrete W18 maximum is checked by
the independent full-domain arithmetic replay; its definition and census
are not yet imported into Lean, so concrete-source formalization remains
partial.

The next proposed method must **derive or eliminate seed families from the
public point jointly**, with measured conditional concentration and charged
proposal cost. A seed-blind schedule, even paired with the 0.1-second N41
fixed-family join, does not supply that concentration. An eligible next gate
is an unpinned N41 public query that preserves the known ordinary relation
while rejecting complete four-seed families before their pair outputs are
enumerated. Only an exact source-bound N131 projection inside one worker,
600 seconds and 4 GiB should advance to an ordinary N131 query.
