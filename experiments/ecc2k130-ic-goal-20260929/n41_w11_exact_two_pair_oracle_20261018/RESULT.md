# Exact implicit two-pair membership and serial work on N41 W11

**The second source pair can be recovered from a target-derived output
point without a two-pair table.** On a positive residual from the
independently replayed N41 public relation, the source-product inverse
oracle found codes `(253,63)` after 279 first-pair states and 0.0139
seconds of target-dependent checked-Sage arithmetic. It exhaustively
checked the frozen public raw point in 0.0389 seconds and found no
two-pair decomposition. A separate direct group join confirmed exactly
one compatible positive witness and zero public-point witnesses.

The same residual-by-residual architecture has an exact work boundary:
applying it serially to the frozen native five-pair search path would
require **442,911,355 first-pair candidate checks**. The native path
made 394,050 right-family queries before its first hit; 394,049 were
exact misses. Compact storage alone therefore does not provide the
whole-family rejection needed for a fast full relation search.

## Exact instance and algebra

The field is `GF(2)[u]/(u^41+u³+1)` and the curve is
`y²+xy=x³+1`, curve ID `EC1N41Ckb1h7d5e80d3c4d0`, subgroup order
549,756,390,943 and cofactor four. The width-11 fixed-seed source has
281 canonical valid codes, four signed pair states per code and seed
mask 56. The two rightmost pair slots have Frobenius rotations 12 and
24. The positive input is the group residual
`R=(1434452595080,1460136977354)` from the independently verified
[unpinned N41 relation](../n41_w11_fivepair_native_join_20261018/RESULT.md).
The second frozen input is that experiment's public raw point
`Q=(1936680952394,910597499030)`.

For a pair output reciprocal `u=1/x` and source product `p`, the exact
source equation `C u²+p u+H=0` gives

`p=C u+H/u=C/x+H x`.

Frobenius rotation applies to both sides. For each first-pair point
`P`, the oracle computes the target-conditioned second point `V=T−P`,
recovers its rotated product from `x(V)`, solves the 10-dimensional
product-code map, checks source validity and folded-column exclusions,
and compares `V` with the four exact signed outputs of that code. It
stores 1,124 first-pair states and a 1,024-entry product-code map.
All 1,124 signed source outputs passed the source-product equation in
the [frozen checked-Sage run](inverse_result.json).

| Frozen arm | Target-dependent outcome | Examined first states | Target-dependent arithmetic |
| --- | --- | ---: | ---: |
| Verified relation residual | Exact hit at state IDs `(278,74)`, codes `(253,63)` | 279 | 0.0139 s |
| Frozen public raw point | Exact miss | 1,124 | 0.0389 s |

Source enumeration and map construction took 24.382 seconds before
these target-dependent intervals. The checked-Sage process reported
259,112,960 B raw maximum RSS; this includes the Sage runtime and is
not an algorithmic table-size measurement. The [independent direct
join](inverse_audit_result.json) rebuilds both signed state lists from
the prior frozen input and checks the hit and miss with the curve group
law, without using the source-product inverse formula.

## Exact free-code SAT control

The [positive fixture](fixture.json) fixes only the residual point for
the solver query; both source codes, their pair roots and signs remain
free. The exact two-pair circuit enforces each source inverse and trace
condition, both pair quadratics, the target S3 link, unequal codes and
all five known cross-code folded-column collisions. Its positive
assignment satisfies all 10,185 CNF clauses and 810 native XOR rows.
The [build](build_result.json) has 4,315 variables and 3,321 AND gates.

One CryptoMiniSat 5.14.7 worker reached the frozen 120-second parent
wall cap with `BOUNDED_UNKNOWN`; the [query receipt](query_result.json)
records 120.302 seconds and 169,132,032 B sampled combined peak RSS,
with no terminal SAT or UNSAT line. This positive control shows search
difficulty for the compact exact encoding despite a complete satisfying
assignment. It is a stage diagnostic on an ordinary host.

## Full-path work boundary and next test

The prior native join examined 396,919 random probe indices, skipped
2,869 at its early code filter, and found its only right-family hash hit
on the final residual. Thus 394,049 complete residual queries had no
right pair. A serial call to the exact implicit oracle would examine all
1,124 first states on each miss and 279 on the final positive query:

`394049×1124+279 = 442,911,355`.

The [frozen work receipt](work_result.json) binds those counts to the
native source and query; the [proof map](PROOF_MAP.md) gives the checked
recurrence and source-inverse theorem. This is an exact count for the
declared serial reuse policy on that residual order, with no wall-time
extrapolation or cross-residual batching. The
[terminal verification](verification_result.json) binds every protocol,
solver cap, completed oracle query, independent group audit and work
count.

For N131 width 33, the exact embedded width-20 source already has
528,180 signed pair states. A complete miss in the same serial inverse
architecture must therefore inspect at least that many first-pair states
for **one** target residual. The [frozen transfer receipt](n131_projection_result.json)
uses the independently counted source and the previous width-33 subset
proof. Its scope is complete misses under this serial scanning policy;
the receipt reports operation counts without extrapolating wall time.

The next target-conditioned method must reject blocks of still-free
first-pair codes before scanning their signed states. Its gate should
preserve the exact positive residual, measure whole-block rejection on
ordinary target-derived residuals, and charge construction plus query
work. The N131 public-point gate remains a separate experiment;
`candidate_id` stays `null` while the full IC pipeline is unresolved.
