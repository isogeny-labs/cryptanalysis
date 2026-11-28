# M31 Metal bitmap width: 20 versus 22 bits

Frozen source and protocol: commit `b365797a7`, [PROTOCOL.md](PROTOCOL.md). The five public Q and three independent walk seeds were paired across 30 fresh-process arms; all arms solved with independently checked public scalars. Every pair matched complete-field certificate digest, queries, relation count and rank. `verify.py` passed. The raw process, setup and work records are in `RAW.jsonl`, with source hashes and schedule in `MANIFEST.json`. These are producer-run local results without independent PCC standing. [pcc:unverified]

| Measure | 20-bit Metal | 22-bit Metal |
| --- | ---: | ---: |
| Median process wall, 15 arms each | 185.634 ms | 166.339 ms |
| Median child CPU, 15 arms each | 99.897 ms | 84.182 ms |
| Median GPU-positive candidates | 1,561,687 | 395,719 |
| Median exact CPU lookups | 1,165,056 | 294,226 |
| Median paired 20/22 wall ratio | — | **1.128×** |
| Median paired 20/22 CPU ratio | — | **1.215×** |
| 22-bit wins, wall / CPU | — | 14/15 / 15/15 |

The candidate cuts bitmap positives by a paired median 3.945×, but the frozen ≥1.15 paired wall gate **failed**. It is not selected as the new default. The CPU gate and win counts passed; this does not override the wall failure. The lower positive rate suggests the remaining cost is the GPU bitmap access or fixed full-lane scan. [pcc:unverified]

The later fixed-input phase diagnosis in `PROFILE_RAW.jsonl` used Q0 and seed 2911332506172719186 and is excluded from the panel. In 20-then-22 order, accumulated screen calls took 61.855 versus 73.916 ms, while the rest of online work after GPU initialization and screen calls took 88.532 versus 68.401 ms. The wider bitmap saved about 20 ms of remaining work but increased screen time about 12 ms in this one diagnostic. This is a cost hypothesis, not an isolated GPU timing comparison or a revised performance claim. A hierarchical two-level screen that first consults the cache-friendlier 20-bit bitmap and consults the 22-bit bitmap only for positives is the next falsifiable candidate.

## Frozen two-level 22-bit follow-up

The protocol in `COARSE_PROTOCOL.md` was frozen before the 30 timed arms. The admission arm matched the ordered GPU flag digest and complete certificate digest for the 22-bit-only and two-level screens. The fresh panel compared the merged 20-bit control with the two-level 22-bit candidate on five public targets and three new seeds, with setup, shader initialization, screening, relation collection, elimination, certificate replay, and process launch charged. `verify_coarse.py` passed all 30 independent public group checks and all 15 complete-field certificate comparisons; there were no failed or censored arms. Source and binary hashes are in `COARSE_MANIFEST.json`, with every process record in `COARSE_RAW.jsonl`. [pcc:unverified]

| Measure | 20-bit control | Two-level 22-bit |
| --- | ---: | ---: |
| Median charged wall, 15 arms each | 186.274 ms | 166.015 ms |
| Median charged child CPU, 15 arms each | 101.251 ms | 84.195 ms |
| Median GPU-positive candidates | 1,560,941 | 396,249 |
| Median exact CPU lookups | 1,172,726 | 296,901 |
| Median accumulated screen time | 61.970 ms | 60.928 ms |
| Median paired control/candidate wall ratio | — | **1.132×** |
| Median paired control/candidate CPU ratio | — | **1.207×** |
| Candidate wins, wall / CPU | — | 15/15 / 15/15 |

The frozen ≥1.15 wall gate **failed**, despite passing the CPU and win-count gates. The two-level screen is therefore not selected as a default. It kept the roughly fourfold reduction in positive candidates while bringing accumulated screen time close to the 20-bit control in this panel. The remaining charged wall cost calls for a different algorithmic or dataflow change; these local producer timings do not establish a broader performance claim. [pcc:unverified]
