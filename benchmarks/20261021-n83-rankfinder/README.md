# n = 83 rank finder (Tier 1, repeated alternating pairs)

Copies of the inspected report and result graph. The raw receipt, protocol and
verifier are in `experiments/koblitz-n83-rankfinder-20261021/` (run
39527997793).

| File | Content |
| --- | --- |
| `report.pdf` | the experiment's README.pdf: design, gates, secondaries, host and isolation records |
| `result.pdf`, `result.svg`, `result.png` | frozen ratios with 95% bootstrap intervals |

Primary: R = E2E(kM38IC + cM38IC) / E2E(kM38RF + cM38RF) = 1.0196 [1.0147,
1.0255] over 36 alternating pairs, one GitHub-hosted runner, one pinned CPU
(Tier 1, instance scope). Factor-base construction is charged to no arm.
