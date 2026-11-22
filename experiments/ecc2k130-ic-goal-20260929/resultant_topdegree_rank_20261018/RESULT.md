# Full-rank degree-four coefficients of the target-conditioned resultant

**The N131 W33 resultant's highest-degree coefficient vectors span all
131 output bits as soon as two first-code bits remain free.** This holds
for both the frozen constructed positive and the frozen public raw
point. It rules out a nonzero binary-linear output projection that
removes every degree-four term from this joint two-pair equation. The
independent Sage field and GF(2)-matrix replay matches the pure-integer
binary-field rank computation on every frozen row.

For source-product bases `P_i,Q_j`, define
`A_ij=P_i²P_j+P_iP_j²` and `B_uv=Q_u²Q_v+Q_uQ_v²`.
The coefficient of `x_i x_j y_u y_v` in the 13-term resultant is
`c₃₃ A_ij B_uv`. The source-code block offset does not occur in this
degree-four coefficient. On N131, the 496 `B_uv` values alone have
binary rank 131. The frozen `c₃₃` and `A_01` are both nonzero, so
their scalar multiples already give a full-rank degree-four family
at first-code width two. The [proof map](PROOF_MAP.md) records the
checked Lean span-to-projection implication and its concrete bridges.

| Frozen source and target | Rank of second-source cube pair coefficients | Joint degree-four rank at first-code widths |
| --- | ---: | --- |
| N41 W11, positive residual | 37 of 41 | `k=2`: 37; `k=3,4,5`: 41 |
| N41 W11, ordinary residual index 1 | 37 of 41 | `k=2`: 37; `k=3,4,5`: 41 |
| N131 W33, constructed positive | **131 of 131** | `k=2,3,4`: **131** |
| N131 W33, frozen public raw point | **131 of 131** | `k=2,3,4`: **131** |

The N41 field is `GF(2)[u]/(u^41+u³+1)` with seed `s=112` and pair
rotations `(12,24)`. The N131 field is
`GF(2)[u]/(u^131+u^13+u²+u+1)` with seed mask `898618` and pair
rotations `(0,18)`; both use `y²+xy=x³+1`. The curve IDs are
`EC1N41Ckb1h7d5e80d3c4d0` and `EC1N131Ckb1heb5f1998f20b`.
The exact 13-term coefficients and public points are hash-pinned in
[protocol.json](protocol.json). `candidate_id: null` records the
unresolved complete IC method.

The [rank result](result.json) stores the source pair coefficient,
`c₃₃`, all independent second-source pivot vectors, and pivot labels
for each joint block width. The [Sage audit](audit_result.json)
reconstructs both binary fields independently and uses Sage GF(2)
matrix rank for every row. The rank producer took 1.061 seconds after
its checked launcher startup; the independent Sage audit command
took 8.28 seconds including launcher and import. These are ordinary-host
algorithmic diagnostics. [verify.py](verify.py) checks all pinned
inputs, rank pivots, the independent audit, and the Lean axioms log;
its [receipt](verification_result.json) passes.

The earlier [joint Gröbner panel](../joint_block_gb_20261018/RESULT.md)
completed N131 width-three positive and public blocks but reached a
600-second search cap on the width-four constructed positive. The
full-rank result explains why taking a trace or linear combination of
output bits cannot remove that block system's top degree. A useful
next experiment must test a nonlinear relation among output equations,
such as low-degree Macaulay syzygies that cancel the quartic terms while
preserving every zero, and charge the resulting equation count and
rank before a bounded N131 solver query.
