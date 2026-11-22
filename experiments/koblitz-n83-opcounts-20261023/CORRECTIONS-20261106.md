# Corrections and disclosures, 2026-11-06

Source: sheriff case SHF-20261106-a114e7 (crypto-autoresearcher, branch
`claude/sheriff-reaudit-20261106`, PR #3071,
`research/sheriff/SHF-20261106-a114e7/`): prior findings CAN-1 to CAN-5 of
SHF-20261028-0f3f64 (verdict `not_fixed`), K2 of SHF-20261016-3caa6f and
K-N1 of SHF-20261017-e4d7f6 (`partially_fixed`), and new findings CAX-1 to
CAX-3.

Class: disclosure and wording only. No measurement changed, no row was
promoted or demoted, no ruling changed, nothing is relabelled as an
improvement. The frozen protocol, `band.py`, the producer and every file
under `run_github_39882571652/` are unchanged; the band in `band.md` /
`band-v2.md` stays the record. New read-outs are computed from the
archived receipts by `disclosures.py` (output in
[`disclosures-20261106/`](disclosures-20261106/disclosures.md)), and every
number below is from that output unless it says otherwise
`[pcc:unverified]`.

## CAX-2: every counter, field-kind sensitivity, crossover weights

Section 5a asks for every unpriced counter of every arm with its count.
[`disclosures-20261106/disclosures.md`](disclosures-20261106/disclosures.md)
§1 lists every counter of S, P and rT with its mean count per target
(one band unit) and its class in the frozen kind map (group, unpriced, reported but
not priced, bounded).

The field kinds (`field_mul`, `field_sqr`, `field_inv`,
`field_half_trace`) are reported, not priced, by the frozen map, as
constituents of priced kinds. They are 7.197e9 operations per S target
(against 3.093e9 unpriced) and 1.093e10 per P target (against 4.688e9).
Charged at w as well (sensitivity, beside the band, never instead of it):

| arm | map | gap w = 0 | w = 0.1 | w = 1 | crossover w* (rho scalar muls at 0 GAE) | w* (at 104 GAE) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| S | frozen | 0.01138 | 29.00 | 115.5 | 0.0028551 | 0.0028563 |
| P | frozen | 0.01141 | 43.93 | 175.0 | 0.0018804 | 0.0018812 |
| S | field kinds charged | 0.01138 | 96.43 | 384.2 | 0.00085479 | 0.00085514 |
| P | field kinds charged | 0.01141 | 146.4 | 583.3 | 0.00056274 | 0.00056297 |

The crossover w* is the weight at which the arm's mean cost equals rT's:
the IC arm is cheaper only if one unpriced native operation costs less
than w* GAE (S: about 1/350 of a group addition under the frozen map,
about 1/1170 with field kinds charged). The rulings are unchanged under
the sensitivity: S vs rT and P vs rT unresolved, and the S vs P order
the same as in the band (see CAN-3 for its single-seed caveat).

## CAN-2: the band unit leaves two phases uncharged; the IC costs are lower bounds

The unit "S = kS's rank stage + cS's setup, linear algebra and online"
(PROTOCOL.md) is not all of the IC's work:

- **Factor-base construction.** Every IC process loads the K600 base from a
  file (`base_source` `retained_header`); `ec_frobenius` (base
  construction) is 0 in every phase of every IC record. Its measured wall
  time X = 427.524 ms (replay run 39007026856, Intel Xeon Platinum 8573C;
  `docs/ic/baselines.json` other_records[13].uncharged_phases) would be at
  most 2.27e6 GAE if all of it were group additions at this run's rT step
  (188.33 ns per walk step). That bound mixes hosts and is for
  illustration only. With it, the w = 0 gap would be at most 0.267 for S
  and for P (band: 0.01138 / 0.01141), still below 1.
- **Linear algebra.** The unit takes the cold process's checked load of
  the cached factor-log table, not the rank process's solve: kS's and kP's
  `linear_algebra` phase holds 179,700 `la_mulmods` outside the unit.
  Adding them moves the w = 1 gap from 115.5026 to 115.5093 (S) and from
  175.0188 to 175.0255 (P).

So the IC costs in the band are **lower bounds** on the IC's work, and the
w >= 0.1 gaps are lower bounds on the IC's distance to rho. No ruling
changes. Counting base construction needs a counted run that constructs
the base in process (see "Runs needed" below).

## CAN-3: the intervals exclude rank-seed variance; S < P at w = 0 is single-seed

