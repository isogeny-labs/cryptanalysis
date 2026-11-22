# Seven-pair affine-seed circuit on the N131 challenge curve

The seven-free-pair circuit passes a complete constructed assignment and an
independent checked-Sage group replay on the exact N131 curve. Its control
formula has **122,080 AND gates and 194,458 variables**. The current
eight-free-pair all-fiber public formula has 134,886 AND gates and 200,192
variables; this structural comparison saves **12,806 AND gates and 5,734
variables** while retaining all four raw-fiber and 32 terminal choices.
The seven-pair source has the independently counted
[2,138.64042535 labeled-tuple mean upper ceiling](../n131_w18_four_seed_sevenpair_source_20261011/RESULT.md).

The field is `GF(2)[t]/(t^131+t^13+t²+t+1)`, with curve
`y²+xy=x³+1` and subgroup order
`680564733841876926932320129493409985129`. Seven W18 slots use
rotations `0,16,...,96`. Each has a 17-bit canonical left source mask,
two affine seed bits selecting `212..215`, an exact inverse-and-trace
rationality witness for both endpoints, and a reciprocal pair output.
The seed-dependent pair equation uses the halftrace square of the selected
seed. All fourteen endpoints must occupy distinct signed-Frobenius folded
columns and avoid the selected terminal state's columns. Six halftrace-cubic
group links join their pair outputs to one of 128 exact terminal residuals.

| Constructed N131 control | Result |
| --- | ---: |
| Variables / AND gates | **194,458 / 122,080** |
| Clauses / native-XOR rows | **392,967 / 68,705** |
| XCNF bytes | **13,679,936** |
| Complete primary assignment | **3,673 variables bound** |
| Full assignment check | **392,967 clauses and 68,705 XOR rows pass** |
| Independent Sage group replay | **14 distinct folded columns; raw sum and fourfold public projection pass** |

The [source](circuit.py) binds every folded-column collision from the saved
W18 table, including the rare collisions between different masks in the
same orbit. The [control receipt](control_result.json) hashes its formula
and source, and the [checked-Sage audit](sage_audit_result.json) reconstructs
each source point from the exact curve, verifies that each recorded rotated
pair point is an allowed sum, then verifies the seven-pair sum plus terminal
and its projected public point. The [runtime receipt](sage_runtime_info.json)
records the checked local Sage build.

This first constructed assignment uses affine seed `212` in every slot.
The next correctness gate must exercise nonzero seed-selection bits in the
same complete circuit, then build the frozen ordinary-point formula and run
the unpinned query under a stated wall, CPU, and memory cap. The control
formula is not a measured ordinary-query result; the source ceiling is not
relation yield. This remains a proposal-stage component with
`candidate_id: null`.
