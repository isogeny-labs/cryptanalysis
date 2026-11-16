# Kangaroo, Cheon, Pohlig-Hellman, modular arithmetic: WALL-only fixes (2026-11-12)

Branch `perf/ca-kangaroo-cheon-pohlig`, base `cea0f68f`
(`claude/performance-optimization-parallel-vgenii`). Scope: `src/kangaroo.c`,
`src/cheon.c`, `src/pohlig.c`, `src/modarith.c` (not `ca_addmod`),
`src/group_zp.c` (no change needed). Prior notes read first:
`POHLIG_EC_SCAN_2026-10-15.md`, `20261110-glv-invmod-wall-only.md`,
`20261112-c-hotpath-audit.md`.

All changes are WALL class: results, `group_ops`, `iterations`,
`table_entries`, RNG draws, checkpoint bytes and perfbench fingerprints are
unchanged. Primary evidence is callgrind `Ir` (deterministic). Wall numbers are
**local, unisolated, [pcc:unverified]**, shared 4-vCPU VM, load average
1.4-1.8, `-O3` Release, no `-march`, 5-9 samples per run, no A/A arm. No
benchmark record, leaderboard row or pcc claim is made. Instruction counts are
a poor proxy for the commits that interleave independent multiplication chains
(they hide latency, they do not remove instructions); those rows say so.

Build: `cmake -DCMAKE_BUILD_TYPE=Release -DCA_BUILD_TESTS=ON -DCA_BUILD_TOOLS=ON
-DCA_BUILD_SHARED=OFF`, `-j2`. Binary SHA-256 (temporary build dirs deleted):
base `ca_perfbench` `1ea0d4c8...6b3c`, candidate `b73845a5...3f05`; base
`libcryptanalysis.a` `352da0ef...c2`, candidate `630d0d5f...a8`.

## Commits and before/after

| commit | change | kernel | base Ir | cand Ir | wall (local) |
|---|---|---|--:|--:|---|
| 44eac54f | kangaroo: native Z_p hop done in place per lane (inline Montgomery product and hash, no `Yn`/`B` copies, no indirect calls) | `dlp/c_kangaroo_zp61_w36` | 186,207,666 | 119,532,161 (1.56x) | 11.1-11.5 ms -> 8.0-9.0 ms |
| | | `dlp/c_kangaroo_ec56_w34` (EC path untouched) | 184,100,138 | 184,792,565 (+0.4%, neutral) | 14.3-14.6 -> 13.9-14.6 ms (noise) |
| e3d54e0a | cheon: Z_p exponent-orbit BSGS walks 4 orbit segments at once (shared exponent, interleaved ladders); table order, lookups, charges, early exits identical | `dlp/c_cheon56` | 76,955,529 | 65,237,406 (1.18x) | 15.6-16.8 ms -> 6.0-6.1 ms (about 2.7x) |
| 9dac0a71 | modarith: `R mod p` in 64-bit, `divq` mulmod (operands < modulus) in `ca_mont_init`, Tonelli-Shanks, short `ca_powmod` | `field_ec/c_sqrtmod` | 44,556,823 | 34,895,700 (1.28x) | about -5..-9% |
| | | `field_ec/c_powmod` | 50,014,372 | 46,803,108 | flat |
| | | `field_ec/c_is_prime` | 32,920,849 | 31,988,338 | flat |
| c92bed1c | modarith: Miller-Rabin bases 3..37 four at a time after base 2 | `field_ec/c_is_prime` | 32,920,849 | 32,622,488 (Ir not the measure) | 8.5-8.9 ms -> 5.6-5.8 ms (about 1.5x) |
| b3381915 | pohlig: halving tree for `base^(n/q^e)`, `target^(n/q^e)` when >= 3 prime powers | smooth 60-bit Z_p, 200 solves (scratch) | 23,295,047 | 19,307,360 | 3.9 -> 2.4 ms |
| 73f89dfe | pohlig: Z_p digit step uses `(q^e - xk) base_e` instead of a modular inversion | same scratch | 19,307,360 | 12,167,995 (-48% vs base) | about 2.0-2.5 ms |
| | | `dlp/c_pohlig_zp61s` (two big primes, little to gain) | 119,127,605 | 118,924,290 | n/a |
| | | `dlp/c_pohlig_ec48s` | 34,203,653 | 33,640,635 | n/a |

