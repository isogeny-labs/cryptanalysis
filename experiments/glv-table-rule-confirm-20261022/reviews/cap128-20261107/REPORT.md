# Independent review: current GLV size-dependent table cap

**Finding, 2026-11-07.** The 19 new named Lean theorems in `TableBudget.lean` faithfully formalize the conditional arithmetic of the pinned `src/curve.c` selector: cap 32 for `lg<40`, cap 128 for `lg>=40`, a divisor-12 budget, start value 8, and four possible doublings. The new selector equals the previous cap-32 selector below 40 bits and cannot select a smaller table for the same `sqrt_nm` and `lg`. This review checks the selector claim; it does not independently replay the cap-selection performance experiment.

## Pinned evidence and checks

- Target cryptanalysis `main` `702b680419b529a79b6415830057a47310be2b78`; full input hashes and scope are in `REVIEW_PLAN.md`. The target `src/curve.c` SHA-256 is `e1d624e58c54f25f9225be97481b50c0ed406cedcfdffa8ba66f01a5fbed7f63`, equal to the live receipt's source pin `e71ebecaf3a076590ddd3affa4878b4c80d85095`.
- Fresh `ELAN_TOOLCHAIN=leanprover/lean4:v4.34.1 lean TableBudget.lean` exited 0. All 27 printed declaration axiom sets contain only `propext` and `Quot.sound`; the eight older theorems and 19 new ones are included. The reviewed file contains no `sorry`, custom `axiom`, `unsafe`, or `native_decide`. `LEAN_SHA256SUMS` passed all seven entries. See `machine/` for the log, checks, and hashes.
- Fresh `python3 check_lean_source_binding.py --live` exited 0. It rejected five changed-selector controls: divisor, threshold, large cap, small cap, and fixed guard cap.
- The blind arithmetic report derives the 8/16/32 and 8/16/32/64/128 threshold tables without source or proof access. The separate source-fidelity report checks all 19 theorem types against C without blind-report access. Their source lists and attestations are beside the reports.

## Scoped mathematics and source correspondence

| Budget `b` | cap 32 | cap 128 |
|---:|---:|---:|
| `b<16` | 8 | 8 |
| `16<=b<32` | 16 | 16 |
| `32<=b<64` | 32 | 32 |
| `64<=b<128` | 32 | 64 |
| `128<=b` | 32 | 128 |

The C loop starts at 8 and doubles under both the budget and cap guards. Four changing steps suffice at cap 128; the fifth is fixed. In the C selector path, `n>=64` gives `lg=glv_ilog2(n)+1` between 7 and 64. Substituting the C `sqrt_nm` and `lg` into Lean's `select` gives the same integer threshold rule, provided C's prior `n/c.m` division is defined. `c.m>0` is an external invariant that the Lean theorem does not establish. The products in the selector guard and update stay within C integer ranges on the reached path, as detailed in the source review.

The blind reviewer tested thresholds 15/16, 31/32, 63/64, and 127/128, and the `lg=39/40` branch. At `lg=0`, Lean's total natural division is not a model of C division by zero; the comparison to the divisor-48 baseline explicitly assumes `lg>0`. Monotonicity applies to the numerator for a *fixed* `lg`, not to `lg` itself; the blind review gives counterexamples to monotonicity in `lg` and to nearby strict claims. `diagram.svg` depicts the proved threshold rule, not measured speed or counts.

## Finding and next correction

`LEAN_PROOF.md` says the C loop multiplies only 8 and 16 by two before the cap stops it. That holds for cap 32 but is false on the cap-128 path: it can also multiply 32 and 64. The source theorem, C code, and earlier paragraphs describe all four steps correctly. Correct the narrative sentence in a separately scoped edit; the reviewed theorem types remain valid.

This proof review neither certifies the recorded 40–48-bit operation-count or wall-time results nor checks the solver's group-law correctness, `ca_isqrt`, or general memory safety. Those empirical and code questions need their own pinned raw-row and executable review. Existing performance graphs are unchanged because this review generated no new measurement.
