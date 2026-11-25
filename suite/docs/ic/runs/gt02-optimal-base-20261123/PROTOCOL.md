# GT-02 at the S-optimal base: frozen protocol (written before any data, 2026-11-23)

Instrument: `ca-ic bench` built from cryptanalysis origin/main f9c7b49e (worktree /home/user/wt/gt02-optimal-base), local 4 vCPU / 15 GiB shared host, <=2 jobs, each cell under `tools/lead_sweep.py` `watched_run` (3 GiB, 600 s wall). Isolation tier: none (shared host); isolab-eks not attempted (cells finish in seconds to minutes locally). Counted cost S = ops / sqrt(r) is host independent.

Arms (paired per repeat, same curve, seed, planted targets):
- baseline `binary-subspace:dimension=d` + `mitm` ; lead `mitm:coset_filter=1,m=M`.
- Prime: `prime-abscissa:size=k` + `mitm` vs `mitm:coset_filter=1,m=M` (`--bits`).

Stage A (ladder, seed 20261123): char2 n in {17,19,21,23,25,27,29,31,33}; dimension d in [4, ceil(n/3)+2] (m=2) and [4, ceil(n/3)+3] (m=3, n<=29); 12 repeats, --max-trials 20000000, --max-cofactor 8, --rho-runs 0. A cell with a repeat that exhausts the trial budget is a resource limit (excluded from argmin, reported). d*_base(M) = argmin of mean baseline S; d*_lead(M) = argmin of mean lead S.
Stage B (confirmation, FRESH seed 20261124 = different curve and targets): at d*_base(M) both arms, 12 repeats, baseline with --rho-runs 12 (matched rho, negation walk); also at d*_lead(M) when different, and at d*_base+-1. Headline = paired geometric-mean ratio S_base/S_lead at d*_base (selection on seed A, test on seed B), 95% percentile bootstrap (10,000 resamples) over the 12 repeats. Second statistic: best-of-ladder lead S / best-of-ladder baseline S (each arm at its own optimum, from stage A).
Prime: recalibrated sizes of followups/registry/registry.proposed.json (m=2: 16b 23, 18b 30, 20b 47, 22b 58, 24b 96; m=3 optima 31, 50, 79, 119) plus registry sizes (40, 63, 100, 160, 256) as control, registry seeds, 12 repeats.

Predictions (frozen):
P1 char2 m=2 at d*_base: ratio = 1/(1 - share(1 - setup_lead/setup_base)) as in RECALIBRATION.md section 8; geomean in [1.05, 1.5], lower CI > 1 for every n where the optimum is setup-dominated; ratio grows with d, ~1.00 below the optimum.
P2 best-of-ladder lead vs best-of-ladder baseline: between 1.00 and the d*_base ratio (a shift of the optimum to a larger base recovers part of the gain).
P3 char2 m=3: filter is documented m=2 only; expect ratio 1.000 (no-op) or an unsupported error.
P4 prime: cofactor 1, filter is a no-op: ratio exactly 1.000, identical S, at every size.
P5 gain at the baseline-optimal base shrinks with n (the optimum's setup share falls as hit rate 2n^2/(hr) drops) -- this is the one to watch; falsified if the ratio at n=31,33 is >= the ratio at n=17.
Verification: every repeat's recovered log must verify ([d]G=Q); any unverified repeat marks the cell invalid for ratios.
