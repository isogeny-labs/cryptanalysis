# W23 transfer gate for the fixed-basis affine kernel

The measured N41 fixed-basis kernel cannot be carried over as a direct
per-family traversal of the N131 W23 source under the frozen 600-second
one-worker cap. The exact W23 census has **1,049,218 usable edges per slot**
and maximum folded-column graph degree **3**. Even for one residual chart,
there are at least **1,100,852,116,216** ordered two-edge families with four
distinct folded columns. Visiting them all within 600 seconds requires
**1.835 billion family checks per second**. The fastest measured N41 table
arm visited **228,995 chart/family combinations per second**, a factor of
**8,012** below that required rate. At the same measured rate, one N131 chart
would take about **4.81 million seconds** before the rest of the six-pair
search. This is an explicitly cross-field rate projection, not an N131 run.

For a fixed first edge, at most `2Δ = 6` second-slot edges touch either of
its folded columns, giving the lower count `E(E-2Δ)`; the trivial upper count
is `E² = 1,100,858,411,524`. This is the two-edge instance of the graph
degree argument already written in the [W23 source proof map](../n131_w23_sixpair_density_20261016/PROOF_MAP.md).
That map records the finite-graph Lean bridge as open. The edge count and
maximum degree come from the independent complete source censuses, while
the per-family rate comes from the frozen [N41 six-arm receipt](../n41_native_half_affine_constmul_20261115/abba_result.json).

The [protocol](protocol.json) fixes those source hashes, the 600-second cap,
and the one-chart direct-traversal boundary before calculation. The
[screen](screen.py) computes the counts and rates with exact integers and
high-precision decimal arithmetic; [result.json](result.json) retains all
values. `python3 verify.py` independently rechecks the source hashes and
arithmetic. The N41 arm used a 41-bit field and an ordinary shared host; its
rate is not a measured N131 rate or an algorithm-independent lower bound.

The next method must couple the target to many two-edge source families in
one operation, or eliminate an outer source-code region before visiting
individual pairs. An N41 public-point control should retain its archived
ordinary relation and charge the complete family traversal; a separate
N131 source-bound projection must include the 131-bit field arithmetic,
chart count, memory, and unsuccessful cases before an ordinary public query.
This screen keeps `candidate_id: null` and does not change the active
single-target IC/rho objective.
