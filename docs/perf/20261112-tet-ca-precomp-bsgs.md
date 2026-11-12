# Tet offensive: Bernstein-Lange precomputation, BSGS and grumpy giants (2026-11-12)

Branch `perf/ca-precomp-bsgs`, base `dc4885a6`. Scope: `src/precomp.c`, `src/bsgs.c`,
`src/grumpy.c`. WALL-class changes only: every value, counted unit (`group_ops`,
iterations, collisions, table entries, `bytes_peak`), RNG draw and checkpoint byte is
unchanged. No proof-pinned code was touched (`ca_addmod` itself is unchanged; the walk
calls the existing `ca_addmod_sel`).

Evidence class. Instruction counts are deterministic callgrind `Ir` from
`scripts/perf/perfindex.py instr` (it refuses if fingerprints differ; none differed).
Wall times are **local, unisolated, [pcc:unverified]**, 4-vCPU shared VM, load average
about 2.0 (other agents building), 5 alternating runs with 5 samples each, medians.
No pcc claim, `benchmarks/` row or leaderboard row is made; AGENTS.md section 10 still
applies before any speed claim.

Binaries (Release, gcc, no -march): base `ca_perfbench` sha256 `1ea0d4c8a28288ea...`
(built from `git archive dc4885a6`), candidate `dc99b15f562c8c2810fbec62...`.

## Results

| commit | change | kernel | base Ir | cand Ir | local wall (median) |
|---|---|---|--:|--:|--|
| `9f7389b1` | walk starts via `ca_ec_fb_sum` (one inversion) instead of one inversion per addition | `precomp_build_ec32` | 630,732,851 | 605,928,843 | not separated |
| `2983b93c` | exponent update `ca_addmod` -> `ca_addmod_sel` (branchless) in build and online walks | `precomp_build_ec32` | 605,928,843 | 611,247,363 (+0.9 %) | 59.5 ms -> 50.0 ms (7 alternating runs) |
| `c4dbb662` | grumpy: 3 walks x 32 lanes advanced by one batched op (one inversion per 96 additions) | `grumpy_ec32` | 72,054,474 | 39,090,253 | 6.5 ms -> 3.1 ms |
| `8774fe3c` | bsgs: inline native ec/zp hash, slot base and mask in locals | `bsgs_ec32` | 43,076,871 | 41,223,005 | 3.9 -> 3.6 ms (noisy) |
| | | `bsgs_zp36` | 85,819,148 | 79,258,212 | 6.8 -> 6.3 ms (noisy) |
| `3d780ad3` | grumpy: inline native ec hash | `grumpy_ec32` | 39,090,253 | 38,715,846 | within noise |

End to end, `perfindex.py instr` base vs candidate over the dlp kernels:

| kernel | base Ir | cand Ir | ratio | local wall base -> cand (median) |
|---|--:|--:|--:|--|
| `c_grumpy_ec32` | 72,054,474 | 38,715,846 | 1.861x | 6.4 -> 3.1 ms |
| `c_precomp_build_ec32` | 630,732,851 | 611,247,363 | 1.032x | 62.4 -> 51.9 ms (1.20x) |
| `c_bsgs_zp36` | 85,819,148 | 79,258,212 | 1.083x | 7.1 -> 6.6 ms |
| `c_bsgs_ec32` | 43,076,871 | 41,223,005 | 1.045x | 4.5 -> 3.6 ms (very noisy) |
| `c_pohlig_zp61s` (BSGS inside) | 119,127,605 | 109,920,801 | 1.084x | 8.9 -> 8.3 ms |
| `c_pohlig_ec48s` (BSGS inside) | 34,203,653 | 33,033,558 | 1.035x | not timed |
| `c_precomp_online_ec32` | 156,987,477 | 155,983,237 | 1.006x | neutral |

The wall win of `2983b93c` is not an Ir win (Ir rises 0.9 %): the wrap of the running
exponent mod n is a coin flip on walk data and the branch mispredicted about half the
time, once per walk step. This is the same class as the rho `ca_addmod_sel` fix.

