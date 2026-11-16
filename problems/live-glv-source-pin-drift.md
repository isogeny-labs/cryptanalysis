# Live GLV source no longer matches the corpus proof pin

- **Status:** open
- **Kind:** inherited source-bound proof validation gap
- **Affected work:** Lean corpus gate on main and prime-field IC PR #1536
- **Next action owner:** GLV source-binding and corpus maintainers
- **Last updated:** 2026-11-15

## Problem

The current `src/curve.c` bytes differ from the live GLV source pin in
`tools/lean/current-corpus-gate.py`. The strict source-binding controls refuse
admission before the corpus job reaches native theorem builds. This is an
unreconciled source/proof binding, not evidence of a false theorem or incorrect
curve arithmetic. [pcc:unverified]

## Evidence and uncertainty

The hosted [corpus job](https://github.com/isogeny-labs/cryptanalysis/actions/runs/43767412540/job/132975526584)
on PR head `54e4331a6ab5bf35ca02786a83c095bb74100476` failed with
`src/curve.c SHA-256 differs from the pinned source` in the GLV sized-cap
controls. The current file hashes to
`6d120872c2020870a7fed1f8c28af644a7e31667e7b202986dddbca34772125b`;
the expected pin is
`e1d624e58c54f25f9225be97481b50c0ed406cedcfdffa8ba66f01a5fbed7f63`,
associated with `e71ebecaf3a076590ddd3affa4878b4c80d85095`.
[pcc:unverified]

Base `58c86ef41974ae33aff4b1b6cbd2b7c31ee3592e` and that PR head have
identical curve bytes, expected pins and binding-checker bytes. Calling the
actual binding checker from each revision with those inputs reproduces the
same refusal. The IC additions change neither GLV constants nor those
controls. Full logs and the two source-only reproductions are retained in
[the follow-up evidence](../experiments/prime-field-auxiliary-ic/rust-validation/ci-consumer-followup-20261115/).
This does not establish that a complete base workflow was run locally.
[pcc:unverified]

## What would unblock it

- Review the changed C source against the prior bound revision and preserve
  the old binding and native evidence as history.
- Produce a properly reviewed binding/receipt for the intended current
  implementation, with the actual selector controls and native theorem/
  foundation checks; changing only the digest is insufficient.
- Pass the complete applicable corpus gate on the exact resulting head,
  retaining the new source identity and raw diagnostics.

No source hash, proof pin, control, test or CI job is weakened by this report.

## Next discriminating step

The source-binding maintainer should identify the admitted current source and
run its exact source/selector and native proof checks. A passing full gate
would resolve this binding gap; a selector or proof failure needs its own
correction. Ordinary IC unit-test passes do not discharge this requirement.

## Resolution and history

2026-11-15: recorded the inherited failure and matching base/head refusal
inputs while correcting a separate stale consumer lockfile. Unresolved.
[pcc:unverified]
