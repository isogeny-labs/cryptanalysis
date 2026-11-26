= Two native horizontal charts: exact point-row census
<two-native-horizontal-charts-exact-point-row-census>
#strong[Status:] bounded negative result for the fixed `F_1009` pair;
producer-run and unverified by PCC. This follows
#link("PROTOCOL.md")[the preregistered two-chart proposal], and does not
establish a security-scale performance conclusion. \[pcc:unverified\]

#box(image("two_chart_result.svg", alt: "Exact target support and the matched source-only controls"))

== Input and relation
<input-and-relation>
Use `E/F_1009: y^2=x^3+4x+10`, its first Sage degree-5 isogeny
`phi:E->E'`, group order `r=1069`, and marked generator `G=E.gens()[0]`.
On each curve, choose both signs above the first four admissible
x-values: eight native base points per chart. For an independently
supplied nonidentity `Q`, the evaluator reconstructs the point from
`(x(Q),y(Q))`, then looks for a three-point witness for either `Q` on
the source or `phi(Q)` on the codomain. It has no scalar-label input.
\[pcc:unverified\]

A source witness checks `Q=P1+P2+P3`. A codomain witness checks
`phi(Q)=P1+P2+P3`\; the retained runner independently checks
`[5]Q=dual(phi)(P1)+dual(phi)(P2)+dual(phi)(P3)` in the source group.
This is an exact target-dependent factor-base row with nonzero target
coefficient. Its base-point logarithms are additional unknowns; a row
alone does not extract `d`. \[pcc:unverified\]

== Exact finite census
<exact-finite-census>
The #link("two_chart_census.py")[Sage runner] checks all `1068`
nonidentity `Q=[d]G`, with `d` used only by the test driver to enumerate
inputs. The #link("two_chart_census.json")[retained JSON] includes every
descriptive random-control count. \[pcc:unverified\]

#figure(
  align(center)[#table(
    columns: 2,
    align: (auto,right,),
    table.header([Arm, same total base budget where
      compared], [Supported nonidentity targets],),
    table.hline(),
    [Source native 8], [96],
    [Horizontal codomain native 8], [92],
    [Intersection of the two marked supports], [8],
    [Union of the two 8-point charts], [#strong[180]],
    [One source-native 16-point base], [#strong[510]],
    [128 random 16-point source bases, median], [534],
    [128 random split source-only 8+8 base pairs, median], [180],
  )]
  , kind: table
  )

Of 128 split source-only controls, 68 have support at least 180. The
controls use one fixed Python `random.Random(20261125)` stream and are
descriptive, not independent statistical replicates. Exact source and
codomain counts agree with the earlier
#link("../cm_joint_s4_20261123/NATIVE_THREE_SUM_REPORT.md")[native three-sum census].
The two-chart union is typical of simply splitting the same 16-point
budget into two separate eight-point triple searches; this fixed screen
does not isolate an isogeny-attributable yield increase.
\[pcc:unverified\]

The earlier
#link("../cm_joint_s4_20261123/SIGNED_THREE_SUM_CEILING.md")[signed three-sum ceiling]
bounds #emph[each] signed eight-point chart by 96 distinct nonidentity
targets. Therefore any union of two such separately searched charts has
support at most `96+96=192`, even if their supports are disjoint and
regardless of which horizontal vertices supply the bases. The observed
180 is only 12 below that ceiling, while the measured single
source-native 16-point base has support 510. This closes a
#strong[yield-only] improvement for the fixed two-chart/eight-point
allocation; it does not compare native solver cost or different
allocations. \[pcc:unverified\]

== Work and limit
<work-and-limit>
The two eight-point charts contain `2*C(10,3)=240` indexed triple
candidates, versus `C(18,3)=816` for the 16-point source base. Thus a
direct scan has fewer candidate checks per query, but also a smaller hit
set. The ratios `240/180` and `816/510` are candidate counts per
supported target under a uniform-target simplification; they omit map
evaluation, base construction, query failures, solver cost, rank, and
linear algebra. They are #strong[not] a measured cost advantage.
\[pcc:unverified\]

A full support-table implementation evaluates at least those 240 triples
during cold setup, already above the finite-instance negation-aware rho
reference `sqrt(pi*1069/4)≈28.98` group additions even if each triple
were priced at only one addition. This rules out a cold win for that
direct table construction on this small instance. It does not rule out a
compact coordinate solver or a different base allocation at a larger
instance. The earlier
#link("../cm_joint_s4_20261123/NATIVE_THREE_SUM_COST_REPORT.md")[native S4 cost report]
and
#link("../cm_joint_s4_20261123/MIXED_EQUAL_YIELD_COST_REPORT.md")[equal-yield mixed-base report]
remain the relevant solver-cost baselines; this census adds no
#strong[measured] full same-target comparison. \[pcc:unverified\]

For the #strong[same two signed eight-point charts at P-192], with
subgroup order `r` pinned in the
#link("../cm_joint_s4_20261123/README.md")[joint S4 report], the support
ceiling of 192 makes the hit probability of a uniform nonidentity query
at most `192/(r-1)`. Even one hit needs at least `(r-1)/192 ≈ 2^184.415`
queries in expectation. The negation-aware rho reference is `≈2^95.826`
additions, so the query count alone is `≈2^88.589` times larger if each
natural query costs just one addition equivalent. This is a cold
lower-bound screen for this fixed allocation and uniform-query
mechanism, not a measurement or a bound on larger bases, targeted query
oracles, or all isogeny-assisted index calculus. \[pcc:unverified\]

#strong[Decision:] retain the coordinate-input row construction as a
checked finite mechanism, but do not advance this fixed two-chart
allocation as a yield lead. A successor must predeclare a solver that
exploits native equations sufficiently to overcome the lower support,
include exact pullback and isomorphic-model controls, and account for
the shared rank and cold full cost. The existing study graphs were
checked; no verified graph-level finding warrants changing them.
\[pcc:unverified\]

== Reproduction and proof map
<reproduction-and-proof-map>
```sh
/Volumes/SSD990/cryptanalysis/sage -python research/cm_point_bridge_proposals_20261125/two_chart_census.py > /tmp/two_chart_census.json
cmp /tmp/two_chart_census.json research/cm_point_bridge_proposals_20261125/two_chart_census.json
```

The point-row identity follows from the isogeny homomorphism and
`dual(phi)∘phi=[5]`\; those statements are mathematical prerequisites
and are checked pointwise by Sage on every accepted row here. They are
not newly formalized in Lean by this result. The measured table is a
finite computation, not a theorem about all curves or all factor bases.
No PCC claim is minted because the repository\'s append-only base ledger
cannot currently pass verification; all reported results remain producer
assertions pending independent replay. \[pcc:unverified\]
