# CT190 — block-baseline falsification and fixed-effect treatment diagnostic (prospective)

2026-11-17 UTC. **[pcc:unverified]**. Source-only protocol frozen before implementation and synthetic outcome. This is a *diagnostic* for the physical A/B timing design, not a new transfer algorithm, execution permission, proof, or speedup.

## Source review and hypothesis

The merged CT188 `ct188_physical_crossover_design.py` uses the exact frozen 48 public packets, eight six-slot blocks per packet and six unique four-position two-A/two-B physical sequences (plus duplicated ABBA/BAAB), and fits a seven-column per-packet log-time model: intercept, three periods, B treatment, previous-B, and B×previous-B. The 2,304-position proposed v3 producer is in draft [CT189 #1729](https://github.com/isogeny-labs/cryptanalysis/pull/1729). CT188 controls for *period*, not independent block-level cold-start/host-load offsets. CT185/186 previously found different order and sham confounding. Original fixture remains identified by Git blob `9ac741668dd1ffa9632ff0d58e6f4dd9f2dd18c3` and physical roster digest `1bc8c26a01e7952e57d944fd535c9832607f2ab7bcc910342ad704171ab67af1`.

**Null hypothesis to falsify:** for a packet `p`, in each block `b` and treatment position `i=0..3`, both physical routes have equal intrinsic cost but `log T[p,b,i]=alpha[p,b]+period[p,i]` (a common multiplicative block-wide latency factor). The CT188 estimator may report nonunit treatment despite correct per-period treatment balancing and a clean final A/A control, because its nuisance model has no `alpha[p,b]`. A source-only counterexample is not evidence such correlated load exists on hardware.

## Prospective correction

Add a **separately versioned** `ct190_block_fixed_effect_diagnostic.py`, importing the *existing* CT188 roster and its strict record validator rather than modifying CT188/CT189 or their data. Fit, independently for each of 48 packets, exactly eight block intercepts, three period indicators, physical-B, previous-B, and B×previous-B, 14 columns against the 32 first-four-slot observations. Eliminate block intercepts by within-block demeaning on log durations; then solve the 6×6 normal equations with pivot/finite checks. Do not use A/A slots for treatment estimation; use the existing CT188 full 2,304-record roster/AA validation and preserve its A/A diagnostic and original estimator side by side for direct contrast.

Prove exact design rank 14 over the rationals for every packet before any treatment report (and rank 6 after block demeaning), with no synthetic observation driving rank. Report per-packet coefficients and medians; no naive process-level confidence interval or claim of causal identification beyond the additive block/period/first-order model. Fail closed for incomplete/reordered/incorrect physical arm, malformed or nonpositive durations, rank deficiencies or nonfinite coefficients. Status remains [pcc:unverified].

## Falsification and controls

Source-only normal Python and optimized `-O` tests must cover:
1. Exact pinned 48×8×6 roster and 14-column rational rank per packet.
2. Equal intrinsic algorithm cost and uniform timings -> original and corrected contrasts both 1.00.
3. Equal intrinsic algorithm cost, **packet-specific common block latency**, chosen in advance mathematically to expose the omitted-variable risk -> original CT188 contrast materially nonunit, corrected approximately 1.00, and all A/A within-block ratios 1.00.
4. Programmed 1.25 direct/B intrinsic cost with identical block shocks -> corrected 1.25, not 1.00; test nonzero first-order carryover separately.
5. Missing/altered physical observations, wrong roster, and zero/non-integer times reject.

These synthetic times are deliberately generated, **not native hardware measurements**. Hold the original 48 fixture, 695/701 custody, CT189 producer, CT188 reader, Rust evaluator, previous v1/v2/sham records, CT125 norm-point source, and all ongoing PR branches untouched. No paid EKS/Spot/GPU or unapproved local benchmark. Final acceptance requires exact-head source CI and ordinary PCC/review gates for any subsequent merge.

## Unchanged scientific gate

This diagnostic neither prices actual `C169,C13a,C13b,N2_actual,D` nor closes the original whole-corpus/native-parity gap, nor solves a prime-field ECDLP. Complete cold single-target baseline/candidate comparisons must still count admission, setup, transfer, linear algebra, inversion, individual logarithm, verification, memory, paired uncertainty and independent signed PCC; stronger rho/BSGS/IC baseline determines the ratio. [pcc:unverified]

## Sources checked

- Merged [CT188 #1725](https://github.com/isogeny-labs/cryptanalysis/pull/1725): original exact seven-column design, roster, conditional estimator.
- Draft [CT189 #1729](https://github.com/isogeny-labs/cryptanalysis/pull/1729): physical cold-process producer and 21-counter reader.
- [CT173 norm price audit](CT173_NORM_POINT_PRICE_PATH_AUDIT.md): `D_padd` is not the actual `N2_actual` operation.
- Merged [crypto #4215](https://github.com/isogeny-labs/crypto/pull/4215), [cryptanalysis #1523](https://github.com/isogeny-labs/cryptanalysis/pull/1523), [GPU IC #4178](https://github.com/isogeny-labs/crypto/pull/4178) and original [#3877](https://github.com/isogeny-labs/crypto/pull/3877).
- Research-KB MCP and autoresearcher shared lab-contract were not exposed/decodable in this connector runtime; no novelty or absence claim is made.
