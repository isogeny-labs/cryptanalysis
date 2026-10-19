# Local validation (cloud-agent VM; diagnostics only)

Everything here ran on the cloud-agent VM: a shared 4-vCPU Intel Xeon guest
at 2.1 GHz, with transparent huge pages set to `madvise`, using rustc
1.97.0 (the runner pins 1.99.0). Some processes ran concurrently. **None of
these times is timing evidence.** They check correctness, show where a
probe's time goes on this machine, and give rough sizes.

## Derivation and tests

- `make_rankcut_source.py` is byte-identical to the rank-cut experiment's
  `make_online_source.py` (sha256 `7e81a642...`, its protocol's
  `online_derivation` pin). It reproduces the rank-cut producer's frozen
  digest, `c390733e...`.
- The nine rank-probe edits then apply, with every counted replacement
  matching, giving the producer `d4394df3...`. `restore.py` re-derives it
  and checks every pin. The producer builds with no warnings of its own.
- `cargo test --release --locked --bins` (`cargo-test-online.txt`): all 18
  producer tests pass, plus the 4 tuned-rho tests. lift2's 24 tests also
  pass (`cargo-test-lift2.txt`). The three new `rankprobe_tests` are:
  - `frame_conjugates_commute_with_point_addition`: on random points of a
    9-orbit base, φ^s(T_s) = T and φ^s(T_s ± R) = T ± φ^s(R), with the frame
    tabulated by `frame_build128`.
  - `frame_keys_are_the_rankcut_keys`: on 200 random states (roots of two
    random base points) and random targets, the frame keys equal the
    rank-cut loop's keys (`rankcut_keys128`). The fields compared are
    canonical, partner, partner shift and candidate, in order.
  - `frame_loops_find_the_rankcut_relation_with_the_rankcut_probes`: on 40
    planted four-point targets, in three settings (folded with the Feistel
    order, folded with the left-major order, and unfolded), `PIPE_FRAME`,
    `PIPE_FRAME_PLANT` and `PIPE_FRAME_SWAPPED` return the compact S3
    loop's and `PIPE_PADD`'s relation, intermediates, probe count, root
    calls and relation checks. The swapped loop exercises the exact-order
    resolution; the planted loop checks keys, and frames are built.

## Full K600 rank stages against the archive (`rank_exactness_local.json`)

The inputs were rank seed 201 and point s000 of the rank-cut panel: the
same inputs as run 38891404048's block K1 (archived kR). Three concurrent
processes ran with `KIC_RANK_SOLVE` = `padd` (kR), `frame` (kP) and
`frame_plant` (kPX).

| arm | rank, attempts | relation digest | per-attempt probes | root calls | padd counters | factor-log table | target relation, scalar, probes | frames | rank stage (diagnostic) | ns per probe (diagnostic) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: |
| kR (`padd`) | 600, 600 | = archive | = archive (600 of 600) | = archive | = archive | = B's | = archive | 0 | 279.6 s | 258.7 |
| kP (`frame`) | 600, 600 | = archive | = archive | = archive | = archive | = B's | = archive | 600 | 258.6 s | 239.3 |
| kPX (`frame_plant`) | 600, 600 | = archive | = archive | = archive | = archive | = B's | = archive | 600 | 452.4 s | 418.7 |

- There were 1,080,101,628 probes in each arm. The counters were 600
  resolved hits, 283 pairs emitted in the other order and evaluated in the
  S3 order, 0 fallback states and 0 exceptional inputs, the same as the
  archive in every arm.
- kPX compared all 540,100,256 candidates with the rank-cut keys and found
  no difference.
- B's index digests (logical-state blake3, table-map sum and xor, 29,878,182
  entries) held in every arm.
- On this VM the candidate's rank stage was 1.08x faster than the baseline's,
  run concurrently. This is a diagnostic only.

## Profile (`profile_local.json`, `profile.patch`, `../figures/profile.*`)

The patch adds one env-guarded diagnostic (`KIC_PROF3`) to a scratch copy
of this producer; it is not part of any frozen producer. The workload is
the first rank target of seed 201: 6,000 states (1.99 M probes) scanned for
15 interleaved rounds, with the stages added one at a time for both loops,
then the production loops on the same states.

The median increments, in ns per probe, for the rank-cut loop:

| Stage | ns per probe |
| --- | ---: |
| fold rebuild | 0.4 |
| root y | 3.7 |
| per-candidate input maps and prefix products | 25.3 |
| batched inversion | 20.7 |
| lambda products, normal-basis maps and partners | 39.1 |
| lift_scan keys | 54.3 |
| prefetch and key store | 57.2 |
| lookups and hit check | 57.5 |

The frame loop's inputs stage is 9.3 ns per probe. The production loops
took a median of 268.2 ns per probe for `padd` and 233.2 for `frame`; the
ratio per round had a median of 1.106 and ranged from 0.90 to 1.43. The
probe counts were equal in every round.

A second build, with `RUSTFLAGS=-C target-feature=+pclmulqdq`, cut the
isolated multiplication from 16.9 to 11.1 ns. Its production loops did not
separate from the default build's (`padd` 286.9 and `frame` 257.1 ns per
probe), so the change was not pursued.

`lift_scan_u128_micro.rs` is a standalone microbenchmark of a branch-free
`u128` lift_scan, checked equal to lift_scan and to the full scan on 65,536
random words. It took 46–54 ns per word against 55–63 ns. That is not a
large exact cut, so it was not pursued.

## Runner, wrapper, gates and verifier

- `run_schedule.py --segments O1,C1`: 6 rows, all valid.
  - Q0: cR and cP both give the archived relation [77273, 22971, 54962,
    62539] and scalar 3141592653589793, with 1,987,852 probes.
  - s000: cR, cP and cPI give one relation [52563, 90300, 13948, 94652] and
    2,385,634 probes, and rT gives the same scalar, 29550818704994.
  - `verify_receipt.py --correctness-only` passes every check
    (`correctness_O1_C1.json`), including the oracle replay.
- `run_schedule.py --segments K1 --max-runs-per-segment 2` ran the first
  two shuffled K1 rows, kR and kP, with the new rank seed 301. Both rows are
  valid:
  - both reach full rank, write B's table and give one relation digest
    (`6c99bff2...`), one per-attempt probe vector (982,994,775 probes) and
    one root-call count (491,547,414);
  - both give the same counters: 600 resolved hits, 308 swapped pairs, 0
    fallback states and 0 exceptional inputs;
  - kP built 600 frames and kR none;
  - each gives C1's target relation, probe count and scalar;
  - the rank gates pass (`correctness_K1_two_rows.json`).

  The two stage times were 250.9 s and 242.7 s, run one at a time. These
  are diagnostics only.
- `synthetic_stats.py` (`synthetic_stats.json`) runs the verifier's
  statistics path on run 38891404048's rows, renamed:
  - a planted 1.08x rank effect gives R = 1.0698 [1.0677, 1.0718] and
    "improvement";
  - no effect gives 0.9997 [0.9977, 1.0018] and "not separated".

  The A/A and planted controls pass in both cases.
