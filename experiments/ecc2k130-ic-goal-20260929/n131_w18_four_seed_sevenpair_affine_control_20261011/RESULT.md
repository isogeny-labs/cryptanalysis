# All four affine seed branches pass an N131 constructed control

The seven-pair N131 circuit now has a complete constructed assignment whose
seed sequence is **`212,213,214,215,212,213,214`**. Every clause and
native-XOR row passes, and independent checked Sage verifies the exact
pair-output equation for each seed, all seven rotated pair points, their
successive group sums, the terminal addition, and the fourfold projected
public point. This closes the nonzero seed-bit correctness gate left by the
[first control](../n131_w18_four_seed_sevenpair_circuit_20261011/RESULT.md).

The curve is `y²+xy=x³+1` over
`GF(2)[t]/(t^131+t^13+t²+t+1)`, subgroup order
`680564733841876926932320129493409985129`, curve ID
`EC1N131Ckb1heb5f1998f20b`. The deterministic [control producer](runner.py)
selects seven valid W18 pairs from the saved rational-mask and folded-column
table, one per slot, with sixteen distinct folded columns including the
frozen terminal pair. It constructs a raw target from their actual group
sum, then binds the pair masks, affine seed bits, inverse witnesses, pair
outputs, five intermediate sums, six branch bits, and one terminal choice.

| Mixed-seed constructed control | Result |
| --- | ---: |
| Seed sequence | `212,213,214,215,212,213,214` |
| Formula variables / AND gates | **194,458 / 122,080** |
| Clauses / native-XOR rows | **392,967 / 68,705** |
| XCNF bytes | **13,680,536** |
| Bound primary variables | **3,673** |
| Complete assignment check | **All 392,967 clauses and 68,705 XOR rows pass** |
| Independent checked-Sage replay | **All four seed values, pair gates, group sum, and projection pass** |

The [control receipt](control_result.json) freezes the selected masks,
seed sequence, point witnesses, circuit hash, formula hash, and assignment
counts. Its [compressed XCNF](control.xcnf.gz) is byte-replayed by the
[independent Sage audit](sage_audit_result.json), which also recomputes the
curve arithmetic from the exact field polynomial. The
[Sage runtime receipt](sage_runtime_info.json) was saved before the jobs.

This is a correctness control for the complete four-seed wiring. The next
stage must freeze the same public target and resource envelope as the
eight-pair baseline, construct the seven-pair ordinary formula, and seek an
unpinned relation. Its source-count ceiling is an exact support calculation;
ordinary-query yield and rank remain to be measured. This proposal has
`candidate_id: null`.
