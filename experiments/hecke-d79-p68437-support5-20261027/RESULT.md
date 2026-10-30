# Five-source trace cancellations close the p68437 rational relation space

On the frozen 40-point D79 class over `F_68437`, an indexed signed pair–triple enumeration finds **87 verified degree-13 outside-trace relations of support five**. Adding them to the 416-row support-at-most-four baseline raises rational rank from 34 to **40**. The independent Sage audit exhaustively checked all `C(40,5)·16 = 10,528,128` canonical signed patterns in each arm and reproduced the exact candidate sets and ranks.

| Row system | New support-five relations | Rational rank | Rank over `F_109` |
| --- | ---: | ---: | ---: |
| Frozen base + direct + degree-13 support ≤4 | — | 34 | 34 |
| Baseline + direct support five | 196 | 39 | 39 |
| Baseline + degree-13 trace support five | 87 | **40** | 39 |
| Baseline + both support-five arms | 283 | **40** | 39 |

The producer indexes 3,120 signed pairs and probes them with 39,520 signed triples, restricting each match to five distinct indices with the global smallest index in the triple. It records 1,176 and 522 raw pair–triple matches; each canonical direct or trace relation appears in six splits. Exact deduplication yields the 196 and 87 rows above. Every row is independently replayed as a group equation on `E: y²+y=x³−x²−10x−20` over `F_68437`. An additional checked-Sage audit constructs the order-109 subgroup coordinate vector: 38 of its 40 entries are nonzero, and all 699 combined rows annihilate it. Together with the mod-109 minor certificate, this identifies the one-dimensional remaining subgroup-log freedom for this exact class matrix.

`inputs.json` froze the parent class, source, analysis and audit receipt hashes before enumeration. `pre_run.json` pinned the indexed producer before it ran; `post_run.json` pinned its output before the exhaustive Sage audit. `post_audit.json` and `post_q_audit.json` bind the two independent audit receipts. The cross-linked verifier passes. The original source fibers, curve and class identities were retained from the prospectively selected p68437 holdout; no new class or target was selected after the rank-34 result.

The indexed producer measured 57.3 ms for direct and 56.3 ms for trace candidate generation, with 0.6 and 2.1 ms of its row group-law checks. The separate Sage exhaustive audits took 41.3 and 45.0 seconds. These are different implementations and operation boundaries on an ordinary shared host; the timing contrast is a diagnostic, not a calibrated speedup. The full 10,528,128-pattern count was audited in each arm under the 1,800-second job cap. `candidate_id` and `target_online_ms` remain null; reusable class/source construction and target handling are outside this relation-space experiment.

The finite Lean kernel and minor certificates, along with the written rank proof and formalization boundary, are in [PROOF_MAP.md](PROOF_MAP.md). The next experiment should stop source lifting at the first support-five rank-completing prefix on this frozen case, then test that stopping rule prospectively on newly selected primes. Its cost record must include unsuccessful prefixes and all source-dependent work.
