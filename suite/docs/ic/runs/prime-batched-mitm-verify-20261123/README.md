# mitm-prime-batched: independent verification and scale-up (2026-11-23)

Question: does the claim PCC-20261122-ae5817 (priced S falls 1.98-4.86x at m=2) survive an independent
re-run with fresh seeds, is the gain partly an accounting change, and does it keep growing to 28 and 32 bits?
Protocol and predictions frozen before data: `PROTOCOL.md` (two amendments, each dated before the data it governs).
Code: cryptanalysis `origin/main` cb73ed6f (contains the oracle, PR #1891). Host: 4 vCPU cloud VM shared with another
agent (load average 1.4-3.0 during runs), no isolation tier, one host. Claims written: PCC-20261123-932211 and
PCC-20261123-99112d, both `unverified` (unsigned recompute proofs; CI signs, not this session).

## 1. Fresh-seed re-run (runner `tools/lead_sweep.py`, `registry-fresh.json`): confirmed
Same instances, repeats, budgets and gate as the frozen registry; only the per-phase seeds are new. Phases 1, 2, 3: PASS; every row
verified [d]G=Q. Priced-S ratio baseline/lead, geometric mean, 95% bootstrap (recomputed by `analyze.py`, matches the runner):

| bits | m=2 | m=3 | original m=2 / m=3 |
|--:|:--|:--|:--|
| 16 | 2.07 [2.00,2.15] | 1.69 [1.51,1.86] | 1.98 / 1.67 |
| 18 | 2.72 | 2.09 | 2.96 / 2.14 |
| 20 | 3.07 | 3.03 | 2.91 / 2.68 |
| 22 | 4.59 | 3.60 | 3.71 / 3.68 |
| 24 | 4.40 [4.10,4.72] | 3.77 [3.63,3.91] | 4.86 / 4.65 |

The priced-S claim reproduces (every CI lower bound above 1.5). P1 scoreboard: lower bounds above 1.5 yes; ratio rises with bits, nearly (4.59 at 22 bits, 4.40 at 24); CI overlap with the original: yes at 16, 20, 24 bits, **no at 22 bits** (fresh 4.59 [4.50,4.70] vs original 3.71 [3.54,3.90]); m=3 at 24 bits is 3.77 against the original 4.65. Seed-to-seed variation of a single curve per size is larger than the bootstrap over 6-8 targets shows.

## 2. Accounting audit (`audit.py`, amendment 1): the headline mixes three effects
Per instance, 24 planted targets, 10 replicate processes per arm in rotated order on one pinned CPU; per-target log-ratios averaged over
replicates, bootstrapped over targets. All arms recover every target verified, with identical trials and relations to `mitm` at m=2.
Arms: B0 registry baseline `mitm`; B1 `mitm:negation_folded=1`; B3 `mitm:negation_folded=1,native_setup_pricing=1` (the scalar build charged the way the lead is);
L2 lead m=2; M3n `mitm:m=3,native_setup_pricing=1`; L3 lead m=3. "wall" is total `wall_seconds`, no calibration involved.

| bits | priced S, L2 vs B0 | wall, L2 vs B0 | wall, fold alone (B1 vs B0) | wall, L2 vs B3 (same pricing, folded) | wall, L3 vs M3n |
|--:|:--|:--|:--|:--|:--|
| 16 | 2.17 | 1.27 [1.22,1.32] | 1.15 | 1.09 [1.07,1.12] | 1.29 |
| 18 | 2.87 | 1.60 [1.54,1.66] | 1.31 | 1.20 [1.16,1.23] | 1.76 |
| 20 | 3.47 | 1.76 [1.71,1.81] | 1.39 | 1.30 [1.28,1.32] | 1.67 |
| 22 | 4.23 | 1.86 [1.82,1.90] | 1.50 | 1.34 [1.33,1.37] | 1.79 |
| 24 | 4.45 | 1.94 [1.90,1.99] | 1.39 | 1.37 [1.36,1.39] | 1.98 |

At 24 bits, 4.45x priced S = 1.79 (the negation fold, counted; the registry baseline arm builds the full table, a flag removes the
difference) x 1.75 (pricing convention: the scalar build is charged 131,328 additions at the calibrated ns per addition, about 98 ns, while it measures about 44 ns per entry;
native pricing of the scalar build alone, `B2`, lowers its S by 2.1x with wall unchanged) x 1.41 (genuine batching, S; wall 1.37). P2 scoreboard: the fold was predicted to be about half of the registry gain; it is about 40% in log terms (1.79 of 4.45), the pricing convention is the other large part (1.75x); wall gain vs the folded control stays below 2x at every size (P4 holds); wall-S at 24 bits above 1.5 (P2 holds).
So **part of the headline is an accounting change**
and does not count as improvement; the genuine gain is wall 1.37x at 24 bits against a scalar build with the same fold and same pricing (1.94x against the unmodified registry baseline).
The m=3 gain against the scalar m=3 oracle is wall 1.3-2.0x. Counted-pricing control (L2c) equals B1 in S (fold only), as the note says.
Noise: an A/A split of the 10 B0 replicates gives wall ratios 0.97-1.10 at 16, 20, 24 bits, so the 16-bit gain vs B3 (1.09) is at the noise floor; `ns_per_add` varied 74-140 ns between processes
(it prices every native arm, so single-process S carries calibration noise up to about 1.9x at worst; the replicate average and the wall column do not depend on it).

## 3. Extension to 28 and 32 bits (sizes 2^(b/3) = 645, 1625, the registry's rule; amendment 1)
Runner PASS at both (`ext/`): priced S m=2 4.57 (24), 4.88 [4.49,5.32] (28, 4 targets), 3.91 [3.68,4.28] (32, 3 targets); m=3 4.33, 3.99, 2.61. Audit (24 targets, 6 replicates):

| bits | priced S L2 vs B0 | wall L2 vs B0 | wall L2 vs B3 | priced S L3 vs B0 | lead S / matched rho | baseline S / rho |
|--:|:--|:--|:--|:--|--:|--:|
| 24 | 4.77 [4.64,4.91] | 1.91 | 1.41 [1.39,1.44] | 4.24 | 7.2 | 34.0 |
| 28 | 5.24 [5.02,5.49] | 2.38 [2.30,2.48] | 1.50 [1.45,1.54] | 3.98 | 14.9 | 77.2 |
| 32 | 3.77 [3.64,3.91] | 2.28 [2.18,2.38] | 1.65 [1.60,1.70] | 2.60 | 26.5 | 98.7 |

Trend: the priced-S ratio peaks near 28 bits and falls at 32 (it does **not** keep growing); the genuine wall gain against the same-priced scalar build grows slowly (1.41, 1.50, 1.65) and is about
half of the setup (lead setup is 51% of wall at 32 bits). P3 (keeps rising) is refuted for priced S; the distance to rho grows (P3's second part holds).

## 4. The registry size is not S-optimal for either arm (amendment 2, size sweep, 4 replicates, one curve per size)
`sweep/` (archived), `size-sweep.txt`. Each arm at its own best size on the grid (grid factor about 1.4, optimum is a grid minimum):

| bits | baseline best S (size) | lead L2 best S (size) | ratio of optima | lead S/rho at its optimum | baseline S/rho at its optimum |
|--:|:--|:--|--:|--:|--:|
| 24 | 17.4 (90) | 8.0 (180) | 2.2 | 6.3 | 13.7 |
| 28 | 23.3 (226) | 11.2 (450) | 2.1 | 12.6 | 26.1 |
| 32 | 39.8 (570) | 18.7 (1140) | 2.1 | 20.5 | 43.7 |

At each arm's own optimum the priced-S gain is a constant about 2.1-2.2x, not growing; the registry sizes (2^(b/3)) sit near the lead's optimum
and above the baseline's, which is what makes the fixed-size ratio look larger (4.9-6.6x at 24 bits for sizes 256-512). Wall gain against the same-priced folded scalar at the sizes below its optimum is 0.95-1.1x (no gain).
P5 (not blind, see PROTOCOL) holds: about 2x, roughly constant.

## 5. Distance to matched rho.negation
Lead S/rho at its own optimum: 6.3 (24), 12.6 (28), 20.5 (32 bits): about x2 per 4 bits, i.e. the gap still grows with the field (pair-table family law). Not an advance over rho; an engineering gain of the baseline.

## 6. What was not done
Second host / isolab-eks (no AWS here); signed pcc verdict (CI key); S3 checkpoint and S3 raw archive (no credentials; raw reports archived in the repo as `*-raw.tar.xz`, sha256-pinned in the validator reports);
research-kb lookup (not an index-calculus novelty claim here; MCP not queried in this session); one curve per size; no sizes above 32 bits; m>3 (oracle supports 2, 3 only); conductor check (crypto, not used).
The first run of arm A (`fresh-run1-nocommit/`) lacked the commit hash in its manifest (git worktree issue); rerun as `fresh/`, same seeds, different timings (kept, not cited).
