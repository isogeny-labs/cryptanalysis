# Independent source-fidelity review: GLV table selector

**Verdict: holds for the stated, conditional selector-arithmetic claim.** At repository commit `927d1eada55ff51e87b89930cad48672147e0929`, the eight Lean theorem *types* describe the same threshold selector as the `glv_rho_solve` C loop, provided `s` denotes the C value `ca_isqrt(n / c.m) + 1`, `lg` denotes `glv_ilog2(n) + 1`, and both arms receive the same values. The theorem `loop48_le_loop12` then says only that replacing 48 with 12 cannot decrease the selected table size. This review does not independently run Lean, compile C, replay rows, or infer an operation-count improvement from the theorem.

## Source identity and literal rule

- The exact target-commit `src/curve.c` SHA-256 is `60796724ef7d7c5b3b7dfd89c29db85d5e188deb247b5d9d0bd69b84551afe20`. It equals the `8bf648dcbefe7b8131e5fb26909c77e68778332a` blob and `live-source-binding.json` claim. The earlier `42761f85b06242cb54f2a5fa405c723451897503` C blob hashes to `3f3a100d635d814bdfa0f6624a40b9d77c9c564f65db2bbc568dcd4b55285efe`; the baseline `7cb3dce4cac9176d74afb6403048b5fabbaab834` hashes to `e504bb18f0e80134c9ccf9abc1b7a825097286a759075090d2693ef82b406975`.
- Target `src/curve.c:746-751` sets `sqrt_nm = ca_isqrt(n / c.m) + 1`, `lg = glv_ilog2(n) + 1`, `rbudget = sqrt_nm / (12u * (uint64_t)lg)`, `rr = 8`, then doubles while `(uint64_t)rr * 2 <= rbudget && rr * 2 <= 32` and assigns `c.r = rr`. The historical 42761f85 blob has the same selector at lines 609-614. The 7cb3dce baseline has the same loop at lines 605-610 with divisor 48. `PROTOCOL.md` calls this `sqrt(n/m) / (c · log2 n)` informally; the literal C expression uses integer division, `ca_isqrt` plus one, and integer `floor(log2 n)` plus one.
- `check_lean_source_binding.py` pins hashes and requires one exact six-line selector snippet in each historical file. Its `--live` mode checks the working C file against the 8bf648dc blob, not the target commit ID; the separately computed target-commit hash establishes the exact content match here. The checker also rejects changing the current divisor to 48 or cap to 64. Its text checks alone do not establish C semantics, but the full-file hashes prevent unnoticed changes to the pinned files.

## Declaration-by-declaration correspondence

`TableBudget.lean` defines `tableSize(b)` as 8 for `b < 16`, 16 for `16 <= b < 32`, and 32 otherwise; `step(b,r)` as the exact C double guard; and `loopResult(b)` as two steps from 8. With the C cap, the only successful doubles are `8 -> 16 -> 32`.

| Public theorem type | Source-fidelity finding |
| --- | --- |
| `loopResult_eq_tableSize` | Holds as a formula: the C guard fires at budgets 16 and 32, giving exactly the three cases. |
| `loopResult_fixed` | A further guard check cannot double 8 below budget 16, 16 below 32, or 32 past the cap. Deterministic repetition makes this the loop's terminal value. |
| `tableSize_cases` | Matches the only three reachable C values, assuming the selector is reached. |
| `loopResult_bounds` | Bounds 8 through 32 agree with the C start and cap; the case theorem is stronger. |
| `tableSize_mono` | The threshold formula is nondecreasing in budget, as needed for the same-input comparison. |
| `budget48_le_budget12` | For natural `s` and `lg > 0`, integer quotient by `48*lg` is at most quotient by `12*lg`; this matches the two C divisors when arithmetic is defined. |
| `table48_le_table12` | Applies monotonicity to the two C-style integer budgets. |
| `loop48_le_loop12` | Combines the loop bridge and quotient comparison. It establishes no direction for runtime or operation counts. |

## Input and C arithmetic boundary

- `glv_rho_solve` returns before constructing this selector when `n < 64` (`src/curve.c:687-699`). Its `glv_ilog2` starts at -1 and increments once per nonzero right shift (`src/curve.c:29-37`), so for any reached `n` in `uint64_t`, `lg` is an integer from 7 to 64. Thus the C `12u * (uint64_t)lg` and historical `48u * (uint64_t)lg` are positive and at most 768 and 3072, respectively; the usual arithmetic conversion yields `uint64_t` multiplication. There is no overflow in either product on this reached path. `rr` is `uint32_t`; the guard's cast makes its first product `uint64_t`, and its uncast second product and `rr *= 2` involve only 8, 16, and at most 32 before termination. No overflow occurs in those operations.
- The Lean file deliberately accepts arbitrary natural `s` and positive `lg`; it neither derives them from `n` nor proves `c.m > 0`. The C file assigns `c.m = g->aut_order` at line 712, without a local nonzero check before `n / c.m`. If that external invariant fails, C division is undefined and there is no C selector outcome to which the theorem applies. The review cannot establish the invariant from the permitted files. Likewise, the proof does not model the implementation of `ca_isqrt`, compiler behavior, or group-order validity.
- The receipt `lean-receipt.json` reports exit 0 and standard axioms for all eight declarations under `leanprover/lean4:v4.34.1`, agreeing with the target `lean-toolchain` and the exact Lean source hash `823903d27e906feccfe40f29df7feb7a23669b0c96d0bdc1f79ff0e3bddf93b4`. This is producer evidence, not a fresh kernel check by this reviewer.

## Adverse cases and wording issue

- At budgets `0, 15, 16, 31, 32, 63, 64`, the formula and cap-32 loop give `8, 8, 16, 16, 32, 32, 32`. A wrong cap of 64 gives 64 at budget 64, violating `tableSize_cases` and `loopResult_bounds`; the exact-snippet checker rejects this mutation.
- With `s=2688, lg=7`, divisor 48 gives budget 8 and table 8; divisor 12 gives budget 32 and table 32. Replacing the new divisor with 48 loses this strict change; the checker rejects that mutation. `s=0, lg=1` gives both budgets 0 and table 8 in Lean, though `s=0` is outside the intended C `ca_isqrt(...) + 1` input. `lg=0` is excluded by the last three theorem hypotheses and cannot occur after the C `n < 64` branch; Lean's total natural-number division at zero must not be used to describe C division by zero.
- `LEAN_PROOF.md` also names a merged `d488af97` source hash `4ab176d1...`; that is not the target commit's C hash. Its separate live receipt and this target-commit read both identify `60796724...afe20`, so the stale provenance sentence does not break the selector formula, but should not be cited as the current-main hash.

**Joint owned:** source identity, literal C-to-Lean formula correspondence, and boundaries above. Kernel execution, proof-term audit, empirical replay, and performance attribution are outside this review.
