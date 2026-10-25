# N41 two-half affine gate on the four-code traversal

The affine gate rejects **248,145 of 248,640** frozen first-two-code families before source-product lookup while preserving the unique exact seven-pair witness. It uses the fact that the quadratic resultant is affine-linear in each bit of the third-pair product. Splitting the eight first-two sum roots into two sets of four keeps each span below the 41-dimensional field; a single span over all eight roots has full dimension on this workload and provides no rejection.

## Exact workload and method

The field is `GF(2^41)` with modulus `t^41+t^3+1`; the curve is `y^2+xy=x^3+x^2+1`, curve ID `EC1N41Ckb1h7d5e80d3c4d0`, and the DLP subgroup order is `549756390943`. The frozen raw target is `(1970584690684,115750356512)`. The last three pair states are fixed at IDs `(14,109,51)`, and the fourth pair ranges over all 160 states in [target_table.json](../n41_four_code_suffix_quotient_20261024/target_table.json). Every chart is paired with the 1,554 admissible first-two code families in `cases.jsonl`, yielding 248,640 families. The third pair has 40 admissible source products in a seven-dimensional binary span.

For each first-two sum root and residual target chart, the exact third-product inverse is

`R(p) = c0 + c1*p + c2*p^2`,

where `c0`, `c1`, and `c2` are the frozen quadratic-inverse coefficients implemented in [affine_gate_run.py](affine_gate_run.py). In characteristic two, `L(p)=c1*p+c2*p^2` is additive. For each four-root half, the program forms the binary span of its four sets of `L(b_j)` for the eight recorded source-product basis generators, plus the three differences between root constants and the half's anchor constant. It rejects the family only when the anchor is outside **both** spans. Membership in either span is necessary for an actual source product at a root in that half. The basis has eight generators and rank seven; each half's measured span rank was 30 or 31.

The input hashes, runtime receipt, and expected workload are fixed in [affine_gate_protocol.json](affine_gate_protocol.json). The command was:

```sh
./sage --runtime-info > experiments/ecc2k130-ic-goal-20260929/n41_cubic_product_inverse_20261024/affine_gate_runtime_info.json
./sage -python experiments/ecc2k130-ic-goal-20260929/n41_cubic_product_inverse_20261024/affine_gate_run.py
./sage -python experiments/ecc2k130-ic-goal-20260929/n41_cubic_product_inverse_20261024/affine_gate_verify.py
```

The measured target-dependent interval starts at the first chart/family screen and ends after all 160 charts and survivor source-product checks. Input loading, source-product and case preparation, process launch, and the final point replay are outside that interval. The independent verifier rechecks the frozen hashes, output arithmetic, exact inverse hit, target group sum, and 14 distinct folded columns. The run used an ordinary shared host; it has no Tier 0 or Tier 1 isolation receipt.

## Result

| Frozen N41 four-code screen | Recorded value |
| --- | ---: |
| Residual charts | 160 |
| First-two-code families | 248,640 |
| Half-0 / half-1 surviving families | 258 / 237 |
| Families surviving either half | **495 (0.199083%)** |
| Families rejected | **248,145 (99.800917%)** |
| Source-product hits | `(fourth_state=0, left_code=24, right_code=37, root_index=2, third_code=10)` |
| Exact witness state IDs | `(97,151,42,0,14,109,51)` |
| Distinct folded columns in witness | 14 |
| Target-dependent loop | **503.842466666 s** |
| Source/case setup | 4.433524208 s |
| Sampled process RSS | 266,944,512 bytes |

The full indexed group traversal for this frozen target recorded 22.708110291 s wall time, including its 0.582576999 s setup, in [traversal_result.json](../n41_four_code_suffix_quotient_20261024/traversal_result.json). The affine Sage screen therefore has a higher measured component cost despite its selectivity. These two ordinary-host runs have different cost boundaries and no isolation receipt; they are diagnostics for the next implementation experiment, not an IC-versus-rho pair. The next concrete step is a native field/rank implementation with the same frozen inputs and exact witness check, followed by a matched traversal comparison. The constructed N131 control can then test the identical gate before a public-target producer is timed.

The complete run is in [affine_gate_result.json](affine_gate_result.json); terminal output is [affine_gate_stdout.txt](affine_gate_stdout.txt), and the independent replay is [affine_gate_verify_stdout.txt](affine_gate_verify_stdout.txt). The run result is a point-decomposition stage diagnostic with `candidate_id: null`; no complete IC candidate or one-target online comparison has been formed from it.

## Proof map

The [AffineGate.lean](AffineGate.lean) module uses the pinned `leanprover/lean4:v4.35.0` toolchain. `lean AffineGate.lean` completed with no errors; [the axiom audit](affine_gate_lean_stdout.txt) for all three declarations reports only `propext`, `Classical.choice`, and `Quot.sound`. The [build receipt](affine_gate_lean_receipt.json) records hashes; `lean4checker --fresh` was unavailable.

| Mathematical result | Lean declaration | Exact hypotheses and status |
| --- | --- | --- |
| `p ↦ c1*p+c2*p²` is additive | `AffineGate.image_add` | Any commutative ring with `2=0`; checked. |
| The image of a selected product-basis sum is the sum of selected images | `AffineGate.image_sum` | Same ring; checked by induction. |
| A genuine root places the half anchor in the generated binary span | `AffineGate.true_witness_passes_half` | Selected elements belong to the source basis; the root shift and every basis image are in the gate's generator list; the exact quadratic resultant vanishes; checked. |
| The common-root quadratic inverse vanishes for an actual third-pair state | `QuadraticInverse.common_root_resultant_zero` | Characteristic two and cancellation at the excluded factor; checked in the existing module. |

The Lean statements prove the lossless span implication. The concrete binary-curve charts, exact first-two roots, source products, and group identity are checked by the Sage producer and verifier. A full Lean definition of the curve and chart map remains a separate formalization step.
