# Coset-filtered MITM pair table: frozen ratchet protocol (draft for the owner's push)

- **Status.** Drafted 2026-11-21 in a cloud session that cannot push. **Retrospective / exploratory**: this
  file and the first data were produced in the same session, and nothing is committed yet, so the
  "frozen before timing" condition of AGENTS.md ("Track research work in pull requests") is met only
  by the owner's rerun after this file is committed (checklist step 6). Until then every number is
  `[pcc:unverified]`.
- **Lead.** `coset_filter=1` on the `mitm` and `mitm-frobenius` decomposition oracles (branch
  `claude/mitm-coset-class-filter`, commit `23d3424c`), found by the graph-theory note
  (`isogeny-labs/workspace`, `docs/notes/graph-theory-ic-20261121.md`, section 6; trunk PR #59) and
  screened by the lead-testing protocol (GT-02 phases 1 to 3 PASS, trunk
  `docs/notes/graph-theory-ic-20261121/GT-02-phase*-SUMMARY.md`). The trunk's harness never writes a
  `BASELINES.md` row (trunk `docs/lead-testing/PROTOCOL.md` section 7); this is the cryptanalysis-side
  protocol that section 7 asks for.
- **Class (BASELINES.md rule).** Engineering, stage level: the pair table of one decomposition oracle
  inside `ic bench`. It is reported as a stage improvement and becomes a pipeline improvement only if
  it moves end-to-end `S` of a baseline row's pipeline (AGENTS.md, "Improvement"). It does **not**
  replace any current `BASELINES.md` row: those rows are crypto's `ic price` pipelines at n = 41, 53,
  61 and the n = 83 / n = 19 producers, not `ic bench`'s `mitm` oracles (see "Ratchet sizes" below).

## 1. Hypothesis

On a curve with cofactor h > 1, a subgroup target `R = [a]G + [b]Q` can be written `P_i + P_j` only if the
classes of `P_i` and `P_j` in `E/<G>` cancel, so building only the class-cancelling pairs produces
**exactly the same relations, trials and recovered logarithm** as the full table and lowers counted
`S = ops / sqrt(r)` by the share of the table that no target can hit. Cofactor 2 labels are free
(`Tr(x) = Tr(a)`); larger cofactors cost one charged `[r]P` per signed pair. At cofactor 1 and at m = 3
the filter is a no-op by construction.

## 2. Arms (m = 2 only)

| arm | `ca-ic bench` flags (all else equal) | regime |
|:--|:--|:--|
| baseline (oracle) | `--oracle mitm` | char2: `--factor-base binary-subspace:dimension=D` |
| lead | `--oracle mitm:coset_filter=1` | char2 |
| baseline (oracle) | `--oracle mitm-frobenius` | koblitz: `--factor-base koblitz-orbit:divisor=V` |
| lead | `--oracle mitm-frobenius:coset_filter=1` | koblitz |

Common flags: `--repeats 8 --seed 20261121 --max-trials 8000000 --max-cofactor 8
--solver-budget-seconds 300 --targets walk (default) --linalg incremental-gauss (default)`;
`--rho-runs 8` on the baseline arm only (the matched rho is priced once per instance, in the baseline
process, by `ic bench`'s own rule: negation walk on char2, lower of signed-Frobenius and negation on
Koblitz). One process per arm. m = 3 is not run (the filter is a no-op there; PROTOCOL of the trunk
pairs it against the m = 2 baseline, which is a different question).

## 3. Instances, sizes and tiers

Ratchet sizes (BASELINES.md): n = 19, 41, 53, 61, 83. `ic bench` draws its own curve at a degree
(random binary curve with cofactor <= 8 for char2; the one Koblitz curve `ic` knows for a Koblitz degree)
and a factor base is a plug-in parameter, so a cell is a **degree**, not a BASELINES curve ID. What the
harness can run, measured in this session (raw in the S3 object named by the record):

| ratchet size | char2 cell | Koblitz cell | status here |
|--:|:--|:--|:--|
| 19 | `c2-19`, dim 6 (r = 65,617, h = 8; BASELINES' E0 has r = 130,873, so a different curve) | `ic bench --koblitz-degree 19`: 1 column at divisor 0, no verified base at any other divisor | char2 run; Koblitz harness limit |
| 41 | not run: `--char2-degree 41` did not finish drawing a curve in 300 s (resource limit) | the BASELINES curve itself (r = 549,756,390,943) but divisor `0` gives 2 columns and an unverified row, and `1`, `0;1` abort with a failed allocation (`oom_alloc`, 0.47 / 0.92 GiB peak) | not runnable; resource / implementation limit, not a negative |
| 53, 61 | not run | no row completes at divisors `0`, `1`, `0;1` (exit 1, no verified row) | not runnable here |
| 83 | not run | `ic: no Koblitz instance at degree 83` | not runnable here |

So the cells that run are the registry's size ladder plus the ratchet's smallest binary size:
char2 n = 19, 21, 23, 25, 27, 29 and Koblitz n = 23, 31, 43 (the divisors the lead-testing registry
checked: `0;1`, `0;1;2`, `1`). Two controls: `ctl-prime16` (prime 16-bit, size 40, cofactor 1: ratio must be
1) and `ctl-aa-c2-19` (the baseline arm run twice: the A/A ratio must be 1 within the noise floor of F3).
Koblitz n = 31 and 43 use the instance `ic` returns, whose cofactor is 1,492 and 1,894 (`r` is a small
prime factor of the group order); there the lead pays one scalar label per signed pair.

**Tier.** Wall time is not the measured quantity: `S` is counted group-addition equivalents, with the
non-group work (lookups, row operations) converted by `ic bench`'s per-operation calibration. That
calibration is pinned on prime-16, Koblitz n = 23 and 31 (S identical across processes) and measured
in-process on the char2 cells and Koblitz n = 43, where `S` moves by up to 0.04% between two runs of the
same arm (observed: 0.004% to 0.04% between this session's two passes; A/A ratio 0.9997 on char2-19). The recorded
host here is a shared 4 vCPU / 15 GiB cloud VM running other jobs, which meets neither Tier 0 nor
Tier 1 (AGENTS.md, "CPU performance evidence tiers"); no wall-time ratio is claimed. A Tier 1 wall
ratio needs a dedicated allocation and is not part of this protocol.

## 4. Seeds and repeats

`--seed 20261121` for every cell (distinct from the registry's 123145648762, 20261102, 20261104);
8 repeats per cell; the harness derives the repeat seeds and plants the same targets in both arms.
Pairing is repeat i against repeat i; a pair is valid only if both arms report the same instance,
`r`, repeat seed, relations found, targets tried and recovered logarithm and both verify `[d]G = Q`.

## 5. Statistic

Per cell, the geometric mean of the 8 paired ratios `S_baseline / S_lead`, with a 95% percentile
bootstrap of the mean log ratio (10,000 resamples of the 8 pairs, Python `random.Random(20261119)`,
2.5% and 97.5% order statistics): `analyze_ratchet.py`. The matched-rho distance `S / rho_S`
(baseline arm's mean over 8 rho runs) is reported beside it and is not a gate. Kills and timeouts are
rows (status `oom_killed`, `oom_alloc`, `timeout`, `crashed`), read as resource or implementation limits.

## 6. Falsifiers (any one stops a claim for the cell, or for the lead)

- **F1 exactness.** Any pair with different relations, trials or recovered logarithm, or any logarithm
  failing `[d]G = Q`: the lead is wrong; no ratio is read.
- **F2 gain.** A cell whose lower 95% bound is <= 1: no claim of a gain for that cell [pcc:unverified] (the claim is cut
  to the cells that pass, and the failing cell is listed).
- **F3 null controls.** `ctl-prime16` (cofactor 1) outside [0.999, 1.001], or the A/A control
  `ctl-aa-c2-19` outside [0.999, 1.001] (the in-process calibration noise floor measured here is
  0.03%): the instrument has a bias; no ratio from the run is read. A cell whose lower bound is within
  0.1% of 1 is read as 1.
- **F4 accounting.** The lead's setup GAE must include the label cost (it does: the scalar labels are
  charged in the oracle's setup); a lead whose `setup_gae` excludes a label cost is relabelling.
- **F5 scope.** A sign that the gain depends on the size choice (BASELINES.md: sizing artefacts do not
  count): the factor-base parameters are the registry's, identical in both arms, so a ratio >1 here is a
  ratio at fixed base, not a base-size effect.

## 7. Claims to run after the data

Both claim texts below are `[pcc:unverified]` until the verdicts are signed.

```sh
# claim 1: exactness (measurement), proofs recompute (validator report) + replay certificate
python3 tools/pcc/pcc.py claim new --kind measurement --claim-type data \
  --statement "coset_filter=1 returns identical relations, trials and logarithms to the plain mitm / mitm-frobenius table on every paired repeat (8 repeats x 9 cells + controls), all verified" \
  --scope "ca-ic bench m=2, seed 20261121, cryptanalysis 23d3424c, cells in docs/ic/mitm-coset-filter-ratchet-20261121/PROTOCOL.md" \
  --proof recompute:<validator-report.json> --proof replay:<replay-certificate.json>

# claim 2: counted-S speedup, stage level (speedup kind: recompute + replay)
python3 tools/pcc/pcc.py claim new --kind speedup --claim-type data \
  --statement "Stage improvement: coset_filter=1 lowers counted S of the m=2 MITM pair table by geometric-mean ratios in [LOW, HIGH] across char2 n=19..29 and Koblitz n=23, 31, 43, lower 95% bootstrap bound > 1 on every cell; no claim about end-to-end ECDLP, no claim against rho" \
  --scope "ic bench stage level, counted S, shared-VM host (no isolation tier), retrospective until the confirmatory rerun" \
  --proof recompute:<validator-report.json> --proof replay:<replay-certificate.json>
```

The validator report and replay certificate must be produced by a key the producer does not hold
(`pcc` rule); until they exist the numbers stay `[pcc:unverified]`. Replace `[LOW, HIGH]` with the
confirmatory run's numbers.

## 8. Reporting

Observed values (the 8 paired ratios, the intervals, the S means, the matched-rho distance) are kept
apart from model values (the table-share predictions of the graph-theory note section 6). A
cell that could not run is listed with its limit. No adjective on significance; no claim at m >= 3;
no claim for prime fields (cofactor 1, a no-op); no extrapolation to n = 41..83 curves that `ic bench`
cannot build.
