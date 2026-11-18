# CT198 — original frozen-48 Jacobian route cost identity
Date: 2026-11-17 America/Denver. Standing: **[pcc:unverified]**.
[Prospective protocol](CT198_ROUTE_COST_PROTOCOL.md) was committed at `8eb7fe9b704768f64bfe3a812dd65ebfdc24354d` before the audit implementation.

## Scientific result: what norm-point reuse can and cannot improve
This calculation uses the **original source-frozen** CT125 48 public Jacobian class packets, not synthetic timing and not the unauthenticated 695/701 whole corpus. The literal fixture is Git blob `9ac741668dd1ffa9632ff0d58e6f4dd9f2dd18c3`; the fixed original CT125 Rust source Git blob is `b80eb91a39ae1e87f0fcde95e52ea3d3634558bc`. There are 8 identity and 40 nonidentity packets across 2 directions × 4 cofactor sectors × 6 public scalar labels. These source records are prior producer evidence, not independent PCC verification.

The source fixture's **complete 21-field counter dictionaries**, summed exactly, give:

| CT125 event, all 48 packets | Direct composite | Literal sequential | Strongest retained-lift chain |
|---|---:|---:|---:|
| Degree-169 evaluation | 48 | 0 | 0 |
| Degree-13 evaluation | 0 | 96 | 96 |
| Transported norm doubling | 48 | 96 | 48 |
| Generic halving factorization | 40 | 80 | 40 |
| Explicit half check | 352 | 704 | 352 |
| Generic ordinate | 160 | 320 | 160 |
| Correction dictionary lookup | 48 | 96 | 48 |
| Quadratic source phi | 48 | 96 | 48 |
| Quadratic target phi | 48 | 96 | 48 |
| Source lift addition | 48 | 96 | 48 |
| Final actual norm | 48 | 48 | 48 |
| Final full-order check | 48 | 48 | 48 |

For **every** individual public packet, the direct-composite and retained-lift routes have equal counts in **all 19 non-isogeny fields**. Direct spends 1 × degree-169 and 0 × degree-13, retained spends 0 × degree-169 and 2 × degree-13. Both already spend **exactly one transported norm doubling**. The identity subgroup packets follow the same structural comparison; they must not be blended with the 40 generic rows in timing inference.

Hence under an additive model with identical-priced common stages, for one packet:

`T_retained − T_direct = C13a + C13b − C169`.

In the frozen-48 total, the same expression is multiplied by 48. Norm-price `N2_actual` **cancels identically** from the direct-vs-retained difference. Therefore even a dramatic norm-point reuse improvement over literal sequential cannot by itself demonstrate improvement over direct composite. The only distinguishing *counted* work between the two strongest routes is the degree-169 versus degree-13 pair. Per-arm cost differences not represented by counts (setup, allocation, caches, point/curve-dependent prices, memory and recovery) remain unpriced and can reverse any symbolic prediction.

Literal sequential has the same two degree-13 evaluations as retained but **48 more transported norms** across the fixture, plus repeated halving and correction work. Its integer counter vector is componentwise at least that of the retained route; this is not proof of faster wall time because the route implementations and point-dependent prices may differ.

## Operational decision
1. First price the native C169 and both C13 hops **on the same 48 operands and same host**. If C169 is cheaper than C13a+C13b, the retained chain needs a separately **measured**, end-to-end non-counter advantage; norm-point reuse alone cannot win against the direct route.
2. Price `N2_actual` and `D_padd` separately to quantify the sequential-vs-retained benefit, but do not silently use that saving in the retained-vs-direct comparison.
3. Require original authenticated 695/701 corpus, native all-48 arithmetic/counter replay, same-host paired A/A and physical A/B, full cold same-target rho, BSGS and IC with setup, transfer, target recovery, linear algebra, final verification, memory, uncertainty/CI and independent PCC before promoting any complete solver advantage.

## Reproduction and limitations
The source-only script is `ct198_route_cost_audit.py`; its tests are `test_ct198_route_cost_audit.py`, with tampered norm, C13, C169, unrelated non-isogeny fields, missing rows, duplicate labels, negative/boolean counters, and altered Git source fixture. It reuses `source_contract.validate_fixture` and reports nonpooled 8-vs-40 group counts.

From the repository root:

```sh
D=experiments/chained-transfer-public-target/primitive-pricing-01/ct192-public48-norm
python3 -S -m unittest discover -s "$D" -p test_ct198_route_cost_audit.py -v
python3 -O -S -m unittest discover -s "$D" -p test_ct198_route_cost_audit.py -v
python3 -S "$D/ct198_route_cost_audit.py" > /tmp/ct198-frozen48.json
python3 -O -S "$D/ct198_route_cost_audit.py" > /tmp/ct198-frozen48-opt.json
cmp /tmp/ct198-frozen48.json /tmp/ct198-frozen48-opt.json
```

The original 48 records were summed independently using the GitHub content connector before writing the implementation. No local Cargo/rustc is present and the original authenticated whole corpus is not accessible. GitHub scoped source CI is to be inspected for the **exact final head**, not presumed successful. No native arithmetic, EKS/Spot/GPU, paid workload, warm primitive timing, cold solve, PCC signature, or protected merge was performed. This report is an exact **counter-identity** observation with producer-only standing, not an independently verified execution or speed claim. **[pcc:unverified]**