Why grumpy gained so much: each iteration advanced 3 points through one batched op, so
one `ca_invmod` (about 28.5 M Ir of 72 M) served 3 additions. Lane `t*32+c` holds
`walk_t + c*step_t`; one 96-element batched op moves every lane by `32*step_t`. Iteration
`i` reads lane `i mod 32`. Up to 31 points beyond the last one used may be computed at a
refill; they are not counted (`ops += 3` per iteration as before). Checkpoint saves use
the lane of the saved iteration (`gr_lanes_sync`).

## Identity checks

1. `perfindex.py instr`: fingerprints of base and candidate equal for all 7 kernels
   (the fingerprints include the answers and the counted stats).
2. `/home/user/wt/pb/h/ident.c` (not committed, scratch harness linked against each
   `libcryptanalysis.a`): 455 output lines covering
   - precomp builds on 32- and 36-bit curves and a 33-bit safe-prime Z_p^*, default,
     `walks` 1/3/7/64/100, Bloom early-abort on, `max_precomp_ops` cut (300k and 20k),
     `dp_bits`/`table_size` overrides: checkpoint file FNV-1a, dp, chains, r, ops,
     stats, and 24 online solves each (answer, ops, attempts);
   - BSGS (full group, intervals of 17, 70k and 300 width, small `table_size`, three
     groups, table API, orders 1..28 tiny group) and grumpy (same intervals,
     `max_ops` stops, `m` override, tiny group): answer, status, ops, iterations,
     table entries, `bytes_peak`;
   - grumpy and BSGS checkpoints: file bytes after the header (walk words and table)
     at a `max_ops` stop, then the resumed run's answer and stats.
   Base (built from a clean `git archive`) vs candidate: zero differing lines. The only
   lines that differ between two runs of the base itself are the 25 lines of the
   `threads=2` precomp case (thread scheduling decides which chains land in the table);
   they are excluded.
3. `ctest` in the candidate build: 20/20 pass (including `precomp`, `bsgs`, `grumpy`,
   `pohlig`-using suites).

## Tried and reverted

| idea | outcome |
|---|---|
| Fuse `pc_build_worker` with the vtable `ec_hash` and the batch like the GLV batch (inline hash, denominators, 4-chain Montgomery trick, in-place additions; the open thread from `20261112-c-hotpath-audit.md`) | identity held but `precomp_build_ec32` Ir rose 630.7 M -> 641.2 M and local wall was equal (61.5 vs 61.7 ms, 5 alternating runs). The batch already is the same arithmetic; the staging copies and the vtable call are a small part of about 270 Ir per step. Reverted. |
| Inline `ec_hash` in the precomp build and online loops | Ir 611,247,363 -> 611,273,027 (0.0 %). Reverted. |

## Deferred (would change a counted unit, a method or a shared file)

- `ec_batch_op`'s Montgomery product (`if (hi < mh) rr += p`) and `ca_submod`
  (`a >= b ? a - b : a + (m - b)`) are data-dependent selects inside `group_ec.c` /
  `ca_modarith.h`; branchless forms could give a further wall win across every walk,
  but they are outside this scope.
- `ca_htab1_init` / `ca_htab_init` zero the whole table (25 MB of `memset` in
  `bsgs_zp36`, 12.6 MB in grumpy); calloc-style lazy zero pages would avoid it, but the
  files are in `util.c`, and `bytes_peak` (a reported unit) depends on the capacity.
- `precomp_online`: 81 % of Ir is `ca_invmod` from one `ec_op` per step. The walk is
  serial; batching attempts speculatively would run wasted attempts (most solves finish
  on attempt 1 to 5) and `ca_invmod` is in `modarith.c`. Not done.
- Precomp build walks per step cost about 270 Ir at 256 lanes with 6 Montgomery
  products each; a larger `walks` would cut the inversion share (1.3 %) but `walks`
  is a parameter in the checkpoint identity and the RNG stream, so it is a method change.
- `qsort` in `pc_collect` is 0.1 % at this table size; it matters only for tables of
  10^7 entries or more.
