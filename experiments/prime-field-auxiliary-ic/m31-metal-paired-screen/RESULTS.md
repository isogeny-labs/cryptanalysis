# Paired Metal x-coordinate screen

The frozen source and protocol are at commit `17ea02bae`. Mode 3 fuses the target-minus and target-plus x-coordinate calculations for each pair entry, using one inverse of the shared ordinary denominator. Identity and equal-x cases call the prior candidate routine. Mode 2 is the exact-x GPU control with the same coarse/fine bitmaps, exact x table, output order and Rust witness replay. [pcc:unverified]

The fixed Q0 admission checked **every flag in the first 64-lane GPU round** against Rust affine addition and exact x membership for both modes. Their full ordered flag digests, complete certificate digests, scalar, queries, relations and rank matched. `edge_check.swift` also compared all 32 flags from four inputs (identity, P, −P and 2P) against the original kernel, including vertical and tangent outputs. Admission and edge checks were excluded from timing. [pcc:unverified]

The fresh 30-arm panel used five public Q and three new seeds. All 30 answers passed independent affine multiplication; all 15 matched pairs had identical complete certificate digests, queries, relations and rank. `verify.py` passed, with no failures or censored arms. `PAIRED_MANIFEST.json` fixes source and binary hashes and schedule; `PAIRED_RAW.jsonl` retains each process record. [pcc:unverified]

| Metric | Exact-x control | Paired x candidate |
| --- | ---: | ---: |
| Median charged wall, 15 arms each | 148.720 ms | 131.872 ms |
| Median charged child CPU, 15 arms each | 68.278 ms | 68.048 ms |
| Median accumulated GPU screen | 54.262 ms | 37.900 ms |
| Median GPU-positive candidates | 1,476 | 1,476 |
| Median Rust exact lookups | 202 | 202 |
| Median paired control/candidate wall ratio | — | **1.159×** |
| Median paired control/candidate CPU ratio | — | **1.004×** |
| Candidate wins, wall / CPU | — | 15/15 / 11/15 |

The candidate reduced the measured screen phase but **failed the frozen ≥1.20 wall and CPU gates**. It is not selected as a replacement for mode 2. This is a local producer comparison, not independent PCC standing. A direct same-target comparison against the merged 20-bit Metal path is needed to determine the joint effect; ratios from separate panels must not be multiplied into a claimed end-to-end gain. [pcc:unverified]

## Direct comparison with the merged 20-bit Metal path

The independently seeded `DIRECT_PROTOCOL.md` compared mode 0 with mode 3 in 30 fresh-process arms. Fixed Q0 admission checked the mode 3 first-round flags against Rust arithmetic and matched the complete certificate with mode 0 before timing. All 30 timed answers passed independent affine multiplication; every pair matched complete certificate digest, queries, relation count and rank. `verify_direct.py` passed; there were no failed or censored arms. Raw records and source/binary hashes are in `DIRECT_RAW.jsonl` and `DIRECT_MANIFEST.json`. [pcc:unverified]

| Metric | Merged 20-bit control | Paired exact-x candidate |
| --- | ---: | ---: |
| Median charged wall, 15 arms each | 146.659 ms | 106.808 ms |
| Median charged child CPU, 15 arms each | 87.879 ms | 60.485 ms |
| Median accumulated GPU screen | 40.470 ms | 28.747 ms |
| Median GPU-positive candidates | 1,561,637 | 1,488 |
| Median Rust exact lookups | 1,172,962 | 205 |
| Median paired control/candidate wall ratio | — | **1.361×** |
| Median paired control/candidate CPU ratio | — | **1.455×** |
| Candidate wins, wall / CPU | — | **14/15 / 15/15** |

The prespecified ≥1.20 median and ≥12/15 win gates passed locally. The one wall loss was target 3, seed index 2: the candidate took 319.665 ms versus 158.024 ms for the control, while its CPU metric still favored the candidate. It is retained in every statistic. This is a direct, setup-charged IC-vs-IC improvement on this public panel, subject to independent PCC standing and fresh-seed confirmation; it does not follow from multiplying earlier component ratios. Matched rho distance on these fresh seeds is pending. [pcc:unverified]
