# Independent source-fidelity review: GLV cap-128 selector (T-1842)

## Bound inputs and verdict

Reviewed commit `702b680419b529a79b6415830057a47310be2b78` in `/var/tmp/cryptanalysis-glv-cap128-review-20261107`. This review compares the types of the 19 declarations from `capFor_below40` through `baseline48_le_select` with the literal selector in `src/curve.c`; it does not infer performance. The current C file is byte-identical, by SHA-256, to the source pin `e71ebecaf3a076590ddd3affa4878b4c80d85095` recorded by the live binding. No build or experiment was run for this review. The archived Lean receipt reports `lean TableBudget.lean` exit 0 and axiom prints for all 27 declarations; this reviewer did not independently reproduce machine verification. **Fidelity verdict: holds for the conditional, pure selector arithmetic**, with the input and C execution conditions below. **Proof narrative needs one factual correction** (last section).

| Input | SHA-256 |
| --- | --- |
| `src/curve.c` | `e1d624e58c54f25f9225be97481b50c0ed406cedcfdffa8ba66f01a5fbed7f63` |
| `experiments/glv-table-rule-confirm-20261022/TableBudget.lean` | `ff60c81349e98cbae472f16873ab63672005b74098721a678fc514425b55448e` |
| `experiments/glv-table-rule-confirm-20261022/LEAN_PROOF.md` | `ab863ed839221fc6479e39e4cee75fd7fb1b34e56d9c91d0887ab6f70b135a6d` |
| `experiments/glv-table-rule-confirm-20261022/check_lean_source_binding.py` | `f0eb5c9a5ed53dfeea4f504d955567a333d7904dd6a12b473a33d9af4575236e` |
| `experiments/glv-table-rule-confirm-20261022/live-source-binding.json` | `f3fba6eeb94b7930b2f0c8589060378c86194e8336e058f1cd0b616f15519c98` |
| `experiments/glv-table-rule-confirm-20261022/lean-receipt.json` | `6e4415c40eff22fb0eea9688a0d5c40def26ec5beb1be239dfdcd0c377292c04` |
| `lean-toolchain` | `d5edba4e4b8faad9c1baeadb265716d20d03be4d1a2647dc5e35b0c0325bea7b` (`leanprover/lean4:v4.34.1`) |

## C-to-Lean correspondence

On the GLV selector path C sets `sqrt_nm = ca_isqrt(n / c.m) + 1`, `lg = glv_ilog2(n) + 1`, `rbudget = sqrt_nm / (12u * (uint64_t)lg)`, `rcap = lg >= 40 ? 128 : 32`, and `rr = 8`; it doubles while both `2*rr <= rbudget` and `2*rr <= rcap`. Lean's `select s lg = loopCap (capFor lg) (s / (12*lg))` is the same arithmetic after substituting the C values for `s` and `lg`. `loopCap` unrolls four steps. Its fixed-point lemmas for both reachable caps justify replacing the C while loop by that unrolling.

The C `n < 64` branch returns before the selector, and the identity-target branch can return even earlier. For any reached selector with a defined positive `c.m`, `n >= 64`, so `glv_ilog2(n)+1` is the bit length, in `[7,64]`. The C product `12u * (uint64_t)lg` is then at most 768. `rr` starts at 8, reaches at most 128, and its guard and update products are at most 256; the 32-bit and 64-bit unsigned operations cannot wrap on these reachable values. The proof is over `Nat` and does not establish that `c.m > 0` or that `ca_isqrt(n / c.m)` computes a particular mathematical group-size estimate. Division by zero before the selector is outside the theorem; the source-binding checker checks exact text and full-file hashes, not that precondition.

## Declaration-type findings

| Declarations | Type-level source-fidelity finding |
| --- | --- |
| `capFor_below40`, `capFor_from40` | Exactly split the cap at `lg < 40` versus `40 <= lg`, with 32 and 128 respectively. In C, `lg` is a nonnegative bit length on the reached path; the Lean types are stronger by quantifying over all naturals. |
| `loopCap32_eq_tableSize`, `loopCap128_eq_tableSize128`, `loopCap32_eq_loopResult` | Encode the literal guard from start value 8 and give the correct three and five threshold cases. The cap-32 four-step result equals the predecessor's two-step result. |
| `loopCap32_fixed`, `loopCap128_fixed` | State that a fifth guard-and-double step changes nothing. Together with the threshold results, they cover the entire while loop for both C cap values. They make no statement about an arbitrary cap. |
| `tableSize128_cases`, `tableSize128_mono`, `tableSize_le_tableSize128`, `tableSize128_eq_tableSize_below32` | Correctly constrain outputs to 8/16/32/64/128, monotonicity in budget, cap-32 versus cap-128 ordering, and equality when `budget < 64`. The last declaration's name says `below32`, but its type and proof map correctly use the first new threshold, 64. |
| `select_below40`, `select_from40`, `select_eq_old_below40` | Correctly specialize `select` to the predecessor cap-32 rule below 40 bits and to the cap-128 threshold formula from 40 bits. `select_eq_old_below40` duplicates `select_below40` at the type level. |
| `select_bounds`, `select_cases`, `select_mono_budget` | Correctly bound and enumerate selected values and prove nondecrease in `s` for fixed `lg`. `select_mono_budget` calls `s` a budget in its name, but its type orders the numerator `sqrt_nm`; fixed-denominator division makes that true. |
| `old_le_select`, `baseline48_le_select` | Correctly compare results for the *same* `s` and `lg`. The former compares cap-32/divisor-12 with current cap; the latter chains the cap-32/divisor-48 baseline to it and requires `lg > 0`. These are selector-value comparisons only. |

The predecessor C blob at `8bf648dcbefe7b8131e5fb26909c77e68778332a` has divisor 12 and fixed cap 32 (`60796724ef7d7c5b3b7dfd89c29db85d5e188deb247b5d9d0bd69b84551afe20`). The baseline blob at `7cb3dce4cac9176d74afb6403048b5fabbaab834` has divisor 48 and fixed cap 32 (`e504bb18f0e80134c9ccf9abc1b7a825097286a759075090d2693ef82b406975`). These match the comparator definitions. The baseline blob also has another later selector site; this comparison applies to the GLV selector identified by the source-binding checker, not every selector in that file.

## Adverse controls and limits

I checked boundary cases directly against the definitions: budget 15/16 selects 8/16; 31/32 selects 16/32; cap 128 at 63/64 selects 32/64 and at 127/128 selects 64/128. With `lg=39`, the cap remains 32 even for budget >=128; with `lg=40`, the cap is 128. At `lg=0`, Lean division is totalized and can produce a selector value, while C never reaches this state from `n>=64`; comparisons that model a C divisor change therefore require positive `lg` where stated. For the cap-128 path, the fifth step is stopped by the cap even when budget >=256.

The archived `live-source-binding.json` reports five rejected changed-selector controls: divisor 48, threshold 41, large cap 64, small cap 64, and substituting a fixed cap in the guard. I inspected the checker code and receipt but did not execute those controls. They test literal source binding, not the Lean theorem types or runtime behavior. No independent compiler, executable, memory-safety, group-correctness, or performance check was performed.

`LEAN_PROOF.md` says, “The C loop itself multiplies only 8 and 16 by two before the cap stops it.” That is false for the cap-128 branch: for budget >=128 it also multiplies 32 and 64 by two. The theorem types and the preceding proof-map description correctly include all four doublings. Correct this narrative sentence; it does not change the scoped fidelity verdict.
