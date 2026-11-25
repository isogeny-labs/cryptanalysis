---
title: "n = 83 field ops 2 (R1): local diagnostic"
date: 2026-11-07
---

# n = 83 field ops 2 (R1): local diagnostic

This is the local diagnostic that sized the Tier 1 design of
`koblitz-n83-fieldops2-20261107`. It is not evidence: it ran on a shared
cloud-agent VM, one pinned CPU (`taskset -c 2`), rustc 1.97, built from the
frozen derivation (`make_fieldops2_source.py`) `[pcc:unverified]`. A is the field-ops row
(`ic_online_fieldops_r770`), B the R1 producer (`ic_online_fieldops2_r770`), both
built with `-C target-feature=+pclmulqdq`. Each round ran a fresh process of A
and then of B on the M38 closure base: 4 cold rounds (seed 7) and 3 rank
rounds (rank seed 1501) `[pcc:unverified]`.

| stage (mean ms) | A | B | B / A |
| --- | ---: | ---: | ---: |
| index build (cold process) | 4240 | 4067 | 0.9592 |
| scan self-test (cold process) | 1171 | 1248 | 1.0656 |
| online, one target (cold process) | 861 | 820 | 0.9518 |
| rank stage (rank process) | 3531 | 3474 | 0.9840 |

On every round the index, layout, relation, per-attempt probe and root-call
digests of A and B were identical `[pcc:unverified]`. The self-test does not run field products, so its B / A
is noise on this VM and is kept as measured. The four B / A figures are the
`modelled` factors that `power_check.py` reads (`inputs/local_profile.json`).
