# GLV table selector: source-bound Lean proof and archived result replay

![Proof and measurement boundary](lean-proof.svg)

## Question and exact scope

The [held-out experiment](REPORT.md) changed the `glv_rho_solve` table-budget
divisor from 48 to 12. This addendum proves a deterministic selector property:
for the same `sqrt_nm` and positive `lg`, the new rule cannot choose a smaller
table. It checks that the pure Lean selector matches the pinned C loop. It does
not turn the measured operation-count gain into a theorem.

| Input or artifact | Pinned evidence |
| --- | --- |
| Baseline `src/curve.c` | commit `7cb3dce4cac9176d74afb6403048b5fabbaab834`, SHA-256 `e504bb18f0e80134c9ccf9abc1b7a825097286a759075090d2693ef82b406975` |
| Current `src/curve.c` | commit `42761f85b06242cb54f2a5fa405c723451897503`, SHA-256 `3f3a100d635d814bdfa0f6624a40b9d77c9c564f65db2bbc568dcd4b55285efe` |
| Merged source at this PR update | commit `d488af97a0cae6d7e96686da17aeff2f0db5f29f`, SHA-256 `4ab176d18c6b8b562fb48aba23e67127a61d59e4450a93d781902c47579fac20`; [live receipt](live-source-binding.json) |
| Formal source | [TableBudget.lean](TableBudget.lean), Lean `v4.34.1` from the repository root `lean-toolchain` |
| Source check | [check_lean_source_binding.py](check_lean_source_binding.py), [receipt](lean-source-binding.json): exact C selector in both pinned sources; two changed-selector controls rejected |
| Kernel and axiom check | [lean-receipt.json](lean-receipt.json): build exit 0; six printed theorem axiom sets contain only `propext` and `Quot.sound` |
| Archived measurement replay | [lean-analysis-replay.json](lean-analysis-replay.json): both 80,000-row arm files, result JSON, result Markdown, and SVG checked |

The committed [source protocol pin](PROTOCOL.sha256) verifies the historical
`42761f85` C file, protocol, run script, and analysis script at that commit.
The additional live check pins the merged C file separately and rejects two
changed-selector controls. All 13 original entries in
[SHA256SUMS](SHA256SUMS), including the original performance chart and report
PDF, pass. The new proof files are supplemental and do not modify those frozen
inputs or outputs.

## Proof map

| Lean declaration | Statement and role |
| --- | --- |
| `GlvTableBudget.loopResult_eq_tableSize` | Two C-style guard-and-double steps from 8 equal the three threshold cases: budget below 16 gives 8; budget from 16 to 31 gives 16; budget at least 32 gives 32. |
| `GlvTableBudget.loopResult_fixed` | A third step cannot change the result. Together with the prior theorem, this identifies the full loop result. |
| `GlvTableBudget.loopResult_bounds` | The result is between 8 and 32; `tableSize_cases` strengthens this to exactly 8, 16, or 32. |
| `GlvTableBudget.tableSize_mono` | The selector is nondecreasing in its integer budget. |
| `GlvTableBudget.budget48_le_budget12` | For every natural `s` and positive natural `lg`, `s/(48*lg) ≤ s/(12*lg)`. |
| `GlvTableBudget.loop48_le_loop12` | Combining the two results, the divisor change from 48 to 12 cannot reduce the selected table size for the same `s` and `lg`. |

The readable argument is short: the cap of 32 permits only `8 → 16 → 32`.
The two possible successful doublings occur precisely at budget thresholds
16 and 32. Lowering a positive divisor from `48*lg` to `12*lg` cannot lower
the quotient, and a threshold selector cannot decrease as its budget grows.

The C branch returns before this selector when `n < 64`, so `lg =
glv_ilog2(n)+1` is positive on the path covered by the proof. The full-file
hash and exact-snippet checks bind the historical and current C start value,
guard, cap, and two divisors. The Lean model uses unbounded natural arithmetic; it does not
formalize the C compiler, group-order validity, division by `c.m`, other
solver paths, or memory behavior. The C loop itself multiplies only 8 and 16
by two before the cap stops it.

## Archived outcome and graph state

An isolated rerun of `analyze.py` and `chart.py` reproduced committed
`results.json`, `results.md`, and `confirm.svg` byte for byte. The primary
paired group-operation ratios remain **0.95654** for `j=1728` (97.5% interval
`[0.94800, 0.96490]`) and **0.96708** for `j=0` (`[0.95812, 0.97619]`)
over 28–34-bit groups. The identity control still has **45,700** equal-table
rows with zero differing operation counts. The source chart SVG and PNG and
the original PDF retain their committed hashes; this selector proof changes
no canonical performance figure or numerical result.

These are archived operation counts, not wall-time measurements. The theorem
does not prove that a larger table is faster, that each solve is correct, or
that the observed ratios hold at other sizes or for the separate covariant
walk. The archived row analysis and existing CI support the measurements in
their stated scope; a fresh solver run was not performed for this addendum.

## Reproduce

From this experiment directory, with the repository's pinned Lean toolchain:

```sh
ELAN_TOOLCHAIN=leanprover/lean4:v4.34.1 lean TableBudget.lean
python3 check_lean_source_binding.py
python3 check_lean_source_binding.py --live
sha256sum -c SHA256SUMS
```

Run `sha256sum -c PROTOCOL.sha256` from the historical `42761f85` checkout;
its full-file C hash intentionally differs from the later merged source.

To replay the analysis, copy `analyze.py`, `chart.py`, and both `rows_*.jsonl.gz`
files into a scratch directory, run the two Python scripts there, and compare
the three generated hashes with [lean-analysis-replay.json](lean-analysis-replay.json).
`lean4checker` was unavailable on this host. Lean compilation and the printed
axiom audit passed; no independent semantic review of the C-to-Lean
correspondence has yet been recorded.
