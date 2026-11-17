# CT173 — original CT126 `D` is not the CT125 norm-point runtime operation

Date: 2026-11-16 (America/Denver); continuation of CT172, [cryptanalysis #1692](https://github.com/isogeny-labs/cryptanalysis/pull/1692). **Scientific standing: [pcc:unverified].** Source-level producer audit only; no new native execution, microbenchmark, cold solve, independent signed PCC, or owner admission.

## Concrete source-level accounting defect

CT125's **actual reused** runtime calls the following within `Runtime::norm_point(to, point)`:

```rust
self.bump(|c| c.transported_norm_doubling += 1);
let target = &self.geometry.models[to].quadratic;
descend_point(curve::pmul(&target.f, &target.curve, &point, 2))
```

By contrast, CT126's `D` timer runs **only**
`curve::padd(&target.quadratic.f, e, &final_pts[i], &final_pts[i])`.
The timed call uses `padd(P,P)`, while CT125 executes `pmul(P,2)` *and* `descend_point` after the composite/two-hop output. Those are different executable code paths even though both calculate the mathematical doubled point (before descent).

At pinned crypto `isogeny_algos/src/curve.rs`, `pmul` uses an unconditional doubling `b = padd(f,c,&b,&b)` **inside each loop iteration**, including its last one. With `k=2`, the source-level control-flow trace is:

1. k=2: double `P` to `2P`; k becomes 1.
2. k=1: `padd(O,2P)` updates `r`, then double `2P` to `4P`; k becomes 0.
3. Return `r=2P`; CT125 then descends that point.

This is **two source-level doublings and one identity addition**, rather than the CT126 `D` timer's **one doubling**; optimization may eliminate dead work, so **no quantitative machine-cost ratio follows from source control flow alone**. The `descend_point` and the actual operand distribution can also change cost. Counting `transported_norm_doubling:1` therefore does **not** establish that the implementation's priced operation is CT126's `D`. The arithmetic map/equality itself is not disputed.

### Immutable source identities inspected

- CT125 optimized derivative: `isogeny-labs/cryptanalysis`, `experiments/chained-transfer-public-target/fixed-jacobian-chain-evaluator-02/derived/lib.rs`, Git blob `b80eb91a39ae1e87f0fcde95e52ea3d3634558bc` (read in CT172 branch).
- CT126 existing Rust comparator: `experiments/chained-transfer-public-target/primitive-pricing-01/src/main.rs`, Git blob `ac4146577f5019fc17674deb342eb5d9fc749715`.
- Actual math library: `isogeny-labs/crypto@4de29a113dfc1b9d32c1809820b8caa2975042a8`, `isogeny_algos/src/curve.rs`, Git blob `f933d66c2621238e2b4c8bf0be1d2c16f6d44fb1`.
- Frozen prior symbolic-model pre-registration `CT143_COST_ENVELOPE_PROTOCOL.md` is **not edited**, because retrospective protocol rewriting would hide a changed experiment definition.

## Implication for the CT143 pricing envelope

The CT143 equalities are sound *as a symbolic model* if the `d` symbol means the **complete runtime cost of the CT125 norm-point step**, not an unrelated arithmetic microkernel. For selected common arithmetic operands define:

- `a`: actual cost of the degree-169 evaluation;
- `b,c`: actual first and second degree-13 map costs;
- `n`: observed cost of `descend_point(pmul(target_curve, P,2))`, using the CT125 runtime and fixed model (with setup/dispatch accounted for separately).

Then the count-only gross route headroom is `min(a,b+c)-n`, NOT the physically measured quantity `min(a,b+c)-D_padd` until equality of their costs is established by an admitted measurement. The same caveat applies to `2n` in the literal two-hop route. Whole timing still requires corrections, initial halving, admission, setup, inverse if needed, transfer/matrix/individual-log recovery and source verification.

For the exceptional (8) and generic (40) frozen cohorts, per-direction/per-sector **input-dependent** branch behavior must be retained. A single average `D_padd` for five forward nonidentity CT126 points is neither an exact nor a defensible automatic price for all 48. Do not assert the performance conclusion changes sign without an actual paired measurement.

## Additional independent two-repository selected-data audit (source only)

A fresh connector-side **independent JS field-by-field comparison** read the exact original 48-vector object (original blob `19bc5c1ad37d55daa51a9ec95fa0af90296385c6`) from pinned crypto commit `4de29a113dfc1b9d32c1809820b8caa2975042a8`, and the optimized 48-vector object (blob `9ac741668dd1ffa9632ff0d58e6f4dd9f2dd18c3`) from CT172. Cohorts were matched by `(from,to,sector,scalar_OUTSIDE_runtime)`; all 48 public input/output keys and all non-counter fields matched. The only counter differences found in all 48 cohorts were:

| Route | Original → optimized | Frequency |
|---|---|---:|
| Direct | `degree169_elliptic_evaluation: 2 → 1`; new `transported_norm_doubling: 1` | 48 |
| Literal sequential | `degree13_elliptic_evaluation: 4 → 2`; new `transported_norm_doubling: 2` | 48 |
| Retained lift | `degree13_elliptic_evaluation: 4 → 2`; new `transported_norm_doubling: 1` | 48 |

There were **zero** other field differences in the matched 48 rows. Note that the original counters **omit the new** `transported_norm_doubling` field entirely; it is a schema addition, not an original value of zero. This comparison is independent source parsing by this producer, **not a signed independent scientific verifier** and is not a substitute for the original 695/701 raw corpus.

## Correct next experiment and acceptance criteria

1. Preserve old CT126 raw timing and CT143 envelope unchanged as a historical *proxy*; add an explicit **`N2_actual` paired timing arm** to the existing CT141-approved *Rust* pricing path, where `N2_actual` executes the *same* `pmul(...,2)+descend_point` as CT125, with matched operands, source/target model, identity/nonidentity classes and reverse direction. Also retain the old `D_padd` arm to measure the actual discrepancy. Do not benchmark a novel substitute implementation.
2. Require exact operand/result parity, order/field checks, original fixed-corpus keys, paired same-host A/A/ABBA, host/toolchain/optimizer provenance, cold setup and peak RSS. Check all 48 strata before extrapolating and do not mix results from different hosts/strategies.
3. Re-evaluate CT143 with the observed runtime operation, then run complete **cold single-target prime-field** rho, BSGS, IC and transferred candidate with all setup/transfer/LA/recovery/verification charged. Require `baseline/candidate > 1` with proper uncertainty and an independently signed PCC.
4. Do not invoke CT141 manually, start EKS/Spot/GPU, change the immutable original corpus/CT125 derivative, bypass red CI/artifact/PCC/ledger checks or declare speedup. Current owner STOP remains active.

**Disposition:** The prior `D` is an instrumented arithmetic *proxy*, not the exact runtime norm-point cost. This is a **measurement-design defect**, not a demonstrated runtime regression or cryptanalytic advantage. [pcc:unverified]
