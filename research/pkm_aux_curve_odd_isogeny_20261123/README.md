# PKM auxiliary-curve factor base: odd-degree isogeny towers, the m frontier, and structure-aware solvers (2026-11-23)

All figures here are `[pcc:unverified]`: producer runs on one unisolated
container (4 vCPU, 15 GiB), no CI verification yet.

**Question** (owner, workspace PR isogeny-labs/workspace#86, this PR #1927).
Petit–Kosters–Messeng §3.4 build a factor base as the abscissae of a coset
`V = x(R' + ⟨Q⟩)` on an auxiliary curve `E'`, with membership written as a
chain of small Vélu x-maps. Three branches had not been tested:

- **A.** isogeny towers whose levels have odd prime degree (3, 5) or mixed
  degrees (2·3, 3·2); every isogeny tower measured before used degree 2;
- **B.** the m = 2..9 frontier through the lab's lead-testing protocol;
- **C.** solvers other than F4, in particular ones that eliminate the tower
  (the intermediate variables of the guide's page 6) instead of running a
  Gröbner basis on it.

## Answer

| branch | result |
|:--|:--|
| A | Odd degrees cut F4 work by a **constant factor** at equal `log2 |V|` (m = 2: degree 3, 1.4–2.5x wall and 1.3–2.0x widest matrix; degree 5, 3.3–5.7x wall and 1.1–2.5x widest matrix). Mixed 2,3 / 3,2: no material effect (0.87–3.2x, both sides of 1). The growth rate is unchanged and the frontier moves by at most about one bit of `|V|`. The lead-sweep gate, which pairs by `t` (not by `|V|`), reads **FAIL** for degree 3. |
| B | Under the 60 s per-system budget at p = 786433, every tower form (Kummer, Dickson, isogeny of any degree) stops at about `|V| = 2^8–2^9.5` for m = 2, `2^5` for m = 3, `2^3` for m = 4, and completes nothing at m ≥ 5 even at `|V| = 8`. |
| C | Eliminating the tower by resultants (univariate solve with FLINT) costs the same **order** as enumerating the factor base: linear in `|V|` at m = 2 (to `|V| = 2^20`), quadratic at m = 3 (to `2^10`), 1–8x faster than pure-Python enumeration. Both Gröbner solvers on the tower system (the pilot's F4, and msolve 0.6.5) grow about 8–10x per doubling of `|V|` at m = 2 and 25–60x at m = 3. Every solver returned enumeration's exact solution set on every system. |

Nothing measured here beats enumeration of the factor base by more than a
constant, so none of it changes the index-calculus exponent or the distance to
rho. No claim is made about rho, larger fields or deployed curves.

## What was built

- `suite/examples/pkm_tower_pilot.rs`, flag `--iso-degrees d1,d2,…`
  (commit 36fb74f08): isogeny levels of any prime degree, repeated cyclically,
  x-only Vélu on an auxiliary curve with a point of exact order
  `N = Π d_j`, `V = x(R' + ⟨Q⟩)` with `2R' ∉ ⟨Q⟩`, `|V| = N`. Level `j` of
  odd degree `d` is `y_{j+1} = y_j + Σ_{Q∈S} (v_Q/(y_j − x_Q) + u_Q/(y_j − x_Q)²)`,
  `v_Q = 6x_Q² + 2a_j`, `u_Q = 4y_Q²`, written as an equation of degree `d`.
  The default (`2`) keeps the original code path. Tests: the F_61 worked
  example of the auxiliary-curves guide reproduces exactly (`r₁`, `r₂`,
  `V = {5, 11, 15, 16, 17, 19, 25, 37, 58}`, χ = 60, x = 2 → 49 → 25
  rejected); towers of degree 3, 5, 7, 2·3, 3·2 build and every level
  equation has the expected degree; the BSGS point count equals the exact
  count.
- `solvers_c.py`: one m = 2 system, four solvers (enumeration, univariate
  elimination, msolve, the pilot's F4), every pair set checked against
  enumeration.
- `scaling_c.py`: enumeration vs univariate elimination at m = 2, 3, far past
  the Gröbner frontier, both on the registry primes 786433 and 3221225473.
- `equal_v.py`: odd-degree vs degree-2 isogeny towers, interpolated at equal
  `log2 |V|`.
- Leads `leads/pkm-iso-deg{3,5,23}.json` (`lead-testing.lead/v1`).

**Build.** `main` (71313c2f) does not compile: C (`src/linalg.c`,
`src/indexcalc.c`) and Rust (`ic_framework/plugins.rs`, `cli/tools/ic/bench.rs`)
were broken by the 2026-11-21 `mt-work` merges (e59dda7e and its parents).
Everything was built from `git archive 9824fb08` (the last commit before them)
plus this branch's `pkm_tower_pilot.rs`. The pilot builds and its tests pass
there. The lead-sweep manifest therefore records `cryptanalysis: None` (the
build tree is not a git checkout).

## A. Odd and mixed degrees

Lead sweep, `pkm-iso-deg3`, phase 1 (workspace `docs/lead-testing`, registry
sha256 `e840213ad5cf…`, p = 786433, seed 1347112276, 3 planted + 3 random
targets, 60 s per system, `--jobs 2`): `data/sweep_deg3_phase1/`. The run hit
the session's 2-hour background limit after m = 2..5 (m = 6, 7 partial; 8, 9
not started). Gate on the completed cells: **FAIL** ("lead lost cells the
reference completed at m = 2, 3, 4"), paired speed-up 0.73 [0.64, 0.82] at
m = 2. The gate pairs `(kind, t, target)`; a degree-3 cell at the same `t`
carries `3^t` instead of `2^t` abscissae, so this verdict measures the larger
`|V|` and not the degree. It is recorded as the protocol's verdict and not
re-gated.

Equal-`|V|` reading (`equal_v.py`, random targets, the same rows plus
`data/branch_a/`; reference = the baseline's degree-2 isogeny rows, log-linear
interpolation between completed sizes, no extrapolation):

| m | degrees | log2 V | lead ms | ref ms (interp) | ms ratio ref/lead | lead max_cols | ref max_cols (interp) | cols ratio |
|--:|:--|--:|--:|--:|--:|--:|--:|--:|
| 2 | 2,3 | 2.58 | 0.6 | 1 | 1.11 | 69 | 92 | 1.33 |
| 2 | 2,3 | 3.58 | 2.0 | 4 | 2.16 | 155 | 234 | 1.51 |
| 2 | 2,3 | 5.17 | 54.6 | 70 | 1.29 | 900 | 831 | 0.92 |
| 2 | 2,3 | 6.17 | 227.6 | 729 | 3.20 | 1,607 | 3,648 | 2.27 |
| 2 | 2,3 | 7.75 | 20,371.7 | 17,678 | 0.87 | 13,492 | 11,993 | 0.89 |
| 2 | 3 | 1.58 | 0.1 | 0 | 1.63 | 15 | 24 | 1.60 |
| 2 | 3 | 3.17 | 1.3 | 2 | 1.43 | 105 | 167 | 1.59 |
| 2 | 3 | 4.75 | 12.7 | 32 | 2.54 | 409 | 538 | 1.31 |
| 2 | 3 | 6.34 | 651.2 | 1,059 | 1.63 | 2,577 | 4,196 | 1.63 |
| 2 | 3 | 7.92 | 14,013.3 | 24,036 | 1.72 | 6,892 | 13,442 | 1.95 |
| 2 | 3,2 | 2.58 | 0.5 | 1 | 1.41 | 55 | 92 | 1.67 |
| 2 | 3,2 | 4.17 | 11.8 | 13 | 1.13 | 372 | 366 | 0.98 |
| 2 | 3,2 | 5.17 | 43.3 | 70 | 1.62 | 661 | 831 | 1.26 |
| 2 | 3,2 | 6.75 | 2,453.1 | 2,635 | 1.07 | 6,520 | 5,905 | 0.91 |
| 2 | 5 | 2.32 | 0.1 | 0 | 3.38 | 27 | 69 | 2.54 |
| 2 | 5 | 4.64 | 8.4 | 27 | 3.26 | 452 | 500 | 1.11 |
| 2 | 5 | 6.97 | 732.5 | 4,188 | 5.72 | 2,826 | 7,024 | 2.49 |
| 3 | 2,3 | 2.58 | 68.6 | 157 | 2.29 | 839 | 1,431 | 1.71 |
| 3 | 2,3 | 3.58 | 4,337.2 | 6,777 | 1.56 | 7,955 | 7,664 | 0.96 |
| 3 | 3 | 3.17 | 1,001.6 | 1,492 | 1.49 | 2,506 | 4,433 | 1.77 |
| 3 | 3,2 | 2.58 | 38.3 | 157 | 4.10 | 907 | 1,431 | 1.58 |
| 3 | 3,2 | 4.17 | 23,588.9 | - | - | 11,621 | - | - |

Frontier (smallest log2|V| at which a random-target refutation timed out):
  m=2 degrees=2: 8.00
  m=2 degrees=2,3: 8.75
  m=2 degrees=3: 9.51
  m=2 degrees=5: 9.29
  m=3 degrees=2: 5.00
  m=3 degrees=2,3: 5.17
  m=3 degrees=3: 4.75
  m=3 degrees=3,2: 5.17
  m=3 degrees=5: 4.64
  m=4 degrees=2: 3.00
  m=4 degrees=3: 3.17

Mixed 2,3 and 3,2 (`data/branch_a/deg23_*`, `deg32_*`): ratios 0.87–3.2x (wall) and 0.89–2.3x (widest matrix), on both sides of 1 with no trend: no material effect. The order 2,3 vs 3,2 makes no consistent difference. At m = 3 the mixed orders give 1.6–4.1x (wall) and 0.96–1.7x (widest matrix) where a reference size brackets them, and every mixed form times out at `|V|` = 36, next to degree 2 at 32.

Kummer and Dickson rows of the lead arm equal the baseline's (the flag touches
the isogeny kind only). Planted solutions were found in every completed
planted row (`planted_ok`), in both arms.

## B. The m frontier

From the same sweep (baseline arm, all three tower kinds, smallest `|V|` at
which a random-target refutation hit the 60 s budget):

| m | completes up to `|V|` | times out at `|V|` | peak RSS (largest arm) |
|--:|--:|--:|--:|
| 2 | 128 (degree 2), 243 (degree 3), 125 (degree 5) | 256 / 729 / 625 | 4.9 GiB |
| 3 | 8 (degree 2), 9 (degree 3) | 16 / 27; degree 5 at 25 | 6.0 GiB (killed at the 6 GiB per-cell ceiling of `--jobs 2`) |
| 4 | 4 | 8 (degree 2), 9 (degree 3) | 2.5 GiB |
| 5, 6, 7 | none (smallest cell is `|V| = 8`) | 8 | 3.4–3.8 GiB |
| 8, 9 | not run (time limit) | | |

`oom_killed` and `timeout` are resource limits, not negatives. At m ≥ 5 the
protocol's smallest `t` already gives `|V| = 8`, and no tower kind completes
a system there in 60 s.

## C. Solvers

Same exported systems (`--export`), m = 2, p = 786433, isogeny towers of
degree 2 (`|V|` = 4…256) and 3 (`|V|` = 3…243), one planted and two random
targets each: 36 systems, `data/branch_c/c_deg{2,3}.jsonl`. Every solver's
solution set equals enumeration's (36/36), every planted pair is found, and
msolve's basis is `{1}` exactly when enumeration finds nothing (36/36).

| `|V|` (degree 2) | F4 (pilot) | msolve | enumeration (Python) | univariate (FLINT) |
|--:|--:|--:|--:|--:|
| 32 | 37 ms | 0.02 s | 0.22 ms | 0.15 ms |
| 64 | 0.56–0.66 s | 0.08 s | 0.45 ms | 0.25 ms |
| 128 | 4.5–5.2 s | 0.67 s | 1.0–1.6 ms | 0.4–0.7 ms |
| 256 | 39–44 s | 6.6 s | 1.8 ms | 0.6–0.8 ms |
| 243 (degree 3) | 21 s | 2.0 s | 1.9 ms | 0.7 ms |

m = 3, msolve on the degree-2 isogeny systems (one planted, one random):

| `|V|` | planted | random | 
|--:|--:|--:|
| 4 | 0.009 s | 0.014 s |
| 8 | 0.23 s | 0.22 s |
| 16 | 13.4 s | 13.1 s |
| 32 | – | **timeout at 1,800 s**, peak RSS 2.06 GiB |

That is 25–60x per doubling. Enumeration solves the same m = 3 sizes in 2.5–7 ms (table below).

Past the Gröbner frontier (`scaling_c.py`, random `V`, random curve and
target; both methods ignore `V`'s structure, so a random set costs what a
coset costs). Mean of 3 (m = 2) or 2 (m = 3) instances; all solution sets
agree:

| m | p | `|V|` | enumeration | univariate | solutions |
|--:|--:|--:|--:|--:|--:|
| 2 | 3221225473 | 1,024 | 0.031 s | 0.004 s | 0 |
| 2 | 3221225473 | 16,384 | 0.50 s | 0.16 s | 0 |
| 2 | 3221225473 | 262,144 | 8.3 s | 5.6 s | 9–10 |
| 2 | 3221225473 | 1,048,576 | 32.9 s | 30.8 s | 170–185 |
| 3 | 3221225473 | 64 | 0.14 s | 0.018 s | 0 |
| 3 | 3221225473 | 256 | 2.1 s | 0.28 s | 0 |
| 3 | 3221225473 | 1,024 | 32.1 s | 5.9 s | 0 |
| 3 | 786433 | 256 | 0.52 s | 0.24 s | 4–6 |

The univariate solver computes `F(x) = Π_{v∈V}(x − v)`, the resultant
`R(X) = Π_v S3(v, X, x_R)` (both by product trees), `gcd(R, F)` and its roots.
At m = 3 it finds the roots `u` of `B(u) = Π_v S3(u, v, x_R)` and runs the
m = 2 solve for each, so it is `|V|` times the m = 2 cost. Any method that
writes down `F` is at least linear in `|V|`; the tower only gives a shorter
description of `F`, which does not shorten the gcd.

## Reading

- Odd isogeny degrees are a constant-factor improvement to the F4 tower
  solve, as odd Kummer degrees were (crypto `pkm_odd_tower_f4_20261114`), and
  the isogeny form keeps matching the Kummer form. The auxiliary curve
  contributes a way to write `V`, not a cheaper system.
- The tower presentation is the expensive part. Eliminating it (dense `F`,
  resultant, gcd) brings the cost down to enumeration's order, not below it.
  This is the same direction as crypto `pkm_ideas_20261115` (dense membership
  cheaper than the tower under F4), now with a non-Gröbner solver and to
  `|V| = 2^20`.
- At m ≥ 3 the target of PKM's proposal is a solve that is cheaper than
  `|V|^{m−1}` enumeration. Neither Gröbner solver gets near: both stop at
  `|V| ≈ 16–32` at m = 3 where enumeration takes milliseconds.

## Open and not done

- Lead sweeps for degree 5 and 2·3 were not run through `lead_sweep.py` (the
  degree-3 sweep alone exceeded the session's 2-hour limit); their rows here
  come from direct pilot runs with the registry's phase-1 prime, seed,
  targets and budget, and are not gated.
- Phases 2 and 3 were not run (phase 1 did not pass).
- m = 8, 9 not reached; m ≥ 5 cells time out at the smallest size.
- No `bench.record/v1`: the pilot is a stage diagnostic that reports no `S`.
- S3 resume checkpoint not pushed (no upload token in this session); the
  resume notes are in `RESUME.md` here.
- research-kb was not reachable from this session; prior art was found by
  GitHub code search over the isogeny-labs repositories.
