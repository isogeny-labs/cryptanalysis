# n = 83 online frame, round 2 (Tier 1, repeated alternating pairs)

> Integration note, 2026-10-21: this frozen experiment compares online-frame round 2 with the round-2 index-build producer. The newer rank-finder result landed separately in #1013. This result is retained in `docs/ic/baselines.json` under `other_records`; it does not replace the current rank-finder baseline, and no combined or cross-host delta is claimed. References to the current row in the frozen report mean the row at protocol freeze. Independent replay of the complete retained receipt reproduces `result.json` and `result_table.md` byte for byte.


Copies of the inspected report and result graph. The raw receipt, protocol and
verifier are in `experiments/koblitz-n83-onlineframe2-20261021/` (run
39527549698).

| File | Content |
| --- | --- |
| `report.pdf` | the experiment's README.pdf: design, gates, secondaries, layout check, host and isolation records |
| `result.pdf`, `result.svg`, `result.png` | frozen ratios with 95% bootstrap intervals |

Primary: R = E2E(kM38IC + cM38IC) / E2E(kM38OF + cM38OF) = 1.0165 [1.0110,
1.0221] over 64 alternating pairs, one GitHub-hosted runner, one pinned CPU
(Tier 1, instance scope). The online stage ratio (1.5541 [1.5324, 1.5766]) is
a labelled stage result. Factor-base construction is charged to no arm.
