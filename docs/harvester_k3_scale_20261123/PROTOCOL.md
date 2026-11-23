# Protocol (frozen before the ladder data): gain-forest harvester k=3 beyond toy sizes

Status: all numbers produced under this protocol are [pcc:unverified]. Written 2026-11-23, before the
extended-ladder runs. Lead: cryptanalysis PR #1901 (merged), RES-harvester-k3.

## Instrument and units
`suite/examples/gaudry_cubic_bench` at origin/main 20348aac, `--protocol-la --groebner --lp-rule --lp-arm-only`,
curve over F_{p^3}, prime order n ~ p^3 (so "group order" 2^36..2^42 below, not 2^16..2^20: the task text's
2^16..2^20 range is the size of p, and p < 2^20 is the instance generator's own limit). S = total_ops / sqrt(n),
total_ops = group ops + (oracle F_p muls + precompute)/fp_per_add + la_ops * la_fp_equiv / fp_per_add
(la_ops = Wiedemann + eliminator/harvester merge multiplications mod n). Rho reference = `run_rho3` on the same
instance (plain r-adding rho, 32 jumps, exhaustive storage). `rho.negation` is an ecbench instrument and does
not run on this F_{p^3} family; it is not measured here.

## Arms (paired per (p, seed): same curve, base, residual stream)
- A: eliminator, `--max-lp 2` (the lab's eliminator, as in PR #1901).
- B: gain-forest harvester, `--harvester cycles --max-lp 3` (k=3 large primes).
Every solve is group-checked ([d]G = Q, `correct` = true); a row with correct != true is reported as a failure.

## Ladder
p = 271, 523, 1039, 2083 (re-run here, same code and host, because the raw JSON of PR #1901 is not in the trunk)
and the extension p = 4159, 8317, 16657 (n = 2^36.1, 2^39.1, 2^42.1; three further doublings).
Seeds 1..6 at every size, both arms. Exception, declared in advance because of the 60-minute budget: at p = 16657
arm A is run on seeds 1..2 only (about 20 min per run) and arm B on seeds 1..6.
Disclosure: one calibration run (p = 4159, seed 1, both arms: A S = 2508.3, B S = 824.5) was made to estimate wall
time before this protocol was written; it is a ladder cell and is kept (re-run deterministically in the ladder).
Host: 4 CPUs shared, at most 2 single-threaded processes, `ulimit -v` 6 GiB kill-on-OOM, host/isolation tier
recorded as shared cloud VM (no isolation tier, wall is indicative only; S is a count and does not depend on it).

## Frozen predictions (written after the calibration run, before the other cells)
P1. B/A S ratio stays between 0.25 and 0.40 at p = 4159..16657 (no further improvement beyond the 0.31 seen at 2083).
P2. Extended-ladder (p = 271..16657) fitted exponent of total_ops on n: A in [0.39, 0.45]; B in [0.34, 0.40], i.e. the
    0.332 of the four-point ladder drifts upward; paired B - A about -0.06 (between -0.03 and -0.09).
P3. The harvester's non-multiplication work (hashing, buffer scans, pointer chasing) is not charged in S, but
    wall time per counted op of the harvest phase stays within 2x of the relation phase's.

## Statistics and verdict rule
1. Per seed, least-squares slope of log2 total_ops on log2 n over the sizes it has (A at p = 16657 only seeds 1..2).
   Report mean over seeds, bootstrap 95% CI (10 000 resamples over seeds), and paired B - A on the seeds both have.
2. Local slope between consecutive sizes (per-seed, then mean +- bootstrap CI) to see drift, and the slope of the
   top three sizes (2083, 4159, 8317, 16657 minus the lowest) for A and B.
3. Verdict on the 0.332: "holds" if the B exponent CI over the extended ladder contains 0.332; "drifts back" if its
   lower bound exceeds 0.332 and the paired B - A mean is above -0.05; "improves" if its upper bound is below 0.332.
   Separately, the top-three-size slope is reported as the asymptotic-direction statistic (not a claim).
4. Ratio B/A S per size (paired, per-seed ratios, mean and CI); distance to rho: S_B / S_rho and S_A / S_rho per size
   with the pooled rho S over seeds of that size.
5. S-accounting audit (goal 4), from the JSON of the run: (a) wall ms per counted fp-equivalent op for the
   harvest/LA phase (`linear_algebra_ms` / (la_ops * la_fp_equiv / fp_per_add)) against the relation phase
   ((wall_ms - linear_algebra_ms) / (group_ops + oracle muls / fp_per_add)); (b) wall ratio B/A against S ratio B/A;
   (c) the share of total_ops charged to la_ops and lp_merge_ops; (d) read of the code for uncharged work.
6. k=4: not extended (the k=4 pipeline cost 55 min for two seeds at p = 769; larger p does not fit). Reported as not done.

## Stopping
If a cell is killed by the watchdog it is reported as a kill and counted as missing, never imputed.
