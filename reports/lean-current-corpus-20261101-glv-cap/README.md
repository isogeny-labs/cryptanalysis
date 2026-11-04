# Corpus receipt for the size-dependent GLV table cap

`receipt.json` is the output of `python3 tools/lean/current-corpus-gate.py`
(not edited by hand) for the 97-source corpus with the GLV table-cap change of
PR 1341: `glv_rho_solve` uses `rcap = lg >= 40 ? 128 : 32` instead of a fixed
cap of 32.

What changed against the [October 25 main-update receipt](../lean-current-corpus-20261025-main-update/receipt.json):
only the GLV fields of `fresh_native_evidence` and the `TableBudget.lean` entry of
`fresh_native_source_sha256`. The Hasse, Orbit, Cubic gluing, CM and PQC
evidence hashes, the archive evidence, and the 97 / 90 / 7 file counts are identical.

- `src/curve.c` is pinned to `e71ebecaf3a076590ddd3affa4878b4c80d85095`
  (`e1d624e5...`). The selector is replayed with ten refusals: nine one-edit
  controls (divisor, threshold up and down, large cap up and down, small cap up and
  down, loop bound back to 32 or to 128) and the fixed-cap selector rule, which must
  not admit the new source.
- `TableBudget.lean` (`ff60c813...`) has 27 theorems, each checked natively with
  axioms within `propext` and `Quot.sound`, and matching `lean-receipt.json`.
- Kept as history and still replayed: the fixed-cap source `8bf648dc...` with its
  own controls and its live receipt (`8439b5e8...`), and the eight-theorem
  `TableBudget.lean` (`823903d2...`) rebuilt natively against its original receipt
  (`90c7c692...`). Those older pins are not weakened or overwritten.

The October 25 receipt is kept unchanged as the record of that binding. The gate
no longer compares against it, because the GLV fields it commits to have changed.
This receipt binds sources and native Lean output only. It does not claim the C
change is faster or that the Lean model captures the whole solver.
