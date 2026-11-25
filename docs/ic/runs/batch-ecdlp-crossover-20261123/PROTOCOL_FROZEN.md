# Frozen protocol and predictions (written before any new data)

Date 2026-11-23. Branch `claude/batch-ecdlp-crossover-20261123` (cryptanalysis PR #1955, draft). All numbers below are predictions or plans, not results.

## What I found before taking data (reading code, one probe each of `ca-ic prime` and `ca-ic bench`, no measurement used for selection)
- `ca-ic prime` (the batch IC arm of RES-batch-ic-vs-rho) collects relations with a single-large-prime walk on a fixed 8-orbit base (`prime_orbit_index_calculus.rs`). `mitm-prime-batched` (#1891) is a different oracle: the full pair table of a prime-abscissa base (`ic bench`, `prime_batch_mitm.rs`). It is the same table, entry for entry, as `mitm`; with `native_setup_pricing=0` it charges exactly the scalar op counts, i.e. it differs from `mitm` in wall time alone. Its 1.98-4.86x is a gain in `ic bench` S, which prices the batched preparation as measured nanoseconds.
- The `ca-ic prime` unit is "abstract group operations, independent of coordinates" (`vs_rho.unit`). In that unit batched inversion is already free, so the #1891 gain is 1.00x by construction there.
- The k=3 harvester (#1901) is `gaudry_cubic` (F_p^3 curves, large primes on a cubic ladder); it has no F_p-curve relation phase to replace. Not applicable.
- At single-target scale the `ic bench` pair-table IC is far behind the `ca-ic prime` IC (lead S/matched rho 5.1-11.1 at 16-24 bits in the #1891 summaries, vs `ca-ic prime` K=1 whole-process / rho about 1.7-2.5). So "rebuild the batch arm on #1891" means a new arm: a pair-table batch IC. I build it (executed, every log verified [d]G=Q), count it in the `ca-ic prime` unit, and also report the setup-priced view.

## Arms (same curves and targets as the existing executed batch rho: seeds 1-6 per B in {20, 24, 28} from `ca-ic prime --type generic`)
1. `IC-LP`: `ca-ic prime` as in the previous note (re-run on the current main binary for the rebuilt tree; data reused where identical).
2. `IC-PT(N)`: pair-table batch IC. Base: N smallest abscissae with a point; table of all x(+-Pi +- Pj) (setup N(2N+1) additions, the count `ic bench` reports for the scalar build); relations from walks R=[a]G+jumps whose abscissa hits the table; exact gain-graph solve over Z_r; targets descended by walks R=[a]G+[b]Q+jumps until a hit whose two base columns are determined. Counts in the `ca-ic prime` unit: one per walk step or table entry, scalar multiplication charged ceil(3 bits(r)/2). N is chosen per (B, K) on separate tuning curves (seeds 101, 102), not the evaluation curves.
3. `rho-fold-full` (the tool's seeding charge) and `rho-fold-cheap` (best-seeded) from the previous executed batch rho (`batch_rho.py`, `runs.csv`); "best-seeded rho" is defined as the cheap arm: first walk of each target after the first starts at Q_i at no cost, restarts at [a]G+Q_i, the rest as in `full`. Reported both.

## Predictions (frozen)
- P0: swapping #1891 into the `ca-ic prime` arm changes its counted precompute by exactly 1.00x (no code path shares). Falsified only if I find a shared path.
- P1 (the task's prediction, "crossover moves down by about the relation-phase speedup s"): false in the counted unit, because s=1 there. In the setup-priced view the crossover can move only if the pair-table arm is competitive at all.
- P2: IC-PT in the counted unit costs at least 1.2x the folded batch rho (full seeding) at every K <= 4096, B in {20, 24, 28}, i.e. no crossover. Reason: both scale as sqrt(K r) (table N^2 + K r/N^2 balanced; Kuhn-Struik sqrt(2Kr) steps), IC-PT has no Aut fold beyond the sign. Falsifier: a per-curve crossover K <= 4096 on a majority of curves.
- P3: IC-PT's up-front cost is 3-10x that of IC-LP at the same B (table N^2 vs 8-orbit large-prime collection), so against IC-LP at K <= 256 IC-PT is dearer; at K = 4096 within 0.7-1.5x.
- P4: no IC arm crosses best-seeded rho (cheap arm) for K <= 4096 at any B (the previous note: IC-LP/ cheap folded rho = 4.0, 1.9, 1.4 at B = 20, 24, 28 for K = 4096). Falsifier: any arm with total/total < 1 with a 95% CI excluding 1 over curves.
- P5 (distance remaining): at B = 24 the best IC arm needs to lose >= 1.9x at K = 4096 against cheap folded rho; this closes by a factor of the per-target cost D only (D_IC/D_rho_cheap = 110/59), so no relation-phase speedup can close it: as K grows the cost per target tends to D, not to A.

## Statistics
Paired by curve (same curve, same targets across arms), ratios IC/rho of totals per curve, geometric mean over 6 curves with 95% bootstrap CI (10 000 resamples); crossover K per curve by log-K interpolation of the ratio through 1, as before; replicate noise of executed rho from `runs.csv` (20 replicates K<=256). Host and isolation tier recorded: shared 4-vCPU container, no isolation (tier unisolated), counted ops are host-independent; wall times indicative only.

## Amendment 1 (before any IC-PT data; no data of any arm taken for this note yet)
"Best-seeded" applies to IC as well as rho: IC-PT is run with two seeding modes, `full` ([a]G+[b]Q, 2 smul + 1 per target) and `cheap` (first walk of every target starts at Q itself, restarts at [a]G+Q), exactly mirroring the rho arms. P4 is tested on `cheap` IC-PT vs `cheap` rho (and IC-LP, whose seeding is the tool's own, is reported as is). Table charge: the tool's count N(2N+1) (all signed pairs); the symmetry-exploiting count N^2 is a sensitivity row.
