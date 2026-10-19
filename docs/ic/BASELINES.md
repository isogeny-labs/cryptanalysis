# Index-calculus baselines: the ratchet

**Status (2026-10-15).** This is the first edition of the ledger, with the tuned-rho
rows added from run 38777903922. It takes no new measurement: every number is
copied from a committed experiment, and each row cites that experiment. Figure 1
was checked and stays current: no baseline row's numbers changed. The n=83 rows for lift_scan, the Feistel order and their (not promoted)
combination were added on 2026-10-15; Figure 1 was checked and stays
current, because no baseline row's numbers changed. The n=83 row for the probe pipeline was added on 2026-10-16, the two-level root table and the state fold the same day, each with the same Figure 1 check. On 2026-10-16 the stacked producer (`koblitz-n83-stacked-20261016`, run 38862448935) replaced B's n=83 baseline row, and Figure 1 was re-rendered. Also on 2026-10-16, an accounting correction (sheriff case SHF-20261016-3caa6f, K3 and K4): the n=83 row's `s_ic_setup` was 0.8856, which is setup without the rank stage plus online, while every other row's (B's 32.848 included) is cold minus online with the rank stage in it. It is now 9.6673 on that one meaning, and the B → stack ratchet entry records the paired within-run delta. No measurement changed, and Figure 1 (gaps only) is unchanged. Also on 2026-10-16, disclosures from the same case (K1, K2, R1; no number changed): the n=83 row's headline and `S` are wall time on one host class, with the host-independent operation-count ratio (rank-stage probes and root calls 1.4773x) beside it; factor-base construction is charged to neither arm, so the row's ratio is an upper bound and its cold `S` a lower bound; the §5a GAE band is not computable from that run; and the run was not replayed on another host class. On 2026-10-17, corrections from re-audit SHF-20261017-e4d7f6 (K-N1, K-N2, K-N4; no measurement changed): the setup convention now names what each row leaves out (both n=83 rows leave out factor-base construction; B's row also leaves out 51.3 ms of linear algebra and 32.3 ms of input control, now listed in its JSON `uncharged_phases`); the B → stack history entry's standard gap fields now hold the paired within-run gaps, with B's cross-run figures under `cross_run_context_*`; the n=83 rank stage rounds to 8.7949 (8.79486), not 8.7948; and 2.2837 is per-probe wall time, not a host-speed factor. A replay of rank block K1 with one timed base construction is preregistered (`experiments/koblitz-n83-replay-20261017/PROTOCOL.md`). Figure 1 (gaps only) is unchanged. On 2026-10-17 that replay was archived (`experiments/koblitz-n83-replay-20261017/RESULTS.md`, [run 39007026856](https://github.com/aburan28/cryptanalysis/actions/runs/39007026856)): `replay_pass` on another host class (Intel Xeon Platinum 8573C), rank-stage work identical, per-probe wall ratio 2.6583 there against 2.2905 on the EPYC; construction time X = 427.5 ms is now measured. The n=83 row's replication and uncharged-phase notes record it; no figure of the row changed, and Figure 1 is unchanged. On 2026-10-19 the rank-cut producer (`koblitz-n83-rankcut-20261016`, run 38891404048) replaced the stacked producer's n=83 baseline row (end-to-end cold 1.3336 [1.3300, 1.3377] over the stack, wall time on one host class, probes and root calls unchanged), and Figure 1 was re-rendered. Also on 2026-10-19 the rank-probe producer (`koblitz-n83-rankprobe-20261019`, run 39214027289) replaced the rank-cut producer's n=83 baseline row (end-to-end cold 1.1033 [1.1010, 1.1056] over the rank-cut producer, wall time on one host class, probes and root calls unchanged), and Figure 1 was re-rendered. Also on 2026-10-19 the index-lift producer (`koblitz-n83-indexlift-20261019`, run 39290913632) replaced the rank-probe producer's n=83 baseline row (end-to-end cold 1.0344 [1.0324, 1.0364] over the rank-probe producer with a shared rank stage, wall time on one host class, stored states and table slots byte-identical, probes and root calls unchanged), and Figure 1 was re-rendered. The machine-readable twin is
[`baselines.json`](baselines.json); update both files in the same change.

## The rule this file serves

AGENTS.md, "Success criterion: iterative improvement of the index-calculus
baseline" (owner, 2026-10-15; cryptanalysis#919, crypto#1908):

- **The baseline** for a curve and size is the best current verified IC
  pipeline. It is frozen with its protocol, receipts and end-to-end cold `S`.
- **A success** is any verified, measured improvement over that baseline on
  the same instances, under a protocol frozen before timing. Advance and
  engineering both count. Relabelling and accounting are recorded and do not
  count.
- **The ratchet.** A landed improvement replaces the row here, and the old
  row moves to [the history](#ratchet-history) with its delta.
- **The gap** to the matched rho, and to Bernstein–Lange (BL) where it was
  measured, is the distance remaining. It is not a pass/fail gate. A claim
  to *beat* rho still needs every reference rule: a cold `S` below the
  matched rho's, robust at growing `n`, independently replayed.

**How to read the numbers.**

- **One row, one experiment.** No row combines numbers from two experiments.
  Where an experiment did not measure a quantity, the cell says so.
- **Every gap is IC cost over the reference's cost.** Above 1 is distance
  still to close; below 1 means the IC is cheaper on that boundary. The
  sources quote the online figure the other way up (rho over IC). That
  figure is kept in each JSON row's `source_figure`.
- **`S` = cost / √r**, in the row's own unit. The unit differs between
  experiments, so compare `S` inside a row only. The gaps carry no unit.
- **Setup `S` has one meaning on every row:** `s_ic_setup` =
  `s_ic_cold` - `s_ic_online`: the reusable work for the first target that
  the row's experiment charged, the relation-collection / rank stage and the
  linear algebra (or the verified load of its cached table) included, less
  every phase the JSON row names in `uncharged_phases`. Only n=41–61 (rule
  v3, which builds the factor base inside setup) charge all reusable work.
  Both n=83 rows leave out factor-base construction (the K600 base is loaded
  from a file); B's row also leaves out its linear algebra (51.3 ms) and
  setup input control (32.3 ms), 0.015% of its P_IC. n=19 has no setup `S`. Where the rank stage is timed on its
  own (n=83), the JSON row also splits it into `s_ic_rank_stage` +
  `s_ic_setup_without_rank_stage`. "Cold without the rank stage" is a
  different quantity and is never written into `s_ic_setup`.
- **Tuned rho** means rT770: A's tuned `StrongRhoG` (Fold field kernel, 64
  lanes, DP 6, escape off). `koblitz-n83-reconcile-20261014` found it to be
  the fastest correct n=83 reference. At n=41–61 it has been run as rT770's
  configuration on the one-word kernel (`koblitz-s23-tuned-rho-20261015`).
  ParallelRho, inside crypto's `ic price`, is crypto's own signed-Frobenius
  walk (64 lanes in lockstep). It is the matched rho at n=41–61, but it is
  not rT770.

## The baselines

| n | curve | current best verified IC pipeline (commit; protocol) | targets | `S` cold / online (IC) | `S` cold / online (rho) | cold gap, IC / rho [95%] | online gap, IC / rho [95%] | gap to tuned rho (rT770) | gap to BL (online, IC / BL) | evidence tier | next improvement to try |
|--:|:------|:----------------|:------|-------:|-------:|-------:|-------:|:----------|:-------|:------|:------------|
| 19 | E0 / GF(2^19), a=1 | volcano-ic τ-orbit dim-6 base, Sage Gröbner (arm `tau6`); cryptanalysis `3f722e2e`; protocol.json of volcano-ic/ rho-arm-20261014; run 38520305068 | 10 planted scalars, each one complete ECDLP | 5,154 / not separable | 0.260 / — | **1.94e4** [1.69e4, 2.23e4] (CPU, geometric mean) | not measured: each IC run is cold | none; the matched rho is a signed-Frobenius walk at 0.997× the floor in steps, run in Python/Sage, not tuned for wall time | none | exploratory (GitHub VM, unpinned) | Move tau6's per-relation Gröbner solve out of Sage (native, or the subspace `PDP2ht` oracle); re-run against the same rho arm |
| 41 | K_0 / GF(2^41) | `ic price --single-target` at IC programme baseline v3: 6,560 points, 80 columns, aimed m=3 collection, m=2 pair-table descent; crypto `995ea207`; rule v3 | 64 public points, 1 process each, +4 A/A | 11.17 / 0.121 | 1.459 / 1.318 | **7.66** [6.90, 8.61] | 0.092 [0.071, 0.116] | **measured in a separate experiment, not combined**: see the 41 row of Other verified records (run 38777903922: online IC/tuned 0.09, cold 6.6); the matched rho in this row is ParallelRho (0.56× the strong walk's ns/step) | model only: 2.21 | crypto isolated_bench container | Setup is 98.9% of cold `S`: cut the reusable setup at fixed recipe, as a new IC programme round against v3 |
| 53 | K_0 / GF(2^53) | same pipeline, 27,984 points, 264 columns; crypto `995ea207`; rule v3 | 64 + 4 A/A | 16.98 / 0.058 | 1.282 / 1.236 | **13.2** [11.8, 15.0] | 0.047 [0.036, 0.059] | **measured in a separate experiment, not combined**: see the 53 row below (online 0.0423, cold 10.6); ParallelRho here is 0.53× strong | model only: 1.77 | crypto isolated_bench container | Setup is 99.7% of cold `S`: cut it at fixed recipe; then price the n=53 representative-plus-Frobenius orbit domain as its replacement |
| 61 | K_0 / GF(2^61) | same pipeline, 39,040 points, 320 columns; crypto `995ea207`; rule v3 | 64 + 4 A/A | 24.93 / 0.079 | 1.189 / 1.168 | **21.0** [18.6, 23.8] | 0.067 [0.051, 0.088] | **measured in a separate experiment, not combined**: see the 61 row below (online 0.0687, cold 18.9); ParallelRho here is 0.50× strong | model only: 3.52 | crypto isolated_bench container | Setup is 99.7% of cold `S`, and the cold gap grows as r^0.18: cut the setup; price the compact-orbit K=500 producer on these 64 points |
| 83 | K_1 / GF(2^83) | the index-lift producer (arms cPI / kPI): the rank-probe producer with lift_scan in the root-index build (`KIC_INDEX_CANON=lift`: the canonical key and shift of each stored state's two normal-basis roots by the two-limb lift_scan canonicalizer; same stored states, same 29,880,600 inserts in the same order, same table slots word for word, byte-identical layout digests); B's `koblitz_orbit_dlp_fast_online` + `ic_log_cache.patch`, K600 (99,600 points, 600 orbit columns), lift_scan x Feistel + prefetched probes + 16-byte compact root slots + folded S3 root index (14,940,300 stored states), rank stage's partner roots by point addition in the target's Frobenius frame (candidate ID below); crypto `770f6a69`; `koblitz-n83-indexlift-20261019/protocol.json` at cryptanalysis `8d06c09d9`; run 39290913632 | 20 new public points, three rank blocks (seeds 401-403, shared rank stage), Q0 | 6.366 / 0.01512 (wall time in rT770 steps, 280.33 ns, one host class; setup 6.351, of which rank stage 5.718; factor-base construction not charged, so cold is a lower bound; measured X = 0.43 s gives 6.382, illustrative) | 0.1011 / 0.0908 | **62.9** [52.5, 78.5] (end-to-end cold: shared rank stage + setup + online; wall time, one host; §5a band not computable) | 0.167 [0.091, 0.283] | **measured on this row**: end-to-end cold 62.9, online 0.167 | not measured on this row (B's 235 [61, 645] is in Other verified records) | Tier 1 (GitHub runner, one pinned CPU, CPU-only); one run; not replayed on another host class | The rank stage is still 148.4 s of the 165.2 s end-to-end cold cost (90%) and probes are unchanged (1.75 M per attempt): cut the per-probe cost further or the probes per relation, then setup (the Feistel scan order's exhaustive self-test, 1.87 s per cold process; cPIT, a secondary, 1.0460 over the rank-probe producer, is not promoted); re-run the BL arm on this producer |

![Distance to the matched rho and to Bernstein–Lange, per baseline row.](figures/baselines_gap.png)

*Figure 1. The baseline rows' gaps on a log scale: cold and online to the
matched rho, and online to Bernstein–Lange (a model; the one measured n=83
BL gap is in B's row, now under Other verified records). Each row is one experiment. Bars are 95% intervals where the
source gives one ([source](figures/baselines_gap.tex),
[vector](figures/baselines_gap.pdf)).*

**Curves and candidates.**

| n | curve ID | ICV1 slug | r | IC1 candidate of the baseline |
|--:|:----------|:-------------|---------:|:---------------------------------|
| 19 | `EC1N19Ckb1h01617b86df6c` | (volcano-ic surface curve E0) | 130,873 | none recorded |
| 41 | `EC1N41Ce0he09550ab560a` | `icv1-f2m41-tm2308219-7f48b14a` | 549,756,390,943 | `IC1N41Ckb0fb6560PDP3pairtableRCaimedLAsparseTDwalkISO0h5b25909970b3` |
| 53 | `EC1N53Ce0hb097de99be9a` | `icv1-f2m53-tm56619371-dac20a85` | 21,044,858,204,113 | `IC1N53Ckb0fb27984PDP3pairtableRCaimedLAsparseTDwalkISO0h715dd7692112` |
| 61 | `EC1N61Ce0hd8c15448081e` | `icv1-f2m61-t158598901-ab42b6c5` | 162,888,033,982,417 | `IC1N61Ckb0fb39040PDP3pairtableRCaimedLAsparseTDwalkISO0he9352435e473` |
| 83 | `EC1N83Ce1h35c7ced6b497` | `icv1-f2m83-t6151469093347-9eba6cd5` | 8,569,786,107,849,059 | `IC1N83Ckb1fb99600PDP4s3rootindexRCguidedLAdenseTDsingleISO0hc0ecc1fffbd7` |

**Notes on the rows.**

- **n=19.** The `S` unit is one rho group operation of CPU time
  (2.17e-5 s). The IC's cold `S` is the τ6 arm's CPU per ECDLP in that unit.
  The baseline subspace base reads 1.77e5× rho in the same run. τ6 over the
  baseline base is 9.12 [8.12, 10.27].
- **n=41–61.** The unit is one batched affine addition, measured in each
  row's own process. v3's unit is 2.3–3.2× cheaper than §23's, so `S` is
  not compared across the two (rule v3 README). Every row passes
  `validate_claim` at `vs_rho` (68/68 per size). Both certificates were
  replayed outside the process, and the logarithms equal §23's.
- **n=83.** `S` is derived inside the one run (39290913632): wall ms divided
  by that run's measured rT770 step (280.33 ns) and by sqrt(r), so one unit is
  25,950.6 ms. End-to-end cold is the shared rank stage K (148,384.4 ms, the
  mean over three rank blocks of the mean of kP and kPI; 5.718, 5.71795
  unrounded) plus the mean cold (setup 16,420.2 ms including the verified
  load of the cached factor-log table, 0.6327, plus online 392.3 ms, 0.0151)
  over the 20 points: 6.366. Setup, rank stage included, is 6.351 (5.71795 +
  0.63275 = 6.35069); cold without the rank stage is 0.6479. BL was not run
  on this producer.
  - *Wall time, one host class.* The headline 1.0344 and every `S` are wall
    time from one run on one GitHub runner, not operation counts. The
    stored states and the table slot array are byte-identical (stored-state
    blake3 `d8cfe443...` and table-slot blake3 `5f53764e...` in all 110 IC
    processes, equal to the frozen values), and every relation, per-attempt
    probe count (mean 1,746,508), root-call total and point-addition counter
    is equal across kP and kPI, so the operation counts did not change. The
    saving is index-build wall time (19,778.4 ms against 14,106.3 ms, 1.4021
    [1.4004, 1.4036]); the planted control cPIX (every root keyed by lift_scan
    and checked against the selected canonicalizer, 29,880,600 roots, no
    difference) costs 1,184.6 ms more than cP. The rank stage is shared, not
    a treatment: kPI / kP per attempt 0.9981 [0.9966, 0.9994].
  - *Uncharged phase.* Factor-base construction is charged to neither arm
    (common to both, so R > 1 holds for any X; 1.0344 is an upper bound and
    cold `S` 6.366 a lower bound). At the X measured on another host class
    (427.5 ms) the every-phase figures are R 1.0343 and cold `S` 6.382:
    illustrative, mixing two hosts.
  - *§5a band.* Not computable: the IC arms emit no group additions, scalar
    multiplications, canonicalizations, fold rotations or index inserts.
  - *Replication.* Not replayed on another host class. The stacked row's
    replay found the per-probe wall ratio host-dependent, and index-build
    wall time has not been replayed either, so the same caution applies to
    1.0344.
  - *Not comparable across runs.* This run's rT770 step (280.33 ns), shared
    rank stage (148.4 s) and online mean (392.3 ms) differ from run
    39214027289's (280.64 ns, 143.7 s, 303.8 ms), so the row's `S` and gap
    are not a delta of the rank-probe row; the paired ratio and the paired
    within-run gaps (cP 65.1 [53.9, 81.0] to cPI 62.9 [52.5, 78.5]) are.
- **n=83, the rank-probe producer (Other verified records).** `S` is derived inside the one run (39214027289): wall ms divided
  by that run's measured rT770 step (280.64 ns) and by √r, so one unit is
  25,980.1 ms. End-to-end cold is the mean rank stage (143,706.7 ms over four
  rank blocks, 5.531; 5.53141 unrounded) plus the mean cold (setup 21,995.0 ms
  including the verified load of the cached factor-log table, 0.8466, plus
  online 303.8 ms, 0.0117) over the 20 points: 6.390. Setup, rank stage
  included, is 6.378 (5.53141 + 0.84661 = 6.37802); cold without the rank
  stage is 0.8583. BL was not run on this producer.
  - *Wall time, one host class.* The headline 1.1033 and every `S` are wall
    time from one run on one GitHub runner, not operation counts. The
    operation counts did not change: the gates make every relation,
    per-attempt probe count (mean 1,690,645), root-call total and
    point-addition counter equal across kR, kP, kPaa and kPX, so the
    operation-count ratio is 1.0000. The rank-stage wall ratio 1.1193 is
    entirely per-probe wall time (158.45 ns against 141.54 on this host): the
    conjugate root's candidates computed in the target's Frobenius frame
    instead of mapped between the normal and polynomial bases twice. The
    planted control (278.82 ns per probe) prices the removed work at about
    137 ns per probe.
  - *Uncharged phase.* Factor-base construction is charged to neither arm
    (common to both, so R > 1 holds for any X; 1.1033 is an upper bound and
    cold `S` 6.390 a lower bound). At the X measured on another host class
    (427.5 ms) the every-phase figures are R 1.1030 and cold `S` 6.406:
    illustrative, mixing two hosts.
  - *§5a band.* Not computable: the IC arms emit no group additions, scalar
    multiplications, canonicalizations, fold rotations or index inserts.
  - *Replication.* Not replayed on another host class. The stacked row's
    replay found the per-probe wall ratio host-dependent, and the same caution
    applies to 1.1033.
- **n=83, the rank-cut producer (Other verified records).** `S` is derived inside the one run (38891404048): wall ms divided
  by that run's measured rT770 step (281.01 ns) and by √r, so one unit is
  26,013.6 ms. End-to-end cold is the mean rank stage (173,150.9 ms over four
  rank blocks, 6.656; 6.65617 unrounded) plus the mean cold (setup 22,245.8 ms
  including the verified load of the cached factor-log table, 0.8552, plus
  online 297.9 ms, 0.0115) over the 20 points: 7.523. Setup, rank stage
  included, is 7.511 (6.65617 + 0.85516 = 7.51133); cold without the rank
  stage is 0.8666. BL was not run on this producer.
  - *Wall time, one host class.* The headline 1.3336 and every `S` are wall
    time from one run on one GitHub runner, not operation counts. The
    operation counts did not change: the gates make every relation,
    per-attempt probe count (mean 1,790,030) and root-call total equal across
    kS, kR, kRaa and kRX, so the operation-count ratio is 1.0000. The
    rank-stage wall ratio 1.3768 is entirely per-probe wall time (221.85 ns
    against 161.10 on this host): the batched S3 root solve replaced by point
    addition. The planted control (302.05 ns per probe) prices the removed
    work at about 141 ns per probe.
  - *Uncharged phase.* Factor-base construction is charged to neither arm
    (common to both, so R > 1 holds for any X; 1.3336 is an upper bound and
    cold `S` 7.523 a lower bound). At the X measured on another host class
    (427.5 ms) the every-phase figures are R 1.3328 and cold `S` 7.539:
    illustrative, mixing two hosts.
  - *§5a band.* Not computable: the IC arms emit no group additions, scalar
    multiplications, canonicalizations, fold rotations or index inserts.
  - *Replication.* Not replayed on another host class. The stacked row's
    replay found the per-probe wall ratio host-dependent, and the same caution
    applies to 1.3336.
- **n=83, the stacked producer (Other verified records).** `S` is derived inside the one run (38862448935): wall ms divided
  by that run's measured rT770 step (316.66 ns) and by √r, so one unit is
  29,314.2 ms. End-to-end cold is the mean rank stage (257,814.3 ms over two
  rank processes, 8.795; 8.79486 unrounded) plus the mean cold (setup 25,575.2 ms including the
  verified load of the cached factor-log table, 0.8725, plus online 385.1 ms,
  0.0131) over the 20 points: 9.680. Setup, rank stage included, is 9.667
  (8.79486 + 0.87245 = 9.66731; each `S` is rounded once from its unrounded
  quotient, so rounded parts need not add up exactly);
  cold without the rank stage is 0.8856. The row first landed with
  `s_ic_setup` 0.8856, the cold-without-rank figure; read against B's 32.848
  (rank stage included) that looked like a 37× setup drop, which was
  accounting (corrected 2026-10-16, `corrections` in the JSON). BL was not
  run on the stack.
  - *Wall time, one host class.* The headline 3.2391 and every `S` are
    wall time from one run on one GitHub runner (AMD EPYC 9V74, one pinned
    CPU, CPU-only), not operation counts. The host-independent part is
    the rank stage's operation counts: probes 2,976,293,514 (kP) against
    2,014,683,345 (kS) and root calls 1,488,248,100 against 1,007,441,716,
    both 1.4773x fewer. The rank-stage wall ratio 3.3737 is that 1.4773
    times 2.2837 in wall ns per probe (584.48 against 255.94), measured on
    this host only. That factor is per-probe wall time, not host speed: a
    kP probe (full canonicalization) and a kS probe (lift_scan, compact
    table, prefetch loop) are not the same work, so it mixes cheaper
    per-probe work with host and memory-system effects. Stored
    index states halve (29,880,000 to 14,940,300); online probes are equal
    (cP / cS 1.000133). Setup and index build emit no comparable count, so
    there is no single end-to-end operation-count ratio.
  - *Uncharged phase.* Factor-base construction is charged to neither arm:
    every process loads the K600 base from a file. It is common to both
    arms, so the ratio stays above 1 for any construction cost X, but
    3.2391 is an upper bound and cold `S` 9.680 a lower bound on the
    every-phase figures (X = 1 s: 3.231 and 9.715; 10 s: 3.163 and 10.02;
    60 s: 2.848 and 11.73). **X measured (2026-10-17):** one cold in-process
    construction (`construct:83:1:600`, base hash equal to the retained
    file's) took X = 427.524 ms in the replay below, 65.541 ms more than
    loading the retained file on the same host (361.984 ms). At that X the
    every-phase figures are R 3.2357 and cold `S` 9.6950 (gap 94.56):
    illustrative, since X is from the Intel replay host and the rest from the
    EPYC run. The bounds 3.2391 and 9.680 are within 0.11% and 0.15%.
  - *§5a band.* Not computable from this run: the IC arms emit no group
    additions, scalar multiplications, canonicalizations, fold rotations or
    index inserts, so the gap 94.4 has no 0 / 0.1 / 1 GAE band and holds
    as a wall-time figure on this host only.
  - *Replication.* Rank block K1 was replayed on another host class on
    2026-10-17: [run 39007026856](https://github.com/aburan28/cryptanalysis/actions/runs/39007026856) on an
    INTEL(R) XEON(R) PLATINUM 8573C (the original: AMD EPYC 9V74; same
    image, kernel, toolchain and binary sha256), under the protocol frozen
    at `863f6090` (`experiments/koblitz-n83-replay-20261017/PROTOCOL.md`;
    archived in `RESULTS.md` there). Verdict `replay_pass`: all six runs
    valid; kS, kP, kP, kS reproduce every per-attempt probe count (first
    100 and all 600) and the relation digest of the archived K1 records;
    the constructed base equals the retained one. Not gated: the per-probe
    wall ratio kP / kS is 2.6583 there (first 100 attempts 2.7013) against
    2.2905 for K1 on the EPYC (2.2837 both blocks), so the 3.24x wall-time
    headline is host-dependent, while the operation-count ratio 1.4773
    stands. The replay did not re-measure the cold arms, so it gives no new
    R or `S`; one replay, one other host class, two processes per arm. It
    emits no group-operation counts, so the §5a band stays uncomputable
    (Open).
- **n=83, B (Other verified records).** `S` in B's run is wall ms over that
  run's rT770 step (180.8 ns) and √r. Cold is the matched precomputation
  P_IC (520,825 ms rank stage + 29,022 ms per-process setup; `s_ic_setup`
  32.848 = 31.114 + 1.734) plus the mean online time. P_IC leaves out
  factor-base construction (the base is loaded from a file), the linear
  algebra (51.3 ms) and setup input control (32.3 ms); the JSON row names
  them in `uncharged_phases`. BL's precomputation
  was matched to P_IC in wall time on the same CPU, so the cold IC/BL ratio
  is 0.987 by construction. If PR #918 changes, that row changes with it.

## Other verified records

These rows are kept for context and as the history behind the baselines.
None is combined with another row.

| n | role | experiment | reference | cold gap, IC / ref [95%] | online gap, IC / ref [95%] | BL | tier |
|--:|:-------|:----------------|:---------|-------:|-------:|:-----|:-------|
| 41 | previous baseline (v0) | ledger §23, crypto `0bf67f16` | ParallelRho, same process | 8.04 [7.26, 9.01] | 0.107 [0.082, 0.135] | model 2.50 | crypto isolated_bench container |
| 53 | previous baseline (v0) | ledger §23 | ParallelRho | 14.7 [13.1, 16.7] | 0.057 [0.044, 0.073] | model 2.02 | same |
| 61 | previous baseline (v0) | ledger §23 | ParallelRho | 31.6 [28.2, 35.7] | 0.113 [0.084, 0.148] | model 8.04 | same |
| 41 | other pipeline, complete cold CPU | crypto `disjoint_cold_v2_outcome_20261001` (run 36803331080), compact-orbit K85 | 32-walk signed-Frobenius normal-basis rho (not rT770) | 13.4 [9.37, 18.5] | not measured | none | hosted, A/A and quiet-host gates, second-host replay |
| 53 | other pipeline, complete cold CPU | same, compact-orbit K220 | same | 22.7 [17.9, 31.6] | not measured | none | same |
| 61 | other pipeline | crypto autolab run `20261012T202048Z-5521627904`, compact-orbit K=500 | strong rho rung 3 (not rT770) | 83.4 (median of rows) | 0.072 [0.052, 0.102] (inverse of median 13.94) | none | taskset-pinned container with a CPU-isolation receipt |
| 41 | gap to the tuned rho (this experiment only; cf. the baseline row) | `koblitz-s23-tuned-rho-20261015`, run 38777903922 (PR #923) | tuned = rT770 configuration on the one-word kernel; same run: ParallelRho cold 7.83, strong 6.43, rA770 2.54 | **6.6** [5.91, 7.4] | **0.09** [0.0715, 0.111] | model 0.53 | Tier 1 |
| 53 | gap to the tuned rho (this experiment only; cf. the baseline row) | `koblitz-s23-tuned-rho-20261015`, run 38777903922 (PR #923) | tuned = rT770 configuration on the one-word kernel; same run: ParallelRho cold 11.8, strong 9.2, rA770 3.01 | **10.6** [9.45, 12] | **0.0423** [0.0325, 0.0534] | model 0.322 | Tier 1 |
| 61 | gap to the tuned rho (this experiment only; cf. the baseline row) | `koblitz-s23-tuned-rho-20261015`, run 38777903922 (PR #923) | tuned = rT770 configuration on the one-word kernel; same run: ParallelRho cold 19.4, strong 13.7, rA770 4.42 | **18.9** [16.7, 21.5] | **0.0687** [0.051, 0.0903] | model 0.759 | Tier 1 |
| 83 | previous baseline (B, the BL-arm row), superseded by the stacked producer | `koblitz-n83-bl-arm-20261014`, run 38689817618 (PR #918, not merged yet) | rT770, B's 16 fresh points + Q0 x4 | 360 (no interval; S 32.93 / 0.083 in that run's rT770 steps) | 1.01 [0.30, 2.12], not separated | **measured: 235** [61, 645], 16/16 points BL faster; cold IC/BL 0.987 by construction | Tier 1 |
| 83 | previous baseline (the stacked producer, arms cS / kS), superseded by the rank-cut producer | `koblitz-n83-stacked-20261016`, run 38862448935 (PR #938) | rT770, 20 new points, two rank blocks, Q0 | 94.4 [73.5, 125.3] (end-to-end cold; S 9.680 / 0.01314 in that run's rT770 steps, 316.66 ns) | 0.139 [0.077, 0.237] | none on this row | Tier 1 |
| 83 | previous baseline (the rank-cut producer, arms cR / kR), superseded by the rank-probe producer | `koblitz-n83-rankcut-20261016`, run 38891404048 (PR #970) | rT770, 20 new points, four rank blocks, Q0 | 65.7 [55.4, 80.2] (end-to-end cold; S 7.523 / 0.01145 in that run's rT770 steps, 281.01 ns) | 0.110 [0.059, 0.174] | none on this row | Tier 1 |
| 83 | previous baseline (the rank-probe producer, arms cP / kP), superseded by the index-lift producer | `koblitz-n83-rankprobe-20261019`, run 39214027289 (PR #980) | rT770, 20 new points, four rank blocks, Q0 | 64.0 [53.7, 78.0] (end-to-end cold; S 6.390 / 0.01169 in that run's rT770 steps, 280.64 ns) | 0.129 [0.085, 0.183] | none on this row | Tier 1 |
| 83 | same pipeline as the baseline (merged) | `koblitz-n83-reconcile-20261014`, run 38617911080 | rT770, two seeds per point | 313 (fresh-rank setup) | 0.92 [0.28, 1.78], not separated | none | Tier 1 |
| 83 | same pipeline, first Tier 1 run | `koblitz-single-target-n83-tier1-20261014`, run 38523707244 | rung 3, slower per step than StrongRhoG, so not the matched tuned rho | 134 | 0.36 [0.11, 0.66] | model 33.5 (measured later: 235) | Tier 1 |
| 83 | promoted single improvement over B: two-limb `lift_scan` canonicalizer (this experiment only) | `koblitz-n83-liftscan-20261015`, run 38776966036 (PR #926) | rT770, B's 16 fresh points | cold not measured | IC/rho 0.67 [0.19, 1.38] (inverse of 1.4914 [0.7270, 5.1445]); online full / lift_scan 1.5152 [1.5061, 1.5247] | none | Tier 1 |
| 83 | promoted single improvement over B: Feistel scan order (this experiment only) | `koblitz-n83-scanorder-20261015`, run 38786433493 (PR #927) | rT770, B's 16 fresh points | cold not measured | IC/rho 0.291 [0.163, 0.481] (inverse of 3.4370 [2.0774, 6.1418]); online left-major / Feistel 3.4287 [1.0090, 7.4215]; held-out 384: 1.4507 [1.2023, 1.7424] | none | Tier 1 |
| 83 | **not promoted**: lift_scan x Feistel order combined (this experiment only) | `koblitz-n83-combined-20261015`, run 38803625711 | rT770, 576 new points | cold not measured | IC/rho 0.2145 [0.1949, 0.2353] (inverse of 4.6628 [4.2501, 5.1308], means); frozen primary R_m 1.2363 [1.0671, 1.4276], R_g 1.0611 [0.9083, 1.2430]: `not_separated`; combined vs B 1.9992 [1.7285, 2.3090] | none | Tier 1 |
| 83 | promoted improvement over the combined producer: software-pipelined, prefetched root-table probes (this experiment only) | `koblitz-n83-probepipe-20261015`, run 38822490448 | rT770, 384 new points | cold not measured | IC/rho 0.1462 [0.1307, 0.1626] (inverse of 6.8396 [6.1494, 7.6526]); combined producer 0.2047; online combined / pipeline 1.4001 [1.3971, 1.4032], probes identical | none | Tier 1 |
| 83 | promoted improvement over the probe-pipeline producer: two-level root table, 32 MiB filter + 16-byte slots (this experiment only) | `koblitz-n83-tablefilter-20261015`, run 38829449594 | rT770, 384 new points | cold not measured against rho; cold pP / pT 1.0101 [1.0090, 1.0113] | IC/rho 0.1523 [0.1358, 0.1709] (inverse of 6.5642 [5.8533, 7.3649]); pipeline 0.1620; online pP / pT 1.0633 [1.0589, 1.0679], probes identical, mostly from the 16-byte slot | none | Tier 1 |
| 83 | promoted improvement over the combined producer: folded S3 root index, cold (this experiment only) | `koblitz-n83-state-fold-20261015`, run 38819494806 | rT770, 16 new points | 6.95 [5.53, 9.01] (cB 12.77; setup + online, rank stage excluded; with the rank stage 109.6, was 243.3) | IC/rho 0.163 [0.090, 0.241]; online 5% slower; cold cB / cF 1.8372 [1.8216, 1.8528], setup 1.86×, peak RSS 1.97× | none | Tier 1 |

## Ratchet history

| n | from | to | cold gap | online gap | class |
|--:|:--|:--|:--|:--|:--|
| 41 | §23 (v0, `0bf67f16`) | rule v3 (`995ea207`) | 8.04 → 7.66 | 0.107 → 0.092 | engineering (IC programme rounds R03, R05, R07) |
| 53 | §23 (v0) | rule v3 | 14.7 → 13.2 | 0.057 → 0.047 | engineering |
| 61 | §23 (v0) | rule v3 | 31.6 → 21.0 | 0.113 → 0.067 | engineering |
| 83 | B | lift_scan canonicalizer (PR #926, run 38776966036) | not measured | not measured (online 1.5152 faster, fresh 16) | engineering; promoted by its own frozen rule; baseline row not replaced (no cold `S`) |
| 83 | B | Feistel scan order (PR #927, run 38786433493) | not measured | not measured (online 1.4507 faster, held-out 384) | advance (probe count); promoted; baseline row not replaced (no cold `S`) |
| 83 | better single arm (lift_scan) | lift_scan x Feistel (run 38803625711) | not measured | R_m 1.2363 [1.0671, 1.4276]; R_g 1.0611 [0.9083, 1.2430] | **not promoted**: frozen primary `not_separated` |
| 83 | lift_scan x Feistel combined producer | software-pipelined, prefetched probes (run 38822490448) | not measured | 0.2047 → 0.1462 (online, tuned rho; 1.4001 faster) | engineering; promoted by its own frozen rule; baseline row not replaced (no cold `S`) |
| 83 | probe-pipeline producer | two-level root table (run 38829449594) | not measured | 0.1620 → 0.1523 (online, tuned rho; 1.0633 faster) | engineering; promoted by its own frozen rule; baseline row not replaced (no cold `S` against rho) |
| 83 | lift_scan x Feistel combined producer | folded S3 root index (run 38819494806) | 12.77 → 6.95 (rank stage excluded) | not improved (online 5% slower) | engineering; promoted by its own frozen rule; baseline row not replaced (rank stage still dominates cold cost) |
| 83 | pP, the probe-pipeline producer with B's rank stage (same run; this replaced B's baseline row, run 38689817618) | stacked producer: probe pipeline + 16-byte slots + folded index + rank stage (run 38862448935) | **paired, this run:** 305.8 [237.5, 403.8] → 94.4 [73.5, 125.3] (end-to-end cold, from pP with B's rank stage; 3.24× closer). Context only: B's own run read 360 (a different run, instances and step time) | **paired, this run:** 0.133 [0.072, 0.229] → 0.139 [0.077, 0.237]: online 4.6% slower in this step. Context only: B's run read 1.01 | engineering; promoted by its own frozen primary (end-to-end cold cP / cS 3.2391 [2.9809, 3.5240] in wall time on one host class, factor-base construction excluded; rank-stage probes and root calls 1.4773x fewer; 20 points, two rank blocks, against the probe-pipeline producer); **baseline row replaced**: the first measured n=83 end-to-end cold `S` after B (9.68; was 32.93 in B's run, a different step time) |
| 83 | the stacked producer (arms kS + cS), same run 38891404048, points and rT770 (this replaced the stacked baseline row, run 38862448935) | rank-cut producer: partner roots by point addition in the rank stage (run 38891404048) | **paired, this run:** 87.6 [74.1, 107.2] → 65.7 [55.4, 80.2] (end-to-end cold; 1.33× closer). Context only: the stacked row as landed read 94.4 (a different run, instances and step time) | **paired, this run:** 0.1107 [0.0602, 0.1752] → 0.1101 [0.0590, 0.1744]: online unchanged (same code) | engineering; promoted by its own frozen primary (end-to-end cold kS+cS / kR+cR 1.3336 [1.3300, 1.3377] in wall time on one host class, factor-base construction excluded; probes and root calls unchanged, the saving is per-probe wall time 221.85 → 161.10 ns, rank stage per attempt 1.3770 [1.3735, 1.3813]; 20 points, four rank blocks, against the stacked producer); **baseline row replaced** |
| 83 | the rank-cut producer (arms kR + cR), same run 39214027289, points and rT770 (this replaced the rank-cut baseline row, run 38891404048) | rank-probe producer: the rank-cut loop in the target's Frobenius frame (run 39214027289) | **paired, this run:** 70.6 [59.3, 86.3] → 64.0 [53.7, 78.0] (end-to-end cold; 1.10× closer). Context only: the rank-cut row as landed read 65.7 (a different run, instances and step time) | **paired, this run:** 0.1288 [0.0836, 0.1816] → 0.1291 [0.0847, 0.1830]: online unchanged (same code) | engineering; promoted by its own frozen primary (end-to-end cold kR+cR / kP+cP 1.1033 [1.1010, 1.1056] in wall time on one host class, factor-base construction excluded; probes, root calls and point-addition counters unchanged, the saving is per-probe wall time 158.45 → 141.54 ns, rank stage per attempt 1.1194 [1.1175, 1.1214]; 20 points, four rank blocks, against the rank-cut producer); **baseline row replaced** |
| 83 | the rank-probe producer (arms kP + cP, shared rank stage), same run 39290913632, points and rT770 (this replaced the rank-probe baseline row, run 39214027289) | index-lift producer: lift_scan in the root-index build (run 39290913632) | **paired, this run:** 65.1 [53.9, 81.0] -> 62.9 [52.5, 78.5] (end-to-end cold; 1.03x closer). Context only: the rank-probe row as landed read 64.0 (a different run, instances, rank seeds and step time) | **paired, this run:** 0.1667 [0.0926, 0.2808] -> 0.1666 [0.0914, 0.2830]: online unchanged (same online code) | engineering; promoted by its own frozen primary (end-to-end cold cP / cPI 1.0344 [1.0324, 1.0364] with a shared rank stage, in wall time on one host class, factor-base construction excluded; stored states and table slots byte-identical, probes, root calls and counters unchanged, the saving is index-build wall time 19,778 -> 14,106 ms, cold without rank 1.3376 [1.3340, 1.3406]; 20 points, three rank blocks, against the rank-probe producer); **baseline row replaced** |

The paired cold-time ratios between baselines, each in its own runs, are in
crypto `research/notes/index-calculus/IC_TOOL_PROGRAM.md` §7. The gaps above
are each against that comparison's own rho, and that rho also changed
between §23 and v3. So the gap delta is the distance remaining, not the IC's
own speedup.

## Stage results: canonicalization

Stage improvements are recorded here. One becomes a pipeline improvement
only once it moves an end-to-end `S` above.

| stage | n | experiment | result | tier | pipeline effect |
|:--|--:|:--|:--|:--|:--|
| normal-basis least rotation, isolated | 131 | `canon-n131-20261014` | Five exact canonicalizers on `[u64; 3]`. Ir per uniform word: lift_scan 514, gap_scan 1,435, exhaustive 1,850, exhaustive_bf 3,664, refine_bf 4,510. 0 mismatches. | deterministic Ir; wall times exploratory | none yet |
| the same, inside a decomposition-style loop | 131 | `canon-n131-loop-20261014`, run 38607684318 | lift_scan is fastest on all four workloads: 16/16 contrasts at Bonferroni, ratios 1.83–3.81. In-loop Ir over the loop floor: lift_scan 519, gap_scan 1,760, exhaustive 2,883. | Tier 1 for the timing | none yet. No n=131 pipeline exists, and at n=53 the isolated ranking did not survive the loop (`papers/frobenius-orbits` §4/§7) |

## Open

- **n=41, 53, 61:** the gap to the tuned rho is measured by
  `experiments/koblitz-s23-tuned-rho-20261015` (run 38777903922, PR #923;
  rows above, one per size, each from that experiment alone; n=47, 57 and 59
  are in its README). It ran rT770's configuration on the one-word `Gf2`
  kernel, because `Gf2_128` exists only for n > 64, and it measures about the
  same cost as ParallelRho. It is accounting: no IC change, so no baseline
  row moves. A rho tuned on the one-word kernel is not measured.
- **n=19 and n=41–61:** no Bernstein–Lange walk has run, so the BL figures
  are models or absent.
- **n=83:** the baseline row is the index-lift producer
  (`koblitz-n83-indexlift-20261019`, run 39290913632): the rank-probe producer
  with lift_scan in the root-index build, promoted end to end over the
  rank-probe producer (1.0344 [1.0324, 1.0364] with a shared rank stage, in
  wall time on one host class; stored states, table slots, probes and root
  calls unchanged; 20 points, three rank blocks). Its end-to-end cold `S` is
  6.37 against the tuned rho's 0.101 (gap 62.9 [52.5, 78.5]). The rank-probe
  producer (1.1033 [1.1010, 1.1056] over the rank-cut producer, run
  39214027289), the rank-cut producer (1.3336 [1.3300, 1.3377] over the
  stack, run 38891404048), the stacked producer (3.2391 [2.9809, 3.5240] over
  the probe-pipeline producer, run 38862448935) and B's row (experiment on
  PR #918, not merged yet) are in Other verified records. The rank stage is
  90% of the end-to-end cold cost; the run was not replayed on another host
  class, and the BL gap was not re-measured on this producer.
- **n=19:** IC1 candidate manifests now exist for the baseline and the
  native-solve candidate (`IC1N19Ckb0fb1064PDP2polyboriRCsampleLAkernelTDpdpISO0hb41aed7ef80a`
  and `IC1N19Ckb0fb1064PDP2nativeenumRCsampleLAkernelTDpdpISO0h6952f30ce00e`,
  in `experiments/volcano-n19-native-tau6-20261019/inputs/ic1_manifests.json`),
  and online `S` is separable by definition in that protocol (setup and
  online are timed apart). It has not been measured: the Tier 1 run
  ([39307409409](https://github.com/aburan28/cryptanalysis/actions/runs/39307409409))
  is invalid, because its S0 gate failed (Sage and native varieties equal on
  293 of 300 systems) and no timed row ran. The n=19 row, Figure 1 and the
  ratchet history are unchanged.
- **n=83, §5a band:** the 0 / 0.1 / 1 GAE band for the IC / rho gap is
  uncomputable on both n=83 rows, because the frozen producer emits no
  group-operation counts. The K1 replay (archived 2026-10-17) timed
  factor-base construction but used the same producer, so the band stays
  open until a producer that emits the counts runs under a new protocol.
- **n=83, construction time X (resolved 2026-10-17):** measured in
  `koblitz-n83-replay-20261017` ([run 39007026856](https://github.com/aburan28/cryptanalysis/actions/runs/39007026856)): X = 427.5 ms,
  65.5 ms over the retained-file load. Every-phase stacked R 3.2357 and cold
  `S` 9.6950 (illustrative, two hosts) against the row's 3.2391 and 9.680;
  the row's figures are unchanged. B's row uses the same base; its cold `S`
  was not recomputed.

## Updating this file

1. Freeze a protocol for the candidate improvement against the row's
   pipeline, on the same instances, before timing.
2. When the improvement lands, replace the row in `baselines.json` and in the
   table above. Add a history row with the before and after figures and the
   class (advance, engineering, relabelling, accounting). Relabelling and
   accounting do not replace a baseline.
   Give `s_ic_setup` its one meaning (`s_ic_cold` - `s_ic_online`, rank
   stage included), and record the history delta paired within the
   promoting run; figures from an earlier run go in as context only.
   Say whether the headline is wall time (and on which host class) or
   operation counts, give the operation-count ratio beside a wall-time
   one, name any phase the experiment did not charge, and say whether the
   §5a band was computable and whether the run was replayed elsewhere.
3. Name the next improvement to try in the new row.
4. Re-render Figure 1 and this file's PDF:

   ```sh
   cd docs/ic/figures && pdflatex baselines_gap.tex && pdftoppm -png -r 160 -singlefile baselines_gap.pdf baselines_gap
   cd .. && pandoc BASELINES.md -o BASELINES.pdf --pdf-engine=pdflatex -H pdf-header.tex -V geometry:landscape,margin=1.2cm -V fontsize=9pt
   python3 -m json.tool baselines.json > /dev/null
   ```

## Sources

- crypto `docs/ic/BOUNDARY_TARGETS.md` and `docs/ic/boundary_targets.json`
  (Regime B `vs_rho`; complete cold compact-orbit panel).
- crypto `research/notes/index-calculus/RESEARCH_IC_BOUNDARY_LEDGER.md` §23;
  `research/ic_single_target_20260930/` (PROTOCOL, analysis.json).
- crypto `research/ic_tool_program/rule/v3/` (README, PROTOCOL,
  analysis.json); `research/notes/index-calculus/IC_TOOL_PROGRAM.md` §7.
- crypto `research/notes/ecc2k130/disjoint_cold_v2_outcome_20261001/RESULT.md`.
- cryptanalysis `experiments/koblitz-n83-bl-arm-20261014/` (branch
  `claude/n83-bl-arm`, PR #918): README, `run_github_38689817618/result.json`.
- cryptanalysis `experiments/koblitz-s23-tuned-rho-20261015/`: README,
  `run_github_38777903922/panel/result.json` (PR #923).
- cryptanalysis `experiments/koblitz-n83-reconcile-20261014/`: README,
  `run_github_38617911080/panel/result.json`.
- cryptanalysis `experiments/koblitz-single-target-n83-tier1-20261014/`:
  README, `tier1_github_38523707244/`.
- cryptanalysis `experiments/volcano-ic/rho-arm-20261014/`: README,
  `results/summary.json`.
- cryptanalysis `experiments/canon-n131-20261014/` and
  `experiments/canon-n131-loop-20261014/`.
