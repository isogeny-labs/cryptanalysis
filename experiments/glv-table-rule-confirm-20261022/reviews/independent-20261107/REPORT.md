# Independent review: GLV table selector theorem

**Finding (2026-11-07).** The eight named theorems in `TableBudget.lean` compile with Lean 4.34.1 and support the conditional selector-arithmetic claim: for the same nonnegative `sqrt_nm` and positive `lg`, replacing divisor 48 with 12 cannot decrease the C loop's selected table size. The source binding and two separately frozen reviews agree on the 8/16/32 threshold formula. The review does not independently remeasure the held-out operation-count rows.

## Evidence and method

- Source target: cryptanalysis `927d1eada55ff51e87b89930cad48672147e0929`; review plan and frozen input hashes are in `REVIEW_PLAN.md`. `src/curve.c` SHA-256 `60796724ef7d7c5b3b7dfd89c29db85d5e188deb247b5d9d0bd69b84551afe20` at this target equals the pinned live-source receipt.
- Machine check: `ELAN_TOOLCHAIN=leanprover/lean4:v4.34.1 lean TableBudget.lean`, exit 0; all eight `#print axioms` records contain only `propext` and, where applicable, `Quot.sound`. See `machine/lean-v4.34.1.log` and `machine/source-hashes.txt`. No `sorry`, custom `axiom`, `unsafe`, or `native_decide` appears in the reviewed file.
- Binding check: `python3 check_lean_source_binding.py --live`, exit 0, two negative mutations rejected. See `machine/source-binding.json`. It pins current and historical C snippets and full-file hashes.
- Independent reasoning: `blind/report.md` derived the case table from definitions without source or proof access. `source/report.md` checked each theorem type against C, the historical rule, branch conditions, types and arithmetic bounds without seeing the blind result. Attestations are beside those reports.

## Scoped conclusion

| Budget | C loop result | Lean `tableSize` |
|---|---:|---:|
| `b < 16` | 8 | 8 |
| `16 <= b < 32` | 16 | 16 |
| `b >= 32` | 32 | 32 |

The current C expression uses `sqrt_nm / (12 * lg)`; the prior rule uses divisor 48. For positive `lg`, the prior quotient is at most the current quotient. The threshold formula is nondecreasing, so `loop48_le_loop12` has the stated direction. The loop terminates after at most two changing doubles because its cap is 32. Boundary checks at 15/16 and 31/32 and wrong-divisor/wrong-cap controls support this correspondence. `diagram.svg` shows this exact selector, not a measured performance curve.

The C path reaches the selector only for `n >= 64`, making `lg = glv_ilog2(n)+1` positive. The proof treats `sqrt_nm` and `lg` as natural inputs and assumes the same values for both rules. It does not prove the external `c.m > 0` invariant required by C's `n / c.m`, the implementation of `ca_isqrt`, or an operation-count benefit. The held-out experiment's 160,000 candidate rows and 80,000 rho rows remain producer records; their performance numbers were not independently replayed in this review.

`LEAN_PROOF.md` contains a stale sentence naming the merged `d488af97` C hash as the live source. The later live receipt and this exact target read both identify `60796724...afe20`. The source-fidelity report records the discrepancy; the theorem conclusion uses the exact target hash above. Correct that sentence in a separately scoped documentation edit. No canonical performance graph changes are warranted by this proof review.
