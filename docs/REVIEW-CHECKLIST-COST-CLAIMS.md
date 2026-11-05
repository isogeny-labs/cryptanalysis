# Review checklist: cost claims and approximate arithmetic

Use for any change that publishes a number — a constant in
[BENCHMARKS.md](BENCHMARKS.md), a complexity claim, a cost ledger, or an
approximate fast path with an error set. Derived from the
[truncated-fraction technique note](TECHNIQUES-TRUNCATED-FRACTION.md); the
checklist is the part meant to be applied routinely.

## Bound

- [ ] The bound is stated per unit (per record, per incidence, per leaf) and
      the unit matches the ledger's unit.
- [ ] The bound is re-derived from the loop structure, not quoted from the
      previous version.
- [ ] Worst-case terms are summed, and the reviewer has checked they can
      actually co-occur.
- [ ] The error is one-sided (only truncation, no rounding up); if not, the
      containment argument is redone.
- [ ] Truncation happens before reduction, and the note says so.

## Error set

- [ ] `W` (exact) and `D'` (bounded) are named, and the complement has a
      verified path.
- [ ] The size/rate of `D'` is recomputed, not inherited.
- [ ] Widening `D'` has been priced into the success probability at the quoted
      `q1`, and into any lattice/box factor.
- [ ] Fixups removed by the change were checked for failure modes they were
      silently covering.

## Counts

- [ ] Every stage in the ledger has a before and after number.
- [ ] The break-even inequality `d(early) * n_early < d(late) * n_late` holds
      with the actual fan-outs.
- [ ] Amortizations cover full groups; odd leftovers are metered, not assumed.
- [ ] Extra work is counted per incidence, not per component or per candidate.
- [ ] The per-unit totals recompute from the stage numbers (no manual sum).

## Verification artifacts

- [ ] Exact-arithmetic certificate recomputes every published constant.
- [ ] Certificate derives the error table from the per-term bounds.
- [ ] Bit-exact reference model matches the kernel record by record on
      production-shaped batches.
- [ ] Near-tie and edge-of-`W`/`D'` inputs are in the test set.
- [ ] Every fixup site type tested alone against its bit-level model.
- [ ] A never-branching copy of the hot path runs.
- [ ] Single-change mutants of kernel, model, bound and certificate all fail.
- [ ] Static instruction count/assembly size matches the claimed figure.

## Claim hygiene

- [ ] The published value is the correct rounding (least value at or above, or
      the stated rule) of the computed quantity.
- [ ] Display precision is justified — no digits past what the certificate
      controls.
- [ ] The comparison to the prior package uses the same units and the same
      machine model.
- [ ] Limitations state that nothing ran at production scale.

## Reproduction

- [ ] Runs with no network, no home directory, read-only inputs.
- [ ] Multiple seeds, all passing.
- [ ] Runtime and exit status recorded.
- [ ] `bash scripts/run_experiments.sh <track> <dir> --preflight-only` (or the
      repository equivalent) validates.
