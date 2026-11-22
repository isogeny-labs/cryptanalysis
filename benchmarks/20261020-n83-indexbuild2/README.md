# n = 83 index build, round 2 (Tier 1, repeated alternating pairs)

Copies of the inspected report and result graph. The raw receipt, protocol and
verifier are in `experiments/koblitz-n83-indexbuild2-20261020/` (run
39464544962).

| File | Content |
| --- | --- |
| `report.pdf` | the experiment's README.pdf: design, gates, secondaries, host and isolation records |
| `result.pdf`, `result.svg`, `result.png` | frozen ratios with 95% bootstrap intervals |

Primary: R = E2E(kM38IB + cM38IB) / E2E(kM38IC + cM38IC) = 1.1169 [1.1110,
1.1231] over 36 alternating pairs, one GitHub-hosted runner, one pinned CPU
(Tier 1, instance scope). Factor-base construction is charged to no arm.
