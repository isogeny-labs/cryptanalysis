# tet offensive: ca-ec-tau (src/ec_tau.c)

Scope: `src/ec_tau.c`, `src/ec_tau_internal.h` (header untouched). Base commit
`cea0f68f` (branch `claude/performance-optimization-parallel-vgenii`), worktree branch `perf/ca-ec-tau`.

Scope note: the task text described binary-field (GF(2^m)) Koblitz arithmetic with
PCLMULQDQ. `ec_tau.c` is not that: it is the width-w tau-NAF for j=0 curves
y^2 = x^3 + b over a prime field p = 1 (mod 3), tau in Z[omega], 64-bit Montgomery residues.
No carry-less multiply applies; the work below targets the code that is there.
The Montgomery primitives live in `ca_modarith.h` (out of scope, untouched).

WALL-only: every counter in `ca_tau4_joint_counts`, every output digest, and every
CA_FC_* count is unchanged (identity check below).

## Evidence (local, deterministic; wall is secondary)

Harness: `ca_joint_tau_bench` (CA_BUILD_JOINT_TAU_BENCH, Release, -g added only for profiling, `-j2`),
curve j0-56, 1024 scalar pairs. Ir = callgrind instructions of the whole run (the
generic-replay verify and setup are identical across builds, so deltas are the tau path).
`tau incl.` = inclusive Ir of the tau entry point.

| mode | base total Ir | final total Ir | base tau incl. | final tau incl. | tau delta |
|---|---|---|---|---|---|
| paired2-free-gauge-scored | 112,867,247 | 111,159,782 | 23,281,955 | 21,574,119 | -7.3% |
| paired2-free-gauge-taupair-steered | 111,437,534 | 109,914,956 | 21,852,037 | 20,328,964 | -7.0% |
| paired2-free-gauge | 112,418,984 | 110,870,373 | 22,833,737 | 21,284,743 | -6.8% |
| paired2 | 111,605,097 | 110,089,843 | 22,020,284 | 20,504,592 | -6.9% |
| paired (25 neighbours) | 225,267,775 | 183,793,271 | n/a | n/a | -41.5M Ir total (about -41% of the tau path) |

Per commit (paired2-free-gauge-scored total Ir; base 112,867,247):

1. `92cbe6d2` branch-free `fa`/`fs` (`ca_addmod_sel`, mask borrow): Ir +560k (113,427,382) but
   callgrind branch-sim mispredicts 908,891 -> 814,454 (-10.4%) whole run. A wall change, not an Ir change.
2. `8ad89c3d` atlas recoder: single modulo per residue, one 4-byte fill plus one store per group,
   one division per coordinate: 112,475,546 (paired: 225.27M -> 212.50M including commit 1).
3. `6a7cf1d2` stream statistics accumulated inside the atlas recoder (no rescan of the 256-byte digit
   array), pair rotation score by 3 popcounts over words below the shorter stream (masks of one stream
   are disjoint), inline SWAR popcount when `__POPCNT__` is absent (baseline target called libgcc):
   111,507,921 (paired 190.92M).
4. `d92f3014` reuse the 5-neighbour residues from the shortlist pass: 111,301,241 (-0.95% of tau path).
5. `cab19fc9` hoisted mode predicates and early `continue` when the pair score is already worse
   than the best (exact, since `tau4_pair_score_better` orders by score first): 111,159,782
   (paired 183.79M, 25-neighbour scoring is the main beneficiary).

Mispredicts, scored mode, whole run: base 908,891 -> final 778,704 (-14.3%).

Wall, local, unisolated, [pcc:unverified], load average 2.3-2.9 on a shared 4-vCPU VM, 21-25 interleaved
runs of `online_ms` (1024 mults), min / median ms:

| mode | base | final |
|---|---|---|
| paired2-free-gauge-scored | 3.654 / 3.951 | 2.577 / 2.837 |
| paired2-free-gauge-taupair-steered | 3.702 / 4.066 | 2.451 / 2.703 |
| paired (25 neighbours) | 19.445 / 20.615 | 12.224 / 13.356 |

Binary sha256 prefixes: base `bc17a0aac579f359`, final `e1b1da7ffc0ae9a9`.
These wall numbers are not a validated speedup; they carry no replay certificate or matched rho
reference and must not reach the leaderboard.

## Identity checks

- `ca_joint_tau_bench` over 18 modes x 2 curves (glv-j0-32, j0-56), 36 lines: every
  field except the three timings (input/output digests, all counters, `verified=1`) byte-identical
  base vs each commit (md5 `d4aeca8af7d65d4ed2191baf9696f776` for base and every commit).
- The bench itself replays every output against generic group arithmetic (`verified=1`).

## Tests

`test_joint_tau` (107,723 checks), `test_curve` (2,351,118 checks), `test_sixclass`: all pass after every
commit (test_joint_tau) and at the end (others). `test_joint_tau` also clean under valgrind memcheck.

## Reverted / rejected

- 8-byte chunk skip of empty digit slots in the stream statistics loop: Ir went up on the scored
  modes (+300k): tau-NAF slots are about 80% occupied per 4-group, so chunks rarely skip. Replaced by
  the in-recoder accumulation (commit 3).

## Not done / observations

- The remaining tau path is dominated by inlined Montgomery multiplication/reduction (about 60%),
  whose cost sits in `ca_modarith.h` (out of scope) and whose count is fixed by the counters.
- Remaining mispredicts (~100 per multiplication) are digit-dependent control flow in the evaluation
  loop (digit present, gauge change, power rotation); the rotation `fm` is a counted operation, so it
  cannot be made branch-free without changing a counter.

## Deferred method changes (would change a counter, method or output; not done)

- Computing both rotated seed x-coordinates ahead of time (plane precompute) already exists as a
  separate mode; adopting it for the scored mode changes `rotations`/`mixed_adds` accounting.
- Lazy (delayed-reduction) field add chains in jac_double/jac_triple (f2/f3/f4/f8) need p < 2^62;
  the code accepts any 64-bit p, so that would be a domain restriction.
- Pruning the 25-neighbour search by L1 bounds would change `pair_scores`/`lattice_points_checked`.
