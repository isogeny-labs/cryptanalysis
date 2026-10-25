# n = 83 index build (Tier 1, repeated alternating pairs)

Copies of the inspected report and result graph. The raw receipt, protocol and
verifier are in `experiments/koblitz-n83-indexbuild-20261020/` (run
39383739494).

| File | Content |
| --- | --- |
| `report.pdf` | the experiment's README.pdf: design, gates, secondaries, host and isolation records |
| `result.pdf`, `result.svg`, `result.png` | frozen ratios with 95% bootstrap intervals |

Primary: R = E2E(kM38I + cM38I) / E2E(kM38IB + cM38IB) = 1.7406 [1.7129,
1.7676] over 36 alternating pairs, one GitHub-hosted runner, one pinned CPU
(Tier 1, instance scope). Factor-base construction is charged to no arm.
