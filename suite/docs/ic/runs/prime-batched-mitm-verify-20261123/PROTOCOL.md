# Frozen protocol: independent verification and scale-up of mitm-prime-batched (2026-11-23)

Frozen before any data of this task was taken. Lead spec: workspace
`docs/lead-testing/leads/prime-batched-mitm.json` (unchanged). Claim under test:
`PCC-20261122-ae5817` (unverified). Original run: `../prime-batched-mitm-20261121/`.

## Arms and runs
- A. Re-run: runner `tools/lead_sweep.py run --phase 1|2|3` with `registry-fresh.json`
  (original instances, repeats, budgets, gate; only per-phase seeds re-derived, so every
  planted target is new). Baseline `prime-abscissa`+`mitm`, lead `mitm-prime-batched:m={m}` m=2,3.
  Commit pinned: cryptanalysis `origin/main` at worktree HEAD (contains the oracle).
- B. Accounting audit, same instances/seeds as A, run with `ca-ic bench` directly, arms:
  1. `mitm` (registry baseline; unfolded charge),
  2. `mitm:negation_folded=1` (folded-table baseline: what a fair scalar baseline charges),
  3. `mitm-prime-batched` native pricing (the lead),
  4. `mitm-prime-batched:native_setup_pricing=0,native_probe_pricing=0` (counted control),
  and the wall-time S (`s_wall` = total wall / ns_per_add / sqrt r) of every arm, which does not
  depend on any native price.  A gain is "real" only if the wall-S ratio is also > 1.
- C. Extension: `registry-ext.json` (24-bit anchor, 28 bits size 645, 32 bits size 1625 =
  round(2^(b/3)), the exact rule of the registry's 16..24 sizes), repeats 8/4/3, rho runs 16/8/8.
  A cell the host cannot finish in its wall budget is reported with its repeats completed,
  never read as a negative.

## Statistic (as the protocol): paired per-seed geomean(baseline S / lead S), 95% percentile
bootstrap, 10,000 resamples, seed 20261119. Every solve verified [d]G=Q by the runner.

## Predictions (written before data)
P1. Phases 1-3 re-pass under fresh seeds; each m=2 ratio's 95% CI overlaps the original CI and
    lower bound > 1.5 at 16..24 bits; the ratio rises with bits.
P2. Accounting: the m=2 gain against the folded baseline (arm 2) is about half the registry
    gain (the fold's factor 2 is an accounting difference of the registry baseline, which charges
    the full table); the remaining gain > 1 at >= 20 bits. Counted control (arm 4) ratio to
    baseline ~ 1.7-2.1 at m=2 (fold only). Wall-S ratio (no pricing) at 24 bits >= 1.5 at m=2.
P3. Extension: m=2 ratio keeps rising at 28 and 32 bits but sub-linearly in bits (table
    insertion dominates once batching is cheap); lead S / matched rho grows past 11.5 (the 24-bit
    value) at 28 and 32 bits.  A null (ratio flat or falling) is a valid outcome.
## Host rules: <= 2 threads, kill-on-OOM watchdog (runner), host/isolation tier recorded; no
second CPU-heavy process during natively priced arms (the first original run was invalidated by
that), so cells run with --jobs 1.
