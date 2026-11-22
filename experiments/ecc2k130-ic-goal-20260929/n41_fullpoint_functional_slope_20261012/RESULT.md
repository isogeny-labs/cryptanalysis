# Functional slopes close the N41 control while public source selection remains active

**Computing every affine slope and intermediate point from the selected source states made the frozen positive N41 ten-pair control SAT in 0.524 seconds.** The same control in the free-slope full-point circuit reached its 30-second parent cap. The unpinned query on the same public point and source remained active until its 180-second cap. This isolates a propagation gain in forward point arithmetic and places the remaining search work in choosing source states from the public target.

## Exact circuit and workload

The curve is `EC1N41Ckb1h7d5e80d3c4d0`, `y²+xy=x³+1` over `GF(2)[t]/(t^41+t³+1)`, with subgroup order `549756390943` and cofactor four. The target is the frozen public point `(920359962848,755404565011)` through all four raw preimages. Ten signed W8 pair slots have 140 states each at rotations `(0,7,14,21,28,35,0,7,14,21)`; their source edges must be distinct. The positive control pins only ten state choices and one raw-preimage flag. The public formula leaves them all free. This is a point-decomposition component with `candidate_id: null`.

For each nonexceptional link, compute `d=x₁+x₂`, require `d≠0`, compute `d⁻¹` through the frozen Itoh–Tsujii circuit, and set `λ=(y₁+y₂)d⁻¹`. Then compute `x₃=λ²+λ+d` and `y₃=λ(x₁+x₃)+x₃+y₁`. Every slope and intermediate coordinate is a function of the source choices. The known relation stays inside this chart; links with equal input x-coordinates require separate handling in a complete general solver. The full final `(x,y)` must match one selected raw target preimage. The [proof map](PROOF_MAP.md) links the inherited checked nine-link theorem and records the open binary-field/curve-law formalization bridge.

The [frozen protocol](protocol.json) binds the same public input, source and solver as the [free-slope predecessor](../n41_fullpoint_balanced_sat_20261012/RESULT.md), plus the exact inverse and arithmetic-generator source hashes. Both variants use one CryptoMiniSat worker, a 4-GiB combined RSS ceiling, and 30/180-second parent caps for control/public searches. Formula building and positive assignment checks are separate from the solver intervals. CPU wall observations are exploratory without host isolation.

| Frozen N41 formulation | Free slope | Functional slope |
| --- | ---: | ---: |
| Variables | 33,868 | 121,456 |
| AND gates | 16,956 | 67,698 |
| CNF clauses, public | 174,583 | 325,702 |
| Native-XOR rows, public | 14,401 | 52,354 |
| Serialized public XCNF | 3,108,600 B | 7,034,401 B |
| Pinned positive control | `PARENT_TIME_CAP`, 30.016 s | **SAT, 0.524 s** |
| Unpinned public query | `PARENT_TIME_CAP`, 180.036 s | `PARENT_TIME_CAP`, 180.028 s |

| Functional-slope arm | Terminal result | Solver wall | Sampled combined RSS | Restarts | Validation |
| --- | --- | ---: | ---: | ---: | --- |
| [Pinned control](control.json) | `SAT` | 0.524 s | 121,946,112 B | 1 | 325,713 CNF and 52,354 XOR rows; ten states, distinct edges, nine group links, raw preimage 1 |
| [Unpinned public](public.json) | `PARENT_TIME_CAP`, no SAT/UNSAT line | 180.028 s | 126,746,624 B | 252 | Archived terminal and resource audit |

The [independent audit](audit.json) rechecks the source and solver hashes, formula headers and row counts, exact eleven control-only unit clauses, model literals against every control row, all log hashes and statuses, and the control group sum with separate integer-field arithmetic. It also rebuilds the control formula byte for byte. Its [read-only checker](verify.py) can be rerun against the archived evidence without modifying the receipt. The frozen control model selects state IDs `(76,101,87,53,61,64,2,70,29,108)` and raw preimage 1.

## Next method gate

Functional forward arithmetic now closes the positive control, but the unpinned public search still expends its cap on source selection. The next candidate needs a **target-derived filter on groups of source-state families before their ten choices are expanded**. It should preserve the checked N41 relation, count whole families rejected and all target-dependent work, then find an unpinned N41 row with independent point and folded-column replay. A source-bound compact W18 projection under one worker, 600 seconds, and 4 GiB is required before promoting an N131 public query; later gates are novel rank, target descent, and the matched same-point rho comparison.