- The paired bootstrap resamples the 20 cold points only. kS and kP are
  one rank process each (seed 101), so the rank stage, 97.44% of S's
  unpriced work (96.72% of P's), is a constant in every resample. The
  intervals carry rho's and the cold arm's point-to-point spread, not
  rank-seed spread.
- The archived twin (run 38862448935) has a second rank draw (seed 102)
  with 1.01377x kS's rank probes and 0.97307x kP's. Scaling the rank stage
  by those ratios (an extrapolation: the uncounted twin emits no other
  rank counters) gives S / rT about 29.38 / 117.1 and P / rT about 42.79 /
  170.5 at w = 0.1 / 1, inside the reported intervals.
- "S is cheaper than P at every weight" rests, at w = 0, on S / P =
  0.997317: a 272-group-operation difference between one kS and one kP
  rank draw. It is an order at one rank seed, not a ranking across rank
  seeds.
- The bootstrap bounds depend on the Monte-Carlo draw at the third
  significant figure (S at w = 0.1, upper bound: 39.54 at the frozen seed
  20261023, 39.30 at seed 1, 39.00 at 40,000 draws; full table in
  `disclosures.md` §4). Quote them to 3 significant figures: S / rT 0.0114
  [0.00877, 0.0155], 29.0 [22.3, 39.5], 116 [88.9, 158]; P / rT 0.0114
  [0.00879, 0.0156], 43.9 [33.8, 59.9], 175 [135, 239]. The frozen
  `band.md` digits are unchanged.

## CAN-4: chronology of protocol, data and acceptance analysis

Checked from the git objects and the archived `runs.jsonl` on 2026-11-06:

| event | time (UTC) | evidence |
| --- | --- | --- |
| counted producer and band script | 2026-10-23 01:05:00 | commit `3fa629a09` |
| protocol frozen | 2026-10-23 01:11:19 | commit `765061e1b`, parent of the run head `1a6067f63` |
| first run (serial 1, kS) | started 01:23:55, finished 01:26:49 | `runs.jsonl` `finished_unix_s` - `process_wall_ms` |
| last run (serial 62, rT) | started 01:56:40, finished 01:56:42 | the same |
| acceptance analyzer `analyze_v2.py` | 02:59:00 (19:59:00 -07:00) | commit `ad1fbc64d` |

The acceptance analysis postdates the data by about an hour. It is
stricter only: it adds the complete-panel gate and calls the unchanged
band arithmetic, and its counts and band are byte-identical to the
in-run v1 output, so there is no forking-path effect on any number.
`765061e1b`, `ad1fbc64d` and `3fa629a09` are not on `main` (squash
merge #1077). They are reachable from `refs/pull/1077/head` (`8b205273`,
also `claude/ic-group-op-counts`) and `765061e1b` from
`claude/n83-opcounts-run` (`1a6067f63`); preregistration is provable only
from those refs. `ANALYSIS_V2.md` carries the same table.

## CAN-5: memory beside the band

| arm | runs | peak RSS (median) | stored table entries (mean) |
| --- | ---: | ---: | ---: |
| kS | 1 | 1,876 MB | 29,878,182 (1 GiB root table) |
| cS | 20 | 1,875 MB | 29,878,182 |
| kP | 1 | 5,813 MB | 29,878,182 (4 GiB slots) |
| cP | 20 | 5,813 MB | 29,878,182 |
| rT | 20 | 18.62 MB (18.44 to 56.71) | 138,876 |

The IC arms use about 101x (S) and 312x (P) rT's median peak RSS (33x and
103x its maximum). The band compares GAE only. On memory every IC arm is
worse than rT, so the w = 0 end of the band, where IC is cheaper in GAE,
is not a Pareto point: rT is undominated at every weight.

## CAX-3: the second run of the v2 analysis

The README sentence "A second run reproduced every output byte for byte"
and the same words in `ARTIFACT.json` cited nothing: no output, hash or log
of that 2026-10-23 run was committed, and none is recoverable. Two new runs
on 2026-11-06 reproduce all four archived v2 outputs byte for byte;
their hashes and the exact inputs are in
[`analysis_v2-reproduction-20261106/`](analysis_v2-reproduction-20261106/REPRODUCTION.md).
The claim now cites that record, not the uncommitted run.

## CAX-1, K-N1, K2: which row is current; runs needed

Since 2026-11-04 the n = 83 baseline row is the field-ops producer
(`koblitz-n83-fieldops-20261104`, `docs/ic/baselines.json` baselines[4]);
the rank-finder producer (other_records[20]) is the former baseline. The
README's 2026-10-23 wording "the current rank-finder baseline row" is a
dated status. Neither row has a section 5a band.

Runs needed (not done here; recorded so that nothing is claimed in their
place):

1. **Field-ops band (K-N1).** Port the counters (`op-counts` feature) to
   the field-ops derivation, freeze a protocol like `PROTOCOL.md` with its
   own K block and 20-point cold panel against a matched rT, run it, and
   compute the band with `band.py` (and these disclosures). The same holds
   for the rank-finder row if its band is wanted. This is producer porting
   and a new measured run, not a record fix.
2. **Factor-base construction counted (K2, CAN-2).** A counted run in
   which each IC rank process constructs the K600 base in process
   (`construct:83:1:600`, as the replay did for wall time) so that
   `ec_frobenius` and the lift and projection work are counted into the
   unit.
3. **Rank-seed spread (CAN-3).** Count at least a second rank seed (the
   twin's seed 102) for kS and kP so that the rank stage enters the
   interval.