The
whole-tree `perfindex.py instr` run (base vs candidate `ca_perfbench`, all 31
kernels) accepted every fingerprint: PI 1.024x over all three areas, dlp
1.046x, field_ec 1.027x, relation 1.001x (small Ir moves in `relation/*` from
the `ca_powmod`/`ca_sqrtmod` changes).

## Identity checks (base library vs candidate library, same inputs)

- Perfbench fingerprints equal for every kernel (the harness refuses
  otherwise); they cover answers and the stats counters.
- Cheon: `ca_bench cheon --bits 32..48` rows identical except wall seconds;
  1,055 scratch `ca_cheon_solve` cases (5 primes, 10 divisors, random alpha,
  `max_exps` in {0,1,100,700,1500,3000,5000}, one non-subgroup base) print
  byte-identical rc/answer/iterations/group_ops/table_entries/bytes_peak
  (269 solved, 781 `CA_ERR_LIMIT`, 5 other).
- Kangaroo: tests plus kernel fingerprints; the per-lane hop applies lane
  effects in the same order, so a stop mid-batch leaves later lanes untouched,
  as before (checkpoint bytes unchanged by construction; not diffed on disk).
- Modular arithmetic: 1M random `ca_mont_init` constants and `ca_powmod`
  results vs a `% m` reference, 7,342 `ca_sqrtmod_prime` outputs identical to
  base, 3.2M random `ca_is_prime` inputs plus strong pseudoprimes, 2^64-59 and
  semiprimes identical to base.
- Pohlig-Hellman: 1,500 solves over Z_p groups with prime-power orders,
  subgroup orders, non-member targets and the brute solver give identical
  statuses, answers, `group_ops` and `iterations` (hash equal).

## Tests

`test_modarith` (1,393,344 checks), `test_cheon` (1,091), `test_kangaroo`
(119), `test_pohlig` (281) all pass on the candidate. `-DCA_GLV_FIELD_COUNT`
builds keep the original ladders and serial loops (not built here).

## Reverted ideas

- Sliding-window (w=3) `ca_mont_pow`: 12% fewer products but Ir +16% and wall
  +12% to +14% slower (`c_mont_pow` 11.2 -> 12.7 ms, `c_cheon56` 17.2 -> 19.2
  ms). The right-to-left ladder's multiply and squaring chains are independent;
  the windowed form is one serial chain. Reverted before any commit.
- Kangaroo array-of-structures split (`Ys`/`Yn` pointer swap, no element
  copies for EC): EC 184.10M -> 180.83M Ir (-1.8%) but Z_p 119.5M -> 131.7M
  (+10%) and it needs extra care to keep stop-mid-batch checkpoint bytes.
  Reverted.

## Deferred METHOD / COUNTER changes (not done)

- Kangaroo EC hops spend most time in `ec_batch_op`/`ec_hash` (`group_ec.c`,
  outside scope).
- Pohlig/BSGS Z_p time is `memset`, `ca_htab1_insert`, `ca_bsgs_table_new`
  (`bsgs.c`, `util.c`, outside scope).
- `ca_invmod` (267M Ir in `c_invmod`) could move to a 2-word divstep
  (Bernstein-Yang style) inversion; not tried, a prior audit already replaced
  Euclid with the binary form.
- Pollard-Brent in `ca_factorize` (85% of `c_factorize`): interleaving two
  `(c, seed)` attempts would hide the `y` chain's latency; the factorisation
  is unique so output is unchanged, but speculative work was not attempted.
- Cheon p+1 path (`cheon_mulmod` via `%`, six exponentiations per step) not
  touched.
