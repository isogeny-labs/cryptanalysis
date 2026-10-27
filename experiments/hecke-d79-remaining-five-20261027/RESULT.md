# Five-prime D79 support-four relation-space census

Across the five remaining primes of the frozen eight-case screen, verified degree-13 Hecke trace cancellations add a rational row-space dimension beyond the direct arm at **p=8597** and, jointly with the direct arm, at **p=12197**. At **p=12637**, the direct arm reaches rational rank 40 while the Hecke arm reaches 35. The other two cases have rational rank 40 in each arm. These are exact, source-indexed relation-rank results for the 40-point conductor-four class.

## Frozen construction and result

The curve is `E: y²+y=x³−x²−10x−20` over each `F_p`, with `p=v²+316`. The five values are the first five primes of the [frozen eight-case panel](../hecke-d79-coset-q-panel-20261027/inputs.json); the other three have individual followups. Each case reproduced the 40 class points from the hash-pinned class receipt, built Hecke degrees 2, 5, and 13 from the pinned source, lifted all 14 degree-13 neighbors at each source, checked the Hecke sum and modular polynomial, and obtained 40 `OUTSIDE_CLASS_TRACE` statuses. No source produced a class-closed row or equal-trace source pair. The degree-13 factor patterns match the per-case prespecification.

Both arms enumerate the same 772,240 distinct signed index patterns of support one through four, fixing the first coefficient to `+1` and iterating the remaining coefficients in `[-1,+1]` order. Direct rows are zero sums of class points. Hecke rows are zero sums of the independently computed aggregate outside traces, with their class parts added at the same coefficients. The base consists of the 20 degree-2/5 rows. The table reports independently audited ranks of base plus each arm and base plus both arms; `q` is the largest prime factor of the curve order.

| p | #E(Fp) | q | direct rows (s3/s4) | Hecke rows (s3/s4) | rank over Fq: direct / Hecke / both | rank over Q: direct / Hecke / both |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 3797 | 3880 | 97 | 404 (19/385) | 438 (14/421) | 39 / 39 / 39 | 40 / 40 / 40 |
| 8237 | 8255 | 127 | 289 (9/280) | 275 (3/272) | 39 / 39 / 39 | 40 / 40 / 40 |
| 8597 | 8520 | 71 | 291 (8/283) | 251 (3/248) | 39 / 39 / 39 | 39 / 40 / 40 |
| 12197 | 12280 | 307 | 258 (5/253) | 206 (0/206) | 39 / 39 / 39 | 39 / 39 / 40 |
| 12637 | 12655 | 2531 | 231 (3/228) | 254 (1/253) | 39 / 35 / 39 | 40 / 35 / 40 |

The earlier support-four receipts complete the same frozen eight-case selection: [p14957](../hecke-d79-p14957-rank-20261027/RESULT.md) has direct/Hecke/both ranks `39/39/39` over `F1489` and `40/40/40` over `Q`; [p26237](../hecke-d79-p26237-rank-20261027/RESULT.md) has `35/35/39` over `F137` and `35/35/40` over `Q`; [p36037](../hecke-d79-p36037-rank-20261027/RESULT.md) has `37/34/39` over `F1451` and `37/34/40` over `Q`. Thus complementarity varies across the fixed cohort: it is present at p12197, p26237 and p36037, while p8597 has a Hecke-only rational lift over the direct arm.

For the rank statements, the written linear-algebra proof uses a full-rank selected-row minor over `F_q` for each lower bound and independent explicit kernel vectors for each upper bound; the subgroup-log audit supplies a curve interpretation of one nonzero kernel vector. Over `Q`, a full-rank minor modulo 3 (modulo 7 at `p=8597`) gives the lower bound; the explicit integer kernel vectors give the upper bound for ranks below 40. The generated Lean modules check the finite and integer kernel and inverse-minor certificates. The proof map records the remaining Lean bridge from those certificates to general matrix rank and from the independently checked curve identities to the generated matrices.

## Measurement boundary and replay

All jobs completed below the declared input caps; the recorded launch commands did not add an external timeout. The producer's measured phase totals were 37.2, 36.8, 37.1, 35.6, and 44.5 seconds in ascending `p` order. Median signed enumeration time across three alternating-order repetitions was 1.33–1.74 seconds for the direct arm and 6.94–11.67 seconds for the Hecke arm on this shared host. The Hecke arm constructs aggregate trace sums from degree-13 lifts outside those signed-enumeration intervals. These exploratory stage timings are retained in the machine-readable panel receipt with individual repetitions, startup/runtime information, producer phases, and peak RSS; the row ranks do not imply a full-pipeline time comparison. `candidate_id` and `target_online_ms` are null in every result.

For each case, the independent Sage audit rebuilt the class using Hilbert class polynomial roots, refactored the 40 degree-13 fibers, recomputed every direct and Hecke candidate in the frozen order, checked every row on the curve, and independently recomputed ranks over `Q` and `F_q`. A separate subgroup-log audit checked that all base, direct, and Hecke rows annihilate actual projected class-point logs modulo `q`. All ten audit receipts have `PASS` status. The producer, analysis, audits, per-case frozen inputs, SHA-256 hashes, and exact stdout/stderr are in the subdirectories; [panel-result.json](panel-result.json) verifies their cross-links.

The next experiment should reduce the number of degree-13 lifts and cancellation searches needed to reach the complementary rational dimensions at `p=8597` and `p=12197`, charging source construction, unsuccessful searches, row verification, and linear algebra to the selected strategy.
