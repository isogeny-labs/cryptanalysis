# Frozen equal-decomposition follow-up, 2026-11-25

This is a confound check on the eight-target panel, not the unavailable
L20/L24/L28 panel. The previous frozen panel produced two pairs with different
numbers of valid point decompositions; this comparison holds that number equal.

## Inputs fixed before solver execution

- Retain the prior Cayley inputs, solver logs, and target order from
  `PANEL_PROTOCOL.md` and `panel/summary.json`.
- The comparison root set is exactly `[248,3977,4499,5118,1869,3300]`.
  The first three roots are shared with the Cayley arm. The last three are the
  **first** triple from a `Random(20261126)` shuffle of eligible non-Cayley
  roots for which direct group-law enumeration gives the same number of
  decompositions on all eight frozen targets.
- Before any new solver call, the group-law counts on the four shared-relation
  targets were 6 each; counts on the four scalar targets were 0 each. These
  match the Cayley arm. Every root is curve eligible.
- Generate inputs with the already committed `panel.input_for`, replacing
  only the comparison root set. Run local `msolve` 0.11.0 with one thread,
  default genericity and linear algebra, and `-v 2`.

`balanced_panel.py` executes the eight comparison inputs once in the frozen
target order. It retains every input, output, compressed raw log, exit status,
and the complete F4 round-geometry digest. Any failure or timeout stays in
the record. Compare each new arm to the already retained Cayley arm by
solution count and F4 geometry. Single-run wall times are diagnostics, with
no speedup claim. `[pcc:unverified]`
