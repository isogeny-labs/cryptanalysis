# Frozen independent review plan: GLV table-budget selector

Conductor T-1836. Frozen before reviewer dispatch. This technical review concerns the deterministic selector theorem and its formula-level correspondence to the archived and current C selector. It does not independently rerun or certify the held-out 160,000 curve_solve rows or their operation-count ratios.

## Bound claim and inputs

Cryptanalysis main commit 927d1eada55ff51e87b89930cad48672147e0929. Producer claim: the C glv_rho_solve table selector changing divisor 48 to 12 cannot choose a smaller table for the same positive lg and nonnegative sqrt_nm; the loop returns exactly 8, 16, or 32 according to thresholds. The eight public Lean declarations are GlvTableBudget.loopResult_eq_tableSize, loopResult_fixed, tableSize_cases, loopResult_bounds, tableSize_mono, budget48_le_budget12, table48_le_table12, and loop48_le_loop12 in TableBudget.lean. The held-out performance comparison is a separate empirical statement, not a theorem consequence.

Frozen SHA-256: Lean source 823903d27e906feccfe40f29df7feb7a23669b0c96d0bdc1f79ff0e3bddf93b4; producer proof map 95d80e054b675e2f76025b1791d725dcc9265ce0b0e3e3d6a28e023e31a905fb; run report 08eb5c9435829c7d6db0aaa8c548a18bd03e96559303b046b6f9b057206bd212; C binding checker b841a8213e4a052ddaeafd264520f1d03cca5e75795ac58e7eddc8f4dcdfe059; protocol f44ca1e500ef6cedb3aa1cf9b56f2c2bb26535af0c219ce7feba42dd1f20ce11; current C 60796724ef7d7c5b3b7dfd89c29db85d5e188deb247b5d9d0bd69b84551afe20; lean-toolchain d5edba4e4b8faad9c1baeadb265716d20d03be4d1a2647dc5e35b0c0325bea7b pins Lean v4.34.1. Producer receipt lean-receipt.json and source-binding JSONs are historical evidence, not a fresh reviewer build.

The archived arm files named by .artifacts.json are SHA-pinned and outside this proof review's execution scope. Keep PROTOCOL.md, original raw data, results.json, results.md, graphs and PDF untouched.

## Prior and independent joints

Prior: the natural-number threshold lemma appears true. Formula-level C correspondence also appears plausible, but lg>0, bounded machine integers, c.m, the n<64 early return, and any compiler/runtime behavior require separate scrutiny. A true selector monotonicity theorem cannot explain or guarantee the measured operation-count ratio.

| Joint | Owner and worked attack |
| --- | --- |
| Threshold and budget arithmetic | Blind reviewer derives the complete loop outcome and monotonicity using only start 8, guard 2*r <= budget and 2*r <= 32, and budgets floor(s/(48*lg)), floor(s/(12*lg)) for natural s and positive lg. Check boundaries 15/16 and 31/32, s=0, s=384 and lg=1, and the false extension lg=0. No source, Lean, proof map, receipts or sibling report may be read. |
| Native and source fidelity | Source reviewer reads exact Lean declarations, producer proof map, C src/curve.c at base 7cb3dce4, candidate 42761f85, and current main, plus the binding checker. Check loop start/cap/guard, divisor, integer promotion/overflow, glv_ilog2, early return, c.m, and theorem hypotheses. Do not read blind report. |
| Machine and archival boundary | Coordinator reruns exact pinned Lean source and axiom audit; checks named declarations, source hashes before/after, no forbidden constructs, original receipt and source binding negative controls. Verify which historical artifacts are present and hash-bound without rerunning a trial. |
| Claim interpretation | Coordinator reconciles reviewer reports and explicitly separates selector theorem, C formula, native execution, correctness, memory and observed cost. No algorithmic or performance claim is promoted from the lemma. |

Blindness is mutual until both reports and access attestations are frozen. Each reviewer records sources_read, joints_owned, sibling access and holds/breaks/inconclusive. The coordinator preserves contradictions and corrections. Positive controls are threshold cases and the historical/current exact selector; negative controls are wrong cap 64, wrong divisor 48 in the candidate, lg=0, and an attempted inference that larger selected table implies fewer operations.

## Outcome and publication

Per-claim machine status, semantic fidelity and outcome are separate. Validated_scoped requires a fresh passing Lean check, allowed-axiom audit, independent source fidelity, satisfiable premises, controls and attestations. A code-binding gap or failed control yields partial, needs_revision or inconclusive, with its exact scope. The final packet includes logs, claim table, diagram, inspected PDF, and a PR. No ledger transition or empirical rerun is implied.
