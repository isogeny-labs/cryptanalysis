# Gain-forest cycle harvester, k = 3 large primes: protocol (frozen before any result was read)

Date: 2026-11-22. Branch `claude/gaudry-gain-forest-harvester` (base cryptanalysis main `6b64ee6c`).
Background: `RESEARCH_RESIDUAL_WALKS.md` 11.7, 11.10, 11.11; `graph-theory-ic-20261121/followups/beyond-m3/BEYOND_M3.md` section 4 item 2.
All numbers produced under this protocol are `[pcc:unverified]`.

## Question

Does harvesting cycles of the large-prime graph with a gain-tracking forest (union-find with affine
expressions over `Z/nZ`, sink-pinning, and 3-uniform 2-core peeling of decompositions with three
large primes) lower the end-to-end cost `S` of the Gaudry `k = 3` double-large-prime variant on
`E(F_{p^3})`, against the structured eliminator that 11.11 calls "uncapped"?

## Arms (paired per seed, same instance, same base, same RNG seed)

- **A (eliminator)**: `--protocol-la --groebner --sizes 271,523,1039,2083 --seeds 6 --lp-rule --max-lp 2`
  with the default harvester. This is the arm 11.11 calls uncapped; its behaviour is byte-for-byte
  the pre-change code path.
- **B (cycles)**: the same command plus `--harvester cycles --max-lp 3`.
- Only the large-prime arm of `--protocol-la` (Wiedemann + Gaudry rule `|F'| = ceil(|F|^{2/3})`)
  is compared; the dense and plain-Wiedemann control arms do not depend on the harvester.
- Stop rule unchanged: the run ends when the linear-algebra system pins `d` (confirmed by one
  scalar multiplication in the group). `mu` = harvested rows at stop is reported in addition.

## Statistic (as in 11.11)

Per seed: the end-to-end total-ops exponent (least squares of `log2 total_ops` on `log2 n` over the
sizes) and `S` at each size. Report the mean of per-seed differences (B minus A) with its standard
error (sample sd / sqrt(seeds)) and the sign split. Also per full relation: residuals, row weight,
LA ops, merge ops.

## Verdict rule (pre-registered)

**PASS** if S is lower for the harvester at two or more sizes with the paired difference more than
2 standard errors (mean of B minus A below zero by more than 2 SE) **and** the exponent difference
(B minus A) is not above +0.05. **FAIL** otherwise.

Prediction (model, not measurement): `S` at `p = 523` falls from about 8 600 to about 3 700.

## Inadmissible

Changing the sizes or the seed range after seeing data; dropping a seed; reading a kill, timeout or
OOM as a negative (it is a resource limit and is reported as such); quoting a speedup in `S` without
the paired standard error; counting a run whose recovered logarithm was not group-checked; claiming
anything about rho or deployment sizes from these four sizes.

## Design notes fixed in advance

- Large primes are the base columns `> small` (the `d` column sits at index `small` and is a
  small-base unknown in the harvester). The existing eliminator filters `c >= small` and therefore
  treats `d` as a vertex; this is documented and, because it may confound the comparison, an extra
  diagnostic arm A' (`--eliminator-d-small`, eliminator with large primes `> small`) is run beside A
  and B. A' is not part of the verdict rule.
- Harvester multiplications modulo `n` are charged to `lp_merge_ops` and `la_ops`, so `S` is built
  from the same ledger as the eliminator's.
- If `p = 2083` with six seeds exceeds the time budget, `p = 2083` is run with two seeds and the
  statistic at that size and for the exponent uses those seeds (stated in RESULTS.md).
