# Exact W29 source-edge census and native pair-output generation

The complete fixed-seed W29 source contains **67,109,836 endpoint-valid canonical pair codes** among its `2^28` free codes. A native Gray-code producer processed the entire domain in **202.344 seconds** of source-stage time and emitted the count of **134,219,672 nonzero reciprocal pair outputs**, two per valid code, with zero quadratic failures. Its owning one-worker monitor recorded **202.595 seconds** parent wall and **28,868,608 bytes** sampled combined peak RSS under the frozen 590-second/4-GiB envelope. A separately implemented numeric-order endpoint-validity pass counted the same **67,109,836** codes over the complete domain; it took 22.967 seconds of native count time. The two runs use the same archived field arithmetic but independent enumeration and validity-loop implementations.

## Exact source and scope

The field is `GF(2)[u]/(u^131+u^13+u²+u+1)` and the curve is `y²+xy=x³+1`, ID `EC1N131Ckb1heb5f1998f20b`. The W29 source seed mask is `898618`; its canonical free-code positions are `0..18,20..28`. For code field value `w`, the partner is `w+s` with `s=898618<<1`. A code enters the count only when both field values are nonzero and both satisfy the source trace and inverse-trace conditions. The left pair slot uses Frobenius rotation 54. The product `w(w+s)` is binary linear in the 28 code bits; the native producer updates it and `w` in Gray order.

For each valid code, the producer solves the exact pair-output quadratic `C c²+p c+H=0` using a batched product inverse and the odd-degree half-trace. It checks both roots against the equation and records `quadratic_fail=0` over the full run. The separate numeric-order counter computes `w` afresh from each integer code, batches endpoint inversions, and checks both source trace predicates; it does not call the output-root routine. This count is an exact source-edge census for the declared seed and encoding. Subgroup-usable factor-base point count and folded-column count require their own exact endpoint and orbit audit and are not inferred from the edge count.

## Frozen controls and measurements

| Boundary | Codes visited | Valid codes | Reciprocal outputs | Native interval | Parent wall | Sampled combined RSS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| N41 complete source control | 1,024 | 281 | 562 | 0.001929 s | 0.244 s | 24,641,536 B |
| N131 W29 prefix | 1,048,576 | 263,477 | 526,954 | 0.918515 s | 0.928 s | 28,753,920 B |
| N131 W29 full Gray-code producer | 268,435,456 | **67,109,836** | **134,219,672** | **202.344 s** | **202.595 s** | **28,868,608 B** |
| N131 W29 independent numeric-order count | 268,435,456 | **67,109,836** | — | 22.967 s | 23.218 s | 28,999,680 B |

The N41 native output set matches all 562 outputs in the prior independently checked Sage table. For N131, the first 4,096 codes produced 1,064 valid pairs and 2,128 outputs, matching every reciprocal output in the prior Sage table. The independent Sage auditor also checked the full field trace functional (`Tr(x)=x₀⊕x₁₂₉`) and the fixture code. The complete producer receipt binds its binary, source, field kernel, full input, protocol, stdout/stderr, wall cap, and RSS samples. `audit_full.py` replayed the exact 4,096-code overlap and full-run status; `audit_count.py` compared the separately produced full count. The earlier 65,536-mask W29 sample had projected 68,308,992 valid codes; the complete count resolves that projection for this source.

The pair-output count could be stored in a compact flat array using 17 bytes per field element plus a four-byte code, or **2,818,613,112 bytes** before indexing, alignment, signs, column metadata, and process overhead. This is a representation calculation, not a measured full-pipeline memory footprint. Source production is target-independent preparation; the measured 202.595-second run is not a target online interval. This component retains `candidate_id: null` while exact subgroup point/column inventory, ordinary relation yield, matrix rank, target descent, scalar replay, and same-point rho remain open.

## Next experiment

Use the complete source census to build a compact reusable single-pair output stream or index, then test an exact target-conditioned two-pair terminal query with all W29 codes while retaining a constructed hit and an ordinary residual control. Charge source setup separately from the online query. The relation-search method must also constrain the other three pair families jointly before their Cartesian expansion; the terminal test alone cannot supply the frozen N131 ordinary relation.
